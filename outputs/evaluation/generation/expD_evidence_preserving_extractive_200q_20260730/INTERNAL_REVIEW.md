# Internal Differential Review

This review covers the two claims newly retained by the
`evidence_preserving_extractive_v1` ablation. It is an internal technical and
evidence-fidelity review, not external medical-safety validation.

## Result

- Claims reviewed: 2
- Safe for promotion: 0
- Unsafe or insufficiently query-specific: 2
- Invalid citations: 0
- Non-extractive claims: 0
- Deterministic v3 verification failures: 0

## Findings

### `entitygtv1_039`

The extracted sentence is verbatim and properly cited, but its source QA is
about liposuction and internal abdominal fat. The target query asks how to
remove excess abdominal skin. This is a clinically related but different
scenario, so the answer is not specific enough to retain.

### `entitygtv1_055`

The extracted sentence is verbatim and properly cited, but it categorically
attributes nocturnal cough in children to allergy and recommends allergy
treatment without sufficient clinical qualification. Exact extraction preserves
the source, but it cannot make an overgeneralized source answer safe.

## Decision

Do not promote this fallback. It improves substantive coverage from 54 to 56
answers and retained claims from 69 to 71, but it misses the retained-claim
target and both differential claims fail the internal safety review.

Keep the frozen production configuration unchanged.
