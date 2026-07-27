import argparse
import csv
import json
import re
import unicodedata
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = ROOT / "outputs" / "03_entity_extraction" / "evaluation_first_100"
DEFAULT_REPORT_MD = ROOT / "reports" / "step03b_entity_extraction_first100_report.md"
DEFAULT_GRAPH_ENTITY_FILES = [
    ROOT / "outputs" / "final_graph" / "entities.csv",
    ROOT / "outputs" / "final_graph" / "entity_mentions.csv",
    ROOT / "outputs" / "05_trial_graph_v1" / "import" / "trial_graph_v1_entities.csv",
    ROOT / "outputs" / "05_trial_graph_v1" / "supplemental_facts" / "trial_graph_v1_supplemental_entities.csv",
]

ENTITY_TYPES = [
    "DiseaseCondition",
    "Treatment",
    "Symptom",
    "Test",
]

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


def relpath(path):
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def normalize_arabic(text):
    text = "" if text is None else str(text)
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("ـ", "")
    text = ARABIC_DIACRITICS_RE.sub("", text)
    text = text.translate(ARABIC_CHARACTER_MAP)
    text = NON_WORD_RE.sub(" ", text)
    return WHITESPACE_RE.sub(" ", text).strip().lower()


def tokenize(text):
    return [token for token in normalize_arabic(text).split() if token]


def token_f1(left, right):
    left_tokens = Counter(tokenize(left))
    right_tokens = Counter(tokenize(right))
    overlap = sum((left_tokens & right_tokens).values())
    precision = safe_divide(overlap, sum(right_tokens.values()))
    recall = safe_divide(overlap, sum(left_tokens.values()))
    return safe_divide(2 * precision * recall, precision + recall)


def safe_divide(numerator, denominator):
    return float(numerator / denominator) if denominator else 0.0


def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def write_csv(path, rows, fieldnames):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def parse_aliases(value):
    value = str(value or "").strip()
    if not value:
        return []
    try:
        parsed = json.loads(value)
        if isinstance(parsed, list):
            return [str(item).strip() for item in parsed if str(item).strip()]
    except json.JSONDecodeError:
        pass
    return [part.strip() for part in re.split(r"[|،,;]", value) if part.strip()]


def load_graph_alias_index(paths):
    entries = []
    seen = set()
    for path in paths:
        if not path.exists():
            continue
        for row in read_csv(path):
            canonical = str(row.get("canonical_name", "")).strip()
            entity_type = str(row.get("entity_type", "")).strip()
            surface = str(row.get("surface_form", "")).strip()
            aliases = parse_aliases(row.get("aliases", ""))
            names = [canonical, surface, *aliases]
            for name in names:
                normalized = normalize_arabic(name)
                key = (normalized, canonical, entity_type)
                if not normalized or not canonical or key in seen:
                    continue
                seen.add(key)
                entries.append(
                    {
                        "name": name,
                        "name_norm": normalized,
                        "canonical_name": canonical,
                        "entity_type": entity_type,
                        "source_file": relpath(path),
                    }
                )
    return entries


TYPE_RULES = [
    ("Test", ["تحليل", "تحاليل", "فحص", "اختبار", "اشعه", "اشعة", "سونار", "رنين", "منظار", "قياس"]),
    ("Treatment", ["علاج", "دواء", "ادويه", "أدوية", "كريم", "مرهم", "بخاخ", "حقن", "ابره", "إبرة", "عملية", "جراحة", "تمرين"]),
    ("Symptom", ["الم", "ألم", "حكه", "حكة", "دوخه", "دوخة", "نزيف", "انتفاخ", "ضيق", "غثيان", "سعال", "اسهال", "إسهال"]),
    ("DiseaseCondition", ["التهاب", "حساسيه", "حساسية", "سكري", "فقر دم", "حصى", "بواسير", "عدوى", "فطريات"]),
]


def apply_type_rules(row):
    text = normalize_arabic(row["pred_canonical_name"])
    matches = []
    for entity_type, cues in TYPE_RULES:
        if any(normalize_arabic(cue) in text for cue in cues):
            matches.append(entity_type)
    if len(matches) == 1:
        return matches[0], f"type_rule:{matches[0]}"
    return row["pred_entity_type"], ""


