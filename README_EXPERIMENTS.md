# MG-Retriever Experiment Log

This file summarizes the main experiments performed after the initial graph construction work. It focuses on the work done from retrieval onward, the entity-extraction improvement work, supplemental graph expansion, hallucination mitigation, reliability scoring, and the final 100-query live `GPT-OSS-20B` run.

The goal of these experiments was not only to increase the number of answered questions, but to keep answers evidence-grounded, explainable, and measurable through claim verification and reliability scoring.

## Final Recommended Configuration

The best current configuration is:

- Refined entity inventory from Step 03G.
- Refined relation extraction and validation outputs.
- Refined graph imported into `outputs/05_trial_graph_v1`.
- Supplemental AHD-backed fact layer enabled.
- Exact AHD source-answer facts enabled for exact dataset QA matches.
- Step 9C supplemental relation boost enabled.
- Step 11 prompt instruction for `ANSWERED_BY_SOURCE_QA` enabled.
- Step 12 live generation with `openai/gpt-oss-20b`.
- Step 15 controlled lenient mitigation enabled with `--include-weak`.

This mode keeps weakly supported claims but still removes unsupported claims. This is the safest compromise tested so far: it increases answer coverage without allowing verified hallucinations.

## Final Metrics

Final live run on 100 AHD queries:

| Metric | Value |
|---|---:|
| Queries evaluated | 100 |
| Answerable | 89 |
| Partially answerable | 0 |
| Insufficient evidence | 11 |
| High reliability | 69 |
| Medium reliability | 20 |
| Low reliability | 11 |
| Mean reliability score | 0.7578 |
| Mean claim-support rate | 0.8900 |
| Mean hallucination rate | 0.0000 |
| Mean evidence coverage | 0.2744 |
| Mean relation confidence | 0.6374 |
| Mean source reliability | 0.7758 |

Final output files:

- `outputs/05_trial_graph_v1/final_output/trial_graph_v1_final_explainable_output.csv`
- `outputs/05_trial_graph_v1/final_output/trial_graph_v1_final_explainable_output.json`
- `outputs/05_trial_graph_v1/final_output/trial_graph_v1_final_explainable_output.md`

Final report:

- `reports/trial_graph_v1_final_improved_live_gpt_oss_20b_report.md`

## Main Experiment Results

| Experiment | Dataset size | Main change | Answerable | Partial | Insufficient | High / Medium / Low reliability | Mean reliability | Hallucination rate | Result |
|---|---:|---|---:|---:|---:|---|---:|---:|---|
| Early 25-query baseline after initial Step 13-17 implementation | 25 | Claim extraction, verification, mitigation, reliability scoring | 10 high-label outputs, many low-evidence cases | 0 | 15 low reliability | 10 / 0 / 15 | 0.4158 | Not final | Too many `لا توجد أدلة كافية`; graph coverage was weak. |
| 25-query run after first supplemental facts | 25 | Added manually reviewed AHD-backed supplemental facts | 22 | 1 | 2 | 18 / 5 / 2 | 0.7853 | 0.0400 average after mitigation | Large improvement, but evaluated on only 25 queries. |
| 50-query expanded evaluation | 50 | Tested on offset/newer questions | 28 | 4 | 18 | 23 / 8 / 19 | 0.5855 | 0.0700 average | Showed that the first supplemental layer overfit the first 25 and did not generalize enough. |
| Refined graph + 100-query live baseline | 100 | Refined entities/relations and rebuilt graph/embeddings | 50 | 3 | 47 | 35 / 18 / 47 | 0.5317 | 0.0000 verified | More robust graph, but many remaining coverage gaps. |
| Targeted supplemental facts only | 100 | Added 15 high-value AHD-backed facts and Step 9C supplemental boost | 49 | 3 | 48 | 40 / 12 / 48 | 0.5279 | 0.0000 verified | Helped targeted cases, but not enough globally. |
| Exact-source expansion checkpoint with extractive fallback | 100 | Added exact AHD source-answer facts, but generation was mixed/fallback due API limits | 44 | 13 | 43 | 7 / 39 / 54 | 0.4499 | 0.0367 | Retrieval coverage improved, but fallback generation reduced reliability. Not final. |
| Clean live GPT-OSS-20B strict mode | 100 | Full live run after exact-source prompt fix; unsupported claims removed, weak claims removed | 88 | 1 | 11 | 68 / 21 / 11 | 0.7563 | 0.0000 verified | Strong result; strict and medically conservative. |
| Clean live GPT-OSS-20B controlled lenient mode | 100 | Kept weakly supported claims, still removed unsupported claims | 89 | 0 | 11 | 69 / 20 / 11 | 0.7578 | 0.0000 verified | Best current result and recommended final configuration. |

