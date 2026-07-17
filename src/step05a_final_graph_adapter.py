from __future__ import annotations

import csv
import json
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.config import ROOT_DIR


FINAL_DIR = ROOT_DIR / "outputs" / "final_graph"
ENTITY_SOURCE = FINAL_DIR / "entities.csv"
MENTION_SOURCE = FINAL_DIR / "entity_mentions.csv"
RELATION_SOURCE = FINAL_DIR / "relations_bidirectional.csv"
QA_5K_SOURCE = FINAL_DIR / "provenance" / "qa_records_source_5000.csv"


@dataclass
class FinalGraphRecords:
    entities: list[dict[str, Any]] = field(default_factory=list)
    mentions: list[dict[str, Any]] = field(default_factory=list)
    qa_records: list[dict[str, Any]] = field(default_factory=list)
    medical_relations: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class ValidationResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def clean(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    return "" if text.lower() in {"none", "null", "nan"} else text


def safe_float(value: Any) -> float:
    try:
        return min(1.0, max(0.0, float(clean(value))))
    except ValueError:
        return 0.0


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def parse_aliases(value: Any) -> list[str]:
    try:
        parsed = json.loads(clean(value))
    except json.JSONDecodeError:
        parsed = []
    if not isinstance(parsed, list):
        return []
    seen = set()
    aliases = []
    for value in parsed:
        alias = clean(value)
        if alias and alias not in seen:
            seen.add(alias)
            aliases.append(alias)
    return aliases


def adapt_entities(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    return [
        {
            "entity_id": clean(row.get("entity_id")),
            "canonical_name": clean(row.get("canonical_name")),
            "canonical_name_norm": clean(row.get("canonical_name_norm")),
            "entity_type": clean(row.get("entity_type")),
            "aliases": parse_aliases(row.get("aliases")),
            "confidence": safe_float(row.get("confidence")),
            "mention_count": int(clean(row.get("mention_count")) or 0),
        }
        for row in rows
    ]


def adapt_mentions(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    return [
        {
            "mention_id": clean(row.get("mention_id")),
            "entity_id": clean(row.get("entity_id")),
            "qa_id": clean(row.get("qa_id")),
            "surface_form": clean(row.get("surface_form")),
            "field": clean(row.get("field")),
            "evidence": clean(row.get("evidence")),
            "confidence": safe_float(row.get("confidence") or row.get("llm_confidence")),
            "source_row_number": clean(row.get("source_row_number")),
        }
        for row in rows
    ]


def unique_join(values: list[str]) -> str:
    seen = set()
    ordered = []
    for value in values:
        text = clean(value)
        if text and text not in seen:
            seen.add(text)
            ordered.append(text)
    return "\n".join(ordered)


def build_qa_records(
    mentions: list[dict[str, Any]],
    relations: list[dict[str, Any]],
    preprocessed_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    by_id = {clean(row.get("subset_id")): row for row in preprocessed_rows}
    by_source_row = {clean(row.get("source_row_number")): row for row in preprocessed_rows}
    mentions_by_qa: dict[str, list[dict[str, Any]]] = defaultdict(list)
    relations_by_qa: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for mention in mentions:
        mentions_by_qa[mention["qa_id"]].append(mention)
    for relation in relations:
        relations_by_qa[relation["qa_id"]].append(relation)

    qa_ids = sorted((set(mentions_by_qa) | set(relations_by_qa)) - {""})
    records = []
    for qa_id in qa_ids:
        qa_mentions = mentions_by_qa.get(qa_id, [])
        qa_relations = relations_by_qa.get(qa_id, [])
        source_rows = [item["source_row_number"] for item in qa_mentions if item.get("source_row_number")]
        source_row = Counter(source_rows).most_common(1)[0][0] if source_rows else ""
        trusted = by_id.get(qa_id) or by_source_row.get(source_row)

        if trusted:
            question = clean(trusted.get("question"))
            answer = clean(trusted.get("answer"))
            category = clean(trusted.get("category"))
            source_quality = "preprocessed_id" if qa_id in by_id else "preprocessed_source_row"
        else:
            question = unique_join(
                [item["evidence"] for item in qa_mentions if item["field"].lower() == "question"]
            )
            answer = unique_join(
                [item["evidence"] for item in qa_mentions if item["field"].lower() == "answer"]
            )
            unknown = unique_join(
                [item["evidence"] for item in qa_mentions if item["field"].lower() not in {"question", "answer"}]
            )
            relation_evidence = unique_join([item["evidence"] for item in qa_relations])
            if not question:
                question = unknown or relation_evidence
            if not answer:
                answer = relation_evidence or unknown
            category = ""
            source_quality = "mention_evidence"

        records.append(
            {
                "qa_id": qa_id,
                "question": question,
                "answer": answer,
                "category": category,
                "source_row_number": source_row,
                "source_quality": source_quality,
            }
        )
    return records


def adapt_relations(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    relations = []
    for row in rows:
        direction = clean(row.get("direction"))
        if direction == "original":
            direction = "direct"
        relations.append(
            {
                "relation_id": clean(row.get("edge_id")),
                "source_relation_id": clean(row.get("source_relation_id") or row.get("relation_id")),
                "source_entity_id": clean(row.get("source_entity_id")),
                "target_entity_id": clean(row.get("target_entity_id")),
                "relation_type": clean(row.get("graph_relation_type")),
                "confidence": safe_float(row.get("confidence")),
                "qa_id": clean(row.get("qa_id")),
                "evidence": clean(row.get("evidence")),
                "direction": direction,
            }
        )
    return relations


def duplicate_values(rows: list[dict[str, Any]], key: str) -> list[str]:
    values = [clean(row.get(key)) for row in rows if clean(row.get(key))]
    counts = Counter(values)
    return sorted(value for value, count in counts.items() if count > 1)


def validate(records: FinalGraphRecords) -> ValidationResult:
    result = ValidationResult()
    entity_ids = {row["entity_id"] for row in records.entities}
    qa_ids = {row["qa_id"] for row in records.qa_records}

    for label, rows, key in (
        ("entity", records.entities, "entity_id"),
        ("mention", records.mentions, "mention_id"),
        ("QA", records.qa_records, "qa_id"),
        ("relation", records.medical_relations, "relation_id"),
    ):
        duplicates = duplicate_values(rows, key)
        if duplicates:
            result.errors.append(f"Duplicate {label} IDs: {duplicates[:10]}")

    for mention in records.mentions:
        if mention["entity_id"] not in entity_ids:
            result.errors.append(f"Mention {mention['mention_id']} has missing entity {mention['entity_id']}")
        if mention["qa_id"] not in qa_ids:
            result.errors.append(f"Mention {mention['mention_id']} has missing QA {mention['qa_id']}")

    for relation in records.medical_relations:
        if relation["source_entity_id"] not in entity_ids or relation["target_entity_id"] not in entity_ids:
            result.errors.append(f"Relation {relation['relation_id']} has a missing endpoint")
        if relation["qa_id"] not in qa_ids:
            result.errors.append(f"Relation {relation['relation_id']} has missing QA {relation['qa_id']}")
        if relation["direction"] not in {"direct", "inverse"}:
            result.errors.append(f"Relation {relation['relation_id']} has invalid direction {relation['direction']}")

    evidence_only = sum(row["source_quality"] == "mention_evidence" for row in records.qa_records)
    if evidence_only:
        result.warnings.append(f"QA records reconstructed from mention evidence: {evidence_only}")
    return result


def load_final_graph_records() -> tuple[FinalGraphRecords, ValidationResult]:
    entities = adapt_entities(read_csv(ENTITY_SOURCE))
    mentions = adapt_mentions(read_csv(MENTION_SOURCE))
    relations = adapt_relations(read_csv(RELATION_SOURCE))
    qa_records = build_qa_records(mentions, relations, read_csv(QA_5K_SOURCE))
    records = FinalGraphRecords(
        entities=entities,
        mentions=mentions,
        qa_records=qa_records,
        medical_relations=relations,
    )
    return records, validate(records)


def main() -> int:
    records, validation = load_final_graph_records()
    print("Final graph adapter validation")
    print(f"entities: {len(records.entities)}")
    print(f"mentions: {len(records.mentions)}")
    print(f"qa_records: {len(records.qa_records)}")
    print(f"medical_relations: {len(records.medical_relations)}")
    print(f"validation_errors: {len(validation.errors)}")
    print(f"validation_warnings: {len(validation.warnings)}")
    for warning in validation.warnings:
        print(f"warning: {warning}")
    print(f"status: {'ok' if validation.ok else 'failed'}")
    return 0 if validation.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
