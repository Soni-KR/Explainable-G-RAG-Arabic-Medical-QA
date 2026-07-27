# Unseen 100 Error Analysis

## Run Summary

| Run | Mean BERTScore F1 | Mean reliability | QA fallback queries | Main issue count |
|---|---:|---:|---:|---|
| First unseen 100 | 0.661048 | 0.802045 | 29 | {'acceptable_similarity': 73, 'retrieval_coverage_gap': 19, 'reference_mismatch_or_answer_wording': 7, 'weak_or_irrelevant_qa_fallback': 1} |
| Second unseen 100 | 0.652023 | 0.802011 | 25 | {'acceptable_similarity': 62, 'reference_mismatch_or_answer_wording': 6, 'retrieval_coverage_gap': 31, 'weak_or_irrelevant_qa_fallback': 1} |

## Lowest Second-Unseen Questions

| Query ID | Category | BERTScore F1 | Reliability | QA fallback | Issue label |
|---|---|---:|---:|---|---|
| unseen100_014 | تشخيص | 0.526355 | 0.789 | yes | retrieval_coverage_gap |
| unseen100_008 | علم الأجنة | 0.564809 | 0.777 | yes | retrieval_coverage_gap |
| unseen100_073 | أعشاب طبية | 0.56849 | 0.6557 | no | retrieval_coverage_gap |
| unseen100_081 | مطاعيم و لقاحات | 0.596425 | 0.8237 | no | retrieval_coverage_gap |
| unseen100_011 | البشرة والجمال | 0.607276 | 0.7907 | no | retrieval_coverage_gap |
| unseen100_021 | علم المناعة | 0.607306 | 0.7854 | no | retrieval_coverage_gap |
| unseen100_055 | الحمل والولادة | 0.608076 | 0.802 | yes | retrieval_coverage_gap |
| unseen100_053 | الامراض المعدية | 0.608227 | 0.9042 | yes | weak_or_irrelevant_qa_fallback |
| unseen100_092 | جراحة عامة | 0.611175 | 0.7659 | yes | retrieval_coverage_gap |
| unseen100_040 | أمراض نسائية | 0.612097 | 0.7909 | no | reference_mismatch_or_answer_wording |
| unseen100_068 | هرمونات | 0.613329 | 0.8027 | no | retrieval_coverage_gap |
| unseen100_078 | رمضان | 0.614725 | 0.8354 | no | retrieval_coverage_gap |
| unseen100_059 | جراحة الفك والأسنان | 0.616718 | 0.8095 | no | retrieval_coverage_gap |
| unseen100_018 | جراحة تجميل | 0.618754 | 0.7996 | no | retrieval_coverage_gap |
| unseen100_032 | علم الوراثة | 0.620202 | 0.8102 | no | retrieval_coverage_gap |

## Interpretation

The second unseen set has lower BERTScore than the first, while reliability and hallucination metrics remain stable. The lowest-score cases should be reviewed first to decide whether the next change should target retrieval coverage, QA fallback selection, or answer wording.

## Ablation Results on Second Unseen 100

All ablations reused the same completed live `openai/gpt-oss-20b` raw
responses and changed the Step 11 retrieval context before revalidating and
rerunning Steps 13-17. This isolates retrieval-context effects without making
new Groq calls, but it is not identical to regenerating answers from scratch
under each ablated context.

| Variant | BERTScore F1 | Answerability | Mean reliability | Verification result | Decision |
|---|---:|---|---:|---|---|
| Baseline QA fallback, threshold 0.42 | 0.652023 | 100 answerable | 0.8020 | 133 supported, 0 unsupported | Baseline |
| No QA fallback | 0.647568 | 97 answerable, 3 insufficient | 0.7831 | 136 supported, 4 unsupported before mitigation | Worse |
| Stricter QA fallback, threshold 0.50 | 0.649710 | 97 answerable, 3 insufficient | 0.7814 | 136 supported, 4 unsupported before mitigation | Worse |
| Category-aware fallback, bonus 0.08 | 0.652421 | 100 answerable | 0.8048 | 126 supported, 0 unsupported | Best conservative change |
| Category-aware fallback, bonus 0.12 | 0.654258 | 99 answerable, 1 insufficient | 0.7978 | 125 supported, 1 unsupported before mitigation | BERTScore gain with safety cost |
| Category-aware fallback, bonus 0.15 | 0.654657 | 98 answerable, 2 insufficient | 0.7904 | 124 supported, 2 unsupported before mitigation | Highest BERTScore, not recommended |
| Targeted fallback: question+answer scoring, bonus 0.08, min overlap 2 | 0.649382 | 97 answerable, 2 insufficient, 1 partial | 0.7935 | 133 supported, 1 weak, 0 unsupported | Worse; keep as failed ablation |

