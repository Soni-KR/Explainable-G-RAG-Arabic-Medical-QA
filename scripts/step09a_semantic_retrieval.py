import argparse
import csv
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LOCAL_DEPS_DIR = ROOT / ".deps-step6"
TRIAL_DIR = ROOT / "outputs" / "05_trial_graph_v1"
EMBEDDING_DIR = TRIAL_DIR / "embeddings"
STEP8_DIR = TRIAL_DIR / "query_understanding"
STEP9A_DIR = TRIAL_DIR / "semantic_retrieval"
REPORT_MD = ROOT / "reports" / "trial_graph_v1_step9a_semantic_retrieval_report.md"

DOCUMENTS_CSV = EMBEDDING_DIR / "trial_graph_v1_embedding_documents.csv"
EMBEDDINGS_JSONL = EMBEDDING_DIR / "trial_graph_v1_embeddings.jsonl"
METADATA_JSON = EMBEDDING_DIR / "trial_graph_v1_embeddings_metadata.json"
QUERY_UNDERSTANDING_JSON = STEP8_DIR / "trial_graph_v1_query_understanding.json"

SEMANTIC_RESULTS_JSON = STEP9A_DIR / "trial_graph_v1_semantic_retrieval_results.json"
SEMANTIC_RESULTS_CSV = STEP9A_DIR / "trial_graph_v1_semantic_retrieval_results.csv"
SEMANTIC_METRICS_JSON = STEP9A_DIR / "trial_graph_v1_semantic_retrieval_metrics.json"
SEMANTIC_METRICS_CSV = STEP9A_DIR / "trial_graph_v1_semantic_retrieval_metrics.csv"

ARABIC_DIACRITICS_RE = re.compile(r"[\u064b-\u065f\u0670\u06d6-\u06ed]")
TATWEEL_RE = re.compile(r"\u0640+")
WHITESPACE_RE = re.compile(r"\s+")
TOKEN_RE = re.compile(r"[\w\u0600-\u06ff]+", re.UNICODE)
ARABIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")
ARABIC_LETTER_NORMALIZATION = str.maketrans(
    {
        "أ": "ا",
        "إ": "ا",
        "آ": "ا",
        "ٱ": "ا",
        "ى": "ي",
        "ئ": "ي",
        "ؤ": "و",
        "ة": "ه",
    }
)
PUNCTUATION_NORMALIZATION = str.maketrans({"؟": "?", "،": ",", "؛": ";", "“": '"', "”": '"'})

HARD_ENTITY_BOOST = {"exact": 0.35, "alias": 0.25}
HARD_EVIDENCE_BOOST = {"exact": 0.18, "alias": 0.12}
SOFT_ENTITY_BOOST = 0.12
SOFT_EVIDENCE_BOOST = 0.08


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


def normalize_arabic(value):
    text = "" if value is None else str(value)
    text = text.translate(ARABIC_DIGITS)
    text = TATWEEL_RE.sub("", text)
    text = ARABIC_DIACRITICS_RE.sub("", text)
    text = text.translate(ARABIC_LETTER_NORMALIZATION)
    text = text.translate(PUNCTUATION_NORMALIZATION)
    text = WHITESPACE_RE.sub(" ", text)
    return text.strip().lower()


def load_embedding_stack():
    if LOCAL_DEPS_DIR.exists():
        sys.path.insert(0, str(LOCAL_DEPS_DIR))
    try:
        import numpy as np
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise SystemExit(
            "Step 9A requires Step 6 embedding dependencies. Install with:\n"
            "  python -m pip install --target .deps-step6 -r requirements-step6-embeddings.txt"
        ) from exc
    return np, SentenceTransformer


def load_index(np):
    docs = {row["doc_id"]: row for row in read_csv(DOCUMENTS_CSV)}
    vectors = read_jsonl(EMBEDDINGS_JSONL)
    matrix = np.asarray([row["embedding"] for row in vectors], dtype="float32")
    return docs, vectors, matrix


