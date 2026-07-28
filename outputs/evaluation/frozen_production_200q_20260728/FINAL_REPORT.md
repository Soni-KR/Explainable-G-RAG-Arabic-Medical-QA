# Frozen Two-Cohort Production Evaluation

This is the authoritative no-post-hoc-tuning evaluation of `final_v1`.
The supplemental graph, semantic claim adjudication, E5 claim calibrator,
and forced extractive fallback were disabled. Exact held-out QA matches
were excluded from both main cohorts.

## Executive Result

### Cohort A: AHD reference-answer 100

- Selected retrieval: `vector_graph_conditional_fts`
- Context: 69 non-empty / 31 empty
- Step 12: 66 generated / 34 fallback
- Final substantive answers: 24/100
- Technical failures: 3
- Raw generated-answer BERTScore F1: 0.680128 over 66 successful Step 12 answers
- Post-mitigation BERTScore F1: 0.677259 over 24 answers

### Cohort B: entity-ground-truth 100

- Selected retrieval: `vector_graph_conditional_fts`
- Context: 70 non-empty / 30 empty
- Step 12: 67 generated / 33 fallback
- Final substantive answers: 25/100
- Technical failures: 3
- Raw generated-answer BERTScore F1: 0.680691 over 67 successful Step 12 answers
- Post-mitigation BERTScore F1: 0.664972 over 25 answers

## Optional 200-Query Aggregate

- Final substantive answers: 49/200 (24.5%)
- Generated before mitigation: 133/200
- Technical failures: 6/200
- Raw generated-answer BERTScore F1: 0.680412 over 133 successful Step 12 answers
- Post-mitigation BERTScore F1: 0.67099 over 49 answers
- Reliability decisions: accept=2, flag=22, abstain=176

Retrieval scores are not pooled across 200 because the cohorts use
different independent gold judgments.

## Cohort A: AHD reference-answer 100: Retrieval

| Mode | Direct R@5* | Direct R@10* | Direct MRR | Useful Hit@5 | Judged nDCG@10 | Non-empty | Strong direct |
|---|---:|---:|---:|---:|---:|---:|---:|
| vector_only | 0.693878 | 0.857143 | 0.247722 | 78 | 0.567547 | 72 | 11 |
| graph_only | 0.000000 | 0.000000 | 0.000000 | 1 | 0.011003 | 6 | 1 |
| vector_graph | 0.693878 | 0.857143 | 0.247722 | 78 | 0.558811 | 71 | 11 |
| vector_graph_conditional_fts | 0.714286 | 0.755102 | 0.236167 | 71 | 0.536723 | 69 | 11 |
| vector_graph_conditional_fts_category_bonus | 0.714286 | 0.755102 | 0.230333 | 71 | 0.536137 | 69 | 11 |

Winner: `vector_graph_conditional_fts`. The category bonus guard passed: `False`.

`*` Direct recall uses the 49 queries with at least one human-confirmed
label-2 candidate. Human judgments are incomplete; unjudged candidates were
never converted to label 0. The frozen priority selected conditional FTS for
its higher Recall@5, despite lower Recall@10, MRR, and judged nDCG.

## Cohort A: AHD reference-answer 100: Generation and Verification

- Answerability: `{"partially_answerable": 9, "generation_unavailable": 3, "insufficient_evidence": 73, "supported_but_incomplete": 13, "fully_answerable": 2}`
- Pre-mitigation claims: 148 (support=0.25, weak=0.040541, hallucination=0.709459)
- Removed claims: 111
- Post-mitigation claims: 37 across 24 answers
- Citation validity: 1.0
- Reliability labels: `{"medium": 13, "low": 86, "high": 1}`

**Scope warning:** Post-mitigation support `1.00` and hallucination
`0.00` apply only to surviving claims in substantive answers,
not to all 100 questions.

Top removal checks:

- `claim_query_concept_mismatch`: 53
- `intent_mismatch`: 53
- `support_below_weak_threshold`: 28
- `negation_mismatch`: 17
- `number_mismatch`: 14
- `anatomy_mismatch`: 8
- `recommendation_not_supported`: 2
- `no_valid_citation`: 1

End-to-end latency:

- Mean: 17379.758 ms
- Median: 19583.087 ms
- p95: 35220.620 ms
- Total: 1737975.828 ms

## Cohort B: entity-ground-truth 100: Retrieval

| Mode | Entity R@5 | Entity MRR | Entity nDCG@10 | Gold queries | Non-empty | Strong direct |
|---|---:|---:|---:|---:|---:|---:|
| vector_only | 0.380000 | 0.268683 | 0.305375 | 75 | 72 | 23 |
| graph_only | 0.186667 | 0.152667 | 0.161059 | 75 | 10 | 3 |
| vector_graph | 0.380000 | 0.273329 | 0.305375 | 75 | 70 | 23 |
| vector_graph_conditional_fts | 0.380000 | 0.273329 | 0.305375 | 75 | 70 | 25 |
| vector_graph_conditional_fts_category_bonus | 0.380000 | 0.273329 | 0.305375 | 75 | 70 | 25 |

Winner: `vector_graph_conditional_fts`. The category bonus guard passed: `False`.

## Cohort B: entity-ground-truth 100: Generation and Verification

- Answerability: `{"insufficient_evidence": 72, "supported_but_incomplete": 13, "partially_answerable": 11, "fully_answerable": 1, "generation_unavailable": 3}`
- Pre-mitigation claims: 144 (support=0.243056, weak=0.013889, hallucination=0.743056)
- Removed claims: 109
- Post-mitigation claims: 35 across 25 answers
- Citation validity: 1.0
- Reliability labels: `{"low": 90, "medium": 9, "high": 1}`

**Scope warning:** Post-mitigation support `1.00` and hallucination
`0.00` apply only to surviving claims in substantive answers,
not to all 100 questions.

Top removal checks:

- `intent_mismatch`: 68
- `claim_query_concept_mismatch`: 31
- `support_below_weak_threshold`: 28
- `negation_mismatch`: 11
- `anatomy_mismatch`: 9
- `number_mismatch`: 7
- `recommendation_not_supported`: 1
- `no_valid_citation`: 1

End-to-end latency:

- Mean: 24039.399 ms
- Median: 34755.164 ms
- p95: 35749.694 ms
- Total: 2403939.937 ms

## Steps 8-17

1. **Step 8:** Cached normalized Arabic query analysis, medical phrase extraction, deterministic Neo4j linking, and retrieval planning.
2. **Step 9:** E5 vector retrieval, validated `final_v1` graph traversal, QA retrieval, then label-free conditional FTS when ordinary context was partial.
3. **Step 10:** The same deterministic identity-, intent-, anatomy-, concept-, source-, and contradiction-aware reranker for every ablation.
4. **Step 11:** Absolute relevance gates, deduplication, source provenance, and compact evidence-focused context.
5. **Step 12:** GPT-OSS-20B claim-first Arabic generation with strict citations and no extractive fallback.
6. **Step 13:** Deterministic extraction of atomic generated claims.
7. **Step 14:** Deterministic citation, evidence support, intent, concept, anatomy, negation, and number verification.
8. **Step 15:** Removal of weak or unsupported claims and explicit answerability assignment.
9. **Step 16:** Uncalibrated deterministic reliability scoring (`high/medium/low`).
10. **Step 17:** Explainable records joining the answer, linked entities, supporting evidence/relations, claim audit, removed claims, limitations, scores, and timings.

## Interpretation

- Vector retrieval supplied nearly all measurable retrieval value; graph-only remained weak.
- Conditional FTS modestly improved the independently judged retrieval objective and was selected for both cohorts.
- The category bonus produced no independent-metric improvement and was not selected.
- The main remaining limitation is answer coverage after deterministic verification, not post-mitigation citation validity.
- RAGAS was not added after the freeze because it requires additional judge calls and would be a separate evaluator experiment.

