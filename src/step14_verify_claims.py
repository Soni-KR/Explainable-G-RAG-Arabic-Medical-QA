from __future__ import annotations

import re

from src.models import AnswerClaim, ClaimVerification, EvidenceContextBundle
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
        valid_qa_ids = [item for item in claim.source_qa_ids if item in allowed_qa_ids]
        cited_rows = [evidence_by_id[item] for item in valid_citations]
        scored = []
        for row in cited_rows:
            relation_facts = [
                facts_by_id.get(str(relation_id), "")
                for relation_id in row.get("relation_ids", [])
            ]
            # A source question describes what was asked; it is not factual
            # evidence for an answer. Only answers, evidence text and validated
            # relation facts may support generated claims.
            text_fields = [
                str(row.get("evidence") or ""),
                str(row.get("source_answer") or ""),
                *relation_facts,
            ]
            segments = [
                segment
                for text in text_fields
                for segment in evidence_candidates(text, claim.claim)
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
        cited_entity_identity = max(
            (float(row.get("entity_identity") or 0.0) for row in cited_rows),
            default=0.0,
        )
        cited_vector_similarity = max(
            (float(row.get("vector_similarity") or 0.0) for row in cited_rows),
            default=0.0,
        )
        intent_support_values = [
            float(row.get("intent_support") or 0.0)
            for row in cited_rows
            if "intent_support" in row
        ]
        cited_intent_support = max(intent_support_values) if intent_support_values else None
        question_relevance = max(direct_question_relevance, cited_context_relevance)
        intent_relevance = claim_addresses_intent(
            claim.claim,
            context.primary_intent,
            cited_context_relevance,
            cited_intent_support,
        )
        high_trust_paraphrase = bool(
            cited_context_relevance >= 0.80
            and cited_entity_identity >= 0.75
            and cited_vector_similarity >= 0.84
            and (cited_intent_support is None or cited_intent_support >= 0.50)
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
            and (
                best_score >= support_threshold
                or (best_score >= weak_threshold and high_trust_paraphrase)
            )
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