def load_document_records():
    return {row["doc_id"]: row for row in read_csv(DOCUMENTS_CSV)}


def query_embedding_text(query_record):
    detected = [item["canonical_name"] for item in query_record.get("detected_entities", [])]
    candidates = [item["canonical_name"] for item in query_record.get("semantic_candidate_entities", [])]
    intent_focus = [item["answer_focus"] for item in query_record.get("intents", [])]
    parts = [
        query_record.get("query", ""),
        "Key medical fragments: " + ", ".join(query_record.get("key_medical_fragments", [])),
        "Detected entities: " + ", ".join(detected),
        "Candidate entities: " + ", ".join(candidates),
        "Expanded terms: " + ", ".join(query_record.get("expanded_terms", [])),
        "Primary focus: " + (intent_focus[0] if intent_focus else ""),
    ]
    return "\n".join(part for part in parts if part.strip())


def build_boost_maps(query_record):
    hard_entities = {}
    for entity in query_record.get("detected_entities", []):
        entity_id = entity.get("entity_id", "")
        match_type = entity.get("match_type", "")
        if entity_id:
            hard_entities[entity_id] = max(hard_entities.get(entity_id, 0), HARD_ENTITY_BOOST.get(match_type, 0.2))

    hard_evidence = {}
    for entity in query_record.get("detected_entities", []):
        entity_id = entity.get("entity_id", "")
        match_type = entity.get("match_type", "")
        if entity_id:
            hard_evidence[entity_id] = max(hard_evidence.get(entity_id, 0), HARD_EVIDENCE_BOOST.get(match_type, 0.08))

    soft_entities = {entity.get("entity_id", "") for entity in query_record.get("semantic_candidate_entities", []) if entity.get("entity_id")}
    return hard_entities, hard_evidence, soft_entities


def score_boost(record, hard_entities, hard_evidence, soft_entities):
    entity_id = record.get("entity_id") or record.get("source_id", "")
    doc_type = record.get("doc_type", "")
    if doc_type == "entity":
        if entity_id in hard_entities:
            return hard_entities[entity_id], "hard_entity_seed"
        if entity_id in soft_entities:
            return SOFT_ENTITY_BOOST, "semantic_candidate_entity"
    if doc_type == "evidence":
        if entity_id in hard_evidence:
            return hard_evidence[entity_id], "evidence_for_hard_entity_seed"
        if entity_id in soft_entities:
            return SOFT_EVIDENCE_BOOST, "evidence_for_semantic_candidate_entity"
    return 0.0, "semantic_similarity_only"


def semantic_search(np, model, docs, vectors, matrix, query_record, top_k):
    text = query_embedding_text(query_record)
    query_vector = model.encode([text], normalize_embeddings=True)[0].astype("float32")
    similarities = matrix @ query_vector
    hard_entities, hard_evidence, soft_entities = build_boost_maps(query_record)

    scored = []
    for index, record in enumerate(vectors):
        boost, reason = score_boost(record, hard_entities, hard_evidence, soft_entities)
        raw_score = float(similarities[index])
        final_score = raw_score + boost
        doc = docs.get(record["doc_id"], {})
        scored.append(
            {
                "doc_id": record["doc_id"],
                "doc_type": record.get("doc_type", ""),
                "source_id": record.get("source_id", ""),
                "entity_id": record.get("entity_id", ""),
                "qa_id": record.get("qa_id", ""),
                "title": record.get("title", ""),
                "raw_similarity": round(raw_score, 6),
                "boost": round(boost, 6),
                "final_score": round(final_score, 6),
                "score_reason": reason,
                "text_preview": (doc.get("embedding_text", "") or "")[:350],
            }
        )

    results_by_type = {}
    flat_results = []
    for doc_type in ["entity", "evidence", "qa"]:
        seen_titles = set()
        candidates = [row for row in scored if row["doc_type"] == doc_type]
        candidates.sort(key=lambda row: row["final_score"], reverse=True)
        rank = 0
        for row in candidates:
            if doc_type == "entity":
                title_norm = normalize_arabic(row["title"])
                if title_norm in seen_titles:
                    continue
                seen_titles.add(title_norm)
            rank += 1
            ranked = {**row, "rank": rank}
            results_by_type.setdefault(doc_type, []).append(ranked)
            flat_results.append(ranked)
            if rank >= top_k:
                break
    return text, results_by_type, flat_results


