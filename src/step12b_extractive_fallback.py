from __future__ import annotations

"""Conservative extractive fallback for frozen Step 11 contexts.

This component is intentionally isolated from normal generation. It can only
copy one sentence from one authoritative QA answer, cite that answer once, and
submit the unchanged text to the deterministic v3 claim verifier.
"""

import re
from dataclasses import asdict, dataclass, field
from typing import Any

from src.models import AnswerClaim, ClaimVerification, EvidenceContextBundle
from src.query_relevance import (
    constraint_terms,
    minimum_candidate_concept_coverage,
    query_concept_coverage,
    query_concepts,
)
from src.step14_verify_claims import question_relevance_score, verify_claims


FALLBACK_VERSION = "evidence_preserving_extractive_v1"

# Frozen before the 200-query ablation. These absolute gates favor precision
# over coverage and must not be tuned after inspecting the experiment results.
MIN_ANSWER_RELEVANCE = 0.60
MIN_ORIGINAL_QUESTION_RELEVANCE = 0.50
MIN_INTENT_SUPPORT = 0.75
MIN_QUERY_CONCEPT_COVERAGE = 0.50
MIN_QUERY_CONSTRAINT_COVERAGE = 0.50
MIN_SOURCE_RELIABILITY = 0.90
MIN_SENTENCE_QUERY_RELEVANCE = 0.25
MIN_SENTENCE_CHARS = 12
MAX_SENTENCE_CHARS = 700

