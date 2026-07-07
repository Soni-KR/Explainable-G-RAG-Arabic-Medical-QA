# Arabic Medical Graph-RAG Trial

This repository contains a trial implementation of an Arabic medical Graph-RAG pipeline based on the `mix.png` architecture.

Current stop point: Step 12 answer generation on `trial_graph_v1`.

Step 13 claim extraction / verification has not been run yet.

## Folder Structure

- `scripts/`
  - Step-numbered Python scripts ordered by the pipeline.
  - See `scripts/README.md` for the full script map.
- `reports/`
  - Markdown reports explaining each completed stage.
- `outputs/05_trial_graph_v1/`
  - Frozen trial graph and important outputs from Step 5 to Step 12.
  - See `outputs/05_trial_graph_v1/README.md`.
- `outputs/01_preprocessing/` to `outputs/04_relation_extraction/`
  - Important final preprocessing, chunking, entity, and relation outputs.
- `requirements-step6-embeddings.txt`
  - Embedding dependencies.
- `.env.example`
  - Template for local API keys.

## Do Not Commit

- `.env`
- `.deps-step6/`
- Raw full dataset files such as `AHD.csv`
- Raw LLM response logs
- Request JSONL files
- Python cache files

These are covered in `.gitignore`.

## Setup

Create `.env` locally:

```text
GROQ_API_KEY=your_key_here
```

Install Step 6 embedding dependencies if embeddings need to be regenerated:

```powershell
python -m pip install --target .deps-step6 -r requirements-step6-embeddings.txt
```

## Current Trial Output

The most important current artifacts are:

- `outputs/05_trial_graph_v1/import/`
  - Neo4j-ready entity, evidence, QA, and relation CSVs.
- `outputs/05_trial_graph_v1/embeddings/`
  - Embedding documents, vectors, and metadata.
- `outputs/05_trial_graph_v1/context_construction/`
  - Step 11 evidence context bundles.
- `outputs/05_trial_graph_v1/answer_generation/`
  - Step 12 Qwen-generated answers.

## Next Step

Continue with Step 13 from `mix.png`:

Claim extraction from the Step 12 generated answers, followed by verification and hallucination mitigation.