def tokenize(value):
    return set(TOKEN_RE.findall(normalize_arabic(value)))


def lexical_similarity(query_tokens, text):
    if not query_tokens:
        return 0.0
    doc_tokens = tokenize(text)
    if not doc_tokens:
        return 0.0
    overlap = len(query_tokens & doc_tokens)
    return overlap / (len(query_tokens) ** 0.5 * len(doc_tokens) ** 0.5)


def lexical_search(docs, query_record, top_k):
    text = query_embedding_text(query_record)
    query_tokens = tokenize(text)
    hard_entities, hard_evidence, soft_entities = build_boost_maps(query_record)
    scored = []
    for record in docs.values():
        boost, reason = score_boost(record, hard_entities, hard_evidence, soft_entities)
        raw_score = lexical_similarity(query_tokens, record.get("embedding_text", ""))
        final_score = raw_score + boost
        scored.append(
            {
                "doc_id": record["doc_id"],
                "doc_type": record.get("doc_type", ""),
                "source_id": record.get("source_id", ""),
                "entity_id": record.get("entity_id", ""),
                "qa_id": record.get("qa_id", ""),
                "title": record.get("title", ""),
                "raw_similarity": round(raw_score, 6),
                "boost": round(boost, 6),
                "final_score": round(final_score, 6),
                "score_reason": reason,
                "text_preview": (record.get("embedding_text", "") or "")[:350],
            }
        )

    results_by_type = {}
    flat_results = []
    for doc_type in ["entity", "evidence", "qa"]:
        seen_titles = set()
        candidates = [row for row in scored if row["doc_type"] == doc_type]
        candidates.sort(key=lambda row: row["final_score"], reverse=True)
        rank = 0
        for row in candidates:
            if doc_type == "entity":
                title_norm = normalize_arabic(row["title"])
                if title_norm in seen_titles:
                    continue
                seen_titles.add(title_norm)
            rank += 1
            ranked = {**row, "rank": rank}
            results_by_type.setdefault(doc_type, []).append(ranked)
            flat_results.append(ranked)
            if rank >= top_k:
                break
    return text, results_by_type, flat_results


def relevance_targets(query_record):
    targets = query_record.get("evaluation_targets", {})
    entity_ids = set(targets.get("relevant_entity_ids", []))
    qa_ids = set(targets.get("relevant_qa_ids", []))
    if not entity_ids:
        entity_ids = {
            item.get("entity_id", "")
            for item in query_record.get("detected_entities", []) + query_record.get("semantic_candidate_entities", [])
            if item.get("entity_id")
        }
    return {"entity_ids": entity_ids, "qa_ids": qa_ids}


def result_is_relevant(row, targets):
    doc_type = row.get("doc_type", "")
    if doc_type == "entity":
        return row.get("entity_id", "") in targets["entity_ids"]
    if doc_type == "evidence":
        return row.get("entity_id", "") in targets["entity_ids"] or row.get("qa_id", "") in targets["qa_ids"]
    if doc_type == "qa":
        return row.get("qa_id", "") in targets["qa_ids"]
    return False


def result_relevance_key(row, targets):
    doc_type = row.get("doc_type", "")
    if doc_type == "entity" and row.get("entity_id", "") in targets["entity_ids"]:
        return row.get("entity_id", "")
    if doc_type == "evidence":
        if row.get("qa_id", "") in targets["qa_ids"]:
            return row.get("qa_id", "")
        if row.get("entity_id", "") in targets["entity_ids"]:
            return row.get("entity_id", "")
    if doc_type == "qa" and row.get("qa_id", "") in targets["qa_ids"]:
        return row.get("qa_id", "")
    return ""