SENTENCE_BOUNDARY_RE = re.compile(
    r"(?<=[.!?؟؛])(?:\s+|(?=[A-Za-z\u0600-\u06ff]))|[\r\n\u2028\u2029]+"
)
NOISE_RE = re.compile(
    r"(?:https?://|www\.|(?:^|\s)e-?mail(?:\s|:)|(?:^|\s)tel(?:\.|\s|:))",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ExtractiveCandidate:
    """One exact answer sentence and its deterministic verification trace."""

    claim: AnswerClaim
    sentence_index: int
    evidence_id: str
    qa_id: str
    source_answer: str
    exact_source_match: bool
    sentence_query_relevance: float
    sentence_query_concept_coverage: float
    selection_score: float
    verification: ClaimVerification
    evidence_metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ExtractiveFallbackResult:
    """Outcome for one eligible query."""

    status: str
    reason: str
    selected: ExtractiveCandidate | None = None
    candidate_count: int = 0
    supported_candidate_count: int = 0
    rejected_evidence: list[dict[str, str]] = field(default_factory=list)


def _score(value: Any) -> float:
    try:
        return max(0.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        return 0.0


def _flag(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def compact_whitespace(value: Any) -> str:
    """Normalize spacing only; medical words and punctuation stay unchanged."""

    return " ".join(str(value or "").split()).strip()


def split_answer_sentences(answer: str) -> list[str]:
    """Split answer text at sentence boundaries without rewriting its content."""

    clean = str(answer or "").strip()
    if not clean:
        return []
    return [
        compact_whitespace(part)
        for part in SENTENCE_BOUNDARY_RE.split(clean)
        if compact_whitespace(part)
    ]


def fallback_eligible(
    *,
    output_claims: list[dict[str, Any]] | list[AnswerClaim],
    context: EvidenceContextBundle,
) -> bool:
    """Only non-empty-context rows with no surviving claim may be changed."""

    return not output_claims and bool(context.evidence_items)


def _evidence_gate_reason(
    item: dict[str, Any],
    context: EvidenceContextBundle,
) -> str:
    evidence_id = str(item.get("evidence_id") or "")
    qa_id = str(item.get("qa_id") or "")
    source_answer = str(item.get("source_answer") or "").strip()
    if not evidence_id or evidence_id not in set(context.allowed_evidence_ids):
        return "evidence_not_allowed"
    if not qa_id or qa_id not in set(context.allowed_qa_ids):
        return "qa_not_allowed"
    if not source_answer:
        return "missing_source_answer"
    if _flag(item.get("anatomy_mismatch")):
        return "anatomy_mismatch"
    if _flag(item.get("unrelated_condition_mismatch")):
        return "unrelated_condition_mismatch"
    if _score(item.get("source_reliability")) < MIN_SOURCE_RELIABILITY:
        return "source_reliability_below_gate"
    if _score(item.get("answer_relevance")) < MIN_ANSWER_RELEVANCE:
        return "answer_relevance_below_gate"
    if _score(item.get("intent_support")) < MIN_INTENT_SUPPORT:
        return "intent_support_below_gate"
    if (
        _score(item.get("query_concept_coverage"))
        < MIN_QUERY_CONCEPT_COVERAGE
    ):
        return "query_concept_coverage_below_gate"

    direct_anchor = _flag(item.get("direct_question_anchor"))
    exact_question = _flag(item.get("exact_question_match"))
    if (
        _score(item.get("original_question_relevance"))
        < MIN_ORIGINAL_QUESTION_RELEVANCE
        and not direct_anchor
        and not exact_question
    ):
        return "source_question_relevance_below_gate"

    query_text = context.reformulated_query or context.query
    if (
        constraint_terms(query_text)
        and _score(item.get("query_constraint_coverage"))
        < MIN_QUERY_CONSTRAINT_COVERAGE
    ):
        return "query_constraint_coverage_below_gate"
    return ""


def _candidate_score(
    item: dict[str, Any],
    verification: ClaimVerification,
    sentence_relevance: float,
    sentence_concept_coverage: float,
) -> float:
    """Rank already-supported exact sentences with interpretable metadata."""

    weighted = (
        0.25 * sentence_relevance
        + 0.20 * sentence_concept_coverage
        + 0.15 * _score(item.get("answer_relevance"))
        + 0.10 * _score(item.get("original_question_relevance"))
        + 0.10 * _score(item.get("entity_identity"))
        + 0.05 * _score(item.get("intent_support"))
        + 0.05 * _score(item.get("source_reliability"))
        + 0.05 * _score(item.get("retrieval_score"))
        + 0.05 * _score(verification.support_score)
    )
    return round(weighted, 6)


def select_extractive_fallback(
    context: EvidenceContextBundle,
) -> ExtractiveFallbackResult:
    """Select at most one exact answer sentence accepted by the v3 verifier."""

    query_text = context.reformulated_query or context.query
    concept_count = len(
        query_concepts(query_text, context.query_medical_phrases)
    )
    sentence_concept_floor = max(
        MIN_QUERY_CONCEPT_COVERAGE,
        minimum_candidate_concept_coverage(concept_count),
    )
    candidates: list[ExtractiveCandidate] = []
    rejected_evidence: list[dict[str, str]] = []
    candidate_count = 0

    for item in context.evidence_items:
        evidence_id = str(item.get("evidence_id") or "")
        gate_reason = _evidence_gate_reason(item, context)
        if gate_reason:
            rejected_evidence.append(
                {"evidence_id": evidence_id, "reason": gate_reason}
            )
            continue

        source_answer = str(item.get("source_answer") or "")
        compact_answer = compact_whitespace(source_answer)
        qa_id = str(item.get("qa_id") or "")
        for sentence_index, sentence in enumerate(
            split_answer_sentences(source_answer),
            start=1,
        ):
            if not (MIN_SENTENCE_CHARS <= len(sentence) <= MAX_SENTENCE_CHARS):
                continue
            if NOISE_RE.search(sentence):
                continue
            exact_source_match = bool(
                sentence and sentence in compact_answer
            )
            if not exact_source_match:
                continue

            sentence_relevance = question_relevance_score(
                sentence,
                query_text,
            )
            sentence_concept_coverage = query_concept_coverage(
                query_text,
                sentence,
                context.query_medical_phrases,
            )
            if sentence_relevance < MIN_SENTENCE_QUERY_RELEVANCE:
                continue
            if sentence_concept_coverage < sentence_concept_floor:
                continue

            candidate_count += 1
            claim = AnswerClaim(
                claim=sentence,
                citations=[evidence_id],
                source_qa_ids=[qa_id],
            )
            verification = verify_claims([claim], context)[0]
            if (
                verification.status != "supported"
                or verification.valid_citations != [evidence_id]
                or verification.valid_qa_ids != [qa_id]
            ):
                continue

            candidates.append(
                ExtractiveCandidate(
                    claim=claim,
                    sentence_index=sentence_index,
                    evidence_id=evidence_id,
                    qa_id=qa_id,
                    source_answer=source_answer,
                    exact_source_match=True,
                    sentence_query_relevance=round(
                        sentence_relevance,
                        6,
                    ),
                    sentence_query_concept_coverage=round(
                        sentence_concept_coverage,
                        6,
                    ),
                    selection_score=_candidate_score(
                        item,
                        verification,
                        sentence_relevance,
                        sentence_concept_coverage,
                    ),
                    verification=verification,
                    evidence_metadata={
                        key: item.get(key)
                        for key in (
                            "answer_relevance",
                            "original_question_relevance",
                            "entity_identity",
                            "intent_support",
                            "query_concept_coverage",
                            "query_constraint_coverage",
                            "source_reliability",
                            "retrieval_score",
                            "source_quality",
                            "evidence_origin",
                        )
                    },
                )
            )

    if not candidates:
        return ExtractiveFallbackResult(
            status="no_supported_sentence",
            reason=(
                "No exact authoritative answer sentence passed both the frozen "
                "selection gates and the unchanged deterministic v3 verifier."
            ),
            candidate_count=candidate_count,
            supported_candidate_count=0,
            rejected_evidence=rejected_evidence,
        )

    candidates.sort(
        key=lambda row: (
            row.selection_score,
            row.verification.question_relevance,
            row.verification.query_concept_coverage,
            row.verification.support_score,
            -row.sentence_index,
            row.evidence_id,
        ),
        reverse=True,
    )
    return ExtractiveFallbackResult(
        status="selected",
        reason=(
            "Selected the highest-ranked exact answer sentence that passed the "
            "unchanged deterministic v3 verifier."
        ),
        selected=candidates[0],
        candidate_count=candidate_count,
        supported_candidate_count=len(candidates),
        rejected_evidence=rejected_evidence,
    )


def fallback_audit_payload(
    result: ExtractiveFallbackResult,
) -> dict[str, Any]:
    """Return a JSON-serializable audit without changing the result object."""

    return asdict(result)
