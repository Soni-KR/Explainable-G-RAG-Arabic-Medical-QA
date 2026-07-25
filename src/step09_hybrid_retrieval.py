from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import replace
from difflib import SequenceMatcher
from typing import Any

from src.config import AppConfig, load_final_config
from src.models import (
    HybridRetrievalBundle,
    QueryEntityLinkingResult,
    RetrievalPlanResult,
    RetrievedEvidence,
    RetrievedMedicalRelation,
    UnifiedQueryAnalysisResult,
    VectorSearchResult,
)
from src.neo4j_repository import Neo4jRepository
from src.step06_build_embedding_indexes import load_model
from src.step08a_normalize_query import normalize_query
from src.step09a_qa_corpus import search_qa_corpus


TOKEN_RE = re.compile(r"[\w\u0600-\u06ff]+", re.UNICODE)

# These terms are useful as query context, but too broad to anchor graph expansion.
GENERIC_MEDICAL_TERMS = {
    "دواء", "الدواء", "ادويه", "الادويه", "علاج", "العلاج", "مرض", "المرض",
    "تحليل", "التحليل", "تحاليل", "التحاليل", "جرعه", "الجرعه", "طبيب", "الطبيب",
}

# A conservative vocabulary is enough to catch clear anatomical mismatches without
# pretending to be a full Arabic ontology. Terms are compared only when both the
# query and graph fact explicitly name an anatomical location.
ANATOMY_TERMS = {
    "راس", "دماغ", "عين", "اذن", "انف", "فم", "وجه", "اسنان", "سن", "ضرس", "حلق", "مريء", "مري", "مرئ",
    "رقبه", "صدر", "رئه", "قلب", "بطن", "معده", "قولون", "كبد", "كليه", "كلي",
    "ظهر", "حوض", "رحم", "مبيض", "جلد", "ابط", "مفصل", "ركبه", "يد", "ذراع", "رجل", "ساق", "قدم",
}
IDENTITY_STOPWORDS = {
    "ما", "ماذا", "هل", "هو", "هي", "يوجد", "اريد", "اعرف", "علاج", "اعراض",
    "سبب", "اسباب", "فحص", "تحاليل", "تحليل", "مرض", "حاله", "مستوي", "نسبه",
    "معدل", "ارتفاع", "انخفاض", "هرمون", "شديد", "اكيد", "فعال", "لازم", "مطلوب",
    "صفر", "انا", "اني", "عندي", "لدي", "اعاني", "ممكن", "يمكن", "كيف", "لماذا",
    "الذي", "التي", "هذا", "هذه", "منذ", "يوم", "ايام", "سنه", "سنوات", "عمري",
    "شخص", "متزوج", "متزوجه", "طفل", "طفلي", "ماذا", "افعل", "السلام", "عليكم",
}


def token_set(text: str) -> set[str]:
    return set(TOKEN_RE.findall(normalize_query(text or "").normalized_query))


def lexical_overlap(query: str, text: str) -> float:
    query_tokens = token_set(query)
    text_tokens = token_set(text)
    if not query_tokens or not text_tokens:
        return 0.0
    return len(query_tokens & text_tokens) / len(query_tokens)


def normalized_content_terms(text: str) -> set[str]:
    terms: set[str] = set()
    for token in token_set(text):
        if len(token) <= 1:
            continue
        stripped = token
        for prefix in ("بال", "كال", "لل", "ال"):
            if stripped.startswith(prefix) and len(stripped) > len(prefix) + 1:
                stripped = stripped[len(prefix) :]
                break
        terms.add(stripped)
    return terms


def anatomy_terms(text: str) -> set[str]:
    found: set[str] = set()
    for raw_token in token_set(text):
        variants = {raw_token}
        token = raw_token
        if token.startswith(("و", "ف")) and len(token) > 3:
            token = token[1:]
            variants.add(token)
        for prefix in ("بال", "كال", "لل", "ال"):
            if token.startswith(prefix) and len(token) > len(prefix) + 1:
                variants.add(token[len(prefix) :])
        expanded = set(variants)
        for variant in variants:
            if variant.endswith(("ي", "ك", "ه")) and len(variant) > 3:
                expanded.add(variant[:-1])
            if variant.endswith(("ها", "نا")) and len(variant) > 4:
                expanded.add(variant[:-2])
        for variant in list(expanded):
            if variant.startswith(("ب", "ل")) and len(variant) > 3:
                expanded.add(variant[1:])
        found.update(expanded & ANATOMY_TERMS)
    return found


