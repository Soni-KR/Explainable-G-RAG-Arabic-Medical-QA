from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from scripts.evaluation_common import parse_id_list, parse_optional_bool
from scripts.prepare_evaluation_annotations import CLAIM_ANNOTATIONS_CSV, RETRIEVAL_ANNOTATIONS_CSV


PROVISIONAL_STATUS = "provisional_dataset_annotation"
RETRIEVAL_STATUSES = {"pending_human_annotation", PROVISIONAL_STATUS, "annotated", "adjudicated"}
SUPPORT_LABELS = {"supported", "partially_supported", "unsupported", "not_verifiable"}
CITATION_LABELS = {"yes", "no", "not_applicable"}
CORRECTNESS_LABELS = {"correct", "incorrect", "uncertain"}
HALLUCINATION_LABELS = {"yes", "no", "uncertain"}
SEVERITY_LABELS = {"none", "low", "medium", "high"}
CLAIM_STATUSES = {"pending_human_annotation", PROVISIONAL_STATUS, "annotated", "adjudicated"}


def rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def validate_retrieval(path: Path) -> dict[str, int]:
    errors = []
    seen = set()
    completed = 0
    pending = 0
    provisional = 0
    for line_number, row in enumerate(rows(path), start=2):
        query_id = str(row.get("query_id") or "").strip()
        status = str(row.get("annotation_status") or "").strip()
        if not query_id or query_id in seen:
            errors.append(f"line {line_number}: missing or duplicate query_id")
        seen.add(query_id)
        if status not in RETRIEVAL_STATUSES:
            errors.append(f"line {line_number}: invalid annotation_status")
            continue
        if status == "pending_human_annotation":
            pending += 1
            continue
        if status == PROVISIONAL_STATUS:
            provisional += 1
            continue
        completed += 1
        if not str(row.get("annotator_id") or "").strip():
            errors.append(f"line {line_number}: completed row requires annotator_id")
        try:
            answerable = parse_optional_bool(row.get("answerable_from_final_graph"))
        except ValueError as exc:
            errors.append(f"line {line_number}: {exc}")
            continue
        if answerable is None:
            errors.append(f"line {line_number}: completed row requires answerable_from_final_graph")
        gold_ids = [
            *parse_id_list(row.get("gold_entity_ids")),
            *parse_id_list(row.get("gold_evidence_ids")),
            *parse_id_list(row.get("gold_qa_ids")),
            *parse_id_list(row.get("gold_relation_ids")),
        ]
        if answerable is True and not gold_ids:
            errors.append(f"line {line_number}: answerable row requires at least one gold ID")
        if status == "adjudicated" and not str(row.get("adjudicator_id") or "").strip():
            errors.append(f"line {line_number}: adjudicated row requires adjudicator_id")
    if errors:
        raise ValueError("Retrieval annotation errors:\n- " + "\n- ".join(errors))
    return {"rows": len(seen), "completed": completed, "provisional": provisional, "pending": pending}


def validate_claims(path: Path) -> dict[str, int]:
    errors = []
    seen = set()
    completed = 0
    pending = 0
    provisional = 0
    for line_number, row in enumerate(rows(path), start=2):
        claim_id = str(row.get("claim_id") or "").strip()
        status = str(row.get("adjudication_status") or "").strip()
        if not claim_id or claim_id in seen:
            errors.append(f"line {line_number}: missing or duplicate claim_id")
        seen.add(claim_id)
        if status not in CLAIM_STATUSES:
            errors.append(f"line {line_number}: invalid adjudication_status")
            continue
        if status == "pending_human_annotation":
            pending += 1
            continue
        if status == PROVISIONAL_STATUS:
            provisional += 1
            continue
        completed += 1
        checks = (
            ("human_support_label", SUPPORT_LABELS),
            ("human_citation_valid", CITATION_LABELS),
            ("human_medical_correctness", CORRECTNESS_LABELS),
            ("human_hallucination_label", HALLUCINATION_LABELS),
            ("harm_severity", SEVERITY_LABELS),
        )
        for field, allowed in checks:
            if str(row.get(field) or "").strip() not in allowed:
                errors.append(f"line {line_number}: invalid {field}")
        if not str(row.get("annotator_id") or "").strip():
            errors.append(f"line {line_number}: completed row requires annotator_id")
        if status == "adjudicated" and not str(row.get("adjudicator_id") or "").strip():
            errors.append(f"line {line_number}: adjudicated row requires adjudicator_id")
    if errors:
        raise ValueError("Claim annotation errors:\n- " + "\n- ".join(errors))
    return {"rows": len(seen), "completed": completed, "provisional": provisional, "pending": pending}


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate independent human evaluation annotations.")
    parser.add_argument("--retrieval-file", type=Path, default=RETRIEVAL_ANNOTATIONS_CSV)
    parser.add_argument("--claim-file", type=Path, default=CLAIM_ANNOTATIONS_CSV)
    args = parser.parse_args()
    payload = {
        "retrieval": validate_retrieval(args.retrieval_file.resolve()),
        "claims": validate_claims(args.claim_file.resolve()),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
