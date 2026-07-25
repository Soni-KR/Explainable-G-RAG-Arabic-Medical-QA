from __future__ import annotations

"""Replay production Steps 10-11 after injecting the targeted FTS candidates."""

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any, Sequence

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from scripts.run_generation_ablation import frozen_subgraph
from src.config import load_final_config
from src.step09a_qa_corpus import lexical_relevance
from src.step11_build_evidence_context import build_evidence_context


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RETRIEVAL = (
    ROOT
    / "outputs"
    / "evaluation"
    / "retrieval"
    / "evaluation_v1_retrieval_fullhybrid_qacorpus_identityfix_100q_v1"
    / "full_hybrid.jsonl"
)
DEFAULT_EXPANSION = (
    ROOT
    / "outputs"
    / "evaluation"
    / "retrieval_expansion"
    / "partial_only_fts_candidates_v1.csv"
)
DEFAULT_COMBINED = (
    ROOT / "data" / "evaluation" / "candidate_relevance_combined_pool_v1.csv"
)
DEFAULT_OUTPUT = (
    ROOT
    / "outputs"
    / "evaluation"
    / "retrieval_expansion"
    / "targeted_fts_production_step11_replay.jsonl"
)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            value = line.strip()
            if not value:
                continue
            try:
                records.append(json.loads(value))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL at {path}:{line_number}") from exc
    return records


def text(value: Any) -> str:
    return str(value or "").strip()


def as_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(text(value)))
    except ValueError:
        return default


def evidence_id(qa_id: str) -> str:
    return f"qa::{qa_id}"


def expansion_evidence(row: dict[str, str]) -> dict[str, Any]:
    rank = max(1, as_int(row.get("expansion_rank"), default=10**9))
    query = text(row.get("original_query"))
    question = text(row.get("question"))
    answer = text(row.get("answer"))
    score = lexical_relevance(query, question, rank)
    return {
        "evidence_id": evidence_id(text(row.get("qa_id"))),
        "source_id": text(row.get("qa_id")),
        "qa_id": text(row.get("qa_id")),
        "text": answer,
        "question": question,
        "answer": answer,
        "category": text(row.get("category")),
        "source_quality": "ahd_heldout_safe_corpus",
        "score": score,
        "relation_ids": [],
        "metadata": {
            "source_row_number": as_int(row.get("source_row_number")),
            "source_quality": "ahd_heldout_safe_corpus",
            "retrieval_channel": "partial_fts_expansion",
            "vector_similarity": 0.0,
            "lexical_score": score,
            "expansion_rank": rank,
            "matched_variants": text(row.get("matched_variants")),
            "variant_support_count": as_int(row.get("variant_support_count")),
            "best_variant_rank": as_int(row.get("best_variant_rank")),
            "best_bm25_rank": text(row.get("best_bm25_rank")),
            "safety_mode": text(row.get("safety_mode")),
            "safety_reason": text(row.get("safety_reason")),
            "corpus_version": "ahd_qa_train_v1",
        },
    }


def with_expansion(
    record: dict[str, Any],
    rows: Sequence[dict[str, str]],
) -> dict[str, Any]:
    updated = dict(record)
    evidence = [dict(item) for item in record.get("evidence", [])]
    existing_ids = {
        text(item.get("evidence_id")) for item in evidence
    } | {text(item.get("qa_id")) for item in evidence}
    added = 0
    for row in rows:
        qa_id = text(row.get("qa_id"))
        if not qa_id or qa_id in existing_ids or evidence_id(qa_id) in existing_ids:
            continue
        evidence.append(expansion_evidence(row))
        existing_ids.update((qa_id, evidence_id(qa_id)))
        added += 1
    updated["evidence"] = evidence
    updated["warnings"] = [
        *[str(item) for item in record.get("warnings", [])],
        f"Development replay added {added} targeted heldout-safe FTS candidates.",
    ]
    return updated


def selected_ids(context: Any) -> list[str]:
    return [
        text(item.get("source_id") or item.get("qa_id"))
        for item in context.evidence_items
    ]


def label_for(
    query_id: str,
    source_id: str,
    labels: dict[tuple[str, str], int],
) -> int | None:
    for candidate_id in (source_id, evidence_id(source_id)):
        value = labels.get((query_id, candidate_id))
        if value is not None:
            return value
    return None


