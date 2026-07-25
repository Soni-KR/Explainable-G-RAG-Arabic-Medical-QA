from __future__ import annotations

"""Validate human labels and train a disabled, interpretable two-stage reranker."""

import argparse
import csv
import json
import math
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.config import load_final_config
from src.step08a_normalize_query import normalize_query
from src.step09_hybrid_retrieval import normalized_content_terms, select_relevance_phrases


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ANNOTATIONS = (
    ROOT / "data" / "evaluation" / "candidate_relevance_annotations_100.csv"
)
DEFAULT_FROZEN_QUEUE = DEFAULT_ANNOTATIONS
DEFAULT_RETRIEVAL = (
    ROOT
    / "outputs"
    / "evaluation"
    / "retrieval"
    / "evaluation_v1_retrieval_fullhybrid_qacorpus_identityfix_100q_v1"
    / "full_hybrid.jsonl"
)
DEFAULT_OUTPUT = ROOT / "models" / "candidate_reranker_two_stage_v1.json"

CONFIRMED_STATUSES = {"annotated", "adjudicated", "human_confirmed"}
HUMAN_FIELDS = {
    "relevance_label",
    "error_reason",
    "secondary_error_reason",
    "annotator_id",
    "annotation_status",
    "annotation_notes",
}
KEY_FIELDS = ("query_id", "candidate_type", "candidate_id")
REQUIRED_FEATURE_FIELDS = {
    "query_id",
    "query",
    "candidate_type",
    "candidate_rank",
    "candidate_id",
    "candidate_question",
    "retrieval_channel",
    "retrieval_score",
    "answer_relevance",
    "query_concept_coverage",
    "query_constraint_coverage",
    "entity_identity",
    "intent_support",
    "source_reliability",
    "vector_similarity",
    "graph_support",
    "anatomy_mismatch",
    "unrelated_condition_mismatch",
    "matched_query_concepts",
    "missing_query_concepts",
    "relevance_label",
    "error_reason",
}

NUMERIC_FEATURES = (
    "retrieval_score",
    "answer_relevance",
    "query_concept_coverage",
    "query_constraint_coverage",
    "entity_identity",
    "intent_support",
    "source_reliability",
    "vector_similarity",
    "graph_support",
    "anatomy_mismatch",
    "unrelated_condition_mismatch",
)
DERIVED_FEATURES = (
    "candidate_rank_reciprocal",
    "expansion_rank_reciprocal",
    "variant_support_count",
    "candidate_pool_expansion",
    "matched_query_concept_count",
    "missing_query_concept_count",
    "exact_question_match",
    "candidate_is_relation",
)
PHRASE_FEATURES = (
    "medical_phrase_count",
    "mean_phrase_coverage_in_question",
    "mean_phrase_coverage_in_candidate",
    "minimum_phrase_coverage_in_candidate",
    "exact_phrase_fraction_in_question",
    "exact_phrase_fraction_in_candidate",
    "all_phrases_covered",
)
CHANNEL_FEATURES = (
    "channel_graph_relation",
    "channel_fts_qa",
    "channel_fts_e5_qa",
    "channel_vector",
    "channel_graph",
    "channel_partial_fts_expansion",
    "channel_other",
)
FEATURE_NAMES = (
    *NUMERIC_FEATURES,
    *DERIVED_FEATURES,
    *PHRASE_FEATURES,
    *CHANNEL_FEATURES,
)


# ---------------------------------------------------------------------------
# Annotation validation
# ---------------------------------------------------------------------------


def as_float(value: Any) -> float:
    text = str(value or "").strip().lower()
    if text in {"true", "yes"}:
        return 1.0
    if text in {"false", "no", ""}:
        return 0.0
    try:
        number = float(text)
    except ValueError:
        return 0.0
    return number if math.isfinite(number) else 0.0


def candidate_key(row: dict[str, str]) -> tuple[str, str, str]:
    return tuple(str(row.get(field) or "").strip() for field in KEY_FIELDS)  # type: ignore[return-value]


