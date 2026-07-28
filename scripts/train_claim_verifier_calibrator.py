from __future__ import annotations

"""Train and audit a local semantic calibrator for disputed Step 14 claims.

This is a development evaluator, not an automatic production switch. It uses
query-grouped out-of-fold predictions so claims from one medical question
cannot leak between training and validation folds.
"""

import argparse
import csv
import hashlib
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

import numpy as np

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.config import load_final_config
from src.evidence_policy import authoritative_evidence_texts
from src.models import AnswerClaim, ClaimVerification, EvidenceContextBundle
from src.step14_verify_claims import evidence_candidates, support_score


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REVIEW = (
    ROOT
    / "outputs"
    / "evaluation"
    / "entity_gt_trial_100"
    / "known_answer_diagnosis"
    / "known_answer_removed_claim_review_queue_human_reviewed.csv"
)
DEFAULT_SOURCE = (
    ROOT
    / "outputs"
    / "evaluation"
    / "generation"
    / "entity_gt_trial_100_known_answer_generation_v1"
    / "full_pipeline.jsonl"
)
OUTPUT_ROOT = ROOT / "outputs" / "evaluation" / "claim_verifier"
DEFAULT_MODEL_OUTPUT = ROOT / "models" / "claim_verifier_e5_calibrator_v1.json"
SEED = 20260728

