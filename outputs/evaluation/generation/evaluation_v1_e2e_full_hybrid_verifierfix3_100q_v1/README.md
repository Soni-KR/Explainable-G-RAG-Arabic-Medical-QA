# Final 100-Question Verifier Re-audit

This is the authoritative Steps 13-16 audit of the completed full-hybrid generation
run `evaluation_v1_e2e_full_hybrid_semanticfix_100q_v1`.

No query analysis, retrieval, reranking, context selection, or answer generation was
rerun. The re-audit used the exact saved Step 8-12 artifacts and made zero API calls.
The source run remains unchanged for before/after comparison.

## Changes Evaluated

- Source questions no longer count as factual evidence.
- Arabic interrogative `ما` no longer counts as negation.
- Evidence is checked as local polarity-aligned clauses.
- Explicit action/recommendation paraphrases are aligned conservatively.
- Structured limitation text is excluded from factual claims.
- BERTScore and citation metrics exclude fallback and insufficient-evidence answers.

## Results

| Measure | Result |
|---|---:|
| Questions | 100 |
| Successful Step 12 generations | 74 |
| Substantive post-mitigation answers | 18 |
| Fully answerable | 10 |
| Partially answerable | 8 |
| Insufficient evidence | 82 |
| Retained supported claims | 31 |
| Weakly supported claims removed | 14 |
| Unsupported claims removed | 64 |
| BERTScore F1, substantive answers only | 0.673289 |

The `1.0` automatic claim-support and citation-validity values in `metrics.json`
describe the retained output after deterministic filtering. They are not independent
human judgments. Human confirmation is still required for final claim-support,
hallucination, and reliability conclusions.

Files:

- `full_pipeline.jsonl`: per-question outputs, contexts, claims, verification, and
  timing data.
- `metrics.json`: aggregate metrics with unavailable cases excluded correctly.
- `manifest.json`: source run, hashes, graph/model/runtime configuration, and proof
  that the re-audit made no API calls.
