from __future__ import annotations

"""Replay ranking and compact context selection on the combined human-label pool."""

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Sequence


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ANNOTATIONS = (
    ROOT / "data" / "evaluation" / "candidate_relevance_combined_pool_v1.csv"
)
DEFAULT_OOF = (
    ROOT
    / "outputs"
    / "evaluation"
    / "reranking"
    / "candidate_reranker_two_stage_v2_oof.csv"
)
DEFAULT_OUTPUT = (
    ROOT
    / "outputs"
    / "evaluation"
    / "reranking"
    / "candidate_reranker_two_stage_v2_context_replay.jsonl"
)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def text(value: Any) -> str:
    return str(value or "").strip()


def as_float(value: Any) -> float:
    try:
        return float(text(value))
    except ValueError:
        return 0.0


def as_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(text(value)))
    except ValueError:
        return default


def key(row: dict[str, str]) -> tuple[str, str, str]:
    return (
        text(row.get("query_id")),
        text(row.get("candidate_type")),
        text(row.get("candidate_id")),
    )


def normalized_baseline_score(row: dict[str, str]) -> float:
    rank = max(1, as_int(row.get("pool_rank"), default=10**9))
    pool = text(row.get("candidate_pool"))
    # Original retrieval remains the default path; targeted expansion is a fallback.
    pool_prior = 1.0 if pool == "original_pool" else 0.92
    return pool_prior / rank


def rank_rows(
    rows: Sequence[dict[str, Any]],
    mode: str,
) -> list[dict[str, Any]]:
    if mode == "baseline":
        score = lambda row: float(row["baseline_score"])
    elif mode == "model":
        score = lambda row: float(row["model_score"])
    elif mode == "blend_25":
        score = lambda row: 0.75 * float(row["baseline_score"]) + 0.25 * float(
            row["model_score"]
        )
    elif mode == "blend_50":
        score = lambda row: 0.50 * float(row["baseline_score"]) + 0.50 * float(
            row["model_score"]
        )
    else:
        raise ValueError(f"Unknown ranking mode: {mode}")
    return sorted(
        rows,
        key=lambda row: (
            score(row),
            float(row["p_direct"]),
            float(row["p_usable"]),
            -as_int(row.get("pool_rank"), default=10**9),
        ),
        reverse=True,
    )


def select_context(
    rows: Sequence[dict[str, Any]],
    *,
    mode: str,
    max_items: int,
    minimum_usable_probability: float,
) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    seen_qa: set[str] = set()
    for row in rank_rows(rows, mode):
        if text(row.get("candidate_type")) != "evidence":
            continue
        if mode != "baseline" and float(row["p_usable"]) < minimum_usable_probability:
            continue
        if not text(row.get("candidate_answer_or_evidence")):
            continue
        qa_id = text(row.get("qa_id"))
        if qa_id and qa_id in seen_qa:
            continue
        selected.append(row)
        if qa_id:
            seen_qa.add(qa_id)
        if len(selected) >= max_items:
            break
    return selected


