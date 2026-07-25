from __future__ import annotations

from dataclasses import replace

from src.config import AppConfig, load_final_config
from src.evidence_policy import source_reliability_prior
from src.models import HybridRetrievalBundle, RerankedSubgraph, RetrievedEvidence, RetrievedMedicalRelation
from src.query_relevance import candidate_relevance_features, minimum_candidate_concept_coverage
from src.step09_hybrid_retrieval import (
    lexical_overlap,
    medical_identity_similarity,
    token_set,
)


INTENT_CUES = {
    "treatment_request": {"علاج", "دواء", "ادويه", "يستخدم", "تناول", "جراحه"},
    "symptom_request": {"عرض", "اعراض", "علامه", "يشعر", "الم", "حمى"},
    "diagnosis_request": {"تشخيص", "يعاني", "اصابه", "مرض"},
    "test_request": {"فحص", "تحليل", "تحاليل", "اشعه", "تصوير", "مختبر"},
    "cause_request": {"سبب", "اسباب", "يسبب", "تسبب", "ناتج"},
    "prevention_request": {"وقايه", "تجنب", "منع"},
}


def evidence_source_prior(item: RetrievedEvidence) -> float:
    return source_reliability_prior(item.source_quality)


def intent_support(primary_intent: str, text: str) -> float:
    cues = INTENT_CUES.get(primary_intent, set())
    if not cues:
        return 0.5
    normalized_tokens = {token.removeprefix("ال") for token in token_set(text)}
    return 1.0 if normalized_tokens & cues else 0.0


