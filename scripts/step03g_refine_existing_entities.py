#!/usr/bin/env python
"""Refine the existing large-scale entity inventory using QC rules.

This step is intentionally non-destructive. It keeps the original entity
extraction files unchanged and writes a refined entity table plus a smaller
review queue for cases that should be checked before rebuilding the graph.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "outputs/03_entity_extraction/ahd_entities_llm_merged.csv"
DEFAULT_MENTIONS = ROOT / "outputs/03_entity_extraction/ahd_entity_mentions_llm_merged.csv"
DEFAULT_GT = ROOT / "ground_truth_entities_500.csv"
DEFAULT_OUTPUT_DIR = ROOT / "outputs/03_entity_extraction/refinement"
DEFAULT_REPORT = ROOT / "reports/step03g_entity_refinement_report.md"

VALID_TYPES = {
    "DiseaseCondition",
    "Symptom",
    "Treatment",
    "Drug",
    "DiagnosticTest",
    "BodyPart",
    "Category",
    "Other",
}

TYPE_ALIASES = {
    "Disease": "DiseaseCondition",
    "Condition": "DiseaseCondition",
    "Disease/Condition": "DiseaseCondition",
    "Test": "DiagnosticTest",
    "Procedure": "Treatment",
    "Medication": "Drug",
}

GENERIC_TERMS = {
    "الم",
    "ألم",
    "وجع",
    "التهاب",
    "مرض",
    "امراض",
    "أمراض",
    "علاج",
    "دواء",
    "ادوية",
    "أدوية",
    "حبوب",
    "اعراض",
    "أعراض",
    "مشاكل",
    "مشكلة",
    "حالة",
    "عملية",
    "جراحة",
    "تحليل",
    "فحص",
    "غدة",
    "الغدة",
    "حساسية",
    "تورم",
    "انتفاخ",
    "نزيف",
    "افرازات",
    "إفرازات",
}

BODY_PART_TERMS = {
    "الراس",
    "الرأس",
    "راس",
    "رأس",
    "رقبة",
    "الرقبة",
    "ظهر",
    "الظهر",
    "بطن",
    "البطن",
    "صدر",
    "الصدر",
    "قلب",
    "القلب",
    "كلية",
    "الكلى",
    "سن",
    "اسنان",
    "أسنان",
    "لثة",
    "اللثة",
    "ركبة",
    "الركبة",
    "كتف",
    "الكتف",
    "لسان",
    "اللسان",
}

STOP_PREFIXES = ("ال",)


def normalize_arabic(text: str) -> str:
    text = (text or "").strip()
    text = re.sub(r"[\u064b-\u065f\u0670]", "", text)
    text = text.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")
    text = text.replace("ى", "ي").replace("ة", "ه")
    text = re.sub(r"[^\w\s/+-]", " ", text, flags=re.UNICODE)
    text = re.sub(r"\s+", " ", text)
    return text.strip().lower()


def dearticle(text: str) -> str:
    norm = normalize_arabic(text)
    for prefix in STOP_PREFIXES:
        if norm.startswith(prefix) and len(norm) > len(prefix) + 2:
            return norm[len(prefix) :]
    return norm


def parse_aliases(value: str) -> list[str]:
    value = (value or "").strip()
    if not value:
        return []
    aliases: list[str] = []
    for part in value.split("|"):
        part = part.strip()
        if not part:
            continue
        try:
            parsed = json.loads(part)
            if isinstance(parsed, list):
                aliases.extend(str(x).strip() for x in parsed if str(x).strip())
                continue
        except json.JSONDecodeError:
            pass
        aliases.append(part)
    seen = set()
    result = []
    for alias in aliases:
        key = normalize_arabic(alias)
        if key and key not in seen:
            seen.add(key)
            result.append(alias)
    return result


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: Iterable[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def build_ground_truth_maps(gt_path: Path) -> tuple[dict[str, str], dict[str, str], Counter[str]]:
    """Build conservative style/type hints from reviewed ground truth."""
    gt_rows = load_csv(gt_path) if gt_path.exists() else []
    canonical_by_norm: dict[str, str] = {}
    type_by_norm: dict[str, str] = {}
    counts: Counter[str] = Counter()

    for row in gt_rows:
        name = (row.get("canonical_name") or "").strip()
        etype = normalize_type(row.get("entity_type") or "")
        if not name:
            continue
        keys = {normalize_arabic(name), dearticle(name)}
        for key in keys:
            if key:
                canonical_by_norm.setdefault(key, name)
                if etype:
                    type_by_norm.setdefault(key, etype)
                counts[key] += 1
    return canonical_by_norm, type_by_norm, counts


def normalize_type(entity_type: str) -> str:
    entity_type = (entity_type or "").strip()
    entity_type = TYPE_ALIASES.get(entity_type, entity_type)
    return entity_type if entity_type in VALID_TYPES else entity_type


def is_generic(name: str) -> bool:
    norm = normalize_arabic(name)
    return norm in {normalize_arabic(x) for x in GENERIC_TERMS} or dearticle(name) in {
        dearticle(x) for x in GENERIC_TERMS
    }


def looks_body_part(name: str) -> bool:
    norm = normalize_arabic(name)
    return norm in {normalize_arabic(x) for x in BODY_PART_TERMS} or dearticle(name) in {
        dearticle(x) for x in BODY_PART_TERMS
    }


def quality_flags(row: dict[str, str], aliases: list[str]) -> list[str]:
    name = (row.get("canonical_name") or "").strip()
    etype = normalize_type(row.get("entity_type") or "")
    flags = []
    norm = normalize_arabic(name)

    if not name:
        flags.append("missing_name")
    if etype not in VALID_TYPES:
        flags.append("unknown_type")
    if is_generic(name):
        flags.append("generic_canonical_name")
    if len(norm) <= 2:
        flags.append("very_short_name")
    if len(norm.split()) >= 7:
        flags.append("too_long_for_canonical_name")
    if looks_body_part(name) and etype != "BodyPart":
        flags.append("body_part_name_type_mismatch")
    if etype == "BodyPart" and not looks_body_part(name) and len(norm.split()) > 4:
        flags.append("body_part_too_specific")
    if aliases and normalize_arabic(name) not in {normalize_arabic(a) for a in aliases}:
        flags.append("canonical_name_not_in_aliases")
    return flags


def refine_row(
    row: dict[str, str],
    canonical_by_norm: dict[str, str],
    type_by_norm: dict[str, str],
    duplicate_counts: Counter[str],
) -> dict[str, object]:
    original_name = (row.get("canonical_name") or "").strip()
    original_type = normalize_type(row.get("entity_type") or "")
    aliases = parse_aliases(row.get("aliases") or "")
    norm = normalize_arabic(original_name)
    lookup_keys = [norm, dearticle(original_name)]

    refined_name = original_name
    refined_type = original_type
    actions: list[str] = []
    reasons: list[str] = []

    for key in lookup_keys:
        if key in canonical_by_norm and canonical_by_norm[key] != refined_name:
            refined_name = canonical_by_norm[key]
            actions.append("canonical_style_aligned_to_500_gt")
            reasons.append(f"matched reviewed benchmark entity: {key}")
            break

    for key in lookup_keys:
        gt_type = type_by_norm.get(key)
        if gt_type and gt_type != refined_type:
            refined_type = gt_type
            actions.append("type_aligned_to_500_gt")
            reasons.append(f"type matched reviewed benchmark entity: {key}")
            break

    if original_type not in VALID_TYPES:
        refined_type = TYPE_ALIASES.get(original_type, "Other")
        actions.append("invalid_type_normalized")
        reasons.append(f"invalid original type: {original_type}")

    flags = quality_flags({**row, "canonical_name": refined_name, "entity_type": refined_type}, aliases)
    if duplicate_counts[norm] > 1:
        flags.append("duplicate_canonical_name")
    if is_generic(refined_name):
        actions.append("flagged_for_context_specific_refinement")
        reasons.append("generic term should be kept only if context justifies it")

    needs_review = bool(
        set(flags)
        & {
            "missing_name",
            "unknown_type",
            "generic_canonical_name",
            "very_short_name",
            "too_long_for_canonical_name",
            "body_part_name_type_mismatch",
            "body_part_too_specific",
            "duplicate_canonical_name",
        }
    )

    return {
        **row,
        "refined_canonical_name": refined_name,
        "refined_canonical_name_norm": normalize_arabic(refined_name),
        "refined_entity_type": refined_type,
        "refinement_action": "; ".join(actions) if actions else "kept",
        "refinement_reason": "; ".join(reasons),
        "quality_flags": "; ".join(flags),
        "needs_review": str(needs_review).lower(),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=str(DEFAULT_INPUT))
    parser.add_argument("--mentions", default=str(DEFAULT_MENTIONS))
    parser.add_argument("--ground-truth", default=str(DEFAULT_GT))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--report-md", default=str(DEFAULT_REPORT))
    args = parser.parse_args()

    input_path = Path(args.input)
    mentions_path = Path(args.mentions)
    gt_path = Path(args.ground_truth)
    output_dir = Path(args.output_dir)
    report_path = Path(args.report_md)

    rows = load_csv(input_path)
    canonical_by_norm, type_by_norm, _ = build_ground_truth_maps(gt_path)
    duplicate_counts = Counter(normalize_arabic(r.get("canonical_name", "")) for r in rows)

    refined = [refine_row(r, canonical_by_norm, type_by_norm, duplicate_counts) for r in rows]
    review_rows = [r for r in refined if r["needs_review"] == "true"]
    changed_rows = [r for r in refined if r["refinement_action"] != "kept"]

    base_fields = list(rows[0].keys()) if rows else []
    new_fields = [
        "refined_canonical_name",
        "refined_canonical_name_norm",
        "refined_entity_type",
        "refinement_action",
        "refinement_reason",
        "quality_flags",
        "needs_review",
    ]
    fields = base_fields + [f for f in new_fields if f not in base_fields]

    refined_csv = output_dir / "ahd_entities_llm_merged_refined.csv"
    graph_ready_csv = output_dir / "ahd_entities_llm_merged_graph_ready.csv"
    review_csv = output_dir / "ahd_entities_llm_merged_needs_review.csv"
    changed_csv = output_dir / "ahd_entities_llm_merged_changed_rows.csv"
    graph_ready_mentions_csv = output_dir / "ahd_entity_mentions_llm_merged_graph_ready.csv"

    write_csv(refined_csv, refined, fields)
    write_csv(review_csv, review_rows, fields)
    write_csv(changed_csv, changed_rows, fields)

    graph_ready_rows: list[dict[str, object]] = []
    for row in refined:
        if row["needs_review"] == "true":
            continue
        graph_row = dict(row)
        graph_row["canonical_name"] = row["refined_canonical_name"]
        graph_row["canonical_name_norm"] = row["refined_canonical_name_norm"]
        graph_row["entity_type"] = row["refined_entity_type"]
        graph_ready_rows.append(graph_row)
    write_csv(graph_ready_csv, graph_ready_rows, fields)

    graph_ready_by_id = {str(row.get("entity_id", "")): row for row in graph_ready_rows}
    refined_mentions: list[dict[str, object]] = []
    mentions_read = 0
    mentions_kept = 0
    mentions_dropped = 0
    if mentions_path.exists():
        mention_rows = load_csv(mentions_path)
        mentions_read = len(mention_rows)
        mention_fields = list(mention_rows[0].keys()) if mention_rows else []
        for mention in mention_rows:
            entity_id = mention.get("entity_id", "")
            entity = graph_ready_by_id.get(entity_id)
            if not entity:
                mentions_dropped += 1
                continue
            updated = dict(mention)
            updated["canonical_name"] = entity["canonical_name"]
            updated["entity_type"] = entity["entity_type"]
            refined_mentions.append(updated)
        mentions_kept = len(refined_mentions)
        write_csv(graph_ready_mentions_csv, refined_mentions, mention_fields)

    flag_counter: Counter[str] = Counter()
    action_counter: Counter[str] = Counter()
    type_counter = Counter(str(r["refined_entity_type"]) for r in refined)
    for row in refined:
        for flag in str(row["quality_flags"]).split("; "):
            if flag:
                flag_counter[flag] += 1
        for action in str(row["refinement_action"]).split("; "):
            if action:
                action_counter[action] += 1

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        "\n".join(
            [
                "# Step 03G Entity Inventory Refinement Report",
                "",
                "## Purpose",
                "",
                "This step protects the previously extracted large entity inventory while applying quality-control signals learned from the 500-row reviewed benchmark.",
                "The original extraction file is not overwritten.",
                "",
                "## Inputs",
                "",
                f"- Entity inventory: `{input_path.as_posix()}`",
                f"- Entity mentions: `{mentions_path.as_posix()}`",
                f"- Reviewed benchmark: `{gt_path.as_posix()}`",
                "",
                "## Outputs",
                "",
                f"- Refined inventory: `{refined_csv.as_posix()}`",
                f"- Graph-ready trusted inventory: `{graph_ready_csv.as_posix()}`",
                f"- Graph-ready trusted mentions: `{graph_ready_mentions_csv.as_posix()}`",
                f"- Review queue: `{review_csv.as_posix()}`",
                f"- Changed rows: `{changed_csv.as_posix()}`",
                "",
                "## Summary",
                "",
                f"- Total entities processed: {len(refined)}",
                f"- Graph-ready rows without review flags: {len(graph_ready_rows)}",
                f"- Mention rows read: {mentions_read}",
                f"- Mention rows kept for graph-ready entities: {mentions_kept}",
                f"- Mention rows held back with review-flagged entities: {mentions_dropped}",
                f"- Rows with refinement actions: {len(changed_rows)}",
                f"- Rows flagged for review: {len(review_rows)}",
                "",
                "## Refinement Actions",
                "",
                *[f"- {k}: {v}" for k, v in action_counter.most_common()],
                "",
                "## Quality Flags",
                "",
                *[f"- {k}: {v}" for k, v in flag_counter.most_common()],
                "",
                "## Refined Entity-Type Distribution",
                "",
                *[f"- {k}: {v}" for k, v in type_counter.most_common()],
                "",
                "## Interpretation",
                "",
                "The graph-ready file can be used as a conservative candidate source for rebuilding the graph immediately. The review queue is not discarded; it contains entities whose canonical name or type needs human checking before being trusted as final graph nodes.",
            ]
        ),
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "entities_processed": len(refined),
                "rows_with_refinement_actions": len(changed_rows),
                "rows_flagged_for_review": len(review_rows),
                "graph_ready_rows": len(graph_ready_rows),
                "mention_rows_read": mentions_read,
                "graph_ready_mentions": mentions_kept,
                "mentions_held_back": mentions_dropped,
                "refined_csv": str(refined_csv.relative_to(ROOT)),
                "graph_ready_csv": str(graph_ready_csv.relative_to(ROOT)),
                "graph_ready_mentions_csv": str(graph_ready_mentions_csv.relative_to(ROOT)),
                "review_csv": str(review_csv.relative_to(ROOT)),
                "changed_csv": str(changed_csv.relative_to(ROOT)),
                "report_md": str(report_path.relative_to(ROOT)),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
