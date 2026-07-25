from __future__ import annotations

"""Step 6: deterministic, resumable embeddings for the frozen final graph.

This module intentionally performs only embedding generation and Neo4j vector-
index construction. It does not implement vector retrieval, graph traversal, or
hybrid ranking. Comments are deliberately detailed so a collaborator can audit
each operation without reverse-engineering the code.

Execution flow:
1. Load final-only configuration and connect to Neo4j on port 7688.
2. Read source fields plus existing embedding metadata for all three node types.
3. Build deterministic E5 ``passage:`` documents and SHA-256 text hashes.
4. Skip nodes whose vector and all metadata still match the current contract.
5. Encode stale nodes in small batches and write each batch immediately.
6. Create three cosine vector indexes and wait until they are populated.
7. Verify every vector/metadata field and run one minimal index query.
"""

# Parse command-line flags such as --dry-run, --execute, and --batch-size.
import argparse
# Produce stable SHA-256 hashes used to detect unchanged embedding passages.
import hashlib
# Control noisy Neo4j notification logging without hiding our own errors.
import logging
# Calculate the number of inference batches with ceiling division.
import math
# Validate dynamic Neo4j index names before inserting them into Cypher.
import re
# Adjust Python import paths and configure UTF-8 terminal output.
import sys
# Measure total embedding execution time with a monotonic clock.
import time
# Define an immutable structured record for each embedding document.
from dataclasses import dataclass
# Reuse the loaded E5 model when a failed query triggers a second-pass fallback.
from functools import lru_cache
# Resolve project-relative source paths portably.
from pathlib import Path
# Type dynamic Neo4j rows and generic helper inputs.
from typing import Any

# Direct script execution sets __package__ to an empty value.
if __package__ in {None, ""}:
    # Add the repository root so ``src.*`` imports work from any current directory.
    sys.path.append(str(Path(__file__).resolve().parents[1]))

# The repository root is one directory above this ``src`` file.
ROOT = Path(__file__).resolve().parents[1]
# AppConfig supplies final Neo4j, model, dimension, and index-name settings.
from src.config import AppConfig, load_final_config
# Neo4jRepository owns the authenticated driver and read transaction helper.
from src.neo4j_repository import Neo4jRepository


# These names equal the Neo4j labels and the stored embedding_document_type values.
DOCUMENT_TYPES = ("MedicalEntity", "EvidenceMention", "QARecord")
# Frozen graph counts are safety gates: execution stops if final_v1 unexpectedly changes.
EXPECTED_GRAPH_COUNTS = {
    # One passage is built for every canonical medical entity node.
    "MedicalEntity": 2175,
    # One passage is built for every evidence mention linked to an entity.
    "EvidenceMention": 5767,
    # One passage is built for every full or evidence-reconstructed QA record.
    "QARecord": 2549,
}
# Thirty-two texts per inference batch balances CPU memory and throughput.
DEFAULT_BATCH_SIZE = 32
# At most 200 encoded rows are sent in one Neo4j UNWIND write transaction.
DEFAULT_WRITE_BATCH_SIZE = 200
# Dry runs expose only two truncated examples per type to keep logs concise.
SAMPLE_COUNT = 2


# Freeze records so code cannot accidentally mutate a passage after hashing it.
@dataclass(frozen=True)
class EmbeddingDocument:
    """One deterministic passage and its current/stale decision."""

    # Stable graph ID used to MATCH the target node during writes.
    source_id: str
    # Neo4j label and embedding_document_type metadata value.
    document_type: str
    # Exact E5 passage that is encoded; always starts with ``passage:``.
    text: str
    # SHA-256 of ``text`` used for idempotent resume checks.
    text_hash: str
    # True only when vector content or any compatibility metadata is stale/missing.
    needs_embedding: bool


@lru_cache(maxsize=2)
def load_model(model_name: str, expected_dimension: int):
    """Load E5 on CUDA when available, otherwise CPU, and validate dimension."""

    # Keep heavyweight imports lazy so structural dry runs start quickly.
    try:
        # Torch reports CUDA availability and runs model inference.
        import torch
        # SentenceTransformer handles tokenizer/model loading and normalized encoding.
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        # Explain exactly how to restore the project virtual environment.
        raise RuntimeError(
            "The embedding runtime is unavailable. Activate .venv and install requirements.txt."
        ) from exc

    # CUDA is optional; CPU is the safe automatic fallback.
    device = "cuda" if torch.cuda.is_available() else "cpu"
    # Load the configured Hugging Face model directly on the selected device.
    model = SentenceTransformer(model_name, device=device)
    # Ask the model itself for its output size instead of trusting configuration alone.
    dimension = int(model.get_sentence_embedding_dimension())
    # A mismatched dimension would make existing Neo4j index definitions unsafe.
    if dimension != expected_dimension:
        raise RuntimeError(
            f"Embedding dimension mismatch: configured={expected_dimension}, model={dimension}"
        )
    # Return all runtime facts needed by execution and its final summary.
    return model, device, dimension


