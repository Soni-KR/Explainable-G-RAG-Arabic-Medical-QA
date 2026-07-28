from __future__ import annotations

"""Score five frozen retrieval variants and select one without post-hoc tuning."""

import argparse
import csv
import json
import math
import statistics
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from scripts.build_conditional_fts_ablation import has_strong_direct_evidence


MODE_FILES = {
    "vector_only": "vector_only.jsonl",
    "graph_only": "graph_only.jsonl",
    "vector_graph": "full_hybrid.jsonl",
    "vector_graph_conditional_fts": "vector_graph_conditional_fts.jsonl",
    "vector_graph_conditional_fts_category_bonus": (
        "vector_graph_conditional_fts_category_bonus.jsonl"
    ),
}


class _Context:
    def __init__(self, evidence_items: list[dict[str, Any]]) -> None:
        self.evidence_items = evidence_items


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def load_modes(primary_dir: Path, conditional_dir: Path) -> dict[str, tuple[Path, list[dict[str, Any]]]]:
    output: dict[str, tuple[Path, list[dict[str, Any]]]] = {}
    for mode, filename in MODE_FILES.items():
        root = conditional_dir if mode.startswith("vector_graph_conditional") else primary_dir
        path = root / filename
        if not path.exists():
            raise FileNotFoundError(f"Missing frozen retrieval artifact: {path}")
        output[mode] = (path, read_jsonl(path))
    expected_ids: set[str] | None = None
    for mode, (_, records) in output.items():
        ids = {str(record.get("query_id") or "") for record in records}
        if len(ids) != len(records):
            raise ValueError(f"{mode} contains duplicate or blank query IDs.")
        if expected_ids is None:
            expected_ids = ids
        elif ids != expected_ids:
            raise ValueError(f"{mode} does not contain the same frozen cohort.")
    return output


def context_payload(record: dict[str, Any]) -> dict[str, Any]:
    return dict(
        record.get("final_step11_context")
        or record.get("step11_context")
        or {}
    )


def context_metrics(records: list[dict[str, Any]]) -> dict[str, Any]:
    states = []
    counts = []
    latencies = []
    for record in records:
        payload = context_payload(record)
        items = list(payload.get("evidence_items") or [])
        context = _Context(items)
        state = (
            "insufficient_context"
            if not items
            else "strong_direct_context"
            if has_strong_direct_evidence(context)
            else "partial_context"
        )
        states.append(state)
        counts.append(len(items))
        latencies.append(float((record.get("timings_ms") or {}).get("end_to_end") or 0.0))
    return {
        "query_count": len(records),
        "strong_direct_context_queries": states.count("strong_direct_context"),
        "partial_context_queries": states.count("partial_context"),
        "insufficient_context_queries": states.count("insufficient_context"),
        "nonempty_context_queries": sum(state != "insufficient_context" for state in states),
        "mean_context_items": round(statistics.fmean(counts), 6) if counts else 0.0,
        "mean_retrieval_latency_ms": (
            round(statistics.fmean(latencies), 6) if latencies else 0.0
        ),
    }


def entity_gold_metrics(records: list[dict[str, Any]]) -> dict[str, Any]:
    computed = [
        dict((record.get("metrics") or {}).get("entities") or {})
        for record in records
        if ((record.get("metrics") or {}).get("entities") or {}).get("status")
        == "computed"
    ]
    if not computed:
        return {
            "status": "unavailable",
            "reason": "No independently annotated entity IDs were supplied.",
        }
    return {
        "status": "computed",
        "evaluated_query_count": len(computed),
        "recall_at_5": round(
            statistics.fmean(float(row["recall_at_5"]) for row in computed),
            6,
        ),
        "mrr": round(statistics.fmean(float(row["mrr"]) for row in computed), 6),
        "ndcg_at_10": round(
            statistics.fmean(float(row["ndcg_at_10"]) for row in computed),
            6,
        ),
    }


def load_human_labels(path: Path) -> tuple[dict[tuple[str, str, str], int], set[str]]:
    labels: dict[tuple[str, str, str], int] = {}
    direct_queries: set[str] = set()
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            if str(row.get("annotation_status") or "").strip() != "human_confirmed":
                continue
            query_id = str(row.get("query_id") or "").strip()
            candidate_type = str(row.get("candidate_type") or "").strip()
            candidate_id = str(row.get("candidate_id") or "").strip()
            label_text = str(row.get("relevance_label") or "").strip()
            if not query_id or not candidate_type or not candidate_id or label_text not in {"0", "1", "2"}:
                continue
            label = int(label_text)
            labels[(query_id, candidate_type, candidate_id)] = label
            if label == 2:
                direct_queries.add(query_id)
    if not labels:
        raise ValueError("The human annotation file contains no confirmed labels.")
    return labels, direct_queries


