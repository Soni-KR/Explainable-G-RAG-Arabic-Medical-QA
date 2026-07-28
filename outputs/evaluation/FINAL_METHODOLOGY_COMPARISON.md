# Final Methodology Comparison: Root Pipeline vs. Aziza Trial

## 1. Scope

This report compares the retained root pipeline with the work in
`aziza-trial`. It uses only saved code, manifests, graph files, annotations,
and evaluation outputs. No retrieval, generation, API, or Neo4j experiment was
rerun for this audit.

The goal is to identify:

1. Which work is genuinely shared.
2. Which methodological choices differ.
3. Which reported results are directly comparable.
4. Which ideas should be adopted, rejected, or retested.
5. The final defensible architecture and evaluation methodology.

## 2. Executive Decision

Use the root production architecture as the final system:

- frozen `final_v1` graph;
- `intfloat/multilingual-e5-base` embeddings over the final Neo4j graph;
- one GPT-OSS-20B query-analysis call followed by deterministic linking;
- vector, validated-graph, and QA/evidence retrieval;
- conditional held-out-safe SQLite FTS expansion;
- deterministic reranking with identity, intent, anatomy, generic-node, and
  unrelated-condition controls;
- selective evidence context construction;
- GPT-OSS-20B grounded generation;
- claim support and query-relevance verification;
- abstention when evidence is insufficient.

Do not merge the current supplemental graph into `final_v1`.

The best ideas to borrow from the Aziza trial are:

- a small category-aware QA ranking feature;
- explicit provenance for supplemental facts;
- evaluating several independently sampled question cohorts;
- a future, separately versioned supplemental graph after independent human
  validation.

Do not borrow:

- `ANSWERED_BY_SOURCE_QA` as a medical graph relation;
- supplemental relation-ID prefix bonuses;
- forced extractive answers after model abstention;
- always-on full-dataset QA fallback;
- lexical-overlap-only claim verification;
- self-reported `100% answerable`, `100% supported`, or `0% hallucination`
  metrics produced by those mechanisms.

## 3. Critical Shared-Graph Finding

The following five root and Aziza graph files have identical SHA-256 hashes:

- `entities.csv`
- `entity_mentions.csv`
- `relation_decisions.csv`
- `relations.csv`
- `relations_bidirectional.csv`

Therefore, the construction of the base `final_v1` graph is shared work, not a
comparison between two different final graphs.

The shared final graph contains:

| Object | Count |
|---|---:|
| Medical entities | 2,175 |
| Evidence mentions | 5,767 |
| Accepted direct relations | 1,404 |
| Bidirectional relation rows | 2,808 |
| QA records referenced by the graph | 2,549 |

However, the selected Aziza scripts do not consistently consume these final
files. Their retained paths and embedding metadata point to the older
`trial_graph_v1` static CSV graph:

| Old trial object | Count |
|---|---:|
| Medical entities | 543 |
| Evidence mentions | 1,122 |
| QA records | 480 |
| Direct relations | 185 |
| Bidirectional relation rows | 370 |

This distinction must be stated in any dissertation or paper. Copying
`final_v1` files into a folder does not establish that the evaluated code used
them.

## 4. Step-by-Step Comparison

### Step 5: Graph Construction

**Root**

- Uses the shared, validated `final_v1` graph in Neo4j.
- Keeps entities, mentions, QA records, and medical relations as separate
  schema objects.
- Filters all production queries by configured `graph_version`.

**Aziza trial**

- Includes the same final graph files, but selected scripts use the old trial
  graph through static CSV paths.
- Adds a supplemental layer with 170 entities, 89 relations, and 73 QA rows in
  the currently retained files.
- Documentation also cites older supplemental counts of 46 entities,
  26 relations, and 19 QA rows, so the retained documentation and artifacts
  are not version-consistent.

**Decision**

Keep `final_v1`. Do not import the current supplemental layer.

### Step 6: Embeddings and Indexing

**Root**

- Model: `intfloat/multilingual-e5-base`.
- Dimension: 768.
- Embeds final `MedicalEntity`, `EvidenceMention`, and `QARecord` documents.
- Uses Neo4j vector indexes tied to `final_v1`.

**Aziza trial**

