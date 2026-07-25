from __future__ import annotations

from src.models import (
    AnswerClaim,
    ClaimVerification,
    EvidenceContextBundle,
    GeneratedAnswer,
    MitigatedAnswer,
)
from src.query_relevance import missing_query_concepts, query_concept_coverage


INSUFFICIENT_ANSWER = "لا توجد أدلة كافية ضمن المصادر المسترجعة للإجابة بثقة. يُنصح باستشارة طبيب مختص."


def mitigate_hallucinations(
    generated: GeneratedAnswer,
    verifications: list[ClaimVerification],
    include_weak: bool = False,
    context: EvidenceContextBundle | None = None,
) -> MitigatedAnswer:
    if generated.generation_status == "fallback" and generated.fallback_type != "insufficient_evidence":
        return MitigatedAnswer(
            answer=generated.answer,
            answerability="generation_unavailable",
            limitations=list(generated.limitations),
        )

    allowed_statuses = {"supported", "weakly_supported"} if include_weak else {"supported"}
    kept_rows = [row for row in verifications if row.status in allowed_statuses]
    removed_rows = [row for row in verifications if row.status not in allowed_statuses]
    kept_claims = [row.claim for row in kept_rows]
    query = (
        (context.reformulated_query or context.query)
        if context is not None
        else generated.query
    )
    kept_text = " ".join(item.claim for item in kept_claims)
    query_medical_phrases = context.query_medical_phrases if context is not None else []
    query_coverage = (
        query_concept_coverage(query, kept_text, query_medical_phrases)
        if kept_claims
        else 0.0
    )
    missing_concepts = missing_query_concepts(
        query,
        kept_text,
        query_medical_phrases,
    )

    if not verifications or not kept_claims:
        answerability = "insufficient_evidence"
        answer = INSUFFICIENT_ANSWER
    elif query_coverage >= 0.80 and not removed_rows:
        answerability = "fully_answerable"
        answer = " ".join(
            f"{row.claim.claim} [{'، '.join(row.valid_citations)}]" for row in kept_rows
        )
    elif query_coverage >= 0.50:
        answerability = "partially_answerable"
        answer = " ".join(
            f"{row.claim.claim} [{'، '.join(row.valid_citations)}]" for row in kept_rows
        )
    else:
        answerability = "supported_but_incomplete"
        answer = " ".join(
            f"{row.claim.claim} [{'، '.join(row.valid_citations)}]" for row in kept_rows
        )

    limitations = list(generated.limitations)
    if removed_rows:
        limitations.append("أزيلت ادعاءات لم تدعمها الأدلة المسترجعة بشكل كافٍ.")
    if answerability == "insufficient_evidence":
        limitations.append("لا يمكن تكوين إجابة طبية موثوقة من الأدلة الحالية.")
    return MitigatedAnswer(
        answer=answer,
        answerability=answerability,
        query_coverage=round(query_coverage, 6),
        missing_query_concepts=missing_concepts,
        kept_claims=kept_claims,
        removed_claims=[row.claim.claim for row in removed_rows],
        limitations=list(dict.fromkeys(limitations)),
    )
