from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path
from time import perf_counter
from typing import Any

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from scripts.evaluation_common import (
    DEFAULT_GOLD_FILE,
    RETRIEVAL_OUTPUT_ROOT,
    build_manifest,
    create_run_directory,
    ensure_run_available,
    load_gold_queries,
    macro_average,
    make_run_id,
    write_json,
    write_jsonl,
)
from src.config import AppConfig, load_final_config
from src.evaluation_metrics import efficiency_metrics, retrieval_metrics
from src.models import (
    HybridRetrievalBundle,
    RerankedSubgraph,
    VectorSearchResult,
)
from src.neo4j_repository import Neo4jRepository
from src.step06_build_embedding_indexes import load_model
from src.step08a_normalize_query import normalize_query
from src.step08b_analyze_query import analyze_and_link_query
from src.step08d_plan_retrieval import build_retrieval_plan
from src.step09_hybrid_retrieval import (
    collect_evidence,
    embed_query,
    retrieve_hybrid,
    score_relations,
    seed_scores,
    token_set,
    vector_results,
)
from src.step10_rerank_subgraph import rerank_subgraph


MODES = (
    "lexical_only",
    "vector_only",
    "graph_only",
    "hybrid_without_reranking",
    "full_hybrid",
)


def stable_unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))


def lexical_score(query: str, document: str) -> float:
    query_tokens = token_set(query)
    document_tokens = token_set(document)
    if not query_tokens or not document_tokens:
        return 0.0
    overlap = len(query_tokens & document_tokens)
    if not overlap:
        return 0.0
    recall = overlap / len(query_tokens)
    precision = overlap / len(document_tokens)
    token_f1 = 2 * precision * recall / (precision + recall)
    normalized_query = normalize_query(query).normalized_query
    normalized_document = normalize_query(document).normalized_query
    phrase_bonus = 1.0 if normalized_query and normalized_query in normalized_document else 0.0
    return round(min(1.0, 0.65 * token_f1 + 0.30 * recall + 0.05 * phrase_bonus), 6)


def load_lexical_corpus(repository: Neo4jRepository) -> dict[str, list[dict[str, Any]]]:
    """Read the frozen Neo4j text corpus once; no CSV or supplemental data is used."""
    entities = repository.get_entities()
    mentions = repository._execute_read(
        """
MATCH (mention:EvidenceMention {graph_version: $graph_version})
OPTIONAL MATCH (entity:MedicalEntity)-[:MENTIONED_IN]->(mention)
WHERE entity.graph_version = $graph_version
OPTIONAL MATCH (mention)-[:EVIDENCE_FROM]->(qa:QARecord)
WHERE qa.graph_version = $graph_version
RETURN mention.mention_id AS result_id,
       coalesce(entity.entity_id, '') AS entity_id,
       coalesce(qa.qa_id, '') AS qa_id,
       coalesce(mention.surface_form, '') AS title,
       coalesce(mention.evidence, '') AS text,
       {field: mention.field, confidence: mention.confidence,
        entity_name: entity.canonical_name, question: qa.question,
        answer: qa.answer, category: qa.category,
        source_quality: qa.source_quality} AS metadata
""".strip(),
        {"graph_version": repository.graph_version},
    )
    qa_records = repository._execute_read(
        """
MATCH (qa:QARecord {graph_version: $graph_version})
RETURN qa.qa_id AS result_id,
       qa.qa_id AS qa_id,
       coalesce(qa.question, '') AS title,
       coalesce(qa.question, '') + '\n' + coalesce(qa.answer, '') AS text,
       {question: qa.question, answer: qa.answer, category: qa.category,
        source_row_number: qa.source_row_number,
        source_quality: qa.source_quality} AS metadata
""".strip(),
        {"graph_version": repository.graph_version},
    )
    return {"entities": entities, "mentions": mentions, "qa_records": qa_records}


