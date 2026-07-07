# AHD Step 4 Relation Validation Report

## Current Run

- Provider: `groq`
- Model: `qwen/qwen3-32b`
- Candidate request records before resume filtering: 137
- New request records selected: 15
- Live LLM calls made: 15
- Stopped on rate limit: `False`
- Validated chunks with decisions: 137
- Relation decisions: 462
- Kept relations: 185
- Neo4j bidirectional relation rows: 370
- Rejected relations: 277
- Errors/warnings: 0

## Kept Relation Distribution

- DIAGNOSED_BY: 31
- HAS_SYMPTOM: 64
- INVESTIGATED_BY: 8
- TREATED_BY: 82

## Output Files

- Raw responses: `outputs/04_relation_extraction/ahd_llm_relation_validation_raw_responses.jsonl`
- Validated JSONL: `outputs/04_relation_extraction/ahd_llm_relation_validation_validated.jsonl`
- Decisions CSV: `outputs/04_relation_extraction/ahd_relation_validation_decisions.csv`
- Kept relations CSV: `outputs/04_relation_extraction/ahd_relations_llm_validated.csv`
- Neo4j bidirectional relations CSV: `outputs/04_relation_extraction/ahd_relations_neo4j_bidirectional.csv`
- Errors CSV: `outputs/04_relation_extraction/ahd_relation_validation_errors.csv`