from __future__ import annotations

from typing import Any

from src.models import (
    EVIDENCE_FROM_REL,
    EVIDENCE_MENTION_LABEL,
    MEDICAL_ENTITY_LABEL,
    MEDICAL_RELATION_REL,
    MENTIONED_IN_REL,
    QA_RECORD_LABEL,
)
from src.neo4j_repository import Neo4jRepository


DEFAULT_BATCH_SIZE = 500


def constraint_cypher_templates() -> list[str]:
    return [
        f"CREATE CONSTRAINT medical_entity_id_unique IF NOT EXISTS FOR (n:{MEDICAL_ENTITY_LABEL}) REQUIRE n.entity_id IS UNIQUE",
        f"CREATE CONSTRAINT evidence_mention_id_unique IF NOT EXISTS FOR (n:{EVIDENCE_MENTION_LABEL}) REQUIRE n.mention_id IS UNIQUE",
        f"CREATE CONSTRAINT qa_record_id_unique IF NOT EXISTS FOR (n:{QA_RECORD_LABEL}) REQUIRE n.qa_id IS UNIQUE",
    ]


def node_import_cypher_templates() -> dict[str, str]:
    return {
        "entities": f"UNWIND $rows AS row MERGE (n:{MEDICAL_ENTITY_LABEL} {{entity_id: row.entity_id}}) SET n += row",
        "mentions": f"UNWIND $rows AS row MERGE (n:{EVIDENCE_MENTION_LABEL} {{mention_id: row.mention_id}}) SET n += row",
        "qa_records": f"UNWIND $rows AS row MERGE (n:{QA_RECORD_LABEL} {{qa_id: row.qa_id}}) SET n += row",
    }


def relationship_import_cypher_templates() -> dict[str, str]:
    return {
        "mentioned_in": f"""
UNWIND $rows AS row
MATCH (entity:{MEDICAL_ENTITY_LABEL} {{entity_id: row.entity_id}})
MATCH (mention:{EVIDENCE_MENTION_LABEL} {{mention_id: row.mention_id}})
MERGE (entity)-[r:{MENTIONED_IN_REL}]->(mention)
SET r += row.properties
""".strip(),
        "evidence_from": f"""
UNWIND $rows AS row
MATCH (mention:{EVIDENCE_MENTION_LABEL} {{mention_id: row.mention_id}})
MATCH (qa:{QA_RECORD_LABEL} {{qa_id: row.qa_id}})
MERGE (mention)-[r:{EVIDENCE_FROM_REL}]->(qa)
SET r += row.properties
""".strip(),
        "medical_relations": f"""
UNWIND $rows AS row
MATCH (source:{MEDICAL_ENTITY_LABEL} {{entity_id: row.source_entity_id}})
MATCH (target:{MEDICAL_ENTITY_LABEL} {{entity_id: row.target_entity_id}})
MERGE (source)-[r:{MEDICAL_RELATION_REL} {{relation_id: row.relation_id}}]->(target)
SET r += row.properties
""".strip(),
    }


def chunked(rows: list[dict[str, Any]], batch_size: int) -> list[list[dict[str, Any]]]:
    return [rows[index : index + batch_size] for index in range(0, len(rows), batch_size)]


def graph_record_count_queries() -> dict[str, str]:
    return {
        "MedicalEntity": "MATCH (n:MedicalEntity) RETURN count(n) AS count",
        "EvidenceMention": "MATCH (n:EvidenceMention) RETURN count(n) AS count",
        "QARecord": "MATCH (n:QARecord) RETURN count(n) AS count",
        "MEDICAL_RELATION": "MATCH ()-[r:MEDICAL_RELATION]->() RETURN count(r) AS count",
        "MENTIONED_IN": "MATCH ()-[r:MENTIONED_IN]->() RETURN count(r) AS count",
        "EVIDENCE_FROM": "MATCH ()-[r:EVIDENCE_FROM]->() RETURN count(r) AS count",
    }


