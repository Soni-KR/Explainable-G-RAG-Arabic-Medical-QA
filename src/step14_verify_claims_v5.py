from __future__ import annotations

"""Hard-safety wrapper for selective semantic claim adjudication.

The frozen deterministic verifier remains unchanged. This module adds an
explicit development profile that:

1. runs the existing deterministic verifier;
2. blocks claims that violate non-overridable evidence-fidelity gates;
3. exposes only pure intent/concept disputes to semantic adjudication; and
4. fails closed when semantic adjudication is disabled or unavailable.

The profile is intentionally opt-in. Importing this module does not change the
production verifier or any saved evaluation run.
"""

from dataclasses import asdict, replace
from typing import Any, Protocol

from src.evidence_policy import authoritative_evidence_texts
from src.models import (
    AnswerClaim,
    ClaimVerification,
    EvidenceContextBundle,
)
from src.step14_semantic_adjudication import (
    SOFT_ADJUDICATION_CHECKS,
    eligible_for_semantic_adjudication,
)
from src.step14_verify_claims import (
    content_tokens,
    evidence_candidates,
    support_score,
    verify_claims,
)
from src.step09_hybrid_retrieval import anatomy_terms


VERIFIER_V5_PROFILE = "hard_soft_v5"
LIST_CLAIM_SUPPORT_FLOOR = 0.55
LOW_IDENTITY_FLOOR = 0.20
LOW_CONCEPT_COVERAGE_FLOOR = 0.25
MIN_ABSOLUTE_ANSWER_RELEVANCE = 0.25
HARD_RELATION_FAMILIES = frozenset(
    {"medication_or_treatment", "safety_or_harm"}
)

# These failures can never be cleared by an LLM or learned calibrator.
HARD_SAFETY_CHECKS = frozenset(
    {
        "no_valid_citation",
        "question_only_evidence",
        "no_evidence_segment",
        "support_below_weak_threshold",
        "negation_mismatch",
        "number_mismatch",
        "anatomy_mismatch",
        "recommendation_not_supported",
        "clinical_relation_mismatch",
        "incomplete_list_support",
        "patient_context_mismatch",
        "unrelated_condition_mismatch",
        "type_conflict",
    }
)

# Relation families are intentionally broad enough to accept ordinary Arabic
# paraphrases, but narrow enough to detect a newly invented clinical relation.
RELATION_CUE_PREFIXES: dict[str, tuple[str, ...]] = {
    "medication_or_treatment": (
        "دواء",
        "دوائي",
        "دواي",
        "ادوي",
        "عقار",
        "جرع",
        "مضاد",
        "حقن",
        "حبوب",
        "علاج",
        "يعالج",
        "تعالج",
        "تناول",
        "استخدام",
        "استعمال",
    ),
    "cause": (
        "سبب",
        "اسباب",
        "يسبب",
        "تسبب",
        "بسبب",
        "ينجم",
        "ناتج",
        "نتيج",
        "يؤدي",
    ),
    "diagnosis": (
        "تشخيص",
        "يشخص",
        "يدل",
        "تشير",
        "يشير",
        "مصاب",
        "اصاب",
    ),
    "test": (
        "فحص",
        "اختبار",
        "تحليل",
        "تحاليل",
        "اشع",
        "تصوير",
        "رنين",
        "قياس",
        "منظار",
    ),
    "prevention": (
        "وقاي",
        "يمنع",
        "منع",
        "تجنب",
    ),
    "safety_or_harm": (
        "امن",
        "امان",
        "يضر",
        "ضرر",
        "خطير",
        "خطر",
        "سلام",
    ),
}

LIST_ASSERTION_PREFIXES = (
    "تشمل",
    "تتضمن",
    "تتمثل",
    "من بينها",
)


class SemanticAdjudicator(Protocol):
    """Minimal interface accepted by the v5 verifier."""

    def adjudicate(
        self,
        verifications: list[ClaimVerification],
        context: EvidenceContextBundle,
    ) -> tuple[list[ClaimVerification], dict[str, Any]]:
        ...


def _safe_float(value: Any) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _safe_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes"}


