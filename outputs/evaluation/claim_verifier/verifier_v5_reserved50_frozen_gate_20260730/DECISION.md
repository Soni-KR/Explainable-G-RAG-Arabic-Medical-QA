# Reserved 50-Claim Verifier Decision

## Protocol

- The four-rule post-semantic safety gate was frozen before this run.
- The 50 claims have zero exact claim overlap with the 81-claim development set.
- Human review contains 37 safe/equivalent claims and 13 unsafe claims.
- Human labels were used only for scoring and were not sent to Groq.
- Each eligible claim used GPT-OSS-20B semantic prompt v2, the existing v5 hard
  gates, and the unchanged deterministic post-semantic safety gate.
- The final reproducibility pass was cache-only: 39 cached semantic responses,
  39 cache hits, and zero new API calls.

## Result

| Metric | Result |
|---|---:|
| True positives | 32 |
| True negatives | 5 |
| False positives | 8 |
| False negatives | 5 |
| Precision | 0.800000 |
| Recall | 0.864865 |
| F1 | 0.831169 |
| Safe/equivalent retention | 32/37 |
| Unsafe claims rejected | 5/13 |
| Unsafe claims retained | 8/13 |

The retained unsafe claims include wrong-drug evidence, unsupported medication
recommendations, anatomy mismatches, changed clinical relations, unrelated
conditions/tests, invented patient history, and query mismatch. Several rows
carry more than one error label.

## Decision

The candidate fails the non-negotiable requirement that all 13 unsafe claims
be rejected. No verifier rule was changed after inspecting this result.

The cached v3.1 200-query promotion replay was intentionally not run because
the candidate had already failed its reserved safety gate. Production remains
deterministic v3. The 81-claim post-safety-gate result remains development
evidence only and must not be reported as externally validated precision.

## Artifacts

- `metrics.json`: authoritative aggregate scores and acceptance decision.
- `predictions.csv`: all 50 claim-level decisions and failure metadata.
- `manifest.json`: model, prompt, input checksum, graph version, and cache mode.
- `outputs/evaluation/cache/verifier_v5_reserved50_frozen_gate_20260730/semantic_claim_adjudication.jsonl`:
  append-only model-response cache.
