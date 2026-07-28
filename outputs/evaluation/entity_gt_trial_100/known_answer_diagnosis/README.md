# Known-Answer vs Generalization Diagnosis

## Experiment

Both trials use the same 100 entity-ground-truth questions and frozen
`final_v1` pipeline.

- Generalization trial: excludes each question's exact AHD QA record.
- Known-answer trial: allows that exact AHD QA record.

Retrieval weights, thresholds, prompts, generation settings, and verification
rules were unchanged. The known-answer run uses three narrow correctness fixes:
NFKC normalization, backward-compatible terms for the frozen FTS index, and
exact lexical QA anchoring.

## Exact QA Availability

- External SQLite corpus: 100/100 queries
- Frozen Neo4j `QARecord` nodes: 43/100 queries
- Configured graph version: `final_v1`

The two counts are not contradictory. SQLite holds the full external QA search
corpus, while Neo4j contains only QA records represented in `final_v1`.

## Steps 9-11 Boundary Trace

Before the fixes, the known-answer replay had non-empty context for
84/100 queries and retained the
exact question for only 68/100.
All 31 rejected exact passages were
missing the direct-anchor flag; 30 then
failed the ordinary intent-support gate.

| Measure | Generalization | Known-answer |
|---|---:|---:|
| Non-empty Step 11 context | 71/100 | 100/100 |
| Exact question in Step 9 candidates | 0/100 | 100/100 |
| Exact answer in Step 9 candidates | 4/100 | 100/100 |
| Exact question after Step 10 | 0/100 | 100/100 |
| Exact answer after Step 10 | 4/100 | 100/100 |
| Exact question retained by Step 11 | 0/100 | 100/100 |
| Exact answer retained by Step 11 | 3/100 | 93/100 |
| Exact QA retained but answer display truncated | 0/100 | 7/100 |
| Mean Step 11 context items | 2.200 | 2.830 |

Step 9 now retrieves the exact QA for all 100 known-answer questions, Step 10
keeps all 100, and Step 11 retains all 100. Seven long answers are still shown
as non-exact full strings because Step 11 truncates displayed source answers to
1,000 characters; their exact question/source remains present.

## Generation Comparison

| Measure | Generalization | Known-answer | Change |
|---|---:|---:|---:|
| Non-empty context | 69/100 | 100/100 | +31 |
| Generated | 66/100 | 98/100 | +32 |
| API/generation fallback | 34/100 | 2/100 | -32 |
| Substantive claim-bearing answers | 25/100 | 33/100 | +8 |
| Fully answerable | 5/100 | 7/100 | +2 |
| Partially answerable | 7/100 | 9/100 | +2 |
| Supported but incomplete | 13/100 | 17/100 | +4 |
| Insufficient evidence | 72/100 | 65/100 | -7 |
| BERTScore F1 | 0.676088 | 0.744325 | +0.068237 |

Allowing the exact QA fixes retrieval and technical generation coverage, but
substantive answer coverage rises only from
25 to
33. This isolates the remaining
bottleneck after Step 11: claim verification and mitigation.

## Claim Audit

- Pre-mitigation claims: 198
- Supported / weak / unsupported before mitigation:
  57 /
  4 /
  137
- Claims retained after mitigation: 57
- Claims removed: 141
  (71.2%)
- Removed claims with evidence support score >= 0.40:
  101
- `intent_mismatch` removals:
  107
- `claim_query_concept_mismatch` removals:
  35

Deterministic human-review buckets:

- `evidence_supported_but_query_relevance_gate_failed`: 81
- `low_or_missing_evidence`: 3
- `mixed_relevance_and_support_or_safety_failure`: 33
- `other_requires_human_review`: 15
- `support_or_safety_failure`: 5
- `weak_evidence_conservative_removal`: 4

The largest bucket,
`evidence_supported_but_query_relevance_gate_failed`, contains evidence-backed
claims removed by query-intent, concept, or anatomy gates. It is a suspected
false-rejection queue, not proof that every removal was wrong.

Post-mitigation claim support =
1.00,
hallucination rate =
0.00, and citation
validity = 1.00.
These values apply only to the
33 substantive, claim-bearing
answers. They are not results over all 100 questions.

## Reliability

- Low / medium / high:
  78 /
  18 /
  4
- Mean: 0.211863
- Median: 0.000000
- Range: 0.000000 to
  0.842500

## Latency

| Stage | Mean | Median | p95 | Total |
|---|---:|---:|---:|---:|
| End to end | 42075.4 ms | 44974.8 ms | 45295.7 ms | 4207.5 s |
| Step 12 generation | 808.6 ms | 782.2 ms | 1127.0 ms | 80.9 s |

The known-answer end-to-end figure includes the deliberate 45-second API pacing
between live requests. Step 12 latency is the better estimate of model-call
runtime for this run.

## Conclusion

The apparent contradiction is resolved:

1. Exact QA retrieval and Step 11 context selection now pass 100/100.
2. Technical generation succeeds for 98/100.
3. Only 33/100 answers remain substantive after verification.
4. Therefore, the main current bottleneck is no longer retrieval for this
   known-answer test. It is verifier/mitigator false rejection and strict
   completeness handling.

The next safe action is human adjudication of the removed-claim queue, beginning
with evidence-supported relevance-gate failures. Do not weaken all verification
thresholds from these automatic labels alone.

## Artifacts

- Final known-answer generation:
  `outputs/evaluation/generation/entity_gt_trial_100_known_answer_generation_v1/full_pipeline.jsonl`
- Final known-answer generation metrics:
  `outputs/evaluation/generation/entity_gt_trial_100_known_answer_generation_v1/metrics.json`
- Final known-answer claim audit:
  `outputs/evaluation/claim_audit/entity_gt_trial_100_known_answer_generation_v1/full_pipeline.jsonl`
- Known-answer Step 9 input:
  `outputs/evaluation/retrieval/entity_gt_trial_100_known_answer_retrieval_v2/full_hybrid.jsonl`
- Step 10-11 boundary replay: `known_answer_context_replay.jsonl`
- Generalization removed-claim queue: `removed_claim_review_queue.csv`
- Known-answer removed-claim queue:
  `known_answer_removed_claim_review_queue.csv`
- Machine-readable diagnosis: `diagnosis.json`
