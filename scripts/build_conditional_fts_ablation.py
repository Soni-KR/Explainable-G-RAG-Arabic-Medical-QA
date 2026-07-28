from __future__ import annotations

"""Build label-free conditional-FTS retrieval ablations from a frozen hybrid run.

This evaluation-only builder never reads relevance annotations. It replays the
current production Steps 10 and 11, triggers SQLite FTS only for partial
contexts without strong direct evidence, and writes two immutable artifacts:

1. vector + graph + conditional FTS
2. the same retrieval with a small, label-free inferred-category bonus
"""

import argparse
import hashlib
import json
import sys
from collections import defaultdict
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Any, Iterable

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from scripts.evaluation_common import load_gold_queries, macro_average, write_json, write_jsonl
from scripts.run_generation_ablation import frozen_subgraph
from scripts.run_retrieval_ablation import query_metrics, rankings
from src.config import load_final_config
from src.evaluation_metrics import efficiency_metrics
from src.step08a_normalize_query import normalize_query
from src.step09a_qa_corpus import lexical_candidates, lexical_relevance
from src.step11_build_evidence_context import build_evidence_context


ROOT = Path(__file__).resolve().parents[1]
MODES = (
    "vector_graph_conditional_fts",
    "vector_graph_conditional_fts_category_bonus",
)

# These values are frozen before evaluation and must not be tuned after results.
FTS_VARIANT_LIMIT = 20
MAX_NEW_CANDIDATES = 12
CATEGORY_BONUS = 0.05
STRONG_ANSWER_RELEVANCE = 0.75
STRONG_CONCEPT_COVERAGE = 0.75
STRONG_INTENT_SUPPORT = 0.50
STRONG_SOURCE_RELIABILITY = 0.75


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig") as handle:
        for line_number, line in enumerate(handle, start=1):
            value = line.strip()
            if not value:
                continue
            try:
                records.append(json.loads(value))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL at {path}:{line_number}") from exc
    return records


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def clean_text(value: Any) -> str:
    return str(value or "").strip()


def normalized(value: Any) -> str:
    return normalize_query(clean_text(value)).normalized_query


def stable_unique(values: Iterable[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))


def query_variants(record: dict[str, Any]) -> list[tuple[str, str]]:
    """Return three predeclared, label-free FTS query variants."""
    analysis = dict(record.get("query_analysis") or {})
    phrases = list(analysis.get("medical_phrases") or [])
    phrase_text = " ".join(
        stable_unique(
            clean_text(item.get("normalized_form") or item.get("surface_form"))
            for item in phrases
            if isinstance(item, dict)
        )
    )
    variants = (
        ("original_query", clean_text(record.get("query"))),
        ("reformulated_query", clean_text(analysis.get("reformulated_query"))),
        ("medical_phrases", phrase_text),
    )
    seen: set[str] = set()
    output: list[tuple[str, str]] = []
    for name, text in variants:
        key = normalized(text)
        if not key or key in seen:
            continue
        seen.add(key)
        output.append((name, text))
    return output


def has_strong_direct_evidence(context: Any) -> bool:
    """Use the frozen absolute Step 11 evidence gates to decide expansion."""
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


def infer_preferred_category(context: Any) -> str:
    """Infer a weak category prior from ordinary selected context only.

    This does not use the AHD reference answer, source category, human labels,
    or any expansion candidate. Mismatched context items do not vote.
    """
    votes: dict[str, float] = defaultdict(float)
    display: dict[str, str] = {}
    for item in context.evidence_items:
        if item.get("anatomy_mismatch") or item.get("unrelated_condition_mismatch"):
            continue
        category = clean_text(item.get("category"))
        category_key = normalized(category)
        if not category_key:
            continue
        display.setdefault(category_key, category)
        weight = max(0.01, float(item.get("retrieval_score") or 0.0))
        weight *= max(0.01, float(item.get("source_reliability") or 0.0))
        votes[category_key] += weight
    if not votes:
        return ""
    best_key = sorted(votes, key=lambda key: (-votes[key], key))[0]
    return display[best_key]


