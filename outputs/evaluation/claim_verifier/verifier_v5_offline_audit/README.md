# Verifier v5 Offline Audit

This is a development-only, zero-API replay.

The frozen production verifier and all saved v3/v4 runs are unchanged.
V5 adds non-overridable hard gates before optional semantic review.
Only intent/concept relevance disputes can reach semantic review.

## Human-reviewed development set

- Reviewed claims: 81
- Human-valid claims: 67
- Human-invalid claims: 14
- Valid claims hard-blocked: 1
- Invalid claims hard-blocked: 4
- Valid claims eligible for semantic review: 66
- Invalid claims eligible for semantic review: 9

## Prior 20B pilot replay

- Before v5: TP=10, TN=4, FP=3, FN=0
- After v5 gates: TP=9, TN=7, FP=0, FN=1
- Post-gate precision=1.0000, recall=0.9000

## V3.1 pilot

- Claims audited: 13
- Claims with new hard failures: 2
- Clinical-relation mismatches caught: 1

## Decision

V5 remains disabled. The apparent zero false-positive pilot result
is useful development evidence, but the same reviewed claims helped
shape the gates. A fresh claim-level holdout is required.

See `metrics.json` for the aggregate result and the CSV files for
claim-level provenance.
