# Arabic Medical Graph-RAG

This repository contains **our contribution after the entity and relation hand-off**:
validation and consolidation of the colleague-provided extraction, construction of
the frozen `final_v1` graph, Neo4j import, embeddings, and the complete Arabic
Graph-RAG pipeline from query understanding through explainable answer verification.

It intentionally does not contain the colleague's preprocessing, chunking, or entity
extraction implementation. Those stages are upstream inputs, not work claimed here.

## Contribution Boundary

### Received from the colleague

- Extracted and merged medical entities.
- Entity mentions linked to source Q&A records.
- Candidate medical relations and an initial validated relation set.
- The 5,000-row Q&A source table needed to reconstruct evidence and `QARecord` nodes.

These immutable hand-off files are retained only under
`outputs/final_graph/provenance/`. They are inputs and audit evidence, not active
Steps 1-4 implementations.

### Work completed in this repository

1. Continued and audited relation validation against the supplied AHD evidence.
2. Cleaned entity IDs, aliases, types, references, and duplicate relation forms.
3. Produced direct and inverse medical relations and froze `final_v1`.
4. Adapted the graph to a fixed Neo4j schema and imported it safely.
5. Built multilingual E5 embeddings and three Neo4j vector indexes.
6. Implemented Step 8 query understanding and deterministic entity linking/planning.
7. Implemented Steps 9-11 hybrid retrieval, reranking, and evidence context.
8. Implemented Step 12 grounded generation with GPT-OSS-20B.
9. Implemented Steps 13-17 claim extraction, verification, mitigation, reliability,
   and explainable output.
10. Added independent retrieval/generation evaluation, manifests, latency tracking,
    claim audits, and resumable API caching.
11. Added support for entity extraction precision, recall, F1, and BERTScore against
    an independently annotated ground truth. No score is declared unless labels exist.

## Current Status

| Component | Status | Authoritative artifact |
|---|---|---|
| Colleague hand-off | Preserved as input provenance | `outputs/final_graph/provenance` |
| Validation and graph finalization | Complete and frozen | `outputs/final_graph` |
| Step 5: Neo4j graph | Complete | `neo4j_dump/step05_final_v1_neo4j.dump` |
| Step 6: embeddings/indexes | Complete in Neo4j | three `final_*_vector_index` indexes |
| Step 8: query understanding | Implemented | `src/step08*.py` |
| Steps 9-11 | Implemented | retrieval, reranking, evidence context |
| Step 12 | Implemented | evidence-grounded GPT-OSS-20B generation |
| Steps 13-17 | Implemented | verification, mitigation, scoring, explanation |
| Retrieval evaluation | Leakage-free 100-query full-hybrid diagnostic complete | `outputs/evaluation/retrieval/evaluation_v1_retrieval_fullhybrid_qacorpus_identityfix_100q_v1` |
| Generation evaluation | 100-query full-hybrid run complete | `outputs/evaluation/generation/evaluation_v1_e2e_full_hybrid_semanticfix_100q_v1` |
| Evidence-local verifier re-audit | Complete, zero API calls | `outputs/evaluation/generation/evaluation_v1_e2e_full_hybrid_evidencelocal_100q_v1` |
| Claim-first generation pilot | Complete, 3/3 generated | `outputs/evaluation/generation/evaluation_v1_claimfirst_pilot_3q_v1` |
| Verifier v5 semantic safety-gate audit | Failed reserved 50-claim safety gate; disabled | `outputs/evaluation/claim_verifier/verifier_v5_reserved50_frozen_gate_20260730` |
| Conditional cross-encoder rescue | 100-query pilot failed acceptance gate; disabled | `docs/CONDITIONAL_CROSS_ENCODER_RESCUE.md` |
| Coverage-improvement ablations | Semantic verifier and retrieval rescue rejected | `docs/FINAL_COVERAGE_IMPROVEMENT_ABLATIONS.md` |

## Final Architecture

The implementation follows [`docs/mix.png`](docs/mix.png), beginning at the
colleague hand-off:

```text
Colleague entity/mention/relation hand-off
  -> evidence-based relation validation and entity/reference cleanup
  -> direct + inverse final_v1 relations
  -> fixed Neo4j graph schema
  -> multilingual E5 embeddings and vector indexes

Arabic query
  -> conservative Python normalization
  -> one GPT-OSS-20B structured query-analysis call
  -> deterministic exact/alias Neo4j linking
  -> deterministic retrieval planning
  -> vector + graph + lexical/direct-QA hybrid retrieval
  -> identity/anatomy/intent-aware reranking
  -> compact evidence context
  -> one-call claim-first GPT-OSS-20B generation
  -> per-claim/per-evidence citation verification
  -> unsupported-claim mitigation
  -> reliability score and explainable output
```

Every medical answer uses retrieved evidence. The production pipeline does not use
the experimental supplemental graph and does not alter `final_v1`.

## Repository Layout

```text
data/
  raw/AHD.csv                 Local source used only for independent evaluation
  evaluation/                 Gold templates and provisional review cohorts
docs/mix.png                  Architecture reference
neo4j_dump/                   Persistent final_v1 Neo4j backup
outputs/
  final_graph/                Frozen graph, hand-off provenance, validation audit
  evaluation/                 Retained retrieval/generation/claim results
scripts/
  validate_and_finalize_colleague_graph.py
  evaluation runners and annotation utilities
src/
  Step 5, Step 6, and Steps 8-17 production components
tests/                        Deterministic quality/safety regression tests
```

Old colleague preprocessing/extraction scripts, trial graphs, failed API runs, and
superseded quality-fix runs are isolated under the Git-ignored
`archive/_obsolete_pending_deletion/`. Nothing there is read by production code.

## Environment

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Copy `.env.example` to `.env` and provide local secrets. Never commit `.env`.
Production defaults include:

- `FINAL_GRAPH_VERSION=final_v1`
- `FINAL_NEO4J_URI=bolt://localhost:7688`
- `FINAL_EMBEDDING_MODEL=intfloat/multilingual-e5-base`
- `QUERY_ANALYSIS_MODEL=openai/gpt-oss-20b`
- `ANSWER_GENERATION_MODEL=openai/gpt-oss-20b`

## Graph Validation and Finalization

`scripts/validate_and_finalize_colleague_graph.py` is the retained graph-building
entry point. It starts from the hand-off files in `outputs/final_graph/provenance`.
It does not recreate preprocessing, chunks, or entity extraction.

The script:

- Applies deterministic entity canonicalization and type corrections.
- Preserves aliases and mention-level Q&A evidence.
- Validates candidate relations using their medical evidence excerpts.
- Stores raw successful validation responses as a resumable/auditable cache.
- Preserves every keep/reject decision in `relation_decisions.csv`.
- Produces accepted direct relations.
- Creates explicit inverse relations for Neo4j traversal.
- Validates entity endpoints, QA references, and unique IDs.
- Refuses to overwrite the graph after the frozen manifest exists.

The historical relation-validation model was `qwen/qwen3-32b`. This model was used
only during graph validation; the current answer generator is GPT-OSS-20B.

### final_v1 results

| File | Meaning | Rows |
|---|---|---:|
| `entities.csv` | Canonical medical entities | 2,175 |
| `entity_mentions.csv` | Evidence-backed entity mentions | 5,767 |
| `relation_decisions.csv` | Complete accepted/rejected audit | 3,392 |
| `relations.csv` | Accepted direct relations | 1,404 |
| `relations_bidirectional.csv` | Direct and inverse relations | 2,808 |

`graph_manifest.json` freezes these files with SHA-256 checksums. Current checksum
verification passes for all five files.

### Retained provenance

- `ahd_entities_llm_merged.csv`: colleague entity hand-off.
- `ahd_entity_mentions_llm_merged.csv`: colleague mention/evidence hand-off.
- `ahd_relation_candidates_seed.csv`: candidate relations supplied for validation.
- `ahd_llm_relation_validation_validated.jsonl`: validated relation payloads.
- `relation_validation_raw.jsonl`: resumable raw validator cache.
- `qa_records_source_5000.csv`: Q&A source needed for Neo4j evidence records.

## Step 5: Neo4j Graph

The final graph uses its own persistent database:

- Container: `ahd-neo4j-final`
- Browser: `http://127.0.0.1:7475/browser/`
- Bolt: `bolt://localhost:7688`
- Volume: `neo4j_final_data`
- Graph version: `final_v1`

```powershell
docker compose up -d neo4j-final
python src/step05c_import_final_graph.py --dry-run
python src/step05c_import_final_graph.py --execute
```

The importer uses batched `UNWIND`, `MERGE`, matched relationship endpoints, and
explicit `--execute`. It never clears the database or uses APOC.

Neo4j contains:

| Record | Count |
|---|---:|
| `MedicalEntity` | 2,175 |
| `EvidenceMention` | 5,767 |
| `QARecord` | 2,549 |
| `MEDICAL_RELATION` | 2,808 |
| `MENTIONED_IN` | 5,767 |
| `EVIDENCE_FROM` | 5,767 |

The persistent backup is `neo4j_dump/step05_final_v1_neo4j.dump`.

## Step 6: Embeddings and Indexes

`src/step06_build_embedding_indexes.py` reads the final graph from Neo4j and embeds:

1. Entity canonical names, aliases, normalized names, and types.
2. Evidence mention text and its linked entity.
3. QA questions, answers, and categories.

The model is `intfloat/multilingual-e5-base`, dimension 768, cosine similarity.
Documents use the E5 `passage: ` prefix and incoming queries use `query: `. Mean
pooling respects attention masks and vectors are L2-normalized.

Every vector stores its model, dimension, document type, and graph version. The
builder validates dimensions, writes in batches, skips valid existing embeddings,
and resumes after interruption.

Neo4j vector indexes:

- `final_medical_entity_vector_index`
- `final_evidence_mention_vector_index`
- `final_qa_record_vector_index`

```powershell
python src/step06_build_embedding_indexes.py --dry-run --skip-model-load
python src/step06_build_embedding_indexes.py --execute --batch-size 32
```

Vectors live in Neo4j and in the final dump; duplicate JSONL vectors are not kept.

## Step 8: Query Understanding

The first implementation used separate LLM calls for correction, classification,
phrase extraction, and intent. It was replaced by the current lower-cost design:

1. Python Arabic normalization.
2. One strict GPT-OSS-20B JSON call for correction, reformulation, classification,
   complexity, intent, and explicit medical phrases.
3. Python validation and meaning-preservation guards.
4. Deterministic exact canonical/alias/article-normalized Neo4j linking.
5. Deterministic retrieval planning.

Important changes:

- The guard, not the model's `meaning_changed` field, is final authority.
- Exact and alias matches are separated from semantic candidates.
- Type conflicts and ambiguous matches are not silently linked.
- Generic nodes such as `دواء` remain linked but are low-specificity seeds.
- Intent maps only to relation types actually present in Neo4j.
- Simple queries use one-hop graph retrieval; complex queries may use two hops.

```powershell
python src/step08b_analyze_query.py --query "ما علاج الربو؟" --link
python src/step08d_plan_retrieval.py --query "ما علاج الربو؟"
```

## Steps 9-11: Retrieval, Reranking, Context

### Step 9 changes

Hybrid retrieval combines E5 vector search over entities/evidence/QA records with
Neo4j graph traversal and direct lexical/QA evidence.

The graph contains only 2,549 QA records, so a separate held-out-safe SQLite FTS5
index now exposes 807,698 deduplicated Q&A records from the full AHD corpus. All
500 normalized `eval_test` questions, including duplicate source occurrences, are
excluded before indexing. The external corpus never changes `final_v1`.

After qualitative testing, graph expansion was tightened because semantically close
entities were sometimes medically different. The current code:

- Requires compatible medical identity before using semantic graph seeds.
- Prioritizes exact/alias linked entities.
- Penalizes generic concepts, type conflicts, and unrelated identities.
- Checks anatomy and laterality.
- Deduplicates direct/inverse relations by source relation ID.
- Keeps QA/evidence retrieval available when graph relations are incomplete.

The supplemental graph was reviewed separately but did not activate useful facts in
the clean ablation, so it is excluded from production.

### Step 10 changes