def collect_expansion_candidates(
    record: dict[str, Any],
    index_path: Path,
) -> list[dict[str, Any]]:
    """Run held-out-safe FTS variants and merge candidates by QA ID."""
    original_query = clean_text(record.get("query"))
    original_norm = normalized(original_query)
    merged: dict[str, dict[str, Any]] = {}
    for variant_name, variant_query in query_variants(record):
        rows = lexical_candidates(index_path, variant_query, FTS_VARIANT_LIMIT)
        for rank, row in enumerate(rows, start=1):
            qa_id = clean_text(row.get("qa_id"))
            candidate_question = clean_text(row.get("question"))
            if not qa_id or normalized(candidate_question) == original_norm:
                continue
            score = lexical_relevance(variant_query, candidate_question, rank)
            current = merged.setdefault(
                qa_id,
                {
                    **dict(row),
                    "qa_id": qa_id,
                    "best_score": 0.0,
                    "best_rank": rank,
                    "matched_variants": [],
                    "variant_ranks": {},
                },
            )
            current["best_score"] = max(float(current["best_score"]), score)
            current["best_rank"] = min(int(current["best_rank"]), rank)
            current["matched_variants"].append(variant_name)
            current["variant_ranks"][variant_name] = rank
    candidates = list(merged.values())
    candidates.sort(
        key=lambda row: (
            -float(row["best_score"]),
            -len(set(row["matched_variants"])),
            int(row["best_rank"]),
            clean_text(row["qa_id"]),
        )
    )
    return candidates


def expansion_evidence(
    row: dict[str, Any],
    *,
    preferred_category: str = "",
    use_category_bonus: bool = False,
) -> dict[str, Any]:
    qa_id = clean_text(row.get("qa_id"))
    category = clean_text(row.get("category"))
    base_score = float(row.get("best_score") or 0.0)
    category_matches = bool(
        preferred_category
        and normalized(category) == normalized(preferred_category)
    )
    bonus = CATEGORY_BONUS if use_category_bonus and category_matches else 0.0
    score = min(1.0, base_score + bonus)
    return {
        "evidence_id": f"qa::{qa_id}",
        "source_id": qa_id,
        "qa_id": qa_id,
        "text": clean_text(row.get("answer")),
        "question": clean_text(row.get("question")),
        "answer": clean_text(row.get("answer")),
        "category": category,
        "source_quality": "ahd_heldout_safe_corpus",
        "score": score,
        "relation_ids": [],
        "metadata": {
            "source_row_number": int(row.get("source_row_number") or 0),
            "source_quality": "ahd_heldout_safe_corpus",
            "retrieval_channel": "conditional_fts",
            "evidence_origin": "answer",
            "field": "answer",
            "vector_similarity": 0.0,
            "lexical_score": base_score,
            "best_variant_rank": int(row.get("best_rank") or 0),
            "matched_variants": stable_unique(row.get("matched_variants") or []),
            "variant_ranks": dict(row.get("variant_ranks") or {}),
            "variant_support_count": len(set(row.get("matched_variants") or [])),
            "corpus_version": "ahd_qa_train_v1",
            "category_bonus": bonus,
            "category_bonus_match": category_matches,
            "inferred_preferred_category": preferred_category,
        },
    }


def append_expansion(
    record: dict[str, Any],
    candidates: list[dict[str, Any]],
    *,
    preferred_category: str,
    use_category_bonus: bool,
) -> tuple[dict[str, Any], int]:
    updated = dict(record)
    evidence = [dict(item) for item in record.get("evidence", [])]
    existing = {
        clean_text(value)
        for item in evidence
        for value in (
            item.get("evidence_id"),
            item.get("source_id"),
            item.get("qa_id"),
        )
        if clean_text(value)
    }
    added = 0
    for row in candidates:
        qa_id = clean_text(row.get("qa_id"))
        if qa_id in existing or f"qa::{qa_id}" in existing:
            continue
        evidence.append(
            expansion_evidence(
                row,
                preferred_category=preferred_category,
                use_category_bonus=use_category_bonus,
            )
        )
        existing.update((qa_id, f"qa::{qa_id}"))
        added += 1
        if added >= MAX_NEW_CANDIDATES:
            break
    updated["evidence"] = evidence
    return updated, added


def context_state(context: Any) -> str:
    if not context.evidence_items:
        return "insufficient_context"
    if has_strong_direct_evidence(context):
        return "strong_direct_context"
    return "partial_context"