def relation_families(text: str) -> set[str]:
    """Return explicit clinical-relation families present in Arabic text."""
    tokens = content_tokens(text)
    return {
        family
        for family, prefixes in RELATION_CUE_PREFIXES.items()
        if any(
            token.startswith(prefix)
            for token in tokens
            for prefix in prefixes
        )
    }


def introduces_unsupported_relation(claim: str, evidence: str) -> bool:
    """Detect a clinical relation that appears in the claim but not evidence."""
    claim_families = relation_families(claim) & HARD_RELATION_FAMILIES
    if not claim_families:
        return False
    evidence_families = relation_families(evidence)
    return not claim_families.issubset(evidence_families)


def is_list_assertion(claim: str) -> bool:
    normalized = " ".join(claim.split())
    return any(marker in normalized for marker in LIST_ASSERTION_PREFIXES)


def _authoritative_segments(
    verification: ClaimVerification,
    context: EvidenceContextBundle,
) -> tuple[dict[str, Any], list[str]]:
    evidence_by_id = {
        str(row.get("evidence_id") or ""): row
        for row in context.evidence_items
    }
    relation_facts = {
        str(row.get("relation_id") or ""): str(row.get("fact") or "")
        for row in context.graph_facts
    }
    row = evidence_by_id.get(verification.best_evidence_id, {})
    cited_relation_facts = [
        relation_facts.get(str(relation_id), "")
        for relation_id in row.get("relation_ids", [])
        if relation_facts.get(str(relation_id), "")
    ]
    text_fields, _, _ = authoritative_evidence_texts(
        row,
        cited_relation_facts,
    )
    segments = list(
        dict.fromkeys(
            segment
            for text in text_fields
            for segment in evidence_candidates(
                text,
                verification.claim.claim,
            )
            if segment.strip()
        )
    )
    segments.sort(
        key=lambda segment: support_score(
            verification.claim.claim,
            segment,
        ),
        reverse=True,
    )
    return row, segments


def _anatomy_is_compatible(
    verification: ClaimVerification,
    context: EvidenceContextBundle,
    segments: list[str],
) -> bool:
    """Allow anatomy grounded by either the user query or cited answer.

    The answer may use a pronoun or omit a body location already stated by the
    user. Query anatomy can resolve that context, but it cannot introduce a new
    medical fact because the cited answer still has to support the claim.
    """
    claim_anatomy = anatomy_terms(verification.claim.claim)
    if not claim_anatomy:
        return True
    query_anatomy = anatomy_terms(
        f"{context.query} {context.reformulated_query}"
    )
    evidence_anatomy = anatomy_terms(" ".join(segments))
    return claim_anatomy.issubset(query_anatomy | evidence_anatomy)


def additional_hard_failures(
    verification: ClaimVerification,
    context: EvidenceContextBundle,
) -> list[str]:
    """Apply v5 gates that are absent from the frozen deterministic verifier."""
    if not verification.best_evidence_id:
        return []

    row, segments = _authoritative_segments(verification, context)
    failures: list[str] = []

    # Re-evaluate anatomy over all authoritative cited text. The legacy check
    # sometimes examined one short clause and falsely rejected a location that
    # appeared elsewhere in the same answer.
    if not _anatomy_is_compatible(verification, context, segments):
        failures.append("anatomy_mismatch")

    # Respect explicit non-anatomy mismatch metadata established upstream.
    if _safe_bool(row.get("unrelated_condition_mismatch")):
        failures.append("unrelated_condition_mismatch")
    if _safe_bool(row.get("type_conflict")):
        failures.append("type_conflict")

    # A generic passage from a different clinical scenario must not become a
    # valid answer merely because it recommends seeing a doctor.
    has_context_scores = (
        row.get("entity_identity") is not None
        and row.get("query_concept_coverage") is not None
    )
    entity_identity = _safe_float(row.get("entity_identity"))
    concept_coverage = _safe_float(row.get("query_concept_coverage"))
    answer_relevance = _safe_float(row.get("answer_relevance"))
    if (
        has_context_scores
        and (
            answer_relevance < MIN_ABSOLUTE_ANSWER_RELEVANCE
            or (
                entity_identity < LOW_IDENTITY_FLOOR
                and concept_coverage < LOW_CONCEPT_COVERAGE_FLOOR
            )
        )
    ):
        failures.append("patient_context_mismatch")

    evidence_text = " ".join(segments)
    if segments and introduces_unsupported_relation(
        verification.claim.claim,
        evidence_text,
    ):
        failures.append("clinical_relation_mismatch")

    # Multi-item claims need stronger coverage because partial support for one
    # item cannot validate the entire asserted list.
    if (
        is_list_assertion(verification.claim.claim)
        and verification.support_score < LIST_CLAIM_SUPPORT_FLOOR
    ):
        failures.append("incomplete_list_support")

    return list(dict.fromkeys(failures))