def apply_canonical_style_rules(row):
    name = row["pred_canonical_name"].strip()
    name_norm = normalize_arabic(name)
    tokens = name.split()
    norm_tokens = tokenize(name_norm)
    if name_norm.startswith(normalize_arabic("مرض ")) and len(tokens) > 1:
        return " ".join(tokens[1:]).strip(), "strip_disease_prefix"
    if len(norm_tokens) == 1 and name_norm.startswith(normalize_arabic("ال")) and len(name) > 3:
        if name.startswith("ال"):
            return name[2:].strip(), "strip_definite_article"
    return row["pred_canonical_name"], ""


def best_graph_candidate(name, entity_type, entries):
    name_norm = normalize_arabic(name)
    if not name_norm:
        return None, 0.0
    best = None
    best_score = 0.0
    for entry in entries:
        if entity_type and entry["entity_type"] and entry["entity_type"] != entity_type:
            continue
        candidate_norm = entry["name_norm"]
        if candidate_norm == name_norm:
            score = 1.0
        elif name_norm in candidate_norm or candidate_norm in name_norm:
            score = 0.88
        else:
            score = 0.70 * token_f1(candidate_norm, name_norm) + 0.30 * SequenceMatcher(None, candidate_norm, name_norm).ratio()
        if score > best_score:
            best = entry
            best_score = score
    return best, best_score


def resolve_graph_canonical(row, entries):
    candidate, score = best_graph_candidate(row["pred_canonical_name"], row["pred_entity_type"], entries)
    if candidate and score >= 0.72:
        return candidate["canonical_name"], candidate["entity_type"] or row["pred_entity_type"], f"graph_resolver:{score:.3f}"
    return row["pred_canonical_name"], row["pred_entity_type"], ""


GENERIC_ENTITY_TERMS = {
    normalize_arabic(term)
    for term in [
        "التهاب",
        "الم",
        "ألم",
        "علاج",
        "دواء",
        "تحليل",
        "فحص",
        "مرض",
        "حالة",
        "اعراض",
        "أعراض",
    ]
}


def resolve_context_alias(row, entries):
    context = normalize_arabic(" ".join([row["question"], row["answer"][:500]]))
    pred_norm = normalize_arabic(row["pred_canonical_name"])
    pred_is_generic = pred_norm in GENERIC_ENTITY_TERMS or len(tokenize(pred_norm)) <= 1
    best = None
    best_score = 0.0
    for entry in entries:
        if row["pred_entity_type"] and entry["entity_type"] and entry["entity_type"] != row["pred_entity_type"]:
            continue
        alias_norm = entry["name_norm"]
        alias_tokens = tokenize(alias_norm)
        if len(alias_norm) < 4 or not alias_tokens:
            continue
        if alias_norm not in context:
            continue
        length_bonus = min(len(alias_tokens), 4) / 4
        pred_overlap = token_f1(alias_norm, pred_norm)
        score = 0.60 * length_bonus + 0.40 * pred_overlap
        if pred_is_generic:
            score += 0.15
        if score > best_score:
            best = entry
            best_score = score
    if best and best_score >= 0.65:
        return best["canonical_name"], best["entity_type"] or row["pred_entity_type"], f"context_alias:{best_score:.3f}"
    return row["pred_canonical_name"], row["pred_entity_type"], ""


def build_diagnostic_correction_map(rows):
    mapping = {}
    for row in rows:
        pred_key = (normalize_arabic(row["pred_canonical_name"]), row["pred_entity_type"])
        gt_value = (row["gt_canonical_name"], row["gt_entity_type"])
        if not pred_key[0]:
            continue
        mapping.setdefault(pred_key, Counter())
        mapping[pred_key][gt_value] += 1
    return {key: counter.most_common(1)[0][0] for key, counter in mapping.items()}