def clean_aliases(canonical_name: str, aliases: Any) -> list[str]:
    """Trim aliases, preserve order, and remove canonical/duplicate values."""

    # Neo4j should store aliases as a list; malformed storage becomes an empty list.
    values = aliases if isinstance(aliases, list) else []
    # Seed the seen set with the canonical name so it is not repeated as an alias.
    seen = {str(canonical_name or "").strip()}
    # Accumulate unique aliases in their original deterministic order.
    cleaned = []
    # Inspect every source alias once.
    for value in values:
        # Convert null-like values safely and remove surrounding whitespace.
        alias = str(value or "").strip()
        # Keep only non-empty aliases that were not already emitted.
        if alias and alias not in seen:
            # Record the alias before appending to prevent later duplicates.
            seen.add(alias)
            # Preserve the original Arabic/Latin spelling for semantic encoding.
            cleaned.append(alias)
    # Return a predictable plain list suitable for string joining.
    return cleaned


def passage(*parts: str) -> str:
    """Join non-empty source fields and apply the required E5 passage prefix."""

    # Empty optional fields are discarded; all retained fields are whitespace-trimmed.
    body = " ".join(part.strip() for part in parts if part and part.strip())
    # E5 expects indexed documents to use ``passage:`` rather than ``query:``.
    return f"passage: {body}".strip()


def document_hash(text: str) -> str:
    """Return a stable UTF-8 SHA-256 digest for an exact passage."""

    # UTF-8 preserves Arabic text deterministically across machines.
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def is_current_embedding(
    row: dict[str, Any],
    text_hash: str,
    document_type: str,
    config: AppConfig,
) -> bool:
    """Return True only when vector content and every compatibility field match."""

    # ``all`` makes every condition mandatory; one stale field triggers re-embedding.
    return all(
        (
            # A node without a vector can never be current.
            bool(row.get("has_embedding")),
            # Validate the actual stored list length, not metadata alone.
            int(row.get("actual_dimension") or 0) == config.embeddings.dimension,
            # Prevent mixing vectors produced by different model checkpoints.
            row.get("embedding_model") == config.embeddings.model_name,
            # Validate the declared embedding dimension metadata.
            int(row.get("embedding_dimension") or 0) == config.embeddings.dimension,
            # Prevent reuse across trial_v1/final_v1 boundaries.
            row.get("embedding_graph_version") == config.graph_version,
            # Ensure each node was embedded with the correct passage contract.
            row.get("embedding_document_type") == document_type,
            # Re-embed whenever any source text changes.
            row.get("embedding_text_hash") == text_hash,
        )
    )


def metadata_projection(alias: str) -> str:
    """Build the shared read-only Cypher projection used for stale checks."""

    # The alias comes only from fixed internal calls (e, m, q), never user input.
    return f"""
       // Whether a vector property currently exists on this node.
       {alias}.embedding IS NOT NULL AS has_embedding,
       // Actual vector length detects truncated or incompatible stored lists.
       CASE WHEN {alias}.embedding IS NULL THEN 0 ELSE size({alias}.embedding) END AS actual_dimension,
       // Model checkpoint that generated the existing vector.
       {alias}.embedding_model AS embedding_model,
       // Declared vector dimension stored with the node.
       {alias}.embedding_dimension AS embedding_dimension,
       // Graph version boundary associated with the vector.
       {alias}.embedding_graph_version AS embedding_graph_version,
       // Passage schema used for this node label.
       {alias}.embedding_document_type AS embedding_document_type,
       // Hash of the exact text used to generate the vector.
       {alias}.embedding_text_hash AS embedding_text_hash
""".strip()


