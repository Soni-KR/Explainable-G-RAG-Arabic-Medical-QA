# Frozen Graph: final_v1

This directory is the authoritative, immutable CSV representation of the medical
knowledge graph. `graph_manifest.json` records row counts and SHA-256 checksums.

- `entities.csv`: 2,175 canonical medical entities and aliases.
- `entity_mentions.csv`: 5,767 evidence-backed mentions linked to source Q&A IDs.
- `relation_decisions.csv`: 3,392 validation decisions, including rejected edges.
- `relations.csv`: 1,404 accepted direct medical relations.
- `relations_bidirectional.csv`: 2,808 direct and inverse rows imported into Neo4j.
- `provenance/`: colleague entity/mention hand-off, the 5,000-row QA source,
  candidate edges, raw validator cache, and validated relation records used by our
  finalization/import work.

Runtime import uses `relations_bidirectional.csv`. The decision file remains the
audit trail. Do not edit these files in place; create a new graph version instead.
