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
            for atomic_claim in split_atomic_claim(claim):
                if atomic_claim.claim not in seen:
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
        if any(marker in raw_text for marker in NON_FACTUAL_LIMITATION_MARKERS):
            continue
        citations = list(dict.fromkeys(EVIDENCE_ID_RE.findall(raw_text)))
        claim_text = " ".join(CITATION_BLOCK_RE.sub("", raw_text).split())
        if claim_text and claim_text not in seen:
            claims.append(AnswerClaim(claim=claim_text, citations=citations))
            seen.add(claim_text)
    return claims