def apply_v5_hard_gates(
    verifications: list[ClaimVerification],
    context: EvidenceContextBundle,
) -> tuple[list[ClaimVerification], list[dict[str, Any]]]:
    """Harden deterministic results and expose a claim-level gate audit."""
    hardened: list[ClaimVerification] = []
    audit_rows: list[dict[str, Any]] = []

    for verification in verifications:
        extra_failures = additional_hard_failures(verification, context)
        original_failures = list(verification.failed_checks)
        if "anatomy_mismatch" in original_failures:
            _, segments = _authoritative_segments(verification, context)
            if _anatomy_is_compatible(
                verification,
                context,
                segments,
            ):
                original_failures.remove("anatomy_mismatch")
        all_failures = list(
            dict.fromkeys([*original_failures, *extra_failures])
        )
        hard_failures = sorted(set(all_failures) & HARD_SAFETY_CHECKS)
        soft_failures = sorted(set(all_failures) & SOFT_ADJUDICATION_CHECKS)

        if extra_failures or original_failures != verification.failed_checks:
            status = (
                "unsupported"
                if extra_failures
                else verification.status
            )
            verification = replace(
                verification,
                status=status,
                valid_citations=(
                    [] if extra_failures else verification.valid_citations
                ),
                valid_qa_ids=(
                    [] if extra_failures else verification.valid_qa_ids
                ),
                supporting_relation_ids=(
                    []
                    if extra_failures
                    else verification.supporting_relation_ids
                ),
                failed_checks=all_failures,
                reason=(
                    (
                        "Verifier v5 blocked the claim at a non-overridable "
                        f"safety gate: {', '.join(extra_failures)}."
                    )
                    if extra_failures
                    else verification.reason
                ),
            )

        semantic_eligible = bool(
            not hard_failures
            and eligible_for_semantic_adjudication(verification)
        )
        hardened.append(verification)
        audit_rows.append(
            {
                "claim": verification.claim.claim,
                "status_after_hard_gates": verification.status,
                "best_evidence_id": verification.best_evidence_id,
                "support_score": verification.support_score,
                "hard_failures": hard_failures,
                "soft_failures": soft_failures,
                "semantic_eligible": semantic_eligible,
            }
        )

    return hardened, audit_rows


def verify_claims_v5(
    claims: list[AnswerClaim],
    context: EvidenceContextBundle,
    *,
    semantic_adjudicator: SemanticAdjudicator | None = None,
) -> tuple[list[ClaimVerification], dict[str, Any]]:
    """Run deterministic verification, hard gates, and optional soft review."""
    deterministic = verify_claims(claims, context)
    hardened, gate_rows = apply_v5_hard_gates(deterministic, context)
    semantic_audit: dict[str, Any] = {
        "enabled": semantic_adjudicator is not None,
        "eligible_claims": sum(
            bool(row["semantic_eligible"]) for row in gate_rows
        ),
        "adjudicated_claims": 0,
        "retained_claims": 0,
        "decisions": [],
    }
    verified = hardened
    if semantic_adjudicator is not None:
        verified, semantic_audit = semantic_adjudicator.adjudicate(
            hardened,
            context,
        )

    return verified, {
        "profile": VERIFIER_V5_PROFILE,
        "hard_gate_rows": gate_rows,
        "semantic_adjudication": semantic_audit,
        "verifications": [asdict(item) for item in verified],
    }
