# Script Index

The scripts remain in one directory because several frozen evaluation manifests
record their exact paths. They are grouped here by purpose.

## Graph Construction

- `validate_and_finalize_colleague_graph.py`: validate and freeze the original
  hand-off as `final_v1`.
- `step03_expand_graph_entities.py` and `step03c_batch_expand_entities.py`: resumable
  entity expansion.
- `step04a_prepare_expansion_relations.py` and
  `step04b_validate_expansion_relations.py`: relation candidate preparation and
  evidence-based validation.
- `step05_build_final_graph_v2.py`: additive `final_v1` + expansion merge with
  referential-integrity validation.
- `step09a_build_qa_corpus.py`: build the held-out-safe full-text QA index.

Re-running Steps 3-5 from raw chunks requires the collaborator's upstream
preprocessed/chunked hand-off and the locally licensed AHD source; those large
inputs are intentionally not published. The frozen CSV graph can still be imported
and fully validated without them.

## Final Evaluation

- `run_retrieval_ablation.py`: vector, graph, lexical, and hybrid retrieval modes.
- `build_conditional_fts_ablation.py`: conditional full-text expansion over frozen
  retrieval.
- `run_generation_ablation.py`: resumable Steps 12-17 evaluation.
- `prepare_candidate_relevance_annotations.py`: create blinded candidate queues.
- `evaluate_final_v2_relevance.py`: authoritative offline final-v2 metrics/report.
- `evaluation_common.py`: shared manifest, JSONL, latency, and cohort utilities.

## Annotation and Diagnostic Utilities

The remaining scripts reproduce documented development diagnostics: entity-GT
trials, claim-verifier audits, targeted FTS analyses, reranker studies, oracle
answerability checks, and rejected coverage-improvement ablations. They do not
change the production configuration unless an explicit opt-in flag is supplied.

Every runner writes to a new run ID and refuses to overwrite frozen artifacts.
Secrets are read from `.env` and must never be passed as CLI arguments or committed.
