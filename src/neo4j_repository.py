from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from neo4j import GraphDatabase

from src.config import AppConfig, load_config


class Neo4jRepository:
    """Small connection wrapper for read-only Neo4j health checks."""

    def __init__(self, config: AppConfig | None = None) -> None:
        self.config = config or load_config()
        self._driver = GraphDatabase.driver(
            self.config.neo4j.uri,
            auth=(self.config.neo4j.username, self.config.neo4j.password),
        )

    def close(self) -> None:
        if self._driver is not None:
            self._driver.close()

    def __enter__(self) -> "Neo4jRepository":
        return self

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        self.close()

    def _execute_read(self, query: str, parameters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        with self._driver.session(database=self.config.neo4j.database) as session:
            result = session.execute_read(
                lambda tx: [dict(record) for record in tx.run(query, parameters or {})]
            )
        return result

    @property
    def graph_version(self) -> str:
        return self.config.graph_version

    def _entity_from_row(self, row: dict[str, Any]) -> dict[str, Any]:
        aliases = row.get("aliases")
        if aliases is None:
            aliases = []
        return {
            "entity_id": row.get("entity_id", ""),
            "canonical_name": row.get("canonical_name", ""),
            "canonical_name_norm": row.get("canonical_name_norm", ""),
            "entity_type": row.get("entity_type", ""),
            "aliases": aliases,
        }

    def get_neo4j_version(self) -> str:
        rows = self._execute_read(
            "CALL dbms.components() "
            "YIELD name, versions "
            "WHERE name = 'Neo4j Kernel' "
            "RETURN versions[0] AS version"
        )
        if not rows:
            return "unknown"
        return str(rows[0].get("version") or "unknown")

    def health_check(self) -> dict[str, str]:
        # This is intentionally read-only: no constraints, writes, imports, or retrieval queries.
        self._execute_read("RETURN 1 AS ok")
        return {
            "connection": "ok",
            "database": self.config.neo4j.database,
            "neo4j_version": self.get_neo4j_version(),
            "graph_version": self.config.graph_version,
        }

    def get_entities(self) -> list[dict[str, Any]]:
        """Return the Step 8 entity vocabulary for the configured graph version."""
        rows = self._execute_read(
            """
MATCH (e:MedicalEntity {graph_version: $graph_version})
RETURN e.entity_id AS entity_id,
       e.canonical_name AS canonical_name,
       e.canonical_name_norm AS canonical_name_norm,
       e.entity_type AS entity_type,
       e.aliases AS aliases
ORDER BY e.canonical_name
""".strip(),
            {"graph_version": self.graph_version},
        )
        return [self._entity_from_row(row) for row in rows]

    def get_entity_by_id(self, entity_id: str) -> dict[str, Any] | None:
        """Return one entity by ID within the configured graph version."""
        rows = self._execute_read(
            """
MATCH (e:MedicalEntity {entity_id: $entity_id, graph_version: $graph_version})
RETURN e.entity_id AS entity_id,
       e.canonical_name AS canonical_name,
       e.canonical_name_norm AS canonical_name_norm,
       e.entity_type AS entity_type,
       e.aliases AS aliases
LIMIT 1
""".strip(),
            {"entity_id": entity_id, "graph_version": self.graph_version},
        )
        return self._entity_from_row(rows[0]) if rows else None

    def get_relation_types(self) -> list[str]:
        """Return sorted unique relation types only."""
        rows = self._execute_read(
            """
MATCH ()-[r:MEDICAL_RELATION]->()
WHERE r.graph_version = $graph_version AND r.relation_type IS NOT NULL
RETURN DISTINCT r.relation_type AS relation_type
ORDER BY relation_type
""".strip(),
            {"graph_version": self.graph_version},
        )
        return [str(row["relation_type"]) for row in rows if row.get("relation_type")]

    def get_graph_counts(self) -> dict[str, int]:
        """Return fixed-schema counts for the configured graph version."""
        queries = {
            "MedicalEntity": (
                "MATCH (n) WHERE $label IN labels(n) AND n.graph_version = $graph_version "
                "RETURN count(n) AS count"
            ),
            "EvidenceMention": (
                "MATCH (n) WHERE $label IN labels(n) AND n.graph_version = $graph_version "
                "RETURN count(n) AS count"
            ),
            "QARecord": (
                "MATCH (n) WHERE $label IN labels(n) AND n.graph_version = $graph_version "
                "RETURN count(n) AS count"
            ),
            "MEDICAL_RELATION": (
                "MATCH ()-[r]->() WHERE type(r) = $relationship_type AND r.graph_version = $graph_version "
                "RETURN count(r) AS count"
            ),
            "MENTIONED_IN": (
                "MATCH ()-[r]->() WHERE type(r) = $relationship_type AND r.graph_version = $graph_version "
                "RETURN count(r) AS count"
            ),
            "EVIDENCE_FROM": (
                "MATCH ()-[r]->() WHERE type(r) = $relationship_type AND r.graph_version = $graph_version "
                "RETURN count(r) AS count"
            ),
        }

        counts: dict[str, int] = {}
        for name, query in queries.items():
            parameters = {"graph_version": self.graph_version}
            if name in {"MedicalEntity", "EvidenceMention", "QARecord"}:
                parameters["label"] = name
            else:
                parameters["relationship_type"] = name
            rows = self._execute_read(query, parameters)
            counts[name] = int(rows[0]["count"]) if rows else 0
        return counts

    def find_entities_by_normalized_terms(self, terms: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Find candidate entities by exact canonical/alias normalized terms in one read query."""
        if not terms:
            return []
        return self._execute_read(
            """
UNWIND $terms AS term
MATCH (e:MedicalEntity {graph_version: $graph_version})
WITH term, e,
     CASE WHEN e.canonical_name_norm = term.normalized_form THEN true ELSE false END AS canonical_match,
     [alias IN coalesce(e.aliases, []) WHERE alias IN term.alias_forms] AS alias_matches
WHERE canonical_match OR size(alias_matches) > 0
RETURN term.term_id AS term_id,
       term.original_normalized_form AS original_normalized_form,
       term.normalized_form AS matched_normalized_form,
       e.entity_id AS entity_id,
       e.canonical_name AS canonical_name,
       e.canonical_name_norm AS canonical_name_norm,
       e.entity_type AS entity_type,
       canonical_match AS canonical_match,
       alias_matches AS alias_matches
""".strip(),
            {"terms": terms, "graph_version": self.graph_version},
        )

    def query_vector_index(
        self,
        document_type: str,
        index_name: str,
        embedding: list[float],
        top_k: int,
    ) -> list[dict[str, Any]]:
        """Search one final graph vector index without exposing dynamic Cypher."""
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", index_name):
            raise ValueError("Invalid Neo4j vector index name.")
        if top_k <= 0:
            return []

        queries = {
            "MedicalEntity": """
CALL db.index.vector.queryNodes($index_name, $candidate_k, $embedding)
YIELD node, score
WHERE node.graph_version = $graph_version
RETURN node.entity_id AS result_id,
       node.entity_id AS entity_id,
       '' AS qa_id,
       node.canonical_name AS title,
       node.canonical_name + ' | ' + coalesce(node.entity_type, '') AS text,
       score,
       {entity_type: node.entity_type, aliases: node.aliases} AS metadata
ORDER BY score DESC
LIMIT $top_k
""".strip(),
            "EvidenceMention": """
CALL db.index.vector.queryNodes($index_name, $candidate_k, $embedding)
YIELD node, score
WHERE node.graph_version = $graph_version
OPTIONAL MATCH (entity:MedicalEntity)-[:MENTIONED_IN]->(node)
WHERE entity.graph_version = $graph_version
OPTIONAL MATCH (node)-[:EVIDENCE_FROM]->(qa:QARecord)
WHERE qa.graph_version = $graph_version
RETURN node.mention_id AS result_id,
       coalesce(entity.entity_id, '') AS entity_id,
       coalesce(qa.qa_id, '') AS qa_id,
       coalesce(node.surface_form, '') AS title,
       coalesce(node.evidence, '') AS text,
       score,
       {field: node.field, confidence: node.confidence, entity_name: entity.canonical_name,
        question: qa.question, answer: qa.answer, category: qa.category,
        source_quality: qa.source_quality} AS metadata
ORDER BY score DESC
LIMIT $top_k
""".strip(),
            "QARecord": """
CALL db.index.vector.queryNodes($index_name, $candidate_k, $embedding)
YIELD node, score
WHERE node.graph_version = $graph_version
RETURN node.qa_id AS result_id,
       '' AS entity_id,
       node.qa_id AS qa_id,
       coalesce(node.question, '') AS title,
       coalesce(node.question, '') + '\n' + coalesce(node.answer, '') AS text,
       score,
       {question: node.question, answer: node.answer, category: node.category,
        source_row_number: node.source_row_number, source_quality: node.source_quality} AS metadata
ORDER BY score DESC
LIMIT $top_k
""".strip(),
        }
        if document_type not in queries:
            raise ValueError(f"Unsupported vector document type: {document_type}")
        return self._execute_read(
            queries[document_type],
            {
                "index_name": index_name,
                "candidate_k": max(top_k * 3, top_k),
                "embedding": embedding,
                "graph_version": self.graph_version,
                "top_k": top_k,
            },
        )

    def get_medical_relations(
        self,
        seed_entity_ids: list[str],
        relation_types: list[str],
        hop_depth: int,
        limit: int,
    ) -> list[dict[str, Any]]:
        """Traverse one or two medical-relation hops from trusted seed entities."""
        if not seed_entity_ids or hop_depth <= 0 or limit <= 0:
            return []
        if hop_depth not in {1, 2}:
            raise ValueError("hop_depth must be 1 or 2.")
        path_pattern = "[:MEDICAL_RELATION*1..1]" if hop_depth == 1 else "[:MEDICAL_RELATION*1..2]"
        query = f"""
MATCH (seed:MedicalEntity)
WHERE seed.graph_version = $graph_version AND seed.entity_id IN $seed_entity_ids
MATCH path=(seed)-{path_pattern}-(neighbor:MedicalEntity)
WHERE neighbor.graph_version = $graph_version
  AND all(edge IN relationships(path) WHERE edge.graph_version = $graph_version)
UNWIND relationships(path) AS relation
WITH DISTINCT seed, relation, startNode(relation) AS source, endNode(relation) AS target
WHERE size($relation_types) = 0 OR relation.relation_type IN $relation_types
OPTIONAL MATCH (mention:EvidenceMention)-[:EVIDENCE_FROM]->(qa:QARecord)
WHERE qa.qa_id = relation.qa_id
  AND qa.graph_version = $graph_version
  AND mention.graph_version = $graph_version
WITH seed, relation, source, target,
     collect(DISTINCT CASE WHEN mention IS NULL THEN null ELSE {{
       mention_id: mention.mention_id,
       evidence: mention.evidence,
       field: mention.field,
       confidence: mention.confidence,
       qa_id: qa.qa_id,
       question: qa.question,
       answer: qa.answer,
       category: qa.category,
       source_quality: qa.source_quality
     }} END)[..3] AS evidence_items
RETURN seed.entity_id AS seed_entity_id,
       seed.entity_type AS seed_entity_type,
       relation.relation_id AS relation_id,
       relation.source_relation_id AS source_relation_id,
       source.entity_id AS source_entity_id,
       source.canonical_name AS source_name,
       source.entity_type AS source_entity_type,
       target.entity_id AS target_entity_id,
       target.canonical_name AS target_name,
       target.entity_type AS target_entity_type,
       relation.relation_type AS relation_type,
       relation.confidence AS confidence,
       relation.qa_id AS qa_id,
       relation.evidence AS evidence,
       relation.direction AS direction,
       evidence_items
ORDER BY relation.confidence DESC
LIMIT $limit
""".strip()
        return self._execute_read(
            query,
            {
                "seed_entity_ids": seed_entity_ids,
                "relation_types": relation_types,
                "graph_version": self.graph_version,
                "limit": limit,
            },
        )


def print_schema_inspection(repository: Neo4jRepository) -> None:
    entities = repository.get_entities()
    relation_types = repository.get_relation_types()
    counts = repository.get_graph_counts()

    print(f"graph_version: {repository.graph_version}")
    print(f"entity_count: {len(entities)}")
    print("relation_types:")
    for relation_type in relation_types:
        print(f"- {relation_type}")
    print("graph_counts:")
    for key, value in counts.items():
        print(f"- {key}: {value}")
    print("sample_entities:")
    for entity in entities[:3]:
        aliases = entity.get("aliases")
        print(
            f"- entity_id: {entity.get('entity_id')}, "
            f"canonical_name: {entity.get('canonical_name')}, "
            f"entity_type: {entity.get('entity_type')}, "
            f"aliases_storage: {type(aliases).__name__}, "
            f"aliases_sample: {aliases[:3] if isinstance(aliases, list) else aliases}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only Neo4j repository checks.")
    parser.add_argument("--inspect-schema", action="store_true", help="Inspect Step 8 vocabulary inputs.")
    args = parser.parse_args()

    try:
        with Neo4jRepository() as repository:
            if args.inspect_schema:
                print_schema_inspection(repository)
                return 0
            health = repository.health_check()
    except Exception as exc:
        print("Neo4j connection: failed")
        print(f"database: {load_config().neo4j.database}")
        print("Neo4j version: unknown")
        print(f"graph version: {os.environ.get('GRAPH_VERSION') or load_config().graph_version}")
        print(f"error: {type(exc).__name__}")
        return 1

    print(f"Neo4j connection: {health['connection']}")
    print(f"database: {health['database']}")
    print(f"Neo4j version: {health['neo4j_version']}")
    print(f"graph version: {health['graph_version']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
