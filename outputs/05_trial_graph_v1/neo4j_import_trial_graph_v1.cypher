// AHD Graph-RAG Trial Graph v1
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
