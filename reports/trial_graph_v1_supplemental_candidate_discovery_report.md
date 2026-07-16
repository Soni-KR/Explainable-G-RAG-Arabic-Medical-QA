# Supplemental Candidate Discovery Report

This report proposes dataset-backed evidence candidates for low-evidence or low-reliability answers.
It does not import anything into Neo4j. Every candidate still needs human review before becoming a supplemental fact.

- Failed or weak rows analyzed: 22
- Candidate evidence rows: 110
- High-precision review rows: 14
- Candidate topics CSV: `outputs/05_trial_graph_v1/supplemental_facts/trial_graph_v1_supplemental_candidate_topics.csv`
- Candidate evidence CSV: `outputs/05_trial_graph_v1/supplemental_facts/trial_graph_v1_supplemental_candidate_evidence.csv`
- Candidate review CSV: `outputs/05_trial_graph_v1/supplemental_facts/trial_graph_v1_supplemental_candidate_review.csv`

## Topic Counts

- dental: 5
- other: 4
- drug_safety: 3
- pregnancy_obstetrics: 3
- labs: 2
- surgery_urology: 1
- nutrition: 1
- orthopedics_pain: 1
- respiratory_general: 1
- dermatology_hair: 1

## Recommendation Counts

- reject_low_similarity: 58
- reject_eval_leakage: 22
- reject_generic_topic: 16
- recommended_for_human_review: 14

## Review Workflow

1. Open the candidate review CSV first.
2. For each failed query, approve only rows whose source answer truly supports the missing fact.
3. Convert approved rows into supplemental entities/relations.
4. Re-run provenance, import into Neo4j, then rerun retrieval and generation.
