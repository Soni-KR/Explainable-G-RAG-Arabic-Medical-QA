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

INPUT_CSV = OUTPUT_DIR / "ahd_subset_10000_clean.csv"
CATEGORY_TRANSLATIONS_CSV = BASE_DIR / "Distribution of Question and Answer per category.csv"
OUTPUT_CSV = OUTPUT_DIR / "ahd_subset_10000_preprocessed.csv"
TERMS_CSV = OUTPUT_DIR / "ahd_medical_normalization_terms.csv"
REPORT_MD = REPORTS_DIR / "ahd_preprocessing_report.md"

RANDOM_SEED = 42
SPLIT_TARGETS = {"graph_train": 4000, "validation": 500, "eval_test": 500}
VERY_LONG_ANSWER_CHAR_THRESHOLD = 2500

ARABIC_DIACRITICS_RE = re.compile(r"[\u064b-\u065f\u0670\u06d6-\u06ed]")
TATWEEL_RE = re.compile(r"\u0640+")
WHITESPACE_RE = re.compile(r"\s+")
REPEATED_PUNCT_RE = re.compile(r"([!?؟،,.;:])\1+")
URL_RE = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w.-]+\.\w+\b")

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
PUNCTUATION_NORMALIZATION = str.maketrans(
    {
        "؟": "?",
        "،": ",",
        "؛": ";",
        "“": '"',
        "”": '"',
        "‘": "'",
        "’": "'",
    }
)


# These are weak prompt/chunking hints, not final graph entities.
WEAK_MEDICAL_HINT_TERMS = [
    {"canonical": "داء السكري", "type": "disease", "variants": ["سكري", "السكري", "مرض السكر", "داء السكري", "سكر الدم"]},
    {"canonical": "ارتفاع ضغط الدم", "type": "disease", "variants": ["ضغط الدم", "ارتفاع الضغط", "ارتفاع ضغط الدم", "الضغط المرتفع", "الضغط"]},
    {"canonical": "انخفاض ضغط الدم", "type": "disease", "variants": ["انخفاض الضغط", "انخفاض ضغط الدم", "الضغط المنخفض"]},
    {"canonical": "التهاب", "type": "condition", "variants": ["التهاب", "التهابات", "ملتهب", "ملتهبة"]},
    {"canonical": "حساسية", "type": "condition", "variants": ["حساسية", "تحسس", "الحساسيه", "الحساسية"]},
    {"canonical": "ألم", "type": "symptom", "variants": ["ألم", "الم", "وجع", "اوجاع"]},
    {"canonical": "صداع", "type": "symptom", "variants": ["صداع", "الشقيقة", "الصداع", "الصداع النصفي"]},
    {"canonical": "حمى", "type": "symptom", "variants": ["حمى", "حرارة", "ارتفاع الحرارة", "سخونة"]},
    {"canonical": "غثيان", "type": "symptom", "variants": ["غثيان", "لعيان", "غثيان وقيء"]},
    {"canonical": "قيء", "type": "symptom", "variants": ["قيء", "استفراغ", "ترجيع", "تقيؤ"]},
    {"canonical": "إسهال", "type": "symptom", "variants": ["إسهال", "اسهال", "الاسهال"]},
    {"canonical": "إمساك", "type": "symptom", "variants": ["إمساك", "امساك", "الامساك"]},
    {"canonical": "دواء", "type": "treatment", "variants": ["دواء", "دوائي", "أدوية", "ادوية", "عقار", "حبوب"]},
    {"canonical": "مضاد حيوي", "type": "treatment", "variants": ["مضاد حيوي", "مضادات حيوية", "مضاد حيوى", "انتيبيوتيك"]},
    {"canonical": "جرعة", "type": "treatment", "variants": ["جرعة", "الجرعة", "جرعات"]},
    {"canonical": "تحليل مخبري", "type": "test", "variants": ["تحليل", "تحاليل", "فحص مخبري", "فحوصات", "اختبار"]},
    {"canonical": "تصوير بالرنين المغناطيسي", "type": "test", "variants": ["رنين مغناطيسي", "الرنين المغناطيسي", "mri", "MRI"]},
    {"canonical": "أشعة", "type": "test", "variants": ["أشعة", "اشعة", "تصوير", "صورة اشعة"]},
    {"canonical": "الحمل", "type": "condition", "variants": ["حمل", "الحمل", "حامل", "الولادة"]},
    {"canonical": "الدورة الشهرية", "type": "condition", "variants": ["الدورة الشهرية", "الدوره الشهريه", "الطمث", "الحيض"]},
    {"canonical": "تكيس المبايض", "type": "disease", "variants": ["تكيس المبايض", "تكيسات المبايض", "تكيس المبيض"]},
    {"canonical": "التهاب المسالك البولية", "type": "disease", "variants": ["التهاب المسالك", "التهاب المسالك البولية", "التهاب البول", "حرقان البول"]},
    {"canonical": "فقر الدم", "type": "disease", "variants": ["فقر الدم", "انيميا", "أنيميا", "نقص الدم"]},
    {"canonical": "القولون العصبي", "type": "disease", "variants": ["قولون عصبي", "القولون العصبي", "القولون"]},
    {"canonical": "اكتئاب", "type": "disease", "variants": ["اكتئاب", "الاكتئاب", "كآبة"]},
    {"canonical": "قلق", "type": "symptom", "variants": ["قلق", "القلق", "توتر", "خوف"]},
    {"canonical": "وسواس قهري", "type": "disease", "variants": ["وسواس", "وسواس قهري", "الوسواس القهري"]},
    {"canonical": "ربو", "type": "disease", "variants": ["ربو", "الربو", "حساسية الصدر"]},
    {"canonical": "القلب", "type": "anatomy", "variants": ["قلب", "القلب", "الشرايين"]},
    {"canonical": "الكلى", "type": "anatomy", "variants": ["كلية", "الكلى", "الكليه", "الكليتين"]},
    {"canonical": "الكبد", "type": "anatomy", "variants": ["كبد", "الكبد"]},
    {"canonical": "المعدة", "type": "anatomy", "variants": ["معدة", "المعدة", "المعده"]},
    {"canonical": "الجلد", "type": "anatomy", "variants": ["جلد", "الجلد", "البشرة", "البشره"]},
]