def normalize_candidate_schema(
    rows: Sequence[dict[str, str]],
    fieldnames: Sequence[str],
) -> tuple[list[dict[str, str]], list[str]]:
    """Map the combined-pool rank field to the trainer's stable feature name."""

    normalized_fields = list(fieldnames)
    if "candidate_rank" not in normalized_fields and "pool_rank" in normalized_fields:
        normalized_fields.append("candidate_rank")
    normalized_rows: list[dict[str, str]] = []
    for source in rows:
        row = dict(source)
        if not str(row.get("candidate_rank") or "").strip():
            row["candidate_rank"] = str(row.get("pool_rank") or "").strip()
        normalized_rows.append(row)
    return normalized_rows, normalized_fields


def read_csv(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader), list(reader.fieldnames or [])


def load_query_medical_phrases(path: Path) -> dict[str, list[str]]:
    phrases_by_query: dict[str, list[str]] = {}
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            text = line.strip()
            if not text:
                continue
            try:
                record = json.loads(text)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid retrieval JSONL at {path}:{line_number}") from exc
            analysis = dict(record.get("query_analysis") or {})
            query_id = str(record.get("query_id") or "")
            phrases_by_query[query_id] = select_relevance_phrases(
                list(analysis.get("medical_phrases") or []),
                str(analysis.get("primary_intent") or ""),
            )
    return phrases_by_query


def validate_candidate_rows(
    rows: Sequence[dict[str, str]],
    fieldnames: Sequence[str],
) -> dict[str, Any]:
    missing_fields = sorted(REQUIRED_FEATURE_FIELDS.difference(fieldnames))
    if missing_fields:
        raise ValueError(f"Annotation file is missing fields: {missing_fields}")

    keys = [candidate_key(row) for row in rows]
    duplicate_keys = len(keys) - len(set(keys))
    if duplicate_keys:
        raise ValueError(f"Annotation file contains {duplicate_keys} duplicate candidate keys.")

    label_counts = {
        label: sum(str(row.get("relevance_label") or "").strip() == label for row in rows)
        for label in ("0", "1", "2")
    }
    blank_labels = sum(not str(row.get("relevance_label") or "").strip() for row in rows)
    invalid_labels = sum(
        bool(str(row.get("relevance_label") or "").strip())
        and str(row.get("relevance_label") or "").strip() not in {"0", "1", "2"}
        for row in rows
    )
    label_two_with_reason = sum(
        str(row.get("relevance_label") or "").strip() == "2"
        and bool(str(row.get("error_reason") or "").strip())
        for row in rows
    )
    weak_labels_without_reason = sum(
        str(row.get("relevance_label") or "").strip() in {"0", "1"}
        and not str(row.get("error_reason") or "").strip()
        for row in rows
    )

    return {
        "rows": len(rows),
        "queries": len({str(row.get("query_id") or "") for row in rows}),
        "duplicate_keys": duplicate_keys,
        "blank_labels": blank_labels,
        "invalid_labels": invalid_labels,
        "label_two_with_reason": label_two_with_reason,
        "weak_labels_without_reason": weak_labels_without_reason,
        "label_counts": label_counts,
    }


def validate_against_frozen_queue(
    annotated_rows: Sequence[dict[str, str]],
    annotated_fields: Sequence[str],
    frozen_queue: Path,
) -> dict[str, Any]:
    frozen_rows, frozen_fields = read_csv(frozen_queue)
    annotated_by_key = {candidate_key(row): row for row in annotated_rows}
    frozen_by_key = {candidate_key(row): row for row in frozen_rows}

    missing_keys = sorted(set(frozen_by_key).difference(annotated_by_key))
    extra_keys = sorted(set(annotated_by_key).difference(frozen_by_key))
    comparable_fields = sorted(
        set(annotated_fields).intersection(frozen_fields).difference(HUMAN_FIELDS)
    )
    changed_rows = 0
    for key in set(annotated_by_key).intersection(frozen_by_key):
        if any(
            str(annotated_by_key[key].get(field) or "")
            != str(frozen_by_key[key].get(field) or "")
            for field in comparable_fields
        ):
            changed_rows += 1

    if missing_keys or extra_keys or changed_rows:
        raise ValueError(
            "Human annotation file does not match the frozen candidate queue: "
            f"missing={len(missing_keys)}, extra={len(extra_keys)}, "
            f"changed_candidate_rows={changed_rows}."
        )
    return {
        "frozen_queue": str(frozen_queue.relative_to(ROOT)),
        "missing_candidate_keys": 0,
        "extra_candidate_keys": 0,
        "changed_candidate_rows": 0,
    }


