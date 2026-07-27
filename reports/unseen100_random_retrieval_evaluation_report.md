# Unseen 100-Question Random Retrieval Evaluation

## Purpose

This run tests whether the current best pipeline generalizes beyond the
previous 100-question benchmark. The new evaluation set was sampled from
`AHD.csv` with a fixed random seed and excludes all questions from
`retrieval_gold_annotations_100.csv`.

## Evaluation Set

| Field | Value |
|---|---:|
| Evaluation CSV | `retrieval_gold_annotations_unseen_100_random.csv` |
| Sampling seed | `20260726` |
| Questions | 100 |
| Distinct categories | 90 |
| Maximum questions from one category | 2 |
| Excluded previous benchmark questions | 100 |
| Reference answer source | Original AHD answer |

The references are source AHD answers, not human-adjudicated gold medical
answers. They are useful for comparing system behavior, but they should not be
described as clinical ground truth.

## Pipeline Configuration

| Stage | Configuration |
|---|---|
| Step 8 | `--query-csv retrieval_gold_annotations_unseen_100_random.csv --query-column query --query-id-column query_id --limit 100` |
| Step 9a | Lexical semantic retrieval, `--top-k 25` |
| Step 9c | Hybrid retrieval, `--top-relations 80 --top-contexts 40` |
| Step 10 | Subgraph reranking, `--top-subgraph-edges 8` |
| Step 11 | Evidence contexts with `--qa-fallback-min-score 0.42` |
| Step 12 diagnostic | Extractive retrieval-only generation |
| Step 12 partial live | Groq `openai/gpt-oss-20b` with local key rotation |
| Step 13-17 | Claim extraction, verification, mitigation, reliability, final output |

The non-exact AHD QA fallback was active for 48 of the 100 unseen questions.
Exact normalized question matches are excluded from the fallback to avoid
trivial leakage.

## Live GPT-OSS Attempts

The live `openai/gpt-oss-20b` run was retried with local Groq key rotation.
The script records only the key index used for each request; no API key values
are written to output files. Two partial attempts hit Groq rate limits, then a
final resume with a 15-second delay completed the remaining 9 questions.

First key-rotation attempt:

| Field | Value |
|---|---:|
| Candidate queries | 100 |
| Calls/attempts made | 57 |
| Raw response rows | 47 |
| Valid answers | 46 |
| Final rate-limit errors | 1 |
| Stopped on rate limit | true |
| Keys used | 11 |

Partial live quality on the 46 completed answers:

| Metric | Value |
|---|---:|
| Matched references | 46 / 46 |
| BERTScore Precision | 0.661279 |
| BERTScore Recall | 0.662092 |
| BERTScore F1 | 0.660592 |
| Answerable | 46 |
| Mean reliability | 0.8017 |
| Reliability labels | 28 high, 18 medium |
| Verified claims | 56 |
| Supported claims | 55 |
| Weakly supported claims | 1 |
| Unsupported claims | 0 |
| Claim-support rate | 1.0 |
| Hallucination rate | 0.0 |

After resetting the 11 keys, Step 12 was resumed. This increased the completed
set from 46 to 91 valid answers before rate limiting again.

Second key-rotation attempt after reset:

| Field | Value |
|---|---:|
| Candidate queries | 100 |
| Newly selected queries | 54 |
| Calls/attempts made | 56 |
| Total valid answers after resume | 91 |
| Final rate-limit errors | 2 total raw errors |
| Stopped on rate limit | true |
| Remaining missing queries | 9 |

Partial live quality on the 91 completed answers:

| Metric | Value |
|---|---:|
| Matched references | 91 / 91 |
| BERTScore Precision | 0.661994 |
| BERTScore Recall | 0.656278 |
| BERTScore F1 | 0.658033 |
| Answerable | 91 |
| Mean reliability | 0.8007 |
| Reliability labels | 46 high, 45 medium |
| Verified claims | 104 |
| Supported claims | 103 |
| Weakly supported claims | 1 |
| Unsupported claims | 0 |
| Claim-support rate | 1.0 |
| Hallucination rate | 0.0 |

The remaining missing queries after this attempt were `unseen100_092` through
`unseen100_100`.

Final resume with longer delay:

| Field | Value |
|---|---:|
| Newly selected queries | 9 |
| Calls made | 9 |
| Total valid answers after resume | 100 |
| Errors | 0 |
| Stopped on rate limit | false |
| Delay | 15 seconds |

Final live quality on the complete unseen 100:

