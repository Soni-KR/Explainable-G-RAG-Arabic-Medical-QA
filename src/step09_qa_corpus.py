from __future__ import annotations

"""Held-out-safe AHD QA corpus indexing and semantic reranking.

The medical graph remains frozen. This module adds a separate retrieval corpus
so Step 9 can find source answers even when no validated graph edge exists. The
index builder excludes the complete eval_test split by normalized question.
"""

import csv
import hashlib
import json
import re
import sqlite3
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from src.config import AppConfig
from src.models import VectorSearchResult
from src.step08_normalize_query import normalize_query


TOKEN_RE = re.compile(r"[\w\u0600-\u06ff]+", re.UNICODE)
QUERY_STOPWORDS = {
    "ما", "ماذا", "هل", "كيف", "لماذا", "من", "في", "على", "عن", "الى",
    "إلى", "او", "أو", "هو", "هي", "هذا", "هذه", "انا", "اني", "عندي",
    "لدي", "اريد", "اعرف", "السلام", "عليكم", "دكتور", "طبيب",
}


@dataclass(frozen=True)
class QACorpusBuildSummary:
    source_rows: int
    indexed_rows: int
    heldout_rows: int
    duplicate_rows: int
    invalid_rows: int
    index_path: str
    corpus_version: str


def normalized_text(text: str) -> str:
    return normalize_query(text or "").normalized_query


def content_hash(question_norm: str, answer_norm: str, category: str) -> str:
    payload = "\n".join((question_norm, answer_norm, normalized_text(category)))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def load_holdout_questions(preprocessed_path: Path) -> set[str]:
    """Load every eval_test question, not only the 100-question evaluation sample."""
    with preprocessed_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"split", "question"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError(f"Holdout source is missing columns: {sorted(required)}")
        return {
            normalized_text(row.get("question") or "")
            for row in reader
            if row.get("split") == "eval_test" and normalized_text(row.get("question") or "")
        }


def _batched(values: Iterable[tuple[Any, ...]], size: int) -> Iterable[list[tuple[Any, ...]]]:
    batch: list[tuple[Any, ...]] = []
    for value in values:
        batch.append(value)
        if len(batch) >= size:
            yield batch
            batch = []
    if batch:
        yield batch