def read_embedding_documents(
    repository: Neo4jRepository,
    config: AppConfig,
) -> dict[str, list[EmbeddingDocument]]:
    """Read final graph fields and build all deterministic embedding documents."""

    # Use the configured final graph version in every Cypher MATCH.
    version = config.graph_version
    # Read MedicalEntity source fields plus existing embedding compatibility metadata.
    entities = repository._execute_read(
        f"""
// Restrict entity passages to the isolated final graph.
MATCH (e:MedicalEntity {{graph_version: $version}})
// Return only supported source fields; no descriptions are invented.
RETURN e.entity_id AS source_id,
       e.canonical_name AS canonical_name,
       e.entity_type AS entity_type,
       coalesce(e.aliases, []) AS aliases,
       {metadata_projection('e')}
// Stable ordering keeps hashing and batching reproducible.
ORDER BY e.entity_id
""".strip(),
        # Parameterization prevents accidental string interpolation in filters.
        {"version": version},
    )
    # Read mention evidence together with its explicitly linked entity context.
    mentions = repository._execute_read(
        f"""
// MENTIONED_IN provides the linked canonical entity without semantic inference.
MATCH (e:MedicalEntity {{graph_version: $version}})-[:MENTIONED_IN]->
      (m:EvidenceMention {{graph_version: $version}})
// Include mention surface, evidence, field, and linked entity name/type only.
RETURN m.mention_id AS source_id,
       m.surface_form AS surface_form,
       m.evidence AS evidence,
       m.field AS field,
       e.canonical_name AS entity_name,
       e.entity_type AS entity_type,
       {metadata_projection('m')}
// Stable ordering gives deterministic batches and logs.
ORDER BY m.mention_id
""".strip(),
        {"version": version},
    )
    # Read QA text and preserve the source_quality provenance marker.
    qa_records = repository._execute_read(
        f"""
// Restrict QA passages to final_v1 records.
MATCH (q:QARecord {{graph_version: $version}})
// Use only stored question, answer, category, and provenance fields.
RETURN q.qa_id AS source_id,
       q.question AS question,
       q.answer AS answer,
       q.category AS category,
       q.source_quality AS source_quality,
       {metadata_projection('q')}
// Stable QA IDs define deterministic processing order.
ORDER BY q.qa_id
""".strip(),
        {"version": version},
    )

    # Pre-create one output list per supported Neo4j node label.
    documents: dict[str, list[EmbeddingDocument]] = {key: [] for key in DOCUMENT_TYPES}

    # Convert each entity row into an E5 passage without unsupported descriptions.
    for row in entities:
        # Remove duplicate/canonical aliases before constructing text.
        aliases = clean_aliases(row.get("canonical_name") or "", row.get("aliases"))
        # Fixed field order makes passage text and hashes deterministic.
        text = passage(
            f"الاسم الطبي: {row.get('canonical_name') or ''}.",
            f"النوع: {row.get('entity_type') or ''}.",
            f"المرادفات: {', '.join(aliases)}." if aliases else "",
        )
        # Hash exactly the text that will be passed to E5.
        text_hash = document_hash(text)
        # Store source ID, contract type, text, hash, and current/stale decision.
        documents["MedicalEntity"].append(
            EmbeddingDocument(
                source_id=str(row["source_id"]),
                document_type="MedicalEntity",
                text=text,
                text_hash=text_hash,
                needs_embedding=not is_current_embedding(row, text_hash, "MedicalEntity", config),
            )
        )

    # Convert every evidence node using only explicit mention/entity fields.
    for row in mentions:
        # Mention field is retained so question and answer evidence stay distinguishable.
        text = passage(
            f"الصيغة المذكورة: {row.get('surface_form') or ''}.",
            f"الدليل: {row.get('evidence') or ''}.",
            f"الحقل: {row.get('field') or ''}.",
            f"الكيان الطبي: {row.get('entity_name') or ''}.",
            f"النوع: {row.get('entity_type') or ''}.",
        )
        # Hash the completed evidence passage before checking existing metadata.
        text_hash = document_hash(text)
        # Append an immutable work item for this mention.
        documents["EvidenceMention"].append(
            EmbeddingDocument(
                source_id=str(row["source_id"]),
                document_type="EvidenceMention",
                text=text,
                text_hash=text_hash,
                needs_embedding=not is_current_embedding(row, text_hash, "EvidenceMention", config),
            )
        )

    # Convert each QARecord and explicitly expose its provenance quality.
    for row in qa_records:
        # Normalize absent provenance to an empty string for a deterministic branch.
        source_quality = str(row.get("source_quality") or "")
        # Evidence-reconstructed records get a distinct marker for later down-weighting.
        provenance = (
            "المصدر: سجل معاد البناء من دليل الاستخراج."
            if source_quality == "mention_evidence"
            else "المصدر: سجل سؤال وجواب من البيانات المعالجة."
        )
        # Build the QA passage in question/answer/category/provenance order.
        text = passage(
            f"السؤال: {row.get('question') or ''}.",
            f"الإجابة: {row.get('answer') or ''}.",
            f"التصنيف: {row.get('category') or ''}." if row.get("category") else "",
            provenance,
        )
        # Hash the exact QA passage used by E5.
        text_hash = document_hash(text)
        # Append the QA work item with the same compatibility rules as other labels.
        documents["QARecord"].append(
            EmbeddingDocument(
                source_id=str(row["source_id"]),
                document_type="QARecord",
                text=text,
                text_hash=text_hash,
                needs_embedding=not is_current_embedding(row, text_hash, "QARecord", config),
            )
        )
    # Return all 10,491 documents grouped by their target Neo4j label.
    return documents


