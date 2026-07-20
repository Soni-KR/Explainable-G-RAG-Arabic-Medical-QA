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
- `generation/evaluation_v1_e2e_full_hybrid_semanticfix_100q_v1`: completed live
  100-question full-hybrid run; 74 Step 12 generations and 26 evidence fallbacks.
- `claim_audit/evaluation_v1_e2e_full_hybrid_semanticfix_100q_v1`: matching original
  verifier output.
- `generation/evaluation_v1_e2e_full_hybrid_verifierfix3_100q_v1`: authoritative
  zero-API Steps 13-16 re-audit of the same saved answers and contexts.
- `claim_audit/evaluation_v1_e2e_full_hybrid_verifierfix3_100q_v1`: matching final
  claim audit.

## End-to-End Retrieval Ablation

- `evaluation_v1_e2e_lexical_only_100q_v2` completed under the pre-semantic-fix
  context selector: 9 generated answers and 91 insufficient-evidence fallbacks.
- The corrected full-hybrid run completed all 100 questions. Step 12 generated for
  74; the final verifier retained 31 claims across 18 substantive answers.
- BERTScore F1 is `0.673289` over the 18 substantive answers only. Automatic claim
  support and citation validity are `1.0` after mitigation and must not be reported
  as human medical-accuracy scores.
- Vector-only, graph-only, and hybrid-without-reranking generation remain incomplete.
  New comparable runs must use the same frozen inputs and current pipeline version.

The reviewed supplemental sidecar is not a remedy for this coverage issue: only
four relations passed its acceptance gates, it activated for 0/35 clean evaluation
queries, and its measured context delta was zero. It remains excluded from
`final_v1` pending a larger independently reviewed export.

Each completed run keeps raw JSONL, `metrics.json`, and `manifest.json`. Manifests
record graph/model/index configuration, thresholds, top-k values, source hashes,
runtime versions, and Git state without credentials.
