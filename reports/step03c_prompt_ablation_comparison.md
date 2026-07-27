# Step 03C Prompt Ablation Comparison

This experiment tests whether rerunning entity extraction on the first 100 annotated AHD rows with alternative Groq-hosted models improves the entity-extraction metrics. The same evaluator used in Step 03B is reused for each prediction file.

## Inputs

- Ground truth: `ground_truth_entities_100.csv`
- Original predictions: `llm_entities_vs_gt_100.csv`
- Models tested through Groq: `openai/gpt-oss-20b`, `openai/gpt-oss-120b`, and `llama-3.3-70b-versatile`
- Evaluation mode: `baseline`

## Results

| Prompt version | Status | Valid predictions | Missing/error rows | Canonical F1 | Entity-type F1 | Notes |
|---|---|---:|---:|---:|---:|---|
| Original teammate extraction | Complete | 100 | 0 | 0.4950 | 0.7174 | Baseline from the provided prediction file. |
| `central_v1` | Complete | 100 | 0 | 0.2617 | 0.6429 | Worse than baseline. |
| `anti_generic_v2` | Complete with 1 parse error | 99 | 1 | 0.4729 | 0.5942 | Best GPT-OSS prompt run, but still below baseline. |
| `candidate_rank_v3` | Partial with 18 parse/empty errors | 82 | 18 | 0.2545 | 0.4385 | Unstable JSON behavior; partial JSON recovery was applied where possible. |
| `anti_generic_v2` + Llama 3.3 70B | Complete | 100 | 0 | 0.4876 | 0.5780 | Strongest new model run for canonical-name F1; still below original entity-type F1. |
| `anti_generic_v2` + GPT-OSS-120B | Complete | 100 | 0 | 0.3381 | 0.6181 | Stable output but weak canonical matching. |
| `candidate_rank_v3` + Llama 3.3 70B | Complete | 100 | 0 | 0.4912 | 0.5138 | Nearly matched the original canonical-name F1, but entity-type F1 was still weak. |

## Interpretation

The prompt ablations did not improve the first-100 entity-extraction benchmark. The original teammate extraction remains the strongest reportable result, with canonical-name F1 of `0.4950` and entity-type F1 of `0.7174`. Among the new Groq model runs, Llama 3.3 70B with `anti_generic_v2` was the strongest for canonical-name extraction, reaching canonical-name F1 of `0.4876` with zero format errors. However, its entity-type F1 remained lower at `0.5780`.

The GPT-OSS-120B run was more stable than GPT-OSS-20B in output formatting, but it did not improve extraction quality. It reached canonical-name F1 of only `0.3381`. This suggests that simply increasing model size within the GPT-OSS family does not solve the central-entity selection and canonicalization problem.

The `candidate_rank_v3` prompt was designed to ask the model to list several candidates before selecting the most central entity. In practice, GPT-OSS-20B often returned truncated or invalid JSON under this longer format. A partial-response recovery rule was added to salvage `canonical_name` and `entity_type` when they appeared before truncation, but the run still ended with 18 invalid or empty outputs and weak evaluation scores. The same prompt with Llama 3.3 70B was much stronger for canonical-name extraction, reaching F1 of `0.4912`, but it misclassified many entity types and therefore remained weaker than the original extraction overall.

## Report-Ready Conclusion

Prompt engineering and model switching alone were not sufficient to improve entity extraction on the first 100 annotated AHD records. Llama 3.3 70B is the best Groq model tested so far for canonical-name extraction and nearly matches the original canonical-name score, but the original extraction remains stronger overall because of its entity-type performance. The diagnostic upper bound from Step 03B remains more informative: repeated central-entity selection mistakes and canonical-form mismatches are the main error sources. The next improvement should therefore be a constrained extraction method that combines LLM output with dataset/graph candidate lists and deterministic validation, rather than relying on freer prompt-only extraction.

This follow-up is implemented in Step 03D. The best constrained ensemble improves canonical-name F1 to `0.5317` while preserving the original entity-type F1 of `0.7174`.
