import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TRIAL_DIR = ROOT / "outputs" / "05_trial_graph_v1"
STEP8_DIR = TRIAL_DIR / "query_understanding"
STEP9C_DIR = TRIAL_DIR / "hybrid_retrieval"
STEP10_DIR = TRIAL_DIR / "subgraph_reranking"
REPORT_MD = ROOT / "reports" / "trial_graph_v1_step10_subgraph_reranking_report.md"

QUERY_UNDERSTANDING_JSON = STEP8_DIR / "trial_graph_v1_query_understanding.json"
HYBRID_RELATIONS_CSV = STEP9C_DIR / "trial_graph_v1_hybrid_retrieval_relations.csv"

RERANKED_SUBGRAPHS_JSON = STEP10_DIR / "trial_graph_v1_reranked_subgraphs.json"
RERANKED_RELATIONS_CSV = STEP10_DIR / "trial_graph_v1_reranked_relations.csv"
RERANKED_EVIDENCE_CSV = STEP10_DIR / "trial_graph_v1_reranked_evidence.csv"


def relpath(path):
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def write_csv(path, rows, fieldnames):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def to_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def query_index():
    return {row["query_id"]: row for row in load_json(QUERY_UNDERSTANDING_JSON)}


def relation_signature(row):
    return (
        row.get("source_entity_id", ""),
        row.get("graph_relation_type", ""),
        row.get("target_entity_id", ""),
    )


def rank_reason(edge):
    parts = []
    if edge["primary_intent_match"]:
        parts.append("matches primary intent")
    if edge["evidence_count"] > 1:
        parts.append(f"{edge['evidence_count']} evidence rows")
    if edge["direct_edge_count"] > 0:
        parts.append("has original/direct edge support")
    if edge["semantic_support"] >= 0.5:
        parts.append("strong semantic support")
    if edge["evidence_relevance"] >= 0.25:
        parts.append("evidence overlaps query terms")
    if edge["unique_qa_count"] > 1:
        parts.append(f"{edge['unique_qa_count']} distinct QA sources")
    return "; ".join(parts) if parts else "kept as lower-priority supporting graph edge"


def aggregate_query_edges(query_id, query_record, rows):
    groups = defaultdict(list)
    for row in rows:
        groups[relation_signature(row)].append(row)

    reranked_edges = []
    evidence_rows = []
    primary_relation_types = {
        relation_type
        for relation_type, weight in query_record.get("retrieval_plan", {})
        .get("graph_expansion", {})
        .get("relation_type_weights", {})
        .items()
        if to_float(weight) >= 0.9
    }

    for signature, edge_rows in groups.items():
        edge_rows.sort(key=lambda item: to_float(item.get("hybrid_score")), reverse=True)
        best = edge_rows[0]
        top_scores = [to_float(row.get("hybrid_score")) for row in edge_rows[:3]]
        max_score = top_scores[0]
        mean_top_score = sum(top_scores) / len(top_scores)
        evidence_count = len({row.get("qa_id", "") + "|" + row.get("evidence", "") for row in edge_rows})
        unique_qa_count = len({row.get("qa_id", "") for row in edge_rows if row.get("qa_id", "")})
        direct_edge_count = sum(1 for row in edge_rows if row.get("edge_direction") == "direct")
        semantic_support = max(to_float(row.get("semantic_support")) for row in edge_rows)
        evidence_relevance = max(to_float(row.get("evidence_relevance")) for row in edge_rows)
        relation_weight = max(to_float(row.get("relation_weight")) for row in edge_rows)
        primary_intent_match = best.get("graph_relation_type", "") in primary_relation_types

        rerank_score = (
            0.52 * max_score
            + 0.12 * mean_top_score
            + 0.10 * (1 if primary_intent_match else 0)
            + 0.10 * min(evidence_count, 3) / 3
            + 0.08 * min(unique_qa_count, 3) / 3
            + 0.05 * evidence_relevance
            + 0.06 * min(direct_edge_count, 1)
            + 0.07 * max(relation_weight, 0)
        )

        edge = {
            "query_id": query_id,
            "query": best.get("query", ""),
            "rerank_score": round(rerank_score, 6),
            "max_hybrid_score": round(max_score, 6),
            "mean_top_hybrid_score": round(mean_top_score, 6),
            "evidence_count": evidence_count,
            "unique_qa_count": unique_qa_count,
            "direct_edge_count": direct_edge_count,
            "semantic_support": round(semantic_support, 6),
            "evidence_relevance": round(evidence_relevance, 6),
            "relation_weight": round(relation_weight, 6),
            "primary_intent_match": primary_intent_match,
            "source_entity_id": signature[0],
            "source_name": best.get("source_name", ""),
            "source_type": best.get("source_type", ""),
            "graph_relation_type": signature[1],
            "target_entity_id": signature[2],
            "target_name": best.get("target_name", ""),
            "target_type": best.get("target_type", ""),
            "best_seed_entity_name": best.get("seed_entity_name", ""),
            "best_seed_source": best.get("seed_source", ""),
            "rank_reason": "",
        }
        edge["rank_reason"] = rank_reason(edge)
        reranked_edges.append(edge)

        selected_evidence = []
        seen_qa = set()
        for row in edge_rows:
            qa_id = row.get("qa_id", "")
            if qa_id and qa_id in seen_qa:
                continue
            if qa_id:
                seen_qa.add(qa_id)
            selected_evidence.append(row)
            if len(selected_evidence) >= 3:
                break
        for evidence_rank, row in enumerate(selected_evidence, start=1):
            evidence_rows.append(
                {
                    "query_id": query_id,
                    "source_entity_id": signature[0],
                    "graph_relation_type": signature[1],
                    "target_entity_id": signature[2],
                    "evidence_rank": evidence_rank,
                    "hybrid_score": row.get("hybrid_score", ""),
                    "evidence_relevance": row.get("evidence_relevance", ""),
                    "qa_id": row.get("qa_id", ""),
                    "evidence": row.get("evidence", ""),
                    "reason": row.get("reason", ""),
                    "edge_id": row.get("edge_id", ""),
                    "edge_direction": row.get("edge_direction", ""),
                }
            )

    reranked_edges.sort(key=lambda item: item["rerank_score"], reverse=True)
    for rank, edge in enumerate(reranked_edges, start=1):
        edge["subgraph_rank"] = rank
    return reranked_edges, evidence_rows


