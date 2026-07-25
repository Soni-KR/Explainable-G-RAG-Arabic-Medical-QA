# Evaluation-v1 Annotation Guide

## Independence rule

Annotators must not inspect Step 8 outputs, Step 9 rankings, ablation results,
model confidence, claim-verifier labels, or reliability scores while assigning
gold labels. They may inspect the frozen `final_v1` nodes, relations, and source
evidence directly in Neo4j and compare them with the held-out question and its
reference answer.

Use two independent annotators where possible. An adjudicator resolves conflicts
after both passes. Never copy IDs from a retrieval result into the gold file.

## Retrieval annotations

File: `retrieval_gold_annotations.csv`

- `gold_entity_ids`: `MedicalEntity.entity_id` values explicitly needed to answer the query.
- `gold_evidence_ids`: `EvidenceMention.mention_id` values that directly support an answer claim.
- `gold_qa_ids`: `QARecord.qa_id` values whose answer text is materially relevant.
- `gold_relation_ids`: stable `MEDICAL_RELATION.source_relation_id` values directly relevant to the query.
- `answerable_from_final_graph`: `true` only when final_v1 contains enough evidence for a useful grounded answer.
- ID lists use `|` separators or JSON arrays.

Mark `annotation_status` as:

- `pending_human_annotation`: not reviewed.
- `provisional_dataset_annotation`: automatically proposed from the original
  held-out AHD question/reference and frozen graph provenance. It is a review
  aid, not gold, and retrieval metrics must remain unavailable.
- `annotated`: completed by one annotator.
- `adjudicated`: disagreements resolved and ready for evaluation.

The provisional rows were produced without Step 8, Step 9, supplemental graph
data, or model retrieval predictions. Human reviewers must inspect every proposed
ID directly, remove false positives, add missed relevant IDs, and then change the
status to `annotated` or `adjudicated`.

For an answerable query, annotate every relevant ID you can confirm, not only the
first result. For an unanswerable query, leave gold ID fields empty and explain the
missing evidence in `annotation_notes`.

## Claim-level annotations

File: `human_claim_annotations_<generation_run>.csv`

Create it after a generation run:

```powershell
.\.venv\Scripts\python.exe scripts/prepare_human_claim_annotations.py `
  --generation-run outputs/evaluation/generation/<run_id>
```

Labels:

- `human_support_label`: `supported`, `partially_supported`, `unsupported`, or `not_verifiable`.
- `human_citation_valid`: `yes`, `no`, or `not_applicable`.
- `human_medical_correctness`: `correct`, `incorrect`, or `uncertain`.
- `human_hallucination_label`: `yes`, `no`, or `uncertain`.
- `harm_severity`: `none`, `low`, `medium`, or `high`.
- `adjudication_status`: `annotated` or `adjudicated` when complete.

Rows with `mode=reference_answer` and
`adjudication_status=provisional_dataset_annotation` are claim candidates split
from the original dataset answer. Their `human_*` fields contain provisional
source-grounding suggestions only: the text span is supported by its source
answer, has no citation, and has not been medically verified. Reviewers must
check whether each span is atomic and medically correct, then overwrite every
provisional label. Generated-answer claim sheets remain separate and are created
from a generation run with `prepare_human_claim_annotations.py`.

A claim is supported only when the cited evidence entails the whole atomic claim,
including negation, numbers, duration, population, and treatment context. A claim
is hallucinated when it asserts medical content not supported by the supplied
evidence, even if that content could be generally true.

Run validation before evaluation:

```powershell
.\.venv\Scripts\python.exe scripts/validate_evaluation_annotations.py
```

## Candidate relevance diagnostics

File: `candidate_relevance_annotations_100.csv`

The completed human review is retained separately as
`candidate_relevance_annotations_100_final.csv`; the original queue remains frozen
for candidate-ID and feature-integrity validation.

This file is deliberately different from retrieval gold. It exposes the frozen
system's top candidates so reviewers can diagnose Step 9 retrieval, Step 10
reranking, and Step 11 selection. Because annotators can see model candidates and
scores, these labels must not be copied into the independent retrieval-gold file.

Assign one `relevance_label` to every reviewed candidate:

- `2`: directly and safely answers the query or supports a necessary answer claim.
- `1`: medically related and potentially useful, but incomplete for this query.
- `0`: irrelevant, clinically mismatched, misleading, or unsafe for this query.

For label `0`, set `error_reason` to one of:

- `wrong_disease`
- `wrong_symptom`
- `wrong_anatomy`
- `wrong_intent`
- `generic_test_treatment_match`
- `same_words_different_clinical_situation`
- `unsafe_or_contradictory`
- `other`

Use `secondary_error_reason` only when a second failure materially explains the
mistake. Set `annotation_status` to `annotated` after one human pass and
`adjudicated` after conflict resolution. The reference answer is visible as a
review aid, but lexical similarity alone is not relevance.

Generate or safely refresh the queue with:

```powershell
python scripts/prepare_candidate_relevance_annotations.py
python scripts/prepare_candidate_relevance_annotations.py --refresh
```

Refresh preserves human fields by `(query_id, candidate_type, candidate_id)`.

## Partial-only expansion candidates

File:
`outputs/evaluation/retrieval_expansion/partial_only_fts_candidates_v1.csv`

These 483 rows are new held-out-safe FTS candidates for the 44 queries that had
label-1 candidates but no label-2 candidate. Review them with the same `0/1/2`
definitions and error-reason policy above. Set:

- `annotator_id` to the reviewer identifier.
- `annotation_status` to `annotated` after review.
- `annotation_notes` only when the main/secondary reason needs clarification.

Do not compare a candidate with `reference_answer` while assigning retrieval
relevance. The candidate question and answer must be judged against the user query
itself. These labels diagnose expansion quality and must not be copied into
independent retrieval gold.