def build_qa_corpus_index(
    source_csv: Path,
    preprocessed_split_csv: Path,
    index_path: Path,
    corpus_version: str,
    *,
    batch_size: int = 2000,
    force: bool = False,
) -> QACorpusBuildSummary:
    """Build an atomic SQLite FTS5 index from AHD after removing eval_test QAs."""
    source_csv = source_csv.resolve()
    preprocessed_split_csv = preprocessed_split_csv.resolve()
    index_path = index_path.resolve()
    if index_path.exists() and not force:
        raise FileExistsError(f"QA corpus index already exists: {index_path}")

    holdout_questions = load_holdout_questions(preprocessed_split_csv)
    index_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = index_path.with_suffix(index_path.suffix + ".building")
    if temporary_path.exists():
        temporary_path.unlink()

    connection = sqlite3.connect(str(temporary_path))
    source_rows = indexed_rows = heldout_rows = duplicate_rows = invalid_rows = 0
    try:
        connection.executescript(
            """
PRAGMA journal_mode=OFF;
PRAGMA synchronous=OFF;
PRAGMA temp_store=MEMORY;
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
""".strip()
        )

        seen_hashes: set[str] = set()

        def records() -> Iterable[tuple[Any, ...]]:
            nonlocal source_rows, heldout_rows, duplicate_rows, invalid_rows
            with source_csv.open("r", encoding="utf-8-sig", newline="") as handle:
                reader = csv.DictReader(handle)
                required = {"Question", "Answer", "Category"}
                if not required.issubset(reader.fieldnames or []):
                    raise ValueError(f"AHD source is missing columns: {sorted(required)}")
                for source_row_number, row in enumerate(reader, start=2):
                    source_rows += 1
                    question = str(row.get("Question") or "").strip()
                    answer = str(row.get("Answer") or "").strip()
                    category = str(row.get("Category") or "").strip()
                    if not question or not answer:
                        invalid_rows += 1
                        continue
                    question_norm = normalized_text(question)
                    answer_norm = normalized_text(answer)
                    if not question_norm or not answer_norm:
                        invalid_rows += 1
                        continue
                    if question_norm in holdout_questions:
                        heldout_rows += 1
                        continue
                    digest = content_hash(question_norm, answer_norm, category)
                    if digest in seen_hashes:
                        duplicate_rows += 1
                        continue
                    seen_hashes.add(digest)
                    yield (
                        source_row_number,
                        f"ahdqa_{source_row_number:07d}",
                        source_row_number,
                        question,
                        answer,
                        category,
                        question_norm,
                        answer_norm,
                        digest,
                        corpus_version,
                    )

        insert_sql = """
INSERT OR IGNORE INTO qa_records (
    rowid, qa_id, source_row_number, question, answer, category,
    question_norm, answer_norm, content_hash, corpus_version
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""".strip()
        for batch in _batched(records(), max(1, batch_size)):
            connection.executemany(insert_sql, batch)
            connection.executemany(
                "INSERT INTO qa_fts(rowid, question_norm, answer_norm, category) "
                "VALUES (?, ?, ?, ?)",
                [(row[0], row[6], row[7], row[5]) for row in batch],
            )
            indexed_rows += len(batch)
            connection.commit()
        metadata = {
            "corpus_version": corpus_version,
            "source_csv": source_csv.name,
            "split_source": preprocessed_split_csv.name,
            "source_rows": source_rows,
            "indexed_rows": indexed_rows,
            "heldout_rows": heldout_rows,
            "heldout_unique_questions": len(holdout_questions),
            "duplicate_rows": duplicate_rows,
            "invalid_rows": invalid_rows,
            "holdout_policy": "exclude all normalized eval_test questions",
        }
        connection.executemany(
            "INSERT INTO corpus_metadata(key, value) VALUES (?, ?)",
            [(key, json.dumps(value, ensure_ascii=False)) for key, value in metadata.items()],
        )
        connection.commit()
    except Exception:
        connection.close()
        if temporary_path.exists():
            temporary_path.unlink()
        raise
    else:
        connection.close()

    if index_path.exists():
        index_path.unlink()
    temporary_path.replace(index_path)
    return QACorpusBuildSummary(
        source_rows=source_rows,
        indexed_rows=indexed_rows,
        heldout_rows=heldout_rows,
        duplicate_rows=duplicate_rows,
        invalid_rows=invalid_rows,
        index_path=str(index_path),
        corpus_version=corpus_version,
    )


def read_corpus_metadata(index_path: Path) -> dict[str, Any]:
    if not index_path.exists():
        return {}
    connection = sqlite3.connect(str(index_path))
    try:
        rows = connection.execute("SELECT key, value FROM corpus_metadata").fetchall()
    finally:
        connection.close()
    metadata: dict[str, Any] = {}
    for key, value in rows:
        try:
            metadata[str(key)] = json.loads(value)
        except json.JSONDecodeError:
            metadata[str(key)] = value
    return metadata


def fts_terms(
    query: str,
    limit: int = 24,
    *,
    include_legacy_forms: bool = False,
) -> list[str]:
    normalized = normalized_text(query)
    terms: list[str] = []
    for token in TOKEN_RE.findall(normalized):
        if len(token) < 2 or token in QUERY_STOPWORDS or token in terms:
            continue
        terms.append(token)
        if len(terms) >= limit:
            break
    if not terms:
        terms = [token for token in TOKEN_RE.findall(normalized) if len(token) >= 2][:limit]
    if include_legacy_forms:
        # The existing frozen FTS index contains a few Arabic presentation-form
        # glyphs produced before NFKC normalization was added. Query both forms
        # until that index is deliberately rebuilt under a new corpus version.
        legacy_terms: list[str] = []
        for token in TOKEN_RE.findall(query):
            if (
                len(token) >= 2
                and unicodedata.normalize("NFKC", token) != token
                and token not in terms
                and token not in legacy_terms
            ):
                legacy_terms.append(token)
                if len(legacy_terms) >= limit:
                    break
        terms.extend(legacy_terms)
    return terms


def lexical_relevance(query: str, question: str, position: int) -> float:
    query_tokens = set(fts_terms(query))
    question_tokens = set(TOKEN_RE.findall(normalized_text(question)))
    if not query_tokens or not question_tokens:
        return 0.0
    overlap = len(query_tokens & question_tokens)
    recall = overlap / len(query_tokens)
    precision = overlap / len(question_tokens)
    token_f1 = 0.0 if not overlap else 2 * precision * recall / (precision + recall)
    rank_prior = 1.0 / (1.0 + 0.08 * max(0, position - 1))
    return max(0.0, min(1.0, 0.45 + 0.30 * recall + 0.15 * token_f1 + 0.10 * rank_prior))