def validate_original_subset(
    combined_rows: Sequence[dict[str, str]],
    original_annotations: Path,
) -> dict[str, Any]:
    """Confirm the combined pool preserves every original candidate and label."""

    original_rows, _ = read_csv(original_annotations)
    expected = {candidate_key(row): row for row in original_rows}
    actual = {
        candidate_key(row): row
        for row in combined_rows
        if str(row.get("candidate_pool") or "").strip() == "original_pool"
    }
    missing = sorted(set(expected).difference(actual))
    extra = sorted(set(actual).difference(expected))
    changed_labels = [
        key
        for key in set(expected).intersection(actual)
        if str(expected[key].get("relevance_label") or "").strip()
        != str(actual[key].get("relevance_label") or "").strip()
    ]
    if missing or extra or changed_labels:
        raise ValueError(
            "Combined pool does not preserve the original human annotations: "
            f"missing={len(missing)}, extra={len(extra)}, "
            f"changed_labels={len(changed_labels)}."
        )
    return {
        "original_annotations": str(original_annotations.relative_to(ROOT)),
        "preserved_original_candidates": len(expected),
        "missing_candidate_keys": 0,
        "extra_candidate_keys": 0,
        "changed_labels": 0,
    }


def confirmed_rows(
    rows: Sequence[dict[str, str]],
    fieldnames: Sequence[str],
    explicit_annotator_id: str,
) -> tuple[list[dict[str, str]], dict[str, int], str]:
    has_status = "annotation_status" in fieldnames
    has_annotator = "annotator_id" in fieldnames
    status_counts: dict[str, int] = {}
    confirmed: list[dict[str, str]] = []

    if not has_status and not has_annotator:
        if not explicit_annotator_id:
            return [], {"missing_provenance": len(rows)}, "missing_provenance"
        for source_row in rows:
            row = dict(source_row)
            row["annotation_status"] = "annotated"
            row["annotator_id"] = explicit_annotator_id
            confirmed.append(row)
        return confirmed, {"annotated": len(confirmed)}, "explicit_cli_confirmation"

    if has_status != has_annotator:
        raise ValueError(
            "annotation_status and annotator_id must either both exist or both be absent."
        )

    for row in rows:
        status = str(row.get("annotation_status") or "").strip()
        status_counts[status] = status_counts.get(status, 0) + 1
        if status not in CONFIRMED_STATUSES:
            continue
        if not str(row.get("annotator_id") or "").strip():
            raise ValueError(
                f"Confirmed row {row.get('query_id')}/{row.get('candidate_id')} "
                "must identify its human annotator."
            )
        confirmed.append(dict(row))
    return confirmed, status_counts, "embedded_csv_provenance"


def validate_confirmed_labels(rows: Sequence[dict[str, str]]) -> None:
    for row in rows:
        label = str(row.get("relevance_label") or "").strip()
        reason = str(row.get("error_reason") or "").strip()
        key = f"{row.get('query_id')}/{row.get('candidate_id')}"
        if label not in {"0", "1", "2"}:
            raise ValueError(f"Confirmed row {key} must have label 0, 1, or 2.")
        if label == "2" and reason:
            raise ValueError(f"Directly relevant row {key} must not have an error reason.")
        if label in {"0", "1"} and not reason:
            raise ValueError(f"Weak/irrelevant row {key} must include an error reason.")


# ---------------------------------------------------------------------------
# Feature construction and grouped two-stage modeling
# ---------------------------------------------------------------------------


def term_count(value: Any) -> float:
    return float(sum(bool(part.strip()) for part in str(value or "").split("|")))