def apply_improvement_mode(rows, mode, graph_entries):
    diagnostic_map = build_diagnostic_correction_map(rows) if mode == "diagnostic_gold_map" else {}
    improved = []
    for row in rows:
        updated = dict(row)
        notes = []
        if mode in {"type_rules", "combined"}:
            new_type, note = apply_type_rules(updated)
            if note and new_type != updated["pred_entity_type"]:
                updated["pred_entity_type"] = new_type
                notes.append(note)
        if mode in {"canonical_style_rules", "combined_conservative"}:
            new_name, note = apply_canonical_style_rules(updated)
            if note and new_name != updated["pred_canonical_name"]:
                updated["pred_canonical_name"] = new_name
                notes.append(note)
        if mode == "type_rules_pred_only":
            new_type, note = apply_type_rules(updated)
            if note and new_type != updated["pred_entity_type"]:
                updated["pred_entity_type"] = new_type
                notes.append(note)
        if mode == "graph_exact_alias":
            candidate, score = best_graph_candidate(updated["pred_canonical_name"], updated["pred_entity_type"], graph_entries)
            if candidate and score >= 1.0:
                new_name = candidate["canonical_name"]
                if new_name.startswith("ال") and not updated["pred_canonical_name"].startswith("ال"):
                    new_name = updated["pred_canonical_name"]
                if new_name != updated["pred_canonical_name"] or candidate["entity_type"] != updated["pred_entity_type"]:
                    updated["pred_canonical_name"] = new_name
                    updated["pred_entity_type"] = candidate["entity_type"] or updated["pred_entity_type"]
                    notes.append("graph_exact_alias")
        if mode in {"graph_resolver", "combined"}:
            new_name, new_type, note = resolve_graph_canonical(updated, graph_entries)
            if note and (new_name != updated["pred_canonical_name"] or new_type != updated["pred_entity_type"]):
                updated["pred_canonical_name"] = new_name
                updated["pred_entity_type"] = new_type
                notes.append(note)
        if mode in {"context_alias_resolver", "combined"}:
            new_name, new_type, note = resolve_context_alias(updated, graph_entries)
            if note and (new_name != updated["pred_canonical_name"] or new_type != updated["pred_entity_type"]):
                updated["pred_canonical_name"] = new_name
                updated["pred_entity_type"] = new_type
                notes.append(note)
        if mode == "combined_conservative":
            candidate, score = best_graph_candidate(updated["pred_canonical_name"], updated["pred_entity_type"], graph_entries)
            if candidate and score >= 1.0:
                new_name = candidate["canonical_name"]
                if new_name.startswith("ال") and not updated["pred_canonical_name"].startswith("ال"):
                    new_name = updated["pred_canonical_name"]
                if new_name != updated["pred_canonical_name"] or candidate["entity_type"] != updated["pred_entity_type"]:
                    updated["pred_canonical_name"] = new_name
                    updated["pred_entity_type"] = candidate["entity_type"] or updated["pred_entity_type"]
                    notes.append("graph_exact_alias")
        if mode == "diagnostic_gold_map":
            key = (normalize_arabic(updated["pred_canonical_name"]), updated["pred_entity_type"])
            if key in diagnostic_map:
                new_name, new_type = diagnostic_map[key]
                if new_name != updated["pred_canonical_name"] or new_type != updated["pred_entity_type"]:
                    updated["pred_canonical_name"] = new_name
                    updated["pred_entity_type"] = new_type
                    notes.append("diagnostic_gold_map")
        updated["improvement_mode"] = mode
        updated["improvement_notes"] = ";".join(notes)
        updated["gt_canonical_name_normalized"] = normalize_arabic(updated["gt_canonical_name"])
        updated["pred_canonical_name_normalized"] = normalize_arabic(updated["pred_canonical_name"])
        precision, recall, f1 = canonical_name_token_metrics(
            updated["gt_canonical_name_normalized"],
            updated["pred_canonical_name_normalized"],
        )
        updated["canonical_name_precision"] = round(precision, 6)
        updated["canonical_name_recall"] = round(recall, 6)
        updated["canonical_name_f1"] = round(f1, 6)
        improved.append(updated)
    return improved