def rerank_subgraph(
    bundle: HybridRetrievalBundle,
    config: AppConfig | None = None,
) -> RerankedSubgraph:
    config = config or load_final_config()
    query = bundle.reformulated_query or bundle.query
    evidence_by_relation: dict[str, list[RetrievedEvidence]] = {}
    evidence_by_qa: dict[str, list[RetrievedEvidence]] = {}
    for item in bundle.evidence:
        for relation_id in item.relation_ids:
            evidence_by_relation.setdefault(relation_id, []).append(item)
        if item.qa_id:
            evidence_by_qa.setdefault(item.qa_id, []).append(item)

    reranked_relations: list[RetrievedMedicalRelation] = []
    for relation in bundle.relations:
        supporting = [
            *evidence_by_relation.get(relation.relation_id, []),
            *evidence_by_qa.get(relation.qa_id, []),
        ]
        source_prior = max((evidence_source_prior(item) for item in supporting), default=0.6)
        query_support = max(
            relation.evidence_relevance,
            lexical_overlap(query, relation.evidence),
            lexical_overlap(query, f"{relation.source_name} {relation.target_name}"),
        )
        identity_score = float(relation.metadata.get("identity_score") or 0.0)
        total_penalty = float(relation.metadata.get("total_penalty") or 0.0)
        intent_match = (
            1.0
            if relation.relation_type in set(bundle.plan.preferred_relation_types)
            else (0.45 if not bundle.plan.preferred_relation_types else 0.15)
        )
        candidate_text = " ".join(
            [
                relation.source_name,
                relation.target_name,
                relation.evidence,
                *[
                    " ".join(
                        (
                            str(item.get("question") or ""),
                            str(item.get("evidence") or ""),
                            str(item.get("answer") or ""),
                        )
                    )
                    for item in relation.metadata.get("evidence_items", [])
                ],
            ]
        )
        relevance = candidate_relevance_features(
            query,
            candidate_text,
            source_quality=max(
                (
                    str(item.source_quality or "unknown")
                    for item in supporting
                ),
                key=source_reliability_prior,
                default="unknown",
            ),
            intent_support=intent_match,
            vector_similarity=relation.semantic_support,
            graph_support=1.0,
            retrieval_score=relation.hybrid_score,
            query_medical_phrases=bundle.query_medical_phrases,
        )
        concept_coverage = float(relevance["query_concept_coverage"])
        constraint_coverage = float(relevance["query_constraint_coverage"])
        anatomy_mismatch = bool(relevance["anatomy_mismatch"])
        unrelated_condition_mismatch = bool(relevance["unrelated_condition_mismatch"])
        concept_floor = minimum_candidate_concept_coverage(
            int(relevance["query_concept_count"])
        )
        concept_penalty = (
            0.25
            if concept_floor > 0.0 and concept_coverage < concept_floor
            else 0.0
        )
        rerank_score = (
            0.18 * relation.hybrid_score
            + 0.03 * relation.confidence
            + 0.07 * relation.semantic_support
            + 0.12 * query_support
            + 0.18 * identity_score
            + 0.22 * concept_coverage
            + 0.08 * constraint_coverage
            + 0.06 * source_prior
            + 0.06 * intent_match
            - 0.35 * total_penalty
            - concept_penalty
            - (0.40 if anatomy_mismatch else 0.0)
            - (0.35 if unrelated_condition_mismatch else 0.0)
        )
        metadata = dict(relation.metadata)
        metadata.update(
            {
                "source_quality_prior": round(source_prior, 6),
                "query_support": round(query_support, 6),
                "intent_match": round(intent_match, 6),
                **relevance,
                "concept_floor": round(concept_floor, 6),
                "rank_reason": (
                    "query_concept_coverage+identity+intent+constraints+semantic+"
                    "source_quality-anatomy-unrelated_condition"
                ),
            }
        )
        reranked_relations.append(
            replace(
                relation,
                hybrid_score=round(max(0.0, min(1.0, rerank_score)), 6),
                metadata=metadata,
            )
        )
    reranked_relations.sort(key=lambda item: item.hybrid_score, reverse=True)
    reranked_relations = reranked_relations[: min(config.retrieval.relation_top_k, 12)]
    selected_relation_ids = {item.relation_id for item in reranked_relations}
    selected_qa_ids = {item.qa_id for item in reranked_relations if item.qa_id}

    reranked_evidence: list[RetrievedEvidence] = []
    for item in bundle.evidence:
        original_score = max(0.0, min(1.0, float(item.score or 0.0)))
        question_relevance = lexical_overlap(query, item.question)
        original_question_relevance = lexical_overlap(bundle.query, item.question)
        passage_relevance = lexical_overlap(query, " ".join([item.text, item.answer]))
        relation_support = 1.0 if selected_relation_ids.intersection(item.relation_ids) else 0.0
        qa_support = 1.0 if item.qa_id and item.qa_id in selected_qa_ids else 0.0
        direct_qa = 1.0 if item.evidence_id.startswith("qa::") else 0.0
        inferred_vector_candidate = bool(
            not item.relation_ids
            and item.evidence_id.startswith(("qa::", "mention::"))
            and not item.metadata.get("retrieval_channel")
        )
        vector_similarity = float(
            item.metadata.get("vector_similarity")
            or (
                original_score
                if item.metadata.get("retrieval_channel") == "vector"
                or inferred_vector_candidate
                else 0.0
            )
        )
        entity_identity = medical_identity_similarity(query, item.question)
        if relation_support:
            entity_identity = max(entity_identity, medical_identity_similarity(query, item.text))
        evidence_intent_support = intent_support(
            bundle.plan.primary_intent,
            f"{item.question} {item.text}",
        )
        candidate_text = " ".join((item.question, item.text, item.answer))
        relevance = candidate_relevance_features(
            query,
            candidate_text,
            source_quality=item.source_quality or "unknown",
            intent_support=evidence_intent_support,
            vector_similarity=vector_similarity,
            graph_support=max(relation_support, qa_support),
            retrieval_score=original_score,
            query_medical_phrases=bundle.query_medical_phrases,
        )
        concept_coverage = float(relevance["query_concept_coverage"])
        constraint_coverage = float(relevance["query_constraint_coverage"])
        anatomy_mismatch = bool(relevance["anatomy_mismatch"])
        unrelated_condition_mismatch = bool(relevance["unrelated_condition_mismatch"])
        concept_floor = minimum_candidate_concept_coverage(
            int(relevance["query_concept_count"])
        )
        generic_match = bool(
            int(relevance["query_concept_count"]) > 0
            and int(relevance["candidate_concept_count"]) == 0
        )
        answer_relevance = (
            0.25 * question_relevance
            + 0.25 * entity_identity
            + 0.30 * concept_coverage
            + 0.15 * evidence_intent_support
            + 0.05 * constraint_coverage
            - (0.45 if anatomy_mismatch else 0.0)
            - (0.30 if unrelated_condition_mismatch else 0.0)
            - (0.10 if generic_match else 0.0)
        )
        if relation_support:
            answer_relevance = max(
                answer_relevance,
                0.25 * medical_identity_similarity(query, item.text)
                + 0.30 * concept_coverage
                + 0.20 * evidence_intent_support
                + 0.15 * constraint_coverage
                + 0.10
                - (0.45 if anatomy_mismatch else 0.0)
                - (0.30 if unrelated_condition_mismatch else 0.0),
            )
        semantic_anchor = max(question_relevance, passage_relevance, entity_identity)
        direct_question_anchor = bool(
            original_question_relevance >= 0.85
            and vector_similarity >= 0.90
            and not anatomy_mismatch
        )
        strong_semantic_match = bool(
            vector_similarity >= config.retrieval.context_semantic_min_score
            and semantic_anchor >= 0.10
            and (
                concept_floor == 0.0
                or concept_coverage >= concept_floor
            )
            and not unrelated_condition_mismatch
        )
        if strong_semantic_match and not anatomy_mismatch:
            semantic_answer_relevance = (
                0.55 * vector_similarity
                + 0.25 * semantic_anchor
                + 0.20 * evidence_intent_support
            )
            answer_relevance = max(answer_relevance, semantic_answer_relevance)
        if direct_question_anchor:
            answer_relevance = max(
                answer_relevance,
                0.55 * original_question_relevance
                + 0.25 * vector_similarity
                + 0.20 * max(0.5, evidence_intent_support),
            )
        if anatomy_mismatch:
            answer_relevance = 0.0
        query_relevance = (
            0.75 * question_relevance + 0.25 * passage_relevance
            if direct_qa
            else max(question_relevance, passage_relevance)
        )
        passage_only_penalty = (
            0.15 if direct_qa and question_relevance < 0.05 and passage_relevance > 0.0 else 0.0
        )
        score = (
            0.10 * original_score
            + 0.24 * max(0.0, answer_relevance)
            + 0.12 * query_relevance
            + 0.20 * concept_coverage
            + 0.08 * constraint_coverage
            + 0.10 * evidence_source_prior(item)
            + 0.06 * evidence_intent_support
            + 0.05 * max(relation_support, qa_support)
            + 0.05 * direct_qa
            - passage_only_penalty
            - (
                0.20
                if concept_floor > 0.0
                and concept_coverage < concept_floor
                and not direct_question_anchor
                else 0.0
            )
            - (0.40 if anatomy_mismatch else 0.0)
            - (0.30 if unrelated_condition_mismatch else 0.0)
            - (0.10 if generic_match else 0.0)
        )
        metadata = dict(item.metadata)
        metadata.update(
            {
                "question_relevance": round(question_relevance, 6),
                "original_question_relevance": round(original_question_relevance, 6),
                "passage_relevance": round(passage_relevance, 6),
                "entity_identity": round(entity_identity, 6),
                "intent_support": round(evidence_intent_support, 6),
                **relevance,
                "concept_floor": round(concept_floor, 6),
                "generic_match": generic_match,
                "retrieval_channel": item.metadata.get("retrieval_channel")
                or ("vector" if inferred_vector_candidate else "graph"),
                "vector_similarity": round(vector_similarity, 6),
                "strong_semantic_match": strong_semantic_match,
                "direct_question_anchor": direct_question_anchor,
                "answer_relevance": round(max(0.0, min(1.0, answer_relevance)), 6),
                "rank_reason": (
                    "query_concept_coverage+identity+intent+constraints+semantic+"
                    "source_quality-anatomy-unrelated_condition"
                ),
            }
        )
        reranked_evidence.append(
            replace(
                item,
                score=round(max(0.0, min(1.0, score)), 6),
                metadata=metadata,
            )
        )
    reranked_evidence.sort(key=lambda item: item.score, reverse=True)
    reranked_evidence = reranked_evidence[: config.retrieval.context_top_k]

    warnings = list(bundle.warnings)
    if reranked_evidence and all(item.source_quality == "mention_evidence" for item in reranked_evidence):
        warnings.append("All retained evidence has reconstructed provenance; reliability must remain low.")
    return RerankedSubgraph(
        query=bundle.query,
        primary_intent=bundle.plan.primary_intent,
        query_medical_phrases=bundle.query_medical_phrases,
        relations=reranked_relations,
        evidence=reranked_evidence,
        warnings=list(dict.fromkeys(warnings)),
    )