def aggregate(records: Sequence[dict[str, Any]], mode: str) -> dict[str, Any]:
    selected_labels: list[int] = []
    useful_queries = 0
    direct_queries = 0
    context_queries = 0
    all_zero_with_context = 0
    direct_available = 0
    direct_retained = 0
    partial_only_queries = 0
    rescued_partial_only = 0
    for record in records:
        labels = list(record["pool_labels"])
        chosen = list(record[f"{mode}_selected_labels"])
        selected_labels.extend(chosen)
        context_queries += bool(chosen)
        useful_queries += any(label >= 1 for label in chosen)
        direct_queries += 2 in chosen
        all_zero_with_context += bool(labels and max(labels) == 0 and chosen)
        if 2 in labels:
            direct_available += 1
            direct_retained += 2 in chosen
        if record["original_max_label"] == 1:
            partial_only_queries += 1
            rescued_partial_only += 2 in chosen

    total = len(selected_labels)
    useful = sum(label >= 1 for label in selected_labels)
    direct = sum(label == 2 for label in selected_labels)
    return {
        "queries": len(records),
        "queries_with_context": context_queries,
        "queries_with_useful_context": useful_queries,
        "queries_with_direct_context": direct_queries,
        "all_zero_queries_with_context": all_zero_with_context,
        "selected_candidates": total,
        "selected_label_counts": {
            "0": sum(label == 0 for label in selected_labels),
            "1": sum(label == 1 for label in selected_labels),
            "2": direct,
        },
        "useful_candidate_precision": round(useful / total, 6) if total else None,
        "direct_candidate_precision": round(direct / total, 6) if total else None,
        "direct_available_queries": direct_available,
        "direct_retained_queries": direct_retained,
        "direct_retention_rate": round(direct_retained / direct_available, 6)
        if direct_available
        else None,
        "partial_only_queries": partial_only_queries,
        "expanded_direct_selected_queries": rescued_partial_only,
        "mean_selected_candidates": round(total / len(records), 6),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Replay compact context selection using combined-pool OOF scores."
    )
    parser.add_argument("--annotations", type=Path, default=DEFAULT_ANNOTATIONS)
    parser.add_argument("--oof-predictions", type=Path, default=DEFAULT_OOF)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--max-items", type=int, default=5)
    parser.add_argument("--minimum-usable-probability", type=float, default=0.50)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    annotations = read_csv(args.annotations.resolve())
    predictions = read_csv(args.oof_predictions.resolve())
    predictions_by_key = {key(row): row for row in predictions}
    if len(predictions_by_key) != len(predictions):
        raise ValueError("OOF prediction file contains duplicate candidate keys.")
    missing = [key(row) for row in annotations if key(row) not in predictions_by_key]
    extra = sorted(set(predictions_by_key) - {key(row) for row in annotations})
    if missing or extra:
        raise ValueError(
            "OOF predictions do not match the combined pool: "
            f"missing={len(missing)}, extra={len(extra)}."
        )

    original_max_by_query: dict[str, int] = defaultdict(int)
    prepared_by_query: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for source in annotations:
        row: dict[str, Any] = dict(source)
        prediction = predictions_by_key[key(source)]
        row["baseline_score"] = normalized_baseline_score(source)
        row["p_usable"] = as_float(prediction.get("p_usable"))
        row["p_direct"] = as_float(prediction.get("p_direct"))
        row["model_score"] = as_float(prediction.get("expected_relevance")) / 2.0
        query_id = text(source.get("query_id"))
        if text(source.get("candidate_pool")) == "original_pool":
            original_max_by_query[query_id] = max(
                original_max_by_query[query_id],
                as_int(source.get("relevance_label")),
            )
        prepared_by_query[query_id].append(row)

    modes = ("baseline", "blend_25", "blend_50", "model")
    records: list[dict[str, Any]] = []
    for query_id in sorted(prepared_by_query):
        rows = prepared_by_query[query_id]
        record: dict[str, Any] = {
            "query_id": query_id,
            "query": text(rows[0].get("query")),
            "original_max_label": original_max_by_query[query_id],
            "pool_labels": [as_int(row.get("relevance_label")) for row in rows],
        }
        for mode in modes:
            selected = select_context(
                rows,
                mode=mode,
                max_items=max(1, args.max_items),
                minimum_usable_probability=max(
                    0.0, min(1.0, args.minimum_usable_probability)
                ),
            )
            record[f"{mode}_selected_ids"] = [
                text(row.get("candidate_id")) for row in selected
            ]
            record[f"{mode}_selected_labels"] = [
                as_int(row.get("relevance_label")) for row in selected
            ]
            record[f"{mode}_selected_p_usable"] = [
                round(float(row["p_usable"]), 6) for row in selected
            ]
            record[f"{mode}_selected_p_direct"] = [
                round(float(row["p_direct"]), 6) for row in selected
            ]
        records.append(record)

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
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    threshold_sweep: list[dict[str, Any]] = []
    for threshold in (0.0, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60):
        sweep_records: list[dict[str, Any]] = []
        for query_id in sorted(prepared_by_query):
            rows = prepared_by_query[query_id]
            selected = select_context(
                rows,
                mode="model",
                max_items=max(1, args.max_items),
                minimum_usable_probability=threshold,
            )
            sweep_records.append(
                {
                    "pool_labels": [
                        as_int(row.get("relevance_label")) for row in rows
                    ],
                    "original_max_label": original_max_by_query[query_id],
                    "model_selected_labels": [
                        as_int(row.get("relevance_label")) for row in selected
                    ],
                }
            )
        threshold_sweep.append(
            {
                "minimum_usable_probability": threshold,
                **aggregate(sweep_records, "model"),
            }
        )

    eligible_thresholds = [
        item
        for item in threshold_sweep
        if item["direct_retained_queries"]
        >= aggregate(records, "baseline")["direct_retained_queries"]
    ]
    recommended_threshold = (
        max(
            eligible_thresholds,
            key=lambda item: (
                item["useful_candidate_precision"] or 0.0,
                -(item["all_zero_queries_with_context"] or 0),
                item["direct_retained_queries"],
            ),
        )["minimum_usable_probability"]
        if eligible_thresholds
        else None
    )

    metrics = {
        "evaluation_method": (
            "query_grouped_out_of_fold_scores_with_compact_evidence_only_selection"
        ),
        "annotations": str(args.annotations.resolve().relative_to(ROOT)),
        "oof_predictions": str(args.oof_predictions.resolve().relative_to(ROOT)),
        "max_context_items": max(1, args.max_items),
        "minimum_usable_probability": max(
            0.0, min(1.0, args.minimum_usable_probability)
        ),
        **{mode: aggregate(records, mode) for mode in modes},
        "threshold_sweep": threshold_sweep,
        "recommended_provisional_threshold": recommended_threshold,
        "threshold_note": (
            "The threshold is selected from OOF predictions and remains provisional; "
            "it must not be reported as performance on an untouched final test set."
        ),
        "activation": "disabled_pending_context_replay_decision",
    }
    metrics_path.write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(metrics, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
