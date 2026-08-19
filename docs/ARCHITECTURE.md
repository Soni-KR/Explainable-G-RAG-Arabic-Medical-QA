# Production Architecture

This document describes the frozen `final_v2` system. Historical experiments may
remain in source control for reproducibility, but the switches listed under
"Disabled branches" are not part of production.

![MG-Retriever architecture](architecture.png)

## Graph Layer

Neo4j stores three node labels:

- `MedicalEntity`: canonical name, normalized name, aliases, entity type, version.
- `EvidenceMention`: source phrase, field, evidence text, confidence, version.
- `QARecord`: question, answer, category, source row, version.

Relationships are `MENTIONED_IN`, `EVIDENCE_FROM`, and `MEDICAL_RELATION`.
Medical relations preserve the direct relation ID, confidence, QA provenance,
evidence, and whether an edge is direct or inverse. All reads are filtered by
`graph_version=final_v2`.

## Step 6: Embeddings

`src/step06_build_embedding_indexes.py` builds one E5 passage per entity, evidence
mention, and QA record with `intfloat/multilingual-e5-base` (768 dimensions). It
uses masked mean pooling, L2 normalization, versioned metadata, batched writes, and
three Neo4j vector indexes. Existing valid vectors are resumable.

## Step 8: Query Understanding

1. Conservative Python Arabic normalization.
2. One strict GPT-OSS-20B JSON call for correction, reformulation, class,
   complexity, intent, and explicit medical phrases.
3. Python schema and meaning-preservation validation.
4. Exact canonical, alias, and article-normalized Neo4j linking.
5. Deterministic retrieval planning and low-specificity seed handling.

No LLM assigns graph IDs or retrieval depth.

## Steps 9-11: Retrieval and Context

Step 9 combines:

- E5 vector search over entities, evidence, and QA records;
- one-hop validated graph traversal;
- direct QA retrieval;
- conditional held-out-safe SQLite FTS when ordinary evidence is partial.

Step 10 uses deterministic semantic, identity, intent, concept, constraint,
anatomy, source-quality, and graph-support features. Different diseases, anatomy,
laterality, generic nodes, and type conflicts receive penalties.

Step 11 applies absolute relevance and provenance gates before limiting the context.
It does not add evidence merely for channel diversity. Only selected evidence and
relation cards enter the citation allowlist.

## Steps 12-17: Generation and Safety

Step 12 asks GPT-OSS-20B for at most two self-contained claims, each citing exactly
one allowlisted evidence item. Python, not the model, assigns provenance IDs.

Steps 13-15 extract atomic claims, verify them against one complete evidence-row
feature vector, and remove unsupported claims. Checks include citation validity,
support, entity identity, intent, medical concepts, anatomy, negation, numbers, and
recommendation evidence. The answer state is one of `fully_answerable`,
`partially_answerable`, `supported_but_incomplete`, `insufficient_evidence`, or
`generation_unavailable`.

Steps 16-17 combine retrieval and verification signals into an uncalibrated
reliability label and return the answer, citations, provenance, limitations, claim
audit, and per-stage latency.

## Frozen Configuration

- Graph: `final_v2`
- Embeddings: `intfloat/multilingual-e5-base`, 768 dimensions
- Query and answer model: `openai/gpt-oss-20b` through Groq
- Query prompt: `query_analysis_v1`
- Answer prompt: `grounded_claim_first_v3_1`
- Verification: `deterministic_v3`
- Semantic retrieval seed threshold: 0.72
- Context minimum score: 0.40
- Context minimum answer relevance: 0.35
- Context minimum source reliability: 0.55
- Context minimum intent support: 0.50

## Disabled Branches

The supplemental graph, learned candidate reranker, semantic claim adjudication,
E5 verifier calibrator, conditional cross-encoder rescue, dual-QA experimental
retriever, and forced extractive fallback are disabled. Their pilots either failed
safety gates, provided insufficient gains, or were not independently validated.
