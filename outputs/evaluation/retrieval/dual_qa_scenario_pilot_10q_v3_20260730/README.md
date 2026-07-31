# Dual QA Scenario Pilot

This retrieval-only pilot reused cached Step 8 outputs, `final_v1`, the existing
held-out-safe AHD SQLite index, and multilingual E5. It did not call an LLM,
query Neo4j, use references or annotations for ranking, use the supplemental
graph, or run generation.

## Result

- Queries: 10 from the AHD-reference cohort.
- Frozen baseline non-empty contexts: 8/10.
- Dual + scenario non-empty contexts: 9/10.
- Frozen baseline strong-direct contexts: 2/10.
- Dual + scenario strong-direct contexts: 2/10.
- Known-label useful precision: 0.5625 baseline versus 0.5556.
- Exact source-question leakage: 0.
- Selected explicit scenario conflicts: 0.

The one recovered context was related to the medical topic but did not directly
answer the requested test question. This pilot therefore did not justify
generation or a production change.

See `metrics.json`, `manifest.json`, and the five mode-specific JSONL files for
the complete saved results.