def relpath(path):
    return path.relative_to(BASE_DIR).as_posix()


def normalize_for_matching(value):
    if value is None:
        return ""
    text = str(value)
    text = URL_RE.sub(" ", text)
    text = EMAIL_RE.sub(" ", text)
    text = text.translate(ARABIC_DIGITS)
    text = TATWEEL_RE.sub("", text)
    text = ARABIC_DIACRITICS_RE.sub("", text)
    text = text.translate(ARABIC_LETTER_NORMALIZATION)
    text = text.translate(PUNCTUATION_NORMALIZATION)
    text = REPEATED_PUNCT_RE.sub(r"\1", text)
    text = WHITESPACE_RE.sub(" ", text)
    return text.strip().lower()


def average(values):
    return round(sum(values) / len(values), 2) if values else 0


def load_category_translations():
    translations = {}
    if not CATEGORY_TRANSLATIONS_CSV.exists():
        return translations
    with CATEGORY_TRANSLATIONS_CSV.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            category = row.get("Category", "").strip()
            english = row.get("English translation", "").strip()
            if category and english:
                translations[category] = english
    return translations


def assign_splits(rows):
    rng = random.Random(RANDOM_SEED)
    indexes_by_category = defaultdict(list)
    for row_index, row in enumerate(rows):
        indexes_by_category[row["category"]].append(row_index)

    for indexes in indexes_by_category.values():
        rng.shuffle(indexes)

    def allocate_counts(total_target, used_counts=None):
        used_counts = used_counts or {}
        allocations = {}
        remainders = []
        for category, indexes in indexes_by_category.items():
            capacity = len(indexes) - used_counts.get(category, 0)
            ideal = len(indexes) * total_target / max(1, len(rows))
            base = min(capacity, int(ideal))
            allocations[category] = base
            remainders.append((ideal - int(ideal), category))

        remaining = total_target - sum(allocations.values())
        for _, category in sorted(remainders, reverse=True):
            if remaining <= 0:
                break
            capacity = len(indexes_by_category[category]) - used_counts.get(category, 0)
            if allocations[category] < capacity:
                allocations[category] += 1
                remaining -= 1
        return allocations

    validation_counts = allocate_counts(SPLIT_TARGETS["validation"])
    eval_counts = allocate_counts(SPLIT_TARGETS["eval_test"], validation_counts)

    split_by_index = {}
    for category, indexes in indexes_by_category.items():
        validation_count = validation_counts.get(category, 0)
        eval_count = eval_counts.get(category, 0)
        validation_indexes = indexes[:validation_count]
        eval_indexes = indexes[validation_count : validation_count + eval_count]
        graph_train_indexes = indexes[validation_count + eval_count :]

        for row_index in validation_indexes:
            split_by_index[row_index] = "validation"
        for row_index in eval_indexes:
            split_by_index[row_index] = "eval_test"
        for row_index in graph_train_indexes:
            split_by_index[row_index] = "graph_train"
    return split_by_index