## Entity Extraction Experiments

The entity work was necessary because the graph quality depends heavily on canonical entity names and entity types.

### First-100 Prompt Ablations

Ground truth:

- `ground_truth_entities_100.csv`
- `llm_entities_vs_gt_100.csv`

| Prompt / Model | Valid rows | Missing/error rows | Canonical F1 | Entity-type F1 | Outcome |
|---|---:|---:|---:|---:|---|
| Original teammate extraction | 100 | 0 | 0.4950 | 0.7174 | Strongest initial baseline. |
| `central_v1` | 100 | 0 | 0.2617 | 0.6429 | Worse than baseline. |
| `anti_generic_v2` + GPT-OSS-20B | 99 | 1 | 0.4729 | 0.5942 | Stable enough, but below baseline. |
| `candidate_rank_v3` + GPT-OSS-20B | 82 | 18 | 0.2545 | 0.4385 | Longer prompt caused invalid/truncated JSON. |
| `anti_generic_v2` + Llama 3.3 70B | 100 | 0 | 0.4876 | 0.5780 | Best new model for canonical names, but weak type F1. |
| `anti_generic_v2` + GPT-OSS-120B | 100 | 0 | 0.3381 | 0.6181 | Stable but poor canonical matching. |
| `candidate_rank_v3` + Llama 3.3 70B | 100 | 0 | 0.4912 | 0.5138 | Nearly matched canonical baseline, but type F1 was weak. |

Conclusion: prompt engineering and model switching alone did not beat the teammate baseline. The main issue was not only model strength; it was central-entity selection, canonicalization, and type consistency.

### Ensemble Entity Improvement

The best entity extraction improvement came from constrained post-processing:

| Strategy | Changed rows | Canonical F1 | Entity-type F1 | Outcome |
|---|---:|---:|---:|---|
| Original teammate extraction | 0 | 0.4950 | 0.7174 | Baseline. |
| Llama-rank name + original type | 100 | 0.4912 | 0.7174 | Preserved type but did not improve canonical F1. |
| Llama-rank name + voted type | 100 | 0.4912 | 0.6292 | Type voting hurt. |
| Specificity switch + original type | 15 | 0.5317 | 0.7174 | Best reportable improvement. |
| Agreement switch + original type | 5 | 0.5133 | 0.7174 | Improved but less than specificity switch. |

Successful idea:

- Keep the original entity type.
- Replace only generic canonical names when a more specific model-extracted entity appears in the source QA text.

This became the basis for protecting and refining the larger 2k+ entity inventory instead of discarding it.

### 500-Row Ground Truth Expansion

The 500-row file was created to debug entity extraction beyond the first 100 rows.

| Label source | Rows | Meaning |
|---|---:|---|
| `reviewed_handoff` | 300 | Existing reviewed labels from teammate hand-off. |
| `assistant_reviewed` | 200 | Assistant-reviewed labels based on source QA and Llama candidate-rank pre-annotations. |

Evaluation against Llama candidate-rank on the 500-row file:

| Feature | Precision | Recall | F1 |
|---|---:|---:|---:|
| Canonical name | 0.6470 | 0.6332 | 0.6343 |
| Entity type | 0.7537 | 0.7197 | 0.7284 |

Caveat:

Rows 301-500 are useful for internal development, but for formal publication they should ideally be checked by a human reviewer or second annotator.

### Refined Entity Inventory

Step 03G applied quality-control signals learned from the reviewed benchmark to the large entity inventory.

| Item | Count |
|---|---:|
| Total entities processed | 2253 |
| Graph-ready entities | 2072 |
| Mention rows read | 5904 |
| Graph-ready mention rows kept | 4308 |
| Mention rows held back | 1596 |
| Rows with refinement actions | 99 |
| Rows flagged for review | 181 |

Most common quality flags:

| Flag | Count |
|---|---:|
| Duplicate canonical name | 149 |
| Canonical name not in aliases | 32 |
| Generic canonical name | 26 |
| Body-part/type mismatch | 6 |
| Very short name | 6 |
| Too long for canonical name | 2 |

Outcome:

The refined graph-ready files were used to rebuild the graph:

