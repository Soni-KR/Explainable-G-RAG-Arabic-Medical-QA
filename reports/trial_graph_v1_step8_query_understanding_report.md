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

- Queries processed: 8
- Queries with detected graph entities: 8

## Intent Distribution

- cause_or_condition_question: 2
- diagnostic_test_request: 2
- symptom_check: 5
- treatment_request: 3

## Detected Entity Type Distribution

- DiseaseCondition: 9
- Symptom: 8
- Test: 1

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
