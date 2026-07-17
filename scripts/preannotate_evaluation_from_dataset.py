from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from scripts.prepare_evaluation_annotations import (
    CLAIM_ANNOTATIONS_CSV,
    CLAIM_COLUMNS,
    RETRIEVAL_ANNOTATIONS_CSV,
    RETRIEVAL_COLUMNS,
    ROOT,
)
from src.step05a_final_graph_adapter import load_final_graph_records


ORIGINAL_DATASET = ROOT / "data" / "raw" / "AHD.csv"
PROVISIONAL_STATUS = "provisional_dataset_annotation"
PROVISIONAL_ANNOTATOR = "dataset_preannotation_v1"

ARABIC_DIACRITICS_RE = re.compile(r"[\u064b-\u065f\u0670\u06d6-\u06ed]")
TATWEEL_RE = re.compile(r"\u0640+")
NON_WORD_RE = re.compile(r"[^\w\u0600-\u06ff]+", re.UNICODE)
WHITESPACE_RE = re.compile(r"\s+")
ARABIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")
ARABIC_LETTER_NORMALIZATION = str.maketrans(
    {"أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا", "ى": "ي", "ئ": "ي", "ؤ": "و", "ة": "ه"}
)


def normalize_for_dedupe(value: Any) -> str:
    """Normalize only for deterministic dataset/gold-record comparison."""
    text = str(value or "").strip().translate(ARABIC_DIGITS)
    text = TATWEEL_RE.sub("", text)
    text = ARABIC_DIACRITICS_RE.sub("", text)
    text = text.translate(ARABIC_LETTER_NORMALIZATION)
    text = NON_WORD_RE.sub(" ", text)
    return WHITESPACE_RE.sub(" ", text).strip().lower()

GENERIC_ENTITY_FORMS = {
    "اعراض",
    "تحاليل",
    "تحليل",
    "دواء",
    "علاج",
    "فحص",
    "مرض",
    "حاله",
    "الم",
    "الطبيب",
    "طبيب",
    "الدم",
    "دم",
    "الدوره",
    "الدوره الشهريه",
    "العمليات",
    "عمليات",
    "الضغط",
    "ضغط",
    "الهرمون",
    "هرمون",
}

RELATION_TYPES_BY_GROUP = {
    "treatment": {"TREATED_BY", "TREATS"},
    "symptoms": {"HAS_SYMPTOM", "SYMPTOM_OF"},
    "tests_diagnosis": {"DIAGNOSED_BY", "DIAGNOSES", "INVESTIGATED_BY", "INVESTIGATES"},
    "causes_safety": set(),
    "general_medical": set(),
}

SOURCE_QA_RE = re.compile(r"source_qa_id=([^;]+)")
SOURCE_ROW_RE = re.compile(r"source_row_number=([^;]+)")
SOURCE_CATEGORY_RE = re.compile(r"source_category=([^;]+)")
CLAIM_SPLIT_RE = re.compile(r"(?<=[.!?\u061f;\u061b])(?:\s+|(?=[^\s]))|[\r\n]+")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def extract_note_value(pattern: re.Pattern[str], notes: str) -> str:
    match = pattern.search(notes)
    return match.group(1).strip() if match else ""


def token_set(text: str) -> set[str]:
    return {token for token in normalize_for_dedupe(text).split() if len(token) >= 2}


def is_generic_form(form: str) -> bool:
    if form in GENERIC_ENTITY_FORMS:
        return True
    without_article = form[2:] if form.startswith("ال") and len(form) > 4 else form
    return without_article in GENERIC_ENTITY_FORMS


def contains_phrase(text_norm: str, phrase_norm: str) -> bool:
    if not phrase_norm or is_generic_form(phrase_norm):
        return False
    text_tokens = text_norm.split()
    phrase_tokens = phrase_norm.split()
    if not phrase_tokens or len(phrase_tokens) > len(text_tokens):
        return False
    prefixes = ("وال", "فال", "بال", "كال", "لل", "او", "و", "ف", "ب", "ك", "ل")
    for start in range(len(text_tokens) - len(phrase_tokens) + 1):
        for offset, phrase_token in enumerate(phrase_tokens):
            text_token = text_tokens[start + offset]
            if text_token == phrase_token:
                continue
            if not any(
                text_token == prefix + phrase_token and len(phrase_token) >= 3
                for prefix in prefixes
            ):
                break
        else:
            return True
    return False


