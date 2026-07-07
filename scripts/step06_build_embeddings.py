import argparse
import csv
import json
import re
import sys
from pathlib import Path


# %% [markdown]
# Step 6 - Embeddings and indexing
# Build embedding documents from the frozen trial graph, then encode them with a
# multilingual sentence-transformer model. This is the vector layer for semantic
# and hybrid retrieval.

ROOT = Path(__file__).resolve().parents[1]
LOCAL_DEPS_DIR = ROOT / ".deps-step6"
TRIAL_DIR = ROOT / "outputs" / "05_trial_graph_v1"
IMPORT_DIR = TRIAL_DIR / "import"
EMBEDDING_DIR = TRIAL_DIR / "embeddings"
REPORT_MD = ROOT / "reports" / "trial_graph_v1_step6_embeddings_report.md"

ENTITIES_CSV = IMPORT_DIR / "trial_graph_v1_entities.csv"
MENTIONS_CSV = IMPORT_DIR / "trial_graph_v1_mentions.csv"
QA_CSV = IMPORT_DIR / "trial_graph_v1_qa_sources.csv"
RELATIONS_CSV = IMPORT_DIR / "trial_graph_v1_bidirectional_relations.csv"

DOCUMENTS_CSV = EMBEDDING_DIR / "trial_graph_v1_embedding_documents.csv"
EMBEDDINGS_JSONL = EMBEDDING_DIR / "trial_graph_v1_embeddings.jsonl"
METADATA_JSON = EMBEDDING_DIR / "trial_graph_v1_embeddings_metadata.json"

DEFAULT_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

ARABIC_DIACRITICS_RE = re.compile(r"[\u064b-\u065f\u0670\u06d6-\u06ed]")
TATWEEL_RE = re.compile(r"\u0640+")
WHITESPACE_RE = re.compile(r"\s+")
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


# %% [markdown]
# Shared utilities
# File helpers, Arabic normalization, alias cleaning, and relation context helpers.


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


def parse_json_list(value):
    if not value:
        return []
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return []
    return parsed if isinstance(parsed, list) else []


def normalize_arabic(value):
    text = "" if value is None else str(value)
    text = text.translate(ARABIC_DIGITS)
    text = TATWEEL_RE.sub("", text)
    text = ARABIC_DIACRITICS_RE.sub("", text)
    text = text.translate(ARABIC_LETTER_NORMALIZATION)
    text = text.translate(PUNCTUATION_NORMALIZATION)
    text = WHITESPACE_RE.sub(" ", text)
    return text.strip().lower()


def text_tokens(value):
    return set(re.findall(r"[\w\u0600-\u06ff]+", normalize_arabic(value), flags=re.UNICODE))


def alias_is_compatible(canonical_name, alias):
    canonical_tokens = text_tokens(canonical_name)
    alias_tokens = text_tokens(alias)
    if not canonical_tokens or not alias_tokens:
        return False
    if len(canonical_tokens) == 1:
        return True
    return len(canonical_tokens & alias_tokens) / len(canonical_tokens) >= 0.5


def clean_aliases(canonical_name, aliases):
    cleaned = []
    seen = set()
    for alias in aliases:
        alias = str(alias).strip()
        alias_norm = normalize_arabic(alias)
        if not alias or alias_norm in seen:
            continue
        if alias_is_compatible(canonical_name, alias):
            cleaned.append(alias)
            seen.add(alias_norm)
    return cleaned


def build_relation_contexts(relations):
    entity_contexts = {}
    mention_qa_contexts = {}
    for row in relations:
        if row.get("edge_direction") != "direct":
            continue
        context = f"{row.get('source_name', '')} {row.get('graph_relation_type', '')} {row.get('target_name', '')}. Evidence: {row.get('evidence', '')}"
        for entity_id in [row.get("source_entity_id", ""), row.get("target_entity_id", "")]:
            if entity_id:
                entity_contexts.setdefault(entity_id, []).append(context)
        qa_id = row.get("qa_id", "")
        if qa_id:
            mention_qa_contexts.setdefault(qa_id, []).append(context)
    return entity_contexts, mention_qa_contexts


# %% [markdown]
# Embedding document construction
# Create entity, evidence mention, and QA/source documents for vector search.


def build_embedding_documents():
    entities = read_csv(ENTITIES_CSV)
    mentions = read_csv(MENTIONS_CSV)
    qa_rows = read_csv(QA_CSV)
    relations = read_csv(RELATIONS_CSV)
    entity_contexts, qa_contexts = build_relation_contexts(relations)

    docs = []
    for row in entities:
        aliases = clean_aliases(row.get("canonical_name", ""), parse_json_list(row.get("aliases", "")))
        text = "\n".join(
            [
                f"Entity: {row.get('canonical_name', '')}",
                f"Aliases: {', '.join(aliases)}",
                f"Type: {row.get('entity_type', '')}",
                f"Quality: {row.get('entity_quality', '')}",
                "Relations: " + " | ".join(entity_contexts.get(row.get("entity_id", ""), [])[:8]),
            ]
        )
        docs.append(
            {
                "doc_id": f"entity::{row['entity_id']}",
                "doc_type": "entity",
                "source_id": row["entity_id"],
                "entity_id": row["entity_id"],
                "qa_id": "",
                "title": row.get("canonical_name", ""),
                "embedding_text": text,
            }
        )

    for row in mentions:
        text = "\n".join(
            [
                f"Evidence: {row.get('evidence', '')}",
                f"Entity: {row.get('canonical_name', '')}",
                f"Surface form: {row.get('surface_form', '')}",
                f"Field: {row.get('field', '')}",
                "Relation context: " + " | ".join(qa_contexts.get(row.get("qa_id", ""), [])[:6]),
            ]
        )
        docs.append(
            {
                "doc_id": f"mention::{row['mention_id']}",
                "doc_type": "evidence",
                "source_id": row["mention_id"],
                "entity_id": row.get("entity_id", ""),
                "qa_id": row.get("qa_id", ""),
                "title": row.get("canonical_name", ""),
                "embedding_text": text,
            }
        )

    for row in qa_rows:
        text = "\n".join(
            [
                f"Category: {row.get('category', '')} ({row.get('category_en', '')})",
                f"Question: {row.get('question', '')}",
                f"Answer: {row.get('answer', '')}",
                "Relation context: " + " | ".join(qa_contexts.get(row.get("qa_id", ""), [])[:8]),
            ]
        )
        docs.append(
            {
                "doc_id": f"qa::{row['qa_id']}",
                "doc_type": "qa",
                "source_id": row["qa_id"],
                "entity_id": "",
                "qa_id": row["qa_id"],
                "title": row.get("question", "")[:120],
                "embedding_text": text,
            }
        )
    return docs


