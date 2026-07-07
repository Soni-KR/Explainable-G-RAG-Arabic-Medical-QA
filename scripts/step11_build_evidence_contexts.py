import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TRIAL_DIR = ROOT / "outputs" / "05_trial_graph_v1"
IMPORT_DIR = TRIAL_DIR / "import"
STEP8_DIR = TRIAL_DIR / "query_understanding"
STEP10_DIR = TRIAL_DIR / "subgraph_reranking"
STEP11_DIR = TRIAL_DIR / "context_construction"
REPORT_MD = ROOT / "reports" / "trial_graph_v1_step11_context_construction_report.md"

QA_CSV = IMPORT_DIR / "trial_graph_v1_qa_sources.csv"
QUERY_UNDERSTANDING_JSON = STEP8_DIR / "trial_graph_v1_query_understanding.json"
RERANKED_RELATIONS_CSV = STEP10_DIR / "trial_graph_v1_reranked_relations.csv"
RERANKED_EVIDENCE_CSV = STEP10_DIR / "trial_graph_v1_reranked_evidence.csv"

CONTEXT_BUNDLES_JSON = STEP11_DIR / "trial_graph_v1_context_bundles.json"
CONTEXT_BUNDLES_CSV = STEP11_DIR / "trial_graph_v1_context_bundles.csv"


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


def clean_text(text):
    return " ".join((text or "").split())


def shorten(text, max_chars):
    text = clean_text(text)
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3].rstrip() + "..."


def relation_key(row):
    return (
        row.get("query_id", ""),
        row.get("source_entity_id", ""),
        row.get("graph_relation_type", ""),
        row.get("target_entity_id", ""),
    )


def query_index():
    return {row["query_id"]: row for row in load_json(QUERY_UNDERSTANDING_JSON)}


def qa_index():
    return {row["qa_id"]: row for row in read_csv(QA_CSV)}


def reliability_label(edge, evidence_count):
    score = float(edge.get("rerank_score") or 0)
    if score >= 0.82 and evidence_count >= 2:
        return "strong"
    if score >= 0.75:
        return "medium"
    return "limited"


def build_relation_statement(edge):
    return f"{edge.get('source_name', '')} --{edge.get('graph_relation_type', '')}--> {edge.get('target_name', '')}"


def build_context_bundles(max_edges, max_evidence_per_edge, max_answer_chars, max_context_chars):
    queries = query_index()
    qas = qa_index()
    relations_by_query = defaultdict(list)
    for row in read_csv(RERANKED_RELATIONS_CSV):
        relations_by_query[row.get("query_id", "")].append(row)

    evidence_by_relation = defaultdict(list)
    for row in read_csv(RERANKED_EVIDENCE_CSV):
        evidence_by_relation[relation_key(row)].append(row)

    bundles = []
    flat_rows = []
    for query_id, query_record in queries.items():
        context_chars = 0
        selected_edges = []
        for edge in sorted(relations_by_query.get(query_id, []), key=lambda item: float(item.get("rerank_score") or 0), reverse=True):
            if len(selected_edges) >= max_edges:
                break
            key = relation_key(edge)
            evidence_rows = sorted(evidence_by_relation.get(key, []), key=lambda item: int(item.get("evidence_rank") or 99))
            supporting_evidence = []
            for evidence in evidence_rows[:max_evidence_per_edge]:
                qa = qas.get(evidence.get("qa_id", ""), {})
                item = {
                    "qa_id": evidence.get("qa_id", ""),
                    "evidence_text": clean_text(evidence.get("evidence", "")),
                    "source_question": shorten(qa.get("question", ""), 220),
                    "source_answer": shorten(qa.get("answer", ""), max_answer_chars),
                    "edge_direction": evidence.get("edge_direction", ""),
                    "hybrid_score": evidence.get("hybrid_score", ""),
                }
                added_chars = sum(len(item.get(field, "")) for field in ["evidence_text", "source_question", "source_answer"])
                if context_chars + added_chars > max_context_chars and supporting_evidence:
                    break
                supporting_evidence.append(item)
                context_chars += added_chars

            edge_bundle = {
                "rank": int(edge.get("subgraph_rank") or len(selected_edges) + 1),
                "relation": build_relation_statement(edge),
                "rerank_score": float(edge.get("rerank_score") or 0),
                "source_name": edge.get("source_name", ""),
                "source_type": edge.get("source_type", ""),
                "relation_type": edge.get("graph_relation_type", ""),
                "target_name": edge.get("target_name", ""),
                "target_type": edge.get("target_type", ""),
                "evidence_count": int(edge.get("evidence_count") or len(supporting_evidence)),
                "included_evidence_count": len(supporting_evidence),
                "reliability": reliability_label(edge, int(edge.get("evidence_count") or len(supporting_evidence))),
                "rank_reason": edge.get("rank_reason", ""),
                "supporting_evidence": supporting_evidence,
            }
            selected_edges.append(edge_bundle)

            for evidence_rank, evidence in enumerate(supporting_evidence, start=1):
                flat_rows.append(
                    {
                        "query_id": query_id,
                        "query": query_record["query"],
                        "context_rank": len(flat_rows) + 1,
                        "edge_rank": edge_bundle["rank"],
                        "relation": edge_bundle["relation"],
                        "rerank_score": edge_bundle["rerank_score"],
                        "reliability": edge_bundle["reliability"],
                        "evidence_rank": evidence_rank,
                        "qa_id": evidence["qa_id"],
                        "evidence_text": evidence["evidence_text"],
                        "source_question": evidence["source_question"],
                        "source_answer": evidence["source_answer"],
                    }
                )

        bundle = {
            "query_id": query_id,
            "query": query_record["query"],
            "warnings": query_record.get("warnings", []),
            "detected_entities": query_record.get("detected_entities", []),
            "intents": query_record.get("intents", []),
            "context_policy": {
                "use_only_retrieved_evidence": True,
                "no_answer_generation_in_step_11": True,
                "max_edges": max_edges,
                "max_evidence_per_edge": max_evidence_per_edge,
                "max_context_chars": max_context_chars,
                "used_context_chars_estimate": context_chars,
            },
            "graph_context": selected_edges,
        }
        bundles.append(bundle)
    return bundles, flat_rows