def dcg(relevances):
    import math

    return sum(rel / math.log2(index + 2) for index, rel in enumerate(relevances))


def metric_bundle(rows, targets, relevant_total, recall_k=5, ndcg_k=10):
    if relevant_total <= 0:
        return {
            "relevant_total": 0,
            "retrieved_relevant_at_5": 0,
            "recall_at_5": "",
            "mrr": "",
            "ndcg_at_10": "",
        }
    seen_relevance = set()
    relevances = []
    for row in rows:
        key = result_relevance_key(row, targets)
        if key and key not in seen_relevance:
            seen_relevance.add(key)
            relevances.append(1)
        else:
            relevances.append(0)
    retrieved_relevant_at_5 = sum(relevances[:recall_k])
    first_relevant_rank = next((index + 1 for index, rel in enumerate(relevances) if rel), None)
    ideal_dcg = dcg([1] * min(relevant_total, ndcg_k))
    return {
        "relevant_total": relevant_total,
        "retrieved_relevant_at_5": retrieved_relevant_at_5,
        "recall_at_5": round(retrieved_relevant_at_5 / relevant_total, 6),
        "mrr": round(1 / first_relevant_rank, 6) if first_relevant_rank else 0.0,
        "ndcg_at_10": round(dcg(relevances[:ndcg_k]) / ideal_dcg, 6) if ideal_dcg else 0.0,
    }


def evaluate_semantic_result(query_record, results_by_type):
    targets = relevance_targets(query_record)
    relevant_totals = {
        "entity": len(targets["entity_ids"]),
        "evidence": len(targets["entity_ids"] | targets["qa_ids"]),
        "qa": len(targets["qa_ids"]),
    }
    rows = []
    for doc_type in ["entity", "evidence", "qa"]:
        rows.append(
            {
                "query_id": query_record["query_id"],
                "query": query_record["query"],
                "stage": "semantic_retrieval",
                "result_type": doc_type,
                **metric_bundle(results_by_type.get(doc_type, []), targets, relevant_totals[doc_type]),
            }
        )
    return rows