- Model metadata: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`.
- Retained metadata describes 2,145 documents, exactly matching the old trial
  graph: 543 entities + 1,122 mentions + 480 QA records.
- The referenced embedding JSONL is not present in the handover.

**Decision**

Use the root E5 indexes. They represent the actual final graph and use a
stronger multilingual retrieval model.

### Step 8: Query Understanding

**Root**

- Conservative Python Arabic normalization.
- One GPT-OSS-20B call for correction, reformulation, classification, intent,
  and explicit medical phrase extraction.
- Deterministic exact canonical, alias, and article-normalized Neo4j linking.
- Deterministic retrieval planning.
- Keeps generic linked entities as low-specificity seeds.

**Aziza trial**

- Mostly deterministic normalization, dictionaries, synonym expansion, and
  intent rules over a static CSV vocabulary.
- Cheap and reproducible, but brittle for unseen wording and tied to old graph
  files.
- Its evaluation-target builder explicitly marks entity targets as
  `silver_from_step8_entity_links`.

**Decision**

Use the root flow. Borrow only manually reviewed synonym or category
dictionaries as low-confidence expansions. Never use Step 8 outputs as their
own retrieval ground truth.

### Step 9: Retrieval

**Root**

- E5 vector retrieval over entities, mentions, and QA records.
- One-hop traversal of validated `final_v1` medical relations.
- Held-out-safe SQLite FTS over QA records.
- Conditional targeted FTS only when ordinary retrieval has partial evidence
  but no strong direct candidate.
- Supplemental graph disabled.

**Aziza trial**

- Traverses the old static trial graph plus supplemental CSV relations.
- Gives a score bonus to relation IDs beginning with `target_rel_`,
  `focus_rel_`, `supp_rel_`, or `exact_rel_`.
- Uses a full scan of `AHD.csv` for nearest non-exact QA fallback.
- The fallback is added whenever its threshold passes, not only after a
  demonstrated retrieval failure.

**Decision**

Use the root retrieval pipeline. A small category bonus can be tested inside
the conditional FTS channel. Do not give a bonus because an edge came from the
supplemental graph.

### Step 10: Reranking

**Root**

The current deterministic reranker considers:

- medical concept coverage;
- entity identity;
- intent support;
- anatomy compatibility;
- semantic similarity;
- source quality;
- generic-node penalties;
- unrelated-condition penalties;
- direct-question anchors.

The learned two-stage reranker remains disabled because grouped OOF gains did
not yet translate into a sufficiently strong production replay.

**Aziza trial**

The retained graph-edge score is dominated by:

- maximum hybrid score: weight 0.52;
- mean repeated hybrid score: 0.12;
- primary-intent match: 0.10;
- evidence count: 0.10;
- unique QA count: 0.08;
- evidence relevance: 0.05;
- direct-edge support: 0.06;
- relation weight: 0.07.

It does not explicitly penalize wrong entity identity, wrong anatomy, generic
nodes, or unrelated conditions.

**Decision**

Use the root reranker. Add category compatibility only as a small feature
after identity, anatomy, and intent gates.

### Step 11: Evidence Context

**Root**

- Uses absolute relevance and directness gates.
- Keeps a small, dynamic context rather than filling a fixed quota.
- Selects at most the strongest evidence needed for the query.
- Runs targeted FTS conditionally.
- Allows empty context and an honest insufficient-evidence outcome.

**Aziza trial**

- Selects graph evidence, then independently adds the nearest non-exact AHD QA
  fallback whenever its lexical threshold passes.
- This can improve coverage, but it can also add a medically unrelated answer
  merely because a few words or a category overlap.

**Decision**

Use the root context builder. Test the Aziza category bonus as an ablation,
not as an unconditional fallback.

### Step 12: Answer Generation

**Root**

- Uses GPT-OSS-20B.
- Generates only from the selected context.
- Keeps technical failures separate from retrieval insufficiency.
- Does not convert every abstention into an apparently substantive answer.

**Aziza trial**

- If the model abstains, `apply_abstention_fallback()` copies the highest
  ranked evidence into the final answer.
- It then creates a claim identical to that evidence and labels the claim
  supported.
- In the selected seed-20260728 output, 90 of 100 answers contain the
  extractive-fallback limitation; only 10 are ordinary generated answers.

**Decision**

Do not use forced extractive fallback. An extractive answer is acceptable only
when an exact QA anchor or independently human-labeled direct candidate passes
query-relevance and safety checks.

### Steps 13-15: Claims, Verification, and Mitigation

**Root**

- Extracts atomic claims.
- Verifies evidence support and claim-to-query relevance.
- Checks intent, anatomy, negation, numbers, and recommendations.
- Removes unsupported claims.
- Distinguishes complete, partial, supported-but-incomplete, insufficient, and
  unavailable outcomes.

**Aziza trial**

- Primarily uses lexical token overlap.
- Default structured-claim thresholds are 0.08 for supported and 0.04 for
  weakly supported.
- `--include-weak` retains weak claims.
- Valid citation or QA identifiers can help a weak claim survive even without
  adequate semantic/query relevance.

**Decision**

Use the root verifier. Its false-rejection rate is a real remaining problem,
but weakening it without human labels would trade visible abstention for
hidden medical error.

The next verifier dataset should separately label:

1. Evidence supports the claim.
2. The claim answers the query.
3. The claim preserves anatomy, negation, numbers, and recommendation scope.

### Step 16: Reliability

**Root**

- Reports a reliability score and accept/flag/abstain state.
- Correctly treats current reliability as uncalibrated until human correctness
  labels support AUROC, AUPRC, calibration, and threshold analysis.

**Aziza trial**

- Reliability largely reuses the same context and lexical-verifier signals
  that produced the answerability decision.
- High reliability therefore does not independently prove correctness.

**Decision**

Use the root reliability output, but label it `uncalibrated` until a separate
human outcome set exists.

### Step 17: Explainable Output

Use the root output contract:

- answer or abstention;
- cited evidence IDs and QA IDs;
- retained and removed claims;
- answerability state;
- reliability state;
- limitations.

## 5. Supplemental Graph Audit

The supplemental approach is potentially useful, but the retained version is
not ready for final evaluation or import.

### What the retained artifacts show

- 89 direct supplemental relations.
- Confidence values between 0.97 and 0.99.
- 48 relations are `ANSWERED_BY_SOURCE_QA`.
- 71 unique QA sources.
- 170 entities include `QuestionTopic`, `SourceAnswer`, and several entity
  types outside the fixed medical schema.
- The candidate-review file has 84 rows, all with
  `review_status=needs_review`.

The retained artifacts therefore do not demonstrate independent human
validation of the 89 accepted relations.

### Why `ANSWERED_BY_SOURCE_QA` is problematic

An exact source answer is valuable evidence, but it is not a medical relation
between two medical concepts. Modeling:

`QuestionTopic -> ANSWERED_BY_SOURCE_QA -> SourceAnswer`

as `MEDICAL_RELATION` mixes document retrieval with medical knowledge.
Constructing such edges from queries that failed evaluation also leaks
evaluation answers back into the graph.

### Defensible supplemental-v2 design

If supplemental coverage is pursued:

1. Build facts only from `graph_train`, never evaluation failures.
2. Keep source answers as `QARecord` or `EvidenceMention`, not
   `MedicalEntity`.
3. Exclude `QuestionTopic`, `SourceAnswer`, and `ANSWERED_BY_SOURCE_QA`.
4. Use the fixed entity types unless a schema extension is approved in
   advance.
5. Require two independent human decisions per medical relation.
6. Store evidence, provenance, annotator IDs, and disagreement resolution.
7. Import as `supplemental_v2`, separate from `final_v1`.
8. Test it as an optional retrieval channel on a fresh untouched set.

Only then can `final_v1` versus `final_v1 + supplemental_v2` be a valid
ablation.

## 6. Comparable Results

### 6.1 Human-labeled root retrieval

Original candidate pool:

- 540 human-confirmed candidates across 99 candidate-bearing queries.
- Labels: 335 irrelevant, 157 partial, 48 direct.
- FTS QA direct yield: 32/196 = 16.33%.
- Vector direct yield: 16/296 = 5.41%.
- Graph channels: 0 direct candidates.

After conditional targeted FTS:

- 963 human-confirmed candidates.
- Labels: 620 irrelevant, 281 partial, 62 direct.
- Queries with direct evidence: 37/99 -> 49/99.
- Direct Recall@5: 0.3636 -> 0.3838.
- Direct Recall@10: 0.4141.
- MRR: 0.2279 -> 0.2441.
- Step 11 known-useful queries: 51 -> 56.
- Step 11 known-direct queries: 25 -> 29.

These are the strongest current retrieval results because candidate relevance
was independently human labeled.

### 6.2 Root frozen 100-question generation run

Run:
`full_pipeline_retrieval_v2_targeted_fts_reranked_network_v1`

| Outcome | Count |
|---|---:|
| Generated | 66 |
| Fallback/abstention | 34 |
| Empty due to retrieval | 30 |
| Technical failure | 4 |
| Substantive claim-bearing answers | 26 |
| Fully answerable | 2 |
| Partially answerable | 4 |
| Supported but incomplete | 20 |
| Insufficient evidence | 70 |
| Unavailable | 4 |

BERTScore F1:

- all 100: 0.660743;
- generated 66: 0.665957;
- substantive 26: 0.675803.

Claim audit:

- pre-mitigation claims: 114;
- supported: 36;
- weak: 3;
- unsupported: 75;
- retained: 36;
- removed: 78.

Post-mitigation support rate 1.00, hallucination rate 0.00, and citation
validity 1.00 apply only to the 26 substantive claim-bearing answers. They are
not results over all 100 questions.

Reliability:

- high: 3;
- medium: 9;
- low: 88;
- mean: 0.1592.

Mean end-to-end latency: 15,602 ms.

### 6.3 Root known-answer diagnostic

When the exact QA answer was permitted:

- SQLite exact QA available: 100/100;
- exact QA survived retrieval, reranking, and Step 11: 100/100;
- generated: 98;
- fallbacks: 2;
- substantive answers after verification: 33;
- substantive BERTScore F1: 0.744325.

The main loss happened after generation:

- 198 claims;
- 57 supported;
- 4 weak;
- 137 unsupported;
- 141 removed;
- 101 removed claims had support score >= 0.4;
- 81 were identified as likely query-relevance-gate false rejections.

This proves that exact-answer retrieval works and that verifier recall, not
retrieval alone, is now a major bottleneck.

### 6.4 Human verifier adjudication update

The completed human review is:

`outputs/evaluation/entity_gt_trial_100/known_answer_diagnosis/known_answer_removed_claim_review_queue_human_reviewed.csv`

All 81 queued claims are labeled consistently:

- 67 should have been retained;
- 14 were correctly removed;
- the 67 false rejections affect 47 distinct queries.

Among the 67 valid claims:

- `intent_mismatch`: 62;
- `claim_query_concept_mismatch`: 19;
- `anatomy_mismatch`: 4.

Human labels confirm that all 67 retained claims were evidence-supported,
query-relevant, intent-compatible, and concept-compatible. Across all
81 reviewed claims:

- 72 were fully evidence-supported;
- 74 were query-relevant;
- 75 had a valid intent match;
- 75 had a valid concept match.

The 82.7% false-rejection rate applies specifically to this queue of
81 suspected verifier mistakes. It must not be presented as the false-rejection
rate over every generated or removed claim.

The review disproves two simple fixes:

1. Considering Step 8 secondary intents with the current lexical intent rule
   would recover only 8 of the 62 valid intent failures while also admitting
   3 of the 11 invalid intent failures.
2. A grouped five-fold logistic model using the retained deterministic
   verifier features achieved only 0.6914 OOF AUROC. At threshold 0.50 it
   retained 50/67 valid claims but incorrectly admitted 5/14 invalid claims.

The current metadata and lexical features therefore do not safely separate the
two classes. `query_concept_coverage` must not be relaxed or inverted as a
global rule: valid reviewed claims had lower average coverage than correctly
removed claims.

The next verifier design should:

- retain citation, evidence, negation, number, recommendation, and explicit
  identity/anatomy safety checks;
- treat lexical intent and concept checks as soft escalation signals rather
  than final rejection gates;
- send only disputed claims to a semantic claim-evidence-query adjudicator;
- evaluate that adjudicator with query-grouped splits so prompt examples and
  test claims never share a query;
- keep query coverage as an answer-completeness measure in Step 15/16 rather
  than using it alone to reject an individually supported claim;
- fall back to the conservative deterministic result when semantic
  adjudication is unavailable.

The 81 claims are a calibration/development set, not enough evidence for direct
LLM fine-tuning. A local verifier should be trained only after adding accepted
claims, ordinary unsupported claims, contradiction cases, and a fresh
query-level holdout.

### 6.5 Restricted semantic-adjudication pilot

A selective GPT-OSS-20B adjudicator was implemented behind
`CLAIM_ADJUDICATION_ENABLED=false`. It reviews only claims already rejected by
the deterministic verifier when the remaining failures are soft intent,
concept, or anatomy gates. The 18-claim pilot sent only:

- 12 Arabic questions;
- disputed claim text;
- cited evidence segments.

It did not send human annotations, expected labels, reference answers, database
identifiers, unrelated rows, credentials, or personal identifiers.

The pilot contained 10 human-retain and 8 human-remove claims. Its initial
results were:

| Measure | Result |
|---|---:|
| True positives | 10 |
| True negatives | 3 |
| False positives | 5 |
| False negatives | 0 |
| Retain precision | 0.666667 |
| Retain recall | 1.000000 |
| Retain F1 | 0.800000 |
| Removal specificity | 0.375000 |

The semantic judge recovered every valid pilot claim, but admitting 5/8
correct removals is unsafe. The full 81-claim API evaluation was therefore not
run.

The pilot also exposed an evidence-provenance defect: some
`mention_evidence` passages were copied from the source question, and the
mention `field` was lost between Neo4j retrieval and Step 11. Two false accepts
were question restatements rather than answer facts.

The local pipeline now:

- preserves `EvidenceMention.field` through Steps 9-11;
- marks each item as question, answer, validated relation, or unknown origin;
- removes question-only mentions before generation;
- replaces a question-origin mention with its linked source answer when one is
  available;
- excludes question text from Step 14 factual support;
- recomputes semantic-adjudication eligibility from authoritative answer and
  relation segments.

A conservative offline re-audit reused a cached semantic decision only when
its authoritative evidence payload was unchanged. It projected:

| Measure | Result |
|---|---:|
| True positives | 10 |
| True negatives | 5 |
| False positives | 3 |
| False negatives | 0 |
| Retain precision | 0.769231 |
| Retain recall | 1.000000 |
| Retain F1 | 0.869565 |
| Removal specificity | 0.625000 |

This is an improvement, not a passing result. The three remaining false accepts
are a changed causal/category relationship, generic unrelated follow-up
advice, and a wrong named drug. The feature remains disabled, production
Steps 14-17 were not replayed, and no result is claimed for all 81 reviewed
claims.

#### Follow-up verifier experiments

Two stricter follow-up experiments were run on the same development pilot. No
human labels or expected decisions were sent to either model.

The GPT-OSS-20B v2 schema added explicit checks for:

- direct answer contribution;
- clinical-relation preservation;
- named-entity identity;
- patient-context compatibility.

It completed 17/18 claims before one malformed summary decision. Python now
handles such contradictions by failing closed. The available results were:

- true positives: 10;
- true negatives: 4;
- false positives: 3;
- false negatives: 0;
- retain precision: 0.769231;
- retain recall: 1.000000.

This still fails the zero-false-positive pilot gate. The remaining errors were
an unsupported combination of two separate treatments, a category-to-cause
distortion, and generic advice drawn from a different clinical context.

GPT-OSS-120B was then tested with the same v2 payload and medium reasoning. It
stopped on a token-per-minute limit after 9 claims:

- true positives: 4;
- true negatives: 2;
- false positives: 0;
- false negatives: 3;
- retain recall: 0.571429.

Only three positive claims remained unprocessed, so even a perfect remainder
could reach at most 0.70 recall. Retrying could not satisfy the predeclared
0.80 recall gate and was therefore intentionally skipped.

A fully local E5 logistic calibrator was also evaluated on all 81 reviewed
claims with five-fold stratified grouping by `query_id`:

- OOF AUROC: 0.642857;
- OOF average precision: 0.880355;
- threshold 0.5: 56 TP, 4 TN, 10 FP, 11 FN;
- zero-FP threshold: 3 TP, 14 TN, 0 FP, 64 FN;
- zero-FP recall: 0.044776.

This model is stored as disabled and development-only. The final verifier
decision is:

1. Keep the deterministic Step 14 verifier.
2. Keep the evidence-origin correction in Steps 9, 11, and 14.
3. Keep all semantic and local learned overrides disabled.
4. Prefer an explicit abstention to an unsupported medical claim.
5. Do not claim that the 67 reviewed false rejections are solved.
6. Train a future verifier only after collecting a larger, query-diverse set
   of accepted claims, ordinary unsupported claims, relation distortions,
   named-entity conflicts, and a fresh untouched test set.

### 6.6 Aziza retained results

The selected seed-20260728 run reports:

- all-100 BERTScore F1: 0.655481;
- 100/100 answerable;
- reliability: 62 high, 36 medium, 2 low.

But:

- 90/100 are forced extractive fallbacks;
- only 10/100 are ordinary generated answers;
- claim support and hallucination are partly tautological because the copied
  evidence becomes an identical pre-labeled supported claim;
- a retained herbal-medicine question receives an unrelated
  prothrombin-test answer and is still labeled answerable and supported.

Therefore, report the BERTScore only as an Aziza experimental result. Do not
use `100% answerable`, `100% support`, `0% hallucination`, or the reliability
distribution as trustworthy final safety metrics.

### 6.6 Category-aware fallback result

On the second Aziza unseen cohort:

- baseline BERTScore: 0.652023;
- category bonus 0.08: 0.652421;
- difference: +0.000398.

The gain is small but did not reduce answerability in that ablation. This is a
reasonable feature to retest in the root conditional FTS channel on a fresh
cohort.

## 7. Results That Must Not Be Mixed

Do not combine the following into one headline table without explicit scope:

- root human-labeled candidate retrieval versus Aziza silver entity-target
  retrieval;
- root substantive-answer metrics versus Aziza forced-extractive metrics;
- known-answer trials versus exact-QA-excluded generalization trials;
- old `trial_graph_v1` runs versus `final_v1` runs;
- post-mitigation metrics over claim-bearing answers versus all-query
  end-to-end metrics;
- development cohorts used for tuning versus a final untouched test cohort.

The three Aziza "unseen" cohorts were subsequently used to tune fallback and
category settings. They are development/robustness cohorts, not a final
untouched test set.

## 8. Entity-Evaluation Scope Correction

The files named `ground_truth_entities_100.csv` and
`llm_entities_vs_gt_100.csv` contain 300 aligned rows and 273 unique questions.

The Aziza evaluator's default `--limit 100` evaluates the first 100 entity
rows, not 100 unique questions:

- first 100 aligned rows: canonical token F1 0.4950, type macro F1 0.7174;
- all 300 rows with the same evaluator: canonical token F1 0.310667,
  type macro F1 0.549016.

The first pair is not wrong, but it must be labeled "first 100 aligned entity
rows", not "100-question entity evaluation".

## 9. Final Architecture

The recommended production and research flow is:

1. Normalize the Arabic query in Python.
2. Run one GPT-OSS-20B structured query-analysis call.
3. Link explicit phrases deterministically to `final_v1` Neo4j entities.
4. Create a deterministic retrieval plan.
5. Search E5 entity, evidence, and QA indexes.
6. Traverse validated `final_v1` relations.
7. Fuse and deduplicate vector, graph, and QA candidates.
8. Rerank using identity, concept coverage, intent, anatomy, source quality,
   and mismatch penalties.
9. If no direct candidate exists but partial evidence exists, run targeted,
   held-out-safe SQLite FTS.
10. Re-rank the expanded pool.
11. Build a small evidence context using absolute gates.
12. Generate with GPT-OSS-20B only from that context.
13. Extract atomic claims.
14. Verify evidence support and query relevance separately.
15. Remove unsupported claims; preserve an abstention when needed.
16. Assign an explicitly uncalibrated reliability state.
17. Return answer, citations, retained/removed claims, reliability, and
    limitations.

## 10. Final Experimental Plan

### Development analyses

Continue using existing human candidate labels for:

- retrieval error analysis;
- deterministic reranker tuning;
- targeted FTS gating;
- context-selection analysis.

Use the 81 likely verifier false rejections for human annotation of:

- support;
- query relevance;
- anatomy/negation/numeric consistency;
- acceptable paraphrase.

### Fresh final test set

Create a new untouched 100-200 query set after freezing all code. Exclude:

- all prior root evaluation queries;
- all three Aziza unseen cohorts;
- all fallback-tuning queries;
- all source QAs used to build any supplemental facts.

For each final query:

- human-label top-10 candidate relevance as 0/1/2;
- human-label final medical correctness and completeness;
- human-label each generated claim for support and query relevance;
- record exact-QA availability separately.

### Required ablations

Run the same frozen queries, Step 8 outputs, generator, and verifier for:

1. E5 vector only.
2. Validated graph only.
3. Vector + validated graph.
4. Vector + validated graph + conditional FTS.
5. Previous configuration + category bonus.
6. Optional previous configuration + independently validated
   `supplemental_v2`.

This isolates the contribution of every retrieval channel without changing
generation or verification between runs.

## 11. Authoritative Artifact Paths

Root results:

- `outputs/evaluation/FINAL_RESULTS.md`
- `outputs/evaluation/FINAL_RESULTS.json`
- `outputs/evaluation/entity_gt_trial_100/RESULTS.md`
- `outputs/evaluation/entity_gt_trial_100/RESULTS.json`
- `outputs/evaluation/entity_gt_trial_100/known_answer_diagnosis/README.md`
- `outputs/evaluation/entity_gt_trial_100/known_answer_diagnosis/diagnosis.json`
- `outputs/evaluation/claim_verifier/semantic_claim_adjudication_pilot_v1/`
- `outputs/evaluation/claim_verifier/semantic_claim_adjudication_pilot_v2/`
- `outputs/evaluation/claim_verifier/semantic_claim_adjudication_pilot_v2_120b/`
- `outputs/evaluation/claim_verifier/local_e5_calibrator_v1/`
- `outputs/evaluation/claim_verifier/FINAL_DECISION.md`
- `outputs/evaluation/claim_verifier/FINAL_DECISION.json`
- `outputs/evaluation/cache/semantic_claim_adjudication_pilot_v1/semantic_claim_adjudication.jsonl`
- `models/claim_verifier_e5_calibrator_v1.json`
- `data/evaluation/candidate_relevance_annotations_100_final.csv`
- `data/evaluation/candidate_relevance_combined_pool_v2.csv`
- `data/evaluation/candidate_relevance_combined_pool_v2_replay_ready.csv`
- `outputs/evaluation/retrieval_expansion/combined_pool_v2_analysis_final/`
- `models/candidate_reranker_two_stage_v2_post_step11.json`

Aziza comparison artifacts:

- `aziza-trial/README_EXPERIMENTS.md`
- `aziza-trial/scripts/step09c_hybrid_retrieval.py`
- `aziza-trial/scripts/step10_rerank_subgraphs.py`
- `aziza-trial/scripts/step11_build_evidence_contexts.py`
- `aziza-trial/scripts/step12_generate_answers.py`
- `aziza-trial/scripts/step14_verify_claims.py`
- `aziza-trial/scripts/step15_mitigate_hallucinations.py`
- `aziza-trial/reports/unseen100_random_error_analysis_report.md`
- `aziza-trial/outputs/05_trial_graph_v1/supplemental_facts/`
- `aziza-trial/outputs/05_trial_graph_v1/evaluation/unseen100_random_seed20260728_category_aware_fallback_t042_b008_live_groq_full_100_final_output.csv`
- `aziza-trial/outputs/05_trial_graph_v1/evaluation/unseen100_random_seed20260728_category_aware_fallback_t042_b008_live_groq_full_100_summary.json`

## 12. Final Conclusion

The two projects do not provide two independent final graphs. They share the
same base `final_v1` graph, then diverge in retrieval, context selection, and
verification.

The root pipeline has lower answer coverage but substantially stronger
evaluation validity and safer failure behavior. The Aziza pipeline demonstrates
that QA fallback can increase apparent coverage, and that category matching may
help slightly, but its current supplemental graph, forced extraction, and
lexical verifier make the headline safety and answerability metrics
unreliable.

The final system should therefore keep the root architecture, add only the
small category-aware feature as a controlled ablation, and redesign any future
supplemental graph as a separately validated retrieval channel. The next
highest-value verifier work is a second, independently specified pilot that
explicitly judges named-entity identity, clinical relation preservation, and
whether a claim contributes an answer. It must pass a predeclared
false-acceptance criterion before evaluation on the remaining reviewed claims.
After that, run one fresh untouched end-to-end evaluation.
