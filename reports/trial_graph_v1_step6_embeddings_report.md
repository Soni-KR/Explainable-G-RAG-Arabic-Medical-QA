# Trial Graph v1 Step 6 Embeddings Report

This is the official Step 6 embedding/indexing layer for the frozen `trial_graph_v1` graph.

## Model

- Embedding model: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`

## Documents

- Prepared documents: 2145
- Embedded documents: 2145

## Output Files

- Embedding documents: `outputs/05_trial_graph_v1/embeddings/trial_graph_v1_embedding_documents.csv`
- Embeddings JSONL: `outputs/05_trial_graph_v1/embeddings/trial_graph_v1_embeddings.jsonl`
- Metadata: `outputs/05_trial_graph_v1/embeddings/trial_graph_v1_embeddings_metadata.json`

## Scope

- Entity nodes are embedded using canonical names, compatible aliases, entity type, quality, and relation context.
- Evidence mentions are embedded using evidence text, entity names, surface form, field, and relation context.
- QA/source records are embedded using question, answer, category, and relation context.
