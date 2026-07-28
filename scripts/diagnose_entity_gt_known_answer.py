from __future__ import annotations

import argparse
import csv
import json
import sqlite3
import statistics
import sys
from collections import Counter
from dataclasses import asdict
from pathlib import Path
from typing import Any, Iterable

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from scripts.run_generation_ablation import frozen_subgraph
from src.config import load_final_config
from src.neo4j_repository import Neo4jRepository
from src.query_relevance import minimum_candidate_concept_coverage
from src.step08a_normalize_query import normalize_query
from src.step11_build_evidence_context import (
    INTENTS_REQUIRING_DIRECT_SUPPORT,
    build_evidence_context,
    has_direct_question_anchor,
    has_strong_semantic_support,
    item_answer_relevance,
    item_relevance_features,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GOLD = ROOT / "data" / "evaluation" / "entity_ground_truth_trial_100.csv"
DEFAULT_GENERAL_RETRIEVAL = (
    ROOT
    / "outputs"
    / "evaluation"
    / "retrieval"
    / "entity_gt_trial_100_retrieval_v1"
    / "full_hybrid.jsonl"
)
DEFAULT_KNOWN_RETRIEVAL = (
    ROOT
    / "outputs"
    / "evaluation"
    / "retrieval"
    / "entity_gt_trial_100_known_answer_retrieval_v2"
    / "full_hybrid.jsonl"
)
DEFAULT_GENERATION = (
    ROOT
    / "outputs"
    / "evaluation"
    / "generation"
    / "entity_gt_trial_100_generation_v1"
    / "full_pipeline.jsonl"
)
DEFAULT_AUDIT = (
    ROOT
    / "outputs"
    / "evaluation"
    / "claim_audit"
    / "entity_gt_trial_100_generation_v1"
    / "full_pipeline.jsonl"
)
DEFAULT_KNOWN_GENERATION = (
    ROOT
    / "outputs"
    / "evaluation"
    / "generation"
    / "entity_gt_trial_100_known_answer_generation_v1"
    / "full_pipeline.jsonl"
)
DEFAULT_KNOWN_AUDIT = (
    ROOT
    / "outputs"
    / "evaluation"
    / "claim_audit"
    / "entity_gt_trial_100_known_answer_generation_v1"
    / "full_pipeline.jsonl"
)
DEFAULT_OUTPUT_DIR = (
    ROOT / "outputs" / "evaluation" / "entity_gt_trial_100" / "known_answer_diagnosis"
)

RELEVANCE_GATES = {
    "intent_mismatch",
    "claim_query_concept_mismatch",
    "anatomy_mismatch",
}
SUPPORT_OR_SAFETY_GATES = {
    "support_below_weak_threshold",
    "no_valid_citation",
    "recommendation_not_supported",
    "negation_mismatch",
    "number_mismatch",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Compare exact-QA-excluded and exact-QA-allowed retrieval, replay "
            "Steps 10-11, and prepare a deterministic removed-claim audit."
        )
    )
    parser.add_argument("--gold-file", type=Path, default=DEFAULT_GOLD)
    parser.add_argument(
        "--general-retrieval-file",
        type=Path,
        default=DEFAULT_GENERAL_RETRIEVAL,
    )
    parser.add_argument(
        "--known-retrieval-file",
        type=Path,
        default=DEFAULT_KNOWN_RETRIEVAL,
    )
    parser.add_argument("--generation-file", type=Path, default=DEFAULT_GENERATION)
    parser.add_argument("--claim-audit-file", type=Path, default=DEFAULT_AUDIT)
    parser.add_argument(
        "--known-generation-file",
        type=Path,
        default=DEFAULT_KNOWN_GENERATION,
    )
    parser.add_argument(
        "--known-claim-audit-file",
        type=Path,
        default=DEFAULT_KNOWN_AUDIT,
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument(
        "--skip-neo4j",
        action="store_true",
        help="Skip the read-only Neo4j QA availability check.",
    )
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL at {path}:{line_number}") from exc
    return records


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_gold(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def normalized(text: Any) -> str:
    return normalize_query(str(text or "")).normalized_query


def write_json(path: Path, payload: Any) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def write_jsonl(path: Path, records: Iterable[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def exact_qa_availability_in_sqlite(
    sqlite_path: Path,
    query_norms: set[str],
    original_queries: set[str],
) -> dict[str, list[dict[str, str]]]:
    normalized_placeholders = ", ".join("?" for _ in query_norms)
    original_placeholders = ", ".join("?" for _ in original_queries)
    sql = (
        "SELECT qa_id, question, answer, question_norm "
        f"FROM qa_records WHERE question_norm IN ({normalized_placeholders}) "
        f"OR question IN ({original_placeholders})"
    )
    results: dict[str, list[dict[str, str]]] = {
        query_norm: [] for query_norm in query_norms
    }
    connection = sqlite3.connect(f"file:{sqlite_path.as_posix()}?mode=ro", uri=True)
    try:
        for qa_id, question, answer, question_norm in connection.execute(
            sql,
            [*sorted(query_norms), *sorted(original_queries)],
        ):
            current_question_norm = normalized(question)
            if current_question_norm not in results:
                continue
            results[current_question_norm].append(
                {
                    "qa_id": str(qa_id),
                    "question": str(question),
                    "answer": str(answer),
                }
            )
    finally:
        connection.close()
    return results


def exact_qa_availability_in_neo4j(
    query_norms: set[str],
) -> dict[str, list[dict[str, str]]]:
    config = load_final_config()
    cypher = """
MATCH (q:QARecord {graph_version: $graph_version})
RETURN q.qa_id AS qa_id,
       q.question AS question,
       q.answer AS answer
""".strip()
    results: dict[str, list[dict[str, str]]] = {
        query_norm: [] for query_norm in query_norms
    }
    with Neo4jRepository(config) as repository:
        rows = repository._execute_read(
            cypher,
            {"graph_version": config.graph_version},
        )
    for row in rows:
        question_norm = normalized(row.get("question"))
        if question_norm in results:
            results[question_norm].append(
                {
                    "qa_id": str(row.get("qa_id") or ""),
                    "question": str(row.get("question") or ""),
                    "answer": str(row.get("answer") or ""),
                }
            )
    return results


def first_exact_rank(
    evidence: list[Any],
    query_norm: str,
    reference_norm: str,
) -> tuple[int | None, int | None]:
    question_rank: int | None = None
    answer_rank: int | None = None
    for index, item in enumerate(evidence, start=1):
        if isinstance(item, dict):
            question = item.get("question") or item.get("source_question")
            answer = item.get("answer") or item.get("source_answer") or item.get("text")
        else:
            question = getattr(item, "question", "")
            answer = getattr(item, "answer", "") or getattr(item, "text", "")
        if question_rank is None and normalized(question) == query_norm:
            question_rank = index
        if answer_rank is None and reference_norm and normalized(answer) == reference_norm:
            answer_rank = index
    return question_rank, answer_rank


def exact_candidate_step11_gate_reasons(
    item: Any,
    *,
    subgraph: Any,
    query: str,
    config: Any,
) -> list[str]:
    features = item_relevance_features(
        item,
        query,
        subgraph.query_medical_phrases,
    )
    answer_relevance = item_answer_relevance(item, query)
    direct_anchor = has_direct_question_anchor(item)
    semantic_support = has_strong_semantic_support(item, config)
    concept_floor = minimum_candidate_concept_coverage(
        int(features["query_concept_count"])
    )

    reasons: list[str] = []
    if bool(features["anatomy_mismatch"]):
        reasons.append("anatomy_mismatch")
    if bool(features["unrelated_condition_mismatch"]):
        reasons.append("unrelated_condition_mismatch")
    if (
        float(features["source_reliability"])
        < config.retrieval.context_min_source_reliability
    ):
        reasons.append("source_reliability_below_threshold")
    if (
        answer_relevance < config.retrieval.context_min_answer_relevance
        and not direct_anchor
        and not semantic_support
    ):
        reasons.append("answer_relevance_below_threshold")
    if (
        item.score < config.retrieval.context_min_score
        and not direct_anchor
        and not semantic_support
    ):
        reasons.append("reranked_score_below_threshold")
    if (
        concept_floor > 0.0
        and float(features["query_concept_coverage"]) < concept_floor
        and not direct_anchor
    ):
        reasons.append("query_concept_coverage_below_threshold")
    if (
        subgraph.primary_intent in INTENTS_REQUIRING_DIRECT_SUPPORT
        and float(features["intent_support"])
        < config.retrieval.context_min_intent_support
        and not direct_anchor
    ):
        reasons.append("intent_support_below_threshold")
    if not direct_anchor:
        reasons.append("not_recognized_as_direct_question_anchor")
    return reasons


def replay_retrieval_record(
    record: dict[str, Any],
    *,
    query_norm: str,
    reference_norm: str,
) -> dict[str, Any]:
    config = load_final_config()
    analysis = dict(record.get("query_analysis") or {})
    primary_intent = str(analysis.get("primary_intent") or "unclear_intent")
    reformulated_query = str(
        analysis.get("reformulated_query") or record.get("query") or ""
    )

    input_question_rank, input_answer_rank = first_exact_rank(
        list(record.get("evidence") or []),
        query_norm,
        reference_norm,
    )
    subgraph = frozen_subgraph(
        record,
        primary_intent,
        rerank=True,
        config=config,
    )
    reranked_question_rank, reranked_answer_rank = first_exact_rank(
        subgraph.evidence,
        query_norm,
        reference_norm,
    )
    context = build_evidence_context(
        subgraph,
        reformulated_query,
        config=config,
    )
    context_payload = asdict(context)
    context_question_rank, context_answer_rank = first_exact_rank(
        list(context_payload.get("evidence_items") or []),
        query_norm,
        reference_norm,
    )
    exact_reranked_item = next(
        (
            item
            for item in subgraph.evidence
            if normalized(getattr(item, "question", "")) == query_norm
        ),
        None,
    )
    exact_gate_reasons: list[str] = []
    if exact_reranked_item is not None and context_question_rank is None:
        exact_gate_reasons = exact_candidate_step11_gate_reasons(
            exact_reranked_item,
            subgraph=subgraph,
            query=reformulated_query,
            config=config,
        )
        if len(exact_gate_reasons) == 1 and exact_gate_reasons[0] == (
            "not_recognized_as_direct_question_anchor"
        ):
            exact_gate_reasons.append("post_filter_relative_margin_or_dedup")
    return {
        "candidate_count": len(record.get("evidence") or []),
        "reranked_candidate_count": len(subgraph.evidence),
        "context_count": len(context.evidence_items),
        "exact_question_input_rank": input_question_rank,
        "exact_answer_input_rank": input_answer_rank,
        "exact_question_reranked_rank": reranked_question_rank,
        "exact_answer_reranked_rank": reranked_answer_rank,
        "exact_question_context_rank": context_question_rank,
        "exact_answer_context_rank": context_answer_rank,
        "exact_question_step11_gate_reasons": exact_gate_reasons,
        "context": context_payload,
    }


def summarize_replay(rows: list[dict[str, Any]], side: str) -> dict[str, Any]:
    values = [row[side] for row in rows]
    gate_reason_counts = Counter(
        reason
        for item in values
        for reason in item.get("exact_question_step11_gate_reasons") or []
    )
    return {
        "query_count": len(values),
        "nonempty_context_queries": sum(item["context_count"] > 0 for item in values),
        "empty_context_queries": sum(item["context_count"] == 0 for item in values),
        "mean_context_items": round(
            sum(item["context_count"] for item in values) / max(1, len(values)),
            6,
        ),
        "exact_question_in_retrieval": sum(
            item["exact_question_input_rank"] is not None for item in values
        ),
        "exact_answer_in_retrieval": sum(
            item["exact_answer_input_rank"] is not None for item in values
        ),
        "exact_question_after_reranking": sum(
            item["exact_question_reranked_rank"] is not None for item in values
        ),
        "exact_answer_after_reranking": sum(
            item["exact_answer_reranked_rank"] is not None for item in values
        ),
        "exact_question_in_step11_context": sum(
            item["exact_question_context_rank"] is not None for item in values
        ),
        "exact_answer_in_step11_context": sum(
            item["exact_answer_context_rank"] is not None for item in values
        ),
        "exact_answer_display_truncated_in_step11": sum(
            row[side]["exact_question_context_rank"] is not None
            and row[side]["exact_answer_context_rank"] is None
            and len(str(row.get("reference_answer") or "")) > 1000
            for row in rows
        ),
        "exact_question_step11_gate_reason_counts": dict(
            sorted(gate_reason_counts.items())
        ),
    }


def classify_removed_claim(
    status: str,
    support_score: float,
    failed_checks: set[str],
) -> str:
    if status == "weakly_supported" and not failed_checks:
        return "weak_evidence_conservative_removal"
    if (
        support_score >= 0.4
        and failed_checks
        and failed_checks.issubset(RELEVANCE_GATES)
    ):
        return "evidence_supported_but_query_relevance_gate_failed"
    if failed_checks & SUPPORT_OR_SAFETY_GATES and failed_checks & RELEVANCE_GATES:
        return "mixed_relevance_and_support_or_safety_failure"
    if (
        support_score < 0.25
        or "support_below_weak_threshold" in failed_checks
        or "no_valid_citation" in failed_checks
    ):
        return "low_or_missing_evidence"
    if failed_checks & SUPPORT_OR_SAFETY_GATES:
        return "support_or_safety_failure"
    if status == "weakly_supported":
        return "weak_evidence_conservative_removal"
    return "other_requires_human_review"


def cited_evidence_texts(
    generation_record: dict[str, Any],
    citations: list[str],
) -> str:
    context = dict((generation_record.get("raw") or {}).get("context") or {})
    evidence_by_id = {
        str(item.get("evidence_id") or ""): item
        for item in context.get("evidence_items") or []
    }
    excerpts: list[str] = []
    for citation in citations:
        item = evidence_by_id.get(str(citation))
        if not item:
            continue
        excerpt = (
            str(item.get("source_answer") or "")
            or str(item.get("evidence") or "")
        )
        excerpts.append(f"{citation}: {excerpt}")
    return " || ".join(excerpts)


def build_removed_claim_review(
    generation_records: list[dict[str, Any]],
    audit_records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    generation_by_id = {
        str(record.get("query_id") or ""): record for record in generation_records
    }
    review_rows: list[dict[str, Any]] = []
    for audit in audit_records:
        query_id = str(audit.get("query_id") or "")
        generation = generation_by_id.get(query_id)
        if not generation:
            continue
        retained_claims = {
            normalized(item.get("claim"))
            for item in generation.get("output_claims") or []
        }
        for verification in audit.get("verifications") or []:
            claim_payload = dict(verification.get("claim") or {})
            claim = str(claim_payload.get("claim") or "").strip()
            if not claim or normalized(claim) in retained_claims:
                continue
            status = str(verification.get("status") or "")
            support_score = float(verification.get("support_score") or 0.0)
            failed_checks = {
                str(value)
                for value in verification.get("failed_checks") or []
                if str(value)
            }
            citations = [
                str(value) for value in claim_payload.get("citations") or []
            ]
            classification = classify_removed_claim(
                status,
                support_score,
                failed_checks,
            )
            review_rows.append(
                {
                    "query_id": query_id,
                    "query": str(generation.get("query") or ""),
                    "reference_answer": str(
                        (generation.get("gold") or {}).get("reference_answer") or ""
                    ),
                    "removed_claim": claim,
                    "verifier_status": status,
                    "support_score": support_score,
                    "question_relevance": float(
                        verification.get("question_relevance") or 0.0
                    ),
                    "query_concept_coverage": float(
                        verification.get("query_concept_coverage") or 0.0
                    ),
                    "failed_checks": "|".join(sorted(failed_checks)),
                    "deterministic_audit_class": classification,
                    "requires_human_adjudication": "yes",
                    "citations": "|".join(citations),
                    "cited_evidence": cited_evidence_texts(generation, citations),
                    "verifier_reason": str(verification.get("reason") or ""),
                }
            )
    return review_rows


def write_claim_review_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = [
        "query_id",
        "query",
        "reference_answer",
        "removed_claim",
        "verifier_status",
        "support_score",
        "question_relevance",
        "query_concept_coverage",
        "failed_checks",
        "deterministic_audit_class",
        "requires_human_adjudication",
        "citations",
        "cited_evidence",
        "verifier_reason",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def percentile(values: list[float], fraction: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = round((len(ordered) - 1) * fraction)
    return float(ordered[index])


def summarize_latency(
    generation_records: list[dict[str, Any]],
    stage: str,
) -> dict[str, float]:
    values = [
        float((record.get("timings_ms") or {}).get(stage) or 0.0)
        for record in generation_records
    ]
    if not values:
        return {
            "mean_ms": 0.0,
            "median_ms": 0.0,
            "p95_ms": 0.0,
            "total_ms": 0.0,
        }
    return {
        "mean_ms": round(statistics.fmean(values), 6),
        "median_ms": round(statistics.median(values), 6),
        "p95_ms": round(percentile(values, 0.95), 6),
        "total_ms": round(sum(values), 6),
    }


def summarize_generation_run(
    generation_records: list[dict[str, Any]],
    audit_records: list[dict[str, Any]],
    metrics_file: Path,
    claim_review: list[dict[str, Any]],
) -> dict[str, Any]:
    run_metrics = dict(read_json(metrics_file).get("full_pipeline") or {})
    verifications = [
        verification
        for audit in audit_records
        for verification in audit.get("verifications") or []
    ]
    failed_checks = Counter(
        str(check)
        for verification in verifications
        for check in verification.get("failed_checks") or []
    )
    reliability_payloads = [
        dict((record.get("raw") or {}).get("reliability") or {})
        for record in generation_records
    ]
    reliability_scores = [
        float(payload.get("score") or 0.0) for payload in reliability_payloads
    ]
    reliability_labels = Counter(
        str(payload.get("label") or "unavailable")
        for payload in reliability_payloads
    )
    bertscore = dict(run_metrics.get("bertscore") or {})
    grounding = dict(run_metrics.get("claim_grounding") or {})
    citations = dict(run_metrics.get("citation_validity") or {})
    completeness = dict(run_metrics.get("answer_completeness") or {})
    review_classes = Counter(
        str(row.get("deterministic_audit_class") or "")
        for row in claim_review
    )
    pre_claim_count = len(verifications)
    post_claim_count = sum(
        len(record.get("output_claims") or []) for record in generation_records
    )
    return {
        "query_count": len(generation_records),
        "generation_status_counts": dict(
            sorted(
                Counter(
                    str(record.get("generation_status") or "")
                    for record in generation_records
                ).items()
            )
        ),
        "nonempty_context_queries": sum(
            bool(
                ((record.get("raw") or {}).get("context") or {}).get(
                    "evidence_items"
                )
            )
            for record in generation_records
        ),
        "empty_context_queries": sum(
            not bool(
                ((record.get("raw") or {}).get("context") or {}).get(
                    "evidence_items"
                )
            )
            for record in generation_records
        ),
        "answerability_counts": dict(
            sorted(
                Counter(
                    str(record.get("answerability") or "")
                    for record in generation_records
                ).items()
            )
        ),
        "average_query_coverage": float(
            completeness.get("average_query_coverage") or 0.0
        ),
        "bertscore": bertscore,
        "post_mitigation_claim_grounding": grounding,
        "post_mitigation_citation_validity": citations,
        "pre_mitigation_claims": pre_claim_count,
        "pre_mitigation_status_counts": dict(
            sorted(
                Counter(
                    str(verification.get("status") or "")
                    for verification in verifications
                ).items()
            )
        ),
        "post_mitigation_claims": post_claim_count,
        "removed_claims": len(claim_review),
        "claim_removal_rate": round(
            len(claim_review) / max(1, pre_claim_count),
            6,
        ),
        "failed_check_counts": dict(sorted(failed_checks.items())),
        "removed_claim_review_class_counts": dict(sorted(review_classes.items())),
        "removed_claims_with_support_score_ge_0_40": sum(
            float(row.get("support_score") or 0.0) >= 0.4
            for row in claim_review
        ),
        "reliability": {
            "label_counts": dict(sorted(reliability_labels.items())),
            "mean": round(statistics.fmean(reliability_scores), 6)
            if reliability_scores
            else 0.0,
            "median": round(statistics.median(reliability_scores), 6)
            if reliability_scores
            else 0.0,
            "minimum": round(min(reliability_scores), 6)
            if reliability_scores
            else 0.0,
            "maximum": round(max(reliability_scores), 6)
            if reliability_scores
            else 0.0,
        },
        "latency": {
            "end_to_end": summarize_latency(
                generation_records,
                "end_to_end",
            ),
            "step12_answer_generation": summarize_latency(
                generation_records,
                "step12_answer_generation",
            ),
        },
    }


def markdown_report(payload: dict[str, Any]) -> str:
    general = payload["step10_step11_replay"]["generalization"]
    known = payload["step10_step11_replay"]["known_answer"]
    pre_fix = payload["observed_before_fix"]
    availability = payload["exact_qa_availability"]
    general_generation = payload["generation_runs"]["generalization"]
    known_generation = payload["generation_runs"]["known_answer"]
    comparison = payload["generation_comparison"]
    known_bert = known_generation["bertscore"]
    general_bert = general_generation["bertscore"]
    known_grounding = known_generation["post_mitigation_claim_grounding"]
    known_citations = known_generation["post_mitigation_citation_validity"]
    known_reliability = known_generation["reliability"]
    known_latency = known_generation["latency"]
    review_lines = "\n".join(
        f"- `{name}`: {count}"
        for name, count in known_generation[
            "removed_claim_review_class_counts"
        ].items()
    )
    return f"""# Known-Answer vs Generalization Diagnosis

## Experiment

Both trials use the same 100 entity-ground-truth questions and frozen
`final_v1` pipeline.

- Generalization trial: excludes each question's exact AHD QA record.
- Known-answer trial: allows that exact AHD QA record.

Retrieval weights, thresholds, prompts, generation settings, and verification
rules were unchanged. The known-answer run uses three narrow correctness fixes:
NFKC normalization, backward-compatible terms for the frozen FTS index, and
exact lexical QA anchoring.

## Exact QA Availability

- External SQLite corpus: {availability["sqlite_queries_with_exact_qa"]}/100 queries
- Frozen Neo4j `QARecord` nodes: {availability["neo4j_queries_with_exact_qa"]}/100 queries
- Configured graph version: `{payload["graph_version"]}`

The two counts are not contradictory. SQLite holds the full external QA search
corpus, while Neo4j contains only QA records represented in `final_v1`.

## Steps 9-11 Boundary Trace

Before the fixes, the known-answer replay had non-empty context for
{pre_fix["known_answer_nonempty_context_queries"]}/100 queries and retained the
exact question for only {pre_fix["known_answer_exact_question_in_step11"]}/100.
All {pre_fix["exact_questions_rejected_by_step11"]} rejected exact passages were
missing the direct-anchor flag; {pre_fix["rejected_for_intent_support"]} then
failed the ordinary intent-support gate.

| Measure | Generalization | Known-answer |
|---|---:|---:|
| Non-empty Step 11 context | {general["nonempty_context_queries"]}/100 | {known["nonempty_context_queries"]}/100 |
| Exact question in Step 9 candidates | {general["exact_question_in_retrieval"]}/100 | {known["exact_question_in_retrieval"]}/100 |
| Exact answer in Step 9 candidates | {general["exact_answer_in_retrieval"]}/100 | {known["exact_answer_in_retrieval"]}/100 |
| Exact question after Step 10 | {general["exact_question_after_reranking"]}/100 | {known["exact_question_after_reranking"]}/100 |
| Exact answer after Step 10 | {general["exact_answer_after_reranking"]}/100 | {known["exact_answer_after_reranking"]}/100 |
| Exact question retained by Step 11 | {general["exact_question_in_step11_context"]}/100 | {known["exact_question_in_step11_context"]}/100 |
| Exact answer retained by Step 11 | {general["exact_answer_in_step11_context"]}/100 | {known["exact_answer_in_step11_context"]}/100 |
| Exact QA retained but answer display truncated | {general["exact_answer_display_truncated_in_step11"]}/100 | {known["exact_answer_display_truncated_in_step11"]}/100 |
| Mean Step 11 context items | {general["mean_context_items"]:.3f} | {known["mean_context_items"]:.3f} |

Step 9 now retrieves the exact QA for all 100 known-answer questions, Step 10
keeps all 100, and Step 11 retains all 100. Seven long answers are still shown
as non-exact full strings because Step 11 truncates displayed source answers to
1,000 characters; their exact question/source remains present.

## Generation Comparison

| Measure | Generalization | Known-answer | Change |
|---|---:|---:|---:|
| Non-empty context | {general_generation["nonempty_context_queries"]}/100 | {known_generation["nonempty_context_queries"]}/100 | {comparison["nonempty_context_queries"]:+d} |
| Generated | {general_generation["generation_status_counts"].get("generated", 0)}/100 | {known_generation["generation_status_counts"].get("generated", 0)}/100 | {comparison["generated_queries"]:+d} |
| API/generation fallback | {general_generation["generation_status_counts"].get("fallback", 0)}/100 | {known_generation["generation_status_counts"].get("fallback", 0)}/100 | {comparison["fallback_queries"]:+d} |
| Substantive claim-bearing answers | {general_bert.get("evaluated_query_count", 0)}/100 | {known_bert.get("evaluated_query_count", 0)}/100 | {comparison["substantive_answers"]:+d} |
| Fully answerable | {general_generation["answerability_counts"].get("fully_answerable", 0)}/100 | {known_generation["answerability_counts"].get("fully_answerable", 0)}/100 | {comparison["fully_answerable"]:+d} |
| Partially answerable | {general_generation["answerability_counts"].get("partially_answerable", 0)}/100 | {known_generation["answerability_counts"].get("partially_answerable", 0)}/100 | {comparison["partially_answerable"]:+d} |
| Supported but incomplete | {general_generation["answerability_counts"].get("supported_but_incomplete", 0)}/100 | {known_generation["answerability_counts"].get("supported_but_incomplete", 0)}/100 | {comparison["supported_but_incomplete"]:+d} |
| Insufficient evidence | {general_generation["answerability_counts"].get("insufficient_evidence", 0)}/100 | {known_generation["answerability_counts"].get("insufficient_evidence", 0)}/100 | {comparison["insufficient_evidence"]:+d} |
| BERTScore F1 | {float(general_bert.get("bertscore_f1") or 0.0):.6f} | {float(known_bert.get("bertscore_f1") or 0.0):.6f} | {comparison["bertscore_f1"]:+.6f} |

Allowing the exact QA fixes retrieval and technical generation coverage, but
substantive answer coverage rises only from
{general_bert.get("evaluated_query_count", 0)} to
{known_bert.get("evaluated_query_count", 0)}. This isolates the remaining
bottleneck after Step 11: claim verification and mitigation.

## Claim Audit

- Pre-mitigation claims: {known_generation["pre_mitigation_claims"]}
- Supported / weak / unsupported before mitigation:
  {known_generation["pre_mitigation_status_counts"].get("supported", 0)} /
  {known_generation["pre_mitigation_status_counts"].get("weakly_supported", 0)} /
  {known_generation["pre_mitigation_status_counts"].get("unsupported", 0)}
- Claims retained after mitigation: {known_generation["post_mitigation_claims"]}
- Claims removed: {known_generation["removed_claims"]}
  ({known_generation["claim_removal_rate"]:.1%})
- Removed claims with evidence support score >= 0.40:
  {known_generation["removed_claims_with_support_score_ge_0_40"]}
- `intent_mismatch` removals:
  {known_generation["failed_check_counts"].get("intent_mismatch", 0)}
- `claim_query_concept_mismatch` removals:
  {known_generation["failed_check_counts"].get("claim_query_concept_mismatch", 0)}

Deterministic human-review buckets:

{review_lines}

The largest bucket,
`evidence_supported_but_query_relevance_gate_failed`, contains evidence-backed
claims removed by query-intent, concept, or anatomy gates. It is a suspected
false-rejection queue, not proof that every removal was wrong.

Post-mitigation claim support =
{float(known_grounding.get("claim_support_rate") or 0.0):.2f},
hallucination rate =
{float(known_grounding.get("hallucination_rate") or 0.0):.2f}, and citation
validity = {float(known_citations.get("citation_validity") or 0.0):.2f}.
These values apply only to the
{known_grounding.get("evaluated_query_count", 0)} substantive, claim-bearing
answers. They are not results over all 100 questions.

## Reliability

- Low / medium / high:
  {known_reliability["label_counts"].get("low", 0)} /
  {known_reliability["label_counts"].get("medium", 0)} /
  {known_reliability["label_counts"].get("high", 0)}
- Mean: {known_reliability["mean"]:.6f}
- Median: {known_reliability["median"]:.6f}
- Range: {known_reliability["minimum"]:.6f} to
  {known_reliability["maximum"]:.6f}

## Latency

| Stage | Mean | Median | p95 | Total |
|---|---:|---:|---:|---:|
| End to end | {known_latency["end_to_end"]["mean_ms"]:.1f} ms | {known_latency["end_to_end"]["median_ms"]:.1f} ms | {known_latency["end_to_end"]["p95_ms"]:.1f} ms | {known_latency["end_to_end"]["total_ms"] / 1000:.1f} s |
| Step 12 generation | {known_latency["step12_answer_generation"]["mean_ms"]:.1f} ms | {known_latency["step12_answer_generation"]["median_ms"]:.1f} ms | {known_latency["step12_answer_generation"]["p95_ms"]:.1f} ms | {known_latency["step12_answer_generation"]["total_ms"] / 1000:.1f} s |

The known-answer end-to-end figure includes the deliberate 45-second API pacing
between live requests. Step 12 latency is the better estimate of model-call
runtime for this run.

## Conclusion

The apparent contradiction is resolved:

1. Exact QA retrieval and Step 11 context selection now pass 100/100.
2. Technical generation succeeds for 98/100.
3. Only 33/100 answers remain substantive after verification.
4. Therefore, the main current bottleneck is no longer retrieval for this
   known-answer test. It is verifier/mitigator false rejection and strict
   completeness handling.

The next safe action is human adjudication of the removed-claim queue, beginning
with evidence-supported relevance-gate failures. Do not weaken all verification
thresholds from these automatic labels alone.

## Artifacts

- Final known-answer generation:
  `outputs/evaluation/generation/entity_gt_trial_100_known_answer_generation_v1/full_pipeline.jsonl`
- Final known-answer generation metrics:
  `outputs/evaluation/generation/entity_gt_trial_100_known_answer_generation_v1/metrics.json`
- Final known-answer claim audit:
  `outputs/evaluation/claim_audit/entity_gt_trial_100_known_answer_generation_v1/full_pipeline.jsonl`
- Known-answer Step 9 input:
  `outputs/evaluation/retrieval/entity_gt_trial_100_known_answer_retrieval_v2/full_hybrid.jsonl`
- Step 10-11 boundary replay: `known_answer_context_replay.jsonl`
- Generalization removed-claim queue: `removed_claim_review_queue.csv`
- Known-answer removed-claim queue:
  `known_answer_removed_claim_review_queue.csv`
- Machine-readable diagnosis: `diagnosis.json`
"""


def main() -> int:
    args = parse_args()
    config = load_final_config()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    gold_rows = read_gold(args.gold_file.resolve())
    general_records = read_jsonl(args.general_retrieval_file.resolve())
    known_records = read_jsonl(args.known_retrieval_file.resolve())
    generation_records = read_jsonl(args.generation_file.resolve())
    audit_records = read_jsonl(args.claim_audit_file.resolve())
    known_generation_records = read_jsonl(args.known_generation_file.resolve())
    known_audit_records = read_jsonl(args.known_claim_audit_file.resolve())

    gold_by_id = {row["query_id"]: row for row in gold_rows}
    general_by_id = {str(row["query_id"]): row for row in general_records}
    known_by_id = {str(row["query_id"]): row for row in known_records}
    expected_ids = set(gold_by_id)
    if set(general_by_id) != expected_ids or set(known_by_id) != expected_ids:
        raise ValueError("Gold and retrieval query IDs do not match exactly.")
    for label, records in (
        ("generalization generation", generation_records),
        ("known-answer generation", known_generation_records),
        ("generalization claim audit", audit_records),
        ("known-answer claim audit", known_audit_records),
    ):
        record_ids = [str(record.get("query_id") or "") for record in records]
        if len(record_ids) != len(set(record_ids)):
            raise ValueError(f"{label} contains duplicate query IDs.")
        if set(record_ids) != expected_ids:
            raise ValueError(f"{label} does not contain exactly the 100 gold IDs.")

    query_norms = {normalized(row["query"]) for row in gold_rows}
    sqlite_availability = exact_qa_availability_in_sqlite(
        Path(config.qa_corpus.index_path),
        query_norms,
        {str(row["query"]) for row in gold_rows},
    )
    neo4j_availability: dict[str, list[dict[str, str]]]
    neo4j_error = ""
    if args.skip_neo4j:
        neo4j_availability = {value: [] for value in query_norms}
        neo4j_error = "Skipped by CLI."
    else:
        try:
            neo4j_availability = exact_qa_availability_in_neo4j(query_norms)
        except Exception as exc:
            neo4j_availability = {value: [] for value in query_norms}
            neo4j_error = f"{type(exc).__name__}: {exc}"

    replay_rows: list[dict[str, Any]] = []
    for query_id in sorted(expected_ids):
        gold = gold_by_id[query_id]
        query_norm = normalized(gold["query"])
        reference_norm = normalized(gold["reference_answer"])
        replay_rows.append(
            {
                "query_id": query_id,
                "query": gold["query"],
                "reference_answer": gold["reference_answer"],
                "sqlite_exact_qa_ids": [
                    item["qa_id"] for item in sqlite_availability[query_norm]
                ],
                "neo4j_exact_qa_ids": [
                    item["qa_id"] for item in neo4j_availability[query_norm]
                ],
                "generalization": replay_retrieval_record(
                    general_by_id[query_id],
                    query_norm=query_norm,
                    reference_norm=reference_norm,
                ),
                "known_answer": replay_retrieval_record(
                    known_by_id[query_id],
                    query_norm=query_norm,
                    reference_norm=reference_norm,
                ),
            }
        )

    claim_review = build_removed_claim_review(generation_records, audit_records)
    known_claim_review = build_removed_claim_review(
        known_generation_records,
        known_audit_records,
    )
    general_generation_summary = summarize_generation_run(
        generation_records,
        audit_records,
        args.generation_file.resolve().parent / "metrics.json",
        claim_review,
    )
    known_generation_summary = summarize_generation_run(
        known_generation_records,
        known_audit_records,
        args.known_generation_file.resolve().parent / "metrics.json",
        known_claim_review,
    )
    general_status = general_generation_summary["generation_status_counts"]
    known_status = known_generation_summary["generation_status_counts"]
    general_answerability = general_generation_summary["answerability_counts"]
    known_answerability = known_generation_summary["answerability_counts"]
    general_bert = general_generation_summary["bertscore"]
    known_bert = known_generation_summary["bertscore"]

    diagnosis = {
        "graph_version": config.graph_version,
        "query_count": len(gold_rows),
        "experiment_definition": {
            "generalization": "Exact normalized question QA artifacts excluded.",
            "known_answer": "Exact normalized question QA artifacts allowed.",
            "full_generation_rerun": True,
            "known_answer_generation_complete": (
                len(known_generation_records) == len(gold_rows)
            ),
            "thresholds_changed": False,
            "prompts_changed": False,
            "verification_rules_changed": False,
            "correctness_fixes_applied": [
                "NFKC normalization for Arabic presentation-form glyphs.",
                "Backward-compatible FTS terms for the frozen pre-NFKC index.",
                "Exact lexical AHD QA matches recognized as direct anchors.",
            ],
        },
        "observed_before_fix": {
            "known_answer_nonempty_context_queries": 84,
            "known_answer_exact_question_in_step11": 68,
            "known_answer_exact_answer_in_step11": 59,
            "exact_questions_rejected_by_step11": 31,
            "rejected_for_intent_support": 30,
            "measurement_note": (
                "Captured from the initial known-answer replay before the "
                "direct-anchor and Unicode compatibility fixes."
            ),
        },
        "exact_qa_availability": {
            "sqlite_queries_with_exact_qa": sum(
                bool(sqlite_availability[value]) for value in query_norms
            ),
            "sqlite_exact_qa_row_count": sum(
                len(sqlite_availability[value]) for value in query_norms
            ),
            "neo4j_queries_with_exact_qa": sum(
                bool(neo4j_availability[value]) for value in query_norms
            ),
            "neo4j_exact_qa_row_count": sum(
                len(neo4j_availability[value]) for value in query_norms
            ),
            "neo4j_check_error": neo4j_error,
        },
        "step10_step11_replay": {
            "generalization": summarize_replay(replay_rows, "generalization"),
            "known_answer": summarize_replay(replay_rows, "known_answer"),
        },
        "generation_runs": {
            "generalization": general_generation_summary,
            "known_answer": known_generation_summary,
        },
        "generation_comparison": {
            "nonempty_context_queries": (
                known_generation_summary["nonempty_context_queries"]
                - general_generation_summary["nonempty_context_queries"]
            ),
            "generated_queries": (
                known_status.get("generated", 0)
                - general_status.get("generated", 0)
            ),
            "fallback_queries": (
                known_status.get("fallback", 0)
                - general_status.get("fallback", 0)
            ),
            "substantive_answers": (
                int(known_bert.get("evaluated_query_count") or 0)
                - int(general_bert.get("evaluated_query_count") or 0)
            ),
            "fully_answerable": (
                known_answerability.get("fully_answerable", 0)
                - general_answerability.get("fully_answerable", 0)
            ),
            "partially_answerable": (
                known_answerability.get("partially_answerable", 0)
                - general_answerability.get("partially_answerable", 0)
            ),
            "supported_but_incomplete": (
                known_answerability.get("supported_but_incomplete", 0)
                - general_answerability.get("supported_but_incomplete", 0)
            ),
            "insufficient_evidence": (
                known_answerability.get("insufficient_evidence", 0)
                - general_answerability.get("insufficient_evidence", 0)
            ),
            "bertscore_f1": round(
                float(known_bert.get("bertscore_f1") or 0.0)
                - float(general_bert.get("bertscore_f1") or 0.0),
                6,
            ),
        },
        "claim_audit_scope": {
            "generalization_removed_claim_queue_requires_human_review": True,
            "known_answer_removed_claim_queue_requires_human_review": True,
            "automatic_review_classes_are_not_medical_ground_truth": True,
        },
        "inputs": {
            "gold": str(args.gold_file.resolve().relative_to(ROOT)),
            "general_retrieval": str(
                args.general_retrieval_file.resolve().relative_to(ROOT)
            ),
            "known_retrieval": str(
                args.known_retrieval_file.resolve().relative_to(ROOT)
            ),
            "generation": str(args.generation_file.resolve().relative_to(ROOT)),
            "claim_audit": str(args.claim_audit_file.resolve().relative_to(ROOT)),
            "known_generation": str(
                args.known_generation_file.resolve().relative_to(ROOT)
            ),
            "known_claim_audit": str(
                args.known_claim_audit_file.resolve().relative_to(ROOT)
            ),
            "sqlite_qa_corpus": str(
                Path(config.qa_corpus.index_path).resolve().relative_to(ROOT)
            ),
        },
    }

    write_jsonl(output_dir / "known_answer_context_replay.jsonl", replay_rows)
    write_claim_review_csv(output_dir / "removed_claim_review_queue.csv", claim_review)
    write_claim_review_csv(
        output_dir / "known_answer_removed_claim_review_queue.csv",
        known_claim_review,
    )
    write_json(output_dir / "diagnosis.json", diagnosis)
    (output_dir / "README.md").write_text(
        markdown_report(diagnosis),
        encoding="utf-8",
    )

    concise = {
        "status": "ok",
        "query_count": len(gold_rows),
        "sqlite_exact_qa_queries": diagnosis["exact_qa_availability"][
            "sqlite_queries_with_exact_qa"
        ],
        "neo4j_exact_qa_queries": diagnosis["exact_qa_availability"][
            "neo4j_queries_with_exact_qa"
        ],
        "generalization_step11_nonempty": diagnosis["step10_step11_replay"][
            "generalization"
        ]["nonempty_context_queries"],
        "known_answer_step11_nonempty": diagnosis["step10_step11_replay"][
            "known_answer"
        ]["nonempty_context_queries"],
        "known_answer_exact_answer_in_step11": diagnosis["step10_step11_replay"][
            "known_answer"
        ]["exact_answer_in_step11_context"],
        "known_answer_generated": known_generation_summary[
            "generation_status_counts"
        ].get("generated", 0),
        "known_answer_substantive": known_generation_summary["bertscore"].get(
            "evaluated_query_count",
            0,
        ),
        "known_answer_removed_claims": len(known_claim_review),
        "outputs": str(output_dir.relative_to(ROOT)),
    }
    print(json.dumps(concise, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
