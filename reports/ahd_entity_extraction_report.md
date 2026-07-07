# AHD Step 3 Entity Extraction Report

## Purpose

Step 3 converts graph-train chunks into validated, normalized, evidence-linked Arabic medical entities for graph construction.

This step is entity-only: no relations, no Neo4j import, no category/body-part/other nodes.

## Allowed Entity Types

- DiseaseCondition
- Symptom
- Treatment
- Test

## Current Run

- Provider: `groq`
- Model: `llama-3.3-70b-versatile`
- Mode used: `validate-existing`
- Live LLM call executed: `False`
- Resume mode: `False`
- Append raw mode: `False`
- Total available chunks: 1093
- Candidate chunks before resume filtering: 1093
- Existing successful raw responses: 199
- Existing errored raw responses: 1
- New LLM calls made in this run: 0
- Stopped on rate limit: `False`
- Chunks requested after resume filtering: 1093
- Chunks with qa_records: 1093
- Chunks missing qa_records: 0
- Total validated chunks after merging old + new responses: 199
- Failed chunks: 4
- Extracted unique entities: 543
- Entity mentions: 1122
- Alias count: 912
- Non-actionable / low-signal entities: 4
- Validation/model errors: 95
- Average entities per validated chunk: 5.02
- Chunks with zero entities: 4
- Low-confidence entities (< 0.5): 0
- Low-confidence mentions (< 0.5): 0
- Generic/noisy entities rejected: 21
- Standalone allergen/trigger entities rejected: 2
- Background medication entities rejected: 2
- Category-like entities rejected: 1
- Context-only entities rejected: 2
- BodyPart/category/other accidental outputs rejected: 60

## Entity Type Distribution

- DiseaseCondition: 184
- Symptom: 91
- Test: 50
- Treatment: 218

## Entity Quality

- high: 434
- low: 4
- medium: 105
- is_actionable_medical_entity=false: 4

## Model Usage

Chunks by model:
- `llama-3.1-8b-instant`: 180
- `llama-3.3-70b-versatile`: 19

Extracted entity records by model before merging:
- `llama-3.1-8b-instant`: 904
- `llama-3.3-70b-versatile`: 94

Model used per validated chunk:
- `chunk_00001`: `llama-3.3-70b-versatile`
- `chunk_00002`: `llama-3.3-70b-versatile`
- `chunk_00003`: `llama-3.3-70b-versatile`
- `chunk_00004`: `llama-3.3-70b-versatile`
- `chunk_00005`: `llama-3.3-70b-versatile`
- `chunk_00006`: `llama-3.3-70b-versatile`
- `chunk_00007`: `llama-3.3-70b-versatile`
- `chunk_00008`: `llama-3.3-70b-versatile`
- `chunk_00009`: `llama-3.3-70b-versatile`
- `chunk_00010`: `llama-3.3-70b-versatile`
- `chunk_00011`: `llama-3.3-70b-versatile`
- `chunk_00012`: `llama-3.3-70b-versatile`
- `chunk_00013`: `llama-3.3-70b-versatile`
- `chunk_00014`: `llama-3.3-70b-versatile`
- `chunk_00015`: `llama-3.3-70b-versatile`
- `chunk_00016`: `llama-3.3-70b-versatile`
- `chunk_00018`: `llama-3.3-70b-versatile`
- `chunk_00019`: `llama-3.3-70b-versatile`
- `chunk_00020`: `llama-3.3-70b-versatile`
- `chunk_00021`: `llama-3.1-8b-instant`
- `chunk_00022`: `llama-3.1-8b-instant`
- `chunk_00023`: `llama-3.1-8b-instant`
- `chunk_00024`: `llama-3.1-8b-instant`
- `chunk_00025`: `llama-3.1-8b-instant`
- `chunk_00026`: `llama-3.1-8b-instant`
- `chunk_00027`: `llama-3.1-8b-instant`
- `chunk_00028`: `llama-3.1-8b-instant`
- `chunk_00029`: `llama-3.1-8b-instant`
- `chunk_00030`: `llama-3.1-8b-instant`
- `chunk_00031`: `llama-3.1-8b-instant`
- `chunk_00032`: `llama-3.1-8b-instant`
- `chunk_00033`: `llama-3.1-8b-instant`
- `chunk_00034`: `llama-3.1-8b-instant`
- `chunk_00035`: `llama-3.1-8b-instant`
- `chunk_00036`: `llama-3.1-8b-instant`
- `chunk_00037`: `llama-3.1-8b-instant`
- `chunk_00038`: `llama-3.1-8b-instant`
- `chunk_00039`: `llama-3.1-8b-instant`
- `chunk_00040`: `llama-3.1-8b-instant`
- `chunk_00041`: `llama-3.1-8b-instant`
- `chunk_00042`: `llama-3.1-8b-instant`
- `chunk_00043`: `llama-3.1-8b-instant`
- `chunk_00044`: `llama-3.1-8b-instant`
- `chunk_00045`: `llama-3.1-8b-instant`
- `chunk_00046`: `llama-3.1-8b-instant`
- `chunk_00047`: `llama-3.1-8b-instant`
- `chunk_00048`: `llama-3.1-8b-instant`
- `chunk_00049`: `llama-3.1-8b-instant`
- `chunk_00050`: `llama-3.1-8b-instant`
- `chunk_00051`: `llama-3.1-8b-instant`
- ... 149 more chunks omitted

