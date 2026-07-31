# Evidence-Adaptive Generation v4.2: Frozen v3 Comparison

This report compares only Steps 12–17. Both versions use the exact same
saved Step 11 context per query; Steps 8–11, `final_v1`, embeddings,
retrieval, reranking, prompts outside Step 12, and verification thresholds
were not rerun or changed.

## Decision

**KEEP_V3_AS_FINAL**

v4 reduced substantive answers from 49 to 46 and surviving claims from 72 to 56; the differential review also found 13 unsafe claims. Retain v3 and record v4 as an unsuccessful generation ablation.

## Main Results

| Scope | Version | Substantive answers | Surviving claims | Pre-mitigation support | Technical/schema failures | Citation validity | BERTScore F1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| AHD reference 100 | v3 | 24 | 37 | 0.250 | 3/2 | 1.000 | 0.677259 |
| AHD reference 100 | v4 | 25 | 31 | 0.310 | 0/0 | 1.000 | 0.679175 |
| Entity-GT 100 | v3 | 25 | 35 | 0.243 | 3/1 | 1.000 | 0.664972 |
| Entity-GT 100 | v4 | 21 | 25 | 0.236 | 0/0 | 1.000 | 0.670413 |
| Aggregate 200 | v3 | 49 | 72 | 0.247 | 6/3 | 1.000 | 0.670990 |
| Aggregate 200 | v4 | 46 | 56 | 0.272 | 0/0 | 1.000 | 0.675175 |

BERTScore is scoped to substantive post-mitigation answers with an AHD
reference; it is not a score over fallback/abstention text.

## Differential Safety Review

- Differential v4 claims: 50
- Evidence-fidelity review complete: True
- Unsafe differential claims: 13
- Invalid citations: 0

The review checked wrong drugs, changed clinical relations, anatomy errors, unsupported recommendations, negation/number errors, and invalid citations.

## Outcome Breakdown

| Version | Generated | Fallback | Fully answerable | Partially answerable | Supported but incomplete | Insufficient evidence | Generation unavailable |
|---|---:|---:|---:|---:|---:|---:|---:|
| v3 | 133 | 67 | 3 | 20 | 26 | 145 | 6 |
| v4 | 139 | 61 | 7 | 13 | 26 | 154 | 0 |

## Claim Verification

| Version | Claims before mitigation | Supported | Weak | Unsupported | Surviving |
|---|---:|---:|---:|---:|---:|
| v3 | 292 | 72 | 8 | 212 | 72 |
| v4 | 206 | 56 | 13 | 137 | 56 |

## Latency

| Version/stage | Mean ms | Median ms | p95 ms | Total ms |
|---|---:|---:|---:|---:|
| v3 `end_to_end` | 20709.58 | 27495.34 | 35433.75 | 4141915.77 |
| v3 `step12_answer_generation` | 2934.42 | 820.76 | 20073.36 | 586884.38 |
| v4 `end_to_end` | 11622.66 | 17818.78 | 18191.95 | 2324532.58 |
| v4 `step12_answer_generation` | 436.54 | 565.17 | 813.81 | 87307.86 |

`end_to_end` includes runner pacing. `step12_answer_generation` is
the cleaner provider/generation comparison.

## Artifacts

- `comparison_metrics`: `outputs/evaluation/generation/evidence_adaptive_v4_2_comparison_200q_20260729/comparison_metrics.json`
- `differential_safety_audit`: `outputs/evaluation/generation/evidence_adaptive_v4_2_comparison_200q_20260729/differential_safety_audit.csv`
- `differential_review_decisions`: `outputs/evaluation/generation/evidence_adaptive_v4_2_comparison_200q_20260729/differential_review_decisions.json`
- `final_comparison`: `outputs/evaluation/generation/evidence_adaptive_v4_2_comparison_200q_20260729/FINAL_COMPARISON.md`
- `manifest`: `outputs/evaluation/generation/evidence_adaptive_v4_2_comparison_200q_20260729/manifest.json`
