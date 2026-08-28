import argparse
import csv
import json
import random
import re
from collections import Counter, defaultdict
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent
REPO_ROOT = BASE_DIR
OUTPUT_DIR = BASE_DIR / "outputs" / "01_preprocessing"
REPORTS_DIR = BASE_DIR / "reports"

DEFAULT_INPUT_CSV = REPO_ROOT / "data" / "raw" / "AHD.csv"
DEFAULT_EXISTING_GRAPH_CSV = (
    BASE_DIR
    / "outputs"
    / "final_graph"
    / "provenance"
    / "qa_records_source_5000.csv"
)
DEFAULT_EVALUATION_CSV = (
    REPO_ROOT
    / "data"
    / "evaluation"
    / "retrieval_gold_annotations_100.csv"
)

DEFAULT_TARGET_ROWS = 10000
DEFAULT_RANDOM_SEED = 20260731
DEFAULT_OUTPUT_TAG = "graph_build"
DEFAULT_SUBSET_PREFIX = "ahd"


URL_RE = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w.-]+\.\w+\b")
WHITESPACE_RE = re.compile(r"\s+")
TATWEEL_RE = re.compile("\u0640+")
ARABIC_DIACRITICS_RE = re.compile(r"[\u064b-\u065f\u0670\u06d6-\u06ed]")
PUNCT_SPACE_RE = re.compile(r"[^\w\u0600-\u06ff]+", re.UNICODE)
ARABIC_DIGITS = str.maketrans(
    "\u0660\u0661\u0662\u0663\u0664\u0665\u0666\u0667\u0668\u0669"
    "\u06f0\u06f1\u06f2\u06f3\u06f4\u06f5\u06f6\u06f7\u06f8\u06f9",
    "01234567890123456789",
)
ARABIC_LETTER_NORMALIZATION = str.maketrans(
    {
        "\u0623": "\u0627",
        "\u0625": "\u0627",
        "\u0622": "\u0627",
        "\u0671": "\u0627",
        "\u0649": "\u064a",
        "\u0626": "\u064a",
        "\u0624": "\u0648",
        "\u0629": "\u0647",
    }
)


def clean_text(value):
    if value is None:
        return ""
    value = str(value).replace("\ufeff", "")
    value = URL_RE.sub(" ", value)
    value = EMAIL_RE.sub(" ", value)
    value = TATWEEL_RE.sub("", value)
    value = WHITESPACE_RE.sub(" ", value)
    return value.strip()


def normalize_for_dedupe(value):
    value = clean_text(value)
    value = value.translate(ARABIC_DIGITS)
    value = TATWEEL_RE.sub("", value)
    value = ARABIC_DIACRITICS_RE.sub("", value)
    value = value.translate(ARABIC_LETTER_NORMALIZATION)
    value = PUNCT_SPACE_RE.sub(" ", value)
    value = WHITESPACE_RE.sub(" ", value)
    return value.strip().lower()


