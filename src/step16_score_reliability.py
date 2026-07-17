from __future__ import annotations

from src.models import ClaimVerification, EvidenceContextBundle, MitigatedAnswer, ReliabilityResult


SOURCE_PRIORS = {"preprocessed_id": 1.0, "preprocessed_source_row": 0.9, "mention_evidence": 0.5, "unknown": 0.6}


def safe_average(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def reliability_label(score: float) -> str:
    if score >= 0.80:
        return "high"
    if score >= 0.55:
        return "medium"
    return "low"


def score_reliability(
    mitigated: MitigatedAnswer,
    verifications: list[ClaimVerification],
    context: EvidenceContextBundle,
) -> ReliabilityResult:
    claim_count = len(verifications)
    supported = [item for item in verifications if item.status == "supported"]
    unsupported = [item for item in verifications if item.status == "unsupported"]
    claim_support_rate = len(supported) / claim_count if claim_count else 0.0
    hallucination_rate = len(unsupported) / claim_count if claim_count else 0.0
    mean_support = safe_average([item.support_score for item in supported])
    evidence_coverage = (
        sum(1 for item in supported if item.valid_citations) / claim_count if claim_count else 0.0
    )

    facts = {str(item.get("relation_id") or ""): item for item in context.graph_facts}
    supported_relation_ids = {
        relation_id for item in supported for relation_id in item.supporting_relation_ids
    }
    relation_confidence = safe_average(
        [float(facts[item].get("confidence") or 0.0) for item in supported_relation_ids if item in facts]
    )

    evidence_by_id = {str(item.get("evidence_id") or ""): item for item in context.evidence_items}
    cited_ids = {citation for item in supported for citation in item.valid_citations}
    source_reliability = safe_average(
        [
            SOURCE_PRIORS.get(str(evidence_by_id[item].get("source_quality") or "unknown"), 0.6)
            for item in cited_ids
            if item in evidence_by_id
        ]
    )
    answerability_score = {
        "answerable": 1.0,
        "partially_answerable": 0.55,
        "insufficient_evidence": 0.0,
    }.get(mitigated.answerability, 0.0)

    components = {
        "claim_support": claim_support_rate,
        "mean_support": mean_support,
        "evidence_coverage": evidence_coverage,
        "relation_confidence": relation_confidence,
        "source_reliability": source_reliability,
        "answerability": answerability_score,
    }
    score = (
        0.30 * claim_support_rate
        + 0.20 * mean_support
        + 0.15 * evidence_coverage
        + 0.15 * relation_confidence
        + 0.15 * source_reliability
        + 0.05 * answerability_score
    )
    if mitigated.answerability == "insufficient_evidence":
        score = min(score, 0.20)
    score = max(0.0, min(1.0, score))
    return ReliabilityResult(
        score=round(score, 6),
        label=reliability_label(score),
        claim_support_rate=round(claim_support_rate, 6),
        hallucination_rate=round(hallucination_rate, 6),
        evidence_coverage=round(evidence_coverage, 6),
        relation_confidence=round(relation_confidence, 6),
        source_reliability=round(source_reliability, 6),
        calibrated=False,
        components={key: round(value, 6) for key, value in components.items()},
    )