def lexical_results(
    query: str,
    corpus: dict[str, list[dict[str, Any]]],
    plan: Any,
) -> list[VectorSearchResult]:
    candidates: list[VectorSearchResult] = []
    entity_rows = []
    for row in corpus["entities"]:
        aliases = row.get("aliases") if isinstance(row.get("aliases"), list) else []
        text = " | ".join(
            [str(row.get("canonical_name") or ""), *[str(alias) for alias in aliases], str(row.get("entity_type") or "")]
        )
        score = lexical_score(query, text)
        if score:
            entity_rows.append((score, row, text))
    for score, row, text in sorted(entity_rows, key=lambda item: item[0], reverse=True)[: plan.entity_top_k]:
        candidates.append(
            VectorSearchResult(
                result_id=str(row.get("entity_id") or ""),
                document_type="MedicalEntity",
                score=score,
                entity_id=str(row.get("entity_id") or ""),
                title=str(row.get("canonical_name") or ""),
                text=text,
                metadata={"entity_type": row.get("entity_type"), "aliases": row.get("aliases") or []},
            )
        )

    for document_type, rows, top_k in (
        ("EvidenceMention", corpus["mentions"], plan.evidence_top_k),
        ("QARecord", corpus["qa_records"], plan.qa_top_k),
    ):
        ranked = []
        for row in rows:
            text = " ".join(
                [str(row.get("title") or ""), str(row.get("text") or ""), json.dumps(row.get("metadata") or {}, ensure_ascii=False)]
            )
            score = lexical_score(query, text)
            if score:
                ranked.append((score, row))
        for score, row in sorted(ranked, key=lambda item: item[0], reverse=True)[:top_k]:
            candidates.append(
                VectorSearchResult(
                    result_id=str(row.get("result_id") or ""),
                    document_type=document_type,
                    score=score,
                    entity_id=str(row.get("entity_id") or ""),
                    qa_id=str(row.get("qa_id") or ""),
                    title=str(row.get("title") or ""),
                    text=str(row.get("text") or ""),
                    metadata=dict(row.get("metadata") or {}),
                )
            )
    return candidates


def graph_bundle(
    analysis: Any,
    linking: Any,
    plan: Any,
    repository: Neo4jRepository,
    config: AppConfig,
) -> HybridRetrievalBundle:
    seeds = seed_scores(linking, plan, [], config)
    rows = repository.get_medical_relations(
        list(seeds),
        plan.preferred_relation_types,
        max(1, plan.hop_depth),
        max(config.retrieval.relation_top_k * 3, config.retrieval.relation_top_k),
    )
    relations = score_relations(
        rows,
        analysis.reformulated_query,
        seeds,
        plan.preferred_relation_types,
        [],
    )[: config.retrieval.relation_top_k]
    evidence = collect_evidence(relations, [], config.retrieval.context_top_k * 2)
    return HybridRetrievalBundle(
        query=analysis.original_query,
        normalized_query=analysis.normalized_query,
        reformulated_query=analysis.reformulated_query,
        plan=plan,
        relations=relations,
        evidence=evidence,
        warnings=[] if seeds else ["Graph-only mode had no deterministically linked seed entity."],
    )


def vector_bundle(
    analysis: Any,
    plan: Any,
    repository: Neo4jRepository,
    config: AppConfig,
    model: Any,
) -> HybridRetrievalBundle:
    embedding, _ = embed_query(analysis.reformulated_query, config, model=model)
    vectors = vector_results(repository, embedding, config, plan)
    evidence = collect_evidence([], vectors, config.retrieval.context_top_k * 2)
    return HybridRetrievalBundle(
        query=analysis.original_query,
        normalized_query=analysis.normalized_query,
        reformulated_query=analysis.reformulated_query,
        plan=plan,
        vector_results=vectors,
        evidence=evidence,
    )


