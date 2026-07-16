# Explainable Graph-RAG For Arabic Medical QA

This repository contains an Arabic medical Graph-RAG pipeline for the AHD dataset. The current implementation extends the original retrieval architecture with evidence-focused context construction, Qwen answer generation, claim verification, hallucination mitigation, reliability scoring, and final explainable output.

The project follows the architecture in `mix.png`, with a frozen `trial_graph_v1` stored under `outputs/05_trial_graph_v1/`.

## Current Status

Completed:

- Steps 1-7: dataset preprocessing, chunking, entity/relation extraction, graph construction, embeddings, and Neo4j-ready graph files.
- Step 8: Arabic medical query understanding with normalization, synonym expansion, intent detection, and key medical fragments.
- Step 9: semantic + graph hybrid retrieval.
- Step 10: subgraph reranking.
- Step 11: evidence-focused context construction.
- Step 12: Qwen answer generation.
- Step 13: claim extraction.
- Step 14: graph-based fact verification.
- Step 15: hallucination mitigation.
- Step 16: reliability scoring.
- Step 17: final explainable Arabic output.

Additional improvement:

- Dataset-derived supplemental facts.
- Candidate discovery for low-evidence failures.
- Focused supplemental graph expansion from AHD-backed facts.

## Repository Layout

- `scripts/`
  - Step-numbered Python scripts.
  - See `scripts/README.md` for the detailed script map.
- `outputs/05_trial_graph_v1/`
  - Frozen graph, embeddings, retrieval outputs, context bundles, generated answers, verification outputs, reliability scores, and final explainable outputs.
- `reports/`
  - Markdown reports for each major stage.
- `requirements-step6-embeddings.txt`
  - Local embedding/search dependencies.
- `.env.example`
  - Local environment template.

## Setup

Create a local `.env` from `.env.example`:

```powershell
Copy-Item .env.example .env
```

Then add your own keys locally:

```text
GROQ_API_KEY=your_key_here
```

Install embedding dependencies only if you need to rebuild Step 6/9A:

```powershell
python -m pip install --target .deps-step6 -r requirements-step6-embeddings.txt
```

## Neo4j

The main graph import files are in:

```text
outputs/05_trial_graph_v1/import/
```

Supplemental graph facts are in:

```text
outputs/05_trial_graph_v1/supplemental_facts/
```

To import supplemental facts into an existing Neo4j container:

```powershell
$container = "ahd-neo4j-final"

docker cp outputs\05_trial_graph_v1\supplemental_facts\trial_graph_v1_supplemental_entities.csv "${container}:/var/lib/neo4j/import/trial_graph_v1_supplemental_entities.csv"
docker cp outputs\05_trial_graph_v1\supplemental_facts\trial_graph_v1_supplemental_relations.csv "${container}:/var/lib/neo4j/import/trial_graph_v1_supplemental_relations.csv"
docker cp outputs\05_trial_graph_v1\supplemental_facts\trial_graph_v1_supplemental_qa_sources.csv "${container}:/var/lib/neo4j/import/trial_graph_v1_supplemental_qa_sources.csv"
docker cp outputs\05_trial_graph_v1\supplemental_facts\import_supplemental_medical_facts.cypher "${container}:/var/lib/neo4j/import/import_supplemental_medical_facts.cypher"
docker exec -it $container cypher-shell -u neo4j -p "YOUR_PASSWORD" -f /var/lib/neo4j/import/import_supplemental_medical_facts.cypher
```

Expected supplemental relation count after the focused expansion:

```cypher
MATCH ()-[r:MEDICAL_RELATION]->()
WHERE r.is_supplemental = true
RETURN count(r) AS supplemental_relations;
```

Expected:

```text
26
```

## Run The Current Evaluation Pipeline

Use non-overlapping offsets to avoid retesting tuned questions. Example fresh batch:

```powershell
python scripts\step08_understand_queries.py --from-qa --limit 50 --offset 75 --graph-covered-only --scan-limit 700
python scripts\step09a_semantic_retrieval.py --top-k 25
python scripts\step09c_hybrid_retrieval.py --top-relations 50 --top-contexts 30
python scripts\step10_rerank_subgraphs.py
python scripts\step11_build_evidence_contexts.py
python scripts\step12_generate_answers.py --run-live --provider groq --force-overwrite --limit 50 --model qwen/qwen3-32b --sleep-seconds 60 --stop-on-rate-limit
python scripts\step13_extract_claims.py
python scripts\step14_verify_claims.py
python scripts\step15_mitigate_hallucinations.py
python scripts\step16_score_reliability.py
python scripts\step17_build_final_output.py
```

Summarize final metrics:

```powershell
python -c "import csv,collections; rows=list(csv.DictReader(open('outputs/05_trial_graph_v1/final_output/trial_graph_v1_final_explainable_output.csv',encoding='utf-8-sig'))); print('rows',len(rows)); print(collections.Counter(r['answerability_label'] for r in rows)); print(collections.Counter(r['reliability_label'] for r in rows)); print('avg reliability',sum(float(r['overall_reliability_score']) for r in rows)/len(rows)); print('avg hallucination',sum(float(r['hallucination_rate']) for r in rows)/len(rows)); print('avg support',sum(float(r['claim_support_rate']) for r in rows)/len(rows))"
```

## Metrics

- Entity extraction: Precision, Recall, F1, BERTScore F1.
- Relation extraction: Candidate Recall, Triplet Precision/Recall/F1.
- Retrieval: Recall@5, MRR, nDCG@10, RAGAS Context Precision/Recall.
- Final answer: BERTScore F1, ROUGE-L, E5 similarity, RAGAS Faithfulness, RAGAS Answer Relevancy.
- Hallucination: Claim-support rate, hallucination rate.
- Reliability: AUROC/AUPRC when gold labels exist, calibration/threshold analysis.
- Efficiency: average latency.

## Do Not Commit

Do not commit:

- `.env`
- `.deps-step6/`
- `AHD.csv`
- `neo4j.dump`
- `neo4j_dump/`
- raw LLM request/response logs
- Python cache files

Large local files such as `neo4j.dump` should be shared separately through a release asset, Git LFS, or cloud storage.
