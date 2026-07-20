from __future__ import annotations

from dataclasses import replace

from src.config import AppConfig, load_final_config
from src.models import HybridRetrievalBundle, RerankedSubgraph, RetrievedEvidence, RetrievedMedicalRelation
from src.step09_hybrid_retrieval import (
    anatomy_terms,
    lexical_overlap,
    medical_identity_similarity,
    token_set,
)


SOURCE_QUALITY_PRIORS = {
    "preprocessed_id": 1.0,
    "preprocessed_source_row": 0.9,
    "ahd_heldout_safe_corpus": 0.95,
    "supplemental_dataset_validated": 0.8,
    "mention_evidence": 0.55,
    "": 0.65,
}
INTENT_CUES = {
    "treatment_request": {"علاج", "دواء", "ادويه", "يستخدم", "تناول", "جراحه"},
    "symptom_request": {"عرض", "اعراض", "علامه", "يشعر", "الم", "حمى"},
    "diagnosis_request": {"تشخيص", "يعاني", "اصابه", "مرض"},
    "test_request": {"فحص", "تحليل", "تحاليل", "اشعه", "تصوير", "مختبر"},
    "cause_request": {"سبب", "اسباب", "يسبب", "تسبب", "ناتج"},
    "prevention_request": {"وقايه", "تجنب", "منع"},
}


def evidence_source_prior(item: RetrievedEvidence) -> float:
    return SOURCE_QUALITY_PRIORS.get(item.source_quality, 0.65)


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
        rerank_score = (
            0.34 * relation.hybrid_score
            + 0.04 * relation.confidence
            + 0.08 * relation.semantic_support
            + 0.22 * query_support
            + 0.18 * identity_score
            + 0.08 * source_prior
            + 0.06 * intent_match
            - 0.35 * total_penalty
        )
        metadata = dict(relation.metadata)
        metadata.update(
            {
                "source_quality_prior": round(source_prior, 6),
                "query_support": round(query_support, 6),
                "intent_match": round(intent_match, 6),
                "rank_reason": "identity+query_support+semantic+source_quality+intent-entity_conflicts",
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
        medical_phrase_coverage = float(
            item.metadata.get("medical_phrase_coverage") or 0.0
        )
        if item.source_quality == "ahd_heldout_safe_corpus":
            entity_identity = max(entity_identity, medical_phrase_coverage)
        if relation_support:
            entity_identity = max(entity_identity, medical_identity_similarity(query, item.text))
        evidence_intent_support = intent_support(
            bundle.plan.primary_intent,
            f"{item.question} {item.text}",
        )
        query_anatomy = anatomy_terms(query)
        question_anatomy = anatomy_terms(item.question)
        anatomy_mismatch = bool(
            query_anatomy and question_anatomy and query_anatomy.isdisjoint(question_anatomy)
        )
        answer_relevance = (
            0.35 * question_relevance
            + 0.45 * entity_identity
            + 0.20 * evidence_intent_support
            - (0.30 if anatomy_mismatch else 0.0)
        )
        if relation_support:
            answer_relevance = max(
                answer_relevance,
                0.35 * medical_identity_similarity(query, item.text)
                + 0.25 * evidence_intent_support
                + 0.20
                - (0.30 if anatomy_mismatch else 0.0),
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
            0.20 * item.score
            + 0.28 * max(0.0, answer_relevance)
            + 0.18 * query_relevance
            + 0.16 * evidence_source_prior(item)
            + 0.08 * max(relation_support, qa_support)
            + 0.10 * direct_qa
            - passage_only_penalty
        )
        metadata = dict(item.metadata)
        metadata.update(
            {
                "question_relevance": round(question_relevance, 6),
                "original_question_relevance": round(original_question_relevance, 6),
                "passage_relevance": round(passage_relevance, 6),
                "entity_identity": round(entity_identity, 6),
                "medical_phrase_coverage": round(medical_phrase_coverage, 6),
                "intent_support": round(evidence_intent_support, 6),
                "anatomy_mismatch": anatomy_mismatch,
                "retrieval_channel": item.metadata.get("retrieval_channel")
                or ("vector" if inferred_vector_candidate else "graph"),
                "vector_similarity": round(vector_similarity, 6),
                "strong_semantic_match": strong_semantic_match,
                "direct_question_anchor": direct_question_anchor,
                "answer_relevance": round(max(0.0, min(1.0, answer_relevance)), 6),
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
        relations=reranked_relations,
        evidence=reranked_evidence,
        warnings=list(dict.fromkeys(warnings)),
    )
