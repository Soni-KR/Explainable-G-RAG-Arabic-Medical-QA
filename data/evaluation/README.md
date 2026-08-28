# Evaluation Data

Only `ANNOTATION_GUIDE.md` is public. It defines the retrieval and claim-labeling
protocol without publishing dataset-derived content.

The evaluation scripts expect locally supplied cohorts, relevance judgments,
reference answers, and claim audits. These files are ignored by Git because they
contain AHD questions, answers, evidence, or model outputs. Obtain them through the
authorized project channel and restore them under `data/evaluation/` when needed.

Missing labels must remain missing. They must never be converted to label 0.
