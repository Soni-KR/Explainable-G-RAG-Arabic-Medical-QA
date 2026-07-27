// Optional APOC version for typed Neo4j relationships.
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
