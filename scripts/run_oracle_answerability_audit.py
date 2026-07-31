from __future__ import annotations

"""Run a reference-answer oracle audit over frozen empty-context queries."""

import argparse
import csv
import hashlib
import json
import os
import statistics
import subprocess
import sys
from collections import Counter, defaultdict
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Any, Iterable

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.config import load_final_config
from src.oracle_answerability import (
    BORDERLINE_ANSWER_SIMILARITY,
    BROAD_ANSWER_SIMILARITY,
    MIN_CONCEPT_COVERAGE,
    MIN_QUESTION_SIMILARITY,
    MIN_SCENARIO_SCORE,
    STRONG_ANSWER_SIMILARITY,
    answer_fts_candidates,
    candidate_payload,
    diagnose_failure,
    diagnosis_payload,
    normalized,
    rank_oracle_candidates,
)
from src.step06_build_embedding_indexes import load_model
from src.step09_hybrid_retrieval import select_relevance_phrases
from src.step09a_qa_corpus import read_corpus_metadata


ROOT = Path(__file__).resolve().parents[1]
AUDIT_VERSION = "oracle_answerability_v1_1"
OUTPUT_ROOT = (
    ROOT / "outputs" / "evaluation" / "oracle_answerability"
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


def clean_text(value: Any) -> str:
    return str(value or "").strip()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    if not path.exists():
        return records
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


def append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(
            json.dumps(payload, ensure_ascii=False) + "\n"
        )
        handle.flush()


def write_json(path: Path, payload: Any) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
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


def is_empty_context(record: dict[str, Any]) -> bool:
    context = dict(
        record.get("final_step11_context")
        or record.get("step11_context")
        or {}
    )
    return not bool(context.get("evidence_items"))


def analysis_phrases(record: dict[str, Any]) -> list[str]:
    analysis = dict(record.get("query_analysis") or {})
    return select_relevance_phrases(
        list(analysis.get("medical_phrases") or []),
        clean_text(analysis.get("primary_intent")),
    )


def current_retrieval_index(
    record: dict[str, Any],
) -> tuple[dict[str, list[str]], set[tuple[str, str]]]:
    """Index every saved pre-Step11 QA/evidence candidate."""

    by_qa: dict[str, list[str]] = defaultdict(list)
    content: set[tuple[str, str]] = set()

    def add(
        *,
        qa_id: Any,
        identifier: Any,
        question: Any,
        answer: Any,
    ) -> None:
        qa_key = clean_text(qa_id)
        identifier_key = clean_text(identifier)
        if qa_key and identifier_key:
            by_qa[qa_key].append(identifier_key)
        question_norm = normalized(question)
        answer_norm = normalized(answer)
        if question_norm and answer_norm:
            content.add((question_norm, answer_norm))

    for item in record.get("evidence", []):
        metadata = dict(item.get("metadata") or {})
        add(
            qa_id=item.get("qa_id"),
            identifier=(
                item.get("evidence_id")
                or item.get("source_id")
            ),
            question=item.get("question"),
            answer=(
                item.get("answer")
                or metadata.get("answer")
            ),
        )
    for relation in record.get("relations", []):
        relation_id = relation.get("relation_id")
        add(
            qa_id=relation.get("qa_id"),
            identifier=relation_id,
            question="",
            answer=relation.get("evidence"),
        )
        metadata = dict(relation.get("metadata") or {})
        for item in metadata.get("evidence_items", []):
            add(
                qa_id=item.get("qa_id") or relation.get("qa_id"),
                identifier=(
                    item.get("mention_id") or relation_id
                ),
                question=item.get("question"),
                answer=item.get("answer") or item.get("evidence"),
            )
    return (
        {
            qa_id: list(dict.fromkeys(values))
            for qa_id, values in by_qa.items()
        },
        content,
    )


def load_empty_queries(
    cohorts: list[str],
    limit: int,
) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    for cohort in cohorts:
        for record in read_jsonl(COHORT_FILES[cohort]):
            if not is_empty_context(record):
                continue
            gold = dict(record.get("gold") or {})
            if not clean_text(gold.get("reference_answer")):
                continue
            payload = dict(record)
            payload["_cohort"] = cohort
            selected.append(payload)
    if limit > 0:
        selected = selected[:limit]
    return selected


def percentile(values: list[float], fraction: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return (
        ordered[lower] * (1.0 - weight)
        + ordered[upper] * weight
    )


def write_summary_csv(
    path: Path,
    records: list[dict[str, Any]],
) -> None:
    fields = [
        "cohort",
        "query_id",
        "query",
        "failure_class",
        "confidence",
        "requires_manual_review",
        "strong_equivalent_count",
        "borderline_count",
        "strongest_answer_similarity",
        "strongest_question_similarity",
        "strongest_scenario_score",
        "original_question_rows_excluded",
        "fts_candidates",
        "top_oracle_qa_id",
        "top_oracle_question",
        "top_oracle_answer",
        "top_oracle_retrieved_by_current_pipeline",
        "latency_ms",
    ]
    with path.open(
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for record in records:
            diagnosis = dict(record.get("diagnosis") or {})
            candidates = list(record.get("oracle_candidates") or [])
            top = candidates[0] if candidates else {}
            writer.writerow(
                {
                    "cohort": record.get("cohort"),
                    "query_id": record.get("query_id"),
                    "query": record.get("query"),
                    "failure_class": diagnosis.get(
                        "failure_class"
                    ),
                    "confidence": diagnosis.get("confidence"),
                    "requires_manual_review": diagnosis.get(
                        "requires_manual_review"
                    ),
                    "strong_equivalent_count": diagnosis.get(
                        "strong_equivalent_count"
                    ),
                    "borderline_count": diagnosis.get(
                        "borderline_count"
                    ),
                    "strongest_answer_similarity": diagnosis.get(
                        "strongest_answer_similarity"
                    ),
                    "strongest_question_similarity": diagnosis.get(
                        "strongest_question_similarity"
                    ),
                    "strongest_scenario_score": diagnosis.get(
                        "strongest_scenario_score"
                    ),
                    "original_question_rows_excluded": record.get(
                        "original_question_rows_excluded"
                    ),
                    "fts_candidates": record.get("fts_candidates"),
                    "top_oracle_qa_id": top.get("qa_id"),
                    "top_oracle_question": top.get("question"),
                    "top_oracle_answer": top.get("answer"),
                    "top_oracle_retrieved_by_current_pipeline": (
                        top.get("retrieved_by_current_pipeline")
                    ),
                    "latency_ms": dict(
                        record.get("timings_ms") or {}
                    ).get("total"),
                }
            )


def write_manual_queue(
    path: Path,
    records: list[dict[str, Any]],
    *,
    priority_only: bool = False,
) -> None:
    fields = [
        "cohort",
        "query_id",
        "query",
        "reference_answer",
        "automatic_failure_class",
        "automatic_reason",
        "oracle_rank",
        "qa_id",
        "source_question",
        "source_answer",
        "answer_similarity",
        "question_similarity",
        "scenario_score",
        "scenario_conflicts",
        "query_concept_coverage",
        "retrieved_by_current_pipeline",
        "human_failure_class",
        "human_equivalent_evidence",
        "annotation_notes",
        "annotation_status",
    ]
    with path.open(
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for record in records:
            diagnosis = dict(record.get("diagnosis") or {})
            if not diagnosis.get("requires_manual_review"):
                continue
            if priority_only and not (
                int(diagnosis.get("strong_equivalent_count") or 0)
                or int(diagnosis.get("borderline_count") or 0)
            ):
                continue
            candidates = list(record.get("oracle_candidates") or [])
            if priority_only:
                candidates = [
                    candidate
                    for candidate in candidates
                    if candidate.get("equivalent_evidence")
                    or candidate.get("borderline_equivalence")
                ]
            for candidate in candidates[:5]:
                writer.writerow(
                    {
                        "cohort": record.get("cohort"),
                        "query_id": record.get("query_id"),
                        "query": record.get("query"),
                        "reference_answer": record.get(
                            "reference_answer"
                        ),
                        "automatic_failure_class": diagnosis.get(
                            "failure_class"
                        ),
                        "automatic_reason": diagnosis.get("reason"),
                        "oracle_rank": candidate.get("oracle_rank"),
                        "qa_id": candidate.get("qa_id"),
                        "source_question": candidate.get("question"),
                        "source_answer": candidate.get("answer"),
                        "answer_similarity": candidate.get(
                            "answer_similarity"
                        ),
                        "question_similarity": candidate.get(
                            "question_similarity"
                        ),
                        "scenario_score": candidate.get(
                            "scenario_score"
                        ),
                        "scenario_conflicts": json.dumps(
                            candidate.get("scenario_conflicts") or [],
                            ensure_ascii=False,
                        ),
                        "query_concept_coverage": candidate.get(
                            "query_concept_coverage"
                        ),
                        "retrieved_by_current_pipeline": (
                            candidate.get(
                                "retrieved_by_current_pipeline"
                            )
                        ),
                        "human_failure_class": "",
                        "human_equivalent_evidence": "",
                        "annotation_notes": "",
                        "annotation_status": (
                            "pending_human_confirmation"
                        ),
                    }
                )


def summarize(
    records: list[dict[str, Any]],
    expected_count: int,
) -> dict[str, Any]:
    classes = Counter(
        dict(record.get("diagnosis") or {}).get(
            "failure_class",
            "unclassified",
        )
        for record in records
    )
    confidences = Counter(
        dict(record.get("diagnosis") or {}).get(
            "confidence",
            "unknown",
        )
        for record in records
    )
    latencies = [
        float(dict(record.get("timings_ms") or {}).get("total") or 0.0)
        for record in records
    ]
    return {
        "status": (
            "complete"
            if len(records) == expected_count
            else "partial"
        ),
        "expected_empty_context_queries": expected_count,
        "completed_queries": len(records),
        "failure_class_counts": dict(sorted(classes.items())),
        "confidence_counts": dict(sorted(confidences.items())),
        "manual_review_queries": sum(
            bool(
                dict(record.get("diagnosis") or {}).get(
                    "requires_manual_review"
                )
            )
            for record in records
        ),
        "priority_manual_review_queries": sum(
            bool(
                int(
                    dict(record.get("diagnosis") or {}).get(
                        "strong_equivalent_count"
                    )
                    or 0
                )
                or int(
                    dict(record.get("diagnosis") or {}).get(
                        "borderline_count"
                    )
                    or 0
                )
            )
            for record in records
        ),
        "strong_equivalent_queries": sum(
            int(
                dict(record.get("diagnosis") or {}).get(
                    "strong_equivalent_count"
                )
                or 0
            )
            > 0
            for record in records
        ),
        "exact_reference_duplicate_queries": sum(
            any(
                bool(candidate.get("exact_reference_answer_match"))
                for candidate in record.get(
                    "oracle_candidates",
                    [],
                )
            )
            for record in records
        ),
        "latency_ms": {
            "mean": (
                round(statistics.fmean(latencies), 3)
                if latencies
                else 0.0
            ),
            "median": (
                round(statistics.median(latencies), 3)
                if latencies
                else 0.0
            ),
            "p95": round(percentile(latencies, 0.95), 3),
            "total": round(sum(latencies), 3),
        },
        "scope_warning": (
            "The oracle searches the full SQLite answer FTS index and then "
            "E5-reranks its shortlist. Absence from this shortlist is not "
            "proof of absence from the full semantic answer space."
        ),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Diagnose why frozen evaluation queries ended with empty "
            "Step 11 contexts."
        )
    )
    parser.add_argument(
        "--cohort",
        choices=(*COHORT_FILES, "all"),
        default="all",
    )
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument(
        "--candidate-k",
        type=int,
        default=100,
        help="Full answer-FTS shortlist size before E5 reranking.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=25,
        help="Number of nearest oracle passages saved per query.",
    )
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument(
        "--allow-model-download",
        action="store_true",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    output_dir = OUTPUT_ROOT / args.run_id
    results_path = output_dir / "oracle_results.jsonl"
    if output_dir.exists() and not args.resume:
        raise FileExistsError(
            f"Run already exists; use --resume: {output_dir}"
        )

    selected_cohorts = (
        list(COHORT_FILES)
        if args.cohort == "all"
        else [args.cohort]
    )
    queries = load_empty_queries(
        selected_cohorts,
        args.limit,
    )
    if not queries:
        raise ValueError("No empty-context queries with references found.")
    completed_records = (
        read_jsonl(results_path)
        if args.resume and results_path.exists()
        else []
    )
    completed_ids = {
        (clean_text(record.get("cohort")), clean_text(record.get("query_id")))
        for record in completed_records
    }

    config = load_final_config()
    index_path = Path(config.qa_corpus.index_path)
    metadata = read_corpus_metadata(index_path)
    if (
        metadata.get("corpus_version")
        != config.qa_corpus.corpus_version
    ):
        raise RuntimeError("QA corpus version mismatch.")
    if not args.allow_model_download:
        os.environ.setdefault("HF_HUB_OFFLINE", "1")
        os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
    model, device, dimension = load_model(
        config.embeddings.model_name,
        config.embeddings.dimension,
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    for index, record in enumerate(queries, start=1):
        cohort = clean_text(record.get("_cohort"))
        query_id = clean_text(record.get("query_id"))
        if (cohort, query_id) in completed_ids:
            print(
                json.dumps(
                    {
                        "status": "cached",
                        "progress": f"{index}/{len(queries)}",
                        "cohort": cohort,
                        "query_id": query_id,
                    }
                ),
                flush=True,
            )
            continue

        query = clean_text(record.get("query"))
        gold = dict(record.get("gold") or {})
        reference_answer = clean_text(
            gold.get("reference_answer")
        )
        analysis = dict(record.get("query_analysis") or {})
        primary_intent = clean_text(
            analysis.get("primary_intent")
        )
        phrases = analysis_phrases(record)
        by_qa, content = current_retrieval_index(record)

        started = perf_counter()
        fts_started = perf_counter()
        rows, excluded = answer_fts_candidates(
            index_path,
            reference_answer,
            original_query=query,
            limit=args.candidate_k,
        )
        fts_ms = (perf_counter() - fts_started) * 1000.0
        rank_started = perf_counter()
        candidates = rank_oracle_candidates(
            rows,
            query=query,
            reference_answer=reference_answer,
            primary_intent=primary_intent,
            query_medical_phrases=phrases,
            current_retrieval_by_qa=by_qa,
            current_retrieval_content=content,
            model=model,
            top_k=args.top_k,
        )
        rank_ms = (perf_counter() - rank_started) * 1000.0
        diagnosis = diagnose_failure(candidates)
        payload = {
            "audit_version": AUDIT_VERSION,
            "cohort": cohort,
            "query_id": query_id,
            "query": query,
            "reference_answer": reference_answer,
            "primary_intent": primary_intent,
            "query_medical_phrases": phrases,
            "frozen_step11_state": "empty_context",
            "source_retrieval_file": str(
                COHORT_FILES[cohort].relative_to(ROOT)
            ),
            "oracle_scope": (
                "full_answer_fts_then_e5_rerank"
            ),
            "reference_used_offline_only": True,
            "original_question_rows_excluded": excluded,
            "fts_candidates": len(rows),
            "diagnosis": diagnosis_payload(diagnosis),
            "oracle_candidates": [
                candidate_payload(candidate)
                for candidate in candidates
            ],
            "timings_ms": {
                "answer_fts": round(fts_ms, 3),
                "e5_rerank": round(rank_ms, 3),
                "total": round(
                    (perf_counter() - started) * 1000.0,
                    3,
                ),
            },
        }
        append_jsonl(results_path, payload)
        completed_records.append(payload)
        completed_ids.add((cohort, query_id))
        print(
            json.dumps(
                {
                    "status": "ok",
                    "progress": f"{index}/{len(queries)}",
                    "cohort": cohort,
                    "query_id": query_id,
                    "failure_class": diagnosis.failure_class,
                    "manual_review": (
                        diagnosis.requires_manual_review
                    ),
                    "top_similarity": (
                        diagnosis.strongest_answer_similarity
                    ),
                    "latency_ms": payload["timings_ms"]["total"],
                },
                ensure_ascii=False,
            ),
            flush=True,
        )

    ordered = sorted(
        completed_records,
        key=lambda item: (
            clean_text(item.get("cohort")),
            clean_text(item.get("query_id")),
        ),
    )
    write_summary_csv(output_dir / "summary.csv", ordered)
    write_manual_queue(
        output_dir / "borderline_manual_review.csv",
        ordered,
    )
    write_manual_queue(
        output_dir / "priority_manual_review.csv",
        ordered,
        priority_only=True,
    )
    metrics = summarize(ordered, len(queries))
    write_json(output_dir / "metrics.json", metrics)
    manifest = {
        "run_id": args.run_id,
        "audit_version": AUDIT_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "cohorts": selected_cohorts,
        "source_files": {
            cohort: {
                "path": str(
                    COHORT_FILES[cohort].relative_to(ROOT)
                ),
                "sha256": sha256(COHORT_FILES[cohort]),
            }
            for cohort in selected_cohorts
        },
        "graph_version": config.graph_version,
        "graph_queried": False,
        "graph_expanded": False,
        "supplemental_graph_used": False,
        "generation_run": False,
        "reference_use": "offline oracle diagnosis only",
        "qa_corpus": {
            "path": str(index_path.relative_to(ROOT)),
            "sha256": sha256(index_path),
            "metadata": metadata,
        },
        "oracle_search": {
            "scope": "full answer FTS shortlist then E5 rerank",
            "candidate_k": args.candidate_k,
            "saved_top_k": args.top_k,
            "exact_normalized_source_question_excluded": True,
            "full_808k_answer_vector_index_available": False,
        },
        "thresholds": {
            "strong_answer_similarity": (
                STRONG_ANSWER_SIMILARITY
            ),
            "borderline_answer_similarity": (
                BORDERLINE_ANSWER_SIMILARITY
            ),
            "broad_answer_similarity": BROAD_ANSWER_SIMILARITY,
            "minimum_scenario_score": MIN_SCENARIO_SCORE,
            "minimum_concept_coverage": MIN_CONCEPT_COVERAGE,
            "minimum_question_similarity": (
                MIN_QUESTION_SIMILARITY
            ),
        },
        "embedding": {
            "model": config.embeddings.model_name,
            "dimension": dimension,
            "device": device,
            "offline": not args.allow_model_download,
        },
        "runtime": {
            "python": sys.version,
            "git": git_runtime(),
        },
    }
    write_json(output_dir / "manifest.json", manifest)
    print(
        json.dumps(
            {
                "status": metrics["status"],
                "completed_queries": len(ordered),
                "expected_queries": len(queries),
                "output_dir": str(output_dir),
            },
            ensure_ascii=False,
        ),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
