from __future__ import annotations

import re

from src.models import AnswerClaim, GeneratedAnswer


SENTENCE_SPLIT_RE = re.compile(r"(?<![A-Za-z])\.|[!؟?؛;\n]+")
ATOMIC_CLAUSE_SPLIT_RE = re.compile(
    r"(?<![A-Za-z])\.|[!؟?؛;\n]+|،\s*(?=(?:ومن|كما|ثم|ويجب|وينصح|ويُنصح))|\s+(?=(?:لتحديد|للتأكد)\s+ما\s+إذا)"
)
EVIDENCE_ID_RE = re.compile(r"\bE\d+\b")
CITATION_BLOCK_RE = re.compile(r"\[\s*E\d+(?:\s*[,،]\s*E\d+)*\s*\]")
NON_FACTUAL_LIMITATION_MARKERS = (
    "لا توجد أدلة كافية",
    "الأدلة المسترجعة غير كافية",
    "يُنصح باستشارة طبيب",
    "ينصح باستشارة طبيب",
)
META_EVIDENCE_MARKERS = (
    "في الأدلة", "في البيانات", "في المعلومات", "في المصادر", "في المواد",
    "الأدلة المقدمة", "الأدلة المرفقة", "الأدلة المتاحة", "المعلومات المتوفرة",
    "المعلومات المقدمة", "المعلومات المرفقة", "المصادر المرفقة", "بناء على الأدلة",
)
INSUFFICIENCY_MARKERS = (
    "لا توجد أدلة", "لا توجد معلومات", "لا توجد بيانات", "لا يوجد دليل",
    "لا يمكن تحديد", "لا يمكننا تأكيد", "لا يمكن تأكيد", "غير كافية", "غير كافي",
)
EVIDENCE_ADAPTIVE_MODES = {
    "strong_direct_evidence",
    "partial_or_mixed_evidence",
    "structured_claims_v3_1",
}


def is_non_factual_limitation(text: str) -> bool:
    if any(marker in text for marker in NON_FACTUAL_LIMITATION_MARKERS):
        return True
    return bool(
        any(marker in text for marker in INSUFFICIENCY_MARKERS)
        and any(marker in text for marker in META_EVIDENCE_MARKERS)
    )


def split_atomic_claim(claim: AnswerClaim) -> list[AnswerClaim]:
    """Split strong compound-claim boundaries while preserving provenance."""
    pieces = [" ".join(piece.split()).strip(" ،") for piece in ATOMIC_CLAUSE_SPLIT_RE.split(claim.claim)]
    useful = [piece for piece in pieces if len(piece.split()) >= 3]
    if len(useful) <= 1:
        return [claim]
    return [
        AnswerClaim(
            claim=piece,
            citations=list(claim.citations),
            source_qa_ids=list(claim.source_qa_ids),
        )
        for piece in useful
    ]


def extract_claims(answer: GeneratedAnswer) -> list[AnswerClaim]:
    """Return structured claims, or recover atomic claims from a generated answer."""
    if answer.claims:
        claims: list[AnswerClaim] = []
        seen: set[str] = set()
        for claim in answer.claims:
            # Structured Step 12 profiles validate self-contained claims with
            # one citation each. Splitting again can detach a test, treatment,
            # or recommendation from its disease or symptom.
            atomic_claims = (
                [claim]
                if answer.generation_mode in EVIDENCE_ADAPTIVE_MODES
                else split_atomic_claim(claim)
            )
            for atomic_claim in atomic_claims:
                if (
                    atomic_claim.claim not in seen
                    and not is_non_factual_limitation(atomic_claim.claim)
                ):
                    claims.append(atomic_claim)
                    seen.add(atomic_claim.claim)
        return claims
    if answer.generation_status != "generated":
        return []

    claims: list[AnswerClaim] = []
    seen: set[str] = set()
    for sentence in SENTENCE_SPLIT_RE.split(answer.answer):
        raw_text = " ".join(sentence.removeprefix("-").split())
        if len(raw_text.split()) < 3:
            continue
        if is_non_factual_limitation(raw_text):
            continue
        citations = list(dict.fromkeys(EVIDENCE_ID_RE.findall(raw_text)))
        claim_text = " ".join(CITATION_BLOCK_RE.sub("", raw_text).split())
        if claim_text and claim_text not in seen:
            claims.append(AnswerClaim(claim=claim_text, citations=citations))
            seen.add(claim_text)
    return claims
