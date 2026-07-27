import argparse
import csv
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = ROOT / "outputs" / "03_entity_extraction" / "ensemble_first_100"

DEFAULT_SOURCES = {
    "original": ROOT / "llm_entities_vs_gt_100.csv",
    "llama_rank": ROOT
    / "outputs"
    / "03_entity_extraction"
    / "prompt_ablation_first_100"
    / "candidate_rank_v3_llama_3_3_70b"
    / "predictions.csv",
    "llama_anti": ROOT
    / "outputs"
    / "03_entity_extraction"
    / "prompt_ablation_first_100"
    / "anti_generic_v2_llama_3_3_70b"
    / "predictions.csv",
    "gpt_oss_120b": ROOT
    / "outputs"
    / "03_entity_extraction"
    / "prompt_ablation_first_100"
    / "anti_generic_v2_gpt_oss_120b"
    / "predictions.csv",
}

ENTITY_TYPES = {"DiseaseCondition", "Treatment", "Symptom", "Test"}
ARABIC_DIACRITICS_RE = re.compile(r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]")
NON_WORD_RE = re.compile(r"[^\w\s]", flags=re.UNICODE)
WHITESPACE_RE = re.compile(r"\s+")
ARABIC_CHARACTER_MAP = str.maketrans(
    {
        "أ": "ا",
        "إ": "ا",
        "آ": "ا",
        "ٱ": "ا",
        "ى": "ي",
        "ؤ": "و",
        "ئ": "ي",
    }
)

GENERIC_NAMES = {
    "الم",
    "ألم",
    "التهاب",
    "علاج",
    "دواء",
    "مرض",
    "حالة",
    "اعراض",
    "أعراض",
    "فحص",
    "تحليل",
}

TYPE_CUES = [
    ("Test", ["تحليل", "تحاليل", "فحص", "اختبار", "اشعة", "اشعه", "سونار", "رنين", "منظار", "قياس"]),
    (
        "Treatment",
        [
            "علاج",
            "دواء",
            "ادوية",
            "أدوية",
            "كريم",
            "مرهم",
            "بخاخ",
            "حقن",
            "ابرة",
            "إبرة",
            "عملية",
            "جراحة",
            "تمرين",
            "فيتامين",
            "مضاد",
        ],
    ),
    (
        "Symptom",
        [
            "الم",
            "ألم",
            "حكة",
            "دوخة",
            "نزيف",
            "انتفاخ",
            "ضيق",
            "غثيان",
            "سعال",
            "اسهال",
            "إسهال",
            "حرقة",
            "طنين",
        ],
    ),
    (
        "DiseaseCondition",
        [
            "التهاب",
            "حساسية",
            "سكري",
            "فقر دم",
            "حصى",
            "بواسير",
            "عدوى",
            "فطريات",
            "تكيس",
            "ورم",
        ],
    ),
]


def relpath(path):
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def normalize_arabic(text):
    text = unicodedata.normalize("NFKC", str(text or ""))
    text = text.replace("ـ", "")
    text = ARABIC_DIACRITICS_RE.sub("", text)
    text = text.translate(ARABIC_CHARACTER_MAP)
    text = NON_WORD_RE.sub(" ", text)
    return WHITESPACE_RE.sub(" ", text).strip().lower()


def tokens(text):
    return [token for token in normalize_arabic(text).split() if token]


def read_csv(path, limit):
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))[:limit]


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["question", "answer", "entity_type", "canonical_name"])
        writer.writeheader()
        writer.writerows(rows)


def is_generic(name):
    name_norm = normalize_arabic(name)
    generic_norms = {normalize_arabic(item) for item in GENERIC_NAMES}
    return name_norm in generic_norms or len(tokens(name_norm)) == 0


def cue_type(name):
    name_norm = normalize_arabic(name)
    matches = []
    for entity_type, cues in TYPE_CUES:
        if any(normalize_arabic(cue) in name_norm for cue in cues):
            matches.append(entity_type)
    return matches[0] if len(matches) == 1 else ""


def context_contains(row, name):
    if not name:
        return False
    context = normalize_arabic(f"{row['question']} {row['answer']}")
    return normalize_arabic(name) in context


def majority_type(candidates, fallback):
    votes = [item for item in candidates if item in ENTITY_TYPES]
    if not votes:
        return fallback
    counts = Counter(votes)
    best_type, best_count = counts.most_common(1)[0]
    if best_count >= 2:
        return best_type
    return fallback


