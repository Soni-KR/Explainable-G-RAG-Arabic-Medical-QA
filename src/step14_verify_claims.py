from __future__ import annotations

import re

from src.evidence_policy import authoritative_evidence_texts
from src.models import AnswerClaim, ClaimVerification, EvidenceContextBundle
from src.query_relevance import (
    minimum_candidate_concept_coverage,
    query_concept_coverage,
    query_concepts,
)
from src.step08a_normalize_query import normalize_query
from src.step09_hybrid_retrieval import anatomy_terms


TOKEN_RE = re.compile(r"[\w\u0600-\u06ff]+", re.UNICODE)
NUMBER_RE = re.compile(r"\d+(?:[.,]\d+)?")
TEXT_SEGMENT_RE = re.compile(
    r"(?<![A-Za-z])\.|[!؟?؛;\n،:]+|(?:-{2,}|(?<=\s)[-–—](?=\s))"
)
# ``ما`` is often interrogative in medical questions (for example, ``ما علاج``),
# so treating it as a universal negation marker causes false rejections.
NEGATIONS = {"لا", "ليس", "ليست", "لم", "لن", "بدون", "غير"}
STOPWORDS = {"من", "في", "على", "الى", "إلى", "عن", "مع", "او", "أو", "هذا", "هذه", "هو", "هي", "قد"}
CLAIM_INTENT_CUES = {
    "treatment_request": {
        "علاج", "علاجات", "يعالج", "تعالج", "دواء", "ادويه", "دوائيه",
        "يستخدم", "استخدام", "استعمال", "تناول", "تقليل", "زياده", "ايقاف",
        "وقف", "اقلاع", "تجنب", "مراجعه", "مضمضه", "غسول", "جراحه",
    },
    "symptom_request": {"عرض", "اعراض", "علامه", "يشعر", "الم", "حمي"},
    "diagnosis_request": {
        "تشخيص", "يشخص", "يعاني", "اصابه", "مرض", "نتيجه", "ناتج", "ناتجا", "يدل", "تشير",
    },
    "test_request": {
        "فحص", "اختبار", "تحليل", "تحاليل", "اشعه", "تصوير", "مختبر", "سونار",
        "قياس", "منظار", "رنين",
    },
    "cause_request": {
        "سبب", "اسباب", "يسبب", "تسبب", "ناتج", "ناتجا", "نتيجه", "بسبب", "يؤدي",
    },
    "prevention_request": {"وقايه", "تجنب", "منع"},
}
VERIFICATION_TOKEN_EQUIVALENTS = {
    "اختبار": "فحص",
    "تحليل": "فحص",
    "تحاليل": "فحص",
    "اجراء": "عمل",
    "تصوير": "اشعه",
    "محوسب": "مقطعي",
    "كمبيوتر": "مقطعي",
    "بالكمبيوتر": "مقطعي",
    "المقطعي": "مقطعي",
    "للمخ": "مخ",
    "بالرنين": "رنين",
}
VERIFICATION_STOPWORDS = {
    "يجب", "افضل", "جيد", "ومن", "ما", "اذا", "كان", "لتحديد", "لاكتشاف",
    "للتاكد", "للمريض", "للمريضه", "لل", "ينصح", "ننصحك", "انصحك", "مبدييا",
}
RECOMMENDATION_MARKERS = {
    "يجب", "ينصح", "ينصحك", "ننصحك", "انصحك", "افضل", "جيد", "يتوجب", "لابد",
}
EVIDENCE_ACTION_MARKERS = RECOMMENDATION_MARKERS | CLAIM_INTENT_CUES["treatment_request"] | {
    "عمل", "اجراء", "فحص", "اختبار", "تحليل", "قياس", "زياره", "مراجعه", "يمكن",
}


def content_tokens(text: str) -> set[str]:
    normalized = normalize_query(text or "").normalized_query
    tokens: set[str] = set()
    for token in TOKEN_RE.findall(normalized):
        if len(token) <= 1 or token in STOPWORDS:
            continue
        reduced = token.removeprefix("ال")
        if reduced.startswith("و") and len(reduced) > 3:
            reduced = reduced[1:]
        tokens.add(reduced or token)
    return tokens