FEATURE_NAMES = [
    "deterministic_support_score",
    "authoritative_support_score",
    "question_relevance",
    "claim_query_concept_coverage",
    "context_answer_relevance",
    "context_entity_identity",
    "context_intent_support",
    "context_vector_similarity",
    "context_query_concept_coverage",
    "context_source_reliability",
    "claim_evidence_e5",
    "claim_query_e5",
    "query_evidence_e5",
    "claim_evidence_length_ratio",
    "evidence_segment_count",
    "failed_intent",
    "failed_concept",
    "failed_anatomy",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8-sig") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def verification_from_dict(payload: dict[str, Any]) -> ClaimVerification:
    values = dict(payload)
    values["claim"] = AnswerClaim(**dict(values["claim"]))
    return ClaimVerification(**values)


def resolve_local_model_snapshot(model_name: str) -> Path:
    """Resolve a cached Hugging Face snapshot without making network calls."""
    direct = Path(model_name)
    if direct.exists():
        return direct.resolve()
    cache_root = (
        Path.home()
        / ".cache"
        / "huggingface"
        / "hub"
        / f"models--{model_name.replace('/', '--')}"
        / "snapshots"
    )
    snapshots = sorted(
        (item for item in cache_root.glob("*") if item.is_dir()),
        key=lambda item: item.stat().st_mtime,
        reverse=True,
    )
    if not snapshots:
        raise FileNotFoundError(
            f"No local Hugging Face snapshot exists for {model_name}. "
            "This evaluator will not download models automatically."
        )
    return snapshots[0].resolve()


def best_authoritative_segments(
    verification: ClaimVerification,
    context: EvidenceContextBundle,
) -> tuple[list[str], dict[str, Any]]:
    evidence_by_id = {
        str(row.get("evidence_id") or ""): row
        for row in context.evidence_items
    }
    facts_by_id = {
        str(row.get("relation_id") or ""): str(row.get("fact") or "")
        for row in context.graph_facts
    }
    row = evidence_by_id.get(verification.best_evidence_id, {})
    relation_facts = [
        facts_by_id.get(str(relation_id), "")
        for relation_id in row.get("relation_ids", [])
        if facts_by_id.get(str(relation_id), "")
    ]
    text_fields, _, _ = authoritative_evidence_texts(row, relation_facts)
    segments = {
        segment.strip()
        for text in text_fields
        for segment in evidence_candidates(text, verification.claim.claim)
        if segment.strip()
    }
    ranked = sorted(
        segments,
        key=lambda segment: (
            support_score(verification.claim.claim, segment),
            len(segment),
        ),
        reverse=True,
    )
    return ranked[:4], row


def build_rows(
    review_rows: list[dict[str, str]],
    source_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    source_by_query = {
        str(row.get("query_id") or ""): row for row in source_rows
    }
    rows: list[dict[str, Any]] = []
    for human in review_rows:
        query_id = str(human.get("query_id") or "")
        source = source_by_query.get(query_id)
        if not source:
            raise ValueError(f"Missing source generation record: {query_id}")
        raw = dict(source.get("raw") or {})
        context = EvidenceContextBundle(**dict(raw["context"]))
        wanted_claim = str(human.get("removed_claim") or "")
        verification = next(
            (
                verification_from_dict(item)
                for item in raw.get("verifications", [])
                if str(dict(item.get("claim") or {}).get("claim") or "")
                == wanted_claim
            ),
            None,
        )
        if verification is None:
            raise ValueError(
                f"Could not match reviewed claim for {query_id}: {wanted_claim}"
            )
        segments, evidence_row = best_authoritative_segments(
            verification,
            context,
        )
        rows.append(
            {
                "query_id": query_id,
                "query": context.reformulated_query or context.query,
                "claim": verification.claim.claim,
                "evidence": " ".join(segments),
                "verification": verification,
                "evidence_row": evidence_row,
                "label": int(
                    str(human.get("human_should_retain") or "") == "yes"
                ),
            }
        )
    return rows


def encode_texts(
    rows: list[dict[str, Any]],
    model_snapshot: Path,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, int]:
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(str(model_snapshot), device="cpu")
    query_vectors = model.encode(
        [f"query: {row['query']}" for row in rows],
        batch_size=16,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    claim_vectors = model.encode(
        [f"passage: {row['claim']}" for row in rows],
        batch_size=16,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    evidence_vectors = model.encode(
        [f"passage: {row['evidence']}" for row in rows],
        batch_size=16,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    return (
        np.asarray(query_vectors, dtype=np.float64),
        np.asarray(claim_vectors, dtype=np.float64),
        np.asarray(evidence_vectors, dtype=np.float64),
        int(model.get_sentence_embedding_dimension()),
    )


def safe_float(value: Any) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


def build_features(
    rows: list[dict[str, Any]],
    query_vectors: np.ndarray,
    claim_vectors: np.ndarray,
    evidence_vectors: np.ndarray,
) -> np.ndarray:
    features: list[list[float]] = []
    for index, row in enumerate(rows):
        verification: ClaimVerification = row["verification"]
        evidence_row: dict[str, Any] = row["evidence_row"]
        evidence = str(row["evidence"] or "")
        claim = str(row["claim"] or "")
        authoritative_score = max(
            (
                support_score(claim, segment)
                for segment in evidence_candidates(evidence, claim)
            ),
            default=0.0,
        )
        failed = set(verification.failed_checks)
        length_ratio = (
            min(len(claim), len(evidence)) / max(len(claim), len(evidence))
            if claim and evidence
            else 0.0
        )
        features.append(
            [
                safe_float(verification.support_score),
                authoritative_score,
                safe_float(verification.question_relevance),
                safe_float(verification.query_concept_coverage),
                safe_float(evidence_row.get("answer_relevance")),
                safe_float(evidence_row.get("entity_identity")),
                safe_float(evidence_row.get("intent_support")),
                safe_float(evidence_row.get("vector_similarity")),
                safe_float(evidence_row.get("query_concept_coverage")),
                safe_float(evidence_row.get("source_reliability")),
                float(np.dot(claim_vectors[index], evidence_vectors[index])),
                float(np.dot(claim_vectors[index], query_vectors[index])),
                float(np.dot(query_vectors[index], evidence_vectors[index])),
                length_ratio,
                float(len(evidence_candidates(evidence, claim))),
                float("intent_mismatch" in failed),
                float("claim_query_concept_mismatch" in failed),
                float("anatomy_mismatch" in failed),
            ]
        )
    return np.asarray(features, dtype=np.float64)


def binary_metrics(labels: np.ndarray, predictions: np.ndarray) -> dict[str, Any]:
    tp = int(np.sum((labels == 1) & (predictions == 1)))
    tn = int(np.sum((labels == 0) & (predictions == 0)))
    fp = int(np.sum((labels == 0) & (predictions == 1)))
    fn = int(np.sum((labels == 1) & (predictions == 0)))

    def divide(left: float, right: float) -> float:
        return left / right if right else 0.0

    precision = divide(tp, tp + fp)
    recall = divide(tp, tp + fn)
    return {
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn,
        "precision": round(precision, 6),
        "recall": round(recall, 6),
        "f1": round(divide(2 * precision * recall, precision + recall), 6),
        "specificity": round(divide(tn, tn + fp), 6),
        "accuracy": round(divide(tp + tn, len(labels)), 6),
    }


def choose_zero_false_positive_threshold(
    labels: np.ndarray,
    probabilities: np.ndarray,
) -> tuple[float, dict[str, Any]]:
    candidates = sorted(
        {0.0, 1.0, *[float(value) for value in probabilities]},
    )
    evaluated = [
        (
            threshold,
            binary_metrics(labels, (probabilities >= threshold).astype(int)),
        )
        for threshold in candidates
    ]
    safe = [item for item in evaluated if item[1]["fp"] == 0]
    threshold, metrics = max(
        safe,
        key=lambda item: (
            item[1]["recall"],
            item[1]["f1"],
            -item[0],
        ),
    )
    return float(threshold), metrics


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Train a query-grouped local E5 claim calibrator."
    )
    parser.add_argument("--review-file", type=Path, default=DEFAULT_REVIEW)
    parser.add_argument("--source-run", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--run-id", default="local_e5_calibrator_v1")
    parser.add_argument(
        "--model-output",
        type=Path,
        default=DEFAULT_MODEL_OUTPUT,
    )
    args = parser.parse_args()

    from sklearn.calibration import calibration_curve
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import (
        average_precision_score,
        brier_score_loss,
        roc_auc_score,
    )
    from sklearn.model_selection import StratifiedGroupKFold
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    review_path = args.review_file.resolve()
    source_path = args.source_run.resolve()
    config = load_final_config()
    model_snapshot = resolve_local_model_snapshot(config.embeddings.model_name)
    rows = build_rows(read_csv(review_path), read_jsonl(source_path))
    query_vectors, claim_vectors, evidence_vectors, dimension = encode_texts(
        rows,
        model_snapshot,
    )
    features = build_features(
        rows,
        query_vectors,
        claim_vectors,
        evidence_vectors,
    )
    labels = np.asarray([row["label"] for row in rows], dtype=np.int64)
    groups = np.asarray([row["query_id"] for row in rows])

    splitter = StratifiedGroupKFold(
        n_splits=5,
        shuffle=True,
        random_state=SEED,
    )
    probabilities = np.zeros(len(rows), dtype=np.float64)
    fold_ids = np.zeros(len(rows), dtype=np.int64)
    for fold, (train_indices, test_indices) in enumerate(
        splitter.split(features, labels, groups),
        start=1,
    ):
        model = make_pipeline(
            StandardScaler(),
            LogisticRegression(
                C=1.0,
                class_weight="balanced",
                max_iter=5000,
                random_state=SEED,
            ),
        )
        model.fit(features[train_indices], labels[train_indices])
        probabilities[test_indices] = model.predict_proba(
            features[test_indices]
        )[:, 1]
        fold_ids[test_indices] = fold

    safe_threshold, safe_metrics = choose_zero_false_positive_threshold(
        labels,
        probabilities,
    )
    default_metrics = binary_metrics(
        labels,
        (probabilities >= 0.5).astype(int),
    )
    fraction_positive, mean_predicted = calibration_curve(
        labels,
        probabilities,
        n_bins=5,
        strategy="quantile",
    )
    metrics = {
        "status": "development_only",
        "rows": len(rows),
        "queries": len(set(groups)),
        "positive_claims": int(labels.sum()),
        "negative_claims": int((labels == 0).sum()),
        "cross_validation": "StratifiedGroupKFold(n_splits=5, group=query_id)",
        "roc_auc": round(float(roc_auc_score(labels, probabilities)), 6),
        "average_precision": round(
            float(average_precision_score(labels, probabilities)),
            6,
        ),
        "brier_score": round(
            float(brier_score_loss(labels, probabilities)),
            6,
        ),
        "threshold_0_5": default_metrics,
        "zero_false_positive_threshold": round(safe_threshold, 8),
        "zero_false_positive_metrics": safe_metrics,
        "meets_development_gate": bool(
            safe_metrics["fp"] == 0 and safe_metrics["recall"] >= 0.80
        ),
        "calibration_bins": [
            {
                "mean_predicted": round(float(predicted), 6),
                "fraction_positive": round(float(observed), 6),
            }
            for predicted, observed in zip(
                mean_predicted,
                fraction_positive,
            )
        ],
    }

    final_model = make_pipeline(
        StandardScaler(),
        LogisticRegression(
            C=1.0,
            class_weight="balanced",
            max_iter=5000,
            random_state=SEED,
        ),
    )
    final_model.fit(features, labels)
    scaler: StandardScaler = final_model.named_steps["standardscaler"]
    classifier: LogisticRegression = final_model.named_steps[
        "logisticregression"
    ]
    model_payload = {
        "enabled": False,
        "status": "development_only_requires_fresh_holdout",
        "feature_names": FEATURE_NAMES,
        "scaler_mean": scaler.mean_.tolist(),
        "scaler_scale": scaler.scale_.tolist(),
        "coefficient": classifier.coef_[0].tolist(),
        "intercept": float(classifier.intercept_[0]),
        "threshold": safe_threshold,
        "embedding_model": config.embeddings.model_name,
        "embedding_dimension": dimension,
        "graph_version": config.graph_version,
        "training_rows": len(rows),
        "training_queries": len(set(groups)),
        "review_sha256": hashlib.sha256(review_path.read_bytes()).hexdigest(),
        "source_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
        "seed": SEED,
    }

    output_directory = OUTPUT_ROOT / args.run_id
    output_rows = []
    for index, row in enumerate(rows):
        output_rows.append(
            {
                "query_id": row["query_id"],
                "claim": row["claim"],
                "human_should_retain": row["label"],
                "fold": int(fold_ids[index]),
                "oof_probability": round(float(probabilities[index]), 8),
                "prediction_at_0_5": int(probabilities[index] >= 0.5),
                "prediction_at_safe_threshold": int(
                    probabilities[index] >= safe_threshold
                ),
            }
        )
    write_csv(output_directory / "oof_predictions.csv", output_rows)
    write_json(output_directory / "metrics.json", metrics)
    write_json(
        output_directory / "manifest.json",
        {
            "run_id": args.run_id,
            "review_file": str(review_path),
            "source_run": str(source_path),
            "model_output": str(args.model_output.resolve()),
            "embedding_model": config.embeddings.model_name,
            "embedding_snapshot": str(model_snapshot),
            "feature_names": FEATURE_NAMES,
            "human_labels_sent_to_external_service": False,
            "network_used": False,
            "production_enabled": False,
        },
    )
    write_json(args.model_output.resolve(), model_payload)
    print(
        json.dumps(
            {
                "status": "ok",
                "output": str(output_directory),
                "model": str(args.model_output.resolve()),
                "metrics": metrics,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
