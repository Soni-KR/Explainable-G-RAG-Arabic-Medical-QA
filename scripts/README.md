# Script Map

This folder follows the current Explainable Graph-RAG pipeline for Arabic medical QA on the AHD dataset. Steps 1-7 build the frozen graph and indexes. Steps 8-17 implement query understanding, retrieval, evidence-grounded generation, hallucination mitigation, reliability scoring, and final explainable output.

## Step 1 - Dataset Subset And Preprocessing

- `step01_prepare_subset.py`
  - Samples the AHD subset and records category distribution.
- `step01_preprocess_medical_normalization.py`
  - Cleans Arabic text, normalizes letters, removes noise, detects duplicates, and creates train/validation/evaluation splits.

## Step 2 - Chunking

- `step02_chunk_preprocessed.py`
  - Groups preprocessed QA rows into category/semantic chunks.
  - Keeps QA records inside each chunk for later evidence linking.

## Step 3 - Entity Extraction

- `step03_extract_entities.py`
  - Uses a Groq-hosted LLM to extract Arabic medical entities from chunks.
  - Normalizes entity names, aliases, and canonical IDs.
- `merge_entity_extractions.py`
  - Merges duplicate entity outputs when needed.

## Step 4 - Relation Extraction

- `step04_prepare_relation_candidates.py`
  - Builds candidate relation pairs from entity co-occurrence and evidence.
- `step04_validate_relations.py`
  - Uses a Groq-hosted LLM to keep/reject medical triples.
  - Produces validated relations with evidence, QA IDs, and source metadata.

## Step 5 - Graph Freeze, Supplemental Facts, And Neo4j

- `step05_build_trial_graph_v1.py`
  - Freezes entities, evidence, QA records, and relations into `outputs/05_trial_graph_v1`.
  - Creates Neo4j-ready CSVs and Cypher import scripts.
- `step05_smoke_test_graph_retrieval.py`
  - Builds Cypher smoke tests for graph retrieval.
- `step05b_derive_supplemental_facts_from_dataset.py`
  - Replaces manual supplemental facts with AHD dataset-derived provenance.
- `step05c_discover_supplemental_candidates.py`
  - Detects low-evidence/low-reliability topics and proposes candidate AHD evidence rows for human review.
  - Does not import facts automatically.
- `step05d_expand_supplemental_facts_from_failures.py`
  - Converts reviewed high-confidence AHD-backed facts into reusable supplemental entities and relations.
  - Current focused expansion adds facts for anemia diet, dental filling, post-surgery review, tooth filing risk, dyspnea/fatigue, IVF stimulation safety, and pregnancy CRP/WBC interpretation.

## Step 6 - Embeddings And Indexing

- `step06_build_embeddings.py`
  - Builds embedding documents for entities, evidence, and QA records.
  - Generates vector embeddings for semantic retrieval.
- `step06_smoke_test_embedding_search.py`
  - Smoke-tests embedding search.

## Step 8 - Medical Query Understanding

- `step08_understand_queries.py`
  - Normalizes Arabic user queries.
  - Supports `--from-qa`, `--limit`, `--offset`, `--graph-covered-only`, and `--scan-limit`.
  - Detects entities, synonym expansions, intent, relation priorities, and key medical fragments.
  - Outputs a structured query object for retrieval.

## Step 9 - Adaptive Hybrid Retrieval

- `step09a_semantic_retrieval.py`
  - Runs semantic retrieval over entity, evidence, and QA embedding documents.
  - Uses detected entities, expansion terms, and key medical fragments.
- `step09c_hybrid_retrieval.py`
  - Combines semantic retrieval, graph traversal, relation priorities, evidence expansion, and supplemental graph facts.

## Step 10 - Subgraph Re-Ranking

- `step10_rerank_subgraphs.py`
  - Ranks candidate subgraphs by semantic support, graph structure, evidence quality, relation priority, and source reliability.
  - Produces compact reranked relations and evidence.

## Step 11 - Evidence Context Construction

- `step11_build_evidence_contexts.py`
  - Builds prompt-ready context bundles.
  - Includes retrieved entities, relations, evidence sentences, QA IDs, and strict evidence-only instructions.

## Step 12 - GPT-OSS-20B Answer Generation

