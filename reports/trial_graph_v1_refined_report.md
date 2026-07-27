# AHD Graph-RAG Trial Graph v1

This freezes the current Step 3/Step 4 outputs for Step 5 retrieval testing.

## Counts

- Entity nodes: 2072
- Evidence mentions: 4308
- QA/source records: 1411
- Validated direct medical relations: 471
- Neo4j bidirectional relation rows: 942

## Import Files

- Entities: `outputs/05_trial_graph_v1_refined/import/trial_graph_v1_entities.csv`
- Evidence mentions: `outputs/05_trial_graph_v1_refined/import/trial_graph_v1_mentions.csv`
- QA/source records: `outputs/05_trial_graph_v1_refined/import/trial_graph_v1_qa_sources.csv`
- Direct relations: `outputs/05_trial_graph_v1_refined/import/trial_graph_v1_direct_relations.csv`
- Bidirectional relations: `outputs/05_trial_graph_v1_refined/import/trial_graph_v1_bidirectional_relations.csv`

## Neo4j Files

- Standard import Cypher: `outputs/05_trial_graph_v1_refined/neo4j_import_trial_graph_v1.cypher`
- Optional APOC typed-edge Cypher: `outputs/05_trial_graph_v1_refined/neo4j_import_trial_graph_v1_apoc_typed_edges.cypher`
- Retrieval smoke tests: `outputs/05_trial_graph_v1_refined/graph_retrieval_smoke_tests.cypher`

## Design Notes

- The standard import uses a generic `MEDICAL_RELATION` type and stores the actual relation in `graph_relation_type`.
- The bidirectional relation file keeps `edge_direction` as `direct` or `inverse` and keeps `original_relation_id` for provenance.
- Evidence is preserved through `EvidenceMention` nodes linked to `QARecord` source nodes.
- This graph is intentionally frozen for retrieval and answer-generation testing before scaling Step 3/Step 4.
