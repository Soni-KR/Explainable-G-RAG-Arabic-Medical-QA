# Entity Ground-Truth Trial: 100 Queries

This trial is separate from evaluation-v1. It uses the first 100 unique questions in `ground_truth_entities_100.csv`, retains all 119 human entity annotations attached to them, and evaluates the unchanged frozen `final_v1` pipeline. Exact normalized question matches are removed from retrieval.

## Cohort

- Queries: **100**
- Entity annotations: **119**
- Queries with mapped final_v1 entity IDs: **75**
- Queries without a conservative entity-ID mapping: **25**
- Mapping status: `{"mapped": 88, "unresolved": 30, "duplicate_family_resolved": 1}`

Entity retrieval scores therefore cover 75 queries. Evidence, QA, and relation Recall/MRR/nDCG are unavailable because the source ground truth contains entity names/types only.

## Retrieval

| Mode | Scored queries | Recall@5 | MRR | nDCG@10 | Mean latency ms |
|---|---:|---:|---:|---:|---:|
| `lexical_only` | 75 | 0.406667 | 0.296963 | 0.332427 | 5147.00 |
| `vector_only` | 75 | 0.380000 | 0.268683 | 0.305375 | 1106.67 |
| `graph_only` | 75 | 0.186667 | 0.155556 | 0.163491 | 44.72 |
| `hybrid_without_reranking` | 75 | 0.380000 | 0.273329 | 0.305375 | 1081.86 |
| `full_hybrid` | 75 | 0.380000 | 0.273329 | 0.305375 | 1176.25 |

Lexical-only retrieval performed best on entity identity in this cohort. Full hybrid did not improve over vector-only, and graph-only remained the weakest mode.

## Generation

| Outcome | Count |
|---|---:|
| Generated | 66 |
| Fallback | 34 |
| Insufficient-evidence fallback | 31 |
| Technical failure | 3 |
| Substantive claim-bearing answer | 25 |
| Fully answerable | 5 |
| Partially answerable | 7 |
| Supported but incomplete | 13 |
| Insufficient evidence | 72 |
| Generation unavailable | 3 |

## Answer Similarity

The original AHD answer is the dataset reference, not clinician-adjudicated answer gold.

| Scope | Queries | Precision | Recall | BERTScore F1 |
|---|---:|---:|---:|---:|
| All outcomes | 100 | 0.672416 | 0.651184 | 0.660892 |
| Generated responses | 66 | 0.677285 | 0.652141 | 0.663703 |
| Substantive answers | 25 | 0.691689 | 0.663460 | 0.676088 |

## Claims And Mitigation

Before mitigation there were **122** claims: 38 supported, 6 weakly supported, and 78 unsupported.

Step 15 retained **38** and removed **84** claims.

Post-mitigation claim support is **1.00**, hallucination rate **0.00**, and citation validity **1.00**. These values apply only to the **25 substantive claim-bearing answers**, not all 100 questions.

## Reliability

- Labels: `{"low": 86, "medium": 13, "high": 1}`
- Mean: `0.153458`
- Median: `0.000000`
- Range: `0.000000` to `0.807159`

## Latency

| Stage | Mean ms | Median ms | p95 ms | Total ms |
|---|---:|---:|---:|---:|
| `end_to_end` | 10263.06 | 11852.62 | 22430.03 | 1026306.10 |
| `step08_query_understanding` | 0.00 | 0.00 | 0.00 | 0.00 |
| `step08_retrieval_planning` | 0.00 | 0.00 | 0.00 | 0.00 |
| `step09_hybrid_retrieval` | 0.00 | 0.00 | 0.00 | 0.00 |
| `step10_subgraph_reranking` | 106.93 | 56.28 | 456.74 | 10693.22 |
| `step11_context_construction` | 106.22 | 46.10 | 400.05 | 10622.36 |
| `step12_answer_generation` | 7974.87 | 5986.20 | 21144.96 | 797486.89 |
| `step13_claim_extraction` | 0.04 | 0.03 | 0.12 | 3.94 |
| `step14_claim_verification` | 7.93 | 2.34 | 37.91 | 792.78 |
| `step15_hallucination_mitigation` | 0.53 | 0.22 | 1.59 | 53.07 |
| `step16_reliability_scoring` | 0.03 | 0.02 | 0.07 | 2.63 |

## Artifacts

- Cohort: `data/evaluation/entity_ground_truth_trial_100.csv`
- Mapping audit: `data/evaluation/entity_ground_truth_trial_100_mapping.csv`
- Cohort manifest: `data/evaluation/entity_ground_truth_trial_100_manifest.json`
- Step 8 cache: `outputs/evaluation/cache/entity_ground_truth_trial_100/step08_success.jsonl`
- Retrieval: `outputs/evaluation/retrieval/entity_gt_trial_100_retrieval_v1/`
- Generation: `outputs/evaluation/generation/entity_gt_trial_100_generation_v1/`
- Claim audit: `outputs/evaluation/claim_audit/entity_gt_trial_100_generation_v1/`
- Generation cache: `outputs/evaluation/cache/entity_gt_trial_100_generation_v1/`
- This report: `outputs/evaluation/entity_gt_trial_100/RESULTS.md`