## Output Files

- LLM request batch: `outputs/03_entity_extraction/ahd_llm_entity_extraction_requests.jsonl`
- Raw LLM responses: `outputs/03_entity_extraction/ahd_llm_entity_extraction_raw_responses.jsonl`
- Validated LLM JSON: `outputs/03_entity_extraction/ahd_llm_entity_extraction_validated.jsonl`
- Final entities: `outputs/03_entity_extraction/ahd_entities_llm.csv`
- Final mentions/evidence: `outputs/03_entity_extraction/ahd_entity_mentions_llm.csv`
- Alias dictionary: `outputs/03_entity_extraction/ahd_entity_aliases_llm.csv`
- Errors: `outputs/03_entity_extraction/ahd_entity_extraction_errors.csv`

## Sample Extracted Entities

### ent_diseasecondition_e04a557cb82b

- canonical_name: Acanthosis nigricans
- entity_type: DiseaseCondition
- aliases: `["Acanthosis nigricans", "acanthosis nigricans"]`
- mention evidence: مرض الاديسون هو سبب اخر لتغيير لون الجلد الي اسود
- qa_id: ahd5k_04944
- chunk_id: chunk_00052

### ent_diseasecondition_5f5cc11b7f72

- canonical_name: Achondroplasia
- entity_type: DiseaseCondition
- aliases: `["Achondroplasia"]`
- mention evidence: Another possibility, Achondroplasia
- qa_id: ahd5k_04892
- chunk_id: chunk_00147

### ent_diseasecondition_8d0f4dc232cb

- canonical_name: Growth Hormone
- entity_type: DiseaseCondition
- aliases: `["GH", "Growth Hormone"]`
- mention evidence: نصحونا نذهب لاخصائي غدد صماء لانو احتمال يكون نقص في growth hormone
- qa_id: ahd5k_04373
- chunk_id: chunk_00171


## Safe Run Commands

Put your API key in `.env` first:

```text
GROQ_API_KEY=your_key_here
```

Prepare 5 Groq requests only:

```powershell
python scripts\step03_extract_entities.py --provider groq --model llama-3.3-70b-versatile --limit 5 --prepare-only
```

Run live on 5 Groq chunks:

```powershell
python scripts\step03_extract_entities.py --provider groq --model llama-3.3-70b-versatile --limit 5 --run-live --force-overwrite --sleep-seconds 8
```

Resume safely to 20 total chunks. If 5 chunks already succeeded, this calls only the missing 15:

```powershell
python scripts\step03_extract_entities.py --provider groq --model llama-3.3-70b-versatile --limit 20 --run-live --resume --sleep-seconds 30 --stop-on-rate-limit
```

Run the next explicit batch:

```powershell
python scripts\step03_extract_entities.py --provider groq --model llama-3.3-70b-versatile --batch-start 20 --batch-size 20 --run-live --resume --sleep-seconds 30 --stop-on-rate-limit
```

Use a smaller Groq model for bulk extraction after checking your Groq console model/rate-limit page:

```powershell
python scripts\step03_extract_entities.py --provider groq --model <smaller_model_id> --batch-start 15 --batch-size 20 --run-live --resume --sleep-seconds 10 --stop-on-rate-limit
```

Validate existing responses:

```powershell
python scripts\step03_extract_entities.py --validate-existing
```
