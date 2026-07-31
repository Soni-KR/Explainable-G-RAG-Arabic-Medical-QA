from __future__ import annotations

"""Offline oracle diagnostics for empty-context evaluation queries.

The reference answer is intentionally used here, after production retrieval,
to determine whether answer-bearing evidence exists in the held-out-safe AHD
corpus. This module is evaluation-only and must never be imported by the
production retrieval path.
"""

import sqlite3
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from src.query_relevance import query_concept_coverage
from src.step08a_normalize_query import normalize_query
from src.step09a_qa_corpus import fts_terms
from src.step09f_clinical_scenario import (
    clinical_scenario_compatibility,
)


NO_EQUIVALENT_EVIDENCE = "no_equivalent_evidence_exists"
RETRIEVER_MISS = "equivalent_evidence_exists_retriever_miss"
STEP10_11_REJECTION = "relevant_evidence_retrieved_but_step10_11_removed"
BROAD_OR_MISMATCHED = "only_broad_or_mismatched_evidence_exists"
FAILURE_CLASSES = (
    NO_EQUIVALENT_EVIDENCE,
    RETRIEVER_MISS,
    STEP10_11_REJECTION,
    BROAD_OR_MISMATCHED,
)

# Diagnostic thresholds are frozen for this audit. They are not production
# retrieval or verification thresholds.
STRONG_ANSWER_SIMILARITY = 0.88
BORDERLINE_ANSWER_SIMILARITY = 0.84
BROAD_ANSWER_SIMILARITY = 0.80
MIN_SCENARIO_SCORE = 0.55
MIN_CONCEPT_COVERAGE = 0.50
MIN_QUESTION_SIMILARITY = 0.80


@dataclass(frozen=True)
class OracleAnswerCandidate:
    oracle_rank: int
    qa_id: str
    source_row_number: int
    question: str
    answer: str
    category: str
    answer_fts_rank: int
    answer_similarity: float
    question_similarity: float
    scenario_score: float
    scenario_hard_conflict: bool
    scenario_conflicts: list[str]
    query_concept_coverage: float
    exact_reference_answer_match: bool
    equivalent_evidence: bool
    borderline_equivalence: bool
    retrieved_by_current_pipeline: bool
    current_retrieval_ids: list[str]


@dataclass(frozen=True)
class OracleFailureDiagnosis:
    failure_class: str
    confidence: str
    requires_manual_review: bool
    reason: str
    strong_equivalent_count: int
    borderline_count: int
    strongest_answer_similarity: float
    strongest_question_similarity: float
    strongest_scenario_score: float


def normalized(text: Any) -> str:
    return normalize_query(str(text or "")).normalized_query


def _quoted_terms(text: str, limit: int = 32) -> list[str]:
    return [
        f'"{term.replace(chr(34), chr(34) * 2)}"'
        for term in fts_terms(
            text,
            limit=limit,
            include_legacy_forms=True,
        )
    ]


def answer_fts_candidates(
    index_path: Path,
    reference_answer: str,
    *,
    original_query: str,
    limit: int,
) -> tuple[list[dict[str, Any]], int]:
    """Search the full answer FTS column and exclude the source question."""

    terms = _quoted_terms(reference_answer)
    if not terms:
        return [], 0
    match_query = f"answer_norm : ({' OR '.join(terms)})"
    connection = sqlite3.connect(str(index_path))
    try:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
SELECT q.qa_id, q.source_row_number, q.question, q.answer, q.category,
       bm25(qa_fts, 0.0, 1.0, 0.0) AS answer_fts_score