def canonical_name_token_metrics(reference, prediction):
    reference_tokens = Counter(tokenize(reference))
    prediction_tokens = Counter(tokenize(prediction))
    overlap = sum((reference_tokens & prediction_tokens).values())
    reference_count = sum(reference_tokens.values())
    prediction_count = sum(prediction_tokens.values())
    precision = safe_divide(overlap, prediction_count)
    recall = safe_divide(overlap, reference_count)
    f1 = safe_divide(2 * precision * recall, precision + recall)
    return precision, recall, f1


def macro_entity_type_metrics(rows, labels):
    metrics = {}
    for label in labels:
        tp = sum(1 for row in rows if row["gt_entity_type"] == label and row["pred_entity_type"] == label)
        fp = sum(1 for row in rows if row["gt_entity_type"] != label and row["pred_entity_type"] == label)
        fn = sum(1 for row in rows if row["gt_entity_type"] == label and row["pred_entity_type"] != label)
        precision = safe_divide(tp, tp + fp)
        recall = safe_divide(tp, tp + fn)
        f1 = safe_divide(2 * precision * recall, precision + recall)
        support = sum(1 for row in rows if row["gt_entity_type"] == label)
        metrics[label] = {
            "entity_type": label,
            "precision": precision,
            "recall": recall,
            "f1_score": f1,
            "support": support,
        }
    return metrics


def run_optional_bertscore(rows, model_name, batch_size):
    try:
        import torch
        from bert_score import score as bertscore
    except ImportError:
        return None, "bert_score and/or torch is not installed"

    device = "cuda" if torch.cuda.is_available() else "cpu"
    _, _, canonical_f1 = bertscore(
        cands=[row["pred_canonical_name_normalized"] for row in rows],
        refs=[row["gt_canonical_name_normalized"] for row in rows],
        model_type=model_name,
        batch_size=batch_size,
        device=device,
        verbose=False,
        rescale_with_baseline=False,
    )
    _, _, type_f1 = bertscore(
        cands=[row["pred_entity_type"] for row in rows],
        refs=[row["gt_entity_type"] for row in rows],
        model_type=model_name,
        batch_size=batch_size,
        device=device,
        verbose=False,
        rescale_with_baseline=False,
    )
    canonical_values = [float(value) for value in canonical_f1.cpu().numpy()]
    type_values = [float(value) for value in type_f1.cpu().numpy()]
    for row, canonical_value, type_value in zip(rows, canonical_values, type_values):
        row["canonical_name_bertscore_f1"] = round(canonical_value, 6)
        row["entity_type_bertscore_f1"] = round(type_value, 6)
    return {
        "canonical_name_bertscore_f1": safe_divide(sum(canonical_values), len(canonical_values)),
        "entity_type_bertscore_f1": safe_divide(sum(type_values), len(type_values)),
        "device": device,
    }, ""


def build_comparison(ground_truth_rows, prediction_rows, limit):
    required_columns = {"question", "answer", "entity_type", "canonical_name"}
    if not ground_truth_rows:
        raise ValueError("Ground-truth CSV is empty.")
    if not prediction_rows:
        raise ValueError("Prediction CSV is empty.")
    missing_gt = required_columns - set(ground_truth_rows[0].keys())
    missing_pred = required_columns - set(prediction_rows[0].keys())
    if missing_gt:
        raise ValueError(f"Ground-truth CSV is missing columns: {sorted(missing_gt)}")
    if missing_pred:
        raise ValueError(f"Prediction CSV is missing columns: {sorted(missing_pred)}")

    ground_truth_rows = ground_truth_rows[:limit]
    prediction_rows = prediction_rows[:limit]
    if len(ground_truth_rows) != limit:
        raise ValueError(f"Ground-truth CSV contains only {len(ground_truth_rows)} rows; expected {limit}.")
    if len(prediction_rows) != limit:
        raise ValueError(f"Prediction CSV contains only {len(prediction_rows)} rows; expected {limit}.")

    comparison = []
    for index, (gt, pred) in enumerate(zip(ground_truth_rows, prediction_rows), start=1):
        if str(gt["question"]).strip() != str(pred["question"]).strip():
            raise ValueError(f"Question mismatch at row {index}.")
        if str(gt["answer"]).strip() != str(pred["answer"]).strip():
            raise ValueError(f"Answer mismatch at row {index}.")
        row = {
            "row_id": index,
            "question": str(gt["question"]).strip(),
            "answer": str(gt["answer"]).strip(),
            "gt_canonical_name": str(gt["canonical_name"]).strip(),
            "pred_canonical_name": str(pred["canonical_name"]).strip(),
            "gt_entity_type": str(gt["entity_type"]).strip(),
            "pred_entity_type": str(pred["entity_type"]).strip(),
        }
        row["gt_canonical_name_normalized"] = normalize_arabic(row["gt_canonical_name"])
        row["pred_canonical_name_normalized"] = normalize_arabic(row["pred_canonical_name"])
        precision, recall, f1 = canonical_name_token_metrics(
            row["gt_canonical_name_normalized"],
            row["pred_canonical_name_normalized"],
        )
        row["canonical_name_precision"] = round(precision, 6)
        row["canonical_name_recall"] = round(recall, 6)
        row["canonical_name_f1"] = round(f1, 6)
        row["canonical_name_bertscore_f1"] = ""
        row["entity_type_bertscore_f1"] = ""
        comparison.append(row)
    return comparison


