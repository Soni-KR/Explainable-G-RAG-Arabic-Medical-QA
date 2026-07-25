# Final Evaluation Results

This is the consolidated record for the frozen `final_v1` graph and the 100-query `retrieval_v2` generation run. It is generated only from retained artifacts; no API, Neo4j, retrieval, or model call is made by the compiler.

## Final graph

| Artifact | Count |
|---|---:|
| Medical entities | 2,175 |
| Evidence mentions | 5,767 |
| Relation decisions | 3,392 |
| Direct relations | 1,404 |
| Bidirectional Neo4j relations | 2,808 |
| QA records | 2,549 |

The 1,404 accepted direct relations came from 3,392 audited relation decisions, an acceptance yield of 41.39%. This is an extraction/validation yield, not Triplet Precision; independent relation gold does not yet exist.

## Retrieval candidate coverage

| Metric | Before expansion | After expansion |
|---|---:|---:|
| Queries with a direct label-2 candidate | 37/99 | 49/99 |
| End-to-end direct candidate coverage | 37/100 | 49/100 |
| Direct Recall@5 | 36.36% | 38.38% |
| Direct Recall@10 | not measured | 41.41% |
| MRR, direct candidates | 0.2279 | 0.2441 |
| nDCG@5 by raw pool rank | 0.5835 | 0.4643 |

The nDCG@5 decrease is not interpreted as degradation because original and expansion pool ranks were produced by different retrieval passes and are not directly comparable. The targeted expansion reviewed 412 candidates, rescued 12 of 44 partial-only queries, and achieved 31.80% useful yield and 2.91% direct yield.

The frozen conditional artifact processed all 44 target queries, fired on 27 queries, used 483 available raw expansion candidates, and passed every integrity check. It used neither human labels during construction nor the supplemental graph.

### Original retrieval-channel labels

| Channel | Candidates | Label 0 | Label 1 | Label 2 | Useful yield | Direct yield |
|---|---:|---:|---:|---:|---:|---:|
| `fts_qa` | 196 | 99 | 65 | 32 | 49.49% | 16.33% |
| `graph` | 3 | 3 | 0 | 0 | 0.00% | 0.00% |
| `graph_relation` | 45 | 43 | 2 | 0 | 4.44% | 0.00% |
| `vector` | 296 | 190 | 90 | 16 | 35.81% | 5.41% |

FTS QA produced the highest direct yield. Neither graph channel produced a label-2 candidate in the original 540-candidate human review.

## Retrieval latency ablation

| Mode | Retrieval ms | End-to-end with shared Step 8 ms |
|---|---:|---:|
| `lexical_only` | 5634.14 | 6186.96 |
| `vector_only` | 81.13 | 633.95 |
| `graph_only` | 16.49 | 569.31 |
| `hybrid_without_reranking` | 92.76 | 645.58 |
| `full_hybrid` | 121.55 | 674.36 |

These ablation results measured latency only. Their Recall/MRR/nDCG fields were unavailable at run time because the human relevance pool had not yet been frozen.

## Reranker experiment

| Metric | Existing rank | Two-stage grouped OOF |
|---|---:|---:|
| nDCG@5 | 0.4677 | 0.5700 |
| MRR | 0.2422 | 0.2901 |
| Direct at rank 1 | 15 | 20 |
| Useful at rank 1 | 50 | 59 |
| Direct retained in top 5 | 38 | 40 |
| Useful precision@3 | 0.4175 | 0.4949 |

Classification scores: usable-vs-irrelevant AUROC 0.7164, AUPRC 0.5873, F1 0.5900; direct-vs-all AUROC 0.7323, AUPRC 0.1936.

**Decision:** the learned reranker remains disabled. OOF ranking improved, but production-style context replay did not demonstrate a sufficiently reliable gain.

## Step 11 context selection

| Metric | Baseline | Targeted FTS |
|---|---:|---:|
| Queries with context | 70 | 73 |
| Queries with known useful context | 51 | 56 |
| Queries with known direct context | 25 | 29 |
| Useful-candidate precision | 57.06% | 59.62% |
| Direct-candidate precision | 20.25% | 18.27% |

Targeted FTS improved useful and direct query coverage. Direct-candidate precision decreased because more partial evidence was admitted, so Step 11 still needs better directness gating.

## Final 100-query generation

Run: `full_pipeline_retrieval_v2_targeted_fts_reranked_network_v1`

