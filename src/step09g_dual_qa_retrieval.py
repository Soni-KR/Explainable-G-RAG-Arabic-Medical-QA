from __future__ import annotations

"""Dual-field retrieval over the full held-out-safe AHD QA corpus."""

import sqlite3
from dataclasses import asdict, dataclass, field, replace
from pathlib import Path
from typing import Any

from src.config import AppConfig
from src.models import VectorSearchResult
from src.step08a_normalize_query import normalize_query
from src.step09a_qa_corpus import (
    fts_terms,
    lexical_relevance,
    read_corpus_metadata,
)
from src.step09f_clinical_scenario import (
    clinical_scenario_compatibility,
)


QUESTION_ONLY = "question_only"
ANSWER_ONLY = "answer_only"
DUAL_NO_SCENARIO = "dual_no_scenario"
DUAL_WITH_SCENARIO = "dual_with_scenario"
DUAL_QA_MODES = (
    QUESTION_ONLY,
    ANSWER_ONLY,
    DUAL_NO_SCENARIO,
    DUAL_WITH_SCENARIO,
)
RETRIEVAL_VERSION = "dual_qa_scenario_v1"

MIN_SCENARIO_SCORE = 0.45
MIN_QUESTION_COMPATIBILITY = 0.55
MIN_ANSWER_RELEVANCE = 0.50
IDENTITY_RESCUE_QUESTION_SIMILARITY = 0.84


@dataclass(frozen=True)
class DualQARetrievalAudit:
    mode: str
    question_channel_rows: int
    answer_channel_rows: int
    union_rows: int
    exact_questions_excluded: int
    hard_conflicts_rejected: int
    score_gate_rejected: int
    returned_rows: int
    rejected_conflicts: dict[str, int] = field(default_factory=dict)


def _quoted_terms(query: str) -> list[str]:
    return [
        f'"{term.replace(chr(34), chr(34) * 2)}"'
        for term in fts_terms(query)
    ]


def _channel_candidates(
    index_path: Path,
    query: str,
    *,
    channel: str,
    limit: int,
) -> list[dict[str, Any]]:
    if channel not in {"question", "answer"}:
        raise ValueError(f"Unsupported QA retrieval channel: {channel}")
    terms = _quoted_terms(query)
    if not terms or not index_path.exists():
        return []
    column = "question_norm" if channel == "question" else "answer_norm"
    match_query = f"{column} : ({' OR '.join(terms)})"
    weights = (
        "1.0, 0.0, 0.0"
        if channel == "question"
        else "0.0, 1.0, 0.0"
    )
    connection = sqlite3.connect(str(index_path))
    try:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            f"""
SELECT q.qa_id, q.source_row_number, q.question, q.answer, q.category,
       bm25(qa_fts, {weights}) AS lexical_rank
FROM qa_fts
JOIN qa_records AS q ON q.rowid = qa_fts.rowid
WHERE qa_fts MATCH ?
ORDER BY lexical_rank
LIMIT ?
""".strip(),
            (match_query, max(1, int(limit))),
        ).fetchall()
    finally:
        connection.close()
    return [dict(row) for row in rows]


def _dot(left: list[float], right: Any) -> float:
    values = (
        right.tolist()
        if hasattr(right, "tolist")
        else list(right)
    )
    return max(
        0.0,
        min(
            1.0,
            sum(
                float(a) * float(b)
                for a, b in zip(left, values, strict=True)
            ),
        ),
    )


def _mode_score(
    mode: str,
    question_score: float,
    answer_score: float,
    scenario_score: float,
) -> float:
    if mode == QUESTION_ONLY:
        return question_score
    if mode == ANSWER_ONLY:
        return answer_score
    dual_score = (
        0.40 * question_score
        + 0.40 * answer_score
        + 0.20 * min(question_score, answer_score)
    )
    if mode == DUAL_NO_SCENARIO:
        return dual_score
    if mode == DUAL_WITH_SCENARIO:
        return 0.78 * dual_score + 0.22 * scenario_score
    raise ValueError(f"Unsupported dual QA mode: {mode}")


