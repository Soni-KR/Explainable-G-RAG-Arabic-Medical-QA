# Experiment A: Frozen v3 versus v3.1

Only Steps 12-17 differ. Both variants use the exact same saved Step 11
context for every query. Verifier v5, semantic adjudication, and retrieval
rescue are disabled.

**Decision: PENDING_DIFFERENTIAL_REVIEW**

## Results

| Scope | Version | Substantive answers | Retained claims | Pre-mitigation support | Technical/schema failures | Citation validity | BERTScore F1 |
|---|---|---:|---:|---:|---:|---:|---:|
| AHD reference 100 | v3 | 24 | 37 | 0.250 | 3/2 | 1.000 | 0.677259 |
| AHD reference 100 | v3_1 | 29 | 39 | 0.320 | 1/0 | 1.000 | 0.675517 |
| Entity-GT 100 | v3 | 25 | 35 | 0.243 | 3/1 | 1.000 | 0.664972 |
| Entity-GT 100 | v3_1 | 25 | 30 | 0.244 | 0/0 | 1.000 | 0.680620 |
| Aggregate 200 | v3 | 49 | 72 | 0.247 | 6/3 | 1.000 | 0.670990 |
| Aggregate 200 | v3_1 | 54 | 69 | 0.282 | 1/0 | 1.000 | 0.677879 |

BERTScore covers substantive post-mitigation answers only.

## Acceptance Gates

- `substantive_answers_at_least_baseline`: **true**
- `retained_claims_at_least_baseline`: **false**
- `schema_failures_zero`: **true**
- `citation_validity_one`: **true**
- `differential_review_complete`: **false**
- `unsafe_differential_claims_zero`: **false**

## Differential Safety Review

- Candidate-only claims requiring review: 59
- Review complete: False
- Unsafe claims confirmed: 0
- Automatically invalid citations: 0

Review each queued claim for wrong drugs/diseases, changed clinical
relations, anatomy/laterality errors, altered numbers or negation,
and unsupported recommendations.

## Artifacts

- `comparison_metrics`: `outputs/evaluation/generation/experiment_a_v3_vs_v31_200q_20260729/comparison_metrics.json`
- `differential_claim_review_queue`: `outputs/evaluation/generation/experiment_a_v3_vs_v31_200q_20260729/differential_claim_review_queue.csv`
- `experiment_report`: `outputs/evaluation/generation/experiment_a_v3_vs_v31_200q_20260729/EXPERIMENT_A.md`
- `manifest`: `outputs/evaluation/generation/experiment_a_v3_vs_v31_200q_20260729/manifest.json`
