from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from scripts.prepare_evaluation_annotations import CLAIM_COLUMNS, ROOT


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records = []
    with path.open("r", encoding="utf-8-sig") as handle:
        for line_number, line in enumerate(handle, start=1):
            if line.strip():
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    raise ValueError(f"Invalid JSON at {path}:{line_number}") from exc
    return records


def annotation_rows(run_directory: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in sorted(run_directory.glob("*.jsonl")):
        mode = path.stem
        for record in read_jsonl(path):
            query_id = str(record.get("query_id") or "")
            response_text = str(record.get("answer") or "")
            claims = record.get("output_claims") or []
            for index, claim in enumerate(claims, start=1):
                if not isinstance(claim, dict):
                    continue
                rows.append(
                    {
                        "query_id": query_id,
                        "mode": mode,
                        "claim_id": f"{query_id}_{mode}_c{index:02d}",
                        "claim_text": str(claim.get("claim") or "").strip(),
                        "response_text": response_text,
                        "cited_evidence_ids": "|".join(str(item) for item in claim.get("citations") or []),
                        "cited_qa_ids": "|".join(str(item) for item in claim.get("source_qa_ids") or []),
                        "human_support_label": "",
                        "human_citation_valid": "",
                        "human_medical_correctness": "",
                        "human_hallucination_label": "",
                        "harm_severity": "",
                        "annotator_id": "",
                        "annotation_timestamp_utc": "",
                        "adjudication_status": "pending_human_annotation",
                        "adjudicator_id": "",
                        "annotation_notes": "",
                    }
                )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert generation raw outputs into a blank human claim-review sheet.")
    parser.add_argument("--generation-run", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    run_directory = args.generation_run.resolve()
    if not run_directory.is_dir():
        raise FileNotFoundError(f"Generation run directory not found: {run_directory}")
    output = args.output or (
        ROOT / "data" / "evaluation" / f"human_claim_annotations_{run_directory.name}.csv"
    )
    output = output.resolve()
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite claim annotation file: {output}")
    rows = annotation_rows(run_directory)
    if not rows:
        raise RuntimeError("No output claims were found in the generation run.")
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CLAIM_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps({"status": "ok", "claim_count": len(rows), "output": str(output)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