def is_generic_entity(text: str) -> bool:
    normalized = normalize_query(text or "").normalized_query
    return normalized in GENERIC_MEDICAL_TERMS or normalized.removeprefix("ال") in {
        item.removeprefix("ال") for item in GENERIC_MEDICAL_TERMS
    }


def select_relevance_phrases(
    medical_phrases: list[Any],
    primary_intent: str = "",
) -> list[str]:
    """Choose query anchors without making every background detail mandatory."""
    parsed: list[tuple[str, str]] = []
    for phrase in medical_phrases:
        if isinstance(phrase, dict):
            text = str(phrase.get("normalized_form") or phrase.get("surface_form") or "")
            entity_type = str(phrase.get("entity_type") or "")
        else:
            text = str(
                getattr(phrase, "normalized_form", "")
                or getattr(phrase, "surface_form", "")
            )
            entity_type = str(getattr(phrase, "entity_type", ""))
        if text and not is_generic_entity(text):
            parsed.append((text, entity_type))
    if not parsed:
        return []
    if primary_intent in {"medication_safety", "comparison"}:
        selected = [text for text, _ in parsed]
    else:
        clinical_core = [
            text
            for text, entity_type in parsed
            if entity_type in {"DiseaseCondition", "Symptom"}
        ]
        selected = clinical_core or [text for text, _ in parsed]
    return list(dict.fromkeys(selected))


def medical_identity_tokens(text: str) -> set[str]:
    return {
        token
        for token in normalized_content_terms(text)
        if token not in IDENTITY_STOPWORDS and len(token) > 2 and not any(char.isdigit() for char in token)
    }


def medical_identity_similarity(left: str, right: str) -> float:
    left_tokens = medical_identity_tokens(left)
    right_tokens = medical_identity_tokens(right)
    if not left_tokens or not right_tokens:
        return 0.0
    overlap = left_tokens & right_tokens
    if overlap:
        # Exact overlap with a short entity label remains a strong identity
        # signal, while downstream question matching also checks query overlap.
        return len(overlap) / min(len(left_tokens), len(right_tokens))
    fuzzy_score = max(
        SequenceMatcher(None, left_token, right_token).ratio()
        for left_token in left_tokens
        for right_token in right_tokens
    )
    # Fuzzy identity exists only to tolerate close spelling variants. Moderate
    # string resemblance between unrelated Arabic words is not entity identity.
    # Arabic medical terms with no token overlap need a near-exact spelling
    # resemblance. The previous 0.80 floor confused unrelated symptoms whose
    # short words happened to share several characters.
    return fuzzy_score if fuzzy_score >= 0.90 else 0.0


def safe_float(value: Any) -> float:
    try:
        return max(0.0, min(1.0, float(value or 0.0)))
    except (TypeError, ValueError):
        return 0.0


def embed_query(text: str, config: AppConfig, model: Any | None = None) -> tuple[list[float], Any]:
    if model is None:
        model, _, _ = load_model(config.embeddings.model_name, config.embeddings.dimension)
    vector = model.encode(
        [f"query: {text}"],
        normalize_embeddings=True,
        show_progress_bar=False,
    )[0]
    return [float(value) for value in vector.tolist()], model


def vector_results(
    repository: Neo4jRepository,
    embedding: list[float],
    config: AppConfig,
    plan: RetrievalPlanResult,
) -> list[VectorSearchResult]:
    searches = [
        ("MedicalEntity", config.embeddings.entity_vector_index_name, plan.entity_top_k),
        ("EvidenceMention", config.embeddings.evidence_vector_index_name, plan.evidence_top_k),
        ("QARecord", config.embeddings.qa_vector_index_name, plan.qa_top_k),
    ]
    results: list[VectorSearchResult] = []
    for document_type, index_name, top_k in searches:
        for row in repository.query_vector_index(document_type, index_name, embedding, top_k):
            results.append(
                VectorSearchResult(
                    result_id=str(row.get("result_id") or ""),
                    document_type=document_type,
                    score=safe_float(row.get("score")),
                    entity_id=str(row.get("entity_id") or ""),
                    qa_id=str(row.get("qa_id") or ""),
                    title=str(row.get("title") or ""),
                    text=str(row.get("text") or ""),
                    metadata=dict(row.get("metadata") or {}),
                )
            )
    return results