| Metric | Result |
|---|---:|
| Completed queries | 100 |
| LLM-generated responses | 66 |
| Fallback responses | 34 |
| Insufficient-evidence fallbacks | 30 |
| Technical failures | 4 |
| Queries with non-empty Step 11 context | 70 |
| Queries retaining verified claims | 26 |
| Fully answerable | 2 |
| Supported but incomplete | 20 |
| Partially answerable | 4 |
| Insufficient evidence | 70 |
| Generation unavailable | 4 |
| Average query coverage, all 100 | 8.83% |
| Average query coverage, substantive answers (n=26) | 33.96% |
| Post-mitigation claim support | 100.00% |
| Post-mitigation hallucination rate | 0.00% |
| Citation validity | 100.00% |
| Claims with a valid citation | 100.00% |

**Scope warning:** the post-mitigation claim-support rate of `1.00`, hallucination rate of `0.00`, and citation validity of `1.00` apply only to the **26 substantive claim-bearing answers**, containing 36 retained claims. They are not results over all 100 questions.

Before mitigation, generation produced 114 claims: 36 supported, 3 weakly supported, and 75 unsupported. Step 15 removed 78 claims (68.42%). This explains the high safety but low answer coverage.

### Generated-only versus end-to-end

| Metric | Generated-only | All 100 queries |
|---|---:|---:|
| Queries | 66 | 100 |
| Queries retaining substantive claims | 26 | 26 |
| Substantive-answer rate | 39.39% | 26.00% |
| Retained claims | 36 | 36 |
| Average query coverage | 13.38% | 8.83% |
| Mean end-to-end latency | 22363.96 ms | 15602.01 ms |
| Median end-to-end latency | 20521.31 ms | 19853.59 ms |
| p95 end-to-end latency | 30184.47 ms | 30175.35 ms |
| Total recorded latency | 1476021.19 ms | 1560201.02 ms |
| BERTScore F1 | 0.665957 | 0.660743 |

BERTScore uses the original AHD answer associated with each query as the dataset reference. It was calculated offline from the frozen answers; it did not rerun retrieval or generation. The references are not clinician-adjudicated.

### Offline reference metrics

| Scope | Queries | BERTScore precision | Recall | F1 |
|---|---:|---:|---:|---:|
| All frozen outcomes | 100 | 0.675635 | 0.647052 | 0.660743 |
| LLM-generated outcomes | 66 | 0.680636 | 0.652505 | 0.665957 |
| Substantive claim-bearing answers | 26 | 0.688926 | 0.664069 | 0.675803 |

RAGAS context recall, context precision, faithfulness, and answer relevancy are implemented as a resumable post-hoc evaluation over the same frozen records. Their evaluator-LLM run is incomplete because the configured Groq quota stopped it (`status=rate_limited`). Partial judge scores are intentionally not presented as final metrics.

### Claim removal

| Removal classification | Count |
|---|---:|
| `unsupported` | 75 |
| `weakly_supported` | 3 |

| Failed verification check | Removed claims affected |
|---|---:|
| `intent_mismatch` | 37 |
| `claim_query_concept_mismatch` | 33 |
| `support_below_weak_threshold` | 15 |
| `anatomy_mismatch` | 9 |
| `negation_mismatch` | 8 |
| `number_mismatch` | 5 |
| `no_valid_citation` | 1 |
| `recommendation_not_supported` | 1 |

A removed claim can fail more than one check, so failed-check counts can sum to more than the 78 removed claims.

### Empty versus non-empty context

| Outcome | Empty context | Non-empty context |
|---|---:|---:|
| Queries | 30 | 70 |
| Generated | 0 | 66 |
| Fallback | 30 | 4 |
| Substantive claim-bearing answer | 0 | 26 |
| Final insufficient evidence | 30 | 40 |
| Generation unavailable | 0 | 4 |

Failure attribution: 30 queries failed upstream with empty retrieval context; 4 had API/generation technical failures despite context (4 provider response-schema validation failures); and 40 received generated text but no claim survived verification/mitigation.

### Reliability and disposition

| Reliability band | Audit disposition | Count |
|---|---|---:|
| High, score >= 0.80 | accept | 3 |
| Medium, 0.55 <= score < 0.80 | flag | 9 |
| Low, score < 0.55 | abstain | 88 |

Mean reliability was 0.1592; minimum 0.0000; maximum 0.8250. The accept/flag/abstain mapping is an audit interpretation of the existing high/medium/low bands, not a new pipeline rule. Scores are uncalibrated.