def execute_write(repository: Neo4jRepository, query: str, parameters: dict[str, Any]) -> None:
    """Run one explicit Neo4j write transaction and consume its result."""

    # Open a short-lived session against the configured final database.
    with repository._driver.session(database=repository.config.neo4j.database) as session:
        # execute_write retries transient failures according to Neo4j driver policy.
        session.execute_write(lambda tx: tx.run(query, **parameters).consume())


def chunked(rows: list[Any], size: int):
    """Yield consecutive list slices so inference and writes remain bounded."""

    # Step over the list in fixed-size offsets.
    for start in range(0, len(rows), size):
        # Yield one independent batch; the final slice may be smaller.
        yield rows[start : start + size]


def embedding_write_query(document_type: str) -> str:
    """Return label-specific Cypher that updates embedding properties only."""

    # Medical entities are addressed by their frozen entity_id.
    if document_type == "MedicalEntity":
        match = "MATCH (n:MedicalEntity {entity_id: row.source_id, graph_version: $version})"
    # Evidence mentions are addressed by their frozen mention_id.
    elif document_type == "EvidenceMention":
        match = "MATCH (n:EvidenceMention {mention_id: row.source_id, graph_version: $version})"
    # QA records are addressed by their frozen qa_id.
    elif document_type == "QARecord":
        match = "MATCH (n:QARecord {qa_id: row.source_id, graph_version: $version})"
    # Reject programming errors instead of generating unsafe dynamic Cypher.
    else:
        raise ValueError(f"Unsupported document type: {document_type}")
    # The query never creates/deletes nodes or relationships; it only sets vector metadata.
    return f"""
// Expand the parameterized write batch into rows.
UNWIND $rows AS row
// Match an existing final_v1 node by its immutable ID.
{match}
// Store the normalized vector produced by multilingual-e5-base.
SET n.embedding = row.embedding,
    // Record the exact model checkpoint for compatibility checks.
    n.embedding_model = $model,
    // Record the expected vector length for validation and handoff.
    n.embedding_dimension = $dimension,
    // Bind this vector to final_v1 so trial data cannot be mixed in retrieval.
    n.embedding_graph_version = $version,
    // Record which deterministic passage schema generated the vector.
    n.embedding_document_type = $document_type,
    // Persist the passage hash used by resume/idempotency logic.
    n.embedding_text_hash = row.text_hash,
    // Timestamp only newly written/stale vectors; skipped nodes retain their timestamp.
    n.embedding_created_at = datetime()
""".strip()


def safe_index_name(value: str) -> str:
    """Allow only simple Neo4j identifiers in dynamic CREATE INDEX statements."""

    # Cypher cannot parameterize index names, so enforce a strict identifier grammar.
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", value):
        raise ValueError(f"Unsafe Neo4j index name: {value}")
    # The validated value is safe to interpolate into DDL.
    return value


def index_definitions(config: AppConfig) -> tuple[tuple[str, str], ...]:
    """Map each configured final vector-index name to its Neo4j node label."""

    # Keep this tuple ordered for deterministic dry-run and verification output.
    return (
        # Canonical medical entity vector index.
        (safe_index_name(config.embeddings.entity_vector_index_name), "MedicalEntity"),
        # Evidence mention vector index.
        (safe_index_name(config.embeddings.evidence_vector_index_name), "EvidenceMention"),
        # QA/source vector index.
        (safe_index_name(config.embeddings.qa_vector_index_name), "QARecord"),
    )


def create_vector_indexes(repository: Neo4jRepository, config: AppConfig) -> None:
    """Create the three idempotent 768-dimensional cosine indexes and await ONLINE."""

    # Build one index for each document type after all vectors are valid.
    for index_name, label in index_definitions(config):
        # Dimensions and similarity are fixed by the Step 6 handoff contract.
        query = f"""
// IF NOT EXISTS makes repeated successful executions harmless.
CREATE VECTOR INDEX {index_name} IF NOT EXISTS
// Each index covers the embedding property on exactly one node label.
FOR (n:{label}) ON (n.embedding)
OPTIONS {{indexConfig: {{
  // multilingual-e5-base emits 768 floating-point values.
  `vector.dimensions`: {config.embeddings.dimension},
  // Embeddings are unit-normalized and compared with cosine similarity.
  `vector.similarity_function`: 'cosine'
}}}}
""".strip()
        # Submit one DDL statement per index.
        execute_write(repository, query, {})
    # Block for at most five minutes until Neo4j finishes index population.
    execute_write(repository, "CALL db.awaitIndexes(300)", {})