def seed_scores(
    linking: QueryEntityLinkingResult,
    plan: RetrievalPlanResult,
    vectors: list[VectorSearchResult],
    config: AppConfig,
    analysis: UnifiedQueryAnalysisResult | None = None,
) -> dict[str, float]:
    scores = {entity_id: 1.0 for entity_id in plan.primary_entity_ids}
    for entity in linking.linked_entities:
        if entity.status == "linked" and entity.linked_entity_id in scores:
            scores[entity.linked_entity_id] = max(scores[entity.linked_entity_id], entity.match_score)

    # Never add a semantic graph seed beside a deterministic link. That was the
    # main path by which a correct entity was expanded into a different disease.
    if scores:
        return scores

    expected_types = {phrase.entity_type for phrase in (analysis.medical_phrases if analysis else [])}
    query_text = analysis.reformulated_query if analysis else plan.reformulated_query
    phrase_texts = [phrase.normalized_form for phrase in analysis.medical_phrases] if analysis else [query_text]
    semantic_threshold = max(config.retrieval.semantic_seed_threshold, 0.86)
    for result in vectors:
        if result.document_type != "MedicalEntity" or not result.entity_id:
            continue
        if result.score < semantic_threshold or is_generic_entity(result.title):
            continue
        result_type = str(result.metadata.get("entity_type") or "")
        identity_similarity = max(
            (medical_identity_similarity(phrase_text, result.title) for phrase_text in phrase_texts),
            default=0.0,
        )
        if identity_similarity < 0.86:
            continue
        if expected_types and result_type and result_type not in expected_types and identity_similarity < 0.95:
            continue
        # Scores below 0.9 deliberately identify these as semantic, not hard, seeds.
        scores[result.entity_id] = min(0.70, result.score * 0.75)
        if len(scores) >= 2:
            break
    return scores


def semantic_support_maps(vectors: list[VectorSearchResult]) -> tuple[dict[str, float], dict[str, float]]:
    entity_scores: dict[str, float] = defaultdict(float)
    qa_scores: dict[str, float] = defaultdict(float)
    for result in vectors:
        if result.entity_id:
            entity_scores[result.entity_id] = max(entity_scores[result.entity_id], result.score)
        if result.qa_id:
            qa_scores[result.qa_id] = max(qa_scores[result.qa_id], result.score)
    return dict(entity_scores), dict(qa_scores)


