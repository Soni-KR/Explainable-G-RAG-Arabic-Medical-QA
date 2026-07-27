// AHD Graph-RAG Trial Graph v1 retrieval smoke tests.
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