def verification_tokens(text: str) -> set[str]:
    return {
        VERIFICATION_TOKEN_EQUIVALENTS.get(token, token)
        for token in content_tokens(text)
        if token not in VERIFICATION_STOPWORDS
    }


def support_score(claim: str, evidence: str) -> float:
    claim_tokens = verification_tokens(claim)
    evidence_tokens = verification_tokens(evidence)
    if not claim_tokens or not evidence_tokens:
        return 0.0
    return len(claim_tokens & evidence_tokens) / len(claim_tokens)


def question_relevance_score(claim: str, query: str) -> float:
    claim_tokens = content_tokens(claim)
    query_tokens = content_tokens(query)
    if not claim_tokens or not query_tokens:
        return 0.0
    return len(claim_tokens & query_tokens) / min(len(claim_tokens), len(query_tokens))


def negation_matches(claim: str, evidence: str) -> bool:
    claim_tokens = set(TOKEN_RE.findall(normalize_query(claim or "").normalized_query))
    evidence_tokens = set(TOKEN_RE.findall(normalize_query(evidence or "").normalized_query))
    return bool(claim_tokens & NEGATIONS) == bool(evidence_tokens & NEGATIONS)


def numbers_supported(claim: str, evidence: str) -> bool:
    claim_numbers = set(NUMBER_RE.findall(claim))
    return not claim_numbers or claim_numbers.issubset(set(NUMBER_RE.findall(evidence)))


def anatomy_supported(claim: str, evidence: str) -> bool:
    claim_anatomy = anatomy_terms(claim)
    return not claim_anatomy or claim_anatomy.issubset(anatomy_terms(evidence))


def recommendation_matches(claim: str, evidence: str) -> bool:
    claim_markers = content_tokens(claim) & RECOMMENDATION_MARKERS
    return not claim_markers or bool(content_tokens(evidence) & EVIDENCE_ACTION_MARKERS)


def evidence_candidates(text: str, claim: str) -> list[str]:
    """Build local and aggregate candidates from one authoritative evidence field."""
    clean_text = " ".join((text or "").split()).strip()
    if not clean_text:
        return []
    segments = [
        " ".join(segment.split()).strip()
        for segment in TEXT_SEGMENT_RE.split(clean_text)
        if segment.strip()
    ]
    # Aggregate only clauses with the same polarity as the claim. This lets a
    # supported list span comma-separated clauses without letting an unrelated
    # negative clause invalidate it or support its opposite.
    aligned_segments = [segment for segment in segments if negation_matches(claim, segment)]
    candidates = [*segments]
    if len(aligned_segments) > 1:
        candidates.append(" ".join(aligned_segments))
    if negation_matches(claim, clean_text):
        candidates.append(clean_text)
    return list(dict.fromkeys(candidates))


def claim_addresses_intent(
    claim: str,
    primary_intent: str,
    cited_context_relevance: float = 0.0,
    cited_intent_support: float | None = None,
) -> bool:
    """Reject factual restatements that do not answer the requested question type."""
    cues = CLAIM_INTENT_CUES.get(primary_intent)
    if not cues:
        return True
    claim_tokens = content_tokens(claim)
    if claim_tokens & cues:
        return True
    # An exact/high-relevance answer to a treatment or diagnosis question may
    # legitimately recommend a test before treatment can be selected.  This
    # exception is unavailable to weakly related passages.
    context_intent_is_strong = (
        cited_intent_support is None or cited_intent_support >= 0.75
    )
    if primary_intent in {"treatment_request", "diagnosis_request"}:
        if claim_tokens & CLAIM_INTENT_CUES["test_request"]:
            return cited_context_relevance >= 0.75 and context_intent_is_strong
    if primary_intent == "treatment_request":
        return (
            bool(claim_tokens & EVIDENCE_ACTION_MARKERS)
            and cited_context_relevance >= 0.75
            and context_intent_is_strong
        )
    return False