def score_relations(
    rows: list[dict[str, Any]],
    query: str,
    seeds: dict[str, float],
    preferred_relation_types: list[str],
    vectors: list[VectorSearchResult],
    analysis: UnifiedQueryAnalysisResult | None = None,
    low_specificity_entity_ids: list[str] | None = None,
) -> list[RetrievedMedicalRelation]:
    entity_scores, qa_scores = semantic_support_maps(vectors)
    preferred = set(preferred_relation_types)
    expected_types = {phrase.entity_type for phrase in (analysis.medical_phrases if analysis else [])}
    query_anatomy = anatomy_terms(query)
    low_specificity = set(low_specificity_entity_ids or [])
    best_by_fact: dict[str, RetrievedMedicalRelation] = {}
    for row in rows:
        relation_id = str(row.get("relation_id") or "")
        source_relation_id = str(row.get("source_relation_id") or relation_id)
        seed_id = str(row.get("seed_entity_id") or "")
        seed_score = seeds.get(seed_id, 0.0)
        confidence = safe_float(row.get("confidence"))
        relation_type = str(row.get("relation_type") or "")
        intent_score = 1.0 if relation_type in preferred else (0.45 if not preferred else 0.15)
        semantic = max(
            entity_scores.get(str(row.get("source_entity_id") or ""), 0.0),
            entity_scores.get(str(row.get("target_entity_id") or ""), 0.0),
            qa_scores.get(str(row.get("qa_id") or ""), 0.0),
        )
        evidence_parts = [str(row.get("evidence") or "")]
        for item in row.get("evidence_items") or []:
            evidence_parts.extend([str(item.get("evidence") or ""), str(item.get("question") or ""), str(item.get("answer") or "")])
        evidence_relevance = lexical_overlap(query, " ".join(evidence_parts))
        source_name = str(row.get("source_name") or "")
        target_name = str(row.get("target_name") or "")
        seed_type = str(row.get("seed_entity_type") or "")
        endpoint_anatomy = anatomy_terms(f"{source_name} {target_name}")
        anatomy_mismatch = bool(query_anatomy and endpoint_anatomy and query_anatomy.isdisjoint(endpoint_anatomy))
        hard_identity = seed_score >= 0.90
        identity_score = 1.0 if hard_identity else 0.30
        name_overlap = max(lexical_overlap(query, source_name), lexical_overlap(query, target_name))
        medical_identity = max(
            medical_identity_similarity(query, source_name),
            medical_identity_similarity(query, target_name),
        )
        generic_seed = seed_id in low_specificity or is_generic_entity(
            source_name if seed_id == str(row.get("source_entity_id") or "") else target_name
        )
        type_conflict = bool(expected_types and seed_type and seed_type not in expected_types)
        semantic_identity_penalty = 0.25 if not hard_identity and medical_identity < 0.86 else 0.0
        anatomy_penalty = 0.30 if anatomy_mismatch else 0.0
        generic_penalty = 0.22 if generic_seed else 0.0
        type_penalty = 0.25 if type_conflict else 0.0
        total_penalty = anatomy_penalty + generic_penalty + type_penalty + semantic_identity_penalty

        # A semantic-only expansion with a clear conflict is safer to omit than to
        # let relation confidence make it look medically relevant.
        if not hard_identity and (anatomy_mismatch or generic_seed or type_conflict):
            continue
        direction_bonus = 0.03 if str(row.get("direction") or "") == "direct" else 0.0
        hybrid_score = (
            0.12 * confidence
            + 0.30 * identity_score
            + 0.10 * intent_score
            + 0.10 * semantic
            + 0.20 * evidence_relevance
            + 0.12 * max(name_overlap, medical_identity)
            + direction_bonus
            - total_penalty
        )
        relation = RetrievedMedicalRelation(
            relation_id=relation_id,
            source_relation_id=source_relation_id,
            source_entity_id=str(row.get("source_entity_id") or ""),
            source_name=source_name,
            target_entity_id=str(row.get("target_entity_id") or ""),
            target_name=target_name,
            relation_type=relation_type,
            confidence=confidence,
            qa_id=str(row.get("qa_id") or ""),
            evidence=str(row.get("evidence") or ""),
            direction=str(row.get("direction") or ""),
            seed_entity_id=seed_id,
            seed_score=round(seed_score, 6),
            semantic_support=round(semantic, 6),
            evidence_relevance=round(evidence_relevance, 6),
            hybrid_score=round(max(0.0, min(1.0, hybrid_score)), 6),
            metadata={
                "evidence_items": row.get("evidence_items") or [],
                "seed_origin": "hard_link" if hard_identity else "semantic",
                "identity_score": round(identity_score, 6),
                "name_overlap": round(name_overlap, 6),
                "medical_identity": round(medical_identity, 6),
                "query_anatomy": sorted(query_anatomy),
                "endpoint_anatomy": sorted(endpoint_anatomy),
                "anatomy_mismatch": anatomy_mismatch,
                "generic_seed": generic_seed,
                "type_conflict": type_conflict,
                "seed_entity_type": seed_type,
                "source_entity_type": str(row.get("source_entity_type") or ""),
                "target_entity_type": str(row.get("target_entity_type") or ""),
                "total_penalty": round(total_penalty, 6),
            },
        )
        current = best_by_fact.get(source_relation_id)
        if current is None or relation.hybrid_score > current.hybrid_score:
            best_by_fact[source_relation_id] = relation
    return sorted(best_by_fact.values(), key=lambda item: item.hybrid_score, reverse=True)