- `outputs/03_entity_extraction/refinement/ahd_entities_llm_merged_graph_ready.csv`
- `outputs/03_entity_extraction/refinement/ahd_entity_mentions_llm_merged_graph_ready.csv`

## Graph and Retrieval Experiments

### Refined Graph Rebuild

After entity refinement, relation extraction and validation were rerun on the refined inventory.

| Output | Count |
|---|---:|
| Graph-ready entities | 2072 |
| Graph-ready mentions | 4308 |
| QA/source records | 1411 |
| Direct validated relations | 471 |
| Bidirectional relation rows | 942 |
| Embedding documents | 7791 |

Files:

- `outputs/04_relation_extraction/ahd_relations_llm_validated_refined.csv`
- `outputs/04_relation_extraction/ahd_relations_neo4j_bidirectional_refined.csv`
- `outputs/05_trial_graph_v1_refined/`

Result:

The refined graph was structurally cleaner, but retrieval still failed on many user questions because the graph did not contain enough direct evidence for high-value medical facts.

### Step 8 Synonym Expansion and Partial Answerability

Step 8 was extended to improve query understanding:

- Arabic normalization.
- Synonym and alias expansion.
- Detected entities.
- Semantic candidate entities.
- Intent detection.
- Relation-priority selection.
- Non-overlapping evaluation through `--offset`.

This helped retrieval find more relevant graph seeds, but it did not fully solve coverage gaps when the graph lacked the needed facts.

### Supplemental AHD-Backed Facts

The first supplemental layer targeted repeated missing facts from low-evidence outputs.

Initial focused expansion:

| Stage | Supplemental entities | Supplemental relations | Supplemental QA sources |
|---|---:|---:|---:|
| First supplemental layer | 46 | 26 | 19 |
| Targeted supplemental facts | 74 | 41 | 27 |
| Exact-source expansion | 170 | 89 | 73 |

Successful targeted examples:

- Thyroid disease during pregnancy.
- Fetal bone formation.
- Normal blood pressure/heart rate.
- TSH/TAH interpretation.
- Cephadar for dental pain.
- Anemia nutrition.
- Post-surgery urinary symptoms.
- Prothrombin test interpretation.
- Gum color/inflammation.
- G6PD anemia.
- Breast swelling/pain requiring specialist review.

Important caveat:

The exact-source expansion uses exact AHD source QA matches. This is useful for improving an AHD-based QA system and should be reported as provenance-preserving source-answer expansion. It should not be presented as independent external guideline knowledge.

### Step 9C Supplemental Ranking Fix

Problem:

New supplemental relation types such as `IMPORTANT_FOR`, `HAS_SAFETY_NOTE`, `ANSWERED_BY_SOURCE_QA`, and `REQUIRES_SPECIALIST_ASSESSMENT_FOR` were being penalized by the default negative relation weight.

Fix:

Step 9C now boosts reviewed supplemental facts when they overlap the query:

- `supp_rel_*`
- `focus_rel_*`
- `target_rel_*`
- `exact_rel_*`

Result:

Targeted facts moved to top retrieval positions. For example:

- Thyroid/pregnancy evidence became rank 1-2.
- Cephadar dental pain became rank 1.
- Anemia nutrition became rank 1.
- Prothrombin source answer became rank 1.
- TAH/TSH source answer became rank 1.

This was one of the most important retrieval improvements.

## Generation and Hallucination-Mitigation Experiments

### Model Change to GPT-OSS-20B

Qwen was removed from Groq availability, so Step 12 was run with:

```bash
--model openai/gpt-oss-20b
```

GPT-OSS-20B worked, but required multiple API-key passes because Groq daily usage limits interrupted the 100-query run. No API keys are stored in the repository.

### Step 12 Grounded Fallback and Step 15 Preservation Fix

This experiment explains why the mean reliability score increased sharply after
the generation and mitigation fixes.

Problem before the fix:

The LLM sometimes answered with `لا توجد أدلة كافية` even when Step 11 had
already retrieved usable graph evidence. The pipeline accepted the abstention,
so many outputs were marked as insufficient evidence. This made reliability
very low because the scorer saw no supported answer, weak evidence coverage,
and poor answerability.

Fixes applied:

- Step 12 now applies a grounded fallback when the LLM says
  `لا توجد أدلة كافية` but retrieved evidence exists.
- The fallback selects the best evidence using query-evidence overlap, not only
  the top rerank score.
- Step 15 now preserves fully supported answers instead of rewriting them into
  short claim fragments.
