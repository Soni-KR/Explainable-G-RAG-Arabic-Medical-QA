import csv
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

ENTITIES_CSV = ROOT / "outputs" / "03_entity_extraction" / "ahd_entities_llm.csv"
MENTIONS_CSV = ROOT / "outputs" / "03_entity_extraction" / "ahd_entity_mentions_llm.csv"
QA_CSV = ROOT / "outputs" / "01_preprocessing" / "ahd_subset_5000_preprocessed.csv"
DIRECT_RELATIONS_CSV = ROOT / "outputs" / "04_relation_extraction" / "ahd_relations_llm_validated.csv"
BIDIRECTIONAL_RELATIONS_CSV = ROOT / "outputs" / "04_relation_extraction" / "ahd_relations_neo4j_bidirectional.csv"

OUT_DIR = ROOT / "outputs" / "05_trial_graph_v1"
IMPORT_DIR = OUT_DIR / "import"
FROZEN_DIR = OUT_DIR / "frozen_sources"
REPORT_MD = ROOT / "reports" / "trial_graph_v1_report.md"


def relpath(path):
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def write_csv(path, rows, fieldnames):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def parse_json_list(value):
    if not value:
        return []
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return []
    return parsed if isinstance(parsed, list) else []


def copy_frozen_sources():
    FROZEN_DIR.mkdir(parents=True, exist_ok=True)
    for path in [
        ENTITIES_CSV,
        MENTIONS_CSV,
        DIRECT_RELATIONS_CSV,
        BIDIRECTIONAL_RELATIONS_CSV,
        ROOT / "outputs" / "03_entity_extraction" / "ahd_llm_entity_extraction_validated.jsonl",
        ROOT / "outputs" / "04_relation_extraction" / "ahd_llm_relation_validation_validated.jsonl",
        ROOT / "reports" / "ahd_entity_extraction_report.md",
        ROOT / "reports" / "ahd_relation_validation_report.md",
    ]:
        if path.exists():
            shutil.copy2(path, FROZEN_DIR / path.name)


def build_qa_sources(qa_ids):
    qa_rows = read_csv(QA_CSV)
    selected = []
    for row in qa_rows:
        if row.get("subset_id") in qa_ids:
            selected.append(
                {
                    "qa_id": row.get("subset_id", ""),
                    "source_row_number": row.get("source_row_number", ""),
                    "split": row.get("split", ""),
                    "category": row.get("category", ""),
                    "category_en": row.get("category_en", ""),
                    "question": row.get("question", ""),
                    "answer": row.get("answer", ""),
                    "question_norm": row.get("question_norm", ""),
                    "answer_norm": row.get("answer_norm", ""),
                    "qa_char_len": row.get("qa_char_len", ""),
                }
            )
    selected.sort(key=lambda item: item["qa_id"])
    return selected


