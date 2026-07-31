# Evidence-Adaptive Generation v4

## Decision

The proposed change is justified. The frozen 200-query evaluation still has a
retrieval-coverage limit (61 empty Step 11 contexts), but the largest avoidable
loss after successful retrieval is between generation and deterministic
verification. This update targets that boundary only.

It does not change:

- `final_v1`, Neo4j, or the E5 indexes;
- Steps 8-11 retrieval, ranking, thresholds, or selected evidence;
- Step 14 verification rules or thresholds;
- semantic adjudication, the E5 claim calibrator, or supplemental graph use.

The frozen `grounded_claim_first_v3` artifacts and scores remain historical
results. They are not overwritten or reinterpreted as v4 results.

The evaluated implementation version is `grounded_evidence_adaptive_v4_2`.
Version 4.1 sends only each selected passage's authoritative evidence text and
citation handle to the model; duplicated source questions, source answers, and
ranking metadata remain available to Python but are excluded from the API
payload.

Version 4.2 keeps the query-concept requirement in the prompt but does not turn
a deterministic lexical mismatch into a technical generation failure. It records
a warning and leaves the unchanged Step 14 verifier as the final relevance
authority.

## Step 12 policy

Python chooses one of two modes from the existing Step 11 metadata.

### Strong direct evidence

One answer-origin passage must satisfy every gate:

- answer relevance >= 0.75;
- intent support >= 0.75;
- query-concept coverage >= 0.75;
- query-constraint coverage = 1.00;
- source reliability >= 0.75;
- no anatomy mismatch;
- no unrelated-condition mismatch;
- direct-question anchor or entity identity >= 0.50.

Only the highest-scoring eligible passage is sent to the model. Graph facts and
other passages are excluded from this generation call. GPT-OSS-20B produces a
near-extractive answer of at most two self-contained claims.

### Partial or mixed evidence

The selected Step 11 context remains available, but GPT-OSS-20B must:

- return at most two atomic claims;
- use exactly one evidence citation per claim;
- never combine a treatment, test, cause, or relation across passages;
- preserve names, anatomy, negation, numbers, and clinical relations;
- include a query medical concept in every claim;
- answer only the supported part and signal incomplete coverage.

## Deterministic output safeguards

The model returns only:

```json
{
  "claims": [
    {
      "claim_ar": "one self-contained claim",
      "citations": ["E1"]
    }
  ],
  "limitations_ar": []
}
```

Python then:

1. Rejects more than two claims.
2. Requires exactly one allowlisted citation per claim.
3. Requires at least one query medical concept in each claim.
4. Derives QA IDs and relation IDs from the cited Step 11 item.
5. Constructs the final answer only from validated claim text.
6. Replaces model-written limitations with fixed non-medical wording.

This prevents invented provenance and uncited free-form prose. Step 14 remains
the final authority for evidence support, query relevance, intent, anatomy,
negation, numbers, and relation preservation.

## Step 13 policy

Claims produced under either v4 mode are already the structured atomic contract,
so Step 13 preserves them exactly. It does not split them again and therefore
cannot detach a recommendation or test from its disease, symptom, or anatomy.

Legacy v3 cached answers retain the old splitter for reproducibility.

## Frozen-context applicability audit

No model calls were made for this audit. The strict gate was applied read-only to
the 200 frozen Step 11 contexts:

| Cohort | Strong direct | Non-empty context | Empty context |
|---|---:|---:|---:|
| AHD reference 100 | 7 | 69 | 31 |
| Entity ground-truth 100 | 9 | 70 | 30 |
| Total | 16 | 139 | 61 |

The 123 other non-empty contexts use partial/mixed mode. Empty contexts continue
to abstain.

## Verification

- Python compilation: passed.
- Focused v4 tests: 8 passed.
- Full deterministic suite: 70 passed.

## Frozen generation-only evaluation

V4.2 was evaluated as a new Steps 12-17 run against the exact saved Step 11
contexts. V3 outputs were not overwritten, and Steps 8-11, thresholds, retrieval,
reranking, graph data, embeddings, and deterministic verification were unchanged.

```powershell
& '.venv-run\Scripts\python.exe' scripts\run_generation_ablation.py `
  --gold-file data\evaluation\retrieval_gold_annotations_100.csv `
  --mode full_pipeline `
  --run-id evidence_adaptive_v4_2_ahd_reference_100_20260729 `
  --reuse-context-run outputs\evaluation\generation\frozen_prod_ahd_reference_100_steps12_17_network_20260728 `
  --resume `
  --request-interval-seconds 18 `
  --max-rate-limit-retries 1 `
  --rate-limit-backoff-seconds 30
```

```powershell
& '.venv-run\Scripts\python.exe' scripts\run_generation_ablation.py `
  --gold-file data\evaluation\entity_ground_truth_trial_100.csv `
  --mode full_pipeline `
  --run-id evidence_adaptive_v4_2_entity_ground_truth_100_20260729 `
  --reuse-context-run outputs\evaluation\generation\frozen_prod_entity_gt_100_steps12_17_network_20260728 `
  --resume `
  --request-interval-seconds 18 `
  --max-rate-limit-retries 1 `
  --rate-limit-backoff-seconds 30
```

## Final result

The agreed acceptance gate rejected v4.2:

| Metric | v3 | v4.2 |
|---|---:|---:|
| Substantive answers | 49/200 | 46/200 |
| Surviving claims | 72 | 56 |
| Pre-mitigation supported-claim rate | 0.2466 | 0.2718 |
| Technical failures | 6 | 0 |
| Schema failures | 3 | 0 |
| Citation validity | 1.00 | 1.00 |
| Post-mitigation BERTScore F1 | 0.6710 | 0.6752 |

V4.2 improved response-schema stability, support precision, latency, and
BERTScore slightly, but produced fewer substantive answers and fewer surviving
claims. Of 50 automatically identified differential claims, evidence-fidelity
review classified 26 as v3-equivalent, 11 as safe new claims, and 13 as unsafe.
Errors included wrong-drug evidence, changed clinical relations, anatomy/symptom
mismatches, changed dosage, and unsupported recommendations.

The final decision is therefore **keep v3 as production** and retain v4.2 as an
unsuccessful generation ablation. The authoritative comparison is:

`outputs/evaluation/generation/evidence_adaptive_v4_2_comparison_200q_20260729/FINAL_COMPARISON.md`