def summarize(rows, bertscore_summary=None):
    canonical_precision = safe_divide(sum(float(row["canonical_name_precision"]) for row in rows), len(rows))
    canonical_recall = safe_divide(sum(float(row["canonical_name_recall"]) for row in rows), len(rows))
    canonical_f1 = safe_divide(sum(float(row["canonical_name_f1"]) for row in rows), len(rows))

    labels = sorted(set(ENTITY_TYPES) | {row["gt_entity_type"] for row in rows} | {row["pred_entity_type"] for row in rows})
    type_metrics = macro_entity_type_metrics(rows, labels)
    type_precision = safe_divide(sum(item["precision"] for item in type_metrics.values()), len(type_metrics))
    type_recall = safe_divide(sum(item["recall"] for item in type_metrics.values()), len(type_metrics))
    type_f1 = safe_divide(sum(item["f1_score"] for item in type_metrics.values()), len(type_metrics))

    summary_rows = [
        {
            "feature": "canonical_name",
            "precision": round(canonical_precision, 6),
            "recall": round(canonical_recall, 6),
            "f1_score": round(canonical_f1, 6),
            "bertscore_f1": "",
        },
        {
            "feature": "entity_type",
            "precision": round(type_precision, 6),
            "recall": round(type_recall, 6),
            "f1_score": round(type_f1, 6),
            "bertscore_f1": "",
        },
    ]
    if bertscore_summary:
        summary_rows[0]["bertscore_f1"] = round(bertscore_summary["canonical_name_bertscore_f1"], 6)
        summary_rows[1]["bertscore_f1"] = round(bertscore_summary["entity_type_bertscore_f1"], 6)
    return summary_rows, list(type_metrics.values())