def write_cypher_files():
    import_cypher = """// AHD Graph-RAG Trial Graph v1
// Put the CSV files under the Neo4j import directory as trial_graph_v1/*.csv.
// This standard version uses one relationship type, MEDICAL_RELATION, with graph_relation_type as a property.

CREATE CONSTRAINT ahd_entity_id IF NOT EXISTS
FOR (e:MedicalEntity) REQUIRE e.entity_id IS UNIQUE;

CREATE CONSTRAINT ahd_qa_id IF NOT EXISTS
FOR (q:QARecord) REQUIRE q.qa_id IS UNIQUE;

CREATE CONSTRAINT ahd_mention_id IF NOT EXISTS
FOR (m:EvidenceMention) REQUIRE m.mention_id IS UNIQUE;

CREATE CONSTRAINT ahd_relation_edge_id IF NOT EXISTS
FOR ()-[r:MEDICAL_RELATION]-() REQUIRE r.edge_id IS UNIQUE;

LOAD CSV WITH HEADERS FROM 'file:///trial_graph_v1/trial_graph_v1_entities.csv' AS row
MERGE (e:MedicalEntity {entity_id: row.entity_id})
SET e.canonical_name = row.canonical_name,
    e.canonical_name_norm = row.canonical_name_norm,
    e.entity_type = row.entity_type,
    e.entity_quality = row.entity_quality,
    e.is_actionable_medical_entity = row.is_actionable_medical_entity,
    e.mention_count = toInteger(row.mention_count),
    e.source_chunk_count = toInteger(row.source_chunk_count),
    e.qa_count = toInteger(row.qa_count),
    e.avg_confidence = toFloat(row.avg_confidence),
    e.aliases_json = row.aliases,
    e.source_chunks_json = row.source_chunks,
    e.source_models_json = row.source_models,
    e.qa_ids_json = row.qa_ids
FOREACH (_ IN CASE WHEN row.entity_type = 'DiseaseCondition' THEN [1] ELSE [] END | SET e:DiseaseCondition)
FOREACH (_ IN CASE WHEN row.entity_type = 'Symptom' THEN [1] ELSE [] END | SET e:Symptom)
FOREACH (_ IN CASE WHEN row.entity_type = 'Treatment' THEN [1] ELSE [] END | SET e:Treatment)
FOREACH (_ IN CASE WHEN row.entity_type = 'Test' THEN [1] ELSE [] END | SET e:Test);

LOAD CSV WITH HEADERS FROM 'file:///trial_graph_v1/trial_graph_v1_qa_sources.csv' AS row
MERGE (q:QARecord {qa_id: row.qa_id})
SET q.source_row_number = row.source_row_number,
    q.split = row.split,
    q.category = row.category,
    q.category_en = row.category_en,
    q.question = row.question,
    q.answer = row.answer,
    q.question_norm = row.question_norm,
    q.answer_norm = row.answer_norm,
    q.qa_char_len = toInteger(row.qa_char_len);

LOAD CSV WITH HEADERS FROM 'file:///trial_graph_v1/trial_graph_v1_mentions.csv' AS row
MERGE (m:EvidenceMention {mention_id: row.mention_id})
SET m.chunk_id = row.chunk_id,
    m.qa_id = row.qa_id,
    m.source_row_number = row.source_row_number,
    m.surface_form = row.surface_form,
    m.field = row.field,
    m.evidence = row.evidence,
    m.extraction_method = row.extraction_method,
    m.provider = row.provider,
    m.model = row.model,
    m.confidence = toFloat(row.confidence)
WITH row, m
MATCH (e:MedicalEntity {entity_id: row.entity_id})
MERGE (e)-[:MENTIONED_IN]->(m)
WITH row, m
MATCH (q:QARecord {qa_id: row.qa_id})
MERGE (m)-[:EVIDENCE_FROM]->(q);

LOAD CSV WITH HEADERS FROM 'file:///trial_graph_v1/trial_graph_v1_bidirectional_relations.csv' AS row
MATCH (source:MedicalEntity {entity_id: row.source_entity_id})
MATCH (target:MedicalEntity {entity_id: row.target_entity_id})
MERGE (source)-[r:MEDICAL_RELATION {edge_id: row.edge_id}]->(target)
SET r.original_relation_id = row.original_relation_id,
    r.relation_id = row.relation_id,
    r.graph_relation_type = row.graph_relation_type,
    r.edge_direction = row.edge_direction,
    r.candidate_relation_type = row.candidate_relation_type,
    r.validated_relation_type = row.validated_relation_type,
    r.chunk_id = row.chunk_id,
    r.qa_id = row.qa_id,
    r.evidence = row.evidence,
    r.confidence = toFloat(row.confidence),
    r.reason = row.reason,
    r.provider = row.provider,
    r.model = row.model;
"""

    apoc_cypher = """// Optional APOC version for typed Neo4j relationships.
// Run this only if APOC is enabled. It creates HAS_SYMPTOM, TREATS, DIAGNOSES, etc.

LOAD CSV WITH HEADERS FROM 'file:///trial_graph_v1/trial_graph_v1_bidirectional_relations.csv' AS row
MATCH (source:MedicalEntity {entity_id: row.source_entity_id})
MATCH (target:MedicalEntity {entity_id: row.target_entity_id})
CALL apoc.create.relationship(source, row.graph_relation_type, {
  edge_id: row.edge_id,
  original_relation_id: row.original_relation_id,
  relation_id: row.relation_id,
  edge_direction: row.edge_direction,
  candidate_relation_type: row.candidate_relation_type,
  validated_relation_type: row.validated_relation_type,
  chunk_id: row.chunk_id,
  qa_id: row.qa_id,
  evidence: row.evidence,
  confidence: toFloat(row.confidence),
  reason: row.reason,
  provider: row.provider,
  model: row.model
}, target) YIELD rel
RETURN count(rel) AS created_typed_relationships;
"""

    smoke_tests = """// AHD Graph-RAG Trial Graph v1 retrieval smoke tests.
// These queries use the standard MEDICAL_RELATION import.

// 1. Treatments connected to حساسية
MATCH (d:MedicalEntity {canonical_name: 'حساسية'})-[r:MEDICAL_RELATION]->(t:MedicalEntity)
WHERE r.graph_relation_type IN ['TREATED_BY', 'TREATS']
RETURN d.canonical_name AS source, r.graph_relation_type AS relation, t.canonical_name AS target,
       r.confidence AS confidence, r.evidence AS evidence
ORDER BY confidence DESC
LIMIT 20;

// 2. Symptoms connected to حساسية
MATCH (d:MedicalEntity {canonical_name: 'حساسية'})-[r:MEDICAL_RELATION]->(s:MedicalEntity)
WHERE r.graph_relation_type = 'HAS_SYMPTOM'
RETURN d.canonical_name AS disease, s.canonical_name AS symptom,
       r.confidence AS confidence, r.evidence AS evidence
ORDER BY confidence DESC
LIMIT 20;

// 3. Tests that diagnose فقر الدم
MATCH (d:MedicalEntity {canonical_name: 'فقر الدم'})-[r:MEDICAL_RELATION]->(test:MedicalEntity)
WHERE r.graph_relation_type IN ['DIAGNOSED_BY', 'INVESTIGATED_BY']
RETURN d.canonical_name AS disease, r.graph_relation_type AS relation, test.canonical_name AS test,
       r.confidence AS confidence, r.evidence AS evidence
ORDER BY confidence DESC
LIMIT 20;

// 4. Diseases connected to صداع
MATCH (symptom:MedicalEntity {canonical_name: 'صداع'})-[r:MEDICAL_RELATION]->(disease:MedicalEntity)
WHERE r.graph_relation_type = 'SYMPTOM_OF'
RETURN symptom.canonical_name AS symptom, disease.canonical_name AS disease,
       r.confidence AS confidence, r.evidence AS evidence
ORDER BY confidence DESC
LIMIT 20;

// 5. Treatments connected to الجلطة الدماغية
MATCH (d:MedicalEntity {canonical_name: 'الجلطة الدماغية'})-[r:MEDICAL_RELATION]->(treatment:MedicalEntity)
WHERE r.graph_relation_type = 'TREATED_BY'
RETURN d.canonical_name AS disease, treatment.canonical_name AS treatment,
       r.confidence AS confidence, r.evidence AS evidence
ORDER BY confidence DESC
LIMIT 20;

// 6. Evidence trail for one entity
MATCH (e:MedicalEntity {canonical_name: 'حساسية'})-[:MENTIONED_IN]->(m:EvidenceMention)-[:EVIDENCE_FROM]->(q:QARecord)
RETURN e.canonical_name AS entity, m.surface_form AS surface_form, m.field AS field,
       m.evidence AS evidence, q.question AS question, q.answer AS answer
LIMIT 10;
"""

    (OUT_DIR / "neo4j_import_trial_graph_v1.cypher").write_text(import_cypher, encoding="utf-8")
    (OUT_DIR / "neo4j_import_trial_graph_v1_apoc_typed_edges.cypher").write_text(apoc_cypher, encoding="utf-8")
    (OUT_DIR / "graph_retrieval_smoke_tests.cypher").write_text(smoke_tests, encoding="utf-8")