def aggregate(records: Sequence[dict[str, Any]], prefix: str) -> dict[str, Any]:
    labels: list[int] = []
    unreviewed = 0
    context_queries = 0
    useful_queries = 0
    direct_queries = 0
    all_zero_with_context = 0
    for record in records:
        selected = record[f"{prefix}_selected_labels"]
        known = [int(value) for value in selected if value is not None]
        labels.extend(known)
        unreviewed += sum(value is None for value in selected)
        context_queries += bool(selected)
        useful_queries += any(value is not None and value >= 1 for value in selected)
        direct_queries += 2 in selected
        all_zero_with_context += bool(
            record["original_max_label"] == 0 and selected
        )
    total_known = len(labels)
    return {
        "queries": len(records),
        "queries_with_context": context_queries,
        "queries_with_known_useful_context": useful_queries,
        "queries_with_known_direct_context": direct_queries,
        "all_zero_queries_with_context": all_zero_with_context,
        "known_selected_candidates": total_known,
        "unreviewed_selected_candidates": unreviewed,
        "selected_label_counts": {
            "0": sum(value == 0 for value in labels),
            "1": sum(value == 1 for value in labels),
            "2": sum(value == 2 for value in labels),
        },
        "known_useful_precision": round(
            sum(value >= 1 for value in labels) / total_known, 6
        )
        if total_known
        else None,
        "known_direct_precision": round(
            sum(value == 2 for value in labels) / total_known, 6
        )
        if total_known
        else None,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Replay actual production Steps 10-11 with targeted FTS candidates."
    )
    parser.add_argument("--retrieval-jsonl", type=Path, default=DEFAULT_RETRIEVAL)
    parser.add_argument("--expansion", type=Path, default=DEFAULT_EXPANSION)
    parser.add_argument("--combined", type=Path, default=DEFAULT_COMBINED)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    retrieval_records = read_jsonl(args.retrieval_jsonl.resolve())
    expansion_rows = read_csv(args.expansion.resolve())
    combined_rows = read_csv(args.combined.resolve())
    expansion_by_query: dict[str, list[dict[str, str]]] = {}
    for row in expansion_rows:
        expansion_by_query.setdefault(text(row.get("query_id")), []).append(row)

    labels = {
        (text(row.get("query_id")), text(row.get("candidate_id"))): as_int(
            row.get("relevance_label")
        )
        for row in combined_rows
    }
    original_max: dict[str, int] = {}
    for row in combined_rows:
        if text(row.get("candidate_pool")) != "original_pool":
            continue
        query_id = text(row.get("query_id"))
        original_max[query_id] = max(
            original_max.get(query_id, 0),
            as_int(row.get("relevance_label")),
        )

    config = load_final_config()
    records: list[dict[str, Any]] = []
    unreviewed_queue: dict[tuple[str, str], dict[str, str]] = {}
    raw_expansion_by_key = {
        (text(row.get("query_id")), text(row.get("qa_id"))): row
        for row in expansion_rows
    }
    for record in retrieval_records:
        query_id = text(record.get("query_id"))
        analysis = dict(record.get("query_analysis") or {})
        primary_intent = text(analysis.get("primary_intent")) or "unclear_intent"
        reformulated = text(analysis.get("reformulated_query")) or text(
            record.get("query")
        )

        baseline_subgraph = frozen_subgraph(
            record,
            primary_intent,
            rerank=True,
            config=config,
        )
        baseline_context = build_evidence_context(
            baseline_subgraph,
            reformulated,
            config=config,
        )
        expanded_record = with_expansion(
            record,
            expansion_by_query.get(query_id, []),
        )
        expanded_subgraph = frozen_subgraph(
            expanded_record,
            primary_intent,
            rerank=True,
            config=config,
        )
        expanded_context = build_evidence_context(
            expanded_subgraph,
            reformulated,
            config=config,
        )

        baseline_sources = selected_ids(baseline_context)
        expanded_sources = selected_ids(expanded_context)
        baseline_labels = [
            label_for(query_id, source_id, labels) for source_id in baseline_sources
        ]
        expanded_labels = [
            label_for(query_id, source_id, labels) for source_id in expanded_sources
        ]
        for source_id, label in zip(expanded_sources, expanded_labels, strict=True):
            if label is not None:
                continue
            source = raw_expansion_by_key.get((query_id, source_id))
            if source is not None:
                unreviewed_queue[(query_id, source_id)] = source
        records.append(
            {
                "query_id": query_id,
                "query": text(record.get("query")),
                "original_max_label": original_max.get(query_id, 0),
                "expansion_candidates_added": len(
                    expansion_by_query.get(query_id, [])
                ),
                "baseline_selected_ids": baseline_sources,
                "baseline_selected_labels": baseline_labels,
                "expanded_selected_ids": expanded_sources,
                "expanded_selected_labels": expanded_labels,
                "expanded_context_items": expanded_context.evidence_items,
                "expanded_context_warnings": expanded_context.warnings,
            }
        )

    output = args.output.resolve()
    metrics_path = output.with_name(f"{output.stem}_metrics.json")
    queue_path = output.with_name(f"{output.stem}_unreviewed_selected.csv")
    existing = [path for path in (output, metrics_path, queue_path) if path.exists()]
    if existing and not args.force:
        raise FileExistsError(
            "Replay outputs already exist; use --force to replace them: "
            + ", ".join(str(path) for path in existing)
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    queue_rows = list(unreviewed_queue.values())
    queue_fields = list(expansion_rows[0]) if expansion_rows else []
    with queue_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=queue_fields)
        writer.writeheader()
        writer.writerows(queue_rows)

    metrics = {
        "evaluation_method": "actual_production_step10_step11_development_replay",
        "graph_version": config.graph_version,
        "retrieval_file": str(args.retrieval_jsonl.resolve().relative_to(ROOT)),
        "expansion_file": str(args.expansion.resolve().relative_to(ROOT)),
        "baseline": aggregate(records, "baseline"),
        "targeted_expansion": aggregate(records, "expanded"),
        "unreviewed_selected_queue_rows": len(queue_rows),
        "decision": (
            "blocked_pending_human_labels"
            if queue_rows
            else "ready_for_retrieval_decision"
        ),
    }
    metrics_path.write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(metrics, ensure_ascii=False))
    return 3 if queue_rows else 0


if __name__ == "__main__":
    raise SystemExit(main())