def verify_claims(
    claims: list[AnswerClaim],
    context: EvidenceContextBundle,
    support_threshold: float = 0.40,
    weak_threshold: float = 0.25,
) -> list[ClaimVerification]:
    evidence_by_id = {str(item["evidence_id"]): item for item in context.evidence_items}
    facts_by_id = {str(item["relation_id"]): str(item.get("fact") or "") for item in context.graph_facts}
    allowed_qa_ids = set(context.allowed_qa_ids)
    verifications: list[ClaimVerification] = []
    for claim in claims:
        valid_citations = [item for item in claim.citations if item in evidence_by_id]
        pair_results: list[dict[str, object]] = []
        for citation_id in valid_citations:
            row = evidence_by_id[citation_id]
            relation_facts = [
                facts_by_id.get(str(relation_id), "")
                for relation_id in row.get("relation_ids", [])
            ]
            # Question-origin mention text is useful for retrieval but cannot
            # establish an answer fact. This also repairs frozen contexts that
            # predate explicit evidence-origin metadata.
            text_fields, _, question_text_excluded = authoritative_evidence_texts(
                row,
                relation_facts,
            )
            segments = [
                segment
                for text in text_fields
                for segment in evidence_candidates(text, claim.claim)
            ]
            segment_results: list[tuple[float, bool, list[str]]] = []
            for segment in segments:
                score = support_score(claim.claim, segment)
                failed_checks: list[str] = []
                if not negation_matches(claim.claim, segment):
                    failed_checks.append("negation_mismatch")
                if not numbers_supported(claim.claim, segment):
                    failed_checks.append("number_mismatch")
                if not anatomy_supported(claim.claim, segment):
                    failed_checks.append("anatomy_mismatch")
                if not recommendation_matches(claim.claim, segment):
                    failed_checks.append("recommendation_not_supported")
                segment_results.append((score, not failed_checks, failed_checks))
            segment_results.sort(key=lambda item: (item[1], item[0]), reverse=True)
            best_score, constraints_ok, failed_checks = (
                segment_results[0]
                if segment_results
                else (
                    0.0,
                    False,
                    [
                        "question_only_evidence"
                        if question_text_excluded
                        else "no_evidence_segment"
                    ],
                )
            )
            direct_question_relevance = question_relevance_score(
                claim.claim,
                context.reformulated_query or context.query,
            )
            context_relevance = float(row.get("answer_relevance") or 0.0)
            entity_identity = float(row.get("entity_identity") or 0.0)
            vector_similarity = float(row.get("vector_similarity") or 0.0)
            query_text = context.reformulated_query or context.query
            concept_count = len(
                query_concepts(query_text, context.query_medical_phrases)
            )
            claim_concept_coverage = query_concept_coverage(
                query_text,
                claim.claim,
                context.query_medical_phrases,
            )
            cited_concept_coverage = float(
                row.get("query_concept_coverage")
                if row.get("query_concept_coverage") is not None
                else query_concept_coverage(
                    query_text,
                    " ".join(
                        (
                            str(row.get("source_question") or ""),
                            str(row.get("evidence") or ""),
                            str(row.get("source_answer") or ""),
                        )
                    ),
                    context.query_medical_phrases,
                )
            )
            concept_floor = minimum_candidate_concept_coverage(concept_count)
            query_scope_relevant = bool(
                concept_floor == 0.0
                or claim_concept_coverage >= concept_floor
                or (
                    cited_concept_coverage >= concept_floor
                    and context_relevance >= 0.75
                )
            )
            cited_intent_support = (
                float(row.get("intent_support") or 0.0)
                if "intent_support" in row
                else None
            )
            question_relevance = max(direct_question_relevance, context_relevance)
            intent_relevance = claim_addresses_intent(
                claim.claim,
                context.primary_intent,
                context_relevance,
                cited_intent_support,
            )
            high_trust_paraphrase = bool(
                context_relevance >= 0.80
                and entity_identity >= 0.75
                and vector_similarity >= 0.84
                and (cited_intent_support is None or cited_intent_support >= 0.50)
            )
            if question_relevance < 0.25:
                failed_checks.append("query_relevance_below_threshold")
            if not query_scope_relevant:
                failed_checks.append("claim_query_concept_mismatch")
            if not intent_relevance:
                failed_checks.append("intent_mismatch")
            supported = bool(
                constraints_ok
                and (
                    best_score >= support_threshold
                    or (best_score >= weak_threshold and high_trust_paraphrase)
                )
                and question_relevance >= 0.25
                and query_scope_relevant
                and intent_relevance
            )
            weakly_supported = bool(
                not supported
                and constraints_ok
                and best_score >= weak_threshold
                and question_relevance >= 0.15
                and query_scope_relevant
                and intent_relevance
            )
            if best_score < weak_threshold:
                failed_checks.append("support_below_weak_threshold")
            pair_results.append(
                {
                    "citation_id": citation_id,
                    "row": row,
                    "status": (
                        "supported"
                        if supported
                        else "weakly_supported"
                        if weakly_supported
                        else "unsupported"
                    ),
                    "support_score": best_score,
                    "question_relevance": question_relevance,
                    "query_concept_coverage": claim_concept_coverage,
                    "cited_query_concept_coverage": cited_concept_coverage,
                    "failed_checks": list(dict.fromkeys(failed_checks)),
                }
            )

        status_order = {"unsupported": 0, "weakly_supported": 1, "supported": 2}
        pair_results.sort(
            key=lambda item: (
                status_order[str(item["status"])],
                float(item["support_score"]),
                float(item["question_relevance"]),
                float(item["query_concept_coverage"]),
            ),
            reverse=True,
        )
        best_pair = pair_results[0] if pair_results else None
        status = str(best_pair["status"]) if best_pair else "unsupported"
        accepted_pairs = [item for item in pair_results if item["status"] == status]
        accepted_pairs = accepted_pairs if status != "unsupported" else []
        accepted_citations = [str(item["citation_id"]) for item in accepted_pairs]
        accepted_rows = [item["row"] for item in accepted_pairs]
        accepted_qa_ids = {
            str(row.get("qa_id") or "")
            for row in accepted_rows
            if str(row.get("qa_id") or "") in allowed_qa_ids
        }
        valid_qa_ids = [
            item
            for item in claim.source_qa_ids
            if item in allowed_qa_ids and item in accepted_qa_ids
        ]
        relation_ids = list(
            dict.fromkeys(
                str(relation_id)
                for row in accepted_rows
                for relation_id in row.get("relation_ids", [])
            )
        )
        best_score = float(best_pair["support_score"]) if best_pair else 0.0
        question_relevance = float(best_pair["question_relevance"]) if best_pair else 0.0
        claim_concept_coverage = (
            float(best_pair["query_concept_coverage"])
            if best_pair
            else 0.0
        )
        best_evidence_id = str(best_pair["citation_id"]) if best_pair else ""
        failed_checks = list(best_pair["failed_checks"]) if best_pair else ["no_valid_citation"]
        if status == "supported":
            reason = f"Evidence {best_evidence_id} independently supports the claim and query intent."
        elif status == "weakly_supported":
            reason = f"Evidence {best_evidence_id} provides partial support for the claim."
        else:
            reason = (
                f"No single cited evidence item passed all checks; best candidate: "
                f"{best_evidence_id or 'none'}."
            )
        verifications.append(
            ClaimVerification(
                claim=claim,
                status=status,
                support_score=round(best_score, 6),
                question_relevance=round(question_relevance, 6),
                query_concept_coverage=round(claim_concept_coverage, 6),
                valid_citations=accepted_citations,
                valid_qa_ids=valid_qa_ids,
                supporting_relation_ids=relation_ids,
                best_evidence_id=best_evidence_id,
                failed_checks=failed_checks,
                reason=reason,
            )
        )
    return verifications