def ranked_human_candidates(record: dict[str, Any]) -> list[tuple[str, str]]:
    evidence = [
        ("evidence", str(item.get("evidence_id") or ""))
        for item in record.get("evidence", [])
        if item.get("evidence_id")
    ]
    relations = [
        (
            "relation",
            str(item.get("source_relation_id") or item.get("relation_id") or ""),
        )
        for item in record.get("relations", [])
        if item.get("source_relation_id") or item.get("relation_id")
    ]
    # All confirmed direct labels in this cohort are evidence passages. Preserve
    # each channel's production order and place relations after evidence rather
    # than inventing a cross-type score calibration.
    return [*evidence, *relations]


def discounted_gain(labels: list[int]) -> float:
    return sum((2.0**label - 1.0) / math.log2(rank + 2) for rank, label in enumerate(labels))


def human_pool_metrics(
    records: list[dict[str, Any]],
    labels: dict[tuple[str, str, str], int],
    direct_queries: set[str],
) -> dict[str, Any]:
    direct_at_1 = direct_at_5 = direct_at_10 = useful_at_1 = useful_at_5 = 0
    reciprocal_ranks: list[float] = []
    judged_ndcg: list[float] = []
    judged_count = ranked_count = 0
    for record in records:
        query_id = str(record.get("query_id") or "")
        ranked = ranked_human_candidates(record)
        ranked_count += min(10, len(ranked))
        judged = [
            (rank, labels[(query_id, kind, candidate_id)])
            for rank, (kind, candidate_id) in enumerate(ranked, start=1)
            if (query_id, kind, candidate_id) in labels
        ]
        judged_count += sum(rank <= 10 for rank, _ in judged)
        direct_ranks = [rank for rank, label in judged if label == 2]
        useful_ranks = [rank for rank, label in judged if label >= 1]
        first_direct = min(direct_ranks, default=0)
        first_useful = min(useful_ranks, default=0)
        direct_at_1 += int(first_direct == 1)
        direct_at_5 += int(0 < first_direct <= 5)
        direct_at_10 += int(0 < first_direct <= 10)
        useful_at_1 += int(first_useful == 1)
        useful_at_5 += int(0 < first_useful <= 5)
        reciprocal_ranks.append(1.0 / first_direct if first_direct else 0.0)
        judged_top10 = [label for rank, label in judged if rank <= 10]
        if judged_top10:
            ideal = sorted(
                [
                    label
                    for (qid, _, _), label in labels.items()
                    if qid == query_id
                ],
                reverse=True,
            )[: len(judged_top10)]
            denominator = discounted_gain(ideal)
            judged_ndcg.append(
                discounted_gain(judged_top10) / denominator if denominator else 0.0
            )
    query_count = len(records)
    direct_denominator = len(direct_queries)
    return {
        "status": "computed_with_incomplete_judgments",
        "query_count": query_count,
        "queries_with_confirmed_direct_candidate": direct_denominator,
        "confirmed_direct_hit_at_1_all_queries": direct_at_1,
        "confirmed_direct_hit_at_5_all_queries": direct_at_5,
        "confirmed_direct_hit_at_10_all_queries": direct_at_10,
        "confirmed_direct_recall_at_5_answerable_queries": round(
            direct_at_5 / direct_denominator,
            6,
        )
        if direct_denominator
        else 0.0,
        "confirmed_direct_recall_at_10_answerable_queries": round(
            direct_at_10 / direct_denominator,
            6,
        )
        if direct_denominator
        else 0.0,
        "confirmed_direct_mrr_all_queries": round(
            statistics.fmean(reciprocal_ranks),
            6,
        ),
        "confirmed_useful_hit_at_1_all_queries": useful_at_1,
        "confirmed_useful_hit_at_5_all_queries": useful_at_5,
        "judged_only_ndcg_at_10": round(
            statistics.fmean(judged_ndcg),
            6,
        )
        if judged_ndcg
        else 0.0,
        "top10_judgment_coverage": round(judged_count / ranked_count, 6)
        if ranked_count
        else 0.0,
        "warning": (
            "Unjudged candidates were not converted to label 0. Confirmed-hit "
            "figures are lower bounds; judged-only nDCG compresses unjudged rows."
        ),
    }