The original reranker over-rewarded relation confidence and general similarity. It
now exposes and combines semantic support, query-denominated medical-concept
coverage, constraint coverage, entity identity, intent match, source quality, and
graph support. Anatomical mismatch, unrelated clinical conditions, generic matches,
and type conflicts receive explicit penalties. Step 8's extracted DiseaseCondition
and Symptom phrases are the primary relevance anchors, so conversational words and
background treatments are not mistaken for required medical concepts.

The semantic-context correction preserves each vector candidate's original E5
similarity in metadata. This prevents Step 10 from replacing a strong semantic
signal with a lower aggregate score before Step 11 can inspect it.

### Step 11 changes

The original context nearly always supplied twelve items. It now uses absolute
answer-relevance, concept-coverage, intent, source-quality, and mismatch gates before
applying a secondary coverage-aware score margin, deduplication, and a configurable
maximum. A lower-ranked item survives the margin only when it adds a missing query
concept or has a vetted semantic/direct-question anchor.
Only useful `R*` relation facts and `E*` evidence cards become the citation allowlist.
Graph evidence is no longer injected merely for channel diversity; it must pass the
same relevance and safety competition as direct QA and evidence passages.

Step 11 may also retain a high-confidence vector paraphrase when its E5 score is at
least `AHD_CONTEXT_SEMANTIC_MIN_SCORE` (default `0.84`). Intent and anatomical
mismatch gates remain mandatory. Replaying the updated Steps 10-11 over the frozen,
leakage-free 100-question candidates retains context for 70 questions, averages 2.55
items per query, and keeps graph facts in four contexts. The stricter run is not yet
a human-confirmed improvement: candidate labels are required before comparing its
precision with the previous 77-question diagnostic.

```powershell
python src/step17_build_explainable_output.py --query "ما علاج الربو؟" --context-only
```

## Steps 12-17: Grounded Answer and Verification

### Step 12 changes

- Final generation uses Groq `openai/gpt-oss-20b`, not Qwen.
- The model receives only the query and selected Step 11 evidence.
- Current prompt `grounded_evidence_adaptive_v4_2` uses a strict single-passage
  near-extractive mode only when one answer-origin item passes all direct-evidence
  gates. Other non-empty contexts use a constrained partial/mixed mode.
- Strict JSON returns at most two self-contained claims, exactly one allowlisted
  evidence citation per claim, and an optional evidence-coverage limitation.
- Python constructs the final answer from those claims and derives QA/relation
  provenance from the cited Step 11 items; the model cannot author source IDs.
- API failures are technical fallbacks, not medical answers.
- Evaluation caches every successful call and retries HTTP 429 with backoff.
- The frozen v3 evaluation remains the selected production result. A completed
  generation-only v4.2 evaluation reused the exact saved Step 11 contexts for both
  100-query cohorts but reduced substantive answers from 49 to 46 and surviving
  claims from 72 to 56. Its differential review also identified 13 unsafe new
  claims, so v4.2 is retained only as an unsuccessful ablation. See
  `docs/EVIDENCE_ADAPTIVE_GENERATION_V4.md` and
  `outputs/evaluation/generation/evidence_adaptive_v4_2_comparison_200q_20260729/FINAL_COMPARISON.md`.
- Candidate `grounded_claim_first_v3_1` now combines v3's full-context coverage
  with v4's strict claim schema and Python-derived provenance. Its 10-query
  development pilot had zero technical failures and retained 5 claims across 4
  substantive answers. The opt-in Verifier v5 hard-gate re-audit removed its one
  unsafe lexical reinterpretation, leaving 4 claims across 3 substantive answers.
  Both profiles remain disabled pending a fresh holdout. See
  `docs/GENERATION_V3_1.md` and `docs/CLAIM_VERIFIER_V5.md`.

### Steps 13-15 changes

- V4 structured claims are already atomic and are not split again, preventing
  contextless fragments; legacy v3 answers retain their original splitter.
- Limitation text is excluded even when the model incorrectly returns it as a
  structured factual claim.
- Verification checks citations, normalized support, numbers, negation, anatomy,
  intent, and whether recommendations occur in the same evidence segment.
- A source question cannot support a factual claim; only evidence text, source
  answers, and validated relation facts can do so.
- Negation is checked on local clauses, and interrogative Arabic `ما` is not treated
  as a universal negation marker.
