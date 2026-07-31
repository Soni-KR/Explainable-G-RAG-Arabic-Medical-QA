from __future__ import annotations

"""Evaluate dual-field AHD QA retrieval without rerunning Step 8 or generation.

The runner reuses frozen retrieval records, injects held-out-safe QA candidates
only for weak contexts, and replays production Steps 10 and 11. References and
human labels are read only after context selection for evaluation diagnostics.
"""

import argparse
import csv
import hashlib
import json
import os
import statistics
import subprocess
import sys
from collections import defaultdict
from dataclasses import asdict, replace
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from types import SimpleNamespace
from typing import Any, Iterable

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from scripts.build_conditional_fts_ablation import (
    has_strong_direct_evidence,
)
from scripts.run_generation_ablation import (
    frozen_subgraph,
    retrieval_plan_from_dict,
)
from src.config import AppConfig, load_final_config
from src.models import HybridRetrievalBundle, RetrievedEvidence
from src.step06_build_embedding_indexes import load_model
from src.step08a_normalize_query import normalize_query
from src.step09_hybrid_retrieval import (
    collect_evidence,
    embed_query,
)
from src.step09g_dual_qa_retrieval import (
    ANSWER_ONLY,
    DUAL_NO_SCENARIO,
    DUAL_QA_MODES,
    DUAL_WITH_SCENARIO,
    QUESTION_ONLY,
    RETRIEVAL_VERSION,
    audit_payload,
    rank_prepared_dual_results,
    search_dual_qa_corpus,
)
from src.step09f_clinical_scenario import (
    clinical_scenario_compatibility,
)
from src.step10_rerank_subgraph import rerank_subgraph
from src.step11_build_evidence_context import build_evidence_context


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = ROOT / "outputs" / "evaluation" / "retrieval"
LABEL_FILE = (
    ROOT / "data" / "evaluation"
    / "candidate_relevance_combined_pool_v2.csv"
)
COHORT_FILES = {
    "ahd_reference": (
        ROOT / "outputs" / "evaluation" / "retrieval"
        / "frozen_prod_ahd_reference_100_conditional_fts_20260728"
        / "vector_graph_conditional_fts.jsonl"
    ),
    "entity_gt": (
        ROOT / "outputs" / "evaluation" / "retrieval"
        / "frozen_prod_entity_gt_100_conditional_fts_20260728"
        / "vector_graph_conditional_fts.jsonl"
    ),
}
MODES = (
    "baseline_conditional_fts",
    QUESTION_ONLY,
    ANSWER_ONLY,
    DUAL_NO_SCENARIO,
    DUAL_WITH_SCENARIO,
)

# Frozen before this retrieval experiment. They are CLI-visible for audit, but
# the authoritative run records their exact values in the manifest.
DEFAULT_CANDIDATE_K_PER_CHANNEL = 40
DEFAULT_INJECT_TOP_K = 12


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
                raise ValueError(
                    f"Invalid JSONL at {path}:{line_number}"
                ) from exc
    return records


