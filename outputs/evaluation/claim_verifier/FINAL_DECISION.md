# Final Claim-Verifier Decision

## Decision

The production pipeline will keep the conservative deterministic Step 14
verifier. Semantic and locally learned claim-retention overrides remain
disabled.

This decision minimizes unsafe medical claims. It knowingly preserves lower
answer coverage until a larger verifier dataset and a fresh test set exist.

## What Was Fixed

- Neo4j `EvidenceMention.field` is preserved through retrieval.
- Step 9 labels evidence origin.
- Step 11 removes question-only mentions from generation context.
- A question-origin mention with a linked answer contributes only its answer.
- Step 14 uses answer text and validated relation facts as factual evidence.
- Semantic eligibility is recomputed from authoritative evidence.
- Conflicting model summary flags fail closed in Python.

All production retrieval, generation, graph, and answer thresholds remain
unchanged.

## Development Results

| Verifier | Scope | TP | TN | FP | FN | Recall | Decision |
|---|---:|---:|---:|---:|---:|---:|---|
| GPT-OSS-20B v1 | 18 claims | 10 | 3 | 5 | 0 | 1.0000 | Unsafe |
| GPT-OSS-20B v2 | 17 completed | 10 | 4 | 3 | 0 | 1.0000 | Unsafe |
| GPT-OSS-120B v2 | 9 completed | 4 | 2 | 0 | 3 | 0.5714 | Too conservative |
| Local E5 calibrator | 81 OOF | 3 | 14 | 0 | 64 | 0.0448 | Too conservative at zero FP |

The 120B run was not resumed because even a perfect remainder could achieve
only 0.70 recall, below the predeclared 0.80 pilot gate.

## Production State

- `CLAIM_ADJUDICATION_ENABLED=false`
- `models/claim_verifier_e5_calibrator_v1.json` has `enabled=false`
- No semantic adjudicator is called by the production pipeline.
- No supplemental graph is used.
- Graph version remains `final_v1`.

## Interpretation

The 81 human-reviewed claims remain a development/calibration set:

- 67 valid claims were wrongly removed by the old lexical gates.
- 14 claims were correctly removed.

These labels proved the verifier-recall problem, but they are not large or
diverse enough to train and validate a safe replacement. The failed experiments
must not be described as production improvements.

## Required Future Data

Before enabling a learned verifier, collect:

- valid retained claims, not only suspected false rejections;
- ordinary unsupported and hallucinated claims;
- named-drug and named-disease conflicts;
- changed causal, diagnostic, and treatment relationships;
- merged alternatives and partial-support cases;
- generic advice from unrelated clinical contexts;
- a fresh query-level holdout never used for prompt or threshold design.

The final safety rule remains: when support or query relevance is uncertain,
abstain rather than retain the claim.
