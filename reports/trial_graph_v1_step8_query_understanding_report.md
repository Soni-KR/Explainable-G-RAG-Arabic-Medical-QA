# Trial Graph v1 Step 8 Query Understanding Report

This implements the medical query-understanding layer before semantic retrieval or generation.

## Scope

- Arabic query normalization
- Lightweight synonym/variant expansion
- Intent classification
- Entity/alias detection against the frozen trial graph with `match_type`
- Separation between hard detected entities and semantic/expansion candidate entities
- Intent-weighted relation planning
- Retrieval plan construction for Step 9A/9C

## Counts

- Queries processed: 50
- Queries with detected graph entities: 50

## Intent Distribution

- aftercare_question: 4
- cause_or_condition_question: 12
- development_timeline_question: 2
- diagnostic_test_request: 8
- drug_safety_question: 4
- general_medical_question: 11
- normal_range_question: 1
- symptom_check: 19
- treatment_request: 16

## Detected Entity Type Distribution

- DiseaseCondition: 51
- Symptom: 35
- Test: 8
- Treatment: 18

## Output Files

- Query set: `outputs/05_trial_graph_v1/query_understanding/trial_graph_v1_query_set.csv`
- Query understanding JSON: `outputs/05_trial_graph_v1/query_understanding/trial_graph_v1_query_understanding.json`
- Query understanding CSV: `outputs/05_trial_graph_v1/query_understanding/trial_graph_v1_query_understanding.csv`

## Step 9 Planning Notes

- Treat `detected_entities` with `match_type=exact` or strong `alias` as hard query seeds.
- Treat `semantic_candidate_entities` as soft expansion candidates, not exact links.
- Use `relation_type_weights` to prioritize primary intent relations over secondary intent relations.
- Cause/condition questions include a warning because the current graph has no direct `CAUSES` relation.

## Next Step From Mix.png

Use these query-understanding records for Step 9A semantic retrieval over `outputs/05_trial_graph_v1/embeddings/trial_graph_v1_embeddings.jsonl`.
