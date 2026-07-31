# Evidence-Preserving Extractive Fallback

This is a frozen-context internal development ablation. It reuses the
completed v3.1 Step 11 contexts, changes no retrieval component, and
uses the unchanged deterministic v3 claim verifier.

**Decision: DO_NOT_PROMOTE_AUTOMATIC_TARGETS_NOT_MET**

## Aggregate Results

| Metric | Frozen v3.1 | Extractive candidate |
|---|---:|---:|
| Substantive answers | 54/200 | 56/200 |
| Retained claims | 69 | 71 |
| Citation validity | 1.000 | 1.000 |
| Schema failures | 0 | 0 |
| Technical failures | 1 | 1 |
| BERTScore F1 | 0.677879 (54) | 0.676742 (56) |

## Frozen Gates

- `fallback_version`: `evidence_preserving_extractive_v1`
- `min_answer_relevance`: `0.6`
- `min_original_question_relevance`: `0.5`
- `min_intent_support`: `0.75`
- `min_query_concept_coverage`: `0.5`
- `min_query_constraint_coverage`: `0.5`
- `min_source_reliability`: `0.9`
- `min_sentence_query_relevance`: `0.25`
- `min_sentence_chars`: `12`
- `max_sentence_chars`: `700`
- `max_claims_per_query`: `1`
- `citations_per_claim`: `1`
- `semantic_override_enabled`: `False`
- `supplemental_graph_enabled`: `False`
- `verifier`: `deterministic_v3_unchanged`

## Promotion Checks

- `substantive_answers_above_54`: **pass**
- `retained_claims_above_72`: **fail**
- `citation_validity_one`: **pass**
- `schema_failures_zero`: **pass**
- `automatic_extractiveness_invariants_zero`: **pass**
- `differential_medical_review_complete`: **fail**
- `unsafe_differential_claims_zero`: **fail**

The automatic checks establish exact extraction, one valid citation,
and deterministic v3 support. They do not constitute external medical
safety validation. Newly retained claims remain an internal development
result until their differential review is completed.

## Internal Differential Review

Both newly retained claims were reviewed for evidence fidelity and query
specificity. Both preserve their cited source exactly, but neither is safe to
promote:

- `entitygtv1_039` shifts from excess-skin removal to a broader
  liposuction/abdominal-fat scenario.
- `entitygtv1_055` overgeneralizes nocturnal cough in children as allergy and
  recommends allergy treatment without sufficient qualification.

The final decision therefore remains **do not promote**. See
`INTERNAL_REVIEW.md` for the complete internal review.

## Artifacts

- `cohort_a_candidate`: `outputs/evaluation/generation/expD_evidence_preserving_extractive_200q_20260730/ahd_reference_100.jsonl`
- `cohort_b_candidate`: `outputs/evaluation/generation/expD_evidence_preserving_extractive_200q_20260730/entity_ground_truth_100.jsonl`
- `fallback_attempts`: `outputs/evaluation/generation/expD_evidence_preserving_extractive_200q_20260730/fallback_attempts.jsonl`
- `differential_safety_review`: `outputs/evaluation/generation/expD_evidence_preserving_extractive_200q_20260730/differential_safety_review.csv`
- `internal_review`: `outputs/evaluation/generation/expD_evidence_preserving_extractive_200q_20260730/INTERNAL_REVIEW.md`
- `metrics`: `outputs/evaluation/generation/expD_evidence_preserving_extractive_200q_20260730/metrics.json`
- `manifest`: `outputs/evaluation/generation/expD_evidence_preserving_extractive_200q_20260730/manifest.json`
- `report`: `outputs/evaluation/generation/expD_evidence_preserving_extractive_200q_20260730/README.md`
