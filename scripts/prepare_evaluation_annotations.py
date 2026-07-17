from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.config import load_final_config
from src.neo4j_repository import Neo4jRepository


ROOT = Path(__file__).resolve().parents[1]
SOURCE_CSV = ROOT / "outputs" / "final_graph" / "provenance" / "qa_records_source_5000.csv"
RETRIEVAL_ANNOTATIONS_CSV = ROOT / "data" / "evaluation" / "retrieval_gold_annotations_100.csv"
CLAIM_ANNOTATIONS_CSV = ROOT / "data" / "evaluation" / "human_claim_annotations_100.csv"

RETRIEVAL_COLUMNS = (
    "query_id",
    "query",
    "query_group",
    "reference_answer",
    "gold_entity_ids",
    "gold_evidence_ids",
    "gold_qa_ids",
    "gold_relation_ids",
    "answerable_from_final_graph",
    "annotation_status",
    "annotator_id",
    "adjudicator_id",
    "annotation_notes",
)

CLAIM_COLUMNS = (
    "query_id",
    "mode",
    "claim_id",
    "claim_text",
    "response_text",
    "cited_evidence_ids",
    "cited_qa_ids",
    "human_support_label",
    "human_citation_valid",
    "human_medical_correctness",
    "human_hallucination_label",
    "harm_severity",
    "annotator_id",
    "annotation_timestamp_utc",
    "adjudication_status",
    "adjudicator_id",
    "annotation_notes",
)

GROUP_PATTERNS = (
    ("treatment", re.compile(r"(?:علاج|دواء|ادويه|أدوية|جرعه|جرعة|استخدم|استعمل)")),
    ("symptoms", re.compile(r"(?:اعراض|أعراض|علامات|الم|ألم|دوخه|دوخة|سعال|صداع|حراره|حرارة)")),
    ("tests_diagnosis", re.compile(r"(?:تحليل|تحاليل|فحص|اشعه|أشعة|تشخيص|منظار)")),
    ("causes_safety", re.compile(r"(?:سبب|اسباب|أسباب|لماذا|هل.*بسبب|خطر|اضرار|أضرار|آمن|امن)")),
)

EXCLUDED_TEXT = re.compile(
    r"(?:@|https?://|www\.|ارسل صورة|أرسل صورة|ابعث صورة|بعث السؤال باللغة|svp|aid moi)",
    re.IGNORECASE,
)
ARABIC_RE = re.compile(r"[\u0600-\u06ff]")


def stable_rank(value: str) -> str:
    return hashlib.sha256(f"evaluation-v1|{value}".encode("utf-8")).hexdigest()


def query_group(question_norm: str) -> str:
    for group, pattern in GROUP_PATTERNS:
        if pattern.search(question_norm):
            return group
    return "general_medical"


def is_usable(row: dict[str, str], final_qa_ids: set[str]) -> bool:
    question = str(row.get("question") or "").strip()
    answer = str(row.get("answer") or "").strip()
    source_id = str(row.get("subset_id") or "").strip()
    if row.get("split") != "eval_test" or source_id in final_qa_ids:
        return False
    if not (20 <= len(question) <= 350 and 80 <= len(answer) <= 1500):
        return False
    if EXCLUDED_TEXT.search(question) or EXCLUDED_TEXT.search(answer):
        return False
    arabic_count = len(ARABIC_RE.findall(question))
    visible_count = sum(not character.isspace() for character in question)
    return visible_count > 0 and arabic_count / visible_count >= 0.45


