from __future__ import annotations

"""Build a label-free frozen retrieval-v2 artifact with conditional FTS expansion."""

import argparse
import csv
import hashlib
import json
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from scripts.run_generation_ablation import frozen_subgraph
from src.config import load_final_config
from src.step09a_qa_corpus import lexical_relevance
from src.step11_build_evidence_context import build_evidence_context


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASELINE = (
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
DEFAULT_OUTPUT_DIR = (
    ROOT
    / "outputs"
    / "evaluation"
    / "retrieval"
    / "evaluation_v1_retrieval_v2_targeted_fts"
)

STRONG_ANSWER_RELEVANCE = 0.75
STRONG_CONCEPT_COVERAGE = 0.75
STRONG_INTENT_SUPPORT = 0.50
STRONG_SOURCE_RELIABILITY = 0.75
LABEL_FIELDS = (
    "relevance_label",
    "error_reason",
    "secondary_error_reason",
)


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


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def text(value: Any) -> str:
    return str(value or "").strip()


def as_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(text(value)))
    except ValueError:
        return default


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def has_strong_direct_evidence(context: Any) -> bool:
    for item in context.evidence_items:
        if bool(item.get("direct_question_anchor")):
            return True
        if (
            float(item.get("answer_relevance") or 0.0) >= STRONG_ANSWER_RELEVANCE
            and float(item.get("query_concept_coverage") or 0.0)
            >= STRONG_CONCEPT_COVERAGE
            and float(item.get("intent_support") or 0.0) >= STRONG_INTENT_SUPPORT
            and float(item.get("source_reliability") or 0.0)
            >= STRONG_SOURCE_RELIABILITY
            and not bool(item.get("anatomy_mismatch"))
            and not bool(item.get("unrelated_condition_mismatch"))
        ):
            return True
    return False


def expansion_evidence(row: dict[str, str]) -> dict[str, Any]:
    rank = max(1, as_int(row.get("expansion_rank"), default=10**9))
    query = text(row.get("original_query"))
    question = text(row.get("question"))
    answer = text(row.get("answer"))
    score = lexical_relevance(query, question, rank)
    qa_id = text(row.get("qa_id"))
    return {
        "evidence_id": f"qa::{qa_id}",
        "source_id": qa_id,
        "qa_id": qa_id,
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
            "retrieval_version": "retrieval_v2",
        },
    }