- Conservative phrase/action equivalences accept near-exact evidence paraphrases.
- Verification evaluates a complete feature vector for each claim/evidence pair;
  support from one citation can no longer be combined with identity or intent from
  another citation.
- A claim must also cover the query's Step 8 medical anchors, or be supported by a
  citation that demonstrably covers them; a faithfully cited wrong-topic claim is
  rejected as `claim_query_concept_mismatch`.
- Step 15 reports `fully_answerable`, `partially_answerable`,
  `supported_but_incomplete`, or `insufficient_evidence` using supported-claim query
  coverage, not claim support alone.
- Split claims retain only citations that independently support that child claim.
- Unsupported claims are removed; technical failures remain distinguishable from
  insufficient evidence.

These changes reduced wrong graph evidence and unsafe unsupported claims. The main
remaining research trade-off is high safety versus limited answer coverage.

Verifier v5 and the conditional cross-encoder rescue are isolated development
ablations. V5 keeps non-overridable citation, evidence, medication, anatomy,
negation, number, and unrelated-condition gates, while allowing only soft
intent/concept failures to be semantically adjudicated when explicitly enabled.
Its deterministic post-semantic safety gate improved the development-tuned
81-claim result to TP=60, TN=14, FP=0, FN=7 and F1=0.944882. That gain did not
generalize to the reserved 50-claim audit: 8/13 unsafe claims were retained, so
the candidate is rejected and remains disabled. The retrieval rescue runs only
for empty or weak Step 11 contexts and cannot override hard clinical
compatibility gates. Neither feature changes the frozen production
configuration. See `docs/CLAIM_VERIFIER_V5.md`,
`docs/CONDITIONAL_CROSS_ENCODER_RESCUE.md`, and
`docs/FINAL_COVERAGE_IMPROVEMENT_ABLATIONS.md`.

### Steps 16-17

Reliability combines retrieval strength, evidence quality, supported claims,
citation validity, and warnings. It is explicitly uncalibrated until enough human
labels exist for AUROC/AUPRC and calibration analysis. Step 17 returns the answer,
retrieved graph/evidence, citations, claim audit, limitations, reliability metadata,
and per-stage latency. Step 10 and Step 16 use one shared source-prior policy,
including `ahd_heldout_safe_corpus = 0.95`; Step 17 exposes each claim's best
evidence, score, failed checks, valid citations, and reason.

```powershell
python src/step17_build_explainable_output.py --query "ما علاج الربو؟"
```

## Evaluation Work

### Annotation policy

Retrieval and claim annotations are created independently of Step 8, retrieval
outputs, and model predictions. Dataset-derived labels remain explicitly
`provisional_dataset_annotation` until human confirmation. Metrics requiring gold
return `unavailable` rather than treating provisional labels as official truth.
Candidate-relevance labels are a separate diagnostic dataset: reviewers can see the
system's candidates and scores, so these labels may train or diagnose the reranker
but must never be copied into independent retrieval gold.

Active files:

- `retrieval_gold_annotations_100.csv`: 100 provisional held-out questions.
- `human_claim_annotations_100.csv`: 179 provisional claim rows for human review.
- `candidate_relevance_annotations_100.csv`: frozen unlabeled candidate queue.
- `candidate_relevance_annotations_100_final.csv`: all 540 human judgments covering
  the top five evidence candidates and top three available relations for 99
  candidate-bearing queries. The remaining query (`evalv1_045`) is non-medical and
  correctly has retrieval disabled rather than receiving a fabricated candidate.
- `pilot_retrieval_annotations_15.csv`: exact retained qualitative cohort.
- `retrieval_generation_gold_template.csv`: blank annotation schema.
- `ANNOTATION_GUIDE.md`: human labeling/adjudication instructions.

```powershell
python scripts/prepare_candidate_relevance_annotations.py --refresh
python scripts/train_candidate_reranker.py `
  --annotations data/evaluation/candidate_relevance_annotations_100_final.csv `
  --confirmed-annotator-id user_human_review_20260723
```

The final file contains 335 irrelevant, 157 related-but-incomplete, and 48 directly
answering candidates. Only 37/99 queries contain any direct candidate, 44 contain
partial evidence only, and 18 contain only irrelevant candidates. All direct
candidates are QA/evidence passages; no graph relation received label 2.

