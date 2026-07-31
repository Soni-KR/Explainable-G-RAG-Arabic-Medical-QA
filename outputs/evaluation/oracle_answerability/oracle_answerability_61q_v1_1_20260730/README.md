# Oracle Answerability Audit v1.1

## Purpose

This offline audit diagnoses why 61 frozen evaluation queries ended Step 11
with empty context. It does not change retrieval, the graph, generation, or
verification.

The audited queries come from two frozen 100-query cohorts:

- 31 empty-context queries from `ahd_reference`
- 30 empty-context queries from `entity_gt`

The original evaluation QA is excluded. The AHD reference answer is used only
as an offline search oracle and is never exposed to the production pipeline.

## Method

For each query, the audit:

1. Searches answer text in the held-out-safe SQLite FTS corpus of 807,698 QA
   records using the reference answer.
2. Excludes records whose normalized source question matches the evaluated
   question.
3. Keeps 50 lexical candidates.
4. Reranks them locally with `intfloat/multilingual-e5-base`.
5. Saves the nearest 20 candidates.
6. Checks answer similarity, source-question similarity, medical concept
   coverage, and deterministic clinical-scenario compatibility.
7. Checks whether an equivalent passage was already present in the frozen
   production retrieval pool.

No API, Neo4j query, graph expansion, supplemental graph, or generation call
was used.

## Results

| Diagnosis | Queries | Share |
| --- | ---: | ---: |
| Equivalent evidence exists, retriever miss | 4 | 6.6% |
| Relevant evidence retrieved, removed before Step 11 | 2 | 3.3% |
| Only broad or scenario-mismatched evidence found | 55 | 90.2% |
| Total | 61 | 100% |

By cohort:

| Cohort | Retriever miss | Step 10-11 removal | Broad/mismatched |
| --- | ---: | ---: | ---: |
| AHD reference | 1 | 1 | 29 |
| Entity ground truth | 3 | 1 | 26 |

The automatic strong-equivalence cases are:

- `evalv1_037`: candidate retriever miss
- `evalv1_043`: candidate Step 10-11 removal
- `entitygtv1_014`: candidate Step 10-11 removal
- `entitygtv1_023`: candidate retriever miss
- `entitygtv1_033`: candidate retriever miss
- `entitygtv1_095`: candidate retriever miss

These six cases are not human-confirmed labels. For example, a passage can
share the answer meaning while omitting a clinically important scenario
constraint. They remain in the priority review queue.

There are 27 priority-review queries:

- 6 queries with at least one automatic strong-equivalence candidate
- 21 broad/mismatched queries with borderline candidates

The other 34 queries had no strong or borderline candidate in the saved
top-20 oracle results.

## Latency

The run used local CPU inference:

- Mean: 12.850 seconds per query
- Median: 11.484 seconds per query
- p95: 21.412 seconds per query
- Total: 783.866 seconds, about 13.1 minutes

## Interpretation

Retriever misses do not currently dominate the empty-context failures, so this
audit does not justify training an AHD bi-encoder yet. It also does not justify
expanding `final_v1`: only four queries are automatic retriever-miss candidates
and none establishes a missing graph relation as the bottleneck.

The next decision should come from reviewing
`priority_manual_review.csv`. If manual confirmation substantially increases
the retriever-miss count, an AHD-trained bi-encoder can be evaluated on
retrieval metrics before generation. If most borderline candidates are
rejected, abstention remains the correct behavior for those queries.

The two Step 10-11 candidates should be traced separately. One visible cause is
query-intent mismatch: the MCV query was classified as `prevention_request`,
which gave otherwise relevant blood-test evidence zero intent support.

## Scope Limitation

This is a lower-bound oracle. The project does not currently have a full
807,698-answer vector index. The audit searches the full answer FTS index and
then applies E5 only to the lexical shortlist. Therefore, failure to find
equivalent evidence does not prove that no semantic equivalent exists anywhere
in AHD.

## Artifacts

- `oracle_results.jsonl`: complete per-query candidates and diagnoses
- `summary.csv`: one row per audited query
- `priority_manual_review.csv`: 27-query focused confirmation queue
- `borderline_manual_review.csv`: full conservative review archive
- `metrics.json`: aggregate counts and latency
- `manifest.json`: source hashes, model, thresholds, graph version, and runtime

## Decision

- Keep `final_v1` frozen.
- Do not use the supplemental graph.
- Do not expand the graph now.
- Do not train the AHD bi-encoder yet.
- Review the 27-query priority queue first.
- Investigate the two Step 10-11 cases independently.