def build_hint_patterns():
    patterns = []
    for term in WEAK_MEDICAL_HINT_TERMS:
        variants = sorted(
            {normalize_for_matching(variant) for variant in term["variants"] if variant},
            key=len,
            reverse=True,
        )
        patterns.append(
            {
                **term,
                "normalized_variants": variants,
                "patterns": [
                    re.compile(r"(?<!\w)" + re.escape(variant) + r"(?!\w)", re.IGNORECASE)
                    for variant in variants
                ],
            }
        )
    return patterns


HINT_PATTERNS = build_hint_patterns()


def detect_weak_medical_hints(*texts):
    combined_text = " ".join(text for text in texts if text)
    hints = []
    for term in HINT_PATTERNS:
        matched_variant = None
        for pattern, variant in zip(term["patterns"], term["normalized_variants"]):
            if pattern.search(combined_text):
                matched_variant = variant
                break
        if matched_variant:
            hints.append(
                {
                    "canonical": term["canonical"],
                    "type": term["type"],
                    "matched_variant": matched_variant,
                    "hint_strength": "weak",
                    "final_graph_entity": False,
                }
            )
    return hints


def write_terms_dictionary():
    with TERMS_CSV.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["canonical", "type", "variants", "usage"])
        writer.writeheader()
        for term in WEAK_MEDICAL_HINT_TERMS:
            writer.writerow(
                {
                    "canonical": term["canonical"],
                    "type": term["type"],
                    "variants": " | ".join(term["variants"]),
                    "usage": "weak hint only; not a final graph entity",
                }
            )


