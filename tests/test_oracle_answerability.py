from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from src.oracle_answerability import (
    BROAD_OR_MISMATCHED,
    NO_EQUIVALENT_EVIDENCE,
    RETRIEVER_MISS,
    STEP10_11_REJECTION,
    OracleAnswerCandidate,
    answer_fts_candidates,
    diagnose_failure,
    rank_oracle_candidates,
)


class StubModel:
    def encode(self, texts, **_kwargs):
        vectors = []
        for text in texts:
            value = str(text)
            if "الإجابة المرجعية" in value:
                vectors.append([1.0, 0.0, 0.0])
            elif "علاج الربو" in value:
                vectors.append([0.0, 1.0, 0.0])
            else:
                vectors.append([0.0, 0.0, 1.0])
        return vectors


def create_index(path: Path) -> None:
    connection = sqlite3.connect(str(path))
    connection.executescript(
        """
CREATE TABLE qa_records (
    rowid INTEGER PRIMARY KEY,
    qa_id TEXT NOT NULL UNIQUE,
    source_row_number INTEGER NOT NULL,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    category TEXT NOT NULL,
    question_norm TEXT NOT NULL,
    answer_norm TEXT NOT NULL,
    content_hash TEXT NOT NULL UNIQUE,
    corpus_version TEXT NOT NULL
);
CREATE VIRTUAL TABLE qa_fts USING fts5(
    question_norm,
    answer_norm,
    category,
    tokenize='unicode61'
);
CREATE TABLE corpus_metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""
    )
    rows = [
        (
            1,
            "qa_original",
            1,
            "ما علاج الربو؟",
            "الإجابة المرجعية لعلاج الربو.",
            "صدر",
            "ما علاج الربو?",
            "الاجابه المرجعيه لعلاج الربو.",
            "hash-1",
            "test_v1",
        ),
        (
            2,
            "qa_equivalent",
            2,
            "ما علاج الربو عند المريض؟",
            "الإجابة المرجعية لعلاج الربو.",
            "صدر",
            "ما علاج الربو عند المريض?",
            "الاجابه المرجعيه لعلاج الربو.",
            "hash-2",
            "test_v1",
        ),
    ]
    connection.executemany(
        """
INSERT INTO qa_records (
    rowid, qa_id, source_row_number, question, answer, category,
    question_norm, answer_norm, content_hash, corpus_version
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""",
        rows,
    )
    connection.executemany(
        """
INSERT INTO qa_fts(rowid, question_norm, answer_norm, category)
VALUES (?, ?, ?, ?)
""",
        [(row[0], row[6], row[7], row[5]) for row in rows],
    )
    connection.execute(
        "INSERT INTO corpus_metadata(key, value) VALUES (?, ?)",
        ("corpus_version", json.dumps("test_v1")),
    )
    connection.commit()
    connection.close()


def candidate(
    *,
    equivalent: bool,
    retrieved: bool,
    borderline: bool = False,
) -> OracleAnswerCandidate:
    return OracleAnswerCandidate(
        oracle_rank=1,
        qa_id="qa_1",
        source_row_number=1,
        question="سؤال",
        answer="إجابة",
        category="عام",
        answer_fts_rank=1,
        answer_similarity=0.91 if equivalent else 0.85,
        question_similarity=0.88,
        scenario_score=0.75,
        scenario_hard_conflict=False,
        scenario_conflicts=[],
        query_concept_coverage=1.0,
        exact_reference_answer_match=False,
        equivalent_evidence=equivalent,
        borderline_equivalence=borderline,
        retrieved_by_current_pipeline=retrieved,
        current_retrieval_ids=["qa::qa_1"] if retrieved else [],
    )


def test_answer_oracle_excludes_original_question(
    tmp_path: Path,
) -> None:
    index_path = tmp_path / "qa.sqlite"
    create_index(index_path)

    rows, excluded = answer_fts_candidates(
        index_path,
        "الإجابة المرجعية لعلاج الربو.",
        original_query="ما علاج الربو؟",
        limit=10,
    )

    assert excluded == 1
    assert [row["qa_id"] for row in rows] == ["qa_equivalent"]


def test_exact_reference_duplicate_is_oracle_equivalent(
    tmp_path: Path,
) -> None:
    index_path = tmp_path / "qa.sqlite"
    create_index(index_path)
    rows, _ = answer_fts_candidates(
        index_path,
        "الإجابة المرجعية لعلاج الربو.",
        original_query="ما علاج الربو؟",
        limit=10,
    )

    ranked = rank_oracle_candidates(
        rows,
        query="ما علاج الربو؟",
        reference_answer="الإجابة المرجعية لعلاج الربو.",
        primary_intent="treatment_request",
        query_medical_phrases=["ربو"],
        current_retrieval_by_qa={},
        current_retrieval_content=set(),
        model=StubModel(),
        top_k=5,
    )

    assert len(ranked) == 1
    assert ranked[0].exact_reference_answer_match is True
    assert ranked[0].equivalent_evidence is True


def test_exact_reference_duplicate_requires_scenario_compatibility() -> None:
    rows = [
        {
            "qa_id": "qa_wrong_scenario",
            "source_row_number": 2,
            "question": "كيف أستخدم بخاخ التربوهيلر؟",
            "answer": "ينصح بمراجعة الطبيب للتأكد من طريقة الاستخدام.",
            "category": "أمراض الجهاز التنفسي",
            "answer_fts_rank": 1,
        }
    ]

    ranked = rank_oracle_candidates(
        rows,
        query="كيف أستخدم قرص الديسك هيلر؟",
        reference_answer="ينصح بمراجعة الطبيب للتأكد من طريقة الاستخدام.",
        primary_intent="medication_safety",
        query_medical_phrases=["قرص الديسك هيلر"],
        current_retrieval_by_qa={},
        current_retrieval_content=set(),
        model=StubModel(),
        top_k=5,
    )

    assert len(ranked) == 1
    assert ranked[0].exact_reference_answer_match is True
    assert ranked[0].equivalent_evidence is False


def test_failure_taxonomy_separates_retrieval_and_step11() -> None:
    missed = diagnose_failure(
        [candidate(equivalent=True, retrieved=False)]
    )
    filtered = diagnose_failure(
        [candidate(equivalent=True, retrieved=True)]
    )

    assert missed.failure_class == RETRIEVER_MISS
    assert filtered.failure_class == STEP10_11_REJECTION


def test_borderline_and_empty_oracles_are_not_forced_positive() -> None:
    borderline = diagnose_failure(
        [
            candidate(
                equivalent=False,
                retrieved=False,
                borderline=True,
            )
        ]
    )
    empty = diagnose_failure([])

    assert borderline.failure_class == BROAD_OR_MISMATCHED
    assert borderline.requires_manual_review is True
    assert empty.failure_class == NO_EQUIVALENT_EVIDENCE
    assert empty.requires_manual_review is True
