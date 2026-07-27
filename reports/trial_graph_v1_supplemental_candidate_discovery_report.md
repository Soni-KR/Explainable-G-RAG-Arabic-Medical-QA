# Supplemental Candidate Discovery Report

This report proposes dataset-backed evidence candidates for low-evidence or low-reliability answers.
It does not import anything into Neo4j. Every candidate still needs human review before becoming a supplemental fact.

- Failed or weak rows analyzed: 50
- Candidate evidence rows: 246
- High-precision review rows: 84
- Candidate topics CSV: `outputs/05_trial_graph_v1/supplemental_facts/trial_graph_v1_supplemental_candidate_topics.csv`
- Candidate evidence CSV: `outputs/05_trial_graph_v1/supplemental_facts/trial_graph_v1_supplemental_candidate_evidence.csv`
- Candidate review CSV: `outputs/05_trial_graph_v1/supplemental_facts/trial_graph_v1_supplemental_candidate_review.csv`

## Topic Counts

- other: 29
- pregnancy_obstetrics: 6
- labs: 4
- dental: 4
- drug_safety: 3
- surgery_urology: 1
- dermatology_hair: 1
- nutrition: 1
- respiratory_general: 1

## Recommendation Counts

- reject_generic_topic: 112
- recommended_for_human_review: 84
- reject_eval_leakage: 50

## Review Workflow

1. Open the candidate review CSV first.
2. For each failed query, approve only rows whose source answer truly supports the missing fact.
3. Convert approved rows into supplemental entities/relations.
4. Re-run provenance, import into Neo4j, then rerun retrieval and generation.
