# Script Map

This folder is organized by the `mix.png` pipeline. The scripts are kept as plain Python so they can be rerun from the terminal, but each major script now follows a notebook-style structure with section comments such as `# %% [markdown]`.

## Step 1 - Dataset Subset And Preprocessing

- `step01_prepare_subset.py`
  - Samples the 5k subset from the raw AHD CSV.
  - Saves sampling/category distribution outputs.
- `step01_preprocess_medical_normalization.py`
  - Cleans Arabic text.
  - Adds normalized duplicate detection.
  - Adds graph/validation/evaluation split.
  - Adds length statistics and weak medical dictionary hints.

## Step 2 - Chunking

- `step02_chunk_preprocessed.py`
  - Groups preprocessed Q&A rows into LLM-friendly chunks.
  - Keeps `qa_records` inside each chunk for evidence linking.
  - Flags oversized chunks.

## Step 3 - Entity Extraction

- `step03_extract_entities.py`
  - Sends chunks to Groq.
  - Uses a strict entity-only prompt.
  - Validates model JSON.
  - Canonicalizes noisy entity forms.
  - Exports entity, mention, and alias CSV tables.

Important note: this script used to support OpenAI/Gemini branches, but the project actually used Groq. Those unused branches were removed.

## Step 4 - Relation Extraction

- `step04_prepare_relation_candidates.py`
  - Builds candidate relation pairs from entity co-occurrence and evidence.
- `step04_validate_relations.py`
  - Uses Groq/Qwen to strictly keep or reject candidate relations.
  - Exports direct and bidirectional Neo4j-ready relation files.

## Step 5 - Trial Graph Freeze And Neo4j Import

- `step05_build_trial_graph_v1.py`
  - Freezes current entity/relation outputs into `trial_graph_v1`.
  - Creates Neo4j import CSVs and Cypher import scripts.
- `step05_smoke_test_graph_retrieval.py`
  - Runs graph traversal smoke checks over the trial graph files.

## Step 6 - Embeddings

- `step06_build_embeddings.py`
  - Builds embedding documents for entities, mentions, and QA records.
  - Generates multilingual MiniLM embeddings.
- `step06_smoke_test_embedding_search.py`
  - Smoke-tests vector search over generated embeddings.

## Step 8 - Medical Query Understanding

- `step08_understand_queries.py`
  - Normalizes Arabic queries.
  - Detects hard entity matches, semantic candidates, intents, and relation weights.

## Step 9 - Retrieval

- `step09a_semantic_retrieval.py`
  - Runs vector-only semantic retrieval.
- `step09c_hybrid_retrieval.py`
  - Combines Step 8 entity seeds, Step 9A semantic retrieval, and graph traversal.

## Step 10 - Subgraph Reranking

- `step10_rerank_subgraphs.py`
  - Collapses repeated relation evidence into compact ranked subgraph edges.

## Step 11 - Evidence Context Construction

- `step11_build_evidence_contexts.py`
  - Builds prompt-ready evidence bundles from reranked subgraphs.

## Step 12 - Answer Generation

- `step12_generate_answers.py`
  - Uses Groq/Qwen to generate Arabic answers from Step 11 evidence bundles.
  - Stops before claim extraction or verification.

## Cleanup Rule

Keep scripts that reproduce a pipeline step. Delete raw request/response artifacts after successful validation, but keep final CSV/JSON outputs and reports.