def lexical_candidates(index_path: Path, query: str, limit: int) -> list[dict[str, Any]]:
    terms = fts_terms(query, include_legacy_forms=True)
    if not terms or not index_path.exists():
        return []
    match_query = " OR ".join(f'"{term.replace(chr(34), chr(34) * 2)}"' for term in terms)
    connection = sqlite3.connect(str(index_path))
    try:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
SELECT q.qa_id, q.source_row_number, q.question, q.answer, q.category,
       bm25(qa_fts, 3.0, 1.0, 0.3) AS lexical_rank
FROM qa_fts
JOIN qa_records AS q ON q.rowid = qa_fts.rowid
WHERE qa_fts MATCH ?
ORDER BY lexical_rank
LIMIT ?
""".strip(),
            (match_query, max(1, limit)),
        ).fetchall()
    finally:
        connection.close()
    return [dict(row) for row in rows]


def search_qa_corpus(
    original_query: str,
    reformulated_query: str,
    query_embedding: list[float],
    model: Any,
    config: AppConfig,
    *,
    top_k: int | None = None,
    semantic_rerank: bool | None = None,
    candidate_k: int | None = None,
) -> list[VectorSearchResult]:
    """Shortlist with FTS5, then rerank locally with the configured E5 model."""
    corpus = config.qa_corpus
    index_path = Path(corpus.index_path)
    if not corpus.enabled or not index_path.exists():
        return []
    metadata = read_corpus_metadata(index_path)
    if metadata.get("corpus_version") != corpus.corpus_version:
        raise RuntimeError(
            "QA corpus version mismatch: "
            f"configured={corpus.corpus_version}, indexed={metadata.get('corpus_version')}"
        )
    lexical_query = " ".join(dict.fromkeys((original_query, reformulated_query)))
    use_semantic_rerank = (
        corpus.semantic_rerank_enabled
        if semantic_rerank is None
        else bool(semantic_rerank)
    )
    candidates = lexical_candidates(
        index_path,
        lexical_query,
        max(1, candidate_k or corpus.lexical_candidate_k),
    )
    if not candidates:
        return []

    scored: list[tuple[float, int, dict[str, Any]]] = []
    if use_semantic_rerank:
        passages = [
            "passage: " + " ".join((row["question"], row["answer"], row["category"])).strip()
            for row in candidates
        ]
        vectors = model.encode(passages, normalize_embeddings=True, show_progress_bar=False)
        for index, (row, vector) in enumerate(zip(candidates, vectors, strict=True), start=1):
            similarity = float(
                sum(float(a) * float(b) for a, b in zip(query_embedding, vector, strict=True))
            )
            scored.append((max(0.0, min(1.0, similarity)), index, row))
    else:
        for index, row in enumerate(candidates, start=1):
            scored.append((lexical_relevance(lexical_query, str(row["question"]), index), index, row))

    result_limit = max(1, top_k or corpus.semantic_top_k)
    results: list[VectorSearchResult] = []
    for score, lexical_position, row in sorted(scored, key=lambda item: item[0], reverse=True)[:result_limit]:
        qa_id = str(row["qa_id"])
        channel = "fts_e5_qa" if use_semantic_rerank else "fts_qa"
        lexical_score = lexical_relevance(lexical_query, str(row["question"]), lexical_position)
        results.append(
            VectorSearchResult(
                result_id=qa_id,
                document_type="QARecord",
                score=score,
                qa_id=qa_id,
                title=str(row["question"]),
                text=f"{row['question']}\n{row['answer']}",
                metadata={
                    "question": str(row["question"]),
                    "answer": str(row["answer"]),
                    "category": str(row["category"]),
                    "source_row_number": int(row["source_row_number"]),
                    "source_quality": "ahd_heldout_safe_corpus",
                    "retrieval_channel": channel,
                    "vector_similarity": score if use_semantic_rerank else 0.0,
                    "lexical_score": lexical_score,
                    "lexical_position": lexical_position,
                    "lexical_rank": float(row["lexical_rank"]),
                    "corpus_version": corpus.corpus_version,
                },
            )
        )
    return results
