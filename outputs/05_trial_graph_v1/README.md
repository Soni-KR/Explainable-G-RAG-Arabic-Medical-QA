# AHD Graph-RAG Trial Graph v1

This folder contains the frozen trial graph and the important outputs up to Step 12 in `mix.png`.

The graph itself should stay frozen while testing generation and verification. If Step 3 or Step 4 is scaled later, create a new folder such as `trial_graph_v2`.

## Current Status

- Step 5: Neo4j-ready graph construction complete
- Step 6: embeddings generated
- Step 8: query understanding complete
- Step 9A/9B/9C: semantic, graph, and hybrid retrieval tested
- Step 10: subgraph reranking complete
- Step 11: evidence-focused context construction complete
- Step 12: Qwen answer generation complete

Stop point: Step 12. Step 13 claim extraction has not been run.

## Important Files Kept

### Neo4j Import

- `import/trial_graph_v1_entities.csv`
- `import/trial_graph_v1_mentions.csv`
- `import/trial_graph_v1_qa_sources.csv`
- `import/trial_graph_v1_direct_relations.csv`
- `import/trial_graph_v1_bidirectional_relations.csv`
- `neo4j_import_trial_graph_v1.cypher`
- `neo4j_import_trial_graph_v1_apoc_typed_edges.cypher`
- `graph_retrieval_smoke_tests.cypher`

### Step 6 Embeddings

- `embeddings/trial_graph_v1_embedding_documents.csv`
- `embeddings/trial_graph_v1_embeddings.jsonl`
- `embeddings/trial_graph_v1_embeddings_metadata.json`

The old embedding smoke-test result dumps were removed because the report is enough and the test can be rerun.

### Step 8 Query Understanding

- `query_understanding/trial_graph_v1_query_set.csv`
- `query_understanding/trial_graph_v1_query_understanding.csv`
- `query_understanding/trial_graph_v1_query_understanding.json`

### Step 10 Subgraph Reranking

- `subgraph_reranking/trial_graph_v1_reranked_relations.csv`
- `subgraph_reranking/trial_graph_v1_reranked_evidence.csv`
- `subgraph_reranking/trial_graph_v1_reranked_subgraphs.json`

Step 9 semantic/hybrid retrieval dumps were removed because Step 10 is the compact, evidence-aware version to keep.

### Step 11 Context Construction

- `context_construction/trial_graph_v1_context_bundles.csv`
- `context_construction/trial_graph_v1_context_bundles.json`

### Step 12 Answer Generation

- `answer_generation/trial_graph_v1_answers.csv`
- `answer_generation/trial_graph_v1_answers.json`

Raw LLM responses and empty error files were removed after successful validation.

## Reports

The step-by-step explanation and audit trail live in `reports/`.

Most relevant current reports:

- `reports/trial_graph_v1_report.md`
- `reports/trial_graph_v1_step6_embeddings_report.md`
- `reports/trial_graph_v1_step8_query_understanding_report.md`
- `reports/trial_graph_v1_step9a_semantic_retrieval_report.md`
- `reports/trial_graph_v1_step9c_hybrid_retrieval_report.md`
- `reports/trial_graph_v1_step10_subgraph_reranking_report.md`
- `reports/trial_graph_v1_step11_context_construction_report.md`
- `reports/trial_graph_v1_step12_answer_generation_report.md`

## Cleanup Policy

Keep:

- Source data
- Pipeline scripts
- Reports
- Final CSV/JSON artifacts needed by the next step
- Neo4j import files
- Embeddings and metadata

Delete:

- Raw LLM responses after successful validation
- Request JSONL files after the corresponding final CSV/JSON exists
- Empty error files
- Duplicate frozen snapshots
- Smoke-test dumps when the report is enough
- Replaced trial outputs

Local dependency folder `.deps-step6/` is hidden and ignored. It is not a research output, but it is useful for rerunning embedding/search scripts without reinstalling packages.
