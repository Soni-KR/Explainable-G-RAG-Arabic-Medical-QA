# AHD Step 4 Relation Candidate Report

## Purpose

Step 4 tests whether the Step 3 entity layer can feed relation extraction.
This is a candidate layer only: relation pairs still need LLM or manual validation before Neo4j import.

## Current Test

- Validated entity chunks read: 199
- Candidate relation rows: 501
- Chunks with candidates: 137
- Q&A records with candidates: 188
- LLM relation request records: 137
- Included low-quality/non-actionable entities: `False`

## Candidate Relation Distribution

- DIAGNOSED_BY: 91
- HAS_SYMPTOM: 144
- INVESTIGATED_BY: 28
- TREATED_BY: 238

## Output Files

- Relation candidates: `outputs/04_relation_extraction/ahd_relation_candidates_seed.csv`
- LLM relation requests: `outputs/04_relation_extraction/ahd_llm_relation_extraction_requests.jsonl`

## Sample Candidates

- `HAS_SYMPTOM`: حساسية -> سعال (`chunk_00001`, `ahd5k_00970`)
- `HAS_SYMPTOM`: حساسية -> بلغم (`chunk_00001`, `ahd5k_00970`)
- `HAS_SYMPTOM`: التهاب -> سعال (`chunk_00001`, `ahd5k_00970`)
- `HAS_SYMPTOM`: التهاب -> بلغم (`chunk_00001`, `ahd5k_00970`)
- `HAS_SYMPTOM`: ربو -> سعال (`chunk_00001`, `ahd5k_00970`)

## Next Command

```powershell
python scripts\step04_prepare_relation_candidates.py --limit-chunks 200
```
