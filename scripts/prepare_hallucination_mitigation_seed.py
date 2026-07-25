"""Prepare a silver mitigation seed set from the frozen 100-query audit.

This output is useful for schema design, prompt-error analysis, and a future
fine-tuning pipeline. It must not be used to train a model that is then evaluated
on the same evaluation-v1 questions.

Real SFT/DPO training examples must be generated from a disjoint AHD training
cohort and reviewed before model training.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RUN_ID = "full_pipeline_retrieval_v2_targeted_fts_reranked_network_v1"
DEFAULT_INPUT = (
    ROOT
    / "outputs"
    / "evaluation"
    / "generation"
    / RUN_ID
    / "full_pipeline.jsonl"
)
DEFAULT_OUTPUT = ROOT / "data" / "training" / "hallucination_mitigation_seed_v1"


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL at {path}:{line_number}") from exc
    return records


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    temporary.replace(path)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def clean(value: Any) -> str:
    return str(value or "").strip()


def contexts(row: dict[str, Any]) -> list[dict[str, Any]]:
    items = (((row.get("raw") or {}).get("context") or {}).get("evidence_items") or [])
    return [
        {
            "evidence_id": clean(item.get("evidence_id")),
            "qa_id": clean(item.get("qa_id")),
            "evidence": clean(item.get("evidence")),
            "source_quality": clean(item.get("source_quality")),
        }
        for item in items
    ]


def shared_metadata(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "query_id": clean(row.get("query_id")),
        "query": clean(row.get("query")),
        "reference_answer": clean((row.get("gold") or {}).get("reference_answer")),
        "contexts": contexts(row),
        "source_run_id": RUN_ID,
        "annotation_status": "silver_pipeline_verification",
        "permitted_use": "schema_design_error_analysis_and_human_review_only",
        "prohibited_use": (
            "do_not_train_then_evaluate_on_evaluation_v1; create a disjoint "
            "AHD training cohort first"
        ),
    }


def claim_records(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for row in rows:
        metadata = shared_metadata(row)
        for index, verification in enumerate(
            ((row.get("raw") or {}).get("verifications") or []),
            start=1,
        ):
            claim_payload = verification.get("claim") or {}
            records.append(
                {
                    **metadata,
                    "example_id": f"{metadata['query_id']}:claim:{index:03d}",
                    "claim": clean(claim_payload.get("claim")),
                    "citations": list(claim_payload.get("citations") or []),
                    "label": clean(verification.get("status")),
                    "support_score": float(verification.get("support_score") or 0.0),
                    "question_relevance": float(
                        verification.get("question_relevance") or 0.0
                    ),
                    "query_concept_coverage": float(
                        verification.get("query_concept_coverage") or 0.0
                    ),
                    "valid_citations": list(verification.get("valid_citations") or []),
                    "failed_checks": list(verification.get("failed_checks") or []),
                    "best_evidence_id": clean(verification.get("best_evidence_id")),
                    "reason": clean(verification.get("reason")),
                    "task": "claim_support_classification",
                }
            )
    return records


def preference_records(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for row in rows:
        raw_generated = ((row.get("raw") or {}).get("generated") or {})
        mitigated = ((row.get("raw") or {}).get("mitigated") or {})
        rejected = clean(raw_generated.get("answer"))
        chosen = clean(mitigated.get("answer") or row.get("answer"))
        removed_claims = list(mitigated.get("removed_claims") or [])
        if not rejected or not chosen or rejected == chosen or not removed_claims:
            continue
        records.append(
            {
                **shared_metadata(row),
                "example_id": f"{clean(row.get('query_id'))}:preference",
                "task": "grounded_answer_preference",
                "chosen": chosen,
                "rejected": rejected,
                "removed_claims": removed_claims,
                "preference_reason": (
                    "The chosen answer removes claims that failed evidence and "
                    "query-relevance verification."
                ),
            }
        )
    return records


def sft_records(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for row in rows:
        if not row.get("output_claims"):
            continue
        records.append(
            {
                **shared_metadata(row),
                "example_id": f"{clean(row.get('query_id'))}:sft",
                "task": "evidence_grounded_answer_generation",
                "target_answer": clean(row.get("answer")),
                "target_claims": list(row.get("output_claims") or []),
                "answerability": clean(row.get("answerability")),
                "reliability_score": float(
                    (((row.get("raw") or {}).get("reliability") or {}).get("score"))
                    or 0.0
                ),
            }
        )
    return records


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Prepare silver hallucination-mitigation seed data."
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    if hasattr(__import__("sys").stdout, "reconfigure"):
        __import__("sys").stdout.reconfigure(encoding="utf-8")
    input_path = args.input.resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    rows = load_jsonl(input_path)
    if len(rows) != 100:
        raise ValueError(f"Expected frozen 100-query run, found {len(rows)}.")

    claims = claim_records(rows)
    preferences = preference_records(rows)
    sft = sft_records(rows)
    write_jsonl(output_dir / "claim_support_seed.jsonl", claims)
    write_jsonl(output_dir / "answer_preference_seed.jsonl", preferences)
    write_jsonl(output_dir / "grounded_answer_sft_seed.jsonl", sft)

    claim_labels = Counter(record["label"] for record in claims)
    failure_reasons = Counter(
        reason for record in claims for reason in record["failed_checks"]
    )
    manifest = {
        "dataset_version": "hallucination_mitigation_seed_v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_run_id": RUN_ID,
        "source_path": str(input_path.relative_to(ROOT)),
        "source_sha256": sha256(input_path),
        "source_queries": len(rows),
        "annotation_status": "silver_pipeline_verification",
        "claim_examples": len(claims),
        "claim_label_counts": dict(claim_labels),
        "preference_examples": len(preferences),
        "sft_examples": len(sft),
        "failure_reason_counts": dict(failure_reasons.most_common()),
        "evaluation_leakage_warning": (
            "These examples come from evaluation-v1. They are seed/error-analysis "
            "data only. Do not train on them and report evaluation-v1 as held-out."
        ),
        "required_next_dataset": (
            "Generate and human-review equivalent examples from disjoint AHD "
            "graph_train questions before SFT, DPO, or LoRA training."
        ),
    }
    write_json(output_dir / "manifest.json", manifest)
    print(
        json.dumps(
            {
                "status": "ok",
                "claim_examples": len(claims),
                "preference_examples": len(preferences),
                "sft_examples": len(sft),
                "output_dir": str(output_dir.relative_to(ROOT)),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