def vector_index_states(repository: Neo4jRepository, config: AppConfig) -> list[dict[str, Any]]:
    """Return SHOW VECTOR INDEXES rows for only the three final indexes."""

    # Build the exact allowlist expected for final_v1.
    expected = {name for name, _ in index_definitions(config)}
    # Read state, population, target label/property, and effective index options.
    rows = repository._execute_read(
        "SHOW VECTOR INDEXES YIELD name, state, populationPercent, labelsOrTypes, properties, options "
        "RETURN name, state, populationPercent, labelsOrTypes, properties, options"
    )
    # Ignore unrelated vector indexes that may exist in the same Neo4j database.
    return [row for row in rows if row.get("name") in expected]


def validation_query(label: str) -> str:
    """Build aggregate validation Cypher for one supported node label."""

    # ``label`` comes exclusively from DOCUMENT_TYPES, never from user input.
    return f"""
// Validate only nodes belonging to the configured final graph.
MATCH (n:{label} {{graph_version: $version}})
// Total must equal the frozen count for this label.
RETURN count(n) AS total,
       // Missing means no embedding property was stored.
       count(CASE WHEN n.embedding IS NULL THEN 1 END) AS missing,
       // Empty catches a present but zero-length vector.
       count(CASE WHEN n.embedding IS NOT NULL AND size(n.embedding) = 0 THEN 1 END) AS empty,
       // Malformed catches any vector whose actual length is not 768.
       count(CASE WHEN n.embedding IS NOT NULL AND size(n.embedding) <> $dimension THEN 1 END) AS malformed,
       // These checks protect retrieval from mixed model metadata.
       count(CASE WHEN n.embedding_model <> $model THEN 1 END) AS wrong_model,
       count(CASE WHEN n.embedding_dimension <> $dimension THEN 1 END) AS wrong_dimension,
       count(CASE WHEN n.embedding_graph_version <> $version THEN 1 END) AS wrong_version,
       count(CASE WHEN n.embedding_document_type <> $document_type THEN 1 END) AS wrong_document_type,
       // Every vector must retain its deterministic source-text hash.
       count(CASE WHEN n.embedding_text_hash IS NULL OR n.embedding_text_hash = '' THEN 1 END) AS missing_hash,
       // Every generated/stale vector write must be timestamped.
       count(CASE WHEN n.embedding_created_at IS NULL THEN 1 END) AS missing_timestamp
""".strip()


def verify_embeddings(
    repository: Neo4jRepository,
    config: AppConfig,
) -> tuple[dict[str, dict[str, int]], list[dict[str, Any]], bool]:
    """Validate every vector/metadata field and all three index population states."""

    # Collect one aggregate validation row per node type.
    results = {}
    # Validate all supported embedding labels.
    for document_type in DOCUMENT_TYPES:
        # Execute the label-specific validation with final model metadata parameters.
        rows = repository._execute_read(
            validation_query(document_type),
            {
                "version": config.graph_version,
                "model": config.embeddings.model_name,
                "dimension": config.embeddings.dimension,
                "document_type": document_type,
            },
        )
        # Convert Neo4j integer values to plain Python ints for stable comparison/output.
        results[document_type] = {key: int(value) for key, value in rows[0].items()}

    # Inspect only the configured final vector indexes.
    indexes = vector_index_states(repository, config)
    # Vectors pass only when totals match and every error counter is zero.
    vectors_ok = all(
        row["total"] == EXPECTED_GRAPH_COUNTS[document_type]
        and all(row[key] == 0 for key in row if key != "total")
        for document_type, row in results.items()
    )
    # Indexes pass only when exactly three are ONLINE and fully populated.
    indexes_ok = len(indexes) == 3 and all(
        row.get("state") == "ONLINE" and float(row.get("populationPercent") or 0) == 100.0
        for row in indexes
    )
    # Return detailed evidence plus one combined status flag.
    return results, indexes, vectors_ok and indexes_ok