def write_json(path: Path, payload: Any) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def write_jsonl(path: Path, records: Iterable[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(
                json.dumps(record, ensure_ascii=False) + "\n"
            )


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_runtime() -> dict[str, Any]:
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        dirty = bool(
            subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
        )
        return {"commit": commit, "dirty": dirty}
    except (OSError, subprocess.CalledProcessError):
        return {"commit": "unavailable", "dirty": None}


def clean_text(value: Any) -> str:
    return str(value or "").strip()


def normalized(value: Any) -> str:
    return normalize_query(clean_text(value)).normalized_query


def context_state(context: dict[str, Any]) -> str:
    evidence_items = list(context.get("evidence_items") or [])
    if not evidence_items:
        return "empty_context"
    proxy = SimpleNamespace(evidence_items=evidence_items)
    return (
        "direct_context"
        if has_strong_direct_evidence(proxy)
        else "partial_context"
    )


def should_trigger_dual_retrieval(record: dict[str, Any]) -> bool:
    context = dict(
        record.get("final_step11_context")
        or record.get("step11_context")
        or {}
    )
    return context_state(context) != "direct_context"


def medical_phrases(record: dict[str, Any]) -> list[str]:
    analysis = dict(record.get("query_analysis") or {})
    return list(
        dict.fromkeys(
            clean_text(
                phrase.get("normalized_form")
                or phrase.get("surface_form")
            )
            for phrase in analysis.get("medical_phrases", [])
            if isinstance(phrase, dict)
            and clean_text(
                phrase.get("normalized_form")
                or phrase.get("surface_form")
            )
        )
    )


def evidence_key(item: RetrievedEvidence) -> tuple[str, ...]:
    question = normalized(item.question)
    answer = normalized(item.answer)
    if question and answer:
        return ("qa_content", question, answer)
    return (
        "source",
        clean_text(item.qa_id or item.source_id),
        normalized(item.text),
    )


def merge_evidence(
    existing: list[RetrievedEvidence],
    additions: list[RetrievedEvidence],
) -> list[RetrievedEvidence]:
    """Deduplicate aliases of the same AHD row and retain dual provenance."""

    merged = {evidence_key(item): item for item in existing}
    for item in additions:
        key = evidence_key(item)
        current = merged.get(key)
        if current is None:
            merged[key] = item
            continue
        # Prefer the independently scored question/answer representation when
        # both objects describe exactly the same AHD row.
        if clean_text(item.metadata.get("retrieval_channel")).startswith(
            "dual_qa::"
        ):
            merged[key] = item
    return list(merged.values())


def screen_merged_evidence(
    evidence: list[RetrievedEvidence],
    *,
    query: str,
    primary_intent: str,
    query_medical_phrases: list[str],
    enabled: bool,
) -> tuple[list[RetrievedEvidence], int, int]:
    """Annotate every QA passage and reject explicit conflicts when enabled."""

    screened: list[RetrievedEvidence] = []
    hard_conflicts_rejected = 0
    exact_questions_rejected = 0
    query_norm = normalized(query)
    for item in evidence:
        metadata = dict(item.metadata)
        if item.question:
            scenario = clinical_scenario_compatibility(
                query,
                item.question,
                primary_intent=primary_intent,
                query_medical_phrases=query_medical_phrases,
            )
            metadata.update(
                {
                    "scenario_score": scenario.score,
                    "scenario_hard_conflict": (
                        scenario.hard_conflict
                    ),
                    "scenario_conflicts": scenario.conflicts,
                    "scenario_matches": scenario.matches,
                    "scenario_dimensions": scenario.dimensions,
                }
            )
            if (
                enabled
                and query_norm
                and normalized(item.question) == query_norm
            ):
                exact_questions_rejected += 1
                continue
            if enabled and scenario.hard_conflict:
                hard_conflicts_rejected += 1
                continue
        screened.append(replace(item, metadata=metadata))
    return (
        screened,
        hard_conflicts_rejected,
        exact_questions_rejected,
    )


def enrich_context_diagnostics(
    context: dict[str, Any],
    evidence: list[RetrievedEvidence],
) -> dict[str, Any]:
    """Copy retrieval audit fields into selected context for inspection."""

    metadata_by_key: dict[str, dict[str, Any]] = {}
    for item in evidence:
        metadata = dict(item.metadata)
        for key in (item.qa_id, item.source_id):
            if key:
                metadata_by_key[clean_text(key)] = metadata
    enriched = dict(context)
    items = []
    for raw_item in context.get("evidence_items", []):
        item = dict(raw_item)
        metadata = metadata_by_key.get(
            clean_text(item.get("qa_id"))
        ) or metadata_by_key.get(clean_text(item.get("source_id"))) or {}
        for field in (
            "retrieval_channel",
            "question_channel_score",
            "answer_channel_score",
            "question_vector_similarity",
            "answer_vector_similarity",
            "scenario_score",
            "scenario_hard_conflict",
            "scenario_conflicts",
            "scenario_matches",
            "scenario_dimensions",
        ):
            if field in metadata:
                item[field] = metadata[field]
        items.append(item)
    enriched["evidence_items"] = items
    return enriched


def build_mode_record(
    frozen_record: dict[str, Any],
    *,
    mode: str,
    dual_results: list[Any],
    dual_audit: dict[str, Any],
    config: AppConfig,
    shared_retrieval_ms: float,
) -> dict[str, Any]:
    analysis = dict(frozen_record.get("query_analysis") or {})
    primary_intent = clean_text(analysis.get("primary_intent"))
    plan = retrieval_plan_from_dict(
        dict(frozen_record.get("retrieval_plan") or {})
    )
    base = frozen_subgraph(
        frozen_record,
        primary_intent,
        rerank=False,
        config=config,
    )
    additions = collect_evidence(
        [],
        dual_results,
        max(config.retrieval.context_top_k * 2, len(dual_results)),
    )
    merged = merge_evidence(base.evidence, additions)
    merged, existing_hard_rejections, exact_rejections = (
        screen_merged_evidence(
            merged,
            query=base.query,
            primary_intent=primary_intent,
            query_medical_phrases=base.query_medical_phrases,
            enabled=mode == DUAL_WITH_SCENARIO,
        )
    )
    bundle = HybridRetrievalBundle(
        query=base.query,
        normalized_query=clean_text(
            analysis.get("normalized_query")
        ),
        reformulated_query=plan.reformulated_query,
        plan=plan,
        query_medical_phrases=base.query_medical_phrases,
        relations=base.relations,
        evidence=merged,
        warnings=[
            *base.warnings,
            (
                f"Dual QA retrieval mode {mode} used separate source-question "
                "and source-answer scores."
            ),
        ],
    )
    started = perf_counter()
    reranked = rerank_subgraph(bundle, config=config)
    context = build_evidence_context(
        reranked,
        plan.reformulated_query,
        config=config,
    )
    replay_ms = (perf_counter() - started) * 1000.0
    context_payload = enrich_context_diagnostics(
        asdict(context),
        reranked.evidence,
    )
    enriched_audit = dict(dual_audit)
    enriched_audit.update(
        {
            "merged_pool_hard_conflicts_rejected": (
                existing_hard_rejections
            ),
            "merged_pool_exact_questions_rejected": (
                exact_rejections
            ),
        }
    )
    payload = dict(frozen_record)
    payload.update(
        {
            "mode": mode,
            "retrieval_experiment": RETRIEVAL_VERSION,
            "relations": [
                asdict(item) for item in bundle.relations
            ],
            "evidence": [
                asdict(item) for item in bundle.evidence
            ],
            "final_step11_context": context_payload,
            "final_step11_state": context_state(context_payload),
            "final_step11_evidence_count": len(
                context.evidence_items
            ),
            "dual_qa": {
                "triggered": True,
                "audit": enriched_audit,
                "new_candidates_injected": len(additions),
                "supplemental_graph_enabled": False,
                "reference_used_for_retrieval": False,
                "human_labels_used_for_retrieval": False,
            },
            "timings_ms": {
                **dict(frozen_record.get("timings_ms") or {}),
                "dual_qa_shared_retrieval": round(
                    shared_retrieval_ms,
                    3,
                ),
                "dual_qa_step10_step11_replay": round(
                    replay_ms,
                    3,
                ),
            },
        }
    )
    return payload


def unchanged_mode_record(
    frozen_record: dict[str, Any],
    *,
    mode: str,
    reason: str,
) -> dict[str, Any]:
    payload = dict(frozen_record)
    context = dict(
        payload.get("final_step11_context")
        or payload.get("step11_context")
        or {}
    )
    payload.update(
        {
            "mode": mode,
            "retrieval_experiment": RETRIEVAL_VERSION,
            "final_step11_context": context,
            "final_step11_state": context_state(context),
            "final_step11_evidence_count": len(
                context.get("evidence_items") or []
            ),
            "dual_qa": {
                "triggered": False,
                "reason": reason,
                "supplemental_graph_enabled": False,
                "reference_used_for_retrieval": False,
                "human_labels_used_for_retrieval": False,
            },
        }
    )
    return payload


def load_human_labels(
    path: Path,
) -> dict[tuple[str, str], int]:
    if not path.exists():
        return {}
    labels: dict[tuple[str, str], int] = {}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            # A QA can support several graph relations with independent
            # labels. Step 11 evidence items are evaluated only against the
            # human-labelled evidence candidate for that QA, never against a
            # relation label that happens to share its qa_id.
            if clean_text(row.get("candidate_type")) != "evidence":
                continue
            query_id = clean_text(row.get("query_id"))
            qa_id = clean_text(row.get("qa_id"))
            raw_label = clean_text(row.get("relevance_label"))
            if not query_id or not qa_id or raw_label not in {"0", "1", "2"}:
                continue
            key = (query_id, qa_id)
            value = int(raw_label)
            existing = labels.get(key)
            if existing is not None and existing != value:
                raise ValueError(
                    f"Inconsistent human label for {query_id}/{qa_id}"
                )
            labels[key] = value
    return labels


def dot(left: Any, right: Any) -> float:
    left_values = (
        left.tolist() if hasattr(left, "tolist") else list(left)
    )
    right_values = (
        right.tolist() if hasattr(right, "tolist") else list(right)
    )
    return max(
        0.0,
        min(
            1.0,
            sum(
                float(a) * float(b)
                for a, b in zip(
                    left_values,
                    right_values,
                    strict=True,
                )
            ),
        ),
    )


def add_post_selection_diagnostics(
    query_records: dict[str, dict[str, Any]],
    *,
    model: Any,
    human_labels: dict[tuple[str, str], int],
) -> None:
    """Attach evaluation-only diagnostics after every context is frozen."""

    first = next(iter(query_records.values()))
    query_id = clean_text(first.get("query_id"))
    query = clean_text(first.get("query"))
    reference = clean_text(
        dict(first.get("gold") or {}).get("reference_answer")
    )
    texts: list[str] = [
        f"query: {query}",
        f"query: {reference or query}",
    ]
    keys: list[tuple[str, str, str]] = []
    for mode, record in query_records.items():
        context = dict(record.get("final_step11_context") or {})
        for item in context.get("evidence_items", []):
            source_question = clean_text(item.get("source_question"))
            source_answer = clean_text(
                item.get("source_answer")
                or item.get("evidence")
            )
            keys.append((mode, source_question, source_answer))
            texts.extend(
                [
                    f"passage: {source_question or ' '}",
                    f"passage: {source_answer or ' '}",
                ]
            )
    vectors = model.encode(
        texts,
        batch_size=32,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    query_vector = vectors[0]
    reference_vector = vectors[1]
    offset = 2
    mode_scores: dict[str, dict[str, list[float]]] = defaultdict(
        lambda: {"question": [], "answer": []}
    )
    for mode, _question, _answer in keys:
        mode_scores[mode]["question"].append(
            dot(query_vector, vectors[offset])
        )
        mode_scores[mode]["answer"].append(
            dot(reference_vector, vectors[offset + 1])
        )
        offset += 2

    for mode, record in query_records.items():
        context = dict(record.get("final_step11_context") or {})
        evidence_items = list(context.get("evidence_items") or [])
        labelled: list[int] = []
        for item in evidence_items:
            qa_id = clean_text(item.get("qa_id"))
            label = human_labels.get((query_id, qa_id))
            if label is not None:
                labelled.append(label)
        question_scores = mode_scores[mode]["question"]
        answer_scores = mode_scores[mode]["answer"]
        exact_leaks = sum(
            1
            for item in evidence_items
            if normalized(item.get("source_question"))
            == normalized(query)
        )
        hard_conflicts = sum(
            1
            for item in evidence_items
            if bool(
                dict(item).get("scenario_hard_conflict")
                or dict(item).get("metadata", {}).get(
                    "scenario_hard_conflict"
                )
            )
        )
        record["post_selection_diagnostics"] = {
            "reference_used_for_scoring_only": True,
            "human_labels_used_for_scoring_only": True,
            "source_question_similarity_max": (
                round(max(question_scores), 6)
                if question_scores
                else None
            ),
            "source_question_similarity_mean": (
                round(statistics.fmean(question_scores), 6)
                if question_scores
                else None
            ),
            "reference_answer_similarity_max": (
                round(max(answer_scores), 6)
                if answer_scores and reference
                else None
            ),
            "reference_answer_similarity_mean": (
                round(statistics.fmean(answer_scores), 6)
                if answer_scores and reference
                else None
            ),
            "known_label_count": len(labelled),
            "known_useful_count": sum(
                label >= 1 for label in labelled
            ),
            "known_direct_count": sum(
                label == 2 for label in labelled
            ),
            "unlabelled_selected_count": (
                len(evidence_items) - len(labelled)
            ),
            "exact_source_question_leaks": exact_leaks,
            "selected_hard_scenario_conflicts": hard_conflicts,
        }


def percentile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def summarize_mode(
    records: list[dict[str, Any]],
) -> dict[str, Any]:
    contexts = [
        dict(record.get("final_step11_context") or {})
        for record in records
    ]
    diagnostics = [
        dict(record.get("post_selection_diagnostics") or {})
        for record in records
    ]
    retrieval_latencies = [
        float(
            dict(record.get("timings_ms") or {}).get(
                "dual_qa_shared_retrieval"
            )
            or 0.0
        )
        + float(
            dict(record.get("timings_ms") or {}).get(
                "dual_qa_step10_step11_replay"
            )
            or 0.0
        )
        for record in records
    ]
    labelled_total = sum(
        int(item.get("known_label_count") or 0)
        for item in diagnostics
    )
    labelled_useful = sum(
        int(item.get("known_useful_count") or 0)
        for item in diagnostics
    )
    labelled_direct = sum(
        int(item.get("known_direct_count") or 0)
        for item in diagnostics
    )
    reference_max = [
        float(item["reference_answer_similarity_max"])
        for item in diagnostics
        if item.get("reference_answer_similarity_max") is not None
    ]
    question_max = [
        float(item["source_question_similarity_max"])
        for item in diagnostics
        if item.get("source_question_similarity_max") is not None
    ]
    return {
        "query_count": len(records),
        "triggered_query_count": sum(
            bool(dict(record.get("dual_qa") or {}).get("triggered"))
            for record in records
        ),
        "nonempty_context_queries": sum(
            bool(context.get("evidence_items"))
            for context in contexts
        ),
        "direct_context_queries": sum(
            context_state(context) == "direct_context"
            for context in contexts
        ),
        "selected_evidence_items": sum(
            len(context.get("evidence_items") or [])
            for context in contexts
        ),
        "exact_source_question_leaks": sum(
            int(item.get("exact_source_question_leaks") or 0)
            for item in diagnostics
        ),
        "selected_hard_scenario_conflicts": sum(
            int(
                item.get("selected_hard_scenario_conflicts")
                or 0
            )
            for item in diagnostics
        ),
        "known_label_evaluation": {
            "status": (
                "available_for_overlapping_candidates_only"
                if labelled_total
                else "unavailable"
            ),
            "labelled_selected_count": labelled_total,
            "useful_precision": (
                round(labelled_useful / labelled_total, 6)
                if labelled_total
                else None
            ),
            "direct_precision": (
                round(labelled_direct / labelled_total, 6)
                if labelled_total
                else None
            ),
            "missing_labels_are_not_zero": True,
        },
        "reference_answer_semantic_proxy": {
            "status": (
                "dataset_reference_proxy_not_independent_gold"
                if reference_max
                else "unavailable"
            ),
            "mean_max_similarity": (
                round(statistics.fmean(reference_max), 6)
                if reference_max
                else None
            ),
            "queries_at_or_above_0_80": sum(
                value >= 0.80 for value in reference_max
            ),
        },
        "source_question_scenario_proxy": {
            "mean_max_similarity": (
                round(statistics.fmean(question_max), 6)
                if question_max
                else None
            ),
        },
        "latency_ms": {
            "mean": (
                round(statistics.fmean(retrieval_latencies), 3)
                if retrieval_latencies
                else 0.0
            ),
            "median": (
                round(statistics.median(retrieval_latencies), 3)
                if retrieval_latencies
                else 0.0
            ),
            "p95": (
                round(percentile(retrieval_latencies, 0.95), 3)
                if retrieval_latencies
                else 0.0
            ),
            "total": round(sum(retrieval_latencies), 3),
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate separate AHD source-question/source-answer retrieval "
            "against frozen Steps 8–9 inputs."
        )
    )
    parser.add_argument(
        "--cohort",
        choices=(*COHORT_FILES, "all"),
        default="all",
    )
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument(
        "--candidate-k-per-channel",
        type=int,
        default=DEFAULT_CANDIDATE_K_PER_CHANNEL,
    )
    parser.add_argument(
        "--inject-top-k",
        type=int,
        default=DEFAULT_INJECT_TOP_K,
    )
    parser.add_argument(
        "--baseline-state",
        choices=("all", "empty_context", "partial_context"),
        default="all",
        help="Optionally evaluate only one frozen Step 11 context state.",
    )
    parser.add_argument(
        "--allow-model-download",
        action="store_true",
        help="Allow Hugging Face network access instead of local-cache-only loading.",
    )
    parser.add_argument("--run-id", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    output_dir = OUTPUT_ROOT / args.run_id
    if output_dir.exists():
        raise FileExistsError(
            f"Run already exists and will not be overwritten: {output_dir}"
        )

    selected_cohorts = (
        list(COHORT_FILES)
        if args.cohort == "all"
        else [args.cohort]
    )
    config = load_final_config()
    if not args.allow_model_download:
        os.environ.setdefault("HF_HUB_OFFLINE", "1")
        os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
    model, device, dimension = load_model(
        config.embeddings.model_name,
        config.embeddings.dimension,
    )
    human_labels = load_human_labels(LABEL_FILE)
    # Reserve the immutable run directory only after heavyweight local model
    # initialization and evaluation-data validation both succeed.
    output_dir.mkdir(parents=True)
    records_by_mode: dict[str, list[dict[str, Any]]] = {
        mode: [] for mode in MODES
    }
    cohort_metrics: dict[str, Any] = {}
    processed = 0

    for cohort in selected_cohorts:
        source_file = COHORT_FILES[cohort]
        frozen_records = read_jsonl(source_file)
        if args.baseline_state != "all":
            frozen_records = [
                record
                for record in frozen_records
                if context_state(
                    dict(
                        record.get("final_step11_context")
                        or record.get("step11_context")
                        or {}
                    )
                )
                == args.baseline_state
            ]
        if args.limit > 0:
            frozen_records = frozen_records[: args.limit]
        cohort_mode_records: dict[
            str,
            list[dict[str, Any]],
        ] = {mode: [] for mode in MODES}

        for index, frozen_record in enumerate(
            frozen_records,
            start=1,
        ):
            processed += 1
            query_id = clean_text(frozen_record.get("query_id"))
            query = clean_text(frozen_record.get("query"))
            analysis = dict(
                frozen_record.get("query_analysis") or {}
            )
            baseline = unchanged_mode_record(
                frozen_record,
                mode="baseline_conditional_fts",
                reason="frozen baseline",
            )
            per_query: dict[str, dict[str, Any]] = {
                "baseline_conditional_fts": baseline
            }

            if should_trigger_dual_retrieval(frozen_record):
                reformulated_query = clean_text(
                    analysis.get("reformulated_query")
                ) or query
                query_embedding, _ = embed_query(
                    reformulated_query,
                    config,
                    model=model,
                )
                started = perf_counter()
                prepared, prepared_audit = search_dual_qa_corpus(
                    original_query=query,
                    reformulated_query=reformulated_query,
                    primary_intent=clean_text(
                        analysis.get("primary_intent")
                    ),
                    query_medical_phrases=medical_phrases(
                        frozen_record
                    ),
                    query_embedding=query_embedding,
                    model=model,
                    config=config,
                    mode=DUAL_NO_SCENARIO,
                    top_k=max(
                        2 * args.candidate_k_per_channel,
                        args.inject_top_k,
                    ),
                    candidate_k_per_channel=(
                        args.candidate_k_per_channel
                    ),
                    exclude_exact_question=True,
                )
                shared_ms = (perf_counter() - started) * 1000.0
                expected_prepared = (
                    prepared_audit.union_rows
                    - prepared_audit.exact_questions_excluded
                )
                if len(prepared) != expected_prepared:
                    raise RuntimeError(
                        "Prepared dual QA pool was truncated; increase the "
                        "preparation top_k before evaluating modes."
                    )
                for mode in DUAL_QA_MODES:
                    results, audit = rank_prepared_dual_results(
                        prepared,
                        prepared_audit,
                        mode=mode,
                        top_k=args.inject_top_k,
                    )
                    per_query[mode] = build_mode_record(
                        frozen_record,
                        mode=mode,
                        dual_results=results,
                        dual_audit=audit_payload(audit),
                        config=config,
                        shared_retrieval_ms=shared_ms,
                    )
            else:
                for mode in DUAL_QA_MODES:
                    per_query[mode] = unchanged_mode_record(
                        frozen_record,
                        mode=mode,
                        reason=(
                            "Frozen Step 11 already contained strong direct "
                            "evidence."
                        ),
                    )

            add_post_selection_diagnostics(
                per_query,
                model=model,
                human_labels=(
                    human_labels
                    if cohort == "ahd_reference"
                    else {}
                ),
            )
            for mode, record in per_query.items():
                record["cohort"] = cohort
                cohort_mode_records[mode].append(record)
                records_by_mode[mode].append(record)
            print(
                json.dumps(
                    {
                        "status": "ok",
                        "cohort": cohort,
                        "progress": (
                            f"{index}/{len(frozen_records)}"
                        ),
                        "query_id": query_id,
                        "triggered": should_trigger_dual_retrieval(
                            frozen_record
                        ),
                        "baseline_state": (
                            baseline["final_step11_state"]
                        ),
                        "scenario_state": (
                            per_query[DUAL_WITH_SCENARIO][
                                "final_step11_state"
                            ]
                        ),
                    },
                    ensure_ascii=False,
                ),
                flush=True,
            )

        cohort_metrics[cohort] = {
            mode: summarize_mode(records)
            for mode, records in cohort_mode_records.items()
        }

    metrics = {
        "retrieval_experiment": RETRIEVAL_VERSION,
        "cohorts": cohort_metrics,
        "aggregate": {
            mode: summarize_mode(records)
            for mode, records in records_by_mode.items()
        },
        "interpretation_rules": {
            "references_used_only_after_context_selection": True,
            "human_labels_used_only_after_context_selection": True,
            "missing_human_labels_are_unavailable_not_zero": True,
            "semantic_reference_scores_are_proxies": True,
            "generation_was_not_run": True,
        },
    }
    for mode, records in records_by_mode.items():
        write_jsonl(output_dir / f"{mode}.jsonl", records)
    write_json(output_dir / "metrics.json", metrics)
    manifest = {
        "run_id": args.run_id,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "retrieval_experiment": RETRIEVAL_VERSION,
        "graph_version": config.graph_version,
        "supplemental_graph_enabled": False,
        "graph_expansion_performed": False,
        "embedding_model": config.embeddings.model_name,
        "embedding_dimension": dimension,
        "embedding_device": device,
        "qa_corpus": {
            "index_path": str(
                Path(config.qa_corpus.index_path).relative_to(ROOT)
            ),
            "corpus_version": config.qa_corpus.corpus_version,
            "candidate_k_per_channel": (
                args.candidate_k_per_channel
            ),
            "inject_top_k": args.inject_top_k,
            "exact_source_question_exclusion": True,
        },
        "trigger": (
            "saved Step 11 context is empty or lacks strong direct evidence"
        ),
        "baseline_state_filter": args.baseline_state,
        "modes": list(MODES),
        "cohort_files": {
            name: {
                "path": str(COHORT_FILES[name].relative_to(ROOT)),
                "sha256": sha256(COHORT_FILES[name]),
            }
            for name in selected_cohorts
        },
        "human_label_file": {
            "path": str(LABEL_FILE.relative_to(ROOT)),
            "sha256": sha256(LABEL_FILE),
            "use": "post-selection diagnostics only",
        },
        "runtime": {
            "python": sys.version,
            "git": git_runtime(),
        },
        "safeguards": {
            "step08_reused": True,
            "neo4j_queried": False,
            "llm_called": False,
            "embedding_model_loaded_offline": (
                not args.allow_model_download
            ),
            "retrieval_or_generation_thresholds_changed": False,
            "references_used_for_retrieval": False,
            "annotations_used_for_retrieval": False,
            "supplemental_graph_used": False,
        },
        "processed_records": processed,
    }
    write_json(output_dir / "manifest.json", manifest)
    print(
        json.dumps(
            {
                "status": "complete",
                "output_dir": str(output_dir),
                "processed_records": processed,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