def exact_question_match(row: dict[str, str]) -> float:
    query = normalize_query(str(row.get("query") or "")).normalized_query
    candidate = normalize_query(
        str(row.get("candidate_question") or "")
    ).normalized_query
    return 1.0 if query and query == candidate else 0.0


def normalized_phrase_coverage(phrase: str, candidate: str) -> float:
    phrase_terms = normalized_content_terms(phrase)
    if not phrase_terms:
        return 0.0
    candidate_terms = normalized_content_terms(candidate)
    return len(phrase_terms & candidate_terms) / len(phrase_terms)


def exact_phrase_match(phrase: str, candidate: str) -> float:
    normalized_phrase = normalize_query(phrase).normalized_query
    normalized_candidate = normalize_query(candidate).normalized_query
    return (
        1.0
        if normalized_phrase and normalized_phrase in normalized_candidate
        else 0.0
    )


def phrase_features(
    row: dict[str, str],
    medical_phrases: Sequence[str],
) -> list[float]:
    phrases = [str(item).strip() for item in medical_phrases if str(item).strip()]
    if not phrases:
        return [0.0] * len(PHRASE_FEATURES)
    question = str(row.get("candidate_question") or "")
    candidate = " ".join(
        [
            question,
            str(row.get("candidate_answer_or_evidence") or ""),
            str(row.get("source_entity_name") or ""),
            str(row.get("target_entity_name") or ""),
        ]
    )
    question_coverage = [
        normalized_phrase_coverage(phrase, question) for phrase in phrases
    ]
    candidate_coverage = [
        normalized_phrase_coverage(phrase, candidate) for phrase in phrases
    ]
    exact_question = [exact_phrase_match(phrase, question) for phrase in phrases]
    exact_candidate = [exact_phrase_match(phrase, candidate) for phrase in phrases]
    return [
        float(len(phrases)),
        sum(question_coverage) / len(phrases),
        sum(candidate_coverage) / len(phrases),
        min(candidate_coverage),
        sum(exact_question) / len(phrases),
        sum(exact_candidate) / len(phrases),
        1.0 if min(candidate_coverage) >= 1.0 else 0.0,
    ]


def row_features(
    row: dict[str, str],
    medical_phrases: Sequence[str] = (),
) -> list[float]:
    channel = str(row.get("retrieval_channel") or "").strip().lower()
    known_channels = {name.removeprefix("channel_") for name in CHANNEL_FEATURES[:-1]}
    channel_values = [
        1.0 if channel == name.removeprefix("channel_") else 0.0
        for name in CHANNEL_FEATURES[:-1]
    ]
    channel_values.append(1.0 if channel not in known_channels else 0.0)
    rank = max(1.0, as_float(row.get("candidate_rank")))
    expansion_rank = max(1.0, as_float(row.get("pool_rank")))
    return [
        *[as_float(row.get(name)) for name in NUMERIC_FEATURES],
        1.0 / rank,
        1.0 / expansion_rank
        if str(row.get("candidate_pool") or "").strip() == "partial_fts_expansion"
        else 0.0,
        as_float(row.get("variant_support_count")),
        1.0
        if str(row.get("candidate_pool") or "").strip() == "partial_fts_expansion"
        else 0.0,
        term_count(row.get("matched_query_concepts")),
        term_count(row.get("missing_query_concepts")),
        exact_question_match(row),
        1.0 if row.get("candidate_type") == "relation" else 0.0,
        *phrase_features(row, medical_phrases),
        *channel_values,
    ]


def make_pipeline() -> Any:
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler

    return Pipeline(
        [
            ("scale", StandardScaler()),
            (
                "model",
                LogisticRegression(
                    class_weight="balanced",
                    max_iter=2000,
                    random_state=42,
                ),
            ),
        ]
    )


def positive_probability(model: Any, values: Any) -> Any:
    classes = list(model.named_steps["model"].classes_)
    if 1 not in classes:
        raise ValueError("Binary model does not contain positive class 1.")
    return model.predict_proba(values)[:, classes.index(1)]


