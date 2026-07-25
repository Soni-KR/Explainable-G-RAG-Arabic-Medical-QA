from __future__ import annotations

"""Audit the human-labeled targeted-retrieval expansion and combined pool."""

import argparse
import csv
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable, Sequence


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ORIGINAL = (
    ROOT / "data" / "evaluation" / "candidate_relevance_annotations_100_final.csv"
)
DEFAULT_EXPANSION = (
    ROOT
    / "outputs"
    / "evaluation"
    / "retrieval_expansion"
    / "partial_only_fts_candidates_v1_annotated.csv"
)
DEFAULT_COMBINED = (
    ROOT / "data" / "evaluation" / "candidate_relevance_combined_pool_v1.csv"
)
DEFAULT_GOLD = ROOT / "data" / "evaluation" / "retrieval_gold_annotations_100.csv"
DEFAULT_OUTPUT_DIR = (
    ROOT
    / "outputs"
    / "evaluation"
    / "retrieval_expansion"
    / "combined_pool_v1_analysis"
)

LABELS = {"0", "1", "2"}
ORIGINAL_POOL = "original_pool"
EXPANSION_POOL = "partial_fts_expansion"


def read_csv(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader), list(reader.fieldnames or [])


def write_csv(path: Path, rows: Sequence[dict[str, Any]], fields: Sequence[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def text(value: Any) -> str:
    return str(value or "").strip()


def as_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(text(value)))
    except ValueError:
        return default


def mean(values: Iterable[float]) -> float | None:
    items = list(values)
    return sum(items) / len(items) if items else None


def round_metric(value: float | None) -> float | None:
    return round(value, 6) if value is not None else None


def candidate_key(row: dict[str, str]) -> tuple[str, str, str]:
    return (
        text(row.get("query_id")),
        text(row.get("candidate_type")),
        text(row.get("candidate_id")),
    )


def original_key(row: dict[str, str]) -> tuple[str, str, str]:
    return candidate_key(row)


def expansion_key(row: dict[str, str]) -> tuple[str, str]:
    return text(row.get("query_id")), text(row.get("qa_id"))


def discounted_gain(labels: Sequence[int], cutoff: int) -> float:
    return sum(
        ((2**label) - 1.0) / math.log2(rank + 2.0)
        for rank, label in enumerate(labels[:cutoff])
    )


def ranking_metrics(
    rows: Sequence[dict[str, str]],
    rank_field: str,
    *,
    cutoff: int,
) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[text(row.get("query_id"))].append(row)

    reciprocal_ranks: list[float] = []
    ndcg_values: list[float] = []
    direct_at_one = 0
    direct_at_k = 0
    useful_at_one = 0
    for query_rows in grouped.values():
        ranked = sorted(
            query_rows,
            key=lambda row: (
                as_int(row.get(rank_field), default=10**9),
                text(row.get("candidate_id")),
            ),
        )
        labels = [as_int(row.get("relevance_label"), default=0) for row in ranked]
        first_direct = next(
            (rank for rank, label in enumerate(labels, start=1) if label == 2),
            None,
        )
        reciprocal_ranks.append(1.0 / first_direct if first_direct else 0.0)
        direct_at_one += bool(labels and labels[0] == 2)
        useful_at_one += bool(labels and labels[0] >= 1)
        direct_at_k += bool(first_direct and first_direct <= cutoff)
        ideal = sorted(labels, reverse=True)
        ideal_gain = discounted_gain(ideal, cutoff)
        ndcg_values.append(
            discounted_gain(labels, cutoff) / ideal_gain if ideal_gain else 0.0
        )

    count = len(grouped)
    return {
        "queries": count,
        f"direct_recall_at_{cutoff}_all_queries": round_metric(direct_at_k / count),
        f"ndcg_at_{cutoff}_all_queries": round_metric(mean(ndcg_values)),
        "mrr_direct_all_queries": round_metric(mean(reciprocal_ranks)),
        "direct_at_rank_1_count": direct_at_one,
        "useful_at_rank_1_count": useful_at_one,
    }


def validate_and_analyze(
    original_rows: Sequence[dict[str, str]],
    expansion_rows: Sequence[dict[str, str]],
    combined_rows: Sequence[dict[str, str]],
    gold_rows: Sequence[dict[str, str]],
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    errors: list[dict[str, Any]] = []
    gold_ids = {text(row.get("query_id")) for row in gold_rows}

    original_by_key = {original_key(row): row for row in original_rows}
    combined_original = [
        row for row in combined_rows if text(row.get("candidate_pool")) == ORIGINAL_POOL
    ]
    combined_expansion = [
        row for row in combined_rows if text(row.get("candidate_pool")) == EXPANSION_POOL
    ]
    combined_original_by_key = {candidate_key(row): row for row in combined_original}

    duplicate_combined = len(combined_rows) - len(
        {candidate_key(row) for row in combined_rows}
    )
    if duplicate_combined:
        errors.append(
            {"error_type": "duplicate_combined_candidate_key", "count": duplicate_combined}
        )

    missing_original = sorted(set(original_by_key) - set(combined_original_by_key))
    extra_original = sorted(set(combined_original_by_key) - set(original_by_key))
    changed_original_labels = [
        key
        for key in set(original_by_key) & set(combined_original_by_key)
        if text(original_by_key[key].get("relevance_label"))
        != text(combined_original_by_key[key].get("relevance_label"))
    ]
    for error_type, keys in (
        ("missing_original_candidates", missing_original),
        ("extra_original_candidates", extra_original),
        ("changed_original_labels", changed_original_labels),
    ):
        if keys:
            errors.append(
                {
                    "error_type": error_type,
                    "count": len(keys),
                    "examples": json.dumps(keys[:5], ensure_ascii=False),
                }
            )

    invalid_labels = [
        candidate_key(row)
        for row in combined_rows
        if text(row.get("relevance_label")) not in LABELS
    ]
    if invalid_labels:
        errors.append(
            {
                "error_type": "invalid_or_blank_combined_labels",
                "count": len(invalid_labels),
                "examples": json.dumps(invalid_labels[:5], ensure_ascii=False),
            }
        )

    unknown_queries = sorted(
        {text(row.get("query_id")) for row in combined_rows} - gold_ids
    )
    if unknown_queries:
        errors.append(
            {
                "error_type": "combined_queries_missing_from_gold",
                "count": len(unknown_queries),
                "examples": json.dumps(unknown_queries[:5], ensure_ascii=False),
            }
        )

    raw_expansion_by_key_all = {
        expansion_key(row): row for row in expansion_rows
    }
    raw_expansion_labeled = [
        row for row in expansion_rows if text(row.get("relevance_label")) in LABELS
    ]
    raw_expansion_by_key = {expansion_key(row): row for row in raw_expansion_labeled}
    combined_expansion_by_key = {
        expansion_key(row): row for row in combined_expansion
    }
    if raw_expansion_labeled:
        missing_expansion = sorted(
            set(raw_expansion_by_key) - set(combined_expansion_by_key)
        )
        extra_expansion = sorted(
            set(combined_expansion_by_key) - set(raw_expansion_by_key)
        )
    else:
        missing_expansion = []
        extra_expansion = sorted(
            set(combined_expansion_by_key) - set(raw_expansion_by_key_all)
        )
    changed_expansion_labels = [
        key
        for key in set(raw_expansion_by_key) & set(combined_expansion_by_key)
        if text(raw_expansion_by_key[key].get("relevance_label"))
        != text(combined_expansion_by_key[key].get("relevance_label"))
    ]
    for error_type, keys in (
        ("missing_labeled_expansion_candidates", missing_expansion),
        ("extra_combined_expansion_candidates", extra_expansion),
        ("changed_expansion_labels", changed_expansion_labels),
    ):
        if keys:
            errors.append(
                {
                    "error_type": error_type,
                    "count": len(keys),
                    "examples": json.dumps(keys[:5], ensure_ascii=False),
                }
            )

    original_by_query: dict[str, list[dict[str, str]]] = defaultdict(list)
    expansion_by_query: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in combined_original:
        original_by_query[text(row.get("query_id"))].append(row)
    for row in combined_expansion:
        expansion_by_query[text(row.get("query_id"))].append(row)

    original_direct = {
        query_id
        for query_id, rows in original_by_query.items()
        if any(text(row.get("relevance_label")) == "2" for row in rows)
    }
    original_partial_only = {
        query_id
        for query_id, rows in original_by_query.items()
        if not any(text(row.get("relevance_label")) == "2" for row in rows)
        and any(text(row.get("relevance_label")) == "1" for row in rows)
    }
    original_all_zero = {
        query_id
        for query_id, rows in original_by_query.items()
        if all(text(row.get("relevance_label")) == "0" for row in rows)
    }
    expansion_queries = set(expansion_by_query)
    unexpected_expansion_queries = sorted(expansion_queries - original_partial_only)
    missing_target_queries = sorted(original_partial_only - expansion_queries)
    if unexpected_expansion_queries:
        errors.append(
            {
                "error_type": "expansion_applied_outside_partial_only_cohort",
                "count": len(unexpected_expansion_queries),
                "examples": json.dumps(unexpected_expansion_queries[:5]),
            }
        )
    if missing_target_queries:
        errors.append(
            {
                "error_type": "partial_only_queries_missing_expansion",
                "count": len(missing_target_queries),
                "examples": json.dumps(missing_target_queries[:5]),
            }
        )

    query_outcomes: list[dict[str, Any]] = []
    for query_id in sorted(original_by_query):
        original_query_rows = original_by_query[query_id]
        expansion_query_rows = expansion_by_query.get(query_id, [])
        original_max = max(
            as_int(row.get("relevance_label")) for row in original_query_rows
        )
        expansion_max = max(
            [as_int(row.get("relevance_label")) for row in expansion_query_rows],
            default=-1,
        )
        direct_rows = [
            row
            for row in expansion_query_rows
            if text(row.get("relevance_label")) == "2"
        ]
        first_direct_rank = min(
            [as_int(row.get("pool_rank"), default=10**9) for row in direct_rows],
            default=None,
        )
        if original_max == 1 and expansion_max == 2:
            outcome = "rescued_direct"
        elif original_max == 1:
            outcome = "still_partial"
        elif original_max == 2:
            outcome = "already_direct"
        else:
            outcome = "all_zero_not_targeted"
        query_outcomes.append(
            {
                "query_id": query_id,
                "query": text(original_query_rows[0].get("query")),
                "original_max_label": original_max,
                "expansion_reviewed_candidates": len(expansion_query_rows),
                "expansion_max_label": expansion_max if expansion_query_rows else "",
                "first_expansion_direct_rank": first_direct_rank or "",
                "direct_within_rank_5": bool(first_direct_rank and first_direct_rank <= 5),
                "outcome": outcome,
            }
        )

    variant_metrics: list[dict[str, Any]] = []
    for variant, field in (
        ("A", "variant_A"),
        ("B", "variant_B"),
        ("C", "variant_C"),
        ("multiple", "variant_support_count"),
    ):
        if variant == "multiple":
            selected = [
                row
                for row in combined_expansion
                if as_int(row.get(field)) >= 2
            ]
        else:
            selected = [
                row
                for row in combined_expansion
                if text(row.get(field)).lower() == "true"
            ]
        direct_queries = {
            text(row.get("query_id"))
            for row in selected
            if text(row.get("relevance_label")) == "2"
        }
        useful = sum(text(row.get("relevance_label")) in {"1", "2"} for row in selected)
        direct = sum(text(row.get("relevance_label")) == "2" for row in selected)
        variant_metrics.append(
            {
                "variant": variant,
                "reviewed_candidates": len(selected),
                "label_1_or_2": useful,
                "label_2": direct,
                "reviewed_useful_yield": round_metric(useful / len(selected))
                if selected
                else None,
                "reviewed_direct_yield": round_metric(direct / len(selected))
                if selected
                else None,
                "queries_with_label_2": len(direct_queries),
            }
        )

    rescued = [
        row for row in query_outcomes if row["outcome"] == "rescued_direct"
    ]
    still_partial = [
        row for row in query_outcomes if row["outcome"] == "still_partial"
    ]
    label_counts = {
        label: sum(text(row.get("relevance_label")) == label for row in combined_rows)
        for label in sorted(LABELS)
    }
    summary = {
        "integrity": {
            "status": "ok" if not errors else "failed",
            "errors": len(errors),
            "original_rows_preserved": len(combined_original),
            "labeled_expansion_rows_preserved": len(combined_expansion),
            "gold_queries": len(gold_ids),
            "combined_queries": len(original_by_query),
        },
        "before_expansion": {
            "queries_with_direct_candidate": len(original_direct),
            "partial_only_queries": len(original_partial_only),
            "all_zero_queries": len(original_all_zero),
        },
        "expansion": {
            "target_queries": len(expansion_queries),
            "reviewed_candidates": len(combined_expansion),
            "label_counts": {
                label: sum(
                    text(row.get("relevance_label")) == label
                    for row in combined_expansion
                )
                for label in sorted(LABELS)
            },
            "queries_rescued_to_direct": len(rescued),
            "queries_still_partial": len(still_partial),
            "rescued_within_expansion_rank_5": sum(
                bool(row["direct_within_rank_5"]) for row in rescued
            ),
            "reviewed_useful_yield": round_metric(
                sum(
                    text(row.get("relevance_label")) in {"1", "2"}
                    for row in combined_expansion
                )
                / len(combined_expansion)
            ),
            "reviewed_direct_yield": round_metric(
                sum(
                    text(row.get("relevance_label")) == "2"
                    for row in combined_expansion
                )
                / len(combined_expansion)
            ),
        },
        "after_expansion": {
            "queries_with_direct_candidate": len(original_direct) + len(rescued),
            "direct_coverage_candidate_bearing_99": round_metric(
                (len(original_direct) + len(rescued)) / len(original_by_query)
            ),
            "direct_coverage_end_to_end_100": round_metric(
                (len(original_direct) + len(rescued)) / len(gold_ids)
            ),
            "combined_label_counts": label_counts,
        },
        "ranking_by_pool_rank": {
            "original_pool_at_5": ranking_metrics(
                combined_original, "pool_rank", cutoff=5
            ),
            "combined_pool_at_5": ranking_metrics(
                combined_rows, "pool_rank", cutoff=5
            ),
            "combined_pool_at_10": ranking_metrics(
                combined_rows, "pool_rank", cutoff=10
            ),
        },
        "annotation_caveat": (
            "Expansion yield is calculated only over reviewed candidates. "
            "Unreviewed rows after stop-on-label-2 are not negatives."
        ),
    }
    return summary, query_outcomes, variant_metrics, errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit the targeted FTS expansion and combined human-label pool."
    )
    parser.add_argument("--original", type=Path, default=DEFAULT_ORIGINAL)
    parser.add_argument("--expansion", type=Path, default=DEFAULT_EXPANSION)
    parser.add_argument("--combined", type=Path, default=DEFAULT_COMBINED)
    parser.add_argument("--gold", type=Path, default=DEFAULT_GOLD)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    original_rows, _ = read_csv(args.original.resolve())
    expansion_rows, _ = read_csv(args.expansion.resolve())
    combined_rows, _ = read_csv(args.combined.resolve())
    gold_rows, _ = read_csv(args.gold.resolve())
    summary, outcomes, variant_metrics, errors = validate_and_analyze(
        original_rows,
        expansion_rows,
        combined_rows,
        gold_rows,
    )

    output_dir = args.output_dir.resolve()
    paths = {
        "summary": output_dir / "summary.json",
        "query_outcomes": output_dir / "query_outcomes.csv",
        "variant_metrics": output_dir / "variant_metrics.csv",
        "integrity_errors": output_dir / "integrity_errors.csv",
    }
    existing = [path for path in paths.values() if path.exists()]
    if existing and not args.force:
        raise FileExistsError(
            "Analysis outputs already exist; use --force to replace them: "
            + ", ".join(str(path) for path in existing)
        )
    output_dir.mkdir(parents=True, exist_ok=True)
    paths["summary"].write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    write_csv(
        paths["query_outcomes"],
        outcomes,
        (
            "query_id",
            "query",
            "original_max_label",
            "expansion_reviewed_candidates",
            "expansion_max_label",
            "first_expansion_direct_rank",
            "direct_within_rank_5",
            "outcome",
        ),
    )
    write_csv(
        paths["variant_metrics"],
        variant_metrics,
        (
            "variant",
            "reviewed_candidates",
            "label_1_or_2",
            "label_2",
            "reviewed_useful_yield",
            "reviewed_direct_yield",
            "queries_with_label_2",
        ),
    )
    write_csv(
        paths["integrity_errors"],
        errors,
        ("error_type", "count", "examples"),
    )

    print(
        json.dumps(
            {
                "integrity": summary["integrity"],
                "before_expansion": summary["before_expansion"],
                "expansion": summary["expansion"],
                "after_expansion": summary["after_expansion"],
                "output_dir": str(output_dir.relative_to(ROOT)),
            },
            ensure_ascii=False,
        )
    )
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