### Final latency

| Stage | Mean ms | Median ms | p95 ms | Total ms |
|---|---:|---:|---:|---:|
| `end_to_end` | 15602.01 | 19853.59 | 30175.35 | 1560201.02 |
| `step08_query_understanding` | 0.00 | 0.00 | 0.00 | 0.00 |
| `step08_retrieval_planning` | 0.00 | 0.00 | 0.00 | 0.00 |
| `step09_hybrid_retrieval` | 0.00 | 0.00 | 0.00 | 0.00 |
| `step10_subgraph_reranking` | 72.25 | 62.96 | 144.57 | 7225.38 |
| `step11_context_construction` | 84.75 | 68.20 | 187.10 | 8474.93 |
| `step12_answer_generation` | 2874.56 | 772.19 | 19964.28 | 287456.47 |
| `step13_claim_extraction` | 0.03 | 0.03 | 0.08 | 2.97 |
| `step14_claim_verification` | 5.34 | 1.99 | 21.79 | 533.80 |
| `step15_hallucination_mitigation` | 0.75 | 0.30 | 3.44 | 74.71 |
| `step16_reliability_scoring` | 0.02 | 0.02 | 0.03 | 2.03 |

The end-to-end timing includes local processing, API time, configured request pacing, and retries captured inside each query record. Reused frozen Step 8 and retrieval stages are recorded as zero in this generation-only run. The total is the sum of recorded per-query timings and excludes downtime between manual resume commands and waiting for daily quota resets.

## Steps 8-17 in the frozen pipeline

1. **Step 8, query understanding:** conservative Arabic normalization; one GPT-OSS-20B structured analysis call; deterministic exact/alias Neo4j linking; deterministic retrieval planning.
2. **Step 9, hybrid retrieval:** vector entity/evidence/QA search, one-hop final_v1 graph traversal, direct held-out-safe QA FTS, deduplication, and conditional targeted FTS only when ordinary context is partial and lacks strong direct evidence.
3. **Step 10, reranking:** deterministic identity, anatomy, intent, source, semantic, and concept-coverage scoring. The experimental learned reranker remains disabled.
4. **Step 11, context construction:** absolute quality gates, concept and intent coverage checks, unrelated-condition filtering, deduplication, and a maximum of six focused evidence items.
5. **Step 12, generation:** one evidence-grounded GPT-OSS-20B call using only the Step 11 context and requiring citations.
6. **Step 13, claim extraction:** deterministic extraction of factual claims and citations from the generated response.
7. **Step 14, verification:** each claim must be supported by a cited evidence item and relevant to the query's concepts and intent.
8. **Step 15, hallucination mitigation:** unsupported and weak claims are removed; the system abstains when no substantive claim survives.
9. **Step 16, reliability:** deterministic uncalibrated score combining claim support, evidence coverage, relation confidence, source quality, and answerability.
10. **Step 17, explainable output:** final answer, answerability state, reliability, supporting entities/relations/evidence, claim audit, removed claims, warnings, and timing.

## Historical generation scores

These runs are retained for traceability, not head-to-head comparison.

| Run | BERTScore F1 (n) | Claim support (n) | Hallucination | Citation validity (n) | E2E ms |
|---|---:|---:|---:|---:|---:|
| `evaluation_v1_claimfirst_pilot_3q_v1` | 0.6852 (3) | 1.0000 (3) | 0.0000 | 1.0000 (3) | 4049.12 |
| `evaluation_v1_e2e_full_hybrid_semanticfix_100q_v1` | 0.6697 (74) | 1.0000 (12) | 0.0000 | 0.1622 (74) | 8624.38 |
| `evaluation_v1_e2e_full_hybrid_evidencelocal_100q_v1` | 0.6774 (24) | 1.0000 (24) | 0.0000 | 1.0000 (24) | 8626.34 |
| `evaluation_v1_e2e_full_hybrid_verifierfix3_100q_v1` | 0.6733 (18) | 1.0000 (18) | 0.0000 | 1.0000 (18) | 8626.11 |
| `evaluation_v1_e2e_full_hybrid_verifierfix4_100q_v1` | 0.6772 (24) | 1.0000 (24) | 0.0000 | 1.0000 (24) | 8633.06 |
| `evaluation_v1_e2e_lexical_only_100q_v2` | 0.7047 (9) | 1.0000 (4) | 0.0000 | 0.4444 (9) | 568.85 |
| `pilot_15q` | 0.6957 (9) | 1.0000 (3) | 0.0000 | 0.3333 (9) | 4292.40 |