The trainer uses query-grouped five-fold validation and two interpretable stages:
irrelevant versus usable, then partial versus direct. Its phrase-aware out-of-fold
ranking improves evidence nDCG@5 from `0.624496` to `0.683154` and direct-at-rank-1
from 15 to 19 queries. The model remains disabled because the Step 11 replay shows
only a modest precision gain rather than a clear coverage improvement.

| Step 11 replay | Useful precision | Direct precision | Direct queries retained |
|---|---:|---:|---:|
| Current deterministic | 0.527778 | 0.183333 | 25/37 |
| 25% learned blend | 0.537572 | 0.190751 | 25/37 |
| 50% learned blend | 0.552795 | 0.198758 | 25/37 |
| Learned score only | 0.560284 | 0.198582 | 25/37 |

These are out-of-fold diagnostics over the annotated candidate pool, not independent
test results. Production Steps 10-11 are unchanged. The next retrieval work should
target the 18 all-zero queries and, when completeness is required, the 44
partial-only queries.

### Targeted partial-only retrieval expansion

The first expansion phase deliberately targets only the 44 partial-only queries;
the 18 all-zero queries remain valid `insufficient_evidence` cases. Three
query-derived variants are searched against the held-out-safe 807,698-row SQLite
FTS index. Reference answers and human relevance labels are not used to construct
queries. Existing candidates are excluded by query/QA ID and results are
deduplicated across variants.

```powershell
python scripts/run_partial_only_fts_expansion.py `
  --per-variant-k 10 `
  --max-new-per-query 12 `
  --expand-graph-aliases
```

The run produced 483 new candidates covering all 44 queries, excluded 56 existing
hits, and found 103 candidates through multiple variants. Variant B loaded 34
aliases from 11 linked `final_v1` entities. Two unsafe Step 8 substitutions
(`حساسية → إحساس` and `دبقي → دموي`) were detected automatically; those queries
used the original text only. The candidate CSV remains pending human annotation
before any retrieval or generation claim is made.

`src/evaluation_metrics.py` implements entity precision/recall/F1/BERTScore,
relation candidate/triplet metrics, Recall@5, MRR, nDCG@10, answer BERTScore,
claim-support/hallucination/citation rates, latency, and reliability calibration.
Metrics are only reported when their required labels exist.

### 100-question retrieval ablation

`outputs/evaluation/retrieval/ablation_100q` contains five modes and 100 rows per
mode. Formal relevance metrics are unavailable pending human confirmation. Valid
mean end-to-end latency:

| Mode | Mean latency |
|---|---:|
| Lexical only | 6,186.96 ms |
| Vector only | 633.95 ms |
| Graph only | 569.31 ms |
| Hybrid without reranking | 645.58 ms |
| Full hybrid | 674.36 ms |

### 15-question generation pilot

`outputs/evaluation/generation/pilot_15q` is the last complete valid pilot. Nine of
15 questions produced non-fallback answers. Their mean BERTScore F1 was `0.695662`;
mean end-to-end latency over all 15 was `4,292.40 ms`. The small old verifier sample
reported claim support `1.0` over three scoreable queries and citation validity
`0.333333`; these are diagnostic, not final research claims.

The question-by-question Steps 8-12 explanation is
`outputs/evaluation/qualitative/pilot_15q_steps08_12.md`.

### Completed 100-question full-hybrid generation

`evaluation_v1_e2e_full_hybrid_semanticfix_100q_v1` reused the same frozen Step 8
and retrieval candidates for all questions. It completed all 100 rows with 74
successful GPT-OSS-20B generations and 26 evidence fallbacks. Successful API calls
remain in the append-only cache, so no completed call needs to be repeated.

The latest offline evidence-local verifier diagnostic is
`evaluation_v1_e2e_full_hybrid_evidencelocal_100q_v1`. It reused the exact saved
Step 8-12 artifacts and made zero API calls. It verifies every claim against one
complete evidence-row feature vector instead of mixing maxima across citations.
Results:

| Measure | Result |
|---|---:|
| Questions | 100 |
| Step 12 successful generations | 74 |
| Substantive post-mitigation answers | 24 |
| Fully answerable | 15 |
| Partially answerable | 9 |
| Insufficient evidence after mitigation | 76 |
| Retained citation-backed claims | 40 |
| BERTScore F1 over substantive answers only | 0.677404 |

Automatic claim support and citation validity are both `1.0` over the 24 substantive
answers because Step 15 deliberately removes every claim that fails the verifier.
They measure enforcement of the current guards, not independent medical accuracy.
Human claim annotations are still required for a defensible claim-support and
hallucination result.

The 15/9 answerability split above predates the new four-state completeness policy.
It must not be reused as the current `fully_answerable` result; the clean 100-query
generation will recompute those states after candidate annotation and reranker
selection are frozen.

This 100-question re-audit is a verifier diagnostic, not a clean held-out generation
score: its frozen historical retrieval contains six exact-question leakage cases.
The current leakage-free retrieval artifact is
`evaluation_v1_retrieval_fullhybrid_qacorpus_identityfix_100q_v1`.

The new claim-first prompt was tested separately on three leakage-free frozen
retrieval examples in `evaluation_v1_claimfirst_pilot_3q_v1`: all three generated,
seven claims survived, two unsupported claims were removed, and BERTScore F1 was
`0.685236`. This sample is too small for a research conclusion.

A local E5 reranking benchmark improved reference-overlap diagnostics on four of
eight difficult queries, but full fallback retrieval took 94.5 seconds for eight
queries and produced usable context for only three. It is now available only as a
conditional second pass when ordinary Step 11 context is empty and the query has an
identifiable medical concept. It never runs for already successful or non-medical
queries.

The runner supports an offline, non-overwriting re-audit when Steps 13-16 change:

```powershell
python scripts/run_generation_ablation.py `
  --gold-file data/evaluation/retrieval_gold_annotations_100.csv `
  --mode full_pipeline `
  --run-id NEW_NON_OVERWRITING_RUN_ID `
  --reaudit-generation-run outputs/evaluation/generation/evaluation_v1_e2e_full_hybrid_semanticfix_100q_v1
