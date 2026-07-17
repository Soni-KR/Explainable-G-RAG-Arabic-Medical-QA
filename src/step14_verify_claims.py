from __future__ import annotations

import re

from src.models import AnswerClaim, ClaimVerification, EvidenceContextBundle
from src.step08a_normalize_query import normalize_query
from src.step09_hybrid_retrieval import anatomy_terms


TOKEN_RE = re.compile(r"[\w\u0600-\u06ff]+", re.UNICODE)
NUMBER_RE = re.compile(r"\d+(?:[.,]\d+)?")
TEXT_SEGMENT_RE = re.compile(r"[.!؟?؛;\n]+")
NEGATIONS = {"لا", "ليس", "ليست", "لم", "لن", "بدون", "غير", "ما"}
STOPWORDS = {"من", "في", "على", "الى", "إلى", "عن", "مع", "او", "أو", "هذا", "هذه", "هو", "هي", "قد"}
CLAIM_INTENT_CUES = {
    "treatment_request": {"علاج", "دواء", "ادويه", "يستخدم", "تناول", "جراحه"},
    "symptom_request": {"عرض", "اعراض", "علامه", "يشعر", "الم", "حمي"},
    "diagnosis_request": {"تشخيص", "يشخص", "يعاني", "اصابه", "مرض"},
    "test_request": {"فحص", "اختبار", "تحليل", "تحاليل", "اشعه", "تصوير", "مختبر", "سونار"},
    "cause_request": {"سبب", "اسباب", "يسبب", "تسبب", "ناتج"},
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
    return not claim_markers or bool(content_tokens(evidence) & RECOMMENDATION_MARKERS)


def claim_addresses_intent(
    claim: str,
    primary_intent: str,
    cited_context_relevance: float = 0.0,
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
    if primary_intent in {"treatment_request", "diagnosis_request"}:
        return bool(claim_tokens & CLAIM_INTENT_CUES["test_request"]) and cited_context_relevance >= 0.75
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
        valid_qa_ids = [item for item in claim.source_qa_ids if item in allowed_qa_ids]
        cited_rows = [evidence_by_id[item] for item in valid_citations]
        scored = []
        for row in cited_rows:
            relation_facts = [
                facts_by_id.get(str(relation_id), "")
                for relation_id in row.get("relation_ids", [])
            ]
            text_fields = [
                str(row.get("evidence") or ""),
                str(row.get("source_question") or ""),
                str(row.get("source_answer") or ""),
                *relation_facts,
            ]
            segments = [
                segment.strip()
                for text in text_fields
                for segment in TEXT_SEGMENT_RE.split(text)
                if segment.strip()
            ]
            for segment in segments:
                score = support_score(claim.claim, segment)
                constraints_ok = (
                    negation_matches(claim.claim, segment)
                    and numbers_supported(claim.claim, segment)
                    and anatomy_supported(claim.claim, segment)
                    and recommendation_matches(claim.claim, segment)
                )
                scored.append((score, constraints_ok, row))
        scored.sort(key=lambda item: (item[1], item[0]), reverse=True)
        best_score = scored[0][0] if scored else 0.0
        best_constraints = scored[0][1] if scored else False
        direct_question_relevance = question_relevance_score(
            claim.claim,
            context.reformulated_query or context.query,
        )
        # Step 10/11 already evaluates whether each cited passage answers the
        # query using entity identity, anatomy and intent.  Reuse that vetted
        # signal so a medically relevant paraphrase is not rejected merely
        # because it shares few literal words with a long patient question.
        cited_context_relevance = max(
            (float(row.get("answer_relevance") or 0.0) for row in cited_rows),
            default=0.0,
        )
        question_relevance = max(direct_question_relevance, cited_context_relevance)
        intent_relevance = claim_addresses_intent(
            claim.claim,
            context.primary_intent,
            cited_context_relevance,
        )
        relation_ids = list(
            dict.fromkeys(
                relation_id
                for _, _, row in scored[:3]
                for relation_id in row.get("relation_ids", [])
            )
        )

        if (
            valid_citations
            and best_constraints
            and best_score >= support_threshold
            and question_relevance >= 0.25
            and intent_relevance
        ):
            status = "supported"
            reason = "A valid citation supports the claim and the claim directly addresses the query."
        elif (
            valid_citations
            and best_constraints
            and best_score >= weak_threshold
            and question_relevance >= 0.15
            and intent_relevance
        ):
            status = "weakly_supported"
            reason = "The claim has partial evidence support or only moderate relevance to the query."
        else:
            status = "unsupported"
            reason = "The claim lacks sufficient cited support or does not directly answer the query."
        verifications.append(
            ClaimVerification(
                claim=claim,
                status=status,
                support_score=round(best_score, 6),
                question_relevance=round(question_relevance, 6),
                valid_citations=valid_citations,
                valid_qa_ids=valid_qa_ids,
                supporting_relation_ids=relation_ids,
                reason=reason,
            )
        )
    return verifications