def aggregate_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    categories: dict[str, Any] = {}
    for category in ("entities", "evidence", "qa", "relations"):
        categories[category] = macro_average(
            [record["metrics"][category] for record in records],
            ("recall_at_5", "mrr", "ndcg_at_10"),
        )
    categories["efficiency"] = efficiency_metrics(
        [record["timings_ms"] for record in records]
    )
    categories["step11"] = {
        "query_count": len(records),
        "nonempty_context_queries": sum(
            record["final_step11_state"] != "insufficient_context"
            for record in records
        ),
        "strong_direct_context_queries": sum(
            record["final_step11_state"] == "strong_direct_context"
            for record in records
        ),
        "partial_context_queries": sum(
            record["final_step11_state"] == "partial_context"
            for record in records
        ),
        "insufficient_context_queries": sum(
            record["final_step11_state"] == "insufficient_context"
            for record in records
        ),
    }
    return categories


def build_mode(
    baseline_records: list[dict[str, Any]],
    gold_by_id: dict[str, Any],
    *,
    index_path: Path,
    use_category_bonus: bool,
    config: Any,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    output_records: list[dict[str, Any]] = []
    decisions: list[dict[str, Any]] = []
    mode = MODES[1] if use_category_bonus else MODES[0]
    for record in baseline_records:
        started = perf_counter()
        query_id = clean_text(record.get("query_id"))
        gold = gold_by_id.get(query_id)
        if gold is None:
            raise ValueError(f"Baseline query is absent from the gold cohort: {query_id}")
        analysis = dict(record.get("query_analysis") or {})
        primary_intent = clean_text(analysis.get("primary_intent")) or "unclear_intent"
        reformulated_query = clean_text(analysis.get("reformulated_query")) or clean_text(
            record.get("query")
        )
        ordinary_subgraph = frozen_subgraph(
            record,
            primary_intent,
            rerank=True,
            config=config,
        )
        ordinary_context = build_evidence_context(
            ordinary_subgraph,
            reformulated_query,
            config=config,
        )
        ordinary_nonempty = bool(ordinary_context.evidence_items)
        ordinary_direct = has_strong_direct_evidence(ordinary_context)
        trigger = ordinary_nonempty and not ordinary_direct
        preferred_category = infer_preferred_category(ordinary_context)
        candidates = (
            collect_expansion_candidates(record, index_path)
            if trigger
            else []
        )
        if trigger:
            updated, added = append_expansion(
                record,
                candidates,
                preferred_category=preferred_category,
                use_category_bonus=use_category_bonus,
            )
        else:
            updated = dict(record)
            added = 0
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
        ranked = rankings(
            # rankings() needs only the vector results for standalone entity IDs;
            # the baseline record already saved these IDs in its rankings.
            # Preserve them below and use the final subgraph for evidence/relations.
            type(
                "_BundleView",
                (),
                {"vector_results": [], "evidence": final_subgraph.evidence},
            )(),
            final_subgraph,
        )
        ranked["entity_ids"] = stable_unique(
            [
                *list((record.get("rankings") or {}).get("entity_ids") or []),
                *ranked["entity_ids"],
            ]
        )
        elapsed_ms = round((perf_counter() - started) * 1000.0, 3)
        output = dict(updated)
        output.update(
            {
                "mode": mode,
                "relations": [asdict(item) for item in final_subgraph.relations],
                "evidence": [asdict(item) for item in final_subgraph.evidence],
                "rankings": ranked,
                "metrics": query_metrics(ranked, gold),
                "conditional_fts": {
                    "triggered": trigger,
                    "trigger_rule": (
                        "ordinary_step11_context_nonempty_and_no_strong_direct_evidence"
                    ),
                    "raw_candidates_found": len(candidates),
                    "new_candidates_added": added,
                    "exact_question_excluded": True,
                    "category_bonus_enabled": use_category_bonus,
                    "category_bonus_value": CATEGORY_BONUS if use_category_bonus else 0.0,
                    "inferred_preferred_category": preferred_category,
                },
                "final_step11_context": asdict(final_context),
                "final_step11_state": context_state(final_context),
                "final_step11_evidence_count": len(final_context.evidence_items),
                "timings_ms": {
                    **dict(record.get("timings_ms") or {}),
                    "conditional_fts_step10_step11_replay": elapsed_ms,
                    "end_to_end": round(
                        float(
                            (record.get("timings_ms") or {}).get("end_to_end")
                            or 0.0
                        )
                        + elapsed_ms,
                        3,
                    ),
                },
            }
        )
        output_records.append(output)
        decisions.append(
            {
                "query_id": query_id,
                "mode": mode,
                "ordinary_step11_state": context_state(ordinary_context),
                "expansion_triggered": trigger,
                "raw_candidates_found": len(candidates),
                "new_candidates_added": added,
                "inferred_preferred_category": preferred_category,
                "final_step11_state": output["final_step11_state"],
                "final_step11_evidence_count": output["final_step11_evidence_count"],
            }
        )
    return output_records, decisions


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Build frozen label-free conditional-FTS and category-bonus "
            "retrieval ablations."
        )
    )
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--gold-file", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    baseline_path = args.baseline.resolve()
    gold_path = args.gold_file.resolve()
    output_dir = args.output_dir.resolve()
    if output_dir.exists():
        raise FileExistsError(
            "Output directory already exists; frozen ablations are never overwritten."
        )

    config = load_final_config()
    if config.graph_version != "final_v1":
        raise RuntimeError("Conditional FTS evaluation is restricted to final_v1.")
    if not config.qa_corpus.enabled:
        raise RuntimeError("The held-out-safe QA corpus is disabled.")
    index_path = Path(config.qa_corpus.index_path)
    if not index_path.exists():
        raise FileNotFoundError(f"SQLite FTS index does not exist: {index_path}")

    baseline_records = read_jsonl(baseline_path)
    gold_rows = load_gold_queries(gold_path)
    gold_by_id = {row.query_id: row for row in gold_rows}
    baseline_ids = [clean_text(row.get("query_id")) for row in baseline_records]
    if len(baseline_ids) != len(set(baseline_ids)):
        raise ValueError("Baseline retrieval contains duplicate query IDs.")
    if set(baseline_ids) != set(gold_by_id):
        raise ValueError(
            "Baseline and gold cohort query IDs differ; refusing a partial replay."
        )

    outputs: dict[str, list[dict[str, Any]]] = {}
    decisions: list[dict[str, Any]] = []
    for use_category_bonus in (False, True):
        records, mode_decisions = build_mode(
            baseline_records,
            gold_by_id,
            index_path=index_path,
            use_category_bonus=use_category_bonus,
            config=config,
        )
        mode = MODES[1] if use_category_bonus else MODES[0]
        outputs[mode] = records
        decisions.extend(mode_decisions)

    output_dir.mkdir(parents=True, exist_ok=False)
    for mode, records in outputs.items():
        write_jsonl(output_dir / f"{mode}.jsonl", records)
    write_json(
        output_dir / "metrics.json",
        {mode: aggregate_records(records) for mode, records in outputs.items()},
    )
    write_jsonl(output_dir / "decisions.jsonl", decisions)

    manifest = {
        "evaluation": "frozen_conditional_fts_ablation",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "graph_version": config.graph_version,
        "embedding_model": config.embeddings.model_name,
        "baseline_file": str(baseline_path),
        "baseline_sha256": sha256(baseline_path),
        "gold_file": str(gold_path),
        "gold_sha256": sha256(gold_path),
        "qa_index": str(index_path),
        "qa_corpus_version": config.qa_corpus.corpus_version,
        "query_count": len(baseline_records),
        "modes": list(MODES),
        "settings": {
            "fts_variant_limit": FTS_VARIANT_LIMIT,
            "max_new_candidates": MAX_NEW_CANDIDATES,
            "category_bonus": CATEGORY_BONUS,
            "category_source": "weighted ordinary Step 11 selected context",
            "exact_question_excluded": True,
        },
        "expansion_trigger": {
            "ordinary_context_must_be_nonempty": True,
            "strong_direct_evidence_must_be_absent": True,
            "strong_answer_relevance": STRONG_ANSWER_RELEVANCE,
            "strong_concept_coverage": STRONG_CONCEPT_COVERAGE,
            "strong_intent_support": STRONG_INTENT_SUPPORT,
            "strong_source_reliability": STRONG_SOURCE_RELIABILITY,
        },
        "human_relevance_labels_read": False,
        "reference_answers_used_for_retrieval": False,
        "supplemental_graph_used": False,
        "learned_reranker_used": False,
        "semantic_adjudication_used": False,
        "e5_calibrator_used": False,
    }
    write_json(output_dir / "manifest.json", manifest)
    print(
        json.dumps(
            {
                "status": "ok",
                "queries": len(baseline_records),
                "output_dir": str(output_dir),
                "modes": {
                    mode: aggregate_records(records)["step11"]
                    for mode, records in outputs.items()
                },
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