def append_expansion(
    record: dict[str, Any],
    rows: Sequence[dict[str, str]],
) -> tuple[dict[str, Any], int]:
    updated = dict(record)
    evidence = [dict(item) for item in record.get("evidence", [])]
    existing = {
        text(item.get("evidence_id")) for item in evidence
    } | {text(item.get("qa_id")) for item in evidence}
    added = 0
    for row in rows:
        qa_id = text(row.get("qa_id"))
        if not qa_id or qa_id in existing or f"qa::{qa_id}" in existing:
            continue
        evidence.append(expansion_evidence(row))
        existing.update((qa_id, f"qa::{qa_id}"))
        added += 1
    updated["evidence"] = evidence
    updated["retrieval_version"] = "retrieval_v2"
    updated["targeted_fts_expansion"] = {
        "triggered": True,
        "candidate_rows_available": len(rows),
        "new_candidates_added": added,
        "trigger": (
            "ordinary_step11_context_nonempty_and_no_strong_direct_evidence"
        ),
    }
    updated["warnings"] = list(
        dict.fromkeys(
            [
                *[str(item) for item in record.get("warnings", [])],
                (
                    "Conditional targeted FTS expansion added heldout-safe QA "
                    "candidates before production Steps 10-11."
                ),
            ]
        )
    )
    rankings = dict(record.get("rankings") or {})
    rankings["evidence_ids"] = [
        text(item.get("evidence_id") or item.get("qa_id")) for item in evidence
    ]
    rankings["qa_ids"] = list(
        dict.fromkeys(text(item.get("qa_id")) for item in evidence if item.get("qa_id"))
    )
    updated["rankings"] = rankings
    return updated, added


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build frozen retrieval_v2 without reading human relevance labels."
    )
    parser.add_argument("--baseline", type=Path, default=DEFAULT_BASELINE)
    parser.add_argument("--expansion", type=Path, default=DEFAULT_EXPANSION)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    baseline_path = args.baseline.resolve()
    expansion_path = args.expansion.resolve()
    output_dir = args.output_dir.resolve()
    output_path = output_dir / "full_hybrid_targeted_fts.jsonl"
    manifest_path = output_dir / "manifest.json"
    if output_path.exists() or manifest_path.exists():
        raise FileExistsError(
            "Retrieval-v2 output already exists; choose a new output directory. "
            "Existing artifacts are never overwritten."
        )

    records = read_jsonl(baseline_path)
    expansion_rows = read_csv(expansion_path)
    # Workflow metadata such as pending status is allowed, but actual human
    # relevance content is forbidden. None of these workflow fields are read
    # by triggering, scoring, reranking, context selection, or state assignment.
    for row in expansion_rows:
        for field in LABEL_FIELDS:
            if text(row.get(field)):
                raise ValueError(
                    f"Raw expansion row contains human annotation data: {field}"
                )

    expansion_by_query: dict[str, list[dict[str, str]]] = {}
    for row in expansion_rows:
        expansion_by_query.setdefault(text(row.get("query_id")), []).append(row)

    config = load_final_config()
    output_records: list[dict[str, Any]] = []
    decisions: list[dict[str, Any]] = []
    total_added = 0
    for record in records:
        query_id = text(record.get("query_id"))
        analysis = dict(record.get("query_analysis") or {})
        primary_intent = text(analysis.get("primary_intent")) or "unclear_intent"
        reformulated_query = text(analysis.get("reformulated_query")) or text(
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
            reformulated_query,
            config=config,
        )
        candidates = expansion_by_query.get(query_id, [])
        has_partial_context = bool(baseline_context.evidence_items)
        has_strong_direct = has_strong_direct_evidence(baseline_context)
        trigger = bool(candidates and has_partial_context and not has_strong_direct)
        if trigger:
            updated, added = append_expansion(record, candidates)
            total_added += added
        else:
            updated = dict(record)
            updated["retrieval_version"] = "retrieval_v2"
            updated["targeted_fts_expansion"] = {
                "triggered": False,
                "candidate_rows_available": len(candidates),
                "new_candidates_added": 0,
                "trigger": (
                    "ordinary_step11_context_nonempty_and_no_strong_direct_evidence"
                ),
                "reason": (
                    "no_targeted_candidates"
                    if not candidates
                    else "ordinary_context_empty"
                    if not has_partial_context
                    else "strong_direct_evidence_already_available"
                ),
            }
        final_subgraph = frozen_subgraph(
            updated,
            primary_intent,
            rerank=True,
            config=config,
        )
        final_context = build_evidence_context(
            final_subgraph,
            reformulated_query,
            config=config,
        )
        final_has_strong_direct = has_strong_direct_evidence(final_context)
        final_state = (
            "insufficient_context"
            if not final_context.evidence_items
            else "strong_direct_context"
            if final_has_strong_direct
            else "partial_context"
        )
        updated["final_step11_context"] = asdict(final_context)
        updated["final_step11_state"] = final_state
        updated["final_step11_evidence_count"] = len(final_context.evidence_items)
        output_records.append(updated)
        decisions.append(
            {
                "query_id": query_id,
                "targeted_candidates_available": len(candidates),
                "ordinary_context_items": len(baseline_context.evidence_items),
                "ordinary_has_strong_direct_evidence": has_strong_direct,
                "expansion_triggered": trigger,
                "new_candidates_added": int(
                    updated["targeted_fts_expansion"]["new_candidates_added"]
                ),
                "final_step11_state": final_state,
                "final_step11_evidence_count": len(final_context.evidence_items),
            }
        )

    output_dir.mkdir(parents=True, exist_ok=False)
    with output_path.open("w", encoding="utf-8") as handle:
        for record in output_records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    decisions_path = output_dir / "decisions.csv"
    with decisions_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(decisions[0]))
        writer.writeheader()
        writer.writerows(decisions)

    manifest = {
        "retrieval_version": "retrieval_v2",
        "graph_version": config.graph_version,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "baseline_file": str(baseline_path.relative_to(ROOT)),
        "baseline_sha256": sha256(baseline_path),
        "raw_expansion_file": str(expansion_path.relative_to(ROOT)),
        "raw_expansion_sha256": sha256(expansion_path),
        "human_labels_read": False,
        "supplemental_graph_used": False,
        "learned_reranker_used": False,
        "trigger": {
            "requires_targeted_candidates": True,
            "requires_nonempty_ordinary_context": True,
            "requires_no_strong_direct_evidence": True,
            "strong_answer_relevance": STRONG_ANSWER_RELEVANCE,
            "strong_concept_coverage": STRONG_CONCEPT_COVERAGE,
            "strong_intent_support": STRONG_INTENT_SUPPORT,
            "strong_source_reliability": STRONG_SOURCE_RELIABILITY,
        },
        "queries": len(output_records),
        "queries_with_targeted_candidates": len(expansion_by_query),
        "raw_expansion_candidates": len(expansion_rows),
        "queries_triggered": sum(item["expansion_triggered"] for item in decisions),
        "new_candidates_added": total_added,
        "runtime_retrieval_config": asdict(config.retrieval),
        "output_file": str(output_path.relative_to(ROOT)),
        "decisions_file": str(decisions_path.relative_to(ROOT)),
        "methodology_warning": (
            "This is a development artifact because targeted candidate availability "
            "was prepared for the previously identified 44-query partial-only cohort. "
            "The trigger itself is deterministic and label-free."
        ),
    }
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "retrieval_version": manifest["retrieval_version"],
                "queries": manifest["queries"],
                "queries_with_targeted_candidates": manifest[
                    "queries_with_targeted_candidates"
                ],
                "queries_triggered": manifest["queries_triggered"],
                "new_candidates_added": manifest["new_candidates_added"],
                "output_file": manifest["output_file"],
                "human_labels_read": False,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
