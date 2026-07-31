from __future__ import annotations

"""Compare a conditional cross-encoder run with its frozen retrieval baseline."""

import argparse
import csv
import json
import statistics
import sys
from collections import Counter
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from scripts.build_conditional_fts_ablation import has_strong_direct_evidence
from scripts.select_frozen_retrieval import (
    human_pool_metrics,
    load_human_labels,
    read_jsonl,
)


class _Context:
    """Minimal adapter expected by has_strong_direct_evidence()."""

    def __init__(self, items: list[dict[str, Any]]) -> None:
        self.evidence_items = items


def context_payload(record: dict[str, Any]) -> dict[str, Any]:
    return dict(
        record.get("final_step11_context")
        or record.get("step11_context")
        or {}
    )


def context_state(record: dict[str, Any]) -> str:
    items = list(context_payload(record).get("evidence_items") or [])
    if not items:
        return "insufficient_context"
    if has_strong_direct_evidence(_Context(items)):
        return "strong_direct_context"
    return "partial_context"


def load_qa_labels(path: Path) -> dict[tuple[str, str], int]:
    """Index confirmed evidence labels without treating missing labels as zero."""
    labels: dict[tuple[str, str], int] = {}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            if str(row.get("annotation_status") or "").strip() != "human_confirmed":
                continue
            if str(row.get("candidate_type") or "").strip() != "evidence":
                continue
            label_text = str(row.get("relevance_label") or "").strip()
            query_id = str(row.get("query_id") or "").strip()
            qa_id = str(row.get("qa_id") or "").strip()
            if not query_id or not qa_id or label_text not in {"0", "1", "2"}:
                continue
            key = (query_id, qa_id)
            label = int(label_text)
            previous = labels.get(key)
            if previous is not None and previous != label:
                raise ValueError(f"Conflicting confirmed labels for {key}.")
            labels[key] = label
    return labels


def percentile(values: list[float], fraction: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, int(round((len(ordered) - 1) * fraction))))
    return ordered[index]


def summarize_context(
    records: list[dict[str, Any]],
    qa_labels: dict[tuple[str, str], int],
) -> dict[str, Any]:
    states = Counter(context_state(record) for record in records)
    selected_labels: list[int] = []
    unjudged = 0
    useful_queries: set[str] = set()
    direct_queries: set[str] = set()
    mismatch_items = Counter()
    latencies: list[float] = []
    context_sizes: list[int] = []

    for record in records:
        query_id = str(record.get("query_id") or "")
        items = list(context_payload(record).get("evidence_items") or [])
        context_sizes.append(len(items))
        latencies.append(
            float((record.get("timings_ms") or {}).get("end_to_end") or 0.0)
        )
        for item in items:
            qa_id = str(item.get("qa_id") or "")
            label = qa_labels.get((query_id, qa_id))
            if label is None:
                unjudged += 1
            else:
                selected_labels.append(label)
                if label >= 1:
                    useful_queries.add(query_id)
                if label == 2:
                    direct_queries.add(query_id)
            for field in (
                "anatomy_mismatch",
                "unrelated_condition_mismatch",
                "type_conflict",
            ):
                if str(item.get(field) or "").strip().lower() in {
                    "1",
                    "true",
                    "yes",
                }:
                    mismatch_items[field] += 1

    judged = len(selected_labels)
    useful = sum(label >= 1 for label in selected_labels)
    direct = sum(label == 2 for label in selected_labels)
    return {
        "query_count": len(records),
        "context_states": dict(sorted(states.items())),
        "mean_context_items": round(statistics.fmean(context_sizes), 6),
        "known_useful_context_queries": len(useful_queries),
        "known_direct_context_queries": len(direct_queries),
        "selected_judged_items": judged,
        "selected_unjudged_items": unjudged,
        "known_useful_precision": round(useful / judged, 6) if judged else 0.0,
        "known_direct_precision": round(direct / judged, 6) if judged else 0.0,
        "selected_mismatch_flags": dict(sorted(mismatch_items.items())),
        "latency_ms": {
            "mean": round(statistics.fmean(latencies), 6),
            "median": round(statistics.median(latencies), 6),
            "p95": round(percentile(latencies, 0.95), 6),
            "total": round(sum(latencies), 6),
        },
    }