def validation_queries() -> dict[str, str]:
    return {
        "missing_relation_endpoints": "MATCH ()-[r:MEDICAL_RELATION]->() WHERE startNode(r) IS NULL OR endNode(r) IS NULL RETURN count(r) AS count",
        "mentions_without_entity": "MATCH (m:EvidenceMention) WHERE NOT (:MedicalEntity)-[:MENTIONED_IN]->(m) RETURN count(m) AS count",
        "mentions_without_qa_record": "MATCH (m:EvidenceMention) WHERE NOT (m)-[:EVIDENCE_FROM]->(:QARecord) RETURN count(m) AS count",
        "duplicate_entity_ids": "MATCH (n:MedicalEntity) WITH n.entity_id AS id, count(*) AS count WHERE id IS NOT NULL AND count > 1 RETURN count(*) AS count",
        "duplicate_mention_ids": "MATCH (n:EvidenceMention) WITH n.mention_id AS id, count(*) AS count WHERE id IS NOT NULL AND count > 1 RETURN count(*) AS count",
        "duplicate_qa_ids": "MATCH (n:QARecord) WITH n.qa_id AS id, count(*) AS count WHERE id IS NOT NULL AND count > 1 RETURN count(*) AS count",
        "duplicate_relation_ids": "MATCH ()-[r:MEDICAL_RELATION]->() WITH r.relation_id AS id, count(*) AS count WHERE id IS NOT NULL AND count > 1 RETURN count(*) AS count",
    }


def read_counts(repository: Neo4jRepository, queries: dict[str, str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for name, query in queries.items():
        rows = repository._execute_read(query)
        counts[name] = int(rows[0]["count"]) if rows else 0
    return counts


def execute_query(repository: Neo4jRepository, query: str, parameters: dict[str, Any] | None = None) -> None:
    with repository._driver.session(database=repository.config.neo4j.database) as session:
        session.execute_write(lambda tx: tx.run(query, **(parameters or {})).consume())


def execute_batch_import(
    repository: Neo4jRepository,
    query: str,
    rows: list[dict[str, Any]],
    batch_size: int,
) -> None:
    for batch in chunked(rows, batch_size):
        execute_query(repository, query, {"rows": batch})


def node_rows(records: Any, graph_version: str) -> dict[str, list[dict[str, Any]]]:
    return {
        "entities": [{**row, "graph_version": graph_version} for row in records.entities],
        "mentions": [
            {
                "mention_id": row["mention_id"],
                "surface_form": row["surface_form"],
                "field": row["field"],
                "evidence": row["evidence"],
                "confidence": row["confidence"],
                "graph_version": graph_version,
            }
            for row in records.mentions
        ],
        "qa_records": [{**row, "graph_version": graph_version} for row in records.qa_records],
    }


def relationship_rows(records: Any, graph_version: str) -> dict[str, list[dict[str, Any]]]:
    return {
        "mentioned_in": [
            {
                "entity_id": row["entity_id"],
                "mention_id": row["mention_id"],
                "properties": {"graph_version": graph_version},
            }
            for row in records.mentions
        ],
        "evidence_from": [
            {
                "mention_id": row["mention_id"],
                "qa_id": row["qa_id"],
                "properties": {"graph_version": graph_version},
            }
            for row in records.mentions
        ],
        "medical_relations": [
            {
                "source_entity_id": row["source_entity_id"],
                "target_entity_id": row["target_entity_id"],
                "relation_id": row["relation_id"],
                "properties": {
                    "relation_id": row["relation_id"],
                    "source_relation_id": row["source_relation_id"],
                    "relation_type": row["relation_type"],
                    "confidence": row["confidence"],
                    "qa_id": row["qa_id"],
                    "evidence": row["evidence"],
                    "direction": row["direction"],
                    "graph_version": graph_version,
                },
            }
            for row in records.medical_relations
        ],
    }


def planned_counts(records: Any) -> dict[str, int]:
    return {
        "entities": len(records.entities),
        "mentions": len(records.mentions),
        "qa_records": len(records.qa_records),
        "medical_relations": len(records.medical_relations),
        "mentioned_in_relationships": len(records.mentions),
        "evidence_from_relationships": len(records.mentions),
    }


def compare_counts(actual: dict[str, int], records: Any) -> dict[str, bool]:
    expected = {
        "MedicalEntity": len(records.entities),
        "EvidenceMention": len(records.mentions),
        "QARecord": len(records.qa_records),
        "MEDICAL_RELATION": len(records.medical_relations),
        "MENTIONED_IN": len(records.mentions),
        "EVIDENCE_FROM": len(records.mentions),
    }
    return {key: actual.get(key, -1) == value for key, value in expected.items()}


def print_counts(title: str, counts: dict[str, int]) -> None:
    print(title)
    for key, value in counts.items():
        print(f"{key}: {value}")
