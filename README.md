# Explainable Graph-RAG For Arabic Medical QA

This repository contains an Arabic medical Graph-RAG pipeline for the AHD dataset. The current implementation extends the original retrieval architecture with evidence-focused context construction, GPT-OSS-20B answer generation, claim verification, hallucination mitigation, reliability scoring, and final explainable output.

The project follows the architecture in `mix.png`, with a frozen `trial_graph_v1` stored under `outputs/05_trial_graph_v1/`.

## Best Pipeline Handover

This repository is prepared so a teammate can start from the current best
retrieval-and-generation pipeline without repeating the debugging work. The
recommended configuration is the conservative category-aware QA fallback run:

```text
Model: openai/gpt-oss-20b
Evaluation set: retrieval_gold_annotations_unseen_100_random_seed20260728.csv
QA fallback threshold: 0.42
QA fallback category bonus: 0.08
QA fallback scoring mode: question
Hallucination mitigation: remove unsupported claims
Selected result: BERTScore F1 = 0.655481, 100/100 answerable, hallucination = 0.0
```

Do not use the later `question_answer` fallback experiment as the main
pipeline. It was tested and recorded, but it reduced BERTScore and
answerability.

### What Is Included

The handover includes:

- Step 8-17 scripts needed to run retrieval, generation, verification,
  hallucination mitigation, reliability scoring, and final output construction.
- Supplemental AHD-backed fact CSVs and their Neo4j import Cypher script.
- The selected final explainable output under
  `outputs/05_trial_graph_v1/final_output/`.
- The selected unseen-100 evaluation files under
  `outputs/05_trial_graph_v1/evaluation/`.
- Experiment summaries in `README_EXPERIMENTS.md` and `reports/`.

The handover does not include:

- `.env` or any API keys.
- `AHD.csv`, because it is a raw/local dataset file.
- `neo4j.dump`, because it is large and should be sent separately if needed.
- Raw LLM response logs.
- Local dependency folders such as `.deps-step6/`, `.bsdeps/`, or `.uv-cache/`.

### Files Your Teammate Should Know First

| File or Folder | Purpose |
|---|---|
| `README_EXPERIMENTS.md` | Full experiment log with metrics, ablations, successes, and failed attempts. |
| `retrieval_gold_annotations_unseen_100_random_seed20260728.csv` | The selected random unseen 100-question test set used for the best run. |
| `outputs/05_trial_graph_v1/final_output/trial_graph_v1_final_explainable_output.csv` | Current selected final answers, citations, reliability labels, and answerability labels. |
| `outputs/05_trial_graph_v1/evaluation/unseen100_random_seed20260728_category_aware_fallback_t042_b008_live_groq_full_100.csv` | Per-question BERTScore for the selected best run. |
| `outputs/05_trial_graph_v1/evaluation/unseen100_random_seed20260728_category_aware_fallback_t042_b008_live_groq_full_100_summary.json` | Summary BERTScore metrics for the selected best run. |
| `outputs/05_trial_graph_v1/supplemental_facts/` | Supplemental AHD-backed graph facts and provenance files. |
| `reports/unseen100_random_error_analysis_report.md` | Error analysis and fallback ablation results. |

### Reproduce The Selected Best Run

Before running, create `.env` locally from `.env.example` and add a Groq key or
comma-separated key rotation list:

```powershell
Copy-Item .env.example .env
```

Then run the selected pipeline from the repository root:

```powershell
python scripts\step08_understand_queries.py --query-csv retrieval_gold_annotations_unseen_100_random_seed20260728.csv --query-column query --query-id-column query_id --limit 100
python scripts\step09a_semantic_retrieval.py --top-k 25
python scripts\step09c_hybrid_retrieval.py --top-relations 80 --top-contexts 40
python scripts\step10_rerank_subgraphs.py --top-subgraph-edges 8
python scripts\step11_build_evidence_contexts.py --qa-fallback-min-score 0.42 --query-metadata-csv retrieval_gold_annotations_unseen_100_random_seed20260728.csv --query-metadata-id-col query_id --query-metadata-category-col category --qa-fallback-category-bonus 0.08
python scripts\step12_generate_answers.py --run-live --provider groq --force-overwrite --limit 100 --model openai/gpt-oss-20b --sleep-seconds 15 --stop-on-rate-limit
python scripts\step13_extract_claims.py
python scripts\step14_verify_claims.py
python scripts\step15_mitigate_hallucinations.py
python scripts\step16_score_reliability.py
python scripts\step17_build_final_output.py
python scripts\calculate_final_bertscore.py --reference-csv retrieval_gold_annotations_unseen_100_random_seed20260728.csv --reference-query-id-col query_id --reference-query-col query --reference-answer-col reference_answer --output-prefix teammate_reproduced_best_pipeline
```

Expected selected-run reference metrics:

```text
Rows: 100
BERTScore P/R/F1: 0.651960 / 0.661303 / 0.655481
Answerability: 100 answerable
Reliability labels: 62 high, 36 medium, 2 low
Claim support: 1.0
Hallucination: 0.0
```

If `python` resolves to the broken Windows Store alias, use a real Python
environment or run through `uv`:

```powershell
$env:UV_CACHE_DIR = ".uv-cache"
uv run python scripts\step08_understand_queries.py --query-csv retrieval_gold_annotations_unseen_100_random_seed20260728.csv --query-column query --query-id-column query_id --limit 100
```

## Current Status

Completed:

- Steps 1-7: dataset preprocessing, chunking, entity/relation extraction, graph construction, embeddings, and Neo4j-ready graph files.
- Step 8: Arabic medical query understanding with normalization, synonym expansion, intent detection, and key medical fragments.
- Step 9: semantic + graph hybrid retrieval.
- Step 10: subgraph reranking.
- Step 11: evidence-focused context construction.
- Step 12: GPT-OSS-20B answer generation.
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
python scripts\step12_generate_answers.py --run-live --provider groq --force-overwrite --limit 50 --model openai/gpt-oss-20b --sleep-seconds 60 --stop-on-rate-limit
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

### Entity Extraction Ground Truth

If the first-100 entity ground-truth files from `entity_evaluation_first_100_done.ipynb`
are available, place them beside the repository root with these names:

```text
ground_truth_entities_100.csv
llm_entities_vs_gt_100.csv
```

Then run:

```powershell
python scripts\step03b_evaluate_entity_extraction_first100.py --limit 100
```

To include BERTScore F1, install `bert_score` and `torch`, then add `--bertscore`.

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
