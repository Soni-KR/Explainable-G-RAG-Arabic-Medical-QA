# Step 03B Entity Extraction Strategy Comparison

This experiment evaluates post-processing strategies on the first 100
entity-extraction rows provided by the teammate hand-off:

- `ground_truth_entities_100.csv`
- `llm_entities_vs_gt_100.csv`

Each strategy was run with `scripts/step03b_evaluate_entity_extraction_first100.py`
and saved under `outputs/03_entity_extraction/evaluation_first_100/<strategy>/`.
The comparison table is also saved as
`outputs/03_entity_extraction/evaluation_first_100/strategy_comparison.csv`.

## Results

| Strategy | Gold labels used | Changed rows | Canonical F1 | Entity-type F1 | Interpretation |
|---|---:|---:|---:|---:|---|
| Baseline | No | 0 | 0.4950 | 0.7174 | Original first-100 score reproduced from the provided CSV files. |
| Canonical style rules | No | 33 | 0.3233 | 0.7174 | Harmful; exact metric often expects the article/prefix to remain. |
| Type rules | No | 2 | 0.4950 | 0.6953 | Harmful; simple cue rules introduced type mistakes. |
| Graph exact alias | No | 4 | 0.4950 | 0.7174 | Neutral; safe but did not improve this set. |
| Graph resolver | No | 5 | 0.4850 | 0.7174 | Harmful; fuzzy canonicalization changed valid surface forms. |
| Context alias resolver | No | 7 | 0.4880 | 0.7174 | Harmful; context matching sometimes selected the wrong central entity. |
| Combined | No | 31 | 0.4280 | 0.5694 | Harmful; broad rules over-corrected. |
| Combined conservative | No | 36 | 0.3233 | 0.7174 | Harmful because it inherited style normalization. |
| Diagnostic gold map | Yes | 42 | 0.7813 | 0.9163 | Not reportable as a general method; useful as an upper-bound error analysis. |

## Interpretation

The controlled runs show that the current first-100 errors are not mainly
caused by trivial graph-alias normalization or simple type-cue mistakes.
Most reportable post-processing strategies were neutral or harmful. The
diagnostic gold-map result shows a large possible improvement, but it uses the
evaluation labels directly and therefore should be described only as an
error-analysis upper bound.

The practical next step is to improve the extraction stage itself rather than
only post-process its outputs. The most promising direction is to rerun entity
extraction with a stricter prompt that asks for one central medical entity,
short canonical forms, and entity types restricted to `DiseaseCondition`,
`Treatment`, `Symptom`, and `Test`, then validate on this same first-100 file.

## Report-Ready Conclusion

For the methodology/results chapter, the fair baseline remains:

- Canonical-name F1: `0.4950`
- Entity-type F1: `0.7174`

The ablation table should mention that naive canonicalization and type rules
did not improve the first-100 evaluation, while the diagnostic upper bound
indicates that supervised correction or prompt-level extraction changes could
substantially improve both canonical names and entity types.