- No new Groq calls were needed after the fix because existing raw responses
  were revalidated and passed through the corrected local pipeline.

Before/after result:

| Run | BERTScore F1 | Answerability | Mean reliability | Claim support | Hallucination |
|---|---:|---|---:|---:|---:|
| Before fallback/preservation fix | 0.645308 | 91 insufficient, 8 answerable, 1 partial | 0.253371 | Not final | Not final |
| After fallback/preservation fix | 0.646856 | 99 answerable, 1 partial | 0.8094 | 0.9911 | 0.0089 |

Simple example:

If the user asks about normal blood pressure, retrieval may contain a useful
evidence sentence such as: normal blood pressure is around `120/80` and a
doctor should be consulted when readings are abnormal. Before the fix, the LLM
could still answer `لا توجد أدلة كافية`, and the final output would be scored
as low reliability because it contained no usable supported answer. After the
fix, Step 12 chooses the retrieved evidence as a grounded fallback. The final
answer then contains a supported claim, so answerability, evidence coverage,
and reliability all increase.

Why reliability improved more than BERTScore:

BERTScore measures semantic similarity to the reference answer. It improved
only slightly because the wording of the final answer did not always become
much closer to the reference. Reliability improved dramatically because the
pipeline changed many outputs from "insufficient evidence" into supported,
evidence-backed answers. In other words, the main gain was not more fluent
wording; it was avoiding unnecessary abstention when retrieved evidence was
available.

Files from this checkpoint:

- Final answers: `outputs/05_trial_graph_v1/final_output/trial_graph_v1_final_explainable_output.csv`
- Final BERTScore: `outputs/05_trial_graph_v1/evaluation/teammate100_final_bertscore_fixed.csv`
- Summary: `outputs/05_trial_graph_v1/evaluation/teammate100_final_bertscore_fixed_summary.json`

### Random Unseen 100-Question Generalization Checks

After tuning on the teammate 100-question benchmark, three additional random
100-question AHD samples were created to check whether the pipeline generalizes
to questions that were not used during debugging. The sampler uses a fixed seed
for reproducibility, samples across categories, and excludes previously used
questions.

| Run | Seed | Excluded previous questions | Categories | Max per category | BERTScore P | BERTScore R | BERTScore F1 | Answerability | Reliability | Claim support | Hallucination |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|---:|---:|
| Previous tuned benchmark | N/A | N/A | N/A | N/A | 0.665098 | 0.655970 | 0.659652 | 100 answerable | 60 high, 40 medium | 1.0 | 0.0 |
| Unseen random 100, first sample | 20260726 | 100 | 90 | 2 | 0.666061 | 0.658194 | 0.661048 | 100 answerable | 54 high, 46 medium | 1.0 | 0.0 |
| Unseen random 100, second sample | 20260727 | 200 | 88 | 2 | 0.651055 | 0.655511 | 0.652023 | 100 answerable | 57 high, 43 medium | 1.0 | 0.0 |
| Unseen random 100, third sample with category-aware fallback | 20260728 | 300 | 87 | 2 | 0.651960 | 0.661303 | 0.655481 | 100 answerable | 62 high, 36 medium, 2 low | 1.0 | 0.0 |

Interpretation:

The first unseen sample slightly exceeded the tuned benchmark, while the second
unseen sample dropped to BERTScore F1 `0.652023`. This means the system is not
overfitted only to the original 100 questions, but the final-answer similarity
still varies by random sample and category mix. The reliability behavior is
more stable than BERTScore: both unseen samples remained 100 percent
answerable, with no unsupported verified claims and mean reliability around
`0.802`.

The second unseen sample was then used for retrieval error analysis and
ablation. The main finding was that the weaker score was mostly caused by
retrieval coverage gaps, not by hallucination. The QA fallback helped overall:
removing it reduced BERTScore F1 from `0.652023` to `0.647568` and created 3
insufficient answers. Raising the fallback threshold to `0.50` also hurt
BERTScore and reliability. A category-aware QA fallback was then tested by
preferring non-exact AHD fallback rows from the same category as the query.

Second-sample fallback ablations:

