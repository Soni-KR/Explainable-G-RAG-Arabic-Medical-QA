from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path

ANNOTATION_FIELDS = (
    "relevance_label",
    "error_reason",
    "secondary_error_reason",
    "annotation_status",
    "annotator_id",
    "annotation_notes",
)


def read_csv(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader), list(reader.fieldnames or [])


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def clean(value: object) -> str:
    return "" if value is None else str(value).strip()


def truthy_variant(matched: str, variant: str) -> str:
    parts = {part.strip().upper() for part in matched.replace(",", "|").split("|") if part.strip()}
    return "True" if variant.upper() in parts else "False"


def validate_annotations(rows: list[dict[str, str]]) -> None:
    required = {
        "query_id", "qa_id", "relevance_label", "error_reason",
        "annotation_status", "annotator_id"
    }
    if not rows:
        raise ValueError("The annotation file contains no rows.")
    missing = required - set(rows[0])
    if missing:
        raise ValueError(f"Annotation file is missing columns: {sorted(missing)}")

    seen: set[tuple[str, str]] = set()
    for line_no, row in enumerate(rows, start=2):
        key = (clean(row.get("query_id")), clean(row.get("qa_id")))
        if not all(key):
            raise ValueError(f"Row {line_no}: blank query_id or qa_id")
        if key in seen:
            raise ValueError(f"Row {line_no}: duplicate key {key}")
        seen.add(key)

        label = clean(row.get("relevance_label"))
        if label not in {"0", "1", "2"}:
            raise ValueError(f"Row {line_no}: invalid relevance_label={label!r}")
        if label in {"0", "1"} and not clean(row.get("error_reason")):
            raise ValueError(f"Row {line_no}: error_reason required for label {label}")
        if clean(row.get("annotation_status")) != "human_confirmed":
            raise ValueError(f"Row {line_no}: annotation_status must be human_confirmed")
        if not clean(row.get("annotator_id")):
            raise ValueError(f"Row {line_no}: annotator_id is blank")


def mapped_new_row(
    annotation: dict[str, str],
    fields: list[str],
    query_template: dict[str, str] | None,
    next_index: int,
) -> dict[str, str]:
    row = {field: "" for field in fields}
    template = query_template or {}

    row.update({
        "index": str(next_index),
        "combined_version": "candidate_combined_v2",
        "candidate_pool": "partial_fts_expansion_step11_review",
        "query_id": clean(annotation.get("query_id")),
        "query": clean(annotation.get("original_query")) or clean(template.get("query")),
        "query_group": clean(annotation.get("query_group")) or clean(template.get("query_group")),
        "reference_answer": clean(template.get("reference_answer")),
        "primary_intent": clean(annotation.get("primary_intent")) or clean(template.get("primary_intent")),
        "candidate_type": "evidence",
        "pool_rank": clean(annotation.get("expansion_rank")),
        "candidate_id": f"qa::{clean(annotation.get('qa_id'))}",
        "qa_id": clean(annotation.get("qa_id")),
        "source_row_number": clean(annotation.get("source_row_number")),
        "source_quality": "ahd_heldout_safe_corpus",
        "retrieval_channel": "partial_fts_expansion",
        "candidate_question": clean(annotation.get("question")),
        "candidate_answer_or_evidence": clean(annotation.get("answer")),
        "category": clean(annotation.get("category")),
        "retrieval_score": "0.95",
        "source_reliability": "0.95",
        "matched_variants": clean(annotation.get("matched_variants")),
        "variant_A": truthy_variant(clean(annotation.get("matched_variants")), "A"),
        "variant_B": truthy_variant(clean(annotation.get("matched_variants")), "B"),
        "variant_C": truthy_variant(clean(annotation.get("matched_variants")), "C"),
        "variant_support_count": clean(annotation.get("variant_support_count")),
        "variant_a_rank": clean(annotation.get("variant_a_rank")),
        "variant_b_rank": clean(annotation.get("variant_b_rank")),
        "variant_c_rank": clean(annotation.get("variant_c_rank")),
        "best_variant_rank": clean(annotation.get("best_variant_rank")),
        "best_bm25_rank": clean(annotation.get("best_bm25_rank")),
        "safety_mode": clean(annotation.get("safety_mode")),
        "safety_reason": clean(annotation.get("safety_reason")),
        "graph_aliases_added": clean(annotation.get("graph_aliases_added")),
    })

    for field in ANNOTATION_FIELDS:
        row[field] = clean(annotation.get(field))

    imported_note = "Imported from targeted_fts_production_step11_replay_annotated_confirmed.csv."
    row["annotation_notes"] = f"{row.get('annotation_notes', '').strip()} {imported_note}".strip()
    return row


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Merge the 11 human-reviewed Step 11 expansion candidates into the combined relevance pool."
    )
    parser.add_argument("--combined", type=Path, required=True)
    parser.add_argument("--annotations", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()

    combined, fields = read_csv(args.combined)
    annotations, _ = read_csv(args.annotations)
    validate_annotations(annotations)

    needed = {"query_id", "qa_id", "candidate_id", "relevance_label"}
    missing = needed - set(fields)
    if missing:
        raise ValueError(f"Combined pool is missing columns: {sorted(missing)}")

    for row in combined:
        if "combined_version" in row:
            row["combined_version"] = "candidate_combined_v2"

    # The same QA record may legitimately occur more than once for a query
    # because different retrieval channels can retrieve it. Keep every
    # occurrence and apply the same human relevance annotation to all of them.
    by_key: dict[tuple[str, str], list[dict[str, str]]] = {}
    query_templates: dict[str, dict[str, str]] = {}
    for row in combined:
        key = (clean(row.get("query_id")), clean(row.get("qa_id")))
        if all(key):
            by_key.setdefault(key, []).append(row)
        query_templates.setdefault(clean(row.get("query_id")), row)

    numeric_indices = []
    for row in combined:
        try:
            numeric_indices.append(int(float(clean(row.get("index")))))
        except ValueError:
            pass
    next_index = max(numeric_indices, default=len(combined) - 1) + 1

    before_labels = Counter(clean(r.get("relevance_label")) for r in combined)
    updated_annotation_keys = 0
    updated_candidate_occurrences = 0
    appended = 0
    changed_keys: list[str] = []

    for annotation in annotations:
        key = (clean(annotation.get("query_id")), clean(annotation.get("qa_id")))
        matches = by_key.get(key, [])

        if matches:
            for target in matches:
                for field in ANNOTATION_FIELDS:
                    target[field] = clean(annotation.get(field))
                updated_candidate_occurrences += 1
            updated_annotation_keys += 1
        else:
            new_row = mapped_new_row(
                annotation,
                fields,
                query_templates.get(key[0]),
                next_index,
            )
            next_index += 1
            combined.append(new_row)
            by_key.setdefault(key, []).append(new_row)
            appended += 1

        changed_keys.append("|".join(key))

    after_labels = Counter(clean(r.get("relevance_label")) for r in combined)
    write_csv(args.output, combined, fields)

    summary = {
        "status": "PASS",
        "input_combined_rows": len(combined) - appended,
        "annotation_rows": len(annotations),
        "updated_existing_annotation_keys": updated_annotation_keys,
        "updated_existing_candidate_occurrences": updated_candidate_occurrences,
        "appended_new_rows": appended,
        "output_rows": len(combined),
        "labels_before": dict(sorted(before_labels.items())),
        "labels_after": dict(sorted(after_labels.items())),
        "merged_keys": changed_keys,
        "output_file": str(args.output),
    }
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