def write_report(counts):
    lines = [
        "# AHD Graph-RAG Trial Graph v1",
        "",
        "This freezes the current Step 3/Step 4 outputs for Step 5 retrieval testing.",
        "",
        "## Counts",
        "",
        f"- Entity nodes: {counts['entities']}",
        f"- Evidence mentions: {counts['mentions']}",
        f"- QA/source records: {counts['qa_sources']}",
        f"- Validated direct medical relations: {counts['direct_relations']}",
        f"- Neo4j bidirectional relation rows: {counts['bidirectional_relations']}",
        "",
        "## Import Files",
        "",
        f"- Entities: `{relpath(IMPORT_DIR / 'trial_graph_v1_entities.csv')}`",
        f"- Evidence mentions: `{relpath(IMPORT_DIR / 'trial_graph_v1_mentions.csv')}`",
        f"- QA/source records: `{relpath(IMPORT_DIR / 'trial_graph_v1_qa_sources.csv')}`",
        f"- Direct relations: `{relpath(IMPORT_DIR / 'trial_graph_v1_direct_relations.csv')}`",
        f"- Bidirectional relations: `{relpath(IMPORT_DIR / 'trial_graph_v1_bidirectional_relations.csv')}`",
        "",
        "## Neo4j Files",
        "",
        f"- Standard import Cypher: `{relpath(OUT_DIR / 'neo4j_import_trial_graph_v1.cypher')}`",
        f"- Optional APOC typed-edge Cypher: `{relpath(OUT_DIR / 'neo4j_import_trial_graph_v1_apoc_typed_edges.cypher')}`",
        f"- Retrieval smoke tests: `{relpath(OUT_DIR / 'graph_retrieval_smoke_tests.cypher')}`",
        "",
        "## Design Notes",
        "",
        "- The standard import uses a generic `MEDICAL_RELATION` type and stores the actual relation in `graph_relation_type`.",
        "- The bidirectional relation file keeps `edge_direction` as `direct` or `inverse` and keeps `original_relation_id` for provenance.",
        "- Evidence is preserved through `EvidenceMention` nodes linked to `QARecord` source nodes.",
        "- This graph is intentionally frozen for retrieval and answer-generation testing before scaling Step 3/Step 4.",
    ]
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    (OUT_DIR / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    entities = read_csv(ENTITIES_CSV)
    mentions = read_csv(MENTIONS_CSV)
    direct_relations = read_csv(DIRECT_RELATIONS_CSV)
    bidirectional_relations = read_csv(BIDIRECTIONAL_RELATIONS_CSV)

    qa_ids = set()
    for row in mentions:
        if row.get("qa_id"):
            qa_ids.add(row["qa_id"])
    for row in direct_relations:
        if row.get("qa_id"):
            qa_ids.add(row["qa_id"])
    for row in entities:
        for qa_id in parse_json_list(row.get("qa_ids", "")):
            qa_ids.add(str(qa_id))

    qa_sources = build_qa_sources(qa_ids)

    IMPORT_DIR.mkdir(parents=True, exist_ok=True)
    copy_frozen_sources()

    write_csv(IMPORT_DIR / "trial_graph_v1_entities.csv", entities, list(entities[0].keys()))
    write_csv(IMPORT_DIR / "trial_graph_v1_mentions.csv", mentions, list(mentions[0].keys()))
    write_csv(IMPORT_DIR / "trial_graph_v1_qa_sources.csv", qa_sources, list(qa_sources[0].keys()))
    write_csv(IMPORT_DIR / "trial_graph_v1_direct_relations.csv", direct_relations, list(direct_relations[0].keys()))
    write_csv(
        IMPORT_DIR / "trial_graph_v1_bidirectional_relations.csv",
        bidirectional_relations,
        list(bidirectional_relations[0].keys()),
    )

    write_cypher_files()

    counts = {
        "entities": len(entities),
        "mentions": len(mentions),
        "qa_sources": len(qa_sources),
        "direct_relations": len(direct_relations),
        "bidirectional_relations": len(bidirectional_relations),
    }
    write_report(counts)
    print(json.dumps({**counts, "out_dir": relpath(OUT_DIR), "report_md": relpath(REPORT_MD)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