def minimal_vector_query_check(
    repository: Neo4jRepository,
    config: AppConfig,
    model,
) -> dict[str, Any]:
    """Run one non-production entity search solely to prove the index is callable."""

    # E5 requires the ``query:`` prefix for search queries (documents use ``passage:``).
    query_vector = model.encode(
        ["query: ما علاج الربو؟"],
        # Match the cosine index contract by unit-normalizing the query vector.
        normalize_embeddings=True,
        # Neo4j parameters require a serializable numeric sequence.
        convert_to_numpy=True,
        # This is one verification query, so no progress bar is useful.
        show_progress_bar=False,
    )[0]
    # Ask the final entity index for exactly one neighbor.
    rows = repository._execute_read(
        """
// This verifies index execution only; it is not the Step 9B retrieval module.
CALL db.index.vector.queryNodes($index_name, 1, $query_vector)
YIELD node, score
// Return identifiers and score, never the full stored/query vector.
RETURN node.entity_id AS source_id, node.canonical_name AS canonical_name, score
""".strip(),
        {
            # Use the configured final MedicalEntity index name.
            "index_name": config.embeddings.entity_vector_index_name,
            # Convert NumPy scalar values to JSON/Bolt-friendly Python floats.
            "query_vector": [float(value) for value in query_vector.tolist()],
        },
    )
    # An ONLINE but unusable index must fail Step 6 verification.
    if not rows:
        raise RuntimeError("Minimal vector index verification returned no result")
    # Return only the top row for concise execution reporting.
    return rows[0]


def sanitize_sample(text: str, limit: int = 180) -> str:
    """Collapse whitespace and truncate dry-run passage examples."""

    # Samples show source structure without flooding logs with long medical answers.
    return " ".join(text.split())[:limit]


def validate_dry_run_documents(
    documents: dict[str, list[EmbeddingDocument]],
    graph_counts: dict[str, int],
) -> None:
    """Stop before model loading/writes when graph counts or passage text are invalid."""

    # Compare every document type against the frozen final_v1 manifest counts.
    for document_type, expected in EXPECTED_GRAPH_COUNTS.items():
        # Count constructed passages.
        actual = len(documents[document_type])
        # Count source nodes read directly from Neo4j.
        graph_actual = graph_counts[document_type]
        # Any mismatch indicates graph drift or a broken document query.
        if actual != expected or graph_actual != expected:
            raise RuntimeError(
                f"Unexpected {document_type} count: graph={graph_actual}, documents={actual}, expected={expected}"
            )
        # E5 must never receive an empty passage.
        empty_ids = [doc.source_id for doc in documents[document_type] if not doc.text.strip()]
        # Fail with a small ID sample instead of silently writing meaningless vectors.
        if empty_ids:
            raise RuntimeError(f"Empty {document_type} passages: {empty_ids[:5]}")


def dry_run(batch_size: int, load_model_for_dimension: bool) -> int:
    """Validate final targeting, passages, counts, model dimension, and index plan."""

    # Load the isolated final configuration, not the trial/default fallback.
    config = load_final_config()
    # Refuse to proceed if environment overrides point at the trial server/version.
    if config.graph_version != "final_v1" or config.neo4j.uri != "bolt://localhost:7688":
        raise RuntimeError("Step 6 must target final_v1 at bolt://localhost:7688")

    # Open one read-only repository context for all dry-run Neo4j inspection.
    with Neo4jRepository(config=config) as repository:
        # Verify source graph label/relationship counts.
        graph_counts = repository.get_graph_counts()
        # Build passages and current/stale metadata decisions without writing.
        documents = read_embedding_documents(repository, config)
        # Inspect whether matching vector indexes already exist.
        indexes = vector_index_states(repository, config)
    # Stop on count drift or empty passages before optional model loading.
    validate_dry_run_documents(documents, graph_counts)

    # Structural inspection can skip expensive Torch/model initialization.
    device = "not_loaded"
    # Full Phase 3 dry-run loads the model to verify actual 768-dimensional output.
    if load_model_for_dimension:
        # The returned model is intentionally discarded because no encoding occurs here.
        _, device, _ = load_model(config.embeddings.model_name, config.embeddings.dimension)

    # Print concise configuration and passage validation evidence.
    print("Step 6 dry-run")
    print(f"graph_version: {config.graph_version}")
    print(f"neo4j_uri: {config.neo4j.uri}")
    print(f"embedding_model: {config.embeddings.model_name}")
    print(f"expected_dimension: {config.embeddings.dimension}")
    print(f"device: {device}")
    print(f"batch_size: {batch_size}")
    # Accumulate the expected grand total of 10,491 passages.
    total = 0
    # Report each label's total and stale/missing workload.
    for document_type in DOCUMENT_TYPES:
        # Select the deterministic document group for this label.
        docs = documents[document_type]
        # Count nodes that execution would actually encode.
        stale = sum(doc.needs_embedding for doc in docs)
        # Add this label to the grand total.
        total += len(docs)
        # Show count/resume status without exposing any vectors.
        print(f"documents_{document_type}: {len(docs)} (stale_or_missing={stale})")
        # Print only a small sanitized sample of source-derived passage text.
        for doc in docs[:SAMPLE_COUNT]:
            print(f"sample_{document_type}: {sanitize_sample(doc.text)}")
    # Confirm all three document groups sum correctly.
    print(f"documents_total: {total}")
    # Show exactly what index DDL execution intends to create.
    print("intended_indexes:")
    # Iterate over final-only index names and labels.
    for name, label in index_definitions(config):
        print(f"- {name}: label={label}, property=embedding, dimension=768, similarity=cosine")
    # Existing index count helps explain first-run versus resumed state.
    print(f"existing_matching_indexes: {len(indexes)}")
    # Explicitly prove this code path made no writes.
    print("writes_executed: 0")
    print("status: ok")
    # Zero is the conventional successful CLI exit code.
    return 0