def write_report(results, top_k):
    lines = [
        "# Trial Graph v1 Step 10 Subgraph Reranking Report",
        "",
        "This step reranks the Step 9C hybrid retrieval output into compact evidence-aware subgraphs.",
        "It does not generate answers yet. It prepares cleaner graph/evidence units for Step 11 context construction.",
        "",
        "## Reranking Signals",
        "",
        "- Best hybrid retrieval score from Step 9C",
        "- Mean score across repeated evidence rows for the same edge",
        "- Evidence count bonus, capped at 3 evidence rows",
        "- Direct/original edge support bonus",
        "- Primary intent relation match from Step 8",
        "",
        "## Query Results",
        "",
    ]
    for result in results:
        lines.extend([f"### {result['query']}", ""])
        for warning in result.get("warnings", []):
            lines.append(f"- Warning: {warning}")
        if result.get("warnings"):
            lines.append("")
        for edge in result["top_subgraph_edges"][:top_k]:
            lines.append(
                f"- `{edge['rerank_score']}` {edge['source_name']} --{edge['graph_relation_type']}--> {edge['target_name']} "
                f"({edge['rank_reason']})"
            )
        lines.append("")
    lines.extend(
        [
            "## Output Files",
            "",
            f"- Reranked subgraphs JSON: `{relpath(RERANKED_SUBGRAPHS_JSON)}`",
            f"- Reranked relations CSV: `{relpath(RERANKED_RELATIONS_CSV)}`",
            f"- Reranked evidence CSV: `{relpath(RERANKED_EVIDENCE_CSV)}`",
            "",
            "## Next Step From Mix.png",
            "",
            "Continue to Step 11: evidence-focused context construction from the reranked subgraphs.",
        ]
    )
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--top-subgraph-edges", type=int, default=8)
    args = parser.parse_args()

    STEP10_DIR.mkdir(parents=True, exist_ok=True)
    queries = query_index()
    hybrid_rows = read_csv(HYBRID_RELATIONS_CSV)
    rows_by_query = defaultdict(list)
    for row in hybrid_rows:
        rows_by_query[row.get("query_id", "")].append(row)

    all_edge_rows = []
    all_evidence_rows = []
    results = []
    for query_id, query_record in queries.items():
        reranked_edges, evidence_rows = aggregate_query_edges(query_id, query_record, rows_by_query.get(query_id, []))
        top_edges = reranked_edges[: args.top_subgraph_edges]
        all_edge_rows.extend(top_edges)
        keep_signatures = {
            (edge["source_entity_id"], edge["graph_relation_type"], edge["target_entity_id"])
            for edge in top_edges
        }
        all_evidence_rows.extend(
            row
            for row in evidence_rows
            if (row["source_entity_id"], row["graph_relation_type"], row["target_entity_id"]) in keep_signatures
        )
        results.append(
            {
                "query_id": query_id,
                "query": query_record["query"],
                "warnings": query_record.get("warnings", []),
                "top_subgraph_edges": top_edges,
            }
        )

    RERANKED_SUBGRAPHS_JSON.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    write_csv(
        RERANKED_RELATIONS_CSV,
        all_edge_rows,
        [
            "query_id",
            "query",
            "subgraph_rank",
            "rerank_score",
            "max_hybrid_score",
            "mean_top_hybrid_score",
            "evidence_count",
            "unique_qa_count",
            "direct_edge_count",
            "semantic_support",
            "evidence_relevance",
            "relation_weight",
            "primary_intent_match",
            "source_entity_id",
            "source_name",
            "source_type",
            "graph_relation_type",
            "target_entity_id",
            "target_name",
            "target_type",
            "best_seed_entity_name",
            "best_seed_source",
            "rank_reason",
        ],
    )
    write_csv(
        RERANKED_EVIDENCE_CSV,
        all_evidence_rows,
        [
            "query_id",
            "source_entity_id",
            "graph_relation_type",
            "target_entity_id",
            "evidence_rank",
            "hybrid_score",
            "evidence_relevance",
            "qa_id",
            "evidence",
            "reason",
            "edge_id",
            "edge_direction",
        ],
    )
    write_report(results, args.top_subgraph_edges)
    print(
        json.dumps(
            {
                "queries": len(results),
                "reranked_relation_rows": len(all_edge_rows),
                "reranked_evidence_rows": len(all_evidence_rows),
                "subgraphs_json": relpath(RERANKED_SUBGRAPHS_JSON),
                "relations_csv": relpath(RERANKED_RELATIONS_CSV),
                "evidence_csv": relpath(RERANKED_EVIDENCE_CSV),
                "report_md": relpath(REPORT_MD),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
