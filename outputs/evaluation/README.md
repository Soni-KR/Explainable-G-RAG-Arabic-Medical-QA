# Retained Evaluation Results

Only results that still explain the current `final_v1` pipeline are active here.

## Retrieval

- `retrieval/pilot_15q`: five retrieval modes for the final qualitative pilot.
- `retrieval/ablation_100q`: complete 100-question lexical/vector/graph/hybrid
  comparison. Retrieval relevance metrics remain unavailable until provisional IDs
  are human-confirmed; latency metrics are valid.

## Generation and Claim Audit

- `frozen_production_200q_20260728`: authoritative frozen v3 evaluation over the
  two independent 100-query cohorts.
- `generation/evidence_adaptive_v4_2_ahd_reference_100_20260729` and
  `generation/evidence_adaptive_v4_2_entity_ground_truth_100_20260729`: completed
  v4.2 Steps 12-17 ablation runs using the exact v3 Step 11 contexts.
- `generation/evidence_adaptive_v4_2_comparison_200q_20260729`: authoritative
  comparison, differential evidence-fidelity review, and final decision. V4.2
  reduced substantive answers from 49 to 46 and surviving claims from 72 to 56;
  13 unsafe differential claims were found. V3 remains production.
- `generation/dev_v3_1_frozen_context_10q_20260729`: development-only provider
  and schema pilot for structured v3.1. It reused exact Step 11 contexts,
  generated for all 8 non-empty queries, retained 5 claims across 4 answers, and
  had no technical failures. One unsafe lexical reinterpretation was found, so
  this run is not a production result.
- `generation/pilot_15q`: last completed valid 15-question GPT-OSS-20B run.
- `claim_audit/pilot_15q`: matching atomic claim verification output.
- `qualitative/pilot_15q_steps08_12.md`: readable question-by-question inspection.
- `generation/evaluation_v1_e2e_full_hybrid_semanticfix_100q_v1`: completed live
  100-question full-hybrid run; 74 Step 12 generations and 26 evidence fallbacks.
- `claim_audit/evaluation_v1_e2e_full_hybrid_semanticfix_100q_v1`: matching original
  verifier output.
- `generation/evaluation_v1_e2e_full_hybrid_evidencelocal_100q_v1`: latest zero-API
  Steps 13-16 diagnostic using per-claim/per-evidence verification.
- `claim_audit/evaluation_v1_e2e_full_hybrid_evidencelocal_100q_v1`: matching claim
  audit with best evidence and failed checks.
- `generation/evaluation_v1_claimfirst_pilot_3q_v1`: leakage-free three-question
  `grounded_claim_first_v3` pilot.
- `retrieval/evaluation_v1_retrieval_fullhybrid_qacorpus_identityfix_100q_v1`:
  leakage-free full-hybrid diagnostic using the held-out-safe 807,698-row QA index.

The 2026-07-22 zero-API replay of current Steps 10-11 over that frozen clean
artifact retained context for 70/100 queries, with 255 items total (2.55/query),
four contexts containing graph facts, and no semantic-fallback execution.

## End-to-End Retrieval Ablation

- `evaluation_v1_e2e_lexical_only_100q_v2` completed under the pre-semantic-fix
  context selector: 9 generated answers and 91 insufficient-evidence fallbacks.
- The historical full-hybrid run completed all 100 questions. Step 12 generated for
  74; the evidence-local verifier retained 40 claims across 24 substantive answers.
- BERTScore F1 is `0.677404` over the 24 substantive answers only. Automatic claim
  support and citation validity are `1.0` after mitigation and must not be reported
  as human medical-accuracy scores.
- That historical 100-question generation artifact contains six exact-question
  retrieval leaks and is retained only as a verifier diagnostic. Clean generation
  evaluation must use the held-out-safe retrieval run named above.
- Vector-only, graph-only, and hybrid-without-reranking generation remain incomplete.
New comparable runs must use the same frozen inputs and current pipeline version.

The final candidate annotations contain 540 human-reviewed rows across 99
candidate-bearing queries: 495 evidence candidates and 45 graph-relation candidates.
`evalv1_045` is non-medical and correctly has no retrieval candidates. Labels are
335 irrelevant, 157 partial, and 48 direct. Only 37 queries contain a direct
candidate; 44 are partial-only and 18 are all-zero.

`reranking/candidate_reranker_two_stage_v1_context_replay.jsonl` and its metrics
file compare the current Step 11 context with query-grouped out-of-fold learned
scores. The learned score improves selected useful precision from `0.527778` to
`0.560284`, but reduces useful-context coverage from 49 to 44 queries. The model in
`models/candidate_reranker_two_stage_v1.json` therefore remains disabled.

`retrieval_expansion/partial_only_fts_candidates_v1.csv` contains 483 new,
deduplicated candidates for the 44 partial-only queries. The held-out-safe FTS run
excluded 56 existing hits, used graph aliases for 11 queries, and protected two
queries from unsafe reformulation drift by searching their original text only.
All 483 rows remain `pending_human_annotation`.

The reviewed supplemental sidecar is not a remedy for this coverage issue: only
four relations passed its acceptance gates, it activated for 0/35 clean evaluation
queries, and its measured context delta was zero. It remains excluded from
`final_v1` pending a larger independently reviewed export.

Each completed run keeps raw JSONL, `metrics.json`, and `manifest.json`. Manifests
record graph/model/index configuration, thresholds, top-k values, source hashes,
runtime versions, and Git state without credentials.
