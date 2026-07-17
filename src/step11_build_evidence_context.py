from __future__ import annotations

from collections import defaultdict

from src.config import AppConfig, load_final_config
from src.models import EvidenceContextBundle, RerankedSubgraph, RetrievedEvidence
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


def select_context_evidence(
    subgraph: RerankedSubgraph,
    query: str,
    config: AppConfig,
) -> list[RetrievedEvidence]:
    """Keep a small, score-relative context instead of filling a fixed quota."""
    if not subgraph.evidence:
        return []

    best_answer_relevance = max(
        (item_answer_relevance(item, query) for item in subgraph.evidence),
        default=0.0,
    )
    if best_answer_relevance < 0.35:
        return []
    answer_relevance_floor = max(0.35, best_answer_relevance - 0.10)
    best_entity_identity = max(
        (float(item.metadata.get("entity_identity") or 0.0) for item in subgraph.evidence),
        default=0.0,
    )
    entity_identity_floor = best_entity_identity - 0.15 if best_entity_identity >= 0.85 else 0.0
    ranked = sorted(
        (
            item
            for item in subgraph.evidence
            if item_answer_relevance(item, query) >= answer_relevance_floor
            and float(item.metadata.get("entity_identity") or 0.0) >= entity_identity_floor
            and not (
                subgraph.primary_intent in INTENTS_REQUIRING_DIRECT_SUPPORT
                and float(item.metadata.get("intent_support") or 0.0) <= 0.0
                and not item.relation_ids
            )
        ),
        key=lambda item: item.score,
        reverse=True,
    )
    if not ranked:
        return []
    top_score = ranked[0].score
    score_floor = max(
        config.retrieval.context_min_score,
        top_score - config.retrieval.context_relative_margin,
    )
    selected: list[RetrievedEvidence] = []
    per_qa: dict[str, int] = defaultdict(int)
    for item in ranked:
        if item.score < score_floor:
            continue
        question_match = lexical_overlap(query, item.question)
        passage_match = lexical_overlap(query, f"{item.text} {item.answer}")
        answer_relevance = item_answer_relevance(item, query)
        if answer_relevance < answer_relevance_floor or max(question_match, passage_match) < 0.05:
            continue
        qa_key = item.qa_id or item.source_id
        if qa_key and per_qa[qa_key] >= 2:
            continue
        selected.append(item)
        if qa_key:
            per_qa[qa_key] += 1
        if len(selected) >= config.retrieval.context_max_items:
            break

    # Preserve one relation-backed passage when it is reasonably relevant. This
    # prevents a single high-scoring vector passage from erasing the useful graph
    # channel while still avoiding fixed-quota context padding.
    if not any(item.relation_ids for item in selected):
        relation_relevance_floor = max(0.35, answer_relevance_floor - 0.25)
        for item in sorted(subgraph.evidence, key=lambda value: value.score, reverse=True):
            if not item.relation_ids or item in selected:
                continue
            answer_relevance = item_answer_relevance(item, query)
            if (
                item.score >= config.retrieval.context_min_score * 0.8
                and answer_relevance >= relation_relevance_floor
                and float(item.metadata.get("entity_identity") or 0.0) >= entity_identity_floor
                and not (
                    subgraph.primary_intent in INTENTS_REQUIRING_DIRECT_SUPPORT
                    and float(item.metadata.get("intent_support") or 0.0) <= 0.0
                )
            ):
                selected.append(item)
                break

    return sorted(selected, key=lambda item: item.score, reverse=True)[
        : config.retrieval.context_max_items
    ]


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
        relation_ids = [
            relation_id_map[item]
            for item in evidence.relation_ids
            if item in relation_id_map
        ]
        evidence_items.append(
            {
                "evidence_id": display_id,
                "source_id": evidence.source_id,
                "qa_id": evidence.qa_id,
                "evidence": compact(evidence.text, 800),
                "source_question": compact(evidence.question, 500),
                "source_answer": compact(evidence.answer, 1000),
                "category": evidence.category,
                "source_quality": evidence.source_quality or "unknown",
                "retrieval_score": evidence.score,
                "answer_relevance": evidence.metadata.get("answer_relevance", 0.0),
                "entity_identity": evidence.metadata.get("entity_identity", 0.0),
                "intent_support": evidence.metadata.get("intent_support", 0.0),
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
        graph_facts=graph_facts,
        evidence_items=evidence_items,
        allowed_evidence_ids=[item["evidence_id"] for item in evidence_items],
        allowed_qa_ids=allowed_qa_ids,
        warnings=list(dict.fromkeys(warnings)),
    )