def selection_key(
    score: dict[str, Any],
    *,
    use_human_pool: bool,
) -> tuple[float, ...]:
    context = score["step11"]
    if use_human_pool:
        human = score["human_pool"]
        return (
            float(human["confirmed_direct_recall_at_5_answerable_queries"]),
            float(human["confirmed_direct_recall_at_10_answerable_queries"]),
            float(human["confirmed_direct_mrr_all_queries"]),
            float(human["confirmed_useful_hit_at_5_all_queries"]),
            float(context["strong_direct_context_queries"]),
            float(context["nonempty_context_queries"]),
            -float(context["mean_retrieval_latency_ms"]),
        )
    entity = score["entity_gold"]
    if entity.get("status") != "computed":
        raise ValueError("Entity cohort selection requires annotated entity IDs.")
    return (
        float(entity["recall_at_5"]),
        float(entity["ndcg_at_10"]),
        float(entity["mrr"]),
        float(context["strong_direct_context_queries"]),
        float(context["nonempty_context_queries"]),
        -float(context["mean_retrieval_latency_ms"]),
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Select one frozen retrieval artifact using a predeclared rule."
    )
    parser.add_argument("--cohort-name", required=True)
    parser.add_argument("--primary-dir", type=Path, required=True)
    parser.add_argument("--conditional-dir", type=Path, required=True)
    parser.add_argument("--human-annotations", type=Path, default=None)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    if args.output.exists():
        raise FileExistsError("Selection output already exists and will not be overwritten.")
    modes = load_modes(args.primary_dir.resolve(), args.conditional_dir.resolve())
    labels: dict[tuple[str, str, str], int] = {}
    direct_queries: set[str] = set()
    if args.human_annotations is not None:
        labels, direct_queries = load_human_labels(args.human_annotations.resolve())

    scores: dict[str, Any] = {}
    for mode, (path, records) in modes.items():
        scores[mode] = {
            "artifact": str(path),
            "step11": context_metrics(records),
            "entity_gold": entity_gold_metrics(records),
        }
        if labels:
            scores[mode]["human_pool"] = human_pool_metrics(
                records,
                labels,
                direct_queries,
            )

    use_human_pool = bool(labels)
    eligible_modes = list(MODE_FILES)
    category_mode = "vector_graph_conditional_fts_category_bonus"
    plain_conditional = "vector_graph_conditional_fts"
    category_primary = selection_key(
        scores[category_mode],
        use_human_pool=use_human_pool,
    )[0]
    plain_primary = selection_key(
        scores[plain_conditional],
        use_human_pool=use_human_pool,
    )[0]
    category_guard_passed = category_primary > plain_primary
    if not category_guard_passed:
        eligible_modes.remove(category_mode)

    winner = max(
        eligible_modes,
        key=lambda mode: selection_key(
            scores[mode],
            use_human_pool=use_human_pool,
        ),
    )
    payload = {
        "cohort": args.cohort_name,
        "selection_frozen_before_results": True,
        "selection_basis": (
            "confirmed human candidate relevance"
            if use_human_pool
            else "independently annotated Neo4j entity IDs"
        ),
        "selection_rule": (
            [
                "confirmed direct Recall@5 among queries with a label-2 candidate",
                "confirmed direct Recall@10",
                "confirmed direct MRR",
                "confirmed useful Hit@5",
                "strong direct Step 11 contexts",
                "non-empty Step 11 contexts",
                "lower mean latency",
            ]
            if use_human_pool
            else [
                "entity Recall@5",
                "entity nDCG@10",
                "entity MRR",
                "strong direct Step 11 contexts",
                "non-empty Step 11 contexts",
                "lower mean latency",
            ]
        ),
        "category_bonus_guard": {
            "rule": (
                "Category bonus is eligible only if it strictly improves the "
                "cohort's primary independent metric over conditional FTS."
            ),
            "passed": category_guard_passed,
        },
        "scores": scores,
        "selected_mode": winner,
        "selected_artifact": scores[winner]["artifact"],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "status": "ok",
                "cohort": args.cohort_name,
                "selected_mode": winner,
                "selected_artifact": scores[winner]["artifact"],
                "category_bonus_guard_passed": category_guard_passed,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
