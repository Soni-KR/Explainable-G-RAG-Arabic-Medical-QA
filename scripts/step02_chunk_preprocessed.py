import csv
import json
from collections import Counter, defaultdict
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent if SCRIPT_DIR.name == "scripts" else SCRIPT_DIR
PREPROCESSING_DIR = BASE_DIR / "outputs" / "01_preprocessing"
CHUNKING_DIR = BASE_DIR / "outputs" / "02_chunking"
REPORTS_DIR = BASE_DIR / "reports"

INPUT_CSV = PREPROCESSING_DIR / "ahd_subset_5000_preprocessed.csv"
CHUNKS_CSV = CHUNKING_DIR / "ahd_chunks_5000.csv"
CHUNKS_JSONL = CHUNKING_DIR / "ahd_chunks_5000.jsonl"
CHUNK_REPORT_MD = REPORTS_DIR / "ahd_chunking_report.md"

MAX_ROWS_PER_CHUNK = 8
MAX_CHARS_PER_CHUNK = 6500
GRAPH_CONSTRUCTION_SPLIT = "graph_train"


def parse_json_list(value):
    if not value:
        return []
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return []
    return parsed if isinstance(parsed, list) else []


def relpath(path):
    return path.relative_to(BASE_DIR).as_posix()


def medical_focus_for_row(row):
    weak_hints = parse_json_list(row.get("weak_medical_hints", "[]"))
    if weak_hints:
        first = weak_hints[0]
        return f"{first.get('type', 'medical')}::{first.get('canonical', 'unknown')}"
    return "uncategorized::no_weak_hint"


def row_to_chunk_piece(row):
    return (
        f"[QA_ID: {row['subset_id']} | SOURCE_ROW: {row['source_row_number']}]\n"
        f"Split: {row['split']}\n"
        f"Category: {row['category']} ({row['category_en']})\n"
        f"Question: {row['question']}\n"
        f"Answer: {row['answer']}"
    )


def row_to_normalized_piece(row):
    return (
        f"[QA_ID: {row['subset_id']}]\n"
        f"Split: {row['split']}\n"
        f"Category: {row['category']} ({row['category_en']})\n"
        f"Question_norm: {row['question_norm']}\n"
        f"Answer_norm: {row['answer_norm']}"
    )


def row_to_qa_record(row):
    return {
        "subset_id": row["subset_id"],
        "source_row_number": row["source_row_number"],
        "split": row["split"],
        "category": row["category"],
        "category_en": row["category_en"],
        "question": row["question"],
        "answer": row["answer"],
        "question_norm": row["question_norm"],
        "answer_norm": row["answer_norm"],
    }


def make_chunk(category, category_en, semantic_group, rows, chunk_index):
    detected_counter = Counter()
    detected_by_type = defaultdict(Counter)

    for row in rows:
        for term in parse_json_list(row.get("weak_medical_hints", "[]")):
            canonical = term.get("canonical")
            term_type = term.get("type", "unknown")
            if canonical:
                detected_counter[canonical] += 1
                detected_by_type[term_type][canonical] += 1

    chunk_id = f"chunk_{chunk_index:05d}"
    chunk_text = "\n\n---\n\n".join(row_to_chunk_piece(row) for row in rows)
    normalized_chunk_text = "\n\n---\n\n".join(row_to_normalized_piece(row) for row in rows)
    char_count = len(chunk_text)
    oversized = char_count > MAX_CHARS_PER_CHUNK

    return {
        "chunk_id": chunk_id,
        "category": category,
        "category_en": category_en,
        "semantic_group": semantic_group,
        "qa_ids": json.dumps([row["subset_id"] for row in rows], ensure_ascii=False),
        "source_row_numbers": json.dumps([row["source_row_number"] for row in rows], ensure_ascii=False),
        "qa_records": json.dumps([row_to_qa_record(row) for row in rows], ensure_ascii=False),
        "row_count": len(rows),
        "char_count": char_count,
        "normalized_char_count": len(normalized_chunk_text),
        "oversized": oversized,
        "oversized_single_row_chunk": oversized and len(rows) == 1,
        "top_weak_medical_hints": json.dumps(
            [{"canonical": term, "count": count} for term, count in detected_counter.most_common(12)],
            ensure_ascii=False,
        ),
        "weak_hints_by_type": json.dumps(
            {
                term_type: [
                    {"canonical": term, "count": count}
                    for term, count in counter.most_common(8)
                ]
                for term_type, counter in sorted(detected_by_type.items())
            },
            ensure_ascii=False,
        ),
        "chunk_text": chunk_text,
        "normalized_chunk_text": normalized_chunk_text,
    }


def split_group_into_chunks(rows):
    chunks = []
    current = []
    current_chars = 0

    for row in rows:
        piece_len = len(row_to_chunk_piece(row))
        would_exceed_rows = len(current) >= MAX_ROWS_PER_CHUNK
        would_exceed_chars = current and current_chars + piece_len > MAX_CHARS_PER_CHUNK

        if would_exceed_rows or would_exceed_chars:
            chunks.append(current)
            current = []
            current_chars = 0

        current.append(row)
        current_chars += piece_len

    if current:
        chunks.append(current)

    return chunks