def write_report(results, metadata, backend):
    lines = [
        "# Trial Graph v1 Step 9A Semantic Retrieval Report",
        "",
        "This is the semantic retrieval layer over Step 6 MiniLM embeddings, using Step 8 query understanding for exact-entity and expansion boosts.",
        "",
        "## Model",
        "",
        f"- Retrieval backend used for this run: `{backend}`",
        f"- Embedding model: `{metadata.get('model', '')}`",
        f"- Embedded documents searched: {metadata.get('embedded_document_count', '')}",
        "",
        "## Retrieval Scoring",
        "",
        "- Base score: cosine similarity because embeddings are normalized.",
        "- Hard detected entity boost: exact/alias entity matches from Step 8.",
        "- Soft candidate boost: expansion/semantic candidate entities from Step 8.",
        "- Use `--backend embedding` to run the original vector-search path when the local model cache is available.",
        "- Results are still semantic retrieval only; graph traversal comes later in Step 9C.",
        "",
        "## Query Results",
        "",
    ]
    for result in results:
        lines.extend([f"### {result['query']}", ""])
        if result.get("warnings"):
            for warning in result["warnings"]:
                lines.append(f"- Warning: {warning}")
            lines.append("")
        for doc_type in ["entity", "evidence", "qa"]:
            lines.append(f"**Top {doc_type} docs**")
            for item in result["results_by_type"].get(doc_type, [])[:5]:
                lines.append(
                    f"- `{item['final_score']}` {item['title']} ({item['score_reason']}; raw={item['raw_similarity']}, boost={item['boost']})"
                )
            lines.append("")
    lines.extend(
        [
            "## Output Files",
            "",
            f"- Semantic retrieval JSON: `{relpath(SEMANTIC_RESULTS_JSON)}`",
            f"- Semantic retrieval CSV: `{relpath(SEMANTIC_RESULTS_CSV)}`",
            f"- Semantic metrics JSON: `{relpath(SEMANTIC_METRICS_JSON)}`",
            f"- Semantic metrics CSV: `{relpath(SEMANTIC_METRICS_CSV)}`",
            "",
            "## Next Step From Mix.png",
            "",
            "Use these semantic retrieval results in Step 9C hybrid retrieval with graph traversal and relation-weighted reranking.",
        ]
    )
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument("--top-k", type=int, default=8)
    parser.add_argument("--backend", choices=["lexical", "embedding"], default="lexical")
    args = parser.parse_args()

    STEP9A_DIR.mkdir(parents=True, exist_ok=True)
    metadata = json.loads(METADATA_JSON.read_text(encoding="utf-8"))
    model = None
    vectors = None
    matrix = None
    if args.backend == "embedding":
        np, SentenceTransformer = load_embedding_stack()
        model = SentenceTransformer(metadata["model"])
        docs, vectors, matrix = load_index(np)
    else:
        docs = load_document_records()
    query_records = json.loads(QUERY_UNDERSTANDING_JSON.read_text(encoding="utf-8"))

    results = []
    csv_rows = []
    metric_rows = []
    for query_record in query_records:
        if args.backend == "embedding":
            search_text, results_by_type, flat_results = semantic_search(None, model, docs, vectors, matrix, query_record, args.top_k)
        else:
            search_text, results_by_type, flat_results = lexical_search(docs, query_record, args.top_k)
        metric_rows.extend(evaluate_semantic_result(query_record, results_by_type))
        result = {
            "query_id": query_record["query_id"],
            "query": query_record["query"],
            "retrieval_backend": args.backend,
            "semantic_search_text": search_text,
            "detected_entities": query_record.get("detected_entities", []),
            "semantic_candidate_entities": query_record.get("semantic_candidate_entities", []),
            "intents": query_record.get("intents", []),
            "warnings": query_record.get("warnings", []),
            "results_by_type": results_by_type,
        }
        results.append(result)
        for row in flat_results:
            csv_rows.append(
                {
                    "query_id": query_record["query_id"],
                    "query": query_record["query"],
                    **row,
                }
            )

    SEMANTIC_RESULTS_JSON.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    SEMANTIC_METRICS_JSON.write_text(json.dumps(metric_rows, ensure_ascii=False, indent=2), encoding="utf-8")
    write_csv(
        SEMANTIC_RESULTS_CSV,
        csv_rows,
        [
            "query_id",
            "query",
            "doc_type",
            "rank",
            "final_score",
            "raw_similarity",
            "boost",
            "score_reason",
            "title",
            "doc_id",
            "source_id",
            "entity_id",
            "qa_id",
            "text_preview",
        ],
    )
    write_csv(
        SEMANTIC_METRICS_CSV,
        metric_rows,
        [
            "query_id",
            "query",
            "stage",
            "result_type",
            "relevant_total",
            "retrieved_relevant_at_5",
            "recall_at_5",
            "mrr",
            "ndcg_at_10",
        ],
    )
    write_report(results, metadata, args.backend)
    print(
        json.dumps(
            {
                "queries": len(results),
                "retrieval_backend": args.backend,
                "semantic_retrieval_json": relpath(SEMANTIC_RESULTS_JSON),
                "semantic_retrieval_csv": relpath(SEMANTIC_RESULTS_CSV),
                "semantic_metrics_json": relpath(SEMANTIC_METRICS_JSON),
                "semantic_metrics_csv": relpath(SEMANTIC_METRICS_CSV),
                "report_md": relpath(REPORT_MD),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