```

## Frozen Final Evaluation

The authoritative run is
`full_pipeline_retrieval_v2_targeted_fts_reranked_network_v1`. Its consolidated
results and exact artifact paths are in
`outputs/evaluation/FINAL_RESULTS.md`. The final offline BERTScore uses the
original AHD answer associated with each frozen query as a dataset reference:

| Scope | Queries | BERTScore F1 |
|---|---:|---:|
| All outcomes | 100 | 0.660743 |
| LLM-generated outcomes | 66 | 0.665957 |
| Substantive claim-bearing answers | 26 | 0.675803 |

RAGAS context recall, context precision, faithfulness, and answer relevancy are
implemented in `scripts/evaluate_frozen_run_offline.py`. They consume only the
saved frozen artifacts and are resumable, but the complete judge run remains
pending because the configured evaluator API quota was exhausted. Partial RAGAS
scores are not treated as final results.

The hallucination-mitigation seed is in
`data/training/hallucination_mitigation_seed_v1/`. It contains 114 silver
claim-support examples, 44 answer preferences, and 26 grounded-answer examples.
Because these examples come from evaluation-v1, they are for schema design and
error analysis only. Fine-tuning requires an equivalent human-confirmed dataset
from a disjoint AHD training cohort.

## Verification

```powershell
python -m compileall src scripts
python -m unittest discover -s tests -v
```

Current frozen graph checksum verification passes for all five graph files. The
regression suite covers identity gating, anatomy/laterality, generic seeds, dynamic
context, citation allowlists, claim splitting, recommendation support, negation,
numbers, technical fallback handling, and hallucination mitigation.

## Collaboration Rules

Commit production source, tests, documentation, frozen graph CSVs/manifests,
provenance required to reproduce validation/import, and compact evaluation results.
Do not commit `.env`, virtual environments, raw AHD data, caches, or temporary API
requests. Share the 115 MB Neo4j dump through Git LFS or external storage if needed.

Treat `outputs/final_graph/*.csv`, `graph_manifest.json`, the Neo4j dump, and
`FINAL_GRAPH_VERSION=final_v1` as immutable. A changed graph must become `final_v2`.