Conclusion:

The QA fallback helps on the harder second unseen sample. Removing it or making
the threshold too strict reduces BERTScore, answerability, and reliability.
The cleanest improvement is a small same-category preference with
`--qa-fallback-category-bonus 0.08`, because it slightly improves BERTScore and
reliability while keeping all 100 answers answerable and all verified claims
supported. Stronger category bonuses improve BERTScore more, but they introduce
unsupported claims before mitigation and reduce answerability, so they are not
recommended as the main trustworthy configuration.

## Targeted Retrieval Improvement Attempt

The next targeted experiment focused on the lowest-BERTScore coverage-gap
cases. Step 11 was extended with an optional fallback mode that scores AHD
source answers in addition to source questions, filters common Arabic
stopwords, and requires at least two informative overlapping tokens. This
retrieved better evidence for some individual low cases, such as left
testicular pain, but it reduced fallback coverage overall and hurt aggregate
metrics on the full second unseen set. The final BERTScore F1 dropped to
`0.649382`, answerability dropped to 97 fully answerable cases, and mean
reliability dropped to `0.7935`. Therefore this mode is recorded as a failed
ablation and is not selected as the main configuration. The previous
category-aware question-only fallback with bonus `0.08` remains the best
conservative setting.

## Output Files

- First analysis: `outputs\05_trial_graph_v1\evaluation\error_analysis\first_unseen_analysis.csv`
- Second analysis: `outputs\05_trial_graph_v1\evaluation\error_analysis\second_unseen_analysis.csv`
- Second lowest 15: `outputs\05_trial_graph_v1\evaluation\error_analysis\second_unseen_lowest_15.csv`
- First category summary: `outputs\05_trial_graph_v1\evaluation\error_analysis\first_unseen_category_summary.csv`
- Second category summary: `outputs\05_trial_graph_v1\evaluation\error_analysis\second_unseen_category_summary.csv`
- No-fallback ablation: `outputs\05_trial_graph_v1\evaluation\unseen100_random_seed20260727_ablation_no_qa_fallback.csv`
- Threshold 0.50 ablation: `outputs\05_trial_graph_v1\evaluation\unseen100_random_seed20260727_ablation_qa_fallback_t050.csv`
- Category-aware bonus 0.08: `outputs\05_trial_graph_v1\evaluation\unseen100_random_seed20260727_category_aware_fallback_t042_b008.csv`
- Category-aware bonus 0.12: `outputs\05_trial_graph_v1\evaluation\unseen100_random_seed20260727_category_aware_fallback_t042_b012.csv`
- Category-aware bonus 0.15: `outputs\05_trial_graph_v1\evaluation\unseen100_random_seed20260727_category_aware_fallback_t042_b015.csv`
- Targeted question-answer fallback ablation: `outputs\05_trial_graph_v1\evaluation\unseen100_random_seed20260727_targeted_fallback_question_answer_t042_b008_overlap2_live_groq_full_100.csv`
- Targeted question-answer fallback final output: `outputs\05_trial_graph_v1\evaluation\unseen100_random_seed20260727_targeted_fallback_question_answer_t042_b008_overlap2_live_groq_full_100_final_output.csv`
- Third unseen sample after selected change: `retrieval_gold_annotations_unseen_100_random_seed20260728.csv`
- Third unseen final output: `outputs\05_trial_graph_v1\evaluation\unseen100_random_seed20260728_category_aware_fallback_t042_b008_live_groq_full_100_final_output.csv`
- Third unseen BERTScore: `outputs\05_trial_graph_v1\evaluation\unseen100_random_seed20260728_category_aware_fallback_t042_b008_live_groq_full_100.csv`
- Third unseen BERTScore summary: `outputs\05_trial_graph_v1\evaluation\unseen100_random_seed20260728_category_aware_fallback_t042_b008_live_groq_full_100_summary.json`
