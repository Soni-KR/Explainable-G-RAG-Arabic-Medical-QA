# Data Layout

`data/evaluation/` contains the annotation protocol. Populated cohorts and labels
are local-only because they include AHD-derived questions, answers, or evidence.

The following local data are intentionally ignored by Git:

- `data/raw/AHD.csv`: original AHD source dataset (about 396 MB).
- `data/retrieval/ahd_qa_train_v1.sqlite`: generated held-out-safe FTS index
  (about 1.7 GB).
- Populated evaluation CSV/JSON/JSONL/notebook files under `data/evaluation/`.

Obtain AHD through its authorized distribution channel and verify that its license
permits your intended use. Do not commit raw medical data or generated indexes.

The index can be rebuilt with `scripts/step09a_build_qa_corpus.py` after placing the
source CSV at `data/raw/AHD.csv`.