def make_markdown_report(report, examples):
    lines = [
        "# AHD Step 1 Preprocessing and Medical Normalization",
        "",
        "## What was produced",
        "",
        f"- Input: `{report['input_csv']}`",
        f"- Output: `{report['output_csv']}`",
        f"- Medical weak-hint dictionary: `{report['terms_csv']}`",
        "",
        "## Processing performed",
        "",
        "1. Preserved the original cleaned Arabic `question` and `answer` columns from the 10k subset.",
        "2. Added `category_en` from the AHD category distribution file when a translation exists.",
        "3. Added normalized Arabic fields for matching: `question_norm`, `answer_norm`, and `qa_text_norm`.",
        "4. Removed Arabic diacritics and tatweel, normalized Arabic/Persian digits, standardized punctuation, and unified common Arabic letter variants.",
        "5. Added `split` for evaluation-safe separation: `graph_train`, `validation`, and `eval_test`.",
        "6. Added text length columns: `question_char_len`, `answer_char_len`, and `qa_char_len`.",
        "7. Added dictionary-based weak medical hints. These are not final graph entities; final entities must come from Step 3 LLM extraction.",
        "",
        "## Split Policy",
        "",
        "The split is stratified by category as much as possible. Use `graph_train` rows to build the graph. Use `validation` for prompt tuning and design checks. Keep `eval_test` held back for final evaluation so the system is not evaluated on the same rows used to build the graph.",
        "",
        "## Dictionary Hint Policy",
        "",
        "Dictionary hints are deliberately weak. Broad variants such as pressure, test, heart, colon, or pregnancy-related terms can be context-sensitive, so they should guide chunking and LLM prompts only, not become final graph nodes.",
        "",
        "## Summary",
        "",
        f"- Rows processed: {report['rows_processed']}",
        f"- Categories represented: {report['categories']}",
        f"- Rows with English category label: {report['rows_with_category_en']}",
        f"- Rows with at least one weak medical hint: {report['rows_with_weak_medical_hints']}",
        f"- Unique weak hint concepts: {report['unique_weak_hint_concepts']}",
        "",
        "## Split Counts",
        "",
        f"- graph_train: {report['split_counts'].get('graph_train', 0)}",
        f"- validation: {report['split_counts'].get('validation', 0)}",
        f"- eval_test: {report['split_counts'].get('eval_test', 0)}",
        "",
        "## Category Coverage By Split",
        "",
        f"- graph_train categories: {report['categories_by_split'].get('graph_train', 0)}",
        f"- validation categories: {report['categories_by_split'].get('validation', 0)}",
        f"- eval_test categories: {report['categories_by_split'].get('eval_test', 0)}",
        "",
        "## Length Statistics",
        "",
        f"- Average question length: {report['length_stats']['avg_question_char_len']} chars",
        f"- Average answer length: {report['length_stats']['avg_answer_char_len']} chars",
        f"- Average QA length: {report['length_stats']['avg_qa_char_len']} chars",
        f"- Max answer length: {report['length_stats']['max_answer_char_len']} chars",
        f"- Rows with answers over {VERY_LONG_ANSWER_CHAR_THRESHOLD} chars: {report['length_stats']['very_long_answer_rows']}",
        "",
        "## Example transformations",
        "",
    ]

    for index, example in enumerate(examples, start=1):
        lines.extend(
            [
                f"### Example {index}",
                "",
                f"- `subset_id`: `{example['subset_id']}`",
                f"- Split: {example['split']}",
                f"- Category: {example['category']} / {example.get('category_en') or 'N/A'}",
                f"- Original question: {example['question']}",
                f"- Normalized question: {example['question_norm']}",
                f"- Weak medical hints: {example['weak_medical_hints'] or '[]'}",
                "",
            ]
        )
    return "\n".join(lines)


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    category_translations = load_category_translations()
    write_terms_dictionary()

    output_rows = []
    hint_counter = Counter()
    type_counters = {
        "disease": Counter(),
        "symptom": Counter(),
        "treatment": Counter(),
        "test": Counter(),
        "anatomy": Counter(),
        "condition": Counter(),
    }

    with INPUT_CSV.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            question_norm = normalize_for_matching(row["question"])
            answer_norm = normalize_for_matching(row["answer"])
            qa_text_norm = f"السؤال: {question_norm}\nالإجابة: {answer_norm}"
            weak_hints = detect_weak_medical_hints(question_norm, answer_norm)

            for hint in weak_hints:
                hint_counter[hint["canonical"]] += 1
                type_counters.setdefault(hint["type"], Counter())[hint["canonical"]] += 1

            weak_hints_by_type = {}
            for hint_type in ["disease", "symptom", "treatment", "test", "anatomy", "condition"]:
                weak_hints_by_type[hint_type] = [
                    hint["canonical"] for hint in weak_hints if hint["type"] == hint_type
                ]

            question_char_len = len(row["question"])
            answer_char_len = len(row["answer"])
            output_rows.append(
                {
                    **row,
                    "category_en": category_translations.get(row["category"], ""),
                    "question_norm": question_norm,
                    "answer_norm": answer_norm,
                    "qa_text_norm": qa_text_norm,
                    "question_char_len": question_char_len,
                    "answer_char_len": answer_char_len,
                    "qa_char_len": question_char_len + answer_char_len,
                    "weak_medical_hints": json.dumps(weak_hints, ensure_ascii=False),
                    "weak_hint_diseases": json.dumps(weak_hints_by_type["disease"], ensure_ascii=False),
                    "weak_hint_symptoms": json.dumps(weak_hints_by_type["symptom"], ensure_ascii=False),
                    "weak_hint_treatments": json.dumps(weak_hints_by_type["treatment"], ensure_ascii=False),
                    "weak_hint_tests": json.dumps(weak_hints_by_type["test"], ensure_ascii=False),
                    "weak_hint_anatomy": json.dumps(weak_hints_by_type["anatomy"], ensure_ascii=False),
                    "weak_hint_conditions": json.dumps(weak_hints_by_type["condition"], ensure_ascii=False),
                }
            )

    split_by_index = assign_splits(output_rows)
    for row_index, row in enumerate(output_rows):
        row["split"] = split_by_index[row_index]

    fieldnames = [
        "subset_id",
        "source_row_number",
        "split",
        "category",
        "category_en",
        "question",
        "answer",
        "qa_text",
        "question_norm",
        "answer_norm",
        "qa_text_norm",
        "question_char_len",
        "answer_char_len",
        "qa_char_len",
        "weak_medical_hints",
        "weak_hint_diseases",
        "weak_hint_symptoms",
        "weak_hint_treatments",
        "weak_hint_tests",
        "weak_hint_anatomy",
        "weak_hint_conditions",
    ]

    with OUTPUT_CSV.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_rows)

    question_lengths = [row["question_char_len"] for row in output_rows]
    answer_lengths = [row["answer_char_len"] for row in output_rows]
    qa_lengths = [row["qa_char_len"] for row in output_rows]
    examples = [row for row in output_rows if row["weak_medical_hints"] != "[]"][:5]

    report = {
        "input_csv": relpath(INPUT_CSV),
        "output_csv": relpath(OUTPUT_CSV),
        "terms_csv": relpath(TERMS_CSV),
        "rows_processed": len(output_rows),
        "categories": len({row["category"] for row in output_rows}),
        "rows_with_category_en": sum(1 for row in output_rows if row["category_en"]),
        "split_counts": dict(Counter(row["split"] for row in output_rows)),
        "categories_by_split": {
            split: len({row["category"] for row in output_rows if row["split"] == split})
            for split in SPLIT_TARGETS
        },
        "rows_with_weak_medical_hints": sum(
            1 for row in output_rows if row["weak_medical_hints"] != "[]"
        ),
        "unique_weak_hint_concepts": len(hint_counter),
        "length_stats": {
            "avg_question_char_len": average(question_lengths),
            "avg_answer_char_len": average(answer_lengths),
            "avg_qa_char_len": average(qa_lengths),
            "max_question_char_len": max(question_lengths) if question_lengths else 0,
            "max_answer_char_len": max(answer_lengths) if answer_lengths else 0,
            "max_qa_char_len": max(qa_lengths) if qa_lengths else 0,
            "very_long_answer_threshold": VERY_LONG_ANSWER_CHAR_THRESHOLD,
            "very_long_answer_rows": sum(
                1 for length in answer_lengths if length > VERY_LONG_ANSWER_CHAR_THRESHOLD
            ),
        },
        "top_weak_hint_terms": [
            {"canonical": term, "rows": count}
            for term, count in hint_counter.most_common(20)
        ],
        "top_weak_hints_by_type": {
            hint_type: [
                {"canonical": term, "rows": count}
                for term, count in counter.most_common(10)
            ]
            for hint_type, counter in type_counters.items()
        },
    }

    REPORT_MD.write_text(make_markdown_report(report, examples), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
