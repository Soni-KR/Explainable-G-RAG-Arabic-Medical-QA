from __future__ import annotations

"""Replay Step 11 with out-of-fold reranker scores and human candidate labels."""

import argparse
import json
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any, Sequence

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from scripts.run_generation_ablation import frozen_subgraph
from scripts.train_candidate_reranker import (
    confirmed_rows,
    cross_validated_two_stage_scores,
    load_query_medical_phrases,
    read_csv,
    row_features,
    validate_against_frozen_queue,
    validate_candidate_rows,
    validate_confirmed_labels,
)
from src.config import load_final_config
from src.models import RerankedSubgraph, RetrievedEvidence, RetrievedMedicalRelation
from src.step11_build_evidence_context import (
    build_evidence_context,
    select_context_evidence,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ANNOTATIONS = (
    ROOT / "data" / "evaluation" / "candidate_relevance_annotations_100_final.csv"
)
DEFAULT_FROZEN_QUEUE = (
    ROOT / "data" / "evaluation" / "candidate_relevance_annotations_100.csv"
)
DEFAULT_RETRIEVAL = (
    ROOT
    / "outputs"
    / "evaluation"
    / "retrieval"
    / "evaluation_v1_retrieval_fullhybrid_qacorpus_identityfix_100q_v1"
    / "full_hybrid.jsonl"
)
DEFAULT_OUTPUT = (
    ROOT
    / "outputs"
    / "evaluation"
    / "reranking"
    / "candidate_reranker_two_stage_v1_context_replay.jsonl"
)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            text = line.strip()
            if not text:
                continue
            try:
                records.append(json.loads(text))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL at {path}:{line_number}") from exc
    return records


def candidate_key(
    query_id: str,
    candidate_type: str,
    candidate_id: str,
) -> tuple[str, str, str]:
    return query_id, candidate_type, candidate_id


def restrict_to_labeled_pool(
    subgraph: RerankedSubgraph,
    query_id: str,
    labels: dict[tuple[str, str, str], int],
) -> RerankedSubgraph:
    evidence = [
        item
        for item in subgraph.evidence
        if candidate_key(query_id, "evidence", item.evidence_id) in labels
    ]
    relations = [
        item
        for item in subgraph.relations
        if candidate_key(
            query_id,
            "relation",
            item.source_relation_id or item.relation_id,
        )
        in labels
    ]
    return replace(subgraph, evidence=evidence, relations=relations)


def apply_model_scores(
    subgraph: RerankedSubgraph,
    query_id: str,
    model_scores: dict[tuple[str, str, str], float],
    *,
    model_weight: float = 1.0,
) -> RerankedSubgraph:
    weight = max(0.0, min(1.0, model_weight))
    evidence: list[RetrievedEvidence] = []
    for item in subgraph.evidence:
        learned_score = model_scores[
            candidate_key(query_id, "evidence", item.evidence_id)
        ]
        score = ((1.0 - weight) * item.score) + (weight * learned_score)
        evidence.append(
            replace(
                item,
                score=score,
                metadata={
                    **item.metadata,
                    "two_stage_oof_score": learned_score,
                    "two_stage_blend_weight": weight,
                },
            )
        )

    relations: list[RetrievedMedicalRelation] = []
    for item in subgraph.relations:
        relation_id = item.source_relation_id or item.relation_id
        learned_score = model_scores[
            candidate_key(query_id, "relation", relation_id)
        ]
        score = ((1.0 - weight) * item.hybrid_score) + (
            weight * learned_score
        )
        relations.append(
            replace(
                item,
                hybrid_score=score,
                metadata={
                    **item.metadata,
                    "two_stage_oof_score": learned_score,
                    "two_stage_blend_weight": weight,
                },
            )
        )

    return replace(
        subgraph,
        evidence=sorted(evidence, key=lambda item: item.score, reverse=True),
        relations=sorted(
            relations,
            key=lambda item: item.hybrid_score,
            reverse=True,
        ),
    )


def selected_candidate_ids(
    subgraph: RerankedSubgraph,
    reformulated_query: str,
    config: Any,
) -> list[tuple[str, str]]:
    selected_evidence = select_context_evidence(
        subgraph,
        reformulated_query,
        config,
    )
    context = build_evidence_context(
        subgraph,
        reformulated_query,
        config=config,
    )
    selected = [("evidence", item.evidence_id) for item in selected_evidence]
    selected.extend(
        ("relation", str(item.get("source_relation_id") or ""))
        for item in context.graph_facts
        if item.get("source_relation_id")
    )
    return selected


def available_candidate_keys(
    subgraph: RerankedSubgraph,
    query_id: str,
) -> set[tuple[str, str, str]]:
    """Return only candidates that actually exist in the replayed subgraph.

    This prevents combined-pool candidates that are absent from the supplied
    retrieval JSONL from being counted as available to Step 11.
    """
    keys = {
        candidate_key(query_id, "evidence", item.evidence_id)
        for item in subgraph.evidence
    }
    keys.update(
        candidate_key(
            query_id,
            "relation",
            item.source_relation_id or item.relation_id,
        )
        for item in subgraph.relations
    )
    return keys


def failure_diagnostics(
    records: Sequence[dict[str, Any]],
    mode: str,
) -> dict[str, Any]:
    direct_available_not_selected: list[dict[str, Any]] = []
    selected_label_zero: list[dict[str, Any]] = []
    all_zero_with_context: list[dict[str, Any]] = []

    for record in records:
        pool_ids = list(record["pool_candidate_ids"])
        pool_labels = [int(value) for value in record["pool_labels"]]
        selected_ids = list(record[f"{mode}_selected_ids"])
        selected_labels = [
            int(value) for value in record[f"{mode}_selected_labels"]
        ]

        direct_ids = [
            candidate_id
            for candidate_id, label in zip(pool_ids, pool_labels)
            if label == 2
        ]
        if direct_ids and 2 not in selected_labels:
            direct_available_not_selected.append(
                {
                    "query_id": record["query_id"],
                    "query": record["query"],
                    "available_direct_candidate_ids": direct_ids,
                    "selected_candidate_ids": selected_ids,
                    "selected_labels": selected_labels,
                }
            )

        zero_ids = [
            candidate_id
            for candidate_id, label in zip(selected_ids, selected_labels)
            if label == 0
        ]
        if zero_ids:
            selected_label_zero.append(
                {
                    "query_id": record["query_id"],
                    "query": record["query"],
                    "selected_label_zero_candidate_ids": zero_ids,
                    "selected_candidate_ids": selected_ids,
                    "selected_labels": selected_labels,
                }
            )

        if pool_labels and max(pool_labels) == 0 and selected_ids:
            all_zero_with_context.append(
                {
                    "query_id": record["query_id"],
                    "query": record["query"],
                    "selected_candidate_ids": selected_ids,
                    "selected_labels": selected_labels,
                }
            )

    return {
        "mode": mode,
        "direct_available_not_selected_count": len(
            direct_available_not_selected
        ),
        "selected_label_zero_query_count": len(selected_label_zero),
        "selected_label_zero_candidate_count": sum(
            len(item["selected_label_zero_candidate_ids"])
            for item in selected_label_zero
        ),
        "all_zero_queries_with_context_count": len(all_zero_with_context),
        "direct_available_not_selected": direct_available_not_selected,
        "selected_label_zero": selected_label_zero,
        "all_zero_with_context": all_zero_with_context,
    }


def aggregate_mode(
    records: Sequence[dict[str, Any]],
    mode: str,
) -> dict[str, Any]:
    total_selected = 0
    selected_label_counts = {"0": 0, "1": 0, "2": 0}
    context_queries = 0
    useful_context_queries = 0
    direct_context_queries = 0
    all_zero_queries_with_context = 0
    direct_available_queries = 0
    direct_retained_queries = 0

    for record in records:
        labels = [int(value) for value in record["pool_labels"]]
        selected_labels = [
            int(value) for value in record[f"{mode}_selected_labels"]
        ]
        if 2 in labels:
            direct_available_queries += 1
            if 2 in selected_labels:
                direct_retained_queries += 1
        if selected_labels:
            context_queries += 1
        if any(label >= 1 for label in selected_labels):
            useful_context_queries += 1
        if 2 in selected_labels:
            direct_context_queries += 1
        if labels and max(labels) == 0 and selected_labels:
            all_zero_queries_with_context += 1
        total_selected += len(selected_labels)
        for label in selected_labels:
            selected_label_counts[str(label)] += 1

    useful_selected = selected_label_counts["1"] + selected_label_counts["2"]
    return {
        "queries": len(records),
        "queries_with_context": context_queries,
        "queries_with_useful_context": useful_context_queries,
        "queries_with_direct_context": direct_context_queries,
        "all_zero_queries_with_context": all_zero_queries_with_context,
        "selected_candidates": total_selected,
        "selected_label_counts": selected_label_counts,
        "useful_candidate_precision": round(
            useful_selected / total_selected, 6
        )
        if total_selected
        else None,
        "direct_candidate_precision": round(
            selected_label_counts["2"] / total_selected, 6
        )
        if total_selected
        else None,
        "direct_available_queries": direct_available_queries,
        "direct_retained_queries": direct_retained_queries,
        "direct_retention_rate": round(
            direct_retained_queries / direct_available_queries, 6
        )
        if direct_available_queries
        else None,
        "mean_selected_candidates": round(total_selected / len(records), 6),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compare current Step 11 with out-of-fold two-stage reranking."
    )
    parser.add_argument("--annotations", type=Path, default=DEFAULT_ANNOTATIONS)
    parser.add_argument("--frozen-queue", type=Path, default=DEFAULT_FROZEN_QUEUE)
    parser.add_argument("--retrieval-jsonl", type=Path, default=DEFAULT_RETRIEVAL)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--folds", type=int, default=5)
    parser.add_argument("--confirmed-annotator-id", required=True)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    annotation_path = args.annotations.resolve()
    rows, fieldnames = read_csv(annotation_path)
    validate_candidate_rows(rows, fieldnames)
    validate_against_frozen_queue(
        rows,
        fieldnames,
        args.frozen_queue.resolve(),
    )
    confirmed, _, _ = confirmed_rows(
        rows,
        fieldnames,
        args.confirmed_annotator_id.strip(),
    )
    validate_confirmed_labels(confirmed)

    try:
        import numpy as np
    except ImportError as exc:
        raise RuntimeError("Context replay requires numpy.") from exc

    retrieval_path = args.retrieval_jsonl.resolve()
    phrases_by_query = load_query_medical_phrases(retrieval_path)
    x = np.asarray(
        [
            row_features(
                row,
                phrases_by_query[str(row.get("query_id") or "")],
            )
            for row in confirmed
        ],
        dtype=float,
    )
    y = np.asarray([int(row["relevance_label"]) for row in confirmed], dtype=int)
    groups = np.asarray([str(row.get("query_id") or "") for row in confirmed])
    _, _, expected_relevance, folds = cross_validated_two_stage_scores(
        x,
        y,
        groups,
        requested_folds=max(2, args.folds),
    )

    labels = {
        candidate_key(
            str(row["query_id"]),
            str(row["candidate_type"]),
            str(row["candidate_id"]),
        ): int(row["relevance_label"])
        for row in confirmed
    }
    model_scores = {
        candidate_key(
            str(row["query_id"]),
            str(row["candidate_type"]),
            str(row["candidate_id"]),
        ): float(expected_relevance[index]) / 2.0
        for index, row in enumerate(confirmed)
    }
    rows_by_query: dict[str, list[dict[str, str]]] = {}
    for row in confirmed:
        rows_by_query.setdefault(str(row["query_id"]), []).append(row)

    config = load_final_config()
    replay_records: list[dict[str, Any]] = []
    expansion_candidate_keys = {
        candidate_key(
            str(row["query_id"]),
            str(row["candidate_type"]),
            str(row["candidate_id"]),
        )
        for row in confirmed
        if str(row.get("candidate_pool") or "") != "original_pool"
    }
    expected_expansion_query_ids = {
        str(row["query_id"])
        for row in confirmed
        if str(row.get("candidate_pool") or "") != "original_pool"
    }
    available_expansion_keys: set[tuple[str, str, str]] = set()
    available_expansion_query_ids: set[str] = set()

    for retrieval_record in read_jsonl(retrieval_path):
        query_id = str(retrieval_record.get("query_id") or "")
        if query_id not in rows_by_query:
            continue
        analysis = dict(retrieval_record.get("query_analysis") or {})
        primary_intent = str(analysis.get("primary_intent") or "unclear_intent")
        reformulated_query = str(
            analysis.get("reformulated_query")
            or retrieval_record.get("query")
            or ""
        )
        baseline = frozen_subgraph(
            retrieval_record,
            primary_intent,
            rerank=True,
            config=config,
        )
        baseline = restrict_to_labeled_pool(baseline, query_id, labels)

        available_keys = available_candidate_keys(baseline, query_id)
        query_expansion_keys = available_keys & expansion_candidate_keys
        available_expansion_keys.update(query_expansion_keys)
        if query_expansion_keys:
            available_expansion_query_ids.add(query_id)

        model_subgraph = apply_model_scores(
            baseline,
            query_id,
            model_scores,
        )
        blend_25_subgraph = apply_model_scores(
            baseline,
            query_id,
            model_scores,
            model_weight=0.25,
        )
        blend_50_subgraph = apply_model_scores(
            baseline,
            query_id,
            model_scores,
            model_weight=0.50,
        )

        baseline_selected = selected_candidate_ids(
            baseline,
            reformulated_query,
            config,
        )
        model_selected = selected_candidate_ids(
            model_subgraph,
            reformulated_query,
            config,
        )
        blend_25_selected = selected_candidate_ids(
            blend_25_subgraph,
            reformulated_query,
            config,
        )
        blend_50_selected = selected_candidate_ids(
            blend_50_subgraph,
            reformulated_query,
            config,
        )

        annotated_pool_rows = rows_by_query[query_id]
        pool_rows = [
            row
            for row in annotated_pool_rows
            if candidate_key(
                query_id,
                str(row["candidate_type"]),
                str(row["candidate_id"]),
            )
            in available_keys
        ]
        replay_records.append(
            {
                "query_id": query_id,
                "query": retrieval_record.get("query", ""),
                "pool_candidate_ids": [row["candidate_id"] for row in pool_rows],
                "pool_labels": [int(row["relevance_label"]) for row in pool_rows],
                "annotated_pool_candidate_count": len(annotated_pool_rows),
                "available_candidate_count": len(pool_rows),
                "available_expansion_candidate_count": len(query_expansion_keys),
                "baseline_selected_ids": [item[1] for item in baseline_selected],
                "baseline_selected_labels": [
                    labels[candidate_key(query_id, item[0], item[1])]
                    for item in baseline_selected
                ],
                "two_stage_selected_ids": [item[1] for item in model_selected],
                "two_stage_selected_labels": [
                    labels[candidate_key(query_id, item[0], item[1])]
                    for item in model_selected
                ],
                "blend_25_selected_ids": [item[1] for item in blend_25_selected],
                "blend_25_selected_labels": [
                    labels[candidate_key(query_id, item[0], item[1])]
                    for item in blend_25_selected
                ],
                "blend_50_selected_ids": [item[1] for item in blend_50_selected],
                "blend_50_selected_labels": [
                    labels[candidate_key(query_id, item[0], item[1])]
                    for item in blend_50_selected
                ],
            }
        )

    output = args.output.resolve()
    metrics_path = output.with_name(f"{output.stem}_metrics.json")
    existing = [path for path in (output, metrics_path) if path.exists()]
    if existing and not args.force:
        raise FileExistsError(
            "Replay outputs already exist; use --force to replace them: "
            + ", ".join(str(path) for path in existing)
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        for record in replay_records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    expected_expansion_queries = len(expected_expansion_query_ids)
    available_expansion_queries = len(available_expansion_query_ids)
    replay_contains_full_targeted_expansion = (
        expected_expansion_queries == 0
        or available_expansion_queries == expected_expansion_queries
    )
    diagnostics_path = output.with_name(f"{output.stem}_failures.json")
    diagnostics = {
        "baseline": failure_diagnostics(replay_records, "baseline"),
        "blend_25_percent_model": failure_diagnostics(
            replay_records,
            "blend_25",
        ),
        "blend_50_percent_model": failure_diagnostics(
            replay_records,
            "blend_50",
        ),
        "two_stage_out_of_fold": failure_diagnostics(
            replay_records,
            "two_stage",
        ),
    }
    diagnostics_path.write_text(
        json.dumps(diagnostics, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    metrics = {
        "annotation_file": str(annotation_path.relative_to(ROOT)),
        "retrieval_file": str(retrieval_path.relative_to(ROOT)),
        "candidate_pool": "actual_labeled_candidates_present_in_retrieval_subgraph",
        "evaluation_method": "query_grouped_out_of_fold_scores_then_unchanged_step11",
        "folds": folds,
        "retrieval_input_validation": {
            "expected_expansion_candidates": len(expansion_candidate_keys),
            "available_expansion_candidates": len(available_expansion_keys),
            "expected_expansion_queries": expected_expansion_queries,
            "available_expansion_queries": available_expansion_queries,
            "full_targeted_expansion_present": replay_contains_full_targeted_expansion,
        },
        "baseline": aggregate_mode(replay_records, "baseline"),
        "blend_25_percent_model": aggregate_mode(replay_records, "blend_25"),
        "blend_50_percent_model": aggregate_mode(replay_records, "blend_50"),
        "two_stage_out_of_fold": aggregate_mode(replay_records, "two_stage"),
        "activation": (
            "disabled_wrong_retrieval_artifact_for_expansion_replay"
            if not replay_contains_full_targeted_expansion
            else "disabled_pending_step11_gate_tuning"
        ),
        "failure_diagnostics": str(diagnostics_path.relative_to(ROOT)),
    }
    metrics_path.write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                **metrics,
                "records": str(output.relative_to(ROOT)),
                "metrics": str(metrics_path.relative_to(ROOT)),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
