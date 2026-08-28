# MG-Retriever: Explainable Arabic Medical Graph-RAG

MG-Retriever builds an Arabic medical knowledge graph and answers questions with
hybrid retrieval, grounded generation, claim verification, reliability scoring,
and source citations.

> Research prototype only. It does not replace professional medical care.

## Architecture

```text
AHD data
  -> 01 sampling and medical normalization
  -> 02 evidence-aware chunking
  -> 03 LLM medical entity extraction
  -> 04 candidate relation generation and LLM validation
  -> 05 Neo4j graph construction
  -> 06 multilingual E5 embeddings
  -> 08 Arabic query understanding and entity linking
  -> 09 hybrid vector, graph, and optional QA retrieval
  -> 10 reranking
  -> 11 evidence context construction
  -> 12 grounded answer generation
  -> 13-15 claim verification and hallucination mitigation
  -> 16-17 reliability, citations, and explainable output
```

## Repository

The numbered modules under `src/` form the reproducible pipeline. `run.py` runs
Steps 8-17, while `build_qa_index.py` optionally builds the local QA retrieval
index. Datasets, graph exports, embeddings, evaluation cohorts, and generated
results are excluded from GitHub for licensing and privacy reasons.

## Setup

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Set `GROQ_API_KEY` and `NEO4J_PASSWORD` in `.env`.

## Build The Graph

Place the authorized AHD CSV at `data/raw/AHD.csv`. Then run:

```powershell
python src\step01_sample_dataset.py --target-rows 10000
python src\step01_normalize_dataset.py
python src\step02_create_chunks.py
python src\step03_extract_entities.py --run-live --resume --stop-on-rate-limit
python src\step04_generate_relation_candidates.py
python src\step04_validate_relations.py --run-live --resume --stop-on-rate-limit
```

The sampling stage supports held-out evaluation and existing-graph exclusion
files. Steps 3 and 4 cache successful Groq responses and resume interrupted runs.

Prepare the validated graph CSV contract under `outputs/production_graph/`, then
start Neo4j, import the graph, and build its vector indexes:

```powershell
docker compose up -d neo4j
python src\step05_import_graph.py --dry-run
python src\step05_import_graph.py --execute --batch-size 500
python src\step06_build_embeddings.py --graph-version final_v2 --execute --batch-size 32
```

The graph version is configurable through `.env`; `final_v2` is retained only as
the published snapshot identifier for provenance compatibility.

## Run The System

```powershell
python run.py --query "ما علاج الربو؟"
```

Use `--context-only` to inspect retrieval and evidence selection without calling
the answer-generation model.

## Optional QA Retrieval

```powershell
python build_qa_index.py `
  --source data\raw\AHD.csv `
  --split-source path\to\qa_split.csv `
  --execute
```

Without this index, the system continues with Neo4j graph and vector retrieval.

## Privacy

Never commit `.env`, API keys, AHD records, graph dumps, populated evaluation
files, embeddings, or generated medical answers. Confirm dataset licensing and
institutional approval before making any associated artifact public.
