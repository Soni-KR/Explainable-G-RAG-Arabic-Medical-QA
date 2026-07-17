from __future__ import annotations

from src.models import AnswerClaim, ClaimVerification, GeneratedAnswer, MitigatedAnswer


INSUFFICIENT_ANSWER = "لا توجد أدلة كافية في الرسم الطبي للإجابة بثقة. يُنصح باستشارة طبيب مختص."


def mitigate_hallucinations(
    generated: GeneratedAnswer,
    verifications: list[ClaimVerification],
    include_weak: bool = False,
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

    if not verifications or not kept_claims:
        answerability = "insufficient_evidence"
        answer = INSUFFICIENT_ANSWER
    elif removed_rows:
        answerability = "partially_answerable"
        answer = " ".join(
            f"{row.claim.claim} [{'، '.join(row.valid_citations)}]" for row in kept_rows
        )
    else:
        answerability = "answerable"
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
        kept_claims=kept_claims,
        removed_claims=[row.claim.claim for row in removed_rows],
        limitations=list(dict.fromkeys(limitations)),
    )
