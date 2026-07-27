// Copy the three CSV files in outputs/05_trial_graph_v1/supplemental_facts/
// into the Neo4j import directory, then run this file in Neo4j Browser or cypher-shell.

LOAD CSV WITH HEADERS FROM 'file:///trial_graph_v1_supplemental_entities.csv' AS row
MERGE (e:MedicalEntity {entity_id: row.entity_id})
SET e.canonical_name = row.canonical_name,
    e.canonical_name_norm = row.canonical_name_norm,
    e.entity_type = row.entity_type,
    e.entity_quality = row.entity_quality,
    e.graph_version = 'supplemental_v1',
    e.is_supplemental = true;

LOAD CSV WITH HEADERS FROM 'file:///trial_graph_v1_supplemental_qa_sources.csv' AS row
MERGE (q:QARecord {qa_id: row.qa_id})
SET q.question = row.question,
    q.answer = row.answer,
    q.category = row.category,
    q.category_en = row.category_en,
    q.split = row.split,
    q.graph_version = 'supplemental_v1',
    q.is_supplemental = true;

LOAD CSV WITH HEADERS FROM 'file:///trial_graph_v1_supplemental_relations.csv' AS row
MATCH (s:MedicalEntity {entity_id: row.source_entity_id})
MATCH (t:MedicalEntity {entity_id: row.target_entity_id})
MERGE (s)-[r:MEDICAL_RELATION {edge_id: row.edge_id}]->(t)
SET r.relation_id = row.relation_id,
    r.relation_type = row.graph_relation_type,
    r.graph_relation_type = row.graph_relation_type,
    r.evidence = row.evidence,
    r.confidence = toFloat(row.confidence),
    r.qa_id = row.qa_id,
    r.reason = row.reason,
    r.provider = row.provider,
    r.model = row.model,
    r.graph_version = 'supplemental_v1',
    r.is_supplemental = true;
