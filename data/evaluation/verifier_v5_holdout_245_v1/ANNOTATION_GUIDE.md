# Verifier v5 Claim Holdout

Review every row using only the question, claim, and cited evidence. The AHD
reference answer is context for medical intent, not automatic proof that the
claim is supported by its citation.

## Labels

- Evidence support: `yes`, `partial`, or `no`.
- Query relevance and each preservation field: `yes`, `no`, or `not_applicable`.
- Should retain: `yes` only when the claim is evidence-supported, answers the
  query, preserves entity/anatomy/number/negation/relation details, and makes no
  unsupported recommendation.
- Error reason: use one or more of `wrong_drug`, `wrong_disease`,
  `wrong_symptom`, `wrong_anatomy`, `wrong_laterality`, `number_or_duration`,
  `negation_or_safety`, `changed_relation`, `unsupported_recommendation`,
  `different_clinical_scenario`, `irrelevant`, `insufficient_evidence`, or
  `other`.

## Leakage Control

All claims sharing a `query_id` have the same `query_fold`. Never split rows
from one query across training and evaluation. Deterministic verifier status,
scores, failed checks, and `review_focus` are audit metadata only; annotators
must not copy them into human labels.

The prior 81 suspected false rejections are not included as holdout truth.