def cross_validated_two_stage_scores(
    x: Any,
    y: Any,
    groups: Any,
    requested_folds: int,
) -> tuple[Any, Any, Any, int]:
    import numpy as np
    from sklearn.model_selection import GroupKFold

    unique_groups = len(set(groups.tolist()))
    folds = min(max(2, requested_folds), unique_groups)
    p_usable = np.zeros(len(y), dtype=float)
    p_direct_given_usable = np.zeros(len(y), dtype=float)

    for train_indices, test_indices in GroupKFold(n_splits=folds).split(
        x, y, groups=groups
    ):
        stage_a_target = (y[train_indices] > 0).astype(int)
        if len(set(stage_a_target.tolist())) < 2:
            raise RuntimeError("A grouped fold cannot train the usable-candidate stage.")
        stage_a = make_pipeline().fit(x[train_indices], stage_a_target)
        p_usable[test_indices] = positive_probability(stage_a, x[test_indices])

        usable_train = train_indices[y[train_indices] > 0]
        stage_b_target = (y[usable_train] == 2).astype(int)
        if len(set(stage_b_target.tolist())) < 2:
            raise RuntimeError("A grouped fold cannot train the direct-answer stage.")
        stage_b = make_pipeline().fit(x[usable_train], stage_b_target)
        p_direct_given_usable[test_indices] = positive_probability(
            stage_b, x[test_indices]
        )

    p_direct = p_usable * p_direct_given_usable
    expected_relevance = p_usable * (1.0 + p_direct_given_usable)
    return p_usable, p_direct_given_usable, expected_relevance, folds


# ---------------------------------------------------------------------------
# Classification and ranking diagnostics
# ---------------------------------------------------------------------------


def binary_metrics(target: Any, probabilities: Any) -> dict[str, float]:
    from sklearn.metrics import (
        average_precision_score,
        f1_score,
        precision_score,
        recall_score,
        roc_auc_score,
    )

    prediction = (probabilities >= 0.5).astype(int)
    return {
        "roc_auc": round(float(roc_auc_score(target, probabilities)), 6),
        "average_precision": round(
            float(average_precision_score(target, probabilities)), 6
        ),
        "precision_at_0_5": round(
            float(precision_score(target, prediction, zero_division=0)), 6
        ),
        "recall_at_0_5": round(
            float(recall_score(target, prediction, zero_division=0)), 6
        ),
        "f1_at_0_5": round(
            float(f1_score(target, prediction, zero_division=0)), 6
        ),
    }


def discounted_gain(labels: Sequence[int], cutoff: int) -> float:
    return sum(
        ((2**label) - 1.0) / math.log2(rank + 2.0)
        for rank, label in enumerate(labels[:cutoff])
    )