def collect_evidence(
    relations: list[RetrievedMedicalRelation],
    vectors: list[VectorSearchResult],
    limit: int,
) -> list[RetrievedEvidence]:
    candidates: list[RetrievedEvidence] = []
    for relation in relations:
        if relation.evidence:
            source_rows = relation.metadata.get("evidence_items", [])
            source_row = source_rows[0] if source_rows else {}
            candidates.append(
                RetrievedEvidence(
                    evidence_id=f"relation::{relation.relation_id}",
                    source_id=relation.relation_id,
                    qa_id=relation.qa_id,
                    text=relation.evidence,
                    question=str(source_row.get("question") or ""),
                    answer=str(source_row.get("answer") or ""),
                    category=str(source_row.get("category") or ""),
                    source_quality=str(source_row.get("source_quality") or ""),
                    score=relation.hybrid_score,
                    relation_ids=[relation.relation_id],
                )
            )
        for item in relation.metadata.get("evidence_items", []):
            text = str(item.get("evidence") or item.get("answer") or "").strip()
            if not text:
                continue
            candidates.append(
                RetrievedEvidence(
                    evidence_id=f"mention::{item.get('mention_id') or relation.relation_id}",
                    source_id=str(item.get("mention_id") or relation.relation_id),
                    qa_id=str(item.get("qa_id") or relation.qa_id),
                    text=text,
                    question=str(item.get("question") or ""),
                    answer=str(item.get("answer") or ""),
                    category=str(item.get("category") or ""),
                    source_quality=str(item.get("source_quality") or ""),
                    score=relation.hybrid_score,
                    relation_ids=[relation.relation_id],
                )
            )

    for result in vectors:
        if result.document_type == "EvidenceMention":
            metadata = dict(result.metadata)
            channel = str(metadata.get("retrieval_channel") or "vector")
            metadata.update(
                {
                    "retrieval_channel": channel,
                    "vector_similarity": metadata.get("vector_similarity", result.score),
                }
            )
            candidates.append(
                RetrievedEvidence(
                    evidence_id=f"mention::{result.result_id}",
                    source_id=result.result_id,
                    qa_id=result.qa_id,
                    text=result.text,
                    question=str(result.metadata.get("question") or ""),
                    answer=str(result.metadata.get("answer") or ""),
                    category=str(result.metadata.get("category") or ""),
                    source_quality=str(result.metadata.get("source_quality") or ""),
                    score=result.score,
                    metadata=metadata,
                )
            )
        elif result.document_type == "QARecord":
            metadata = dict(result.metadata)
            channel = str(metadata.get("retrieval_channel") or "vector")
            metadata.update(
                {
                    "retrieval_channel": channel,
                    "vector_similarity": metadata.get("vector_similarity", result.score),
                }
            )
            candidates.append(
                RetrievedEvidence(
                    evidence_id=f"qa::{result.qa_id}",
                    source_id=result.result_id,
                    qa_id=result.qa_id,
                    text=str(result.metadata.get("answer") or result.text),
                    question=str(result.metadata.get("question") or result.title),
                    answer=str(result.metadata.get("answer") or ""),
                    category=str(result.metadata.get("category") or ""),
                    source_quality=str(result.metadata.get("source_quality") or ""),
                    score=result.score,
                    metadata=metadata,
                )
            )

    best: dict[tuple[str, ...], RetrievedEvidence] = {}
    for item in candidates:
        normalized = normalize_query(item.text).normalized_query
        question_norm = normalize_query(item.question).normalized_query
        answer_norm = normalize_query(item.answer).normalized_query
        # The same AHD row can exist under ahd5k, ahd10k, and full-corpus IDs.
        # Deduplicate by normalized content so repeated provenance does not fill
        # the small Step 11 context budget.
        key = (
            ("qa_content", question_norm, answer_norm)
            if question_norm and answer_norm
            else ("source", item.qa_id, normalized)
        )
        current = best.get(key)
        if normalized and (current is None or item.score > current.score):
            best[key] = item
    return sorted(best.values(), key=lambda item: item.score, reverse=True)[:limit]