def execute_indexing(batch_size: int, write_batch_size: int) -> int:
    """Embed only stale nodes, write batches immediately, index, and verify."""

    # Always load the dedicated final server/index configuration.
    config = load_final_config()
    # Hard-stop on any accidental trial targeting.
    if config.graph_version != "final_v1" or config.neo4j.uri != "bolt://localhost:7688":
        raise RuntimeError("Step 6 must target final_v1 at bolt://localhost:7688")

    # Start an elapsed-time measurement before loading graph/model resources.
    started = time.perf_counter()
    # Failed IDs stay in memory for concise reporting and safe retry on rerun.
    failed_ids: list[str] = []
    # Count vectors successfully generated and committed in this execution only.
    generated = 0

    # Keep the Neo4j driver open across reads, writes, index DDL, and verification.
    with Neo4jRepository(config=config) as repository:
        # Snapshot source graph counts before embedding.
        graph_counts = repository.get_graph_counts()
        # Build current passages and compare each against stored metadata/hash.
        documents = read_embedding_documents(repository, config)
        # Fail before model inference if final graph drift or empty text is detected.
        validate_dry_run_documents(documents, graph_counts)
        # Keep only missing/stale documents; current vectors never reach model.encode.
        stale_documents = {
            document_type: [doc for doc in documents[document_type] if doc.needs_embedding]
            for document_type in DOCUMENT_TYPES
        }
        # Report how many compatible vectors were reused unchanged.
        skipped = sum(
            len(documents[key]) - len(stale_documents[key]) for key in DOCUMENT_TYPES
        )

        # Load multilingual-e5-base on CUDA when available, otherwise CPU.
        model, device, dimension = load_model(
            config.embeddings.model_name,
            config.embeddings.dimension,
        )

        # Process labels independently so progress and failures stay attributable.
        for document_type in DOCUMENT_TYPES:
            # Select only stale work for this label.
            docs = stale_documents[document_type]
            # Calculate a human-readable number of inference batches.
            batches = math.ceil(len(docs) / batch_size) if docs else 0
            # Encode and commit each batch immediately for interruption-safe resume.
            for batch_number, batch in enumerate(chunked(docs, batch_size), start=1):
                # Isolate failures to one small batch rather than aborting all progress.
                try:
                    # Generate normalized E5 vectors from deterministic passage strings.
                    vectors = model.encode(
                        # Preserve the batch's source order when pairing vectors back to IDs.
                        [doc.text for doc in batch],
                        # Let SentenceTransformer use the configured inference mini-batch.
                        batch_size=batch_size,
                        # Unit normalization is required by the cosine handoff contract.
                        normalize_embeddings=True,
                        # NumPy output is efficient and converted before Bolt serialization.
                        convert_to_numpy=True,
                        # Custom concise progress replaces noisy library progress bars.
                        show_progress_bar=False,
                    )
                    # Pair every vector with its immutable node ID and passage hash.
                    rows = [
                        {
                            # MATCH key for the target Neo4j node.
                            "source_id": doc.source_id,
                            # Convert NumPy float scalars into Bolt-compatible Python floats.
                            "embedding": [float(value) for value in vector.tolist()],
                            # Persist exactly the hash used for stale checks.
                            "text_hash": doc.text_hash,
                        }
                        # zip preserves one-to-one document/vector order.
                        for doc, vector in zip(batch, vectors)
                    ]
                    # Split writes independently from inference size when configured differently.
                    for write_batch in chunked(rows, write_batch_size):
                        # Commit vector and metadata properties for this small write batch.
                        execute_write(
                            repository,
                            embedding_write_query(document_type),
                            {
                                # Parameterized vector rows; vectors are never printed.
                                "rows": write_batch,
                                # Exact model checkpoint metadata.
                                "model": config.embeddings.model_name,
                                # Runtime-validated dimension (768).
                                "dimension": dimension,
                                # final_v1 embedding boundary.
                                "version": config.graph_version,
                                # Passage schema/Neo4j label metadata.
                                "document_type": document_type,
                            },
                        )
                    # Count rows only after all write sub-batches succeed.
                    generated += len(rows)
                    # Emit concise progress without text or vectors.
                    print(
                        f"{document_type}: batch {batch_number}/{batches}, written={len(rows)}",
                        flush=True,
                    )
                # Record failures without exposing medical text or vector values.
                except Exception as exc:
                    # Every ID in this batch remains stale and will be retried next execution.
                    failed_ids.extend(doc.source_id for doc in batch)
                    # Log only exception type and batch size for safe diagnostics.
                    print(
                        f"{document_type}: batch {batch_number}/{batches}, failed={len(batch)}, "
                        f"error={type(exc).__name__}",
                        flush=True,
                    )

        # Build indexes only when every stale node was embedded successfully.
        if not failed_ids:
            create_vector_indexes(repository, config)
        # Run exhaustive aggregate vector/metadata/index validation.
        verification, indexes, verified = verify_embeddings(repository, config)
        # Execute one entity-index call only when all prerequisite checks passed.
        semantic_check = (
            minimal_vector_query_check(repository, config, model) if verified else None
        )

    # Stop timing after Neo4j verification and driver closure.
    elapsed = time.perf_counter() - started
    # Print a compact handoff-quality execution summary.
    print("Step 6 execution summary")
    print(f"graph_version: {config.graph_version}")
    print(f"embedding_model: {config.embeddings.model_name}")
    print(f"embedding_dimension: {config.embeddings.dimension}")
    print(f"device: {device}")
    print(f"batch_size: {batch_size}")
    print(f"elapsed_seconds: {elapsed:.2f}")
    print(f"skipped_existing: {skipped}")
    print(f"newly_generated: {generated}")
    print(f"failed_nodes: {len(failed_ids)}")
    # Expose aggregate error counters, never vectors or full source passages.
    for document_type, counts in verification.items():
        print(f"verification_{document_type}: {counts}")
    # Report index labels/properties/state/population for colleague handoff.
    for index in indexes:
        print(
            f"index_{index['name']}: state={index['state']}, "
            f"population={index['populationPercent']}%, labels={index['labelsOrTypes']}, "
            f"properties={index['properties']}"
        )
    # Report only top ID and score from the one allowed semantic index verification.
    if semantic_check:
        print(
            "semantic_index_check: ok, "
            f"top_entity_id={semantic_check.get('source_id')}, "
            f"score={float(semantic_check.get('score') or 0):.4f}"
        )
    # Success requires both exhaustive verification and no failed write batch.
    status = verified and not failed_ids
    print(f"status: {'ok' if status else 'failed'}")
    # Return a shell-friendly success/failure exit code.
    return 0 if status else 1


