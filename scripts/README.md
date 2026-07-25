# Script Entry Points

The colleague's Steps 1-3 implementation is intentionally not part of this active
repository. Our executable contribution begins with validation of the supplied
entity/relation hand-off.

## Graph Validation

- `validate_and_finalize_colleague_graph.py`: clean the supplied entity layer,
  resume evidence-based relation validation, preserve all decisions, create inverse
  edges, validate references, and freeze `final_v1`.

The script reads only `outputs/final_graph/provenance` and refuses to overwrite an
existing frozen graph manifest.

## Evaluation

- `prepare_evaluation_annotations.py`: independent retrieval/claim templates.
- `preannotate_evaluation_from_dataset.py`: clearly marked provisional AHD labels.
- `validate_evaluation_annotations.py`: schema and annotation-state validation.
- `prepare_human_claim_annotations.py`: human claim-review queue generation.
- `prepare_candidate_relevance_annotations.py`: top-candidate review queue with
  2/1/0 relevance labels and clinical mismatch reasons; preserves existing human
  labels when the queue is refreshed.
- `train_candidate_reranker.py`: validate confirmed candidate labels and train an
  interpretable query-grouped two-stage logistic-regression reranker.
- `evaluate_reranker_context_selection.py`: replay the unchanged Step 11 selector
  using out-of-fold learned scores and compare selected contexts with human labels.
- `run_partial_only_fts_expansion.py`: search three safe query variants for only
  the 44 partial-only queries, exclude old QA IDs, deduplicate new hits, and create
  a human-review queue without using reference answers.
- `run_retrieval_ablation.py`: five frozen retrieval modes.
- `run_generation_ablation.py`: generation ablations and resumable frozen retrieval.
- `evaluation_common.py`: manifests, serialization, hashes, and shared records.
- `build_qualitative_pipeline_report.py`: readable Steps 8-12 inspection report.

The reusable Neo4j, embeddings, and Steps 8-17 pipeline lives in `src/`.
