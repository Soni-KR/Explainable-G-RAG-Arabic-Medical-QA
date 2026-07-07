import csv
import json
import random
import re
from collections import Counter, defaultdict
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent if SCRIPT_DIR.name == "scripts" else SCRIPT_DIR
OUTPUT_DIR = BASE_DIR / "outputs" / "01_preprocessing"
REPORTS_DIR = BASE_DIR / "reports"

INPUT_CSV = BASE_DIR / "AHD.csv"
OUTPUT_CSV = OUTPUT_DIR / "ahd_subset_5000_clean.csv"
DISTRIBUTION_CSV = OUTPUT_DIR / "ahd_subset_5000_category_distribution.csv"
REPORT_JSON = REPORTS_DIR / "ahd_subset_sampling_report.json"

TARGET_ROWS = 5000
RANDOM_SEED = 42


URL_RE = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w.-]+\.\w+\b")
WHITESPACE_RE = re.compile(r"\s+")
TATWEEL_RE = re.compile("\u0640+")
ARABIC_DIACRITICS_RE = re.compile(r"[\u064b-\u065f\u0670\u06d6-\u06ed]")
PUNCT_SPACE_RE = re.compile(r"[^\w\u0600-\u06ff]+", re.UNICODE)
ARABIC_DIGITS = str.maketrans("\u0660\u0661\u0662\u0663\u0664\u0665\u0666\u0667\u0668\u0669\u06f0\u06f1\u06f2\u06f3\u06f4\u06f5\u06f6\u06f7\u06f8\u06f9", "01234567890123456789")
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
    return path.relative_to(BASE_DIR).as_posix()


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


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    rows_by_category = defaultdict(list)
    raw_rows = 0
    skipped_empty = 0
    skipped_duplicate = 0
    skipped_normalized_duplicate = 0
    seen_pairs = set()
    seen_normalized_pairs = set()

    with INPUT_CSV.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for source_row_number, row in enumerate(reader, start=2):
            raw_rows += 1
            question = clean_text(row.get("Question"))
            answer = clean_text(row.get("Answer"))
            category = clean_text(row.get("Category"))

            if not question or not answer or not category:
                skipped_empty += 1
                continue

            dedupe_key = (question, answer, category)
            if dedupe_key in seen_pairs:
                skipped_duplicate += 1
                continue
            seen_pairs.add(dedupe_key)

            normalized_dedupe_key = (
                normalize_for_dedupe(question),
                normalize_for_dedupe(answer),
                normalize_for_dedupe(category),
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

    selected = balanced_sample(rows_by_category, TARGET_ROWS, RANDOM_SEED)
    for idx, row in enumerate(selected, start=1):
        row["subset_id"] = f"ahd5k_{idx:05d}"

    fieldnames = ["subset_id", "source_row_number", "category", "question", "answer", "qa_text"]
    with OUTPUT_CSV.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(selected)

    subset_counts = Counter(row["category"] for row in selected)
    source_counts = {category: len(rows) for category, rows in rows_by_category.items()}

    with DISTRIBUTION_CSV.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["category", "subset_rows", "clean_source_rows"])
        writer.writeheader()
        for category, count in sorted(subset_counts.items(), key=lambda item: (-item[1], item[0])):
            writer.writerow(
                {
                    "category": category,
                    "subset_rows": count,
                    "clean_source_rows": source_counts[category],
                }
            )

    report = {
        "input_csv": relpath(INPUT_CSV),
        "output_csv": relpath(OUTPUT_CSV),
        "distribution_csv": relpath(DISTRIBUTION_CSV),
        "target_rows": TARGET_ROWS,
        "actual_rows": len(selected),
        "random_seed": RANDOM_SEED,
        "raw_rows_seen": raw_rows,
        "clean_rows_available": sum(source_counts.values()),
        "categories_available": len(source_counts),
        "categories_in_subset": len(subset_counts),
        "skipped_empty_question_answer_or_category": skipped_empty,
        "skipped_exact_duplicates": skipped_duplicate,
        "skipped_normalized_duplicates": skipped_normalized_duplicate,
        "sampling_method": (
            "balanced by category: equal base quota per category, then random fill "
            "from remaining clean rows"
        ),
        "top_subset_categories": [
            {"category": category, "rows": count}
            for category, count in subset_counts.most_common(15)
        ],
    }

    with REPORT_JSON.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)

    print(json.dumps(report, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
