from __future__ import annotations

from collections import defaultdict

from src.config import AppConfig, load_final_config
from src.evidence_policy import (
    QUESTION_EVIDENCE,
    authoritative_evidence_texts,
    infer_evidence_origin,
)
from src.models import EvidenceContextBundle, RerankedSubgraph, RetrievedEvidence
from src.query_relevance import (
    candidate_relevance_features,
    matched_query_concepts,
    minimum_candidate_concept_coverage,
    query_concept_coverage,
)
from src.step08a_normalize_query import normalize_query
from src.step09_hybrid_retrieval import lexical_overlap


INTENTS_REQUIRING_DIRECT_SUPPORT = {
    "treatment_request",
    "symptom_request",
    "diagnosis_request",
    "test_request",
    "cause_request",
    "prevention_request",
}


def compact(text: str, limit: int) -> str:
    text = " ".join(str(text or "").split())
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def item_answer_relevance(item: RetrievedEvidence, query: str) -> float:
    if "answer_relevance" in item.metadata:
        return float(item.metadata.get("answer_relevance") or 0.0)
    return max(
        lexical_overlap(query, item.question),
        lexical_overlap(query, f"{item.text} {item.answer}"),
    )


def has_strong_semantic_support(item: RetrievedEvidence, config: AppConfig) -> bool:
    """Recognize vetted vector evidence without weakening hard safety gates."""
    return bool(
        item.metadata.get("strong_semantic_match")
        and float(item.metadata.get("vector_similarity") or 0.0)
        >= config.retrieval.context_semantic_min_score
        and not item.metadata.get("anatomy_mismatch")
    )


def has_direct_question_anchor(item: RetrievedEvidence) -> bool:
    """Honor the anchor decision made from the original query in Step 10."""
    return bool(
        item.metadata.get("direct_question_anchor")
        and float(item.metadata.get("original_question_relevance") or 0.0) >= 0.85
    )


def item_relevance_features(
    item: RetrievedEvidence,
    query: str,
    query_medical_phrases: list[str] | None = None,
) -> dict[str, object]:
    """Use Step 10 features when present and deterministically fill older artifacts."""
    computed = candidate_relevance_features(
        query,
        " ".join((item.question, item.text, item.answer)),
        source_quality=item.source_quality or "unknown",
        intent_support=float(item.metadata.get("intent_support") or 0.0),
        vector_similarity=float(item.metadata.get("vector_similarity") or 0.0),
        graph_support=1.0 if item.relation_ids else 0.0,
        retrieval_score=float(item.score or 0.0),
        query_medical_phrases=query_medical_phrases,
    )
    for key in computed:
        if key in item.metadata:
            computed[key] = item.metadata[key]
    return computed