def lexical_bundle(analysis: Any, plan: Any, corpus: dict[str, list[dict[str, Any]]], config: AppConfig) -> HybridRetrievalBundle:
    results = lexical_results(analysis.reformulated_query, corpus, plan)
    return HybridRetrievalBundle(
        query=analysis.original_query,
        normalized_query=analysis.normalized_query,
        reformulated_query=analysis.reformulated_query,
        plan=plan,
        vector_results=results,
        evidence=collect_evidence([], results, config.retrieval.context_top_k * 2),
    )


def unreranked_subgraph(bundle: HybridRetrievalBundle, config: AppConfig) -> RerankedSubgraph:
    return RerankedSubgraph(
        query=bundle.query,
        relations=bundle.relations[: min(config.retrieval.relation_top_k, 12)],
        evidence=bundle.evidence[: config.retrieval.context_top_k],
        warnings=bundle.warnings,
    )


def run_mode(
    mode: str,
    analysis: Any,
    linking: Any,
    plan: Any,
    repository: Neo4jRepository,
    config: AppConfig,
    model: Any | None,
    corpus: dict[str, list[dict[str, Any]]] | None,
) -> tuple[HybridRetrievalBundle, RerankedSubgraph]:
    if mode == "lexical_only":
        bundle = lexical_bundle(analysis, plan, corpus or {}, config)
        return bundle, unreranked_subgraph(bundle, config)
    if mode == "vector_only":
        bundle = vector_bundle(analysis, plan, repository, config, model)
        return bundle, unreranked_subgraph(bundle, config)
    if mode == "graph_only":
        bundle = graph_bundle(analysis, linking, plan, repository, config)
        return bundle, unreranked_subgraph(bundle, config)

    bundle = retrieve_hybrid(
        analysis,
        linking,
        plan,
        repository=repository,
        config=config,
        model=model,
    )
    if mode == "hybrid_without_reranking":
        return bundle, unreranked_subgraph(bundle, config)
    return bundle, rerank_subgraph(bundle, config=config)


def rankings(bundle: HybridRetrievalBundle, subgraph: RerankedSubgraph) -> dict[str, list[str]]:
    vector_entity_ids = [
        item.entity_id
        for item in bundle.vector_results
        if item.document_type == "MedicalEntity" and item.entity_id
    ]
    relation_entity_ids = [
        entity_id
        for relation in subgraph.relations
        for entity_id in (relation.source_entity_id, relation.target_entity_id)
    ]
    return {
        "entity_ids": stable_unique([*vector_entity_ids, *relation_entity_ids]),
        "evidence_ids": stable_unique([item.source_id for item in subgraph.evidence]),
        "qa_ids": stable_unique([item.qa_id for item in subgraph.evidence]),
        "relation_ids": stable_unique(
            [item.source_relation_id or item.relation_id for item in subgraph.relations]
        ),
    }


def query_metrics(ranked: dict[str, list[str]], gold: Any) -> dict[str, Any]:
    if gold.annotation_status not in {"annotated", "adjudicated"}:
        reason = "Provisional dataset labels require human confirmation before gold scoring."
        return {
            category: {"status": "unavailable", "reason": reason}
            for category in ("entities", "evidence", "qa", "relations")
        }
    return {
        "entities": retrieval_metrics(ranked["entity_ids"], gold.gold_entity_ids or []),
        "evidence": retrieval_metrics(ranked["evidence_ids"], gold.gold_evidence_ids or []),
        "qa": retrieval_metrics(ranked["qa_ids"], gold.gold_qa_ids or []),
        "relations": retrieval_metrics(ranked["relation_ids"], gold.gold_relation_ids or []),
    }


def aggregate_mode(records: list[dict[str, Any]]) -> dict[str, Any]:
    categories = {}
    for category in ("entities", "evidence", "qa", "relations"):
        categories[category] = macro_average(
            [record["metrics"][category] for record in records],
            ("recall_at_5", "mrr", "ndcg_at_10"),
        )
    categories["efficiency"] = efficiency_metrics(
        [record["timings_ms"] for record in records]
    )
    return categories