- `step12_generate_answers.py`
  - Generates Arabic answers using retrieved evidence context.
  - Supports Groq GPT-OSS-20B live generation, resume mode, rate-limit stopping, and evidence citations.

## Steps 13-17 - Trustworthiness Layer

- `step13_extract_claims.py`
  - Splits generated answers into factual claims.
- `step14_verify_claims.py`
  - Verifies claims against retrieved graph evidence.
  - Labels claims as supported, weakly supported, or unsupported.
- `step15_mitigate_hallucinations.py`
  - Removes unsupported claims.
  - Produces answerability labels: `answerable`, `partially_answerable`, or `insufficient_evidence`.
- `step16_score_reliability.py`
  - Computes reliability components:
    - `claim_support_rate`
    - `evidence_coverage`
    - `relation_confidence`
    - `source_reliability`
    - `hallucination_rate`
    - `overall_reliability_score`
- `step17_build_final_output.py`
  - Builds final explainable Arabic output with answer, citations, XAI relations, reliability score, and limitations.

- `step13_17_utils.py`
  - Shared helpers/constants for claim extraction, verification, mitigation, scoring, and final output.

## Recommended Evaluation Command Sequence

Use non-overlapping offsets to avoid retesting tuned questions:

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

## Metrics Tracked

- Entity extraction: Precision, Recall, F1, BERTScore F1
- Relation extraction: Candidate Recall, Triplet Precision/Recall/F1
- Retrieval: Recall@5, MRR, nDCG@10, RAGAS Context Precision/Recall
- Final answer: BERTScore F1, ROUGE-L, E5 similarity, RAGAS Faithfulness, RAGAS Answer Relevancy
- Hallucination: Claim-support rate, hallucination rate
- Reliability: AUROC/AUPRC when gold labels exist, calibration/threshold analysis
- Efficiency: average latency

## Entity Ground-Truth Evaluation

- `step03b_evaluate_entity_extraction_first100.py`
  - Converts the first-100 entity-evaluation notebook into a reproducible script.
  - Requires `ground_truth_entities_100.csv` and `llm_entities_vs_gt_100.csv` with columns: `question`, `answer`, `entity_type`, and `canonical_name`.
  - Computes canonical-name precision, recall, F1, entity-type macro precision, recall, F1, and optional BERTScore F1.

```powershell
python scripts\step03b_evaluate_entity_extraction_first100.py --limit 100
python scripts\step03b_evaluate_entity_extraction_first100.py --limit 100 --bertscore
```

Useful post-processing ablation modes:

```powershell
python scripts\step03b_evaluate_entity_extraction_first100.py --limit 100 --mode baseline
python scripts\step03b_evaluate_entity_extraction_first100.py --limit 100 --mode graph_exact_alias
python scripts\step03b_evaluate_entity_extraction_first100.py --limit 100 --mode diagnostic_gold_map
```

`diagnostic_gold_map` uses the evaluation labels and must be reported only as
an error-analysis upper bound, not as deployable model performance.

- `step03c_extract_entities_first100_prompt_ablation.py`
  - Runs GPT-OSS-20B prompt ablations on the same first-100 entity benchmark.
  - Saves raw responses, prediction CSVs, errors, and run reports under
    `outputs/03_entity_extraction/prompt_ablation_first_100/`.
  - Current prompt versions: `central_v1`, `anti_generic_v2`, and
    `candidate_rank_v3`.

```powershell
python scripts\step03c_extract_entities_first100_prompt_ablation.py --prompt-version central_v1 --limit 100 --sleep-seconds 8 --resume --stop-on-rate-limit
python scripts\step03b_evaluate_entity_extraction_first100.py --limit 100 --mode baseline --predictions outputs\03_entity_extraction\prompt_ablation_first_100\central_v1\predictions.csv --output-dir outputs\03_entity_extraction\prompt_ablation_first_100\central_v1\evaluation --report-md reports\step03c_prompt_ablation_central_v1_evaluation.md
```

## Cleanup Rule

Keep scripts, reports, final CSV/JSON outputs, Neo4j import files, and embedding/index artifacts needed to reproduce downstream steps. Do not commit `.env`, `.deps-step6/`, raw full `AHD.csv`, raw LLM request/response logs unless specifically needed, or local database dumps unless shared via release/LFS.
