# Step 03D Entity Extraction Ensemble Improvement

This experiment uses the first-100 ground-truth hand-off to test whether completed extraction outputs can be combined without using gold labels at prediction time. The goal is to improve canonical entity selection while preserving the stronger entity-type behavior of the original extraction.

## Inputs

- Original predictions: `llm_entities_vs_gt_100.csv`
- Llama 3.3 70B candidate-rank predictions: `outputs/03_entity_extraction/prompt_ablation_first_100/candidate_rank_v3_llama_3_3_70b/predictions.csv`
- Llama 3.3 70B anti-generic predictions: `outputs/03_entity_extraction/prompt_ablation_first_100/anti_generic_v2_llama_3_3_70b/predictions.csv`
- GPT-OSS-120B anti-generic predictions: `outputs/03_entity_extraction/prompt_ablation_first_100/anti_generic_v2_gpt_oss_120b/predictions.csv`

## Results

| Strategy | Changed rows | Canonical F1 | Entity-type F1 | Interpretation |
|---|---:|---:|---:|---|
| Original teammate extraction | 0 | 0.4950 | 0.7174 | Baseline. |
| Llama-rank name + original type | 100 | 0.4912 | 0.7174 | Preserves type score but does not improve canonical F1. |
| Llama-rank name + voted type | 100 | 0.4912 | 0.6292 | Type voting hurts performance. |
| Specificity switch + original type | 15 | 0.5317 | 0.7174 | Best reportable improvement. |
| Agreement switch + original type | 5 | 0.5133 | 0.7174 | Improves canonical F1, but less than specificity switching. |

## Best Strategy

The best reportable strategy is `specificity_switch_original_type`. It starts from the original extraction, keeps the original entity type, and only replaces the canonical name when the original name is generic and a more specific model-extracted entity appears in the source question or answer. This changed 15 rows out of 100.

Compared with the original baseline, this improves canonical-name F1 from `0.4950` to `0.5317` while keeping entity-type F1 unchanged at `0.7174`.

## Report-Ready Conclusion

The main entity-extraction gain did not come from replacing the original extractor with a stronger LLM. It came from a constrained ensemble rule that uses Llama 3.3 70B as a specificity signal while preserving the original model's entity-type decision. This supports the broader system design: for Arabic medical information extraction, the most effective approach is not unrestricted prompting, but controlled LLM extraction combined with deterministic validation and conservative post-processing.
