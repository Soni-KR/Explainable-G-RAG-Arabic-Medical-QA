from __future__ import annotations

"""Shared evidence-source policy used by retrieval and reliability scoring."""

from collections.abc import Iterable, Mapping
from typing import Any

from src.step08a_normalize_query import normalize_query


SOURCE_RELIABILITY_PRIORS: dict[str, float] = {
    "preprocessed_id": 1.0,
    "ahd_heldout_safe_corpus": 0.95,
    "preprocessed_source_row": 0.90,
    "supplemental_dataset_validated": 0.80,
    "unknown": 0.65,
    "": 0.65,
    "mention_evidence": 0.55,
}

QUESTION_EVIDENCE = "question"
ANSWER_EVIDENCE = "answer"
VALIDATED_RELATION_EVIDENCE = "validated_relation"
UNKNOWN_EVIDENCE = "unknown"


def source_reliability_prior(source_quality: str) -> float:
    """Return one consistent prior without treating unknown sources as trusted."""
    key = str(source_quality or "unknown")
    return SOURCE_RELIABILITY_PRIORS.get(key, SOURCE_RELIABILITY_PRIORS["unknown"])


def _normalized(text: Any) -> str:
    return normalize_query(str(text or "")).normalized_query


def _contained(candidate: str, container: str) -> bool:
    """Compare normalized non-empty text without using fuzzy similarity."""
    candidate_norm = _normalized(candidate)
    container_norm = _normalized(container)
    return bool(candidate_norm and container_norm and candidate_norm in container_norm)


def infer_evidence_origin(
    *,
    evidence_origin: Any = "",
    field: Any = "",
    source_quality: Any = "",
    evidence: Any = "",
    source_question: Any = "",
    source_answer: Any = "",
) -> str:
    """Resolve whether a passage came from a question, answer, or validated edge.

    New retrieval records carry an explicit origin. The content comparison is a
    conservative compatibility fallback for frozen artifacts created before
    that metadata was propagated through Steps 9-11.
    """
    explicit = str(evidence_origin or "").strip().lower()
    source_field = str(field or "").strip().lower()
    for value in (explicit, source_field):
        if value in {"question", "source_question"}:
            return QUESTION_EVIDENCE
        if value in {"answer", "source_answer", "qa_answer"}:
            return ANSWER_EVIDENCE
        if value in {"validated_relation", "relation", "graph_relation"}:
            return VALIDATED_RELATION_EVIDENCE

    evidence_text = str(evidence or "").strip()
    if not evidence_text:
        return UNKNOWN_EVIDENCE

    in_answer = _contained(evidence_text, str(source_answer or ""))
    in_question = _contained(evidence_text, str(source_question or ""))
    if in_answer and not in_question:
        return ANSWER_EVIDENCE
    if in_question and not in_answer:
        return QUESTION_EVIDENCE

    # Mention evidence is the only legacy source known to mix question and
    # answer spans. If a span occurs in both, prefer the answer only when the
    # stored answer is non-empty; otherwise it cannot support an answer claim.
    if str(source_quality or "").strip() == "mention_evidence":
        if in_answer and str(source_answer or "").strip():
            return ANSWER_EVIDENCE
        if in_question:
            return QUESTION_EVIDENCE
    return UNKNOWN_EVIDENCE


def authoritative_evidence_texts(
    row: Mapping[str, Any],
    relation_facts: Iterable[str] = (),
) -> tuple[list[str], str, bool]:
    """Return factual support fields while excluding source-question text.

    The source question remains useful for retrieval and relevance scoring, but
    it cannot establish a generated medical fact. Answer text and validated
    relation facts remain authoritative.
    """
    evidence = str(row.get("evidence") or "").strip()
    source_answer = str(row.get("source_answer") or "").strip()
    origin = infer_evidence_origin(
        evidence_origin=row.get("evidence_origin"),
        field=row.get("field"),
        source_quality=row.get("source_quality"),
        evidence=evidence,
        source_question=row.get("source_question"),
        source_answer=source_answer,
    )
    question_evidence_excluded = bool(
        evidence and origin == QUESTION_EVIDENCE
    )
    texts: list[str] = []
    if evidence and not question_evidence_excluded:
        texts.append(evidence)
    if source_answer:
        texts.append(source_answer)
    texts.extend(str(fact or "").strip() for fact in relation_facts if str(fact or "").strip())
    return list(dict.fromkeys(texts)), origin, question_evidence_excluded
