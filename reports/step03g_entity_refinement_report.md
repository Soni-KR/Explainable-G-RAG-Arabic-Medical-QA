# Step 03G Entity Inventory Refinement Report

## Purpose

This step protects the previously extracted large entity inventory while applying quality-control signals learned from the 500-row reviewed benchmark.
The original extraction file is not overwritten.

## Inputs

- Entity inventory: `C:/Users/aziza/Downloads/Explainable-G-RAG-Arabic-Medical-QA-main/outputs/03_entity_extraction/ahd_entities_llm_merged.csv`
- Entity mentions: `C:/Users/aziza/Downloads/Explainable-G-RAG-Arabic-Medical-QA-main/outputs/03_entity_extraction/ahd_entity_mentions_llm_merged.csv`
- Reviewed benchmark: `C:/Users/aziza/Downloads/Explainable-G-RAG-Arabic-Medical-QA-main/ground_truth_entities_500.csv`

## Outputs

- Refined inventory: `C:/Users/aziza/Downloads/Explainable-G-RAG-Arabic-Medical-QA-main/outputs/03_entity_extraction/refinement/ahd_entities_llm_merged_refined.csv`
- Graph-ready trusted inventory: `C:/Users/aziza/Downloads/Explainable-G-RAG-Arabic-Medical-QA-main/outputs/03_entity_extraction/refinement/ahd_entities_llm_merged_graph_ready.csv`
- Graph-ready trusted mentions: `C:/Users/aziza/Downloads/Explainable-G-RAG-Arabic-Medical-QA-main/outputs/03_entity_extraction/refinement/ahd_entity_mentions_llm_merged_graph_ready.csv`
- Review queue: `C:/Users/aziza/Downloads/Explainable-G-RAG-Arabic-Medical-QA-main/outputs/03_entity_extraction/refinement/ahd_entities_llm_merged_needs_review.csv`
- Changed rows: `C:/Users/aziza/Downloads/Explainable-G-RAG-Arabic-Medical-QA-main/outputs/03_entity_extraction/refinement/ahd_entities_llm_merged_changed_rows.csv`

## Summary

- Total entities processed: 2253
- Graph-ready rows without review flags: 2072
- Mention rows read: 5904
- Mention rows kept for graph-ready entities: 4308
- Mention rows held back with review-flagged entities: 1596
- Rows with refinement actions: 99
- Rows flagged for review: 181

## Refinement Actions

- kept: 2154
- canonical_style_aligned_to_500_gt: 61
- type_aligned_to_500_gt: 26
- flagged_for_context_specific_refinement: 26

## Quality Flags

- duplicate_canonical_name: 149
- canonical_name_not_in_aliases: 32
- generic_canonical_name: 26
- body_part_name_type_mismatch: 6
- very_short_name: 6
- too_long_for_canonical_name: 2

## Refined Entity-Type Distribution

- Treatment: 818
- DiseaseCondition: 767
- Symptom: 426
- DiagnosticTest: 242

## Interpretation

The graph-ready file can be used as a conservative candidate source for rebuilding the graph immediately. The review queue is not discarded; it contains entities whose canonical name or type needs human checking before being trusted as final graph nodes.