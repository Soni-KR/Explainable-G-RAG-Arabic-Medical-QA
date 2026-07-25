from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path
from time import perf_counter
from typing import Any

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.config import AppConfig, load_final_config
from src.evaluation_metrics import (
    bertscore_f1,
    claim_grounding_metrics,
    ragas_metric_status,
    retrieval_metrics,
)
from src.models import EvidenceContextBundle, ExplainableMedicalAnswer
from src.neo4j_repository import Neo4jRepository
from src.step08b_analyze_query import analyze_and_link_query
from src.step08d_plan_retrieval import build_retrieval_plan
from src.step09_hybrid_retrieval import (
    add_semantic_qa_fallback,
    retrieve_hybrid,
    semantic_qa_fallback_eligible,
)
from src.step10_rerank_subgraph import rerank_subgraph
from src.step11_build_evidence_context import build_evidence_context
from src.step12_generate_grounded_answer import generate_grounded_answer
from src.step13_extract_claims import extract_claims
from src.step14_verify_claims import verify_claims
from src.step15_mitigate_hallucinations import mitigate_hallucinations
from src.step16_score_reliability import score_reliability


def context_only_payload(context: EvidenceContextBundle) -> dict[str, Any]:
    return {"stage": "step11_context", **asdict(context)}


def run_explainable_pipeline(
    query: str,
    config: AppConfig | None = None,
    repository: Neo4jRepository | None = None,
    embedding_model: Any | None = None,
    relevant_context_ids: set[str] | None = None,
    relevance_grades: dict[str, float] | None = None,
    reference_answer: str = "",
) -> ExplainableMedicalAnswer:
    config = config or load_final_config()
    owns_repository = repository is None
    repository = repository or Neo4jRepository(config=config)
    pipeline_started = perf_counter()
    timings: dict[str, float] = {}

    def record_timing(name: str, started: float) -> None:
        timings[name] = round((perf_counter() - started) * 1000.0, 3)

    try:
        started = perf_counter()
        analysis, linking = analyze_and_link_query(query, repository=repository, config=config)
        record_timing("step08_query_understanding", started)

        started = perf_counter()
        plan = build_retrieval_plan(analysis, linking, config=config)
        record_timing("step08_retrieval_planning", started)

        started = perf_counter()
        retrieval = retrieve_hybrid(
            analysis,
            linking,
            plan,
            repository=repository,
            config=config,
            model=embedding_model,
        )
        record_timing("step09_hybrid_retrieval", started)

        started = perf_counter()
        subgraph = rerank_subgraph(retrieval, config=config)
        record_timing("step10_subgraph_reranking", started)

        started = perf_counter()
        context = build_evidence_context(subgraph, analysis.reformulated_query, config=config)
        record_timing("step11_context_construction", started)

        if semantic_qa_fallback_eligible(
            retrieval,
            context_has_evidence=bool(context.evidence_items),
            config=config,
        ):
            started = perf_counter()
            retrieval = add_semantic_qa_fallback(
                retrieval,
                config=config,
                model=embedding_model,
            )
            record_timing("step09_semantic_qa_fallback", started)
            started = perf_counter()
            subgraph = rerank_subgraph(retrieval, config=config)
            record_timing("step10_fallback_reranking", started)
            started = perf_counter()
            context = build_evidence_context(
                subgraph,
                analysis.reformulated_query,
                config=config,
            )
            record_timing("step11_fallback_context_construction", started)

        started = perf_counter()
        generated = generate_grounded_answer(context, config=config)
        record_timing("step12_answer_generation", started)

        started = perf_counter()
        claims = extract_claims(generated)
        record_timing("step13_claim_extraction", started)

        started = perf_counter()
        verifications = verify_claims(claims, context)
        record_timing("step14_claim_verification", started)

        started = perf_counter()
        mitigated = mitigate_hallucinations(generated, verifications, context=context)
        record_timing("step15_hallucination_mitigation", started)

        started = perf_counter()
        reliability = score_reliability(mitigated, verifications, context)
        record_timing("step16_reliability_scoring", started)
        timings["end_to_end"] = round((perf_counter() - pipeline_started) * 1000.0, 3)

        supported_relation_ids = {
            relation_id
            for item in verifications
            if item.status == "supported"
            for relation_id in item.supporting_relation_ids
        }
        valid_evidence_ids = {
            evidence_id
            for item in verifications
            if item.status == "supported"
            for evidence_id in item.valid_citations
        }
        linked_entities = [
            {
                "entity_id": item.linked_entity_id,
                "canonical_name": item.linked_canonical_name,
                "entity_type": item.linked_entity_type,
                "match_type": item.match_type,
                "match_score": item.match_score,
            }
            for item in linking.linked_entities
            if item.status == "linked"
        ]
        supporting_relations = [
            item for item in context.graph_facts if item.get("relation_id") in supported_relation_ids
        ]
        evidence = [
            item for item in context.evidence_items if item.get("evidence_id") in valid_evidence_ids
        ]
        claim_audit = [
            {
                "claim": item.claim.claim,
                "status": item.status,
                "support_score": item.support_score,
                "question_relevance": item.question_relevance,
                "query_concept_coverage": item.query_concept_coverage,
                "best_evidence_id": item.best_evidence_id,
                "valid_citations": item.valid_citations,
                "valid_qa_ids": item.valid_qa_ids,
                "supporting_relation_ids": item.supporting_relation_ids,
                "failed_checks": item.failed_checks,
                "reason": item.reason,
            }
            for item in verifications
        ]
        warnings = list(
            dict.fromkeys(
                [
                    *analysis.warnings,
                    *linking.warnings,
                    *plan.warnings,
                    *retrieval.warnings,
                    *subgraph.warnings,
                    *context.warnings,
                    *generated.warnings,
                    "Reliability is a deterministic heuristic and has not been calibrated against gold labels.",
                ]
            )
        )
        ranked_context_ids = [
            str(item.get("qa_id") or item.get("source_id") or item.get("evidence_id") or "")
            for item in context.evidence_items
        ]
        relevant_ids = set(relevant_context_ids or set())
        grades = dict(relevance_grades or {})
        relevant_ids.update(grades)
        metrics = {
            "retrieval_and_context": retrieval_metrics(ranked_context_ids, relevant_ids, grades or None),
            "final_answer": {
                **claim_grounding_metrics([item.status for item in verifications]),
                "bertscore": bertscore_f1(mitigated.answer, reference_answer),
                "ragas": ragas_metric_status(bool(reference_answer and relevant_ids)),
            },
            "reliability": {
                "score": reliability.score,
                "calibrated": reliability.calibrated,
                "status": (
                    "heuristic_only"
                    if not reliability.calibrated
                    else "calibrated"
                ),
                "gold_label_metrics": "Use src/evaluation_metrics.py with a labeled JSONL cohort.",
            },
            "efficiency": {
                "end_to_end_latency_ms": timings["end_to_end"],
                "stage_latency_ms": {key: value for key, value in timings.items() if key != "end_to_end"},
            },
        }
        return ExplainableMedicalAnswer(
            query=query,
            answer=mitigated.answer,
            answerability=mitigated.answerability,
            reliability=reliability,
            query_coverage=mitigated.query_coverage,
            missing_query_concepts=mitigated.missing_query_concepts,
            retrieved_entities=linked_entities,
            supporting_relations=supporting_relations,
            evidence=evidence,
            claim_audit=claim_audit,
            removed_claims=mitigated.removed_claims,
            limitations=mitigated.limitations,
            warnings=warnings,
            metrics=metrics,
            timings_ms=timings,
        )
    finally:
        if owns_repository:
            repository.close()