def compare_states(
    baseline: dict[str, dict[str, Any]],
    candidate: dict[str, dict[str, Any]],
) -> dict[str, int]:
    transitions = Counter(
        f"{context_state(baseline[query_id])}->{context_state(candidate[query_id])}"
        for query_id in sorted(baseline)
    )
    return dict(sorted(transitions.items()))


def rescue_runtime(records: list[dict[str, Any]]) -> dict[str, Any]:
    audits = [dict(record.get("cross_encoder_rescue") or {}) for record in records]
    statuses = Counter(str(item.get("status") or "") for item in audits)
    triggers = Counter(str(item.get("trigger") or "") for item in audits)
    return {
        "statuses": dict(sorted(statuses.items())),
        "triggers": dict(sorted(triggers.items())),
        "successful_rescues": sum(item.get("status") == "ok" for item in audits),
        "candidate_count": sum(int(item.get("candidate_count") or 0) for item in audits),
        "rescored_count": sum(int(item.get("rescored_count") or 0) for item in audits),
        "latency_ms": round(sum(float(item.get("latency_ms") or 0.0) for item in audits), 6),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate an isolated conditional cross-encoder rescue run."
    )
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--annotations", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    baseline_rows = read_jsonl(args.baseline.resolve())
    candidate_rows = read_jsonl(args.candidate.resolve())
    baseline = {str(row.get("query_id") or ""): row for row in baseline_rows}
    candidate = {str(row.get("query_id") or ""): row for row in candidate_rows}
    if set(baseline) != set(candidate) or len(baseline) != len(baseline_rows):
        raise ValueError("Baseline and candidate cohorts do not contain identical query IDs.")

    annotations = args.annotations.resolve()
    qa_labels = load_qa_labels(annotations)
    pool_labels, direct_queries = load_human_labels(annotations)
    baseline_context = summarize_context(baseline_rows, qa_labels)
    candidate_context = summarize_context(candidate_rows, qa_labels)
    baseline_pool = human_pool_metrics(baseline_rows, pool_labels, direct_queries)
    candidate_pool = human_pool_metrics(candidate_rows, pool_labels, direct_queries)

    acceptance_checks = {
        "direct_hit_at_1_not_lower": (
            candidate_pool["confirmed_direct_hit_at_1_all_queries"]
            >= baseline_pool["confirmed_direct_hit_at_1_all_queries"]
        ),
        "direct_recall_at_5_not_lower": (
            candidate_pool["confirmed_direct_recall_at_5_answerable_queries"]
            >= baseline_pool["confirmed_direct_recall_at_5_answerable_queries"]
        ),
        "direct_recall_at_10_not_lower": (
            candidate_pool["confirmed_direct_recall_at_10_answerable_queries"]
            >= baseline_pool["confirmed_direct_recall_at_10_answerable_queries"]
        ),
        "direct_mrr_not_lower": (
            candidate_pool["confirmed_direct_mrr_all_queries"]
            >= baseline_pool["confirmed_direct_mrr_all_queries"]
        ),
        "useful_hit_at_5_not_lower": (
            candidate_pool["confirmed_useful_hit_at_5_all_queries"]
            >= baseline_pool["confirmed_useful_hit_at_5_all_queries"]
        ),
    }
    payload = {
        "status": "complete",
        "experiment": "conditional_cross_encoder_rescue",
        "baseline": str(args.baseline.resolve()),
        "candidate": str(args.candidate.resolve()),
        "annotations": str(annotations),
        "missing_labels_policy": "unavailable_not_zero",
        "baseline_context": baseline_context,
        "candidate_context": candidate_context,
        "state_transitions": compare_states(baseline, candidate),
        "baseline_human_pool": baseline_pool,
        "candidate_human_pool": candidate_pool,
        "rescue_runtime": rescue_runtime(candidate_rows),
        "acceptance_checks": acceptance_checks,
        "accepted": all(acceptance_checks.values()),
        "production_decision": (
            "enable"
            if all(acceptance_checks.values())
            else "keep_disabled"
        ),
        "supplemental_graph_used": False,
    }
    if args.output.exists():
        raise FileExistsError(f"Output already exists: {args.output}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "status": "ok",
                "accepted": payload["accepted"],
                "production_decision": payload["production_decision"],
                "output": str(args.output.resolve()),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
