# Evaluation Data

Retained files are limited to the final-v2 evaluation and this repository's entity
extraction/claim-verification audits.

- `retrieval_gold_annotations_100.csv`: frozen 100-question cohort and AHD reference
  answers used for offline answer comparison.
- `final_v2_candidate_relevance_labels_100.csv`: blinded candidate queue before
  annotation.
- `final_v2_candidate_relevance_labels_100_annotated.csv`: completed model-adjudicated
  candidate relevance judgments.
- `entity_ground_truth_trial_100.*`: graph-linked entity-ground-truth trial inputs.
- `entity_extraction/`: original entity GT, aligned predictions, and evaluation
  notebook.
- `claim_verification/`: manually reviewed 81-claim false-rejection audit.
- `human_claim_annotations_100.csv`: claim annotation schema/cohort retained for
  audit continuity.
- `ANNOTATION_GUIDE.md`: relevance and claim-label definitions.

Missing labels must remain missing. They must never be converted to label 0.
