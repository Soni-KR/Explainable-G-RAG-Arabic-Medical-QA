# Trial Graph v1 Outputs

This folder contains the frozen trial graph and the downstream retrieval/generation/trustworthiness artifacts for the Arabic medical Graph-RAG pipeline.

## Current Status

Completed stages:

- Step 5: Neo4j-ready graph construction.
- Step 5B: supplemental fact provenance mapped to AHD dataset evidence.
- Step 5C: low-evidence candidate discovery.
- Step 5D: focused supplemental expansion from reviewed AHD-backed facts.
- Step 6: embeddings and indexing files.
- Step 8: query understanding.
- Step 9A/9C: semantic and hybrid retrieval.
- Step 10: subgraph reranking.
- Step 11: evidence context construction.
- Step 12: Qwen answer generation.
- Step 13: claim extraction.
- Step 14: graph-based claim verification.
- Step 15: hallucination mitigation.
- Step 16: reliability scoring.
- Step 17: final explainable output.

## Important Folders

### `import/`

Neo4j-ready base graph files:

- `trial_graph_v1_entities.csv`
- `trial_graph_v1_mentions.csv`
- `trial_graph_v1_qa_sources.csv`
- `trial_graph_v1_direct_relations.csv`
- `trial_graph_v1_bidirectional_relations.csv`

### `supplemental_facts/`

Dataset-derived supplemental graph layer:

- `trial_graph_v1_supplemental_entities.csv`
- `trial_graph_v1_supplemental_relations.csv`
- `trial_graph_v1_supplemental_qa_sources.csv`
- `trial_graph_v1_supplemental_fact_provenance.csv`
- `trial_graph_v1_supplemental_candidate_topics.csv`
- `trial_graph_v1_supplemental_candidate_evidence.csv`
- `trial_graph_v1_supplemental_candidate_review.csv`
- `import_supplemental_medical_facts.cypher`

Current supplemental graph:

- 26 supplemental relations.
- 46 supplemental entities.
- 19 supplemental QA source records.

### `embeddings/`

Embedding/index artifacts:

- `trial_graph_v1_embedding_documents.csv`
- `trial_graph_v1_embeddings.jsonl`
- `trial_graph_v1_embeddings_metadata.json`

### `query_understanding/`

Step 8 outputs:

- query set
- normalized queries
- detected entities
- intent/relation priorities
- key medical fragments

### `semantic_retrieval/` and `hybrid_retrieval/`

Step 9 outputs:

- semantic retrieval results
- hybrid graph/evidence retrieval results
- retrieval metric reports

### `subgraph_reranking/`

Step 10 outputs:

- `trial_graph_v1_reranked_relations.csv`
- `trial_graph_v1_reranked_evidence.csv`
- `trial_graph_v1_reranked_subgraphs.json`

### `context_construction/`

Step 11 outputs:

- prompt-ready evidence bundles
- LLM prompts with evidence-only instructions

### `answer_generation/`

Step 12 outputs:

- generated Arabic answers
- answer-generation evaluation rows

### `claim_extraction/`, `claim_verification/`, `hallucination_mitigation/`

Steps 13-15 outputs:

- extracted claims
- support/weak/unsupported labels
- hallucination mitigation decisions
- refined answers

### `reliability_scoring/`

Step 16 outputs:

- reliability components
- answerability labels
- final reliability labels

### `final_output/`

Step 17 outputs:

- final Arabic answer
- citations and evidence
- supporting relations
- reliability score
- limitations
- final Markdown/CSV/JSON export

## Neo4j Supplemental Import

Copy the supplemental CSVs into the Neo4j import directory and run:

```powershell
docker exec -it ahd-neo4j-final cypher-shell -u neo4j -p "YOUR_PASSWORD" -f /var/lib/neo4j/import/import_supplemental_medical_facts.cypher
```

Verify:

```cypher
MATCH ()-[r:MEDICAL_RELATION]->()
WHERE r.is_supplemental = true
RETURN count(r) AS supplemental_relations;
```

Expected:

```text
26
```

## Notes

The focused supplemental expansion was built from failures in one evaluation batch. Use a fresh offset batch, such as `--offset 75`, for a cleaner generalization test.