# %% [markdown]
# Model loading and vector generation
# Load local dependencies from `.deps-step6` when available, then encode documents.


def load_sentence_transformer(model_name):
    if LOCAL_DEPS_DIR.exists():
        sys.path.insert(0, str(LOCAL_DEPS_DIR))
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise SystemExit(
            "Step 6 requires sentence-transformers. Install it with:\n"
            "  python -m pip install --target .deps-step6 -r requirements-step6-embeddings.txt\n"
            "Then rerun this script."
        ) from exc
    return SentenceTransformer(model_name)


def build_embeddings(docs, model_name, batch_size, limit):
    model = load_sentence_transformer(model_name)
    selected_docs = docs[:limit] if limit > 0 else docs
    texts = [doc["embedding_text"] for doc in selected_docs]
    vectors = model.encode(
        texts,
        batch_size=batch_size,
        normalize_embeddings=True,
        show_progress_bar=True,
    )
    return selected_docs, vectors


# %% [markdown]
# Outputs and report
# Save document metadata, vector JSONL, embedding metadata, and the Step 6 report.


def write_outputs(docs, embedded_docs, vectors, model_name):
    EMBEDDING_DIR.mkdir(parents=True, exist_ok=True)
    fields = ["doc_id", "doc_type", "source_id", "entity_id", "qa_id", "title", "embedding_text"]
    write_csv(DOCUMENTS_CSV, docs, fields)
    with EMBEDDINGS_JSONL.open("w", encoding="utf-8") as file:
        for doc, vector in zip(embedded_docs, vectors):
            file.write(
                json.dumps(
                    {
                        "doc_id": doc["doc_id"],
                        "doc_type": doc["doc_type"],
                        "source_id": doc["source_id"],
                        "entity_id": doc["entity_id"],
                        "qa_id": doc["qa_id"],
                        "title": doc["title"],
                        "model": model_name,
                        "embedding": [round(float(value), 8) for value in vector.tolist()],
                    },
                    ensure_ascii=False,
                    separators=(",", ":"),
                )
                + "\n"
            )
    metadata = {
        "step": "Step 6 - embeddings/indexing",
        "model": model_name,
        "document_count": len(docs),
        "embedded_document_count": len(embedded_docs),
        "documents_csv": relpath(DOCUMENTS_CSV),
        "embeddings_jsonl": relpath(EMBEDDINGS_JSONL),
        "frozen_graph": "trial_graph_v1",
    }
    METADATA_JSON.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    return metadata


def write_report(metadata):
    lines = [
        "# Trial Graph v1 Step 6 Embeddings Report",
        "",
        "This is the official Step 6 embedding/indexing layer for the frozen `trial_graph_v1` graph.",
        "",
        "## Model",
        "",
        f"- Embedding model: `{metadata['model']}`",
        "",
        "## Documents",
        "",
        f"- Prepared documents: {metadata['document_count']}",
        f"- Embedded documents: {metadata['embedded_document_count']}",
        "",
        "## Output Files",
        "",
        f"- Embedding documents: `{metadata['documents_csv']}`",
        f"- Embeddings JSONL: `{metadata['embeddings_jsonl']}`",
        f"- Metadata: `{relpath(METADATA_JSON)}`",
        "",
        "## Scope",
        "",
        "- Entity nodes are embedded using canonical names, compatible aliases, entity type, quality, and relation context.",
        "- Evidence mentions are embedded using evidence text, entity names, surface form, field, and relation context.",
        "- QA/source records are embedded using question, answer, category, and relation context.",
    ]
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


# %% [markdown]
# CLI entry point
# `--prepare-only` writes documents without loading the model.


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--limit", type=int, default=0, help="Use a small limit for smoke tests. 0 embeds all documents.")
    parser.add_argument("--prepare-only", action="store_true", help="Write embedding documents but do not load the model.")
    args = parser.parse_args()

    docs = build_embedding_documents()
    EMBEDDING_DIR.mkdir(parents=True, exist_ok=True)
    write_csv(DOCUMENTS_CSV, docs, ["doc_id", "doc_type", "source_id", "entity_id", "qa_id", "title", "embedding_text"])

    if args.prepare_only:
        print(
            json.dumps(
                {
                    "prepared_documents": len(docs),
                    "documents_csv": relpath(DOCUMENTS_CSV),
                    "status": "prepare_only",
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return

    embedded_docs, vectors = build_embeddings(docs, args.model, args.batch_size, args.limit)
    metadata = write_outputs(docs, embedded_docs, vectors, args.model)
    write_report(metadata)
    print(json.dumps(metadata, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