def parse_aliases(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    try:
        parsed = json.loads(str(value or "[]"))
    except json.JSONDecodeError:
        return []
    return [str(item).strip() for item in parsed if str(item).strip()] if isinstance(parsed, list) else []


def build_entity_forms(entities: list[dict[str, Any]]) -> dict[str, list[str]]:
    forms: dict[str, list[str]] = {}
    for entity in entities:
        values = [
            str(entity.get("canonical_name") or ""),
            str(entity.get("canonical_name_norm") or ""),
            *parse_aliases(entity.get("aliases")),
        ]
        normalized = {normalize_for_dedupe(value) for value in values if value}
        normalized = {form for form in normalized if not is_generic_form(form)}
        forms[str(entity["entity_id"])] = sorted(normalized, key=lambda value: (-len(value), value))
    return forms


def matched_entities(
    row: dict[str, str],
    entities: list[dict[str, Any]],
    forms_by_entity: dict[str, list[str]],
) -> tuple[list[str], set[str], set[str]]:
    query_norm = normalize_for_dedupe(row["query"])
    answer_norm = normalize_for_dedupe(row["reference_answer"])
    query_forms: dict[str, str] = {}
    answer_forms: dict[str, str] = {}

    for entity in entities:
        entity_id = str(entity["entity_id"])
        for form in forms_by_entity[entity_id]:
            if contains_phrase(query_norm, form):
                if len(form) > len(query_forms.get(entity_id, "")):
                    query_forms[entity_id] = form
            if contains_phrase(answer_norm, form):
                if len(form) > len(answer_forms.get(entity_id, "")):
                    answer_forms[entity_id] = form

    def remove_strict_subphrases(matches: dict[str, str]) -> dict[str, str]:
        all_forms = list(matches.values())
        return {
            entity_id: form
            for entity_id, form in matches.items()
            if not any(form != other and f" {form} " in f" {other} " for other in all_forms)
        }

    query_forms = remove_strict_subphrases(query_forms)
    answer_forms = remove_strict_subphrases(answer_forms)
    query_matches = set(query_forms)
    answer_matches = set(answer_forms)
    specificity = {
        entity_id: max(len(query_forms.get(entity_id, "")), len(answer_forms.get(entity_id, "")))
        for entity_id in query_matches | answer_matches
    }

    ordered = sorted(
        query_matches | answer_matches,
        key=lambda entity_id: (
            entity_id not in query_matches,
            -specificity.get(entity_id, 0),
            entity_id,
        ),
    )
    return ordered[:10], query_matches, answer_matches


def verify_original_rows(rows: list[dict[str, str]]) -> dict[str, bool]:
    wanted: dict[int, dict[str, str]] = {}
    for row in rows:
        source_row = extract_note_value(SOURCE_ROW_RE, row.get("annotation_notes", ""))
        if source_row.isdigit():
            wanted[int(source_row)] = row

    verified = {row["query_id"]: False for row in rows}
    with ORIGINAL_DATASET.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for source_row_number, source in enumerate(reader, start=2):
            selected = wanted.get(source_row_number)
            if selected is None:
                continue
            verified[selected["query_id"]] = (
                normalize_for_dedupe(source.get("Question")) == normalize_for_dedupe(selected["query"])
                and normalize_for_dedupe(source.get("Answer"))
                == normalize_for_dedupe(selected["reference_answer"])
            )
            if all(verified.values()):
                break
    return verified


def select_provenance(
    row: dict[str, str],
    selected_entity_ids: list[str],
    query_entities: set[str],
    answer_entities: set[str],
    mentions_by_qa: dict[str, list[dict[str, Any]]],
    qa_by_id: dict[str, dict[str, Any]],
) -> tuple[list[str], list[str]]:
    selected_set = set(selected_entity_ids)
    query_tokens = token_set(row["query"])
    answer_tokens = token_set(row["reference_answer"])
    source_category = normalize_for_dedupe(
        extract_note_value(SOURCE_CATEGORY_RE, row.get("annotation_notes", ""))
    )
    ranked: list[tuple[float, str]] = []

    for qa_id, mentions in mentions_by_qa.items():
        entity_ids = {str(item.get("entity_id") or "") for item in mentions}
        matched = entity_ids & selected_set
        if not matched:
            continue
        query_overlap = len(entity_ids & query_entities)
        answer_overlap = len(entity_ids & answer_entities)
        if query_overlap == 0 and answer_overlap < 2:
            continue
        qa = qa_by_id.get(qa_id, {})
        qa_tokens = token_set(f"{qa.get('question', '')} {qa.get('answer', '')}")
        lexical_overlap = len((query_tokens | answer_tokens) & qa_tokens) / max(
            1, len(query_tokens | answer_tokens)
        )
        category_match = bool(
            source_category
            and normalize_for_dedupe(str(qa.get("category") or "")) == source_category
        )
        score = query_overlap * 4.0 + answer_overlap * 2.0 + lexical_overlap * 3.0 + category_match * 2.0
        ranked.append((score, qa_id))

    selected_qa_ids = [qa_id for _, qa_id in sorted(ranked, key=lambda item: (-item[0], item[1]))[:5]]
    evidence = [
        mention
        for qa_id in selected_qa_ids
        for mention in mentions_by_qa.get(qa_id, [])
        if str(mention.get("entity_id") or "") in selected_set
    ]
    evidence.sort(
        key=lambda item: (
            str(item.get("entity_id") or "") not in query_entities,
            -float(item.get("confidence") or 0.0),
            str(item.get("mention_id") or ""),
        )
    )
    evidence_ids = list(
        dict.fromkeys(str(item.get("mention_id") or "") for item in evidence if item.get("mention_id"))
    )[:10]
    return selected_qa_ids, evidence_ids


def select_relations(
    row: dict[str, str],
    entity_ids: list[str],
    qa_ids: list[str],
    relations: list[dict[str, Any]],
) -> list[str]:
    entity_set = set(entity_ids)
    qa_set = set(qa_ids)
    preferred_types = RELATION_TYPES_BY_GROUP.get(row.get("query_group", ""), set())
    ranked: list[tuple[int, float, str]] = []
    for relation in relations:
        source_id = str(relation.get("source_entity_id") or "")
        target_id = str(relation.get("target_entity_id") or "")
        qa_id = str(relation.get("qa_id") or "")
        relation_type = str(relation.get("relation_type") or "")
        endpoint_count = int(source_id in entity_set) + int(target_id in entity_set)
        if endpoint_count < 2 and qa_id not in qa_set:
            continue
        if preferred_types and relation_type not in preferred_types:
            continue
        relation_id = str(relation.get("source_relation_id") or relation.get("relation_id") or "")
        if relation_id:
            ranked.append((endpoint_count + int(qa_id in qa_set), float(relation.get("confidence") or 0), relation_id))
    ranked.sort(key=lambda item: (-item[0], -item[1], item[2]))
    return list(dict.fromkeys(relation_id for _, _, relation_id in ranked))[:10]


def provisional_retrieval_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    records, validation = load_final_graph_records()
    if not validation.ok:
        raise RuntimeError("Frozen final graph adapter failed validation; pre-annotation stopped.")
    verified = verify_original_rows(rows)
    forms_by_entity = build_entity_forms(records.entities)
    mentions_by_qa: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for mention in records.mentions:
        mentions_by_qa[str(mention.get("qa_id") or "")].append(mention)
    qa_by_id = {str(qa.get("qa_id") or ""): qa for qa in records.qa_records}

    output = []
    for row in rows:
        entity_ids, query_entities, answer_entities = matched_entities(row, records.entities, forms_by_entity)
        qa_ids, evidence_ids = select_provenance(
            row, entity_ids, query_entities, answer_entities, mentions_by_qa, qa_by_id
        )
        relation_ids = select_relations(row, entity_ids, qa_ids, records.medical_relations)
        answerable = bool(qa_ids and evidence_ids and entity_ids)
        previous_notes = str(row.get("annotation_notes") or "")
        source_qa_id = extract_note_value(SOURCE_QA_RE, previous_notes)
        source_row_number = extract_note_value(SOURCE_ROW_RE, previous_notes)
        source_category = extract_note_value(SOURCE_CATEGORY_RE, previous_notes)
        notes = "; ".join(
            part
            for part in (
                "PROVISIONAL DATASET-DERIVED LABELS; human confirmation required",
                f"original_dataset_row_verified={str(verified.get(row['query_id'], False)).lower()}",
                f"source_qa_id={source_qa_id}" if source_qa_id else "",
                f"source_row_number={source_row_number}" if source_row_number else "",
                f"source_category={source_category}" if source_category else "",
                "method=exact entity phrases in held-out question/reference plus frozen provenance overlap",
                "not eligible for gold metrics until status is annotated or adjudicated",
            )
            if part
        )
        updated = dict(row)
        updated.update(
            {
                "gold_entity_ids": "|".join(entity_ids),
                "gold_evidence_ids": "|".join(evidence_ids),
                "gold_qa_ids": "|".join(qa_ids),
                "gold_relation_ids": "|".join(relation_ids),
                "answerable_from_final_graph": str(answerable).lower(),
                "annotation_status": PROVISIONAL_STATUS,
                "annotator_id": PROVISIONAL_ANNOTATOR,
                "adjudicator_id": "",
                "annotation_notes": notes,
            }
        )
        output.append({column: str(updated.get(column, "")) for column in RETRIEVAL_COLUMNS})
    return output


def reference_claims(text: str) -> list[str]:
    claims = []
    for sentence in CLAIM_SPLIT_RE.split(text.strip()):
        sentence = sentence.strip(" \t,،;؛")
        if len(sentence) >= 8:
            claims.append(sentence)
    return claims or ([text.strip()] if text.strip() else [])


def provisional_claim_rows(retrieval_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    output: list[dict[str, str]] = []
    for row in retrieval_rows:
        source_qa_id = extract_note_value(SOURCE_QA_RE, row.get("annotation_notes", ""))
        for index, claim in enumerate(reference_claims(row["reference_answer"]), start=1):
            values = {
                "query_id": row["query_id"],
                "mode": "reference_answer",
                "claim_id": f"{row['query_id']}_reference_c{index:02d}",
                "claim_text": claim,
                "response_text": row["reference_answer"],
                "cited_evidence_ids": "",
                "cited_qa_ids": "",
                # These are dataset-derived review suggestions, never human-confirmed labels.
                "human_support_label": "supported",
                "human_citation_valid": "not_applicable",
                "human_medical_correctness": "uncertain",
                "human_hallucination_label": "no",
                "harm_severity": "none",
                "annotator_id": PROVISIONAL_ANNOTATOR,
                "annotation_timestamp_utc": "",
                "adjudication_status": PROVISIONAL_STATUS,
                "adjudicator_id": "",
                "annotation_notes": (
                    "PROVISIONAL claim candidate split from the original dataset reference answer; "
                    "human must confirm atomicity, correctness, and overwrite all provisional human_* labels"
                    + (f"; source_qa_id={source_qa_id}" if source_qa_id else "")
                ),
            }
            output.append({column: str(values.get(column, "")) for column in CLAIM_COLUMNS})
    return output


def replace_unconfirmed_csv(path: Path, columns: tuple[str, ...], rows: list[dict[str, str]], status_field: str) -> None:
    if path.exists():
        existing = read_csv(path)
        protected = [
            row for row in existing if str(row.get(status_field) or "") in {"annotated", "adjudicated"}
        ]
        if protected:
            raise RuntimeError(f"Refusing to replace human-confirmed annotations in {path}.")
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)


def main() -> int:
    parser = argparse.ArgumentParser(description="Create provisional evaluation labels from original AHD data.")
    parser.add_argument("--retrieval-file", type=Path, default=RETRIEVAL_ANNOTATIONS_CSV)
    parser.add_argument("--claim-file", type=Path, default=CLAIM_ANNOTATIONS_CSV)
    parser.add_argument("--execute", action="store_true", help="Replace only unconfirmed annotation queues.")
    args = parser.parse_args()
    retrieval_file = args.retrieval_file.resolve()
    claim_file = args.claim_file.resolve()
    source_rows = read_csv(retrieval_file)
    retrieval_rows = provisional_retrieval_rows(source_rows)
    claim_rows = provisional_claim_rows(retrieval_rows)
    summary = {
        "status": "ready" if args.execute else "dry_run",
        "retrieval_rows": len(retrieval_rows),
        "claim_rows": len(claim_rows),
        "answerable_rows": sum(row["answerable_from_final_graph"] == "true" for row in retrieval_rows),
        "rows_with_entities": sum(bool(row["gold_entity_ids"]) for row in retrieval_rows),
        "rows_with_evidence": sum(bool(row["gold_evidence_ids"]) for row in retrieval_rows),
        "annotation_status": PROVISIONAL_STATUS,
        "eligible_for_gold_metrics": False,
    }
    if args.execute:
        replace_unconfirmed_csv(
            retrieval_file,
            RETRIEVAL_COLUMNS,
            retrieval_rows,
            "annotation_status",
        )
        replace_unconfirmed_csv(
            claim_file,
            CLAIM_COLUMNS,
            claim_rows,
            "adjudication_status",
        )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
