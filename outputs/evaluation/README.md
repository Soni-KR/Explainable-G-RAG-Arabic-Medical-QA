# Retained Evaluation Results

Only results that still explain the current `final_v1` pipeline are active here.

## Retrieval

- `retrieval/pilot_15q`: five retrieval modes for the final qualitative pilot.
- `retrieval/ablation_100q`: complete 100-question lexical/vector/graph/hybrid
  comparison. Retrieval relevance metrics remain unavailable until provisional IDs
  are human-confirmed; latency metrics are valid.

## Generation and Claim Audit

- `generation/pilot_15q`: last completed valid 15-question GPT-OSS-20B run.
- `claim_audit/pilot_15q`: matching atomic claim verification output.
- `qualitative/pilot_15q_steps08_12.md`: readable question-by-question inspection.

## Resumable 100-Question Run

`cache/evaluation_v1_generation_verifierfix_100q_resumed_20260717` is append-only
checkpoint state. It currently contains 12 completed records, five successful Step
12 responses, and 12 audits. Do not rename it: the runner locates the cache by run
ID. On completion, the runner will create matching `generation/` and `claim_audit/`
directories without rerunning frozen retrieval.

Each completed run keeps raw JSONL, `metrics.json`, and `manifest.json`. Manifests
record graph/model/index configuration, thresholds, top-k values, source hashes,
runtime versions, and Git state without credentials.
