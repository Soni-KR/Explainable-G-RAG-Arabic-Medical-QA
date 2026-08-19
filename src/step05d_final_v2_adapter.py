"""Read and validate the frozen final_v2 CSV contract for Neo4j import."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.config import ROOT_DIR
from src.step05a_final_graph_adapter import (
    FinalGraphRecords,
    ValidationResult,
    adapt_entities,
    adapt_mentions,
    adapt_relations,
    clean,
    read_csv,
    validate,
)


FINAL_V2_DIR = ROOT_DIR / "outputs" / "final_graph_v2"
ENTITY_SOURCE = FINAL_V2_DIR / "entities.csv"
MENTION_SOURCE = FINAL_V2_DIR / "entity_mentions.csv"
QA_SOURCE = FINAL_V2_DIR / "qa_records.csv"
RELATION_SOURCE = FINAL_V2_DIR / "relations_bidirectional.csv"
MANIFEST_SOURCE = FINAL_V2_DIR / "graph_manifest.json"


def adapt_qa_records(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    return [
        {
            "qa_id": clean(row.get("qa_id")),
            "question": clean(row.get("question")),
            "answer": clean(row.get("answer")),
            "category": clean(row.get("category")),
            "source_row_number": clean(row.get("source_row_number")),
            "source_quality": clean(row.get("source_quality")),
        }
        for row in rows
    ]


def load_final_v2_records() -> tuple[FinalGraphRecords, ValidationResult]:
    if not MANIFEST_SOURCE.exists():
        raise FileNotFoundError(MANIFEST_SOURCE)
    manifest = json.loads(MANIFEST_SOURCE.read_text(encoding="utf-8"))
    if manifest.get("graph_version") != "final_v2":
        raise ValueError("The graph manifest is not final_v2.")

    records = FinalGraphRecords(
        entities=adapt_entities(read_csv(ENTITY_SOURCE)),
        mentions=adapt_mentions(read_csv(MENTION_SOURCE)),
        qa_records=adapt_qa_records(read_csv(QA_SOURCE)),
        medical_relations=adapt_relations(read_csv(RELATION_SOURCE)),
    )
    result = validate(records)
    expected = manifest.get("counts", {})
    actual = {
        "entities": len(records.entities),
        "entity_mentions": len(records.mentions),
        "qa_records": len(records.qa_records),
        "bidirectional_relations": len(records.medical_relations),
    }
    for name, count in actual.items():
        if int(expected.get(name, -1)) != count:
            result.errors.append(
                f"Manifest count mismatch for {name}: expected {expected.get(name)}, read {count}"
            )
    return records, result


def main() -> int:
    records, validation = load_final_v2_records()
    print("Final v2 graph adapter validation")
    print(f"entities: {len(records.entities)}")
    print(f"mentions: {len(records.mentions)}")
    print(f"qa_records: {len(records.qa_records)}")
    print(f"medical_relations: {len(records.medical_relations)}")
    print(f"validation_errors: {len(validation.errors)}")
    print(f"validation_warnings: {len(validation.warnings)}")
    print(f"status: {'ok' if validation.ok else 'failed'}")
    return 0 if validation.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