FROM qa_fts
JOIN qa_records AS q ON q.rowid = qa_fts.rowid
WHERE qa_fts MATCH ?
ORDER BY answer_fts_score
LIMIT ?
""".strip(),
            (match_query, max(1, int(limit))),
        ).fetchall()
    finally:
        connection.close()

    original_norm = normalized(original_query)
    excluded = 0
    deduplicated: dict[tuple[str, str], dict[str, Any]] = {}
    for position, row in enumerate(rows, start=1):
        payload = dict(row)
        if (
            original_norm
            and normalized(payload.get("question")) == original_norm
        ):
            excluded += 1
            continue
        key = (
            normalized(payload.get("question")),
            normalized(payload.get("answer")),
        )
        if not all(key) or key in deduplicated:
            continue
        payload["answer_fts_rank"] = position
        deduplicated[key] = payload
    return list(deduplicated.values()), excluded


def _dot(left: Any, right: Any) -> float:
    left_values = (
        left.tolist() if hasattr(left, "tolist") else list(left)
    )
    right_values = (
        right.tolist() if hasattr(right, "tolist") else list(right)
    )
    return max(
        0.0,
        min(
            1.0,
            sum(
                float(a) * float(b)
                for a, b in zip(
                    left_values,
                    right_values,
                    strict=True,
                )
            ),
        ),
    )


def rank_oracle_candidates(
    rows: list[dict[str, Any]],
    *,
    query: str,
    reference_answer: str,
    primary_intent: str,
    query_medical_phrases: list[str],
    current_retrieval_by_qa: dict[str, list[str]],
    current_retrieval_content: set[tuple[str, str]],
    model: Any,
    top_k: int,
) -> list[OracleAnswerCandidate]:
    """E5-rank answer candidates, then inspect source-question compatibility."""

    if not rows:
        return []
    reference_vector, query_vector = model.encode(
        [
            f"query: {reference_answer}",
            f"query: {query}",
        ],
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    answer_vectors = model.encode(
        [
            f"passage: {str(row.get('answer') or '').strip()}"
            for row in rows
        ],
        batch_size=64,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    answer_ranked = sorted(
        zip(rows, answer_vectors, strict=True),
        key=lambda pair: _dot(reference_vector, pair[1]),
        reverse=True,
    )[: max(1, int(top_k))]
    question_vectors = model.encode(
        [
            f"passage: {str(row.get('question') or '').strip()}"
            for row, _ in answer_ranked
        ],
        batch_size=64,
        normalize_embeddings=True,
        show_progress_bar=False,
    )

    candidates: list[OracleAnswerCandidate] = []
    for oracle_rank, (
        (row, answer_vector),
        question_vector,
    ) in enumerate(
        zip(answer_ranked, question_vectors, strict=True),
        start=1,
    ):
        question = str(row.get("question") or "").strip()
        answer = str(row.get("answer") or "").strip()
        qa_id = str(row.get("qa_id") or "").strip()
        answer_similarity = _dot(reference_vector, answer_vector)
        question_similarity = _dot(query_vector, question_vector)
        scenario = clinical_scenario_compatibility(
            query,
            question,
            primary_intent=primary_intent,
            query_medical_phrases=query_medical_phrases,
        )
        concept_coverage = query_concept_coverage(
            query,
            f"{question} {answer}",
            query_medical_phrases,
        )
        exact_reference = bool(
            normalized(answer)
            and normalized(answer) == normalized(reference_answer)
        )
        scenario_compatible = bool(
            not scenario.hard_conflict
            and (
                scenario.score >= MIN_SCENARIO_SCORE
                or question_similarity >= MIN_QUESTION_SIMILARITY
            )
            and concept_coverage >= MIN_CONCEPT_COVERAGE
        )
        equivalent = bool(
            (
                exact_reference
                or answer_similarity
                >= STRONG_ANSWER_SIMILARITY
            )
            and scenario_compatible
        )
        borderline = bool(
            not equivalent
            and (
                exact_reference
                or answer_similarity
                >= BORDERLINE_ANSWER_SIMILARITY
            )
            and not scenario.hard_conflict
            and concept_coverage >= 0.25
        )
        content_key = (normalized(question), normalized(answer))
        current_ids = list(current_retrieval_by_qa.get(qa_id, []))
        retrieved = bool(
            current_ids or content_key in current_retrieval_content
        )
        candidates.append(
            OracleAnswerCandidate(
                oracle_rank=oracle_rank,
                qa_id=qa_id,
                source_row_number=int(
                    row.get("source_row_number") or 0
                ),
                question=question,
                answer=answer,
                category=str(row.get("category") or "").strip(),
                answer_fts_rank=int(
                    row.get("answer_fts_rank") or 0
                ),
                answer_similarity=round(
                    answer_similarity,
                    6,
                ),
                question_similarity=round(
                    question_similarity,
                    6,
                ),
                scenario_score=scenario.score,
                scenario_hard_conflict=scenario.hard_conflict,
                scenario_conflicts=scenario.conflicts,
                query_concept_coverage=round(
                    concept_coverage,
                    6,
                ),
                exact_reference_answer_match=exact_reference,
                equivalent_evidence=equivalent,
                borderline_equivalence=borderline,
                retrieved_by_current_pipeline=retrieved,
                current_retrieval_ids=current_ids,
            )
        )
    return candidates


def diagnose_failure(
    candidates: list[OracleAnswerCandidate],
) -> OracleFailureDiagnosis:
    """Assign one of the four predeclared failure classes."""

    if not candidates:
        return OracleFailureDiagnosis(
            failure_class=NO_EQUIVALENT_EVIDENCE,
            confidence="low",
            requires_manual_review=True,
            reason=(
                "The reference-answer FTS search returned no candidate; "
                "semantic corpus absence cannot be proven without a full "
                "answer-vector index."
            ),
            strong_equivalent_count=0,
            borderline_count=0,
            strongest_answer_similarity=0.0,
            strongest_question_similarity=0.0,
            strongest_scenario_score=0.0,
        )

    strong = [
        candidate
        for candidate in candidates
        if candidate.equivalent_evidence
    ]
    borderline = [
        candidate
        for candidate in candidates
        if candidate.borderline_equivalence
    ]
    top = candidates[0]
    if strong:
        retrieved = [
            candidate
            for candidate in strong
            if candidate.retrieved_by_current_pipeline
        ]
        if retrieved:
            failure_class = STEP10_11_REJECTION
            reason = (
                "At least one oracle-equivalent passage was present in the "
                "saved retrieval pool but the frozen Step 11 context was empty."
            )
        else:
            failure_class = RETRIEVER_MISS
            reason = (
                "Equivalent evidence was found by reference-answer search but "
                "was absent from the saved production retrieval pool."
            )
        confidence = (
            "high"
            if any(
                candidate.exact_reference_answer_match
                for candidate in strong
            )
            else "medium"
        )
        return OracleFailureDiagnosis(
            failure_class=failure_class,
            confidence=confidence,
            requires_manual_review=confidence != "high",
            reason=reason,
            strong_equivalent_count=len(strong),
            borderline_count=len(borderline),
            strongest_answer_similarity=top.answer_similarity,
            strongest_question_similarity=top.question_similarity,
            strongest_scenario_score=top.scenario_score,
        )

    if borderline:
        return OracleFailureDiagnosis(
            failure_class=BROAD_OR_MISMATCHED,
            confidence="low",
            requires_manual_review=True,
            reason=(
                "Only borderline semantic matches were found. Manual review "
                "is required to distinguish an acceptable paraphrase from a "
                "related but different clinical scenario."
            ),
            strong_equivalent_count=0,
            borderline_count=len(borderline),
            strongest_answer_similarity=top.answer_similarity,
            strongest_question_similarity=top.question_similarity,
            strongest_scenario_score=top.scenario_score,
        )

    broad_signal = bool(
        top.answer_similarity >= BROAD_ANSWER_SIMILARITY
        or top.scenario_score >= MIN_SCENARIO_SCORE
        or top.query_concept_coverage >= 0.25
    )
    if broad_signal:
        failure_class = BROAD_OR_MISMATCHED
        confidence = "medium"
        reason = (
            "The oracle found medically related passages, but none met the "
            "equivalence and clinical-scenario compatibility gates."
        )
    else:
        failure_class = NO_EQUIVALENT_EVIDENCE
        confidence = "medium"
        reason = (
            "No equivalent evidence was found in the full answer-FTS oracle "
            "shortlist. This is a lower-bound diagnosis because a full "
            "808k-answer semantic index is not available."
        )
    return OracleFailureDiagnosis(
        failure_class=failure_class,
        confidence=confidence,
        requires_manual_review=(
            confidence != "high"
            and top.answer_similarity
            >= BROAD_ANSWER_SIMILARITY - 0.02
        ),
        reason=reason,
        strong_equivalent_count=0,
        borderline_count=0,
        strongest_answer_similarity=top.answer_similarity,
        strongest_question_similarity=top.question_similarity,
        strongest_scenario_score=top.scenario_score,
    )


def candidate_payload(
    candidate: OracleAnswerCandidate,
) -> dict[str, Any]:
    return asdict(candidate)


def diagnosis_payload(
    diagnosis: OracleFailureDiagnosis,
) -> dict[str, Any]:
    return asdict(diagnosis)
