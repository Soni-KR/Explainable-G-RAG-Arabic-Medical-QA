import argparse
import csv
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LOCAL_DEPS_DIR = ROOT / ".deps-step6"
SCRIPTS_DIR = ROOT / "scripts"
TRIAL_DIR = ROOT / "outputs" / "05_trial_graph_v1"
EMBEDDING_DIR = TRIAL_DIR / "embeddings"
REPORT_MD = ROOT / "reports" / "trial_graph_v1_step6_embedding_search_report.md"

DOCUMENTS_CSV = EMBEDDING_DIR / "trial_graph_v1_embedding_documents.csv"
EMBEDDINGS_JSONL = EMBEDDING_DIR / "trial_graph_v1_embeddings.jsonl"
METADATA_JSON = EMBEDDING_DIR / "trial_graph_v1_embeddings_metadata.json"
SEARCH_RESULTS_JSON = EMBEDDING_DIR / "trial_graph_v1_embedding_search_test.json"
SEARCH_RESULTS_CSV = EMBEDDING_DIR / "trial_graph_v1_embedding_search_test.csv"

DEFAULT_QUERIES = [
    "ما علاج الحساسية؟",
    "عندي كحة وبلغم هل هذا ربو؟",
    "ما التحاليل المناسبة لفقر الدم؟",
    "ما أسباب صداع مع دوخة؟",
]


def relpath(path):
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def read_jsonl(path):
    rows = []
    with path.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_csv(path, rows, fieldnames):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def load_embedding_stack():
    if LOCAL_DEPS_DIR.exists():
        sys.path.insert(0, str(LOCAL_DEPS_DIR))
    try:
        import numpy as np
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise SystemExit(
            "Step 6 search requires local embedding dependencies. Install with:\n"
            "  python -m pip install --target .deps-step6 -r requirements-step6-embeddings.txt"
        ) from exc
    return np, SentenceTransformer


def load_query_understanding_helpers():
    sys.path.insert(0, str(SCRIPTS_DIR))
    from step08_understand_queries import load_entity_lexicon, understand_query

    return load_entity_lexicon, understand_query


def load_index(np):
    docs = {row["doc_id"]: row for row in read_csv(DOCUMENTS_CSV)}
    vectors = read_jsonl(EMBEDDINGS_JSONL)
    matrix = np.asarray([row["embedding"] for row in vectors], dtype="float32")
    return docs, vectors, matrix


def top_k_for_query(np, model, docs, vectors, matrix, query_text, top_k):
    query_vector = model.encode([query_text], normalize_embeddings=True)[0].astype("float32")
    scores = matrix @ query_vector
    ranked_indices = np.argsort(-scores)
    results_by_type = {}
    flat_results = []
    type_counts = {"entity": 0, "evidence": 0, "qa": 0}
    for index in ranked_indices:
        record = vectors[int(index)]
        doc_type = record.get("doc_type", "")
        if doc_type not in type_counts:
            continue
        if type_counts[doc_type] >= top_k:
            continue
        type_counts[doc_type] += 1
        doc = docs.get(record["doc_id"], {})
        item = {
            "rank": type_counts[doc_type],
            "doc_id": record["doc_id"],
            "doc_type": doc_type,
            "score": round(float(scores[int(index)]), 6),
            "title": record.get("title", ""),
            "source_id": record.get("source_id", ""),
            "entity_id": record.get("entity_id", ""),
            "qa_id": record.get("qa_id", ""),
            "text_preview": (doc.get("embedding_text", "") or "")[:300],
        }
        results_by_type.setdefault(doc_type, []).append(item)
        flat_results.append(item)
        if all(count >= top_k for count in type_counts.values()):
            break
    return results_by_type, flat_results


def build_enriched_query(query, query_index, lexicon, understand_query):
    understood = understand_query({"query_id": f"embedding_query_{query_index:03d}", "query": query}, lexicon)
    detected_names = [item["canonical_name"] for item in understood.get("detected_entities", [])]
    candidate_names = [item["canonical_name"] for item in understood.get("semantic_candidate_entities", [])]
    intent_focus = [item["answer_focus"] for item in understood.get("intents", [])]
    parts = [query]
    parts.extend(detected_names)
    parts.extend(candidate_names)
    parts.extend(understood.get("expanded_terms", []))
    parts.extend(intent_focus[:1])
    return " | ".join(part for part in parts if part), understood