def ranking_metrics(
    rows: Sequence[dict[str, str]],
    scores: Sequence[float],
    cutoff: int = 5,
) -> dict[str, Any]:
    grouped: dict[str, list[int]] = defaultdict(list)
    for index, row in enumerate(rows):
        grouped[str(row.get("query_id") or "")].append(index)

    ndcg_all: list[float] = []
    ndcg_relevant: list[float] = []
    reciprocal_ranks: list[float] = []
    reciprocal_ranks_eligible: list[float] = []
    useful_precisions: list[float] = []
    useful_at_rank_one = 0
    top_one_direct = 0
    eligible_direct_queries = 0
    direct_in_top_k = 0

    for indices in grouped.values():
        ranked = sorted(
            indices,
            key=lambda index: (
                float(scores[index]),
                -as_float(rows[index].get("candidate_rank")),
            ),
            reverse=True,
        )
        labels = [int(rows[index]["relevance_label"]) for index in ranked]
        ideal = sorted(labels, reverse=True)
        ideal_gain = discounted_gain(ideal, cutoff)
        ndcg = discounted_gain(labels, cutoff) / ideal_gain if ideal_gain else 0.0
        ndcg_all.append(ndcg)
        if ideal_gain:
            ndcg_relevant.append(ndcg)

        direct_rank = next(
            (rank for rank, label in enumerate(labels, start=1) if label == 2),
            None,
        )
        reciprocal_ranks.append(1.0 / direct_rank if direct_rank else 0.0)
        if 2 in labels:
            eligible_direct_queries += 1
            reciprocal_ranks_eligible.append(1.0 / direct_rank)
            if direct_rank <= cutoff:
                direct_in_top_k += 1
        if labels and labels[0] == 2:
            top_one_direct += 1
        if labels and labels[0] >= 1:
            useful_at_rank_one += 1

        selected = labels[: min(3, len(labels))]
        useful_precisions.append(
            sum(label >= 1 for label in selected) / len(selected)
            if selected
            else 0.0
        )

    query_count = len(grouped)
    return {
        "queries": query_count,
        "queries_with_any_relevant_candidate": len(ndcg_relevant),
        "queries_with_direct_candidate": eligible_direct_queries,
        "ndcg_at_5_all_queries": round(sum(ndcg_all) / query_count, 6),
        "ndcg_at_5_relevant_queries": round(
            sum(ndcg_relevant) / len(ndcg_relevant), 6
        )
        if ndcg_relevant
        else None,
        "mrr_direct_all_queries": round(
            sum(reciprocal_ranks) / query_count, 6
        ),
        "mrr_direct_eligible_queries": round(
            sum(reciprocal_ranks_eligible) / len(reciprocal_ranks_eligible), 6
        )
        if reciprocal_ranks_eligible
        else None,
        "direct_at_rank_1_count": top_one_direct,
        "useful_at_rank_1_count": useful_at_rank_one,
        "direct_at_rank_1_all_queries": round(top_one_direct / query_count, 6),
        "direct_at_rank_1_eligible_queries": round(
            top_one_direct / eligible_direct_queries, 6
        )
        if eligible_direct_queries
        else None,
        "queries_retaining_direct_at_5": direct_in_top_k,
        "useful_precision_at_3": round(
            sum(useful_precisions) / query_count, 6
        ),
    }


def score_baselines(rows: Sequence[dict[str, str]]) -> dict[str, list[float]]:
    return {
        "current_candidate_rank": [
            -as_float(row.get("candidate_rank")) for row in rows
        ],
        "retrieval_score": [
            as_float(row.get("retrieval_score")) for row in rows
        ],
        "answer_relevance": [
            as_float(row.get("answer_relevance")) for row in rows
        ],
        "query_concept_coverage": [
            as_float(row.get("query_concept_coverage")) for row in rows
        ],
        "oracle_human_label": [
            as_float(row.get("relevance_label")) for row in rows
        ],
    }


def evaluate_rankings(
    rows: Sequence[dict[str, str]],
    model_scores: Sequence[float],
) -> dict[str, Any]:
    all_scores = score_baselines(rows)
    all_scores["two_stage_cross_validated"] = list(model_scores)
    all_metrics = {
        name: ranking_metrics(rows, scores)
        for name, scores in all_scores.items()
    }

    evidence_indices = [
        index for index, row in enumerate(rows) if row.get("candidate_type") == "evidence"
    ]
    evidence_rows = [rows[index] for index in evidence_indices]
    evidence_metrics = {
        name: ranking_metrics(
            evidence_rows,
            [scores[index] for index in evidence_indices],
        )
        for name, scores in all_scores.items()
    }
    return {
        "all_candidates": all_metrics,
        "evidence_candidates_only": evidence_metrics,
    }


def write_oof_predictions(
    path: Path,
    rows: Sequence[dict[str, str]],
    p_usable: Sequence[float],
    p_direct_given_usable: Sequence[float],
    expected_relevance: Sequence[float],
) -> None:
    fields = (
        "query_id",
        "candidate_type",
        "candidate_id",
        "candidate_pool",
        "relevance_label",
        "candidate_rank",
        "p_usable",
        "p_direct_given_usable",
        "p_direct",
        "expected_relevance",
    )
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for index, row in enumerate(rows):
            usable = float(p_usable[index])
            conditional_direct = float(p_direct_given_usable[index])
            writer.writerow(
                {
                    "query_id": row.get("query_id", ""),
                    "candidate_type": row.get("candidate_type", ""),
                    "candidate_id": row.get("candidate_id", ""),
                    "candidate_pool": row.get("candidate_pool", ""),
                    "relevance_label": row.get("relevance_label", ""),
                    "candidate_rank": row.get("candidate_rank", ""),
                    "p_usable": round(usable, 8),
                    "p_direct_given_usable": round(conditional_direct, 8),
                    "p_direct": round(usable * conditional_direct, 8),
                    "expected_relevance": round(float(expected_relevance[index]), 8),
                }
            )