def search_dual_qa_corpus(
    *,
    original_query: str,
    reformulated_query: str,
    primary_intent: str,
    query_medical_phrases: list[str],
    query_embedding: list[float],
    model: Any,
    config: AppConfig,
    mode: str,
    top_k: int = 12,
    candidate_k_per_channel: int = 60,
    exclude_exact_question: bool = True,
) -> tuple[list[VectorSearchResult], DualQARetrievalAudit]:
    """Retrieve and independently score source questions and source answers."""

    if mode not in DUAL_QA_MODES:
        raise ValueError(f"Unsupported dual QA mode: {mode}")
    corpus = config.qa_corpus
    index_path = Path(corpus.index_path)
    if not corpus.enabled or not index_path.exists():
        return [], DualQARetrievalAudit(
            mode=mode,
            question_channel_rows=0,
            answer_channel_rows=0,
            union_rows=0,
            exact_questions_excluded=0,
            hard_conflicts_rejected=0,
            score_gate_rejected=0,
            returned_rows=0,
        )
    metadata = read_corpus_metadata(index_path)
    if metadata.get("corpus_version") != corpus.corpus_version:
        raise RuntimeError(
            "QA corpus version mismatch: "
            f"configured={corpus.corpus_version}, "
            f"indexed={metadata.get('corpus_version')}"
        )

    retrieval_query = " ".join(
        dict.fromkeys(
            value.strip()
            for value in (original_query, reformulated_query)
            if value and value.strip()
        )
    )
    question_rows = _channel_candidates(
        index_path,
        retrieval_query,
        channel="question",
        limit=candidate_k_per_channel,
    )
    answer_rows = _channel_candidates(
        index_path,
        retrieval_query,
        channel="answer",
        limit=candidate_k_per_channel,
    )

    union: dict[str, dict[str, Any]] = {}
    for position, row in enumerate(question_rows, start=1):
        qa_id = str(row["qa_id"])
        item = union.setdefault(qa_id, dict(row))
        item["question_position"] = position
        item["question_lexical_rank"] = float(row["lexical_rank"])
    for position, row in enumerate(answer_rows, start=1):
        qa_id = str(row["qa_id"])
        item = union.setdefault(qa_id, dict(row))
        item["answer_position"] = position
        item["answer_lexical_rank"] = float(row["lexical_rank"])

    original_norm = normalize_query(original_query).normalized_query
    exact_questions_excluded = 0
    rows: list[dict[str, Any]] = []
    for row in union.values():
        question_norm = normalize_query(
            str(row.get("question") or "")
        ).normalized_query
        if (
            exclude_exact_question
            and original_norm
            and question_norm == original_norm
        ):
            exact_questions_excluded += 1
            continue
        rows.append(row)
    if not rows:
        return [], DualQARetrievalAudit(
            mode=mode,
            question_channel_rows=len(question_rows),
            answer_channel_rows=len(answer_rows),
            union_rows=len(union),
            exact_questions_excluded=exact_questions_excluded,
            hard_conflicts_rejected=0,
            score_gate_rejected=0,
            returned_rows=0,
        )

    question_passages = [
        f"passage: {str(row.get('question') or '').strip()}"
        for row in rows
    ]
    answer_passages = [
        f"passage: {str(row.get('answer') or '').strip()}"
        for row in rows
    ]
    vectors = model.encode(
        [*question_passages, *answer_passages],
        batch_size=32,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    question_vectors = vectors[: len(rows)]
    answer_vectors = vectors[len(rows) :]

    hard_conflicts_rejected = 0
    score_gate_rejected = 0
    rejected_conflicts: dict[str, int] = {}
    scored: list[tuple[float, VectorSearchResult]] = []
    for row, question_vector, answer_vector in zip(
        rows,
        question_vectors,
        answer_vectors,
        strict=True,
    ):
        question_position = int(row.get("question_position") or 0)
        answer_position = int(row.get("answer_position") or 0)
        # Keep the single-channel ablations genuinely independent. The dual
        # variants use the union, but question-only and answer-only may score
        # only rows actually retrieved by their respective FTS channel.
        if mode == QUESTION_ONLY and not question_position:
            continue
        if mode == ANSWER_ONLY and not answer_position:
            continue
        question_similarity = _dot(
            query_embedding,
            question_vector,
        )
        answer_similarity = _dot(query_embedding, answer_vector)
        question_lexical = (
            lexical_relevance(
                retrieval_query,
                str(row.get("question") or ""),
                question_position,
            )
            if question_position
            else 0.0
        )
        answer_lexical = (
            lexical_relevance(
                retrieval_query,
                str(row.get("answer") or ""),
                answer_position,
            )
            if answer_position
            else 0.0
        )
        question_score = (
            0.80 * question_similarity + 0.20 * question_lexical
        )
        answer_score = (
            0.85 * answer_similarity + 0.15 * answer_lexical
        )
        scenario = clinical_scenario_compatibility(
            reformulated_query or original_query,
            str(row.get("question") or ""),
            primary_intent=primary_intent,
            query_medical_phrases=query_medical_phrases,
        )
        if mode == DUAL_WITH_SCENARIO and scenario.hard_conflict:
            hard_conflicts_rejected += 1
            for conflict in scenario.conflicts:
                rejected_conflicts[conflict] = (
                    rejected_conflicts.get(conflict, 0) + 1
                )
            continue
        if mode == DUAL_WITH_SCENARIO:
            identity_unmatched = (
                "medical_identity_unmatched" in scenario.conflicts
            )
            if (
                question_score < MIN_QUESTION_COMPATIBILITY
                or answer_score < MIN_ANSWER_RELEVANCE
                or scenario.score < MIN_SCENARIO_SCORE
                or (
                    identity_unmatched
                    and question_similarity
                    < IDENTITY_RESCUE_QUESTION_SIMILARITY
                )
            ):
                score_gate_rejected += 1
                continue

        score = _mode_score(
            mode,
            question_score,
            answer_score,
            scenario.score,
        )
        qa_id = str(row["qa_id"])
        metadata_payload = {
            "question": str(row.get("question") or ""),
            "answer": str(row.get("answer") or ""),
            "category": str(row.get("category") or ""),
            "source_row_number": int(row["source_row_number"]),
            "source_quality": "ahd_heldout_safe_corpus",
            "field": "answer",
            "evidence_origin": "answer",
            "retrieval_channel": f"dual_qa::{mode}",
            "retrieval_version": RETRIEVAL_VERSION,
            "question_vector_similarity": round(
                question_similarity,
                6,
            ),
            "answer_vector_similarity": round(answer_similarity, 6),
            "question_lexical_score": round(question_lexical, 6),
            "answer_lexical_score": round(answer_lexical, 6),
            "question_channel_score": round(question_score, 6),
            "answer_channel_score": round(answer_score, 6),
            "vector_similarity": round(
                min(question_score, answer_score)
                if mode in {DUAL_NO_SCENARIO, DUAL_WITH_SCENARIO}
                else question_score
                if mode == QUESTION_ONLY
                else answer_score,
                6,
            ),
            "scenario_score": scenario.score,
            "scenario_hard_conflict": scenario.hard_conflict,
            "scenario_conflicts": scenario.conflicts,
            "scenario_matches": scenario.matches,
            "scenario_dimensions": scenario.dimensions,
            "question_position": question_position,
            "answer_position": answer_position,
            "question_lexical_rank": row.get(
                "question_lexical_rank"
            ),
            "answer_lexical_rank": row.get("answer_lexical_rank"),
            "corpus_version": corpus.corpus_version,
        }
        scored.append(
            (
                score,
                VectorSearchResult(
                    result_id=qa_id,
                    document_type="QARecord",
                    score=round(score, 6),
                    qa_id=qa_id,
                    title=str(row.get("question") or ""),
                    text=(
                        f"{str(row.get('question') or '')}\n"
                        f"{str(row.get('answer') or '')}"
                    ),
                    metadata=metadata_payload,
                ),
            )
        )

    results = [
        result
        for _, result in sorted(
            scored,
            key=lambda item: (
                item[0],
                float(
                    item[1].metadata.get(
                        "question_channel_score"
                    )
                    or 0.0
                ),
                float(
                    item[1].metadata.get("answer_channel_score")
                    or 0.0
                ),
                item[1].qa_id,
            ),
            reverse=True,
        )[: max(1, int(top_k))]
    ]
    return results, DualQARetrievalAudit(
        mode=mode,
        question_channel_rows=len(question_rows),
        answer_channel_rows=len(answer_rows),
        union_rows=len(union),
        exact_questions_excluded=exact_questions_excluded,
        hard_conflicts_rejected=hard_conflicts_rejected,
        score_gate_rejected=score_gate_rejected,
        returned_rows=len(results),
        rejected_conflicts=dict(sorted(rejected_conflicts.items())),
    )


def audit_payload(audit: DualQARetrievalAudit) -> dict[str, Any]:
    return asdict(audit)


def rank_prepared_dual_results(
    prepared_results: list[VectorSearchResult],
    prepared_audit: DualQARetrievalAudit,
    *,
    mode: str,
    top_k: int = 12,
) -> tuple[list[VectorSearchResult], DualQARetrievalAudit]:
    """Derive an ablation from one fully embedded union candidate pool.

    ``prepared_results`` should come from ``search_dual_qa_corpus`` with
    ``mode=DUAL_NO_SCENARIO`` and a top_k large enough to retain the complete
    question/answer FTS union. This function performs no model inference.
    """

    if mode not in DUAL_QA_MODES:
        raise ValueError(f"Unsupported dual QA mode: {mode}")

    hard_conflicts_rejected = 0
    score_gate_rejected = 0
    rejected_conflicts: dict[str, int] = {}
    ranked: list[VectorSearchResult] = []
    for result in prepared_results:
        metadata = dict(result.metadata)
        question_position = int(metadata.get("question_position") or 0)
        answer_position = int(metadata.get("answer_position") or 0)
        if mode == QUESTION_ONLY and not question_position:
            continue
        if mode == ANSWER_ONLY and not answer_position:
            continue

        question_score = float(
            metadata.get("question_channel_score") or 0.0
        )
        answer_score = float(
            metadata.get("answer_channel_score") or 0.0
        )
        scenario_score = float(metadata.get("scenario_score") or 0.0)
        scenario_conflicts = [
            str(value)
            for value in metadata.get("scenario_conflicts", [])
        ]
        if (
            mode == DUAL_WITH_SCENARIO
            and bool(metadata.get("scenario_hard_conflict"))
        ):
            hard_conflicts_rejected += 1
            for conflict in scenario_conflicts:
                rejected_conflicts[conflict] = (
                    rejected_conflicts.get(conflict, 0) + 1
                )
            continue
        if mode == DUAL_WITH_SCENARIO:
            identity_unmatched = (
                "medical_identity_unmatched" in scenario_conflicts
            )
            question_similarity = float(
                metadata.get("question_vector_similarity") or 0.0
            )
            if (
                question_score < MIN_QUESTION_COMPATIBILITY
                or answer_score < MIN_ANSWER_RELEVANCE
                or scenario_score < MIN_SCENARIO_SCORE
                or (
                    identity_unmatched
                    and question_similarity
                    < IDENTITY_RESCUE_QUESTION_SIMILARITY
                )
            ):
                score_gate_rejected += 1
                continue

        score = _mode_score(
            mode,
            question_score,
            answer_score,
            scenario_score,
        )
        metadata.update(
            {
                "retrieval_channel": f"dual_qa::{mode}",
                "vector_similarity": round(
                    min(question_score, answer_score)
                    if mode in {
                        DUAL_NO_SCENARIO,
                        DUAL_WITH_SCENARIO,
                    }
                    else question_score
                    if mode == QUESTION_ONLY
                    else answer_score,
                    6,
                ),
            }
        )
        ranked.append(
            replace(
                result,
                score=round(score, 6),
                metadata=metadata,
            )
        )

    ranked.sort(
        key=lambda item: (
            item.score,
            float(
                item.metadata.get("question_channel_score") or 0.0
            ),
            float(
                item.metadata.get("answer_channel_score") or 0.0
            ),
            item.qa_id,
        ),
        reverse=True,
    )
    results = ranked[: max(1, int(top_k))]
    return results, DualQARetrievalAudit(
        mode=mode,
        question_channel_rows=prepared_audit.question_channel_rows,
        answer_channel_rows=prepared_audit.answer_channel_rows,
        union_rows=prepared_audit.union_rows,
        exact_questions_excluded=(
            prepared_audit.exact_questions_excluded
        ),
        hard_conflicts_rejected=hard_conflicts_rejected,
        score_gate_rejected=score_gate_rejected,
        returned_rows=len(results),
        rejected_conflicts=dict(sorted(rejected_conflicts.items())),
    )