| Variant | BERTScore F1 | Answerability | Mean reliability | Decision |
|---|---:|---|---:|---|
| Baseline QA fallback, threshold 0.42 | 0.652023 | 100 answerable | 0.8020 | Baseline |
| No QA fallback | 0.647568 | 97 answerable, 3 insufficient | 0.7831 | Worse |
| QA fallback threshold 0.50 | 0.649710 | 97 answerable, 3 insufficient | 0.7814 | Worse |
| Category-aware fallback, bonus 0.08 | 0.652421 | 100 answerable | 0.8048 | Best conservative change |
| Category-aware fallback, bonus 0.12 | 0.654258 | 99 answerable, 1 insufficient | 0.7978 | Higher BERTScore, small safety cost |
| Category-aware fallback, bonus 0.15 | 0.654657 | 98 answerable, 2 insufficient | 0.7904 | Highest BERTScore, not recommended |
| Targeted fallback: question+answer scoring, bonus 0.08, min overlap 2 | 0.649382 | 97 answerable, 2 insufficient, 1 partial | 0.7935 | Worse; keep as failed ablation |

The selected change for the next unseen test was the conservative
category-aware fallback with bonus `0.08`. On the third unseen 100-question
sample, this configuration achieved BERTScore F1 `0.655481`, 100 answerable
outputs, and zero unsupported verified claims. This did not beat the first
unseen sample, but it improved over the second-sample baseline while preserving
the trustworthiness constraints.

A later targeted retrieval attempt tested an optional Step 11 fallback scorer
that compares the query against both AHD source questions and source answers,
filters common Arabic stopwords, and requires at least two informative
overlapping tokens. Although it improved some individual low-coverage contexts,
it hurt aggregate performance on the second unseen set: BERTScore F1 dropped
to `0.649382`, fully answerable outputs dropped to 97, and mean reliability
dropped to `0.7935`. This confirms that the retrieval bottleneck is not solved
by simply broadening lexical fallback scoring; future improvements should focus
on targeted graph coverage or curated synonym/fact additions for recurring
medical concepts.

Important caveat:

The references are AHD source answers, not expert-adjudicated clinical gold
answers. These scores should be described as similarity to source answers, not
as proof of clinical correctness.

Files:

- First unseen sample: `retrieval_gold_annotations_unseen_100_random.csv`
- First unseen final output: `outputs/05_trial_graph_v1/evaluation/unseen100_random_live_groq_full_100_final_output_t042.csv`
- First unseen BERTScore: `outputs/05_trial_graph_v1/evaluation/unseen100_random_live_groq_full_100_t042.csv`
- Second unseen sample: `retrieval_gold_annotations_unseen_100_random_seed20260727.csv`
- Second unseen final output: `outputs/05_trial_graph_v1/evaluation/unseen100_random_seed20260727_live_groq_full_100_final_output_t042.csv`
- Second unseen BERTScore: `outputs/05_trial_graph_v1/evaluation/unseen100_random_seed20260727_live_groq_full_100_t042.csv`
- Error analysis report: `reports/unseen100_random_error_analysis_report.md`
- Targeted fallback failed ablation: `outputs/05_trial_graph_v1/evaluation/unseen100_random_seed20260727_targeted_fallback_question_answer_t042_b008_overlap2_live_groq_full_100.csv`
- Targeted fallback failed ablation final output: `outputs/05_trial_graph_v1/evaluation/unseen100_random_seed20260727_targeted_fallback_question_answer_t042_b008_overlap2_live_groq_full_100_final_output.csv`
- Third unseen sample: `retrieval_gold_annotations_unseen_100_random_seed20260728.csv`
- Third unseen final output: `outputs/05_trial_graph_v1/evaluation/unseen100_random_seed20260728_category_aware_fallback_t042_b008_live_groq_full_100_final_output.csv`
- Third unseen BERTScore: `outputs/05_trial_graph_v1/evaluation/unseen100_random_seed20260728_category_aware_fallback_t042_b008_live_groq_full_100.csv`

### Strict Hallucination Mitigation

Strict mode keeps only `supported` claims and removes:

- `weakly_supported`
- `unsupported`

Strict final result:

| Metric | Value |
|---|---:|
| Answerable | 88 |
| Partially answerable | 1 |
| Insufficient evidence | 11 |
| Mean reliability | 0.7563 |
| Verified hallucination rate | 0.0000 |

Result:

Very safe, but one weakly supported answer was downgraded.

### Controlled Lenient Mitigation

Controlled lenient mode uses:

```bash
python scripts\step15_mitigate_hallucinations.py --include-weak
```

This keeps `weakly_supported` claims but still removes `unsupported` claims.

Final result:

| Metric | Value |
|---|---:|
| Answerable | 89 |
| Partially answerable | 0 |
| Insufficient evidence | 11 |
| Mean reliability | 0.7578 |
| Verified hallucination rate | 0.0000 |

