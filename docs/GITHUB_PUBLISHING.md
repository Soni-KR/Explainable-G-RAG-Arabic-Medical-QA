# GitHub Publishing Checklist

## Included

- Production and evaluation source under `src/`, `scripts/`, and `tests/`.
- Annotation protocols and public documentation.
- `.env.example`, Docker configuration, requirements, citation metadata, and docs.

## Excluded

- `.env` and API/database credentials.
- Virtual environments and Python caches.
- Raw AHD and the generated 1.7 GB SQLite index.
- Populated evaluation cohorts, reference answers, evidence passages, and labels.
- Generated outputs, graph CSVs, database dumps, and embedding indexes.
- Final-v2 retrieval/generation JSONL files and manuscript files.
- API caches, request queues, and run logs.
- Colleague trial workspaces, supervisor template papers, and temporary builds.
- Superseded evaluation runs and disabled learned-model files.

## Separate Release Assets

Upload these files separately instead of committing them to Git:

- `final_v2_graph_csv.zip`
- `final_v2_neo4j_dump.zip` and its SHA-256 file
- `final_v2_evaluation_outputs.zip` for authorized collaborators only
- `MG_Retriever_final_v2.pdf`
- `MG_Retriever_final_v2_source.zip`

See `docs/ARTIFACTS.md` for restore paths. Prepared local copies belong under the
ignored `_local_unpublished/github_release/` directory.

## Pre-push Commands

```powershell
git status --short
git add -A
git diff --cached --check
git diff --cached --stat
git commit -m "Publish frozen MG-Retriever final_v2"
git push
```

Before committing, confirm that `.env`, `data/raw/`, `data/retrieval/`, `outputs/`,
`paper/`, and `_local_unpublished/` do not appear in
`git diff --cached --name-only`.

No project license has been selected. Confirm ownership and licensing with all
authors and the institution before making the repository public.
