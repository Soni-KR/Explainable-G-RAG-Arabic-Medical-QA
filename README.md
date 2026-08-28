# MG-Retriever: Explainable Arabic Medical Graph-RAG

MG-Retriever answers Arabic medical questions using a frozen Neo4j knowledge
graph, multilingual E5 retrieval, grounded LLM generation, claim verification,
hallucination mitigation, reliability scoring, and evidence citations.

> Research prototype only. It is not a medical device and must not replace
> professional diagnosis or treatment.

## Pipeline

```text
Arabic query
  -> query understanding and entity linking
  -> vector, graph, and optional QA retrieval
  -> evidence reranking and context selection
  -> grounded answer generation
  -> claim verification and hallucination mitigation
  -> answer, citations, reliability, and provenance
```

## Files

```text
run.py               Run the complete pipeline
build_qa_index.py    Optionally build the held-out-safe QA search index
src/                 Final-v2 graph, retrieval, generation, and verification code
.env.example         Required environment variables
docker-compose.yml   Local Neo4j service
requirements.txt     Python dependencies
```

Datasets, graph dumps, embeddings, evaluation files, generated outputs, tests, and
research experiments are intentionally not stored in this public repository.

## Setup

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Set `GROQ_API_KEY` and `NEO4J_PASSWORD` in `.env`.

## Prepare Neo4j

Start the final-v2 Neo4j service:

```powershell
docker compose up -d neo4j-final-v2
```

Obtain the authorized `final_v2_graph_csv.zip` artifact and extract it to
`outputs/final_graph_v2/`, then import and embed it:

```powershell
python src\step05e_import_final_v2.py --dry-run
python src\step05e_import_final_v2.py --execute --batch-size 500
python src\step06_build_embedding_indexes.py --graph-version final_v2 --execute --batch-size 32
```

## Run

```powershell
python run.py --query "ما علاج الربو؟"
```

Use `--context-only` to stop before answer generation:

```powershell
python run.py --query "ما علاج الربو؟" --context-only
```

## Optional QA Index

The QA channel requires an authorized AHD CSV and a split file identifying held-out
evaluation questions:

```powershell
python build_qa_index.py `
  --source data\raw\AHD.csv `
  --split-source path\to\qa_split.csv `
  --execute
```

Without this local index, the system still uses Neo4j graph and vector retrieval.

## Privacy

Never commit `.env`, API keys, AHD records, populated evaluation cohorts, Neo4j
dumps, generated embeddings, or model outputs. Confirm licensing with the project
authors and institution before changing repository visibility.