Conclusion:

This is the best compromise tested. It increases answer coverage without introducing verified hallucination.

### Unsafe Compromise Not Recommended

We considered relaxing hallucination mitigation more aggressively because the goal is to answer as many questions as possible.

Rejected option:

- Keep unsupported claims.
- Let the model answer beyond evidence.
- Hide uncertainty.

Reason:

This would damage the main research contribution: explainable and trustworthy Graph-RAG for Arabic medical QA. It would also make reliability scoring less meaningful.

Recommended compromise:

- Keep weakly supported claims.
- Remove unsupported claims.
- Show reliability score and evidence limitations.
- Add more source coverage for the remaining insufficient cases.

## Remaining Failure Cases

After the best final run, 11 questions still return insufficient evidence. These are mostly cases where:

- The graph retrieves related but not direct evidence.
- The source answer is too vague.
- The question asks for specialist lists or complex diagnosis.
- The model remains conservative despite context.

Examples include:

- Cow milk allergy and HA formula substitution.
- Difference between systemic blood pressure and eye pressure.
- Dental symptoms with headache/eye/ear symptoms.
- Allergy/asthma treatments and pregnancy delay.
- Sickle-cell carrier premarital counseling.
- Chiari II medical center list.
- Iron sulfate/vitamin B and acne.
- Chest pain with prior normal cardiac workup.
- Thyroid cure duration.
- CT contrast and face/gland swelling.
- Drug stopping question with unspecified drug.

These should be treated as next candidates for:

- Additional AHD-backed supplemental facts.
- External guideline-cited facts.
- Better prompt handling for exact source-answer evidence.
- A broader retrieval batch.

## Reproducible Final Command Sequence

After graph and embeddings are ready, the final recommended sequence is:

```bash
python scripts\step08_understand_queries.py --from-qa --limit 100 --offset 0 --graph-covered-only --scan-limit 1000
python scripts\step09a_semantic_retrieval.py --top-k 25
python scripts\step09c_hybrid_retrieval.py --top-relations 50 --top-contexts 30
python scripts\step10_rerank_subgraphs.py
python scripts\step11_build_evidence_contexts.py
python scripts\step12_generate_answers.py --run-live --provider groq --force-overwrite --limit 100 --model openai/gpt-oss-20b --sleep-seconds 8 --stop-on-rate-limit
python scripts\step13_extract_claims.py
python scripts\step14_verify_claims.py
python scripts\step15_mitigate_hallucinations.py --include-weak
python scripts\step16_score_reliability.py
python scripts\step17_build_final_output.py
```

If Groq stops on rate limit, resume Step 12 after resetting/changing the key:

```bash
python scripts\step12_generate_answers.py --run-live --provider groq --resume --limit 100 --model openai/gpt-oss-20b --sleep-seconds 8 --stop-on-rate-limit
```

Do not commit API keys. Use `.env` locally or process-only environment variables.

## What Succeeded

- The claim verification and hallucination mitigation layer worked well.
- Verified hallucination reached `0.0` in the final live run.
- Supplemental AHD-backed facts greatly reduced `لا توجد أدلة كافية`.
- Exact AHD source-answer expansion helped when the evaluated query exactly matched a dataset QA record.
- Step 9C ranking fix was essential for surfacing supplemental facts.
- Controlled leniency with `--include-weak` improved answerability without allowing unsupported claims.
- Entity refinement preserved the large 2k entity inventory while removing lower-confidence graph nodes.

## What Did Not Succeed

- Prompt-only entity extraction did not beat the teammate baseline.
- Larger models did not automatically improve entity extraction.
- The `candidate_rank_v3` prompt was unstable with GPT-OSS-20B because of JSON truncation/errors.
- The first supplemental layer improved 25 queries but did not generalize to 50/100 queries.
- Extractive fallback gave complete outputs but lowered reliability, so it should not be used as the final answer-generation method.
- Aggressively allowing unsupported claims would undermine the trustworthiness contribution.

## Recommended Next Experiments

1. Add guideline-cited facts for the 11 remaining insufficient cases.
2. Run the final configuration on 200 or 500 queries.
3. Separate AHD exact-source expansion from true graph generalization in ablation tables.
4. Add an ablation without supplemental facts.
5. Add an ablation without hallucination mitigation.
6. Add latency tracking per step for efficiency reporting.
7. Human-review the assistant-reviewed rows 301-500 before using them as formal gold labels.
