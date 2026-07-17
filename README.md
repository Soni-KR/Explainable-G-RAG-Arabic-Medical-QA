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
| Retrieval evaluation | 100-query ablation complete | `outputs/evaluation/retrieval/ablation_100q` |
| Generation evaluation | 15-query valid pilot complete | `outputs/evaluation/generation/pilot_15q` |
| 100-query generation | Incomplete and resumable | `outputs/evaluation/cache/evaluation_v1_generation_verifierfix_100q_resumed_20260717` |

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
  -> evidence-only GPT-OSS-20B answer generation
  -> atomic claims and citation verification
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
now exposes and combines semantic support, entity identity, intent match, evidence
quality, and validated confidence while penalizing anatomical mismatch, generic
entities, and type conflicts.

The semantic-context correction preserves each vector candidate's original E5
similarity in metadata. This prevents Step 10 from replacing a strong semantic
signal with a lower aggregate score before Step 11 can inspect it.

### Step 11 changes

The original context nearly always supplied twelve items. It now uses minimum score,
relative score margin, source balance, deduplication, and a configurable maximum.
Only useful `R*` relation facts and `E*` evidence cards become the citation allowlist.

Step 11 may also retain a high-confidence vector paraphrase when its E5 score is at
least `AHD_CONTEXT_SEMANTIC_MIN_SCORE` (default `0.84`). Intent and anatomical
mismatch gates remain mandatory. In the frozen 100-question offline diagnostic,
context coverage increased from 31 to 74 questions while mean reference-context
cosine remained stable (`0.8494` before, `0.8463` after). These are diagnostic
dataset-derived comparisons, not human-confirmed retrieval metrics.

```powershell
python src/step17_build_explainable_output.py --query "ما علاج الربو؟" --context-only
```

## Steps 12-17: Grounded Answer and Verification

### Step 12 changes

- Final generation uses Groq `openai/gpt-oss-20b`, not Qwen.
- The model receives only the query and selected Step 11 evidence.
- Strict JSON returns an Arabic answer, atomic claims, citations, QA IDs, relation
  IDs, and limitations.
- Python removes invented IDs outside the evidence allowlist.
- API failures are technical fallbacks, not medical answers.
- Evaluation caches every successful call and retries HTTP 429 with backoff.

### Steps 13-15 changes

- Claims are split atomically while preserving abbreviations such as `H. pylori`.
- Verification checks citations, normalized support, numbers, negation, anatomy,
  intent, and whether recommendations occur in the same evidence segment.
- Conservative phrase equivalences accept near-exact evidence paraphrases.
- Unsupported claims are removed; technical failures remain distinguishable from
  insufficient evidence.

These changes reduced wrong graph evidence and unsafe unsupported claims. The main
remaining research trade-off is high safety versus limited answer coverage.

### Steps 16-17

Reliability combines retrieval strength, evidence quality, supported claims,
citation validity, and warnings. It is explicitly uncalibrated until enough human
labels exist for AUROC/AUPRC and calibration analysis. Step 17 returns the answer,
retrieved graph/evidence, citations, claim audit, limitations, reliability metadata,
and per-stage latency.

```powershell
python src/step17_build_explainable_output.py --query "ما علاج الربو؟"
```

## Evaluation Work

### Annotation policy

Retrieval and claim annotations are created independently of Step 8, retrieval
outputs, and model predictions. Dataset-derived labels remain explicitly
`provisional_dataset_annotation` until human confirmation. Metrics requiring gold
return `unavailable` rather than treating provisional labels as official truth.

Active files:

- `retrieval_gold_annotations_100.csv`: 100 provisional held-out questions.
- `human_claim_annotations_100.csv`: 179 provisional claim rows for human review.
- `pilot_retrieval_annotations_15.csv`: exact retained qualitative cohort.
- `retrieval_generation_gold_template.csv`: blank annotation schema.
- `ANNOTATION_GUIDE.md`: human labeling/adjudication instructions.

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

### Resumable 100-question generation

The first attempt was invalid because every output was a rate-limit/evidence
fallback, so it is not an active result. The replacement cache currently contains
12 completed records, five successful Step 12 responses, and 12 audits.

```powershell
python scripts/run_generation_ablation.py `
  --gold-file data/evaluation/retrieval_gold_annotations_100.csv `
  --mode full_pipeline `
  --run-id evaluation_v1_generation_verifierfix_100q_resumed_20260717 `
  --reuse-retrieval-run outputs/evaluation/retrieval/ablation_100q `
  --resume `
  --request-interval-seconds 8 `
  --max-rate-limit-retries 6 `
  --rate-limit-backoff-seconds 30
```

This resumes Step 12 only from frozen retrieval, caches successful calls, and does
not change retrieval thresholds.

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