def relpath(path):
    try:
        return path.resolve().relative_to(BASE_DIR.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def safe_tag(value):
    tag = re.sub(r"[^A-Za-z0-9_-]+", "_", str(value or "").strip())
    return tag.strip("_") or DEFAULT_OUTPUT_TAG


def parse_source_row_number(value):
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def load_existing_graph_exclusions(path):
    source_rows = set()
    normalized_qa_pairs = set()

    if not path.exists():
        raise FileNotFoundError(f"Existing graph provenance file not found: {path}")

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            source_row_number = parse_source_row_number(row.get("source_row_number"))
            if source_row_number is not None:
                source_rows.add(source_row_number)

            question_norm = normalize_for_dedupe(row.get("question"))
            answer_norm = normalize_for_dedupe(row.get("answer"))
            if question_norm and answer_norm:
                normalized_qa_pairs.add((question_norm, answer_norm))

    return source_rows, normalized_qa_pairs


def load_evaluation_exclusions(path):
    normalized_queries = set()
    normalized_query_answer_pairs = set()

    if not path.exists():
        raise FileNotFoundError(f"Evaluation file not found: {path}")

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            query_norm = normalize_for_dedupe(row.get("query"))
            answer_norm = normalize_for_dedupe(row.get("reference_answer"))

            if query_norm:
                normalized_queries.add(query_norm)
            if query_norm and answer_norm:
                normalized_query_answer_pairs.add((query_norm, answer_norm))

    return normalized_queries, normalized_query_answer_pairs


def balanced_sample(rows_by_category, target_rows, seed):
    rng = random.Random(seed)
    categories = sorted(rows_by_category)
    selected = []

    for category_rows in rows_by_category.values():
        rng.shuffle(category_rows)

    base_quota = max(1, target_rows // max(1, len(categories)))
    leftovers = []

    for category in categories:
        category_rows = rows_by_category[category]
        take = min(base_quota, len(category_rows))
        selected.extend(category_rows[:take])
        leftovers.extend(category_rows[take:])

    if len(selected) < target_rows:
        rng.shuffle(leftovers)
        selected.extend(leftovers[: target_rows - len(selected)])

    selected = selected[:target_rows]
    rng.shuffle(selected)
    return selected


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Prepare an AHD graph-construction subset while excluding existing "
            "graph rows and held-out evaluation questions."
        )
    )
    parser.add_argument("--input-csv", type=Path, default=DEFAULT_INPUT_CSV)
    parser.add_argument(
        "--existing-graph-csv",
        type=Path,
        default=DEFAULT_EXISTING_GRAPH_CSV,
    )
    parser.add_argument(
        "--evaluation-csv",
        type=Path,
        default=DEFAULT_EVALUATION_CSV,
    )
    parser.add_argument("--target-rows", type=int, default=DEFAULT_TARGET_ROWS)
    parser.add_argument("--seed", type=int, default=DEFAULT_RANDOM_SEED)
    parser.add_argument("--output-tag", default=DEFAULT_OUTPUT_TAG)
    parser.add_argument("--subset-prefix", default=DEFAULT_SUBSET_PREFIX)
    parser.add_argument(
        "--force-overwrite",
        action="store_true",
        help="Allow overwriting outputs with the same output tag.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    input_csv = args.input_csv.resolve()
    existing_graph_csv = args.existing_graph_csv.resolve()
    evaluation_csv = args.evaluation_csv.resolve()
    output_tag = safe_tag(args.output_tag)
    subset_prefix = safe_tag(args.subset_prefix)

    if args.target_rows <= 0:
        raise ValueError("--target-rows must be greater than zero.")

    output_csv = OUTPUT_DIR / f"ahd_subset_{args.target_rows}_clean_{output_tag}.csv"
    distribution_csv = (
        OUTPUT_DIR
        / f"ahd_subset_{args.target_rows}_category_distribution_{output_tag}.csv"
    )
    report_json = REPORTS_DIR / f"ahd_subset_sampling_report_{output_tag}.json"

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    output_paths = [output_csv, distribution_csv, report_json]
    existing_outputs = [path for path in output_paths if path.exists()]
    if existing_outputs and not args.force_overwrite:
        formatted = "\n".join(f"- {path}" for path in existing_outputs)
        raise FileExistsError(
            "Graph-construction outputs already exist. Use another --output-tag or "
            f"--force-overwrite:\n{formatted}"
        )

    if not input_csv.exists():
        raise FileNotFoundError(f"AHD input CSV not found: {input_csv}")

    existing_source_rows, existing_graph_qa_pairs = load_existing_graph_exclusions(
        existing_graph_csv
    )
    evaluation_queries, evaluation_query_answer_pairs = load_evaluation_exclusions(
        evaluation_csv
    )

    rows_by_category = defaultdict(list)
    raw_rows = 0
    skipped_empty = 0
    skipped_existing_source_row = 0
    skipped_existing_normalized_qa = 0
    skipped_evaluation_query = 0
    skipped_evaluation_query_answer = 0
    skipped_duplicate = 0
    skipped_normalized_duplicate = 0

    seen_pairs = set()
    seen_normalized_pairs = set()

    with input_csv.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)

        required_columns = {"Question", "Answer", "Category"}
        missing_columns = required_columns - set(reader.fieldnames or [])
        if missing_columns:
            raise ValueError(
                f"AHD input is missing required columns: {sorted(missing_columns)}"
            )

        for source_row_number, row in enumerate(reader, start=2):
            raw_rows += 1

            question = clean_text(row.get("Question"))
            answer = clean_text(row.get("Answer"))
            category = clean_text(row.get("Category"))

            if not question or not answer or not category:
                skipped_empty += 1
                continue

            question_norm = normalize_for_dedupe(question)
            answer_norm = normalize_for_dedupe(answer)
            category_norm = normalize_for_dedupe(category)
            normalized_qa_pair = (question_norm, answer_norm)

            # Primary provenance-safe exclusion.
            if source_row_number in existing_source_rows:
                skipped_existing_source_row += 1
                continue

            # Secondary guard in case line numbering changes in a future AHD copy.
            if normalized_qa_pair in existing_graph_qa_pairs:
                skipped_existing_normalized_qa += 1
                continue

            if normalized_qa_pair in evaluation_query_answer_pairs:
                skipped_evaluation_query_answer += 1
                continue

            # Held-out evaluation queries must not enter graph construction.
            if question_norm in evaluation_queries:
                skipped_evaluation_query += 1
                continue

            dedupe_key = (question, answer, category)
            if dedupe_key in seen_pairs:
                skipped_duplicate += 1
                continue
            seen_pairs.add(dedupe_key)

            normalized_dedupe_key = (
                question_norm,
                answer_norm,
                category_norm,
            )
            if normalized_dedupe_key in seen_normalized_pairs:
                skipped_normalized_duplicate += 1
                continue
            seen_normalized_pairs.add(normalized_dedupe_key)

            rows_by_category[category].append(
                {
                    "source_row_number": source_row_number,
                    "question": question,
                    "answer": answer,
                    "category": category,
                    "qa_text": f"السؤال: {question}\nالإجابة: {answer}",
                }
            )

    clean_rows_available = sum(len(rows) for rows in rows_by_category.values())
    if clean_rows_available < args.target_rows:
        raise RuntimeError(
            f"Only {clean_rows_available} eligible rows remain after exclusions; "
            f"cannot sample {args.target_rows}."
        )

    selected = balanced_sample(rows_by_category, args.target_rows, args.seed)
    for idx, row in enumerate(selected, start=1):
        row["subset_id"] = f"{subset_prefix}_{idx:05d}"

    fieldnames = [
        "subset_id",
        "source_row_number",
        "category",
        "question",
        "answer",
        "qa_text",
    ]
    with output_csv.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(selected)

    subset_counts = Counter(row["category"] for row in selected)
    source_counts = {
        category: len(rows) for category, rows in rows_by_category.items()
    }

    with distribution_csv.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["category", "subset_rows", "eligible_source_rows"],
        )
        writer.writeheader()
        for category, count in sorted(
            subset_counts.items(),
            key=lambda item: (-item[1], item[0]),
        ):
            writer.writerow(
                {
                    "category": category,
                    "subset_rows": count,
                    "eligible_source_rows": source_counts[category],
                }
            )

    selected_source_rows = {row["source_row_number"] for row in selected}
    selected_normalized_qa_pairs = {
        (
            normalize_for_dedupe(row["question"]),
            normalize_for_dedupe(row["answer"]),
        )
        for row in selected
    }
    selected_normalized_questions = {
        normalize_for_dedupe(row["question"]) for row in selected
    }

    overlap_checks = {
        "selected_existing_source_row_overlap": len(
            selected_source_rows & existing_source_rows
        ),
        "selected_existing_normalized_qa_overlap": len(
            selected_normalized_qa_pairs & existing_graph_qa_pairs
        ),
        "selected_evaluation_query_overlap": len(
            selected_normalized_questions & evaluation_queries
        ),
        "selected_evaluation_query_answer_overlap": len(
            selected_normalized_qa_pairs & evaluation_query_answer_pairs
        ),
    }

    report = {
        "input_csv": relpath(input_csv),
        "existing_graph_csv": relpath(existing_graph_csv),
        "evaluation_csv": relpath(evaluation_csv),
        "output_csv": relpath(output_csv),
        "distribution_csv": relpath(distribution_csv),
        "target_rows": args.target_rows,
        "actual_rows": len(selected),
        "random_seed": args.seed,
        "output_tag": output_tag,
        "subset_prefix": subset_prefix,
        "raw_rows_seen": raw_rows,
        "clean_rows_available_after_exclusions_and_deduplication": clean_rows_available,
        "categories_available": len(source_counts),
        "categories_in_subset": len(subset_counts),
        "loaded_existing_graph_source_rows": len(existing_source_rows),
        "loaded_existing_graph_normalized_qa_pairs": len(existing_graph_qa_pairs),
        "loaded_evaluation_queries": len(evaluation_queries),
        "loaded_evaluation_query_answer_pairs": len(
            evaluation_query_answer_pairs
        ),
        "skipped_empty_question_answer_or_category": skipped_empty,
        "skipped_existing_graph_source_row": skipped_existing_source_row,
        "skipped_existing_graph_normalized_qa_guard": skipped_existing_normalized_qa,
        "skipped_evaluation_query_answer_pair": skipped_evaluation_query_answer,
        "skipped_evaluation_question": skipped_evaluation_query,
        "skipped_exact_duplicates": skipped_duplicate,
        "skipped_normalized_duplicates": skipped_normalized_duplicate,
        "sampling_method": (
            "balanced by category: equal base quota per category, then random "
            "fill from remaining eligible clean rows"
        ),
        "overlap_checks": overlap_checks,
        "top_subset_categories": [
            {"category": category, "rows": count}
            for category, count in subset_counts.most_common(15)
        ],
    }

    with report_json.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)

    print(json.dumps(report, ensure_ascii=False, indent=2))

    if any(overlap_checks.values()):
        raise RuntimeError(
            "Safety verification failed: the selected subset overlaps an "
            "exclusion source. Inspect the report before continuing."
        )


if __name__ == "__main__":
    main()
