from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from scripts.evaluate_dual_qa_retrieval import screen_merged_evidence
from src.config import AppConfig, EmbeddingConfig, QACorpusConfig
from src.models import RetrievedEvidence
from src.step09f_clinical_scenario import clinical_scenario_compatibility
from src.step09g_dual_qa_retrieval import (
    ANSWER_ONLY,
    DUAL_NO_SCENARIO,
    DUAL_WITH_SCENARIO,
    QUESTION_ONLY,
    rank_prepared_dual_results,
    search_dual_qa_corpus,
)


class StubEmbeddingModel:
    """Return deterministic unit vectors without loading a real model."""

    def encode(self, texts, **_kwargs):
        vectors = []
        for text in texts:
            normalized = str(text)
            if "الربو" in normalized or "ربو" in normalized:
                vectors.append([1.0, 0.0, 0.0])
            elif "الحساسية" in normalized or "حساسية" in normalized:
                vectors.append([0.0, 1.0, 0.0])
            else:
                vectors.append([0.0, 0.0, 1.0])
        return vectors


def create_test_index(path: Path) -> None:
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
            "qa_exact",
            1,
            "ما علاج الربو لطفل؟",
            "يعالج ربو الطفل تحت إشراف الطبيب.",
            "أمراض الصدر",
            "ما علاج الربو لطفل?",
            "يعالج ربو الطفل تحت اشراف الطبيب.",
            "hash-1",
            "test_v1",
        ),
        (
            2,
            "qa_child",
            2,
            "ما علاج الربو عند طفل عمره ثلاث سنوات؟",
            "علاج الربو للطفل يحدده الطبيب بعد الفحص.",
            "أمراض الأطفال",
            "ما علاج الربو عند طفل عمره ثلاث سنوات?",
            "علاج الربو للطفل يحدده الطبيب بعد الفحص.",
            "hash-2",
            "test_v1",
        ),
        (
            3,
            "qa_adult",
            3,
            "ما علاج الربو لرجل بالغ عمره أربعون سنة؟",
            "علاج الربو للبالغ يحدده الطبيب.",
            "أمراض الصدر",
            "ما علاج الربو لرجل بالغ عمره اربعون سنه?",
            "علاج الربو للبالغ يحدده الطبيب.",
            "hash-3",
            "test_v1",
        ),
        (
            4,
            "qa_answer_only",
            4,
            "ما أسباب الحساسية؟",
            "قد تستخدم موسعات الشعب في علاج الربو.",
            "الحساسية",
            "ما اسباب الحساسيه?",
            "قد تستخدم موسعات الشعب في علاج الربو.",
            "hash-4",
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


def test_scenario_explicit_conflicts_are_hard() -> None:
    age = clinical_scenario_compatibility(
        "طفلي عمره ثلاث سنوات لديه ربو",
        "رجل بالغ عمره أربعون سنة لديه ربو",
        primary_intent="treatment_request",
        query_medical_phrases=["ربو"],
    )
    pregnancy = clinical_scenario_compatibility(
        "أنا حامل وأعاني من الغثيان",
        "لست حامل وأعاني من الغثيان",
        query_medical_phrases=["غثيان"],
    )
    procedure = clinical_scenario_compatibility(
        "أشعر بألم بعد العملية",
        "أشعر بألم قبل العملية",
        query_medical_phrases=["ألم"],
    )

    assert age.hard_conflict is True
    assert "age_group_conflict" in age.conflicts
    assert pregnancy.hard_conflict is True
    assert "pregnancy_conflict" in pregnancy.conflicts
    assert procedure.hard_conflict is True
    assert "procedure_phase_conflict" in procedure.conflicts


def test_duration_mismatch_is_soft() -> None:
    result = clinical_scenario_compatibility(
        "أعاني من صداع منذ يومين",
        "أعاني من صداع مزمن منذ سنوات",
        query_medical_phrases=["صداع"],
    )

    assert result.hard_conflict is False
    assert "duration_mismatch" in result.conflicts


def test_single_channels_are_independent_and_exact_query_is_excluded(
    tmp_path: Path,
) -> None:
    index_path = tmp_path / "qa.sqlite"
    create_test_index(index_path)
    config = AppConfig(
        embeddings=EmbeddingConfig(dimension=3),
        qa_corpus=QACorpusConfig(
            index_path=str(index_path),
            corpus_version="test_v1",
        ),
    )
    common = {
        "original_query": "ما علاج الربو لطفل؟",
        "reformulated_query": "ما علاج الربو لطفل؟",
        "primary_intent": "treatment_request",
        "query_medical_phrases": ["ربو"],
        "query_embedding": [1.0, 0.0, 0.0],
        "model": StubEmbeddingModel(),
        "config": config,
        "top_k": 10,
        "candidate_k_per_channel": 20,
    }

    question_results, question_audit = search_dual_qa_corpus(
        mode=QUESTION_ONLY,
        **common,
    )
    answer_results, answer_audit = search_dual_qa_corpus(
        mode=ANSWER_ONLY,
        **common,
    )

    question_ids = {item.qa_id for item in question_results}
    answer_ids = {item.qa_id for item in answer_results}
    assert "qa_exact" not in question_ids | answer_ids
    assert "qa_answer_only" not in question_ids
    assert "qa_answer_only" in answer_ids
    assert all(
        int(item.metadata["question_position"]) > 0
        for item in question_results
    )
    assert all(
        int(item.metadata["answer_position"]) > 0
        for item in answer_results
    )
    assert question_audit.exact_questions_excluded == 1
    assert answer_audit.exact_questions_excluded == 1


def test_scenario_mode_rejects_adult_candidate_for_child_query(
    tmp_path: Path,
) -> None:
    index_path = tmp_path / "qa.sqlite"
    create_test_index(index_path)
    config = AppConfig(
        embeddings=EmbeddingConfig(dimension=3),
        qa_corpus=QACorpusConfig(
            index_path=str(index_path),
            corpus_version="test_v1",
        ),
    )

    results, audit = search_dual_qa_corpus(
        original_query="ما علاج الربو لطفل؟",
        reformulated_query="ما علاج الربو لطفل؟",
        primary_intent="treatment_request",
        query_medical_phrases=["ربو"],
        query_embedding=[1.0, 0.0, 0.0],
        model=StubEmbeddingModel(),
        config=config,
        mode=DUAL_WITH_SCENARIO,
        top_k=10,
        candidate_k_per_channel=20,
    )

    ids = {item.qa_id for item in results}
    assert "qa_child" in ids
    assert "qa_adult" not in ids
    assert audit.hard_conflicts_rejected >= 1
    assert audit.rejected_conflicts["age_group_conflict"] >= 1


def test_prepared_union_can_derive_all_modes_without_new_inference(
    tmp_path: Path,
) -> None:
    index_path = tmp_path / "qa.sqlite"
    create_test_index(index_path)
    config = AppConfig(
        embeddings=EmbeddingConfig(dimension=3),
        qa_corpus=QACorpusConfig(
            index_path=str(index_path),
            corpus_version="test_v1",
        ),
    )
    prepared, prepared_audit = search_dual_qa_corpus(
        original_query="ما علاج الربو لطفل؟",
        reformulated_query="ما علاج الربو لطفل؟",
        primary_intent="treatment_request",
        query_medical_phrases=["ربو"],
        query_embedding=[1.0, 0.0, 0.0],
        model=StubEmbeddingModel(),
        config=config,
        mode=DUAL_NO_SCENARIO,
        top_k=40,
        candidate_k_per_channel=20,
    )

    question, _ = rank_prepared_dual_results(
        prepared,
        prepared_audit,
        mode=QUESTION_ONLY,
        top_k=10,
    )
    answer, _ = rank_prepared_dual_results(
        prepared,
        prepared_audit,
        mode=ANSWER_ONLY,
        top_k=10,
    )
    scenario, scenario_audit = rank_prepared_dual_results(
        prepared,
        prepared_audit,
        mode=DUAL_WITH_SCENARIO,
        top_k=10,
    )

    assert "qa_answer_only" not in {item.qa_id for item in question}
    assert "qa_answer_only" in {item.qa_id for item in answer}
    assert "qa_adult" not in {item.qa_id for item in scenario}
    assert scenario_audit.hard_conflicts_rejected >= 1


def test_scenario_screen_also_filters_existing_evidence() -> None:
    evidence = [
        RetrievedEvidence(
            evidence_id="qa::adult",
            source_id="adult",
            qa_id="adult",
            text="علاج الربو للبالغ.",
            question="ما علاج الربو لرجل بالغ؟",
            answer="علاج الربو للبالغ.",
            source_quality="ahd_heldout_safe_corpus",
        ),
        RetrievedEvidence(
            evidence_id="qa::child",
            source_id="child",
            qa_id="child",
            text="علاج الربو للطفل.",
            question="ما علاج الربو لطفل؟",
            answer="علاج الربو للطفل.",
            source_quality="ahd_heldout_safe_corpus",
        ),
    ]

    screened, hard_rejections, exact_rejections = (
        screen_merged_evidence(
            evidence,
            query="طفلي لديه ربو، ما العلاج؟",
            primary_intent="treatment_request",
            query_medical_phrases=["ربو"],
            enabled=True,
        )
    )

    assert [item.qa_id for item in screened] == ["child"]
    assert hard_rejections == 1
    assert exact_rejections == 0
