# Step 16 Reliability Scoring Report

- Answers scored: 50
- Mean reliability score: 0.5762
- Reliability labels: {'high': 25, 'low': 19, 'medium': 6}
- Answerability labels: {'answerable': 29, 'insufficient_evidence': 17, 'partially_answerable': 4}
- Score formula: 0.30 claim support + 0.20 non-hallucination + 0.15 evidence coverage + 0.15 relation confidence + 0.15 source reliability + 0.05 context signal.
- Relation confidence uses rerank score, relation reliability label, and evidence count for relations supporting verified claims.
- Source reliability uses cited QA source presence, evidence text presence, relation reliability, relation score, and source diversity.
- AUROC/AUPRC: not available because no gold-supported/unsupported answer labels are present.
- Calibration: proxy bins are reported; true calibration needs gold labels.
- Average latency: not available because Step 12 raw timing traces are not stored.
- Reliability JSON: `outputs/05_trial_graph_v1/reliability_scoring/trial_graph_v1_reliability_scores.json`
- Reliability CSV: `outputs/05_trial_graph_v1/reliability_scoring/trial_graph_v1_reliability_scores.csv`
