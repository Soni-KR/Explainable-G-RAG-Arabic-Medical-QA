from __future__ import annotations

"""Post-build validation for the frozen conditional retrieval-v2 artifact."""

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ARTIFACT_DIR = (
    ROOT
    / "outputs"
    / "evaluation"
    / "retrieval"
    / "evaluation_v1_retrieval_v2_targeted_fts"
)
DEFAULT_EXPANSION = (
    ROOT
    / "outputs"
    / "evaluation"
    / "retrieval_expansion"
    / "partial_only_fts_candidates_v1.csv"
)
DEFAULT_ANNOTATIONS = (
    ROOT / "data" / "evaluation" / "candidate_relevance_annotations_100_final.csv"
)

LABEL_FIELDS = {
    "relevance_label",
    "error_reason",
    "secondary_error_reason",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            value = line.strip()
            if not value:
                continue
            try:
                rows.append(json.loads(value))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL at {path}:{line_number}") from exc
    return rows


def text(value: Any) -> str:
    return str(value or "").strip()


def cohort_sets(rows: list[dict[str, str]]) -> tuple[set[str], set[str], set[str]]:
    grouped: dict[str, list[int]] = defaultdict(list)
    for row in rows:
        grouped[text(row.get("query_id"))].append(
            int(text(row.get("relevance_label")) or "0")
        )
    direct = {query_id for query_id, labels in grouped.items() if 2 in labels}
    partial = {
        query_id
        for query_id, labels in grouped.items()
        if 2 not in labels and 1 in labels
    }
    all_zero = {
        query_id
        for query_id, labels in grouped.items()
        if labels and max(labels) == 0
    }
    return direct, partial, all_zero


def contains_label_fields(value: Any) -> bool:
    if isinstance(value, dict):
        if LABEL_FIELDS.intersection(value):
            return True
        return any(contains_label_fields(item) for item in value.values())
    if isinstance(value, list):
        return any(contains_label_fields(item) for item in value)
    return False


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate cohort safety and Step 11 completeness for retrieval_v2."
    )
    parser.add_argument("--artifact-dir", type=Path, default=DEFAULT_ARTIFACT_DIR)
    parser.add_argument("--expansion", type=Path, default=DEFAULT_EXPANSION)
    parser.add_argument("--annotations", type=Path, default=DEFAULT_ANNOTATIONS)
    args = parser.parse_args()

    artifact_dir = args.artifact_dir.resolve()
    artifact_path = artifact_dir / "full_hybrid_targeted_fts.jsonl"
    manifest_path = artifact_dir / "manifest.json"
    decisions_path = artifact_dir / "decisions.csv"
    validation_path = artifact_dir / "validation.json"
    if validation_path.exists():
        raise FileExistsError(
            "Validation output already exists; artifacts are never overwritten."
        )

    records = read_jsonl(artifact_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    decisions = read_csv(decisions_path)
    expansion_rows = read_csv(args.expansion.resolve())
    annotations = read_csv(args.annotations.resolve())
    _, partial_only, all_zero = cohort_sets(annotations)
    target_ids = {text(row.get("query_id")) for row in expansion_rows}
    triggered_ids = {
        text(record.get("query_id"))
        for record in records
        if bool(dict(record.get("targeted_fts_expansion") or {}).get("triggered"))
    }

    checks = {
        "artifact_has_100_queries": len(records) == 100,
        "all_44_target_queries_processed": (
            len(target_ids) == 44
            and all(
                any(
                    text(record.get("query_id")) == query_id
                    and int(
                        dict(record.get("targeted_fts_expansion") or {}).get(
                            "candidate_rows_available"
                        )
                        or 0
                    )
                    > 0
                    for record in records
                )
                for query_id in target_ids
            )
        ),
        "target_cohort_matches_partial_only_queries": target_ids == partial_only,
        "only_partial_only_queries_expanded": triggered_ids.issubset(partial_only),
        "no_all_zero_queries_expanded": not bool(triggered_ids & all_zero),
        "raw_candidate_count_is_483": (
            len(expansion_rows) == 483
            and int(manifest.get("raw_expansion_candidates") or 0) == 483
        ),
        "builder_did_not_read_human_labels": manifest.get("human_labels_read") is False,
        "artifact_contains_no_relevance_fields": not any(
            contains_label_fields(record) for record in records
        ),
        "supplemental_graph_disabled": manifest.get("supplemental_graph_used") is False,
        "learned_reranker_disabled": manifest.get("learned_reranker_used") is False,
        "every_query_has_final_step11_context": all(
            isinstance(record.get("final_step11_context"), dict)
            and text(record.get("final_step11_state"))
            in {
                "strong_direct_context",
                "partial_context",
                "insufficient_context",
            }
            for record in records
        ),
        "decisions_cover_every_query": len(decisions) == len(records) == 100,
    }
    failures = sorted(name for name, passed in checks.items() if not passed)
    result = {
        "status": "ok" if not failures else "failed",
        "checks": checks,
        "failures": failures,
        "queries": len(records),
        "target_queries": len(target_ids),
        "triggered_queries": len(triggered_ids),
        "all_zero_queries": len(all_zero),
        "raw_expansion_candidates": len(expansion_rows),
        "labels_used_for_artifact_construction": False,
        "labels_used_for_postbuild_cohort_audit": True,
    }
    validation_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False))
    return 0 if not failures else 2


if __name__ == "__main__":
    raise SystemExit(main())