def select_context_evidence(
    subgraph: RerankedSubgraph,
    query: str,
    config: AppConfig,
) -> list[RetrievedEvidence]:
    """Keep only candidates that pass absolute clinical-relevance gates."""
    if not subgraph.evidence:
        return []

    ranked: list[RetrievedEvidence] = []
    for item in subgraph.evidence:
        evidence_origin = infer_evidence_origin(
            evidence_origin=item.metadata.get("evidence_origin"),
            field=item.metadata.get("field"),
            source_quality=item.source_quality,
            evidence=item.text,
            source_question=item.question,
            source_answer=item.answer,
        )
        # A question-only entity mention can help retrieval, but it cannot be
        # passed to the generator as medical evidence. Relation-backed items
        # remain eligible because their validated fact is handled separately.
        if (
            evidence_origin == QUESTION_EVIDENCE
            and not item.answer.strip()
            and not item.relation_ids
        ):
            continue
        features = item_relevance_features(item, query, subgraph.query_medical_phrases)
        answer_relevance = item_answer_relevance(item, query)
        direct_anchor = has_direct_question_anchor(item)
        semantic_support = has_strong_semantic_support(item, config)
        concept_count = int(features["query_concept_count"])
        concept_coverage = float(features["query_concept_coverage"])
        concept_floor = minimum_candidate_concept_coverage(concept_count)
        intent_score = float(features["intent_support"])
        if bool(features["anatomy_mismatch"]) and not direct_anchor:
            continue
        if bool(features["unrelated_condition_mismatch"]) and not direct_anchor:
            continue
        if float(features["source_reliability"]) < config.retrieval.context_min_source_reliability:
            continue
        if (
            answer_relevance < config.retrieval.context_min_answer_relevance
            and not direct_anchor
            and not semantic_support
        ):
            continue
        if (
            item.score < config.retrieval.context_min_score
            and not direct_anchor
            and not semantic_support
        ):
            continue
        if concept_floor > 0.0 and concept_coverage < concept_floor and not direct_anchor:
            continue
        if (
            subgraph.primary_intent in INTENTS_REQUIRING_DIRECT_SUPPORT
            and intent_score < config.retrieval.context_min_intent_support
            and not direct_anchor
        ):
            continue
        ranked.append(item)

    ranked.sort(
        key=lambda item: (
            float(
                item_relevance_features(
                    item,
                    query,
                    subgraph.query_medical_phrases,
                )["query_concept_coverage"]
            ),
            item_answer_relevance(item, query),
            item.score,
        ),
        reverse=True,
    )
    if not ranked:
        return []

    selected: list[RetrievedEvidence] = []
    per_qa: dict[str, int] = defaultdict(int)
    seen_content: set[tuple[str, str, str]] = set()
    covered_concepts: set[str] = set()
    top_score = ranked[0].score
    for item in ranked:
        strong_semantic_support = has_strong_semantic_support(item, config)
        direct_question_anchor = has_direct_question_anchor(item)
        question_match = lexical_overlap(query, item.question)
        passage_match = lexical_overlap(query, f"{item.text} {item.answer}")
        if (
            max(question_match, passage_match) < 0.05
            and not strong_semantic_support
            and not direct_question_anchor
        ):
            continue
        item_text = " ".join((item.question, item.text, item.answer))
        item_concepts = matched_query_concepts(
            query,
            item_text,
            subgraph.query_medical_phrases,
        )
        adds_new_concept = bool(item_concepts - covered_concepts)
        if (
            item.score < top_score - config.retrieval.context_relative_margin
            and not adds_new_concept
            and not strong_semantic_support
            and not direct_question_anchor
        ):
            continue
        content_key = (
            normalize_query(item.question).normalized_query,
            normalize_query(item.text).normalized_query,
            normalize_query(item.answer).normalized_query,
        )
        if content_key in seen_content:
            continue
        qa_key = item.qa_id or item.source_id
        if qa_key and per_qa[qa_key] >= 2:
            continue
        selected.append(item)
        seen_content.add(content_key)
        covered_concepts.update(item_concepts)
        if qa_key:
            per_qa[qa_key] += 1
        if len(selected) >= config.retrieval.context_max_items:
            break

    query_has_concepts = bool(
        selected
        and int(
            item_relevance_features(
                selected[0],
                query,
                subgraph.query_medical_phrases,
            )["query_concept_count"]
        )
        > 0
    )
    combined_candidate_text = " ".join(
        " ".join((item.question, item.text, item.answer)) for item in selected
    )
    aggregate_coverage = query_concept_coverage(
        query,
        combined_candidate_text,
        subgraph.query_medical_phrases,
    )
    if (
        query_has_concepts
        and aggregate_coverage < config.retrieval.context_min_aggregate_concept_coverage
        and not any(has_direct_question_anchor(item) for item in selected)
    ):
        return []
    return selected[: config.retrieval.context_max_items]