## Exact final artifact paths

- Frozen graph: `outputs/final_graph/entities.csv`, `outputs/final_graph/entity_mentions.csv`, `outputs/final_graph/relation_decisions.csv`, `outputs/final_graph/relations.csv`, `outputs/final_graph/relations_bidirectional.csv`.
- Graph manifest: `outputs/final_graph/graph_manifest.json`.
- Neo4j backup with embeddings/index data: `neo4j_dump/step05_final_v1_neo4j.dump`.
- Human candidate annotations: `data/evaluation/candidate_relevance_annotations_100_final.csv`.
- Human-confirmed combined pool: `data/evaluation/candidate_relevance_combined_pool_v2.csv`.
- Replay-ready combined pool: `data/evaluation/candidate_relevance_combined_pool_v2_replay_ready.csv`.
- Retrieval-v2 candidates and final Step 11 states: `outputs/evaluation/retrieval/evaluation_v1_retrieval_v2_targeted_fts/full_hybrid_targeted_fts.jsonl`.
- Retrieval-v2 manifest, validation, and decisions: `outputs/evaluation/retrieval/evaluation_v1_retrieval_v2_targeted_fts/manifest.json`, `validation.json`, and `decisions.csv`.
- Targeted expansion analysis: `outputs/evaluation/retrieval_expansion/combined_pool_v2_analysis_final/summary.json`.
- Step 11 production replay metrics: `outputs/evaluation/retrieval_expansion/targeted_fts_production_step11_replay_v2_metrics.json`.
- Frozen final generation records: `outputs/evaluation/generation/full_pipeline_retrieval_v2_targeted_fts_reranked_network_v1/full_pipeline.jsonl`.
- Frozen final generation metrics and manifest: `outputs/evaluation/generation/full_pipeline_retrieval_v2_targeted_fts_reranked_network_v1/metrics.json` and `outputs/evaluation/generation/full_pipeline_retrieval_v2_targeted_fts_reranked_network_v1/manifest.json`.
- Final claim audit: `outputs/evaluation/claim_audit/full_pipeline_retrieval_v2_targeted_fts_reranked_network_v1/full_pipeline.jsonl` and `outputs/evaluation/claim_audit/full_pipeline_retrieval_v2_targeted_fts_reranked_network_v1/manifest.json`.
- Append-only successful-call cache: `outputs/evaluation/cache/full_pipeline_retrieval_v2_targeted_fts_reranked_network_v1/`.
- Offline BERTScore/RAGAS artifacts: `outputs/evaluation/offline_metrics/final_run_ahd_reference_v1/`.
- Hallucination-mitigation seed and leakage manifest: `data/training/hallucination_mitigation_seed_v1/`.
- Consolidated audit: `outputs/evaluation/FINAL_RESULTS.md` and `outputs/evaluation/FINAL_RESULTS.json`.

## Metrics still unavailable

- `entity_extraction_precision_recall_f1`: Unavailable: independent entity-extraction ground truth was not completed in the retained evaluation artifacts.
- `relation_candidate_recall_triplet_precision_recall_f1`: Unavailable: no independently annotated relation ground truth.
- `ragas_context_precision_recall`: Incomplete: the offline RAGAS workflow is implemented and uses the original AHD answers, but the evaluator API quota stopped the full 100-query judge run. Partial scores are not reported as final.
- `ragas_faithfulness_answer_relevancy`: Incomplete: evaluator-LLM quota stopped the resumable offline run. No retrieval or generation rerun is required.
- `reliability_auroc_auprc_calibration`: Unavailable: no independent binary correctness/reliability labels.
- `step08_accuracy`: Unavailable: query correction, classification, phrase extraction, and linking do not yet have a human-confirmed Step 8 gold set.

## Current conclusion

The strongest verified improvement is the conditional FTS fallback: direct candidate coverage rose from 37/99 to 49/99, while production Step 11 useful context coverage rose from 51 to 56 queries and direct context from 25 to 29. The final verifier achieved perfect support and citation validity on retained claims, but only 26/100 queries retained substantive claims. The next research priority is therefore retrieval/context coverage and verifier recall, not weakening hallucination controls or adding the supplemental graph.
