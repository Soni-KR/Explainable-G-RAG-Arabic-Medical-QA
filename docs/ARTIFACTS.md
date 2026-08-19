# External Release Artifacts

The Git repository contains code, configuration, tests, documentation, and compact
evaluation annotations. Generated graphs, run outputs, and manuscript files are
distributed separately.

## Release Files

| Asset | Purpose | Restore location |
|---|---|---|
| `final_v2_graph_csv.zip` | Importable final-v2 graph tables and manifest | `outputs/final_graph_v2/` |
| `final_v2_neo4j_dump.zip` | Portable Neo4j database backup | Local restore workspace |
| `final_v2_neo4j_dump.zip.sha256` | Dump integrity checksum | Beside the dump ZIP |
| `final_v2_evaluation_outputs.zip` | Frozen retrieval, generation, claim-audit, and metric outputs | `outputs/evaluation/` |
| `MG_Retriever_final_v2.pdf` | Reviewed manuscript | Any local document directory |
| `MG_Retriever_final_v2_source.zip` | Compilable LaTeX manuscript source | Any local build directory |

All restored `outputs/` and `paper/` paths are ignored by Git.

## Restore Graph CSVs

```powershell
New-Item -ItemType Directory -Force outputs\final_graph_v2 | Out-Null
Expand-Archive final_v2_graph_csv.zip outputs\final_graph_v2
python src\step05e_import_final_v2.py --dry-run
```

Run the importer with `--execute` only against the intended empty final-v2 Neo4j
database.

## Restore Evaluation Outputs

```powershell
New-Item -ItemType Directory -Force outputs\evaluation | Out-Null
Expand-Archive final_v2_evaluation_outputs.zip outputs\evaluation
```

The compact annotation files under `data/evaluation/` remain in Git and are the
authoritative labeling inputs. Missing labels must never be converted to zero.