def write_report(search_results, metadata):
    lines = [
        "# Trial Graph v1 Step 6 Embedding Search Report",
        "",
        "This tests whether generated MiniLM embeddings are searchable before Step 9 semantic/hybrid retrieval.",
        "",
        "## Model",
        "",
        f"- Embedding model: `{metadata.get('model', '')}`",
        f"- Embedded documents: {metadata.get('embedded_document_count', '')}",
        "",
        "## Search Tests",
        "",
    ]
    for result in search_results:
        lines.extend([f"### {result['query']}", ""])
        for search_mode, mode_result in result["mode_results"].items():
            lines.append(f"**Search mode: `{search_mode}`**")
            lines.append("")
            lines.append(f"- Search text: `{mode_result['query_text'][:220]}`")
            lines.append("")
            for doc_type in ["entity", "evidence", "qa"]:
                lines.append(f"Top {doc_type} docs")
                for item in mode_result["results_by_type"].get(doc_type, [])[:5]:
                    lines.append(f"- `{item['score']}` {item['title']} ({item['doc_id']})")
                lines.append("")
            lines.append("")
    lines.extend(
        [
            "## Output Files",
            "",
            f"- Search JSON: `{relpath(SEARCH_RESULTS_JSON)}`",
            f"- Search CSV: `{relpath(SEARCH_RESULTS_CSV)}`",
            "",
            "## Status",
            "",
            "- Embeddings generated: yes",
            "- Vector search tested: yes, using linear cosine search over normalized embeddings",
            "- FAISS/Neo4j vector index: not created yet; this smoke test validates the vectors before choosing the production index.",
        ]
    )
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", action="append", help="Arabic query. Can be repeated.")
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()

    np, SentenceTransformer = load_embedding_stack()
    metadata = json.loads(METADATA_JSON.read_text(encoding="utf-8"))
    model = SentenceTransformer(metadata["model"])
    docs, vectors, matrix = load_index(np)
    load_entity_lexicon, understand_query = load_query_understanding_helpers()
    lexicon = load_entity_lexicon()
    queries = args.query or DEFAULT_QUERIES

    search_results = []
    csv_rows = []
    for query_index, query in enumerate(queries, start=1):
        query_id = f"embedding_query_{query_index:03d}"
        enriched_query, understood = build_enriched_query(query, query_index, lexicon, understand_query)
        modes = [("raw_query", query), ("step8_enriched_query", enriched_query)]
        mode_results = {}
        for search_mode, query_text in modes:
            results_by_type, flat_results = top_k_for_query(np, model, docs, vectors, matrix, query_text, args.top_k)
            mode_results[search_mode] = {
                "query_text": query_text,
                "results_by_type": results_by_type,
            }
            for item in flat_results:
                csv_rows.append(
                    {
                        "query_id": query_id,
                        "query": query,
                        "search_mode": search_mode,
                        "search_text": query_text,
                        **item,
                    }
                )
        search_results.append(
            {
                "query_id": query_id,
                "query": query,
                "query_understanding": {
                    "detected_entities": understood.get("detected_entities", []),
                    "semantic_candidate_entities": understood.get("semantic_candidate_entities", []),
                    "intents": understood.get("intents", []),
                    "warnings": understood.get("warnings", []),
                },
                "mode_results": mode_results,
            }
        )

    SEARCH_RESULTS_JSON.write_text(json.dumps(search_results, ensure_ascii=False, indent=2), encoding="utf-8")
    write_csv(
        SEARCH_RESULTS_CSV,
        csv_rows,
        [
            "query_id",
            "query",
            "search_mode",
            "search_text",
            "doc_type",
            "rank",
            "score",
            "title",
            "doc_id",
            "source_id",
            "entity_id",
            "qa_id",
            "text_preview",
        ],
    )
    write_report(search_results, metadata)
    print(
        json.dumps(
            {
                "queries": len(queries),
                "search_json": relpath(SEARCH_RESULTS_JSON),
                "search_csv": relpath(SEARCH_RESULTS_CSV),
                "report_md": relpath(REPORT_MD),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

