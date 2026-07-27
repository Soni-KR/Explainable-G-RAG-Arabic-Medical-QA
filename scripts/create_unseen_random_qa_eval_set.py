from __future__ import annotations

import argparse
import csv
import random
import re
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOKEN_RE = re.compile(r"[\w\u0600-\u06ff]+", re.UNICODE)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def normalize_text(value: str) -> str:
    value = str(value or "").strip()
    value = re.sub(r"[\u064b-\u0652\u0670]", "", value)
    value = value.translate(str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ى": "ي", "ة": "ه"}))
    return " ".join(TOKEN_RE.findall(value.lower()))


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a stratified unseen AHD QA evaluation set.")
    parser.add_argument("--ahd-csv", default="AHD.csv")
    parser.add_argument(
        "--exclude-csv",
        action="append",
        default=["retrieval_gold_annotations_100.csv"],
        help="CSV file containing questions to exclude. Can be repeated.",
    )
    parser.add_argument("--exclude-query-col", default="query")
    parser.add_argument("--output-csv", default="retrieval_gold_annotations_unseen_100_random.csv")
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--seed", type=int, default=20260726)
    parser.add_argument("--min-question-chars", type=int, default=20)
    parser.add_argument("--min-answer-chars", type=int, default=20)
    args = parser.parse_args()

    ahd_path = ROOT / args.ahd_csv
    output_path = ROOT / args.output_csv

    excluded_questions = set()
    for exclude_csv in args.exclude_csv:
        exclude_path = ROOT / exclude_csv
        if not exclude_path.exists():
            continue
        for row in read_csv(exclude_path):
            normalized = normalize_text(row.get(args.exclude_query_col, ""))
            if normalized:
                excluded_questions.add(normalized)

    by_category: dict[str, list[tuple[int, dict[str, str]]]] = defaultdict(list)
    seen_questions = set(excluded_questions)
    for idx, row in enumerate(read_csv(ahd_path), start=1):
        question = row.get("Question", "").strip()
        answer = row.get("Answer", "").strip()
        category = row.get("Category", "").strip() or "Uncategorized"
        normalized = normalize_text(question)
        if not normalized or normalized in seen_questions:
            continue
        if len(question) < args.min_question_chars or len(answer) < args.min_answer_chars:
            continue
        seen_questions.add(normalized)
        by_category[category].append((idx, row))

    rng = random.Random(args.seed)
    categories = [category for category, rows in by_category.items() if rows]
    rng.shuffle(categories)
    if not categories:
        raise RuntimeError("No eligible AHD rows found after exclusions.")

    selected: list[tuple[int, dict[str, str]]] = []
    category_cursor = 0
    while len(selected) < args.limit and categories:
        category = categories[category_cursor % len(categories)]
        bucket = by_category[category]
        if bucket:
            choice_index = rng.randrange(len(bucket))
            selected.append(bucket.pop(choice_index))
        if not bucket:
            categories.remove(category)
            if not categories:
                break
            category_cursor %= len(categories)
        else:
            category_cursor += 1

    if len(selected) < args.limit:
        raise RuntimeError(f"Only selected {len(selected)} rows; requested {args.limit}.")

    output_rows = []
    for sample_number, (ahd_row_index, row) in enumerate(selected, start=1):
        output_rows.append(
            {
                "query_id": f"unseen100_{sample_number:03d}",
                "query": row.get("Question", "").strip(),
                "query_group": "unseen_random_stratified_100",
                "reference_answer": row.get("Answer", "").strip(),
                "category": row.get("Category", "").strip(),
                "ahd_row_index": str(ahd_row_index),
                "sampling_seed": str(args.seed),
                "annotation_status": "source_answer_reference_not_human_adjudicated",
            }
        )

    write_csv(output_path, output_rows)
    category_count = len({row["category"] for row in output_rows})
    print(
        {
            "output_csv": str(output_path.relative_to(ROOT)),
            "rows": len(output_rows),
            "categories": category_count,
            "excluded_existing_questions": len(excluded_questions),
            "seed": args.seed,
        }
    )


if __name__ == "__main__":
    main()