def serialize_pipeline(model: Any) -> dict[str, Any]:
    scaler = model.named_steps["scale"]
    classifier = model.named_steps["model"]
    return {
        "scaler_mean": scaler.mean_.tolist(),
        "scaler_scale": scaler.scale_.tolist(),
        "classes": classifier.classes_.tolist(),
        "coefficients": classifier.coef_.tolist(),
        "intercepts": classifier.intercept_.tolist(),
    }


def train_final_models(x: Any, y: Any) -> tuple[Any, Any]:
    stage_a = make_pipeline().fit(x, (y > 0).astype(int))
    usable = y > 0
    stage_b = make_pipeline().fit(x[usable], (y[usable] == 2).astype(int))
    return stage_a, stage_b


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate labels and train a two-stage human-supervised reranker."
    )
    parser.add_argument("--annotations", type=Path, default=DEFAULT_ANNOTATIONS)
    parser.add_argument("--frozen-queue", type=Path, default=DEFAULT_FROZEN_QUEUE)
    parser.add_argument("--retrieval-jsonl", type=Path, default=DEFAULT_RETRIEVAL)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--minimum-labels", type=int, default=100)
    parser.add_argument("--folds", type=int, default=5)
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument(
        "--original-annotations",
        type=Path,
        default=None,
        help=(
            "For a combined pool, validate that its original_pool rows preserve "
            "this frozen human-annotation file."
        ),
    )
    parser.add_argument(
        "--model-version",
        default="candidate_reranker_two_stage_v1",
    )
    parser.add_argument(
        "--oof-output",
        type=Path,
        default=None,
        help="Optional CSV destination for grouped out-of-fold predictions.",
    )
    parser.add_argument(
        "--confirmed-annotator-id",
        default="",
        help=(
            "Explicit provenance ID required when a human-labeled file omits "
            "annotation_status and annotator_id columns."
        ),
    )
    args = parser.parse_args()

    annotations = args.annotations.resolve()
    frozen_queue = args.frozen_queue.resolve()
    all_rows, fieldnames = read_csv(annotations)
    all_rows, fieldnames = normalize_candidate_schema(all_rows, fieldnames)
    integrity = validate_candidate_rows(all_rows, fieldnames)
    if args.original_annotations is not None:
        frozen_validation = validate_original_subset(
            all_rows,
            args.original_annotations.resolve(),
        )
    else:
        frozen_validation = validate_against_frozen_queue(
            all_rows, fieldnames, frozen_queue
        )
    rows, status_counts, provenance_mode = confirmed_rows(
        all_rows,
        fieldnames,
        explicit_annotator_id=args.confirmed_annotator_id.strip(),
    )
    validate_confirmed_labels(rows)

    label_counts = {
        label: sum(row.get("relevance_label") == label for row in rows)
        for label in ("0", "1", "2")
    }
    minimum = max(1, args.minimum_labels)
    training_ready = (
        len(rows) >= minimum
        and all(label_counts[label] > 0 for label in ("0", "1", "2"))
    )
    summary = {
        "annotation_file": str(annotations.relative_to(ROOT)),
        "integrity": integrity,
        "frozen_candidate_validation": frozen_validation,
        "provenance_mode": provenance_mode,
        "confirmed_annotator_id": args.confirmed_annotator_id.strip() or None,
        "confirmed_rows": len(rows),
        "status_counts": status_counts,
        "label_counts": label_counts,
        "minimum_required": minimum,
        "training_ready": training_ready,
    }
    if args.validate_only:
        print(json.dumps(summary, ensure_ascii=False))
        return 0
    if not training_ready:
        raise RuntimeError(
            "Confirmed human labels are insufficient for two-stage training. "
            f"Current summary: {json.dumps(summary, ensure_ascii=False)}"
        )

    try:
        import numpy as np
        import sklearn
        from sklearn.metrics import f1_score
    except ImportError as exc:
        raise RuntimeError(
            "Training requires numpy and scikit-learn in the project virtual environment."
        ) from exc

    retrieval_path = args.retrieval_jsonl.resolve()
    phrases_by_query = load_query_medical_phrases(retrieval_path)
    missing_phrase_records = sorted(
        {
            str(row.get("query_id") or "")
            for row in rows
            if str(row.get("query_id") or "") not in phrases_by_query
        }
    )
    if missing_phrase_records:
        raise ValueError(
            "Retrieval artifact is missing query analysis for labeled queries: "
            f"{missing_phrase_records[:5]}"
        )
    x = np.asarray(
        [
            row_features(
                row,
                phrases_by_query[str(row.get("query_id") or "")],
            )
            for row in rows
        ],
        dtype=float,
    )
    y = np.asarray([int(row["relevance_label"]) for row in rows], dtype=int)
    groups = np.asarray([str(row.get("query_id") or "") for row in rows])
    p_usable, p_direct_given_usable, model_scores, folds = (
        cross_validated_two_stage_scores(
            x,
            y,
            groups,
            requested_folds=max(2, args.folds),
        )
    )
    p_direct = p_usable * p_direct_given_usable
    three_class_prediction = np.where(
        p_usable < 0.5,
        0,
        np.where(p_direct_given_usable >= 0.5, 2, 1),
    )
    usable_mask = y > 0
    classification = {
        "usable_vs_irrelevant": binary_metrics((y > 0).astype(int), p_usable),
        "direct_vs_partial_among_usable": binary_metrics(
            (y[usable_mask] == 2).astype(int),
            p_direct_given_usable[usable_mask],
        ),
        "direct_vs_all": binary_metrics((y == 2).astype(int), p_direct),
        "three_class_macro_f1": round(
            float(f1_score(y, three_class_prediction, average="macro")), 6
        ),
    }
    rankings = evaluate_rankings(rows, model_scores)
    stage_a, stage_b = train_final_models(x, y)
    config = load_final_config()

    payload = {
        "model_type": "two_stage_logistic_regression",
        "model_version": args.model_version,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "graph_version": config.graph_version,
        "annotation_file": str(annotations.relative_to(ROOT)),
        "frozen_queue": str(frozen_queue.relative_to(ROOT)),
        "retrieval_file": str(retrieval_path.relative_to(ROOT)),
        "provenance_mode": provenance_mode,
        "confirmed_annotator_id": args.confirmed_annotator_id.strip() or None,
        "training_rows": len(rows),
        "training_queries": len(set(groups.tolist())),
        "label_counts": label_counts,
        "grouped_cross_validation_folds": folds,
        "feature_names": list(FEATURE_NAMES),
        "cross_validated_classification": classification,
        "cross_validated_ranking": rankings,
        "stage_a_usable_vs_irrelevant": serialize_pipeline(stage_a),
        "stage_b_direct_vs_partial": serialize_pipeline(stage_b),
        "score_formula": "p_usable * (1 + p_direct_given_usable)",
        "scikit_learn_version": sklearn.__version__,
        "activation": "disabled_pending_explicit_production_decision",
    }
    output = args.output.resolve()
    if output.exists() and not args.force:
        raise FileExistsError(f"Model already exists; use --force to replace it: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    oof_output: Path | None = None
    if args.oof_output is not None:
        oof_output = args.oof_output.resolve()
        if oof_output.exists() and not args.force:
            raise FileExistsError(
                f"OOF predictions already exist; use --force to replace: {oof_output}"
            )
        oof_output.parent.mkdir(parents=True, exist_ok=True)
        write_oof_predictions(
            oof_output,
            rows,
            p_usable,
            p_direct_given_usable,
            model_scores,
        )
    print(
        json.dumps(
            {
                **summary,
                "grouped_cross_validation_folds": folds,
                "classification": classification,
                "ranking": rankings,
                "output": str(output.relative_to(ROOT)),
                "oof_output": str(oof_output.relative_to(ROOT))
                if oof_output
                else None,
                "activation": payload["activation"],
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