def main() -> int:
    parser = argparse.ArgumentParser(description="Run independent retrieval ablations on final_v1.")
    parser.add_argument("--gold-file", type=Path, default=DEFAULT_GOLD_FILE)
    parser.add_argument("--mode", action="append", choices=MODES, default=[])
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--run-id", default="")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    modes = args.mode or list(MODES)
    gold_path = args.gold_file.resolve()
    gold_queries = load_gold_queries(gold_path, args.limit)
    config = load_final_config()
    if config.graph_version != "final_v1":
        raise RuntimeError("Retrieval evaluation is restricted to frozen final_v1.")
    if args.dry_run:
        print(json.dumps({"status": "dry_run", "queries": len(gold_queries), "modes": modes}, indent=2))
        return 0
    if not gold_queries:
        raise RuntimeError("The gold template has no annotated query rows.")

    run_id = args.run_id or make_run_id("retrieval")
    ensure_run_available(RETRIEVAL_OUTPUT_ROOT, run_id)
    records_by_mode: dict[str, list[dict[str, Any]]] = {mode: [] for mode in modes}
    needs_model = any(mode in {"vector_only", "hybrid_without_reranking", "full_hybrid"} for mode in modes)
    model = None
    if needs_model:
        model, _, _ = load_model(config.embeddings.model_name, config.embeddings.dimension)

    with Neo4jRepository(config=config) as repository:
        graph_counts = repository.get_graph_counts()
        corpus = load_lexical_corpus(repository) if "lexical_only" in modes else None
        for gold in gold_queries:
            analysis_started = perf_counter()
            analysis, linking = analyze_and_link_query(gold.query, repository=repository, config=config)
            plan = build_retrieval_plan(analysis, linking, config=config)
            analysis_ms = round((perf_counter() - analysis_started) * 1000.0, 3)
            for mode in modes:
                mode_started = perf_counter()
                bundle, subgraph = run_mode(
                    mode, analysis, linking, plan, repository, config, model, corpus
                )
                retrieval_ms = round((perf_counter() - mode_started) * 1000.0, 3)
                ranked = rankings(bundle, subgraph)
                records_by_mode[mode].append(
                    {
                        "evaluation_version": "evaluation-v1",
                        "query_id": gold.query_id,
                        "query": gold.query,
                        "query_group": gold.query_group,
                        "mode": mode,
                        "gold": gold.to_dict(),
                        "query_analysis": asdict(analysis),
                        "entity_linking": asdict(linking),
                        "retrieval_plan": asdict(plan),
                        "rankings": ranked,
                        "relations": [asdict(item) for item in subgraph.relations],
                        "evidence": [asdict(item) for item in subgraph.evidence],
                        "metrics": query_metrics(ranked, gold),
                        "timings_ms": {
                            "step08_shared_query_processing": analysis_ms,
                            "retrieval_mode": retrieval_ms,
                            "end_to_end": round(analysis_ms + retrieval_ms, 3),
                        },
                        "warnings": list(dict.fromkeys([*bundle.warnings, *subgraph.warnings])),
                    }
                )

    aggregate = {mode: aggregate_mode(records) for mode, records in records_by_mode.items()}
    manifest = build_manifest(
        run_id=run_id,
        run_type="retrieval_ablation",
        modes=modes,
        gold_path=gold_path,
        gold_count=len(gold_queries),
        config=config,
        graph_counts=graph_counts,
        arguments={key: str(value) if isinstance(value, Path) else value for key, value in vars(args).items()},
    )
    run_directory = create_run_directory(RETRIEVAL_OUTPUT_ROOT, run_id)
    for mode, records in records_by_mode.items():
        write_jsonl(run_directory / f"{mode}.jsonl", records)
    write_json(run_directory / "metrics.json", aggregate)
    write_json(run_directory / "manifest.json", manifest)
    print(json.dumps({"status": "ok", "run_id": run_id, "output": str(run_directory), "queries": len(gold_queries), "modes": modes}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