def main() -> int:
    """Parse CLI mode/options and dispatch exactly one Step 6 workflow."""

    # Windows terminals may default to CP1252, which cannot print Arabic samples.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    # Missing embedding properties are expected before first run; silence those notices.
    logging.getLogger("neo4j.notifications").setLevel(logging.ERROR)
    # Define the Step 6 command-line interface.
    parser = argparse.ArgumentParser(
        description="Build final_v1 E5 embeddings and Neo4j vector indexes (Step 6 only)."
    )
    # --dry-run validates without changing Neo4j.
    parser.add_argument("--dry-run", action="store_true")
    # --execute enables vector writes and index DDL.
    parser.add_argument("--execute", action="store_true")
    # Control inference batch size for CPU/GPU memory and throughput.
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
    # Control maximum rows in one Neo4j write transaction.
    parser.add_argument("--write-batch-size", type=int, default=DEFAULT_WRITE_BATCH_SIZE)
    # Allow a fast structural dry-run without importing Torch/loading E5.
    parser.add_argument(
        "--skip-model-load",
        action="store_true",
        help="Inspect documents without loading/downloading the model; dimension is config-validated only.",
    )
    # Convert command-line arguments into typed attributes.
    args = parser.parse_args()
    # Require exactly one mode; both or neither is ambiguous and unsafe.
    if args.dry_run == args.execute:
        print("Choose exactly one of --dry-run or --execute.")
        return 2
    # Reject invalid slice sizes before entering any Neo4j/model workflow.
    if args.batch_size <= 0 or args.write_batch_size <= 0:
        print("Batch sizes must be positive.")
        return 2
    # Execute writes only under the explicit --execute flag.
    if args.execute:
        return execute_indexing(args.batch_size, args.write_batch_size)
    # Otherwise run the zero-write validation path, optionally loading the model.
    return dry_run(args.batch_size, not args.skip_model_load)


# Standard Python entry-point guard prevents execution when imported by tests/tools.
if __name__ == "__main__":
    # Raise SystemExit so the returned status becomes the process exit code.
    raise SystemExit(main())