def build_evidence_context(
    subgraph: RerankedSubgraph,
    reformulated_query: str,
    config: AppConfig | None = None,
) -> EvidenceContextBundle:
    config = config or load_final_config()
    selected_evidence = select_context_evidence(subgraph, reformulated_query, config)
    supported_relation_ids = {
        relation_id
        for evidence in selected_evidence
        for relation_id in evidence.relation_ids
    }
    selected_relations = [
        relation
        for relation in subgraph.relations
        if relation.relation_id in supported_relation_ids
    ][: config.retrieval.context_max_items]

    graph_facts = []
    relation_id_map: dict[str, str] = {}
    for index, relation in enumerate(selected_relations, start=1):
        display_id = f"R{index}"
        relation_id_map[relation.relation_id] = display_id
        graph_facts.append(
            {
                "relation_id": display_id,
                "source_relation_id": relation.source_relation_id,
                "fact": f"{relation.source_name} --{relation.relation_type}--> {relation.target_name}",
                "confidence": relation.confidence,
                "retrieval_score": relation.hybrid_score,
                "qa_id": relation.qa_id,
                "direction": relation.direction,
            }
        )

    evidence_items = []
    allowed_qa_ids: list[str] = []
    for index, evidence in enumerate(selected_evidence, start=1):
        display_id = f"E{index}"
        relevance = item_relevance_features(
            evidence,
            reformulated_query,
            subgraph.query_medical_phrases,
        )
        relation_ids = [
            relation_id_map[item]
            for item in evidence.relation_ids
            if item in relation_id_map
        ]
        authoritative_texts, evidence_origin, question_text_excluded = (
            authoritative_evidence_texts(
                {
                    "evidence": evidence.text,
                    "source_question": evidence.question,
                    "source_answer": evidence.answer,
                    "source_quality": evidence.source_quality,
                    "field": evidence.metadata.get("field"),
                    "evidence_origin": evidence.metadata.get("evidence_origin"),
                }
            )
        )
        context_evidence = authoritative_texts[0] if authoritative_texts else ""
        evidence_items.append(
            {
                "evidence_id": display_id,
                "source_id": evidence.source_id,
                "qa_id": evidence.qa_id,
                "evidence": compact(context_evidence, 800),
                "source_question": compact(evidence.question, 500),
                "source_answer": compact(evidence.answer, 1000),
                "category": evidence.category,
                "source_quality": evidence.source_quality or "unknown",
                "field": str(evidence.metadata.get("field") or ""),
                "evidence_origin": evidence_origin,
                "question_text_excluded": question_text_excluded,
                "retrieval_score": evidence.score,
                "answer_relevance": evidence.metadata.get("answer_relevance", 0.0),
                "entity_identity": evidence.metadata.get("entity_identity", 0.0),
                "intent_support": evidence.metadata.get("intent_support", 0.0),
                "query_concept_coverage": relevance["query_concept_coverage"],
                "query_constraint_coverage": relevance["query_constraint_coverage"],
                "source_reliability": relevance["source_reliability"],
                "matched_query_concepts": relevance["matched_query_concepts"],
                "missing_query_concepts": relevance["missing_query_concepts"],
                "anatomy_mismatch": relevance["anatomy_mismatch"],
                "unrelated_condition_mismatch": relevance[
                    "unrelated_condition_mismatch"
                ],
                "vector_similarity": evidence.metadata.get("vector_similarity", 0.0),
                "original_question_relevance": evidence.metadata.get(
                    "original_question_relevance", 0.0
                ),
                "direct_question_anchor": evidence.metadata.get(
                    "direct_question_anchor", False
                ),
                "exact_question_match": evidence.metadata.get(
                    "exact_question_match", False
                ),
                "relation_ids": relation_ids,
            }
        )
        if evidence.qa_id and evidence.qa_id not in allowed_qa_ids:
            allowed_qa_ids.append(evidence.qa_id)

    warnings = list(subgraph.warnings)
    removed_count = len(subgraph.evidence) - len(selected_evidence)
    if removed_count:
        warnings.append(
            f"Step 11 removed {removed_count} low-value context items; "
            f"{len(selected_evidence)} focused items remain."
        )
    if selected_evidence and selected_evidence[0].score < config.retrieval.context_min_score:
        warnings.append("The best available evidence is below the preferred context score threshold.")
    if not evidence_items:
        warnings.append("No evidence items are available for grounded answer generation.")
    return EvidenceContextBundle(
        query=subgraph.query,
        reformulated_query=reformulated_query,
        primary_intent=subgraph.primary_intent,
        query_medical_phrases=subgraph.query_medical_phrases,
        graph_facts=graph_facts,
        evidence_items=evidence_items,
        allowed_evidence_ids=[item["evidence_id"] for item in evidence_items],
        allowed_qa_ids=allowed_qa_ids,
        warnings=list(dict.fromkeys(warnings)),
    )