def build_context_only(
    query: str,
    config: AppConfig | None = None,
    repository: Neo4jRepository | None = None,
) -> EvidenceContextBundle:
    config = config or load_final_config()
    owns_repository = repository is None
    repository = repository or Neo4jRepository(config=config)
    try:
        analysis, linking = analyze_and_link_query(query, repository=repository, config=config)
        plan = build_retrieval_plan(analysis, linking, config=config)
        retrieval = retrieve_hybrid(analysis, linking, plan, repository=repository, config=config)
        context = build_evidence_context(
            rerank_subgraph(retrieval, config=config),
            analysis.reformulated_query,
            config=config,
        )
        if semantic_qa_fallback_eligible(
            retrieval,
            context_has_evidence=bool(context.evidence_items),
            config=config,
        ):
            retrieval = add_semantic_qa_fallback(retrieval, config=config)
            context = build_evidence_context(
                rerank_subgraph(retrieval, config=config),
                analysis.reformulated_query,
                config=config,
            )
        return context
    finally:
        if owns_repository:
            repository.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the final Arabic medical Graph-RAG pipeline through Step 17.")
    parser.add_argument("--query", required=True, help="Arabic medical query.")
    parser.add_argument("--context-only", action="store_true", help="Stop after Step 11 without answer generation.")
    parser.add_argument(
        "--relevant-context-id",
        action="append",
        default=[],
        help="Independent relevant QA/source ID; repeat to enable Recall@5 and MRR.",
    )
    parser.add_argument(
        "--relevance-grade",
        action="append",
        default=[],
        metavar="ID=GRADE",
        help="Independent graded relevance judgment; repeat to enable nDCG@10.",
    )
    parser.add_argument("--reference-answer", default="", help="Gold answer used only for optional BERTScore/RAGAS.")
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        grades: dict[str, float] = {}
        for raw_grade in args.relevance_grade:
            item_id, separator, value = raw_grade.partition("=")
            if not separator or not item_id.strip():
                raise ValueError("Each --relevance-grade must use ID=GRADE.")
            grades[item_id.strip()] = float(value)
        payload = (
            context_only_payload(build_context_only(args.query))
            if args.context_only
            else asdict(
                run_explainable_pipeline(
                    args.query,
                    relevant_context_ids=set(args.relevant_context_id),
                    relevance_grades=grades,
                    reference_answer=args.reference_answer,
                )
            )
        )
    except Exception as exc:
        print(json.dumps({"status": "failed", "error": type(exc).__name__}, ensure_ascii=False, indent=2))
        return 1
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