def write_report(bundles):
    lines = [
        "# Trial Graph v1 Step 11 Evidence-Focused Context Construction Report",
        "",
        "This step converts Step 10 reranked subgraphs into compact evidence bundles for later LLM answer generation.",
        "It still does not generate medical answers.",
        "",
        "## Context Rules",
        "",
        "- Keep graph relation, rerank score, and reliability label",
        "- Attach source Q&A evidence snippets",
        "- Preserve Step 8 warnings, especially missing CAUSES relation warnings",
        "- Enforce a simple character budget so prompts can stay controllable",
        "",
        "## Query Context Summary",
        "",
    ]
    for bundle in bundles:
        evidence_count = sum(edge["included_evidence_count"] for edge in bundle["graph_context"])
        lines.extend(
            [
                f"### {bundle['query']}",
                "",
                f"- Graph edges included: {len(bundle['graph_context'])}",
                f"- Evidence snippets included: {evidence_count}",
            ]
        )
        for warning in bundle.get("warnings", []):
            lines.append(f"- Warning: {warning}")
        for edge in bundle["graph_context"][:5]:
            lines.append(f"- `{edge['reliability']}` `{edge['rerank_score']}` {edge['relation']}")
        lines.append("")
    lines.extend(
        [
            "## Output Files",
            "",
            f"- Context bundles JSON: `{relpath(CONTEXT_BUNDLES_JSON)}`",
            f"- Context bundles CSV: `{relpath(CONTEXT_BUNDLES_CSV)}`",
            "",
            "## Next Step From Mix.png",
            "",
            "Continue to Step 12: LLM generation using only these evidence-focused context bundles.",
        ]
    )
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-edges", type=int, default=6)
    parser.add_argument("--max-evidence-per-edge", type=int, default=2)
    parser.add_argument("--max-answer-chars", type=int, default=700)
    parser.add_argument("--max-context-chars", type=int, default=6000)
    args = parser.parse_args()

    STEP11_DIR.mkdir(parents=True, exist_ok=True)
    bundles, flat_rows = build_context_bundles(
        args.max_edges,
        args.max_evidence_per_edge,
        args.max_answer_chars,
        args.max_context_chars,
    )
    CONTEXT_BUNDLES_JSON.write_text(json.dumps(bundles, ensure_ascii=False, indent=2), encoding="utf-8")
    write_csv(
        CONTEXT_BUNDLES_CSV,
        flat_rows,
        [
            "query_id",
            "query",
            "context_rank",
            "edge_rank",
            "relation",
            "rerank_score",
            "reliability",
            "evidence_rank",
            "qa_id",
            "evidence_text",
            "source_question",
            "source_answer",
        ],
    )
    write_report(bundles)
    print(
        json.dumps(
            {
                "queries": len(bundles),
                "context_rows": len(flat_rows),
                "context_bundles_json": relpath(CONTEXT_BUNDLES_JSON),
                "context_bundles_csv": relpath(CONTEXT_BUNDLES_CSV),
                "report_md": relpath(REPORT_MD),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