## Final Artifacts

- **frozen manifest:** `outputs/evaluation/frozen_production_200q_20260728/manifest.json`
- **ahd_reference_100 primary retrieval metrics:** `outputs/evaluation/retrieval/frozen_prod_ahd_reference_100_20260728/metrics.json`
- **ahd_reference_100 conditional retrieval metrics:** `outputs/evaluation/retrieval/frozen_prod_ahd_reference_100_conditional_fts_20260728/metrics.json`
- **ahd_reference_100 retrieval selection:** `outputs/evaluation/frozen_production_200q_20260728/ahd_reference_100_retrieval_selection.json`
- **ahd_reference_100 selected retrieval JSONL:** `outputs/evaluation/retrieval/frozen_prod_ahd_reference_100_conditional_fts_20260728/vector_graph_conditional_fts.jsonl`
- **ahd_reference_100 generation records:** `outputs/evaluation/generation/frozen_prod_ahd_reference_100_steps12_17_network_20260728/full_pipeline.jsonl`
- **ahd_reference_100 generation metrics:** `outputs/evaluation/generation/frozen_prod_ahd_reference_100_steps12_17_network_20260728/metrics.json`
- **ahd_reference_100 generation manifest:** `outputs/evaluation/generation/frozen_prod_ahd_reference_100_steps12_17_network_20260728/manifest.json`
- **ahd_reference_100 claim audit:** `outputs/evaluation/claim_audit/frozen_prod_ahd_reference_100_steps12_17_network_20260728/full_pipeline.jsonl`
- **ahd_reference_100 resumable Step 12 cache:** `outputs/evaluation/cache/frozen_prod_ahd_reference_100_steps12_17_network_20260728/step12_success.jsonl`
- **ahd_reference_100 Step 17 explainable output:** `outputs/evaluation/frozen_production_200q_20260728/ahd_reference_100_step17_explainable.jsonl`
- **ahd_reference_100 excluded sandbox-network preflight:** `outputs/evaluation/generation/frozen_prod_ahd_reference_100_steps12_17_20260728`
- **entity_ground_truth_100 primary retrieval metrics:** `outputs/evaluation/retrieval/frozen_prod_entity_gt_100_20260728/metrics.json`
- **entity_ground_truth_100 conditional retrieval metrics:** `outputs/evaluation/retrieval/frozen_prod_entity_gt_100_conditional_fts_20260728/metrics.json`
- **entity_ground_truth_100 retrieval selection:** `outputs/evaluation/frozen_production_200q_20260728/entity_ground_truth_100_retrieval_selection.json`
- **entity_ground_truth_100 selected retrieval JSONL:** `outputs/evaluation/retrieval/frozen_prod_entity_gt_100_conditional_fts_20260728/vector_graph_conditional_fts.jsonl`
- **entity_ground_truth_100 generation records:** `outputs/evaluation/generation/frozen_prod_entity_gt_100_steps12_17_network_20260728/full_pipeline.jsonl`
- **entity_ground_truth_100 generation metrics:** `outputs/evaluation/generation/frozen_prod_entity_gt_100_steps12_17_network_20260728/metrics.json`
- **entity_ground_truth_100 generation manifest:** `outputs/evaluation/generation/frozen_prod_entity_gt_100_steps12_17_network_20260728/manifest.json`
- **entity_ground_truth_100 claim audit:** `outputs/evaluation/claim_audit/frozen_prod_entity_gt_100_steps12_17_network_20260728/full_pipeline.jsonl`
- **entity_ground_truth_100 resumable Step 12 cache:** `outputs/evaluation/cache/frozen_prod_entity_gt_100_steps12_17_network_20260728/step12_success.jsonl`
- **entity_ground_truth_100 Step 17 explainable output:** `outputs/evaluation/frozen_production_200q_20260728/entity_ground_truth_100_step17_explainable.jsonl`

The known-answer exact-QA artifact remains an upper-bound diagnostic
and is excluded from selection, main metrics, and the 200-query aggregate.