def select_rows(rows: list[dict[str, str]], final_qa_ids: set[str], query_count: int) -> list[dict[str, str]]:
    candidates = [row for row in rows if is_usable(row, final_qa_ids)]
    grouped: dict[str, list[dict[str, str]]] = {
        group: []
        for group in ("treatment", "symptoms", "tests_diagnosis", "causes_safety", "general_medical")
    }
    for row in candidates:
        grouped[query_group(str(row.get("question_norm") or ""))].append(row)
    for group_rows in grouped.values():
        group_rows.sort(key=lambda row: stable_rank(str(row.get("subset_id") or "")))

    selected: list[dict[str, str]] = []
    group_names = list(grouped)
    while len(selected) < query_count:
        progressed = False
        for group in group_names:
            if grouped[group] and len(selected) < query_count:
                selected.append(grouped[group].pop(0))
                progressed = True
        if not progressed:
            break
    if len(selected) < query_count:
        raise RuntimeError(
            f"Only {len(selected)} eligible held-out queries remain after leakage and quality filters."
        )
    return selected


def retrieval_annotation_rows(selected: list[dict[str, str]]) -> list[dict[str, str]]:
    output = []
    for index, row in enumerate(selected, start=1):
        source_id = str(row.get("subset_id") or "")
        notes = "; ".join(
            [
                "pending independent human relevance annotation",
                f"source_split={row.get('split', '')}",
                f"source_qa_id={source_id}",
                f"source_row_number={row.get('source_row_number', '')}",
                f"source_category={row.get('category', '')}",
                "direct_qa_id_present_in_final_graph=false",
            ]
        )
        output.append(
            {
                "query_id": f"evalv1_{index:03d}",
                "query": str(row.get("question") or "").strip(),
                "query_group": query_group(str(row.get("question_norm") or "")),
                "reference_answer": str(row.get("answer") or "").strip(),
                "gold_entity_ids": "",
                "gold_evidence_ids": "",
                "gold_qa_ids": "",
                "gold_relation_ids": "",
                "answerable_from_final_graph": "",
                "annotation_status": "pending_human_annotation",
                "annotator_id": "",
                "adjudicator_id": "",
                "annotation_notes": notes,
            }
        )
    return output


def write_csv_exclusive(path: Path, columns: tuple[str, ...], rows: list[dict[str, str]]) -> None:
    if path.exists():
        raise FileExistsError(f"Refusing to overwrite annotation file: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare independent human annotation work queues.")
    parser.add_argument("--query-count", type=int, default=40)
    parser.add_argument("--retrieval-file", type=Path, default=RETRIEVAL_ANNOTATIONS_CSV)
    parser.add_argument("--claim-file", type=Path, default=CLAIM_ANNOTATIONS_CSV)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if args.query_count <= 0:
        raise ValueError("query-count must be positive.")
    with SOURCE_CSV.open("r", encoding="utf-8-sig", newline="") as handle:
        source_rows = list(csv.DictReader(handle))
    config = load_final_config()
    if config.graph_version != "final_v1":
        raise RuntimeError("Annotation preparation is restricted to final_v1.")
    with Neo4jRepository(config=config) as repository:
        qa_rows = repository._execute_read(
            """
MATCH (qa:QARecord {graph_version: $graph_version})
RETURN qa.qa_id AS qa_id
""".strip(),
            {"graph_version": config.graph_version},
        )
    final_qa_ids = {str(row.get("qa_id") or "") for row in qa_rows}
    selected = select_rows(source_rows, final_qa_ids, args.query_count)
    rows = retrieval_annotation_rows(selected)
    summary = {
        "status": "ready" if args.execute else "dry_run",
        "query_count": len(rows),
        "groups": {
            group: sum(row["query_group"] == group for row in rows)
            for group in sorted({row["query_group"] for row in rows})
        },
        "source_split": "eval_test",
        "direct_final_qa_overlap": 0,
        "labels_created": False,
        "label_status": "pending_human_annotation",
    }
    if args.execute:
        retrieval_file = args.retrieval_file.resolve()
        claim_file = args.claim_file.resolve()
        write_csv_exclusive(retrieval_file, RETRIEVAL_COLUMNS, rows)
        write_csv_exclusive(claim_file, CLAIM_COLUMNS, [])
        summary["retrieval_annotations"] = str(retrieval_file)
        summary["claim_annotations"] = str(claim_file)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