def retrieve_hybrid(
    analysis: UnifiedQueryAnalysisResult,
    linking: QueryEntityLinkingResult,
    plan: RetrievalPlanResult,
    repository: Neo4jRepository | None = None,
    config: AppConfig | None = None,
    model: Any | None = None,
) -> HybridRetrievalBundle:
    config = config or load_final_config()
    warnings = list(dict.fromkeys([*analysis.warnings, *linking.warnings, *plan.warnings]))
    query_medical_phrases = select_relevance_phrases(
        analysis.medical_phrases,
        analysis.primary_intent,
    )
    if not plan.use_vector_search and not plan.use_graph_search:
        return HybridRetrievalBundle(
            query=analysis.original_query,
            normalized_query=analysis.normalized_query,
            reformulated_query=analysis.reformulated_query,
            plan=plan,
            query_medical_phrases=query_medical_phrases,
            warnings=warnings,
        )

    owns_repository = repository is None
    repository = repository or Neo4jRepository(config=config)
    try:
        vectors: list[VectorSearchResult] = []
        if plan.use_vector_search:
            query_vector, model = embed_query(analysis.reformulated_query, config, model=model)
            vectors = vector_results(repository, query_vector, config, plan)
            if config.qa_corpus.enabled:
                try:
                    vectors.extend(
                        search_qa_corpus(
                            analysis.original_query,
                            analysis.reformulated_query,
                            query_vector,
                            model,
                            config,
                            top_k=max(plan.qa_top_k, config.qa_corpus.semantic_top_k),
                        )
                    )
                except (OSError, RuntimeError, ValueError) as exc:
                    warnings.append(f"External QA retrieval was unavailable: {exc}")

        seeds = seed_scores(linking, plan, vectors, config, analysis=analysis)
        relation_rows: list[dict[str, Any]] = []
        graph_enabled = plan.use_graph_search or (
            plan.use_vector_search and bool(seeds) and plan.query_class != "non_medical"
        )
        graph_hops = plan.hop_depth or (2 if plan.complexity == "high" else 1)
        if graph_enabled and seeds:
            if not plan.use_graph_search:
                warnings.append("Graph expansion was enabled from high-confidence semantic entity seeds.")
            relation_rows = repository.get_medical_relations(
                list(seeds),
                plan.preferred_relation_types,
                graph_hops,
                max(config.retrieval.relation_top_k * 3, config.retrieval.relation_top_k),
            )
        relations = score_relations(
            relation_rows,
            analysis.reformulated_query,
            seeds,
            plan.preferred_relation_types,
            vectors,
            analysis=analysis,
            low_specificity_entity_ids=plan.low_specificity_entity_ids,
        )[: config.retrieval.relation_top_k]
        evidence = collect_evidence(relations, vectors, config.retrieval.context_top_k * 2)
        if not evidence:
            warnings.append("No usable evidence was retrieved from the final graph.")
        if any(item.source_quality == "mention_evidence" for item in evidence):
            warnings.append("Some QA provenance was reconstructed from mention evidence and should be down-weighted.")
        return HybridRetrievalBundle(
            query=analysis.original_query,
            normalized_query=analysis.normalized_query,
            reformulated_query=analysis.reformulated_query,
            plan=plan,
            query_medical_phrases=query_medical_phrases,
            vector_results=vectors,
            relations=relations,
            evidence=evidence,
            warnings=list(dict.fromkeys(warnings)),
        )
    finally:
        if owns_repository:
            repository.close()


def add_semantic_qa_fallback(
    bundle: HybridRetrievalBundle,
    config: AppConfig | None = None,
    model: Any | None = None,
) -> HybridRetrievalBundle:
    """Add local E5-reranked QA candidates after ordinary context selection fails."""
    config = config or load_final_config()
    if not config.qa_corpus.enabled or not config.qa_corpus.semantic_fallback_enabled:
        return bundle
    query_vector, model = embed_query(bundle.reformulated_query, config, model=model)
    try:
        fallback_vectors = search_qa_corpus(
            bundle.query,
            bundle.reformulated_query,
            query_vector,
            model,
            config,
            top_k=config.qa_corpus.semantic_top_k,
            semantic_rerank=True,
            candidate_k=config.qa_corpus.semantic_fallback_candidate_k,
        )
    except (OSError, RuntimeError, ValueError) as exc:
        return replace(
            bundle,
            warnings=list(
                dict.fromkeys(
                    [*bundle.warnings, f"Conditional semantic QA fallback was unavailable: {exc}"]
                )
            ),
        )
    if not fallback_vectors:
        return replace(
            bundle,
            warnings=list(
                dict.fromkeys(
                    [*bundle.warnings, "Conditional semantic QA fallback found no candidates."]
                )
            ),
        )
    vectors = [*bundle.vector_results, *fallback_vectors]
    evidence = collect_evidence(
        bundle.relations,
        vectors,
        config.retrieval.context_top_k * 2,
    )
    return replace(
        bundle,
        vector_results=vectors,
        evidence=evidence,
        warnings=list(
            dict.fromkeys(
                [
                    *bundle.warnings,
                    "Conditional semantic QA fallback ran because ordinary Step 11 context was empty.",
                ]
            )
        ),
    )


def semantic_qa_fallback_eligible(
    bundle: HybridRetrievalBundle,
    *,
    context_has_evidence: bool,
    config: AppConfig | None = None,
) -> bool:
    """Gate expensive local E5 fallback to failed, identifiable medical queries."""
    config = config or load_final_config()
    if context_has_evidence:
        return False
    if not config.qa_corpus.enabled or not config.qa_corpus.semantic_fallback_enabled:
        return False
    if bundle.plan.query_class in {"non_medical", "unclear"}:
        return False
    if not bundle.plan.use_vector_search:
        return False
    return bool(
        bundle.plan.primary_entity_ids
        or bundle.plan.unresolved_phrases
        or medical_identity_tokens(bundle.reformulated_query)
    )