def write_markdown_report(report, examples):
    lines = [
        "# AHD Step 2 Chunking Report",
        "",
        "## What was produced",
        "",
        f"- Input: `{relpath(INPUT_CSV)}`",
        f"- Chunks CSV: `{relpath(CHUNKS_CSV)}`",
        f"- Chunks JSONL: `{relpath(CHUNKS_JSONL)}`",
        "",
        "## Chunking strategy",
        "",
        f"1. Keep only `{GRAPH_CONSTRUCTION_SPLIT}` rows for graph construction chunks.",
        "2. Group rows by Arabic category, English category label, and weak semantic hint.",
        "3. Use dictionary hints only as weak grouping context, not final graph entities.",
        "4. Put rows with no weak hint into `uncategorized::no_weak_hint` within their category.",
        f"5. Limit each chunk to at most {MAX_ROWS_PER_CHUNK} QA pairs and about {MAX_CHARS_PER_CHUNK} characters.",
        "6. Preserve QA IDs and source row numbers for evidence traceability.",
        "7. Store both original Arabic chunk text and normalized chunk text.",
        "",
        "## Summary",
        "",
        f"- Input rows: {report['input_rows']}",
        f"- Graph-train rows chunked: {report['graph_train_rows']}",
        f"- Output chunks: {report['output_chunks']}",
        f"- Categories: {report['categories']}",
        f"- Semantic groups: {report['semantic_groups']}",
        f"- Average rows per chunk: {report['avg_rows_per_chunk']}",
        f"- Max rows per chunk: {report['max_rows_per_chunk']}",
        f"- Max characters per chunk: {report['max_chars_per_chunk']}",
        f"- Oversized chunks: {report['oversized_chunks']}",
        f"- Oversized single-row chunks: {report['oversized_single_row_chunks']}",
        "",
        "## Example chunks",
        "",
    ]

    for example in examples:
        lines.extend(
            [
                f"### {example['chunk_id']}",
                "",
                f"- Category: {example['category']} / {example['category_en']}",
                f"- Semantic group: `{example['semantic_group']}`",
                f"- QA IDs: `{example['qa_ids']}`",
                f"- Row count: {example['row_count']}",
                f"- Oversized: {example['oversized']}",
                f"- Top weak medical hints: `{example['top_weak_medical_hints']}`",
                "",
            ]
        )

    CHUNK_REPORT_MD.write_text("\n".join(lines), encoding="utf-8")


def main():
    CHUNKING_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    with INPUT_CSV.open("r", encoding="utf-8-sig", newline="") as handle:
        all_rows = list(csv.DictReader(handle))

    rows = [row for row in all_rows if row.get("split") == GRAPH_CONSTRUCTION_SPLIT]

    grouped = defaultdict(list)
    for row in rows:
        key = (row["category"], row["category_en"], medical_focus_for_row(row))
        grouped[key].append(row)

    chunks = []
    chunk_index = 1
    for key in sorted(grouped, key=lambda item: (item[1], item[2], item[0])):
        category, category_en, semantic_group = key
        group_rows = sorted(grouped[key], key=lambda row: row["subset_id"])
        for chunk_rows in split_group_into_chunks(group_rows):
            chunks.append(make_chunk(category, category_en, semantic_group, chunk_rows, chunk_index))
            chunk_index += 1

    fieldnames = [
        "chunk_id",
        "category",
        "category_en",
        "semantic_group",
        "qa_ids",
        "source_row_numbers",
        "qa_records",
        "row_count",
        "char_count",
        "normalized_char_count",
        "oversized",
        "oversized_single_row_chunk",
        "top_weak_medical_hints",
        "weak_hints_by_type",
        "chunk_text",
        "normalized_chunk_text",
    ]

    with CHUNKS_CSV.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(chunks)

    with CHUNKS_JSONL.open("w", encoding="utf-8") as handle:
        for chunk in chunks:
            jsonl_chunk = dict(chunk)
            jsonl_chunk["qa_records"] = json.loads(chunk["qa_records"])
            handle.write(json.dumps(jsonl_chunk, ensure_ascii=False) + "\n")

    row_counts = [int(chunk["row_count"]) for chunk in chunks]
    char_counts = [int(chunk["char_count"]) for chunk in chunks]
    oversized_single_row_chunks = [
        chunk
        for chunk in chunks
        if chunk["oversized_single_row_chunk"]
    ]
    oversized_chunks = [chunk for chunk in chunks if chunk["oversized"]]
    semantic_groups = {chunk["semantic_group"] for chunk in chunks}
    categories = {chunk["category"] for chunk in chunks}
    category_chunk_counts = Counter(chunk["category_en"] or chunk["category"] for chunk in chunks)
    semantic_chunk_counts = Counter(chunk["semantic_group"] for chunk in chunks)

    report = {
        "input_csv": relpath(INPUT_CSV),
        "chunks_csv": relpath(CHUNKS_CSV),
        "chunks_jsonl": relpath(CHUNKS_JSONL),
        "input_rows": len(all_rows),
        "graph_train_rows": len(rows),
        "output_chunks": len(chunks),
        "categories": len(categories),
        "semantic_groups": len(semantic_groups),
        "max_rows_per_chunk_setting": MAX_ROWS_PER_CHUNK,
        "max_chars_per_chunk_setting": MAX_CHARS_PER_CHUNK,
        "avg_rows_per_chunk": round(sum(row_counts) / len(row_counts), 2) if row_counts else 0,
        "max_rows_per_chunk": max(row_counts) if row_counts else 0,
        "min_rows_per_chunk": min(row_counts) if row_counts else 0,
        "avg_chars_per_chunk": round(sum(char_counts) / len(char_counts), 2) if char_counts else 0,
        "max_chars_per_chunk": max(char_counts) if char_counts else 0,
        "oversized_chunks": len(oversized_chunks),
        "oversized_single_row_chunks": len(oversized_single_row_chunks),
        "top_categories_by_chunks": [
            {"category_en": category, "chunks": count}
            for category, count in category_chunk_counts.most_common(15)
        ],
        "top_semantic_groups_by_chunks": [
            {"semantic_group": group, "chunks": count}
            for group, count in semantic_chunk_counts.most_common(15)
        ],
    }

    write_markdown_report(report, chunks[:5])
    print(json.dumps(report, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