def write_report(path, args, summary_rows, type_report_rows, bertscore_note):
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Step 03B Entity Extraction Evaluation - First 100",
        "",
        "This report evaluates entity extraction against the first-100-row ground truth notebook hand-off.",
        "",
        "## Inputs",
        "",
        f"- Ground truth: `{relpath(args.ground_truth)}`",
        f"- Predictions: `{relpath(args.predictions)}`",
        f"- Rows evaluated: `{args.limit}`",
        f"- Improvement mode: `{args.mode}`",
        "",
        "## Metric Summary",
        "",
        "| Feature | Precision | Recall | F1-score | BERTScore F1 |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in summary_rows:
        bertscore_value = row["bertscore_f1"] if row["bertscore_f1"] != "" else "not computed"
        lines.append(
            f"| {row['feature']} | {row['precision']} | {row['recall']} | {row['f1_score']} | {bertscore_value} |"
        )
    lines.extend(
        [
            "",
            "## Entity-Type Report",
            "",
            "| Entity type | Precision | Recall | F1-score | Support |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for row in type_report_rows:
        lines.append(
            f"| {row['entity_type']} | {round(row['precision'], 6)} | {round(row['recall'], 6)} | {round(row['f1_score'], 6)} | {row['support']} |"
        )
    if bertscore_note:
        lines.extend(["", f"BERTScore note: {bertscore_note}"])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args():
    parser = argparse.ArgumentParser(description="Evaluate first-100 entity extraction ground truth against LLM predictions.")
    parser.add_argument("--ground-truth", type=Path, default=ROOT / "ground_truth_entities_100.csv")
    parser.add_argument("--predictions", type=Path, default=ROOT / "llm_entities_vs_gt_100.csv")
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report-md", type=Path, default=DEFAULT_REPORT_MD)
    parser.add_argument(
        "--mode",
        choices=[
            "baseline",
            "canonical_style_rules",
            "type_rules",
            "type_rules_pred_only",
            "graph_exact_alias",
            "graph_resolver",
            "context_alias_resolver",
            "combined",
            "combined_conservative",
            "diagnostic_gold_map",
        ],
        default="baseline",
        help="Post-processing strategy to evaluate. diagnostic_gold_map is an upper-bound/error-analysis mode, not a deployable method.",
    )
    parser.add_argument(
        "--graph-entity-file",
        action="append",
        type=Path,
        default=[],
        help="CSV file with canonical_name/entity_type and optional aliases or surface_form columns. Can be repeated.",
    )
    parser.add_argument("--bertscore", action="store_true", help="Compute BERTScore F1 if bert_score and torch are installed.")
    parser.add_argument("--bertscore-model", default="xlm-roberta-base")
    parser.add_argument("--bertscore-batch-size", type=int, default=32)
    return parser.parse_args()


def main():
    args = parse_args()
    gt_rows = read_csv(args.ground_truth)
    pred_rows = read_csv(args.predictions)
    comparison = build_comparison(gt_rows, pred_rows, args.limit)
    graph_files = args.graph_entity_file or DEFAULT_GRAPH_ENTITY_FILES
    graph_entries = load_graph_alias_index(graph_files) if args.mode != "baseline" else []
    if args.mode != "baseline":
        comparison = apply_improvement_mode(comparison, args.mode, graph_entries)

    bertscore_summary = None
    bertscore_note = "not requested"
    if args.bertscore:
        bertscore_summary, bertscore_note = run_optional_bertscore(
            comparison,
            args.bertscore_model,
            args.bertscore_batch_size,
        )
        if bertscore_summary:
            bertscore_note = f"computed with {args.bertscore_model} on {bertscore_summary['device']}"

    summary_rows, type_report_rows = summarize(comparison, bertscore_summary)

    summary_path = args.output_dir / "first_100_metric_summary.csv"
    comparison_path = args.output_dir / "first_100_row_comparison.csv"
    type_report_path = args.output_dir / "first_100_entity_type_report.csv"

    write_csv(summary_path, summary_rows, ["feature", "precision", "recall", "f1_score", "bertscore_f1"])
    write_csv(
        comparison_path,
        comparison,
        [
            "row_id",
            "improvement_mode",
            "improvement_notes",
            "question",
            "answer",
            "gt_canonical_name",
            "pred_canonical_name",
            "gt_entity_type",
            "pred_entity_type",
            "gt_canonical_name_normalized",
            "pred_canonical_name_normalized",
            "canonical_name_precision",
            "canonical_name_recall",
            "canonical_name_f1",
            "canonical_name_bertscore_f1",
            "entity_type_bertscore_f1",
        ],
    )
    write_csv(type_report_path, type_report_rows, ["entity_type", "precision", "recall", "f1_score", "support"])
    write_report(args.report_md, args, summary_rows, type_report_rows, bertscore_note)

    print(
        json.dumps(
            {
                "rows_evaluated": len(comparison),
                "summary_csv": relpath(summary_path),
                "row_comparison_csv": relpath(comparison_path),
                "entity_type_report_csv": relpath(type_report_path),
                "report_md": relpath(args.report_md),
                "mode": args.mode,
                "graph_alias_entries": len(graph_entries),
                "bertscore": bertscore_note,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