| Metric | Value |
|---|---:|
| Matched references | 100 / 100 |
| BERTScore Precision | 0.666061 |
| BERTScore Recall | 0.658194 |
| BERTScore F1 | 0.661048 |
| Answerable | 100 |
| Mean reliability | 0.8020 |
| Reliability labels | 54 high, 46 medium |
| Verified claims | 115 |
| Supported claims | 114 |
| Weakly supported claims | 1 |
| Unsupported claims | 0 |
| Claim-support rate | 1.0 |
| Hallucination rate | 0.0 |

## Completed Retrieval-Only Diagnostic

| Metric | Value |
|---|---:|
| Matched references | 100 / 100 |
| BERTScore Precision | 0.579321 |
| BERTScore Recall | 0.657931 |
| BERTScore F1 | 0.615458 |
| Answerable | 93 |
| Partially answerable | 5 |
| Insufficient evidence | 2 |
| Mean reliability | 0.457353 |
| Reliability labels | 57 medium, 43 low |
| Verified claims | 165 |
| Supported claims | 133 |
| Weakly supported claims | 25 |
| Unsupported claims | 7 |
| Claim-support rate | 0.9576 |
| Hallucination rate | 0.0424 |

## Comparison With Previous 100-Question Benchmark

| Run | BERTScore F1 | Answerability | Reliability |
|---|---:|---|---|
| New unseen 100, full live GPT-OSS | 0.661048 | 100 answerable | 54 high, 46 medium |
| Previous tuned 100, best full pipeline | 0.659652 | 100 answerable | 60 high, 40 medium |
| New unseen 100, partial live GPT-OSS subset | 0.658033 | 91 answerable / 91 completed | 46 high, 45 medium |
| New unseen 100, partial live GPT-OSS subset | 0.660592 | 46 answerable / 46 completed | 28 high, 18 medium |
| New unseen 100, retrieval-only diagnostic | 0.615458 | 93 answerable, 5 partial, 2 insufficient | 57 medium, 43 low |

The unseen random set is broader than the previous benchmark, with 90
categories represented. The retrieval-only diagnostic is weaker, which suggests
the graph evidence itself is less aligned on the random sample. However, the
complete live GPT-OSS pipeline recovers this gap and slightly exceeds the
previous tuned-100 BERTScore F1 while preserving zero unsupported claims.

## Output Files

- Sample: `retrieval_gold_annotations_unseen_100_random.csv`
- Final diagnostic output: `outputs/05_trial_graph_v1/evaluation/unseen100_random_extract_final_output_t042.csv`
- BERTScore rows: `outputs/05_trial_graph_v1/evaluation/unseen100_random_extract_retrieval_diagnostic_t042.csv`
- BERTScore summary: `outputs/05_trial_graph_v1/evaluation/unseen100_random_extract_retrieval_diagnostic_t042_summary.json`
- Partial live raw responses: `outputs/05_trial_graph_v1/evaluation/unseen100_random_live_groq_partial_raw_responses.jsonl`
- Partial live final output: `outputs/05_trial_graph_v1/evaluation/unseen100_random_live_groq_partial_46_final_output_t042.csv`
- Partial live BERTScore rows: `outputs/05_trial_graph_v1/evaluation/unseen100_random_live_groq_partial_46_t042.csv`
- Partial live BERTScore summary: `outputs/05_trial_graph_v1/evaluation/unseen100_random_live_groq_partial_46_t042_summary.json`
- Partial live 91-answer raw responses: `outputs/05_trial_graph_v1/evaluation/unseen100_random_live_groq_partial_91_raw_responses.jsonl`
- Partial live 91-answer final output: `outputs/05_trial_graph_v1/evaluation/unseen100_random_live_groq_partial_91_final_output_t042.csv`
- Partial live 91-answer BERTScore rows: `outputs/05_trial_graph_v1/evaluation/unseen100_random_live_groq_partial_91_t042.csv`
- Partial live 91-answer BERTScore summary: `outputs/05_trial_graph_v1/evaluation/unseen100_random_live_groq_partial_91_t042_summary.json`
- Full live final output: `outputs/05_trial_graph_v1/evaluation/unseen100_random_live_groq_full_100_final_output_t042.csv`
- Full live raw responses: `outputs/05_trial_graph_v1/evaluation/unseen100_random_live_groq_full_100_raw_responses.jsonl`
- Full live BERTScore rows: `outputs/05_trial_graph_v1/evaluation/unseen100_random_live_groq_full_100_t042.csv`
- Full live BERTScore summary: `outputs/05_trial_graph_v1/evaluation/unseen100_random_live_groq_full_100_t042_summary.json`

## Next Step

This run is now complete. The next useful experiment is either a second random
unseen 100-question sample with a different seed, or an ablation on the same
sample without the non-exact AHD QA fallback.
