# AHD Step 2 Chunking Report

## What was produced

- Input: `outputs/01_preprocessing/ahd_subset_5000_preprocessed.csv`
- Chunks CSV: `outputs/02_chunking/ahd_chunks_5000.csv`
- Chunks JSONL: `outputs/02_chunking/ahd_chunks_5000.jsonl`

## Chunking strategy

1. Keep only `graph_train` rows for graph construction chunks.
2. Group rows by Arabic category, English category label, and weak semantic hint.
3. Use dictionary hints only as weak grouping context, not final graph entities.
4. Put rows with no weak hint into `uncategorized::no_weak_hint` within their category.
5. Limit each chunk to at most 8 QA pairs and about 6500 characters.
6. Preserve QA IDs and source row numbers for evidence traceability.
7. Store both original Arabic chunk text and normalized chunk text.

## Summary

- Input rows: 5000
- Graph-train rows chunked: 4000
- Output chunks: 1093
- Categories: 90
- Semantic groups: 32
- Average rows per chunk: 3.66
- Max rows per chunk: 8
- Max characters per chunk: 11306
- Oversized chunks: 5
- Oversized single-row chunks: 5

## Example chunks

### chunk_00001

- Category: أرجية حساسية / Allergic allergy
- Semantic group: `condition::التهاب`
- QA IDs: `["ahd5k_00970", "ahd5k_03626", "ahd5k_03872", "ahd5k_04414"]`
- Row count: 4
- Oversized: False
- Top weak medical hints: `[{"canonical": "التهاب", "count": 4}, {"canonical": "حساسية", "count": 1}, {"canonical": "ربو", "count": 1}, {"canonical": "المعدة", "count": 1}]`

### chunk_00002

- Category: أرجية حساسية / Allergic allergy
- Semantic group: `condition::حساسية`
- QA IDs: `["ahd5k_00020", "ahd5k_00133", "ahd5k_00257", "ahd5k_00392", "ahd5k_00498", "ahd5k_00510", "ahd5k_00555", "ahd5k_00934"]`
- Row count: 8
- Oversized: False
- Top weak medical hints: `[{"canonical": "حساسية", "count": 8}, {"canonical": "دواء", "count": 2}, {"canonical": "تحليل مخبري", "count": 2}, {"canonical": "الجلد", "count": 1}, {"canonical": "الحمل", "count": 1}, {"canonical": "ربو", "count": 1}]`

### chunk_00003

- Category: أرجية حساسية / Allergic allergy
- Semantic group: `condition::حساسية`
- QA IDs: `["ahd5k_01231", "ahd5k_01245", "ahd5k_01393", "ahd5k_01430", "ahd5k_01589", "ahd5k_01655", "ahd5k_01916", "ahd5k_02011"]`
- Row count: 8
- Oversized: False
- Top weak medical hints: `[{"canonical": "حساسية", "count": 8}, {"canonical": "دواء", "count": 3}, {"canonical": "تحليل مخبري", "count": 2}, {"canonical": "الجلد", "count": 1}]`

### chunk_00004

- Category: أرجية حساسية / Allergic allergy
- Semantic group: `condition::حساسية`
- QA IDs: `["ahd5k_02039", "ahd5k_02115", "ahd5k_02354", "ahd5k_02892", "ahd5k_03243", "ahd5k_03480", "ahd5k_03662", "ahd5k_03703"]`
- Row count: 8
- Oversized: False
- Top weak medical hints: `[{"canonical": "حساسية", "count": 8}, {"canonical": "دواء", "count": 3}, {"canonical": "تحليل مخبري", "count": 1}, {"canonical": "أشعة", "count": 1}, {"canonical": "ربو", "count": 1}]`

### chunk_00005

- Category: أرجية حساسية / Allergic allergy
- Semantic group: `condition::حساسية`
- QA IDs: `["ahd5k_04144", "ahd5k_04347", "ahd5k_04480", "ahd5k_04574", "ahd5k_04654", "ahd5k_04683", "ahd5k_04733", "ahd5k_04819"]`
- Row count: 8
- Oversized: False
- Top weak medical hints: `[{"canonical": "حساسية", "count": 8}, {"canonical": "تحليل مخبري", "count": 3}, {"canonical": "الكبد", "count": 2}, {"canonical": "ربو", "count": 1}, {"canonical": "المعدة", "count": 1}]`