def validate_alignment(reference_rows, sources):
    for name, rows in sources.items():
        if len(rows) != len(reference_rows):
            raise ValueError(f"{name} has {len(rows)} rows; expected {len(reference_rows)}")
        for index, (ref, row) in enumerate(zip(reference_rows, rows), start=1):
            if ref["question"].strip() != row["question"].strip():
                raise ValueError(f"Question mismatch for {name} at row {index}")
            if ref["answer"].strip() != row["answer"].strip():
                raise ValueError(f"Answer mismatch for {name} at row {index}")


def specific_context_switch(original, candidates):
    chosen_name = original["canonical_name"]
    if is_generic(original["canonical_name"]):
        for candidate in candidates:
            if not is_generic(candidate) and context_contains(original, candidate):
                chosen_name = candidate
                break
    return {
        "question": original["question"],
        "answer": original["answer"],
        "canonical_name": chosen_name,
        "entity_type": original["entity_type"],
    }


def choose_row(index, sources, strategy):
    original = sources["original"][index]
    llama_rank = sources["llama_rank"][index]
    llama_anti = sources["llama_anti"][index]
    gpt_oss_120b = sources["gpt_oss_120b"][index]

    if strategy == "llama_rank_name_original_type":
        return {
            "question": original["question"],
            "answer": original["answer"],
            "canonical_name": llama_rank["canonical_name"],
            "entity_type": original["entity_type"],
        }

    if strategy == "llama_rank_name_vote_type":
        chosen_type = majority_type(
            [
                original["entity_type"],
                llama_rank["entity_type"],
                llama_anti["entity_type"],
                gpt_oss_120b["entity_type"],
            ],
            original["entity_type"],
        )
        rule_type = cue_type(llama_rank["canonical_name"])
        if rule_type and chosen_type != original["entity_type"]:
            chosen_type = rule_type
        return {
            "question": original["question"],
            "answer": original["answer"],
            "canonical_name": llama_rank["canonical_name"],
            "entity_type": chosen_type,
        }

    if strategy == "specificity_switch_original_type":
        return specific_context_switch(
            original,
            [llama_rank["canonical_name"], llama_anti["canonical_name"], gpt_oss_120b["canonical_name"]],
        )

    if strategy == "specificity_switch_llama_only_original_type":
        return specific_context_switch(original, [llama_anti["canonical_name"], llama_rank["canonical_name"]])

    if strategy == "agreement_switch_original_type":
        chosen_name = original["canonical_name"]
        model_names = [llama_rank["canonical_name"], llama_anti["canonical_name"], gpt_oss_120b["canonical_name"]]
        normalized = [normalize_arabic(name) for name in model_names if name]
        if is_generic(original["canonical_name"]):
            counts = Counter(normalized)
            for name_norm, count in counts.most_common():
                if count >= 2:
                    for candidate in model_names:
                        if normalize_arabic(candidate) == name_norm and not is_generic(candidate):
                            chosen_name = candidate
                            break
                    break
        return {
            "question": original["question"],
            "answer": original["answer"],
            "canonical_name": chosen_name,
            "entity_type": original["entity_type"],
        }

    raise ValueError(f"Unknown strategy: {strategy}")


def parse_args():
    parser = argparse.ArgumentParser(description="Build first-100 entity extraction ensemble predictions.")
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument(
        "--strategy",
        choices=[
            "llama_rank_name_original_type",
            "llama_rank_name_vote_type",
            "specificity_switch_original_type",
            "specificity_switch_llama_only_original_type",
            "agreement_switch_original_type",
        ],
        required=True,
    )
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_ROOT)
    return parser.parse_args()


def main():
    args = parse_args()
    sources = {name: read_csv(path, args.limit) for name, path in DEFAULT_SOURCES.items()}
    if args.strategy in {"specificity_switch_llama_only_original_type", "llama_rank_name_original_type"}:
        sources["gpt_oss_120b"] = sources["original"]
    if args.strategy == "llama_rank_name_original_type":
        sources["llama_anti"] = sources["original"]
    validate_alignment(sources["original"], sources)
    rows = [choose_row(index, sources, args.strategy) for index in range(args.limit)]

    output_dir = args.output_dir / args.strategy
    predictions_csv = output_dir / "predictions.csv"
    write_csv(predictions_csv, rows)
    print(
        json.dumps(
            {
                "strategy": args.strategy,
                "rows": len(rows),
                "predictions_csv": relpath(predictions_csv),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
