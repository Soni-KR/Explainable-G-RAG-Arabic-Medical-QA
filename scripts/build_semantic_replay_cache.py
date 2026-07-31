from __future__ import annotations

"""Re-key saved semantic decisions for an offline verifier replay.

The script reads only model decision columns from a completed predictions CSV.
Human labels and expected decisions are neither read nor copied into the cache.
"""

import argparse
import csv
import json
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.config import load_final_config
from src.models import AnswerClaim, ClaimVerification, EvidenceContextBundle
from src.step14_semantic_adjudication import (
    adjudication_fingerprint,
    build_adjudication_cases,
)
from src.step14_verify_claims_v5 import apply_v5_hard_gates


DECISION_COLUMNS = {
    "query_id",
    "claim",
    "predicted_evidence_support",
    "predicted_query_relevance",
    "predicted_intent_match",
    "predicted_concept_match",
    "predicted_anatomy_match",
    "predicted_answer_contribution",
    "predicted_clinical_relation_preserved",
    "predicted_named_entity_identity_preserved",
    "predicted_patient_context_compatible",
    "predicted_should_retain",
    "reason",
}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8-sig") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def read_decisions(path: Path) -> dict[tuple[str, str], dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = DECISION_COLUMNS - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Predictions file lacks decision columns: {missing}")
        decisions: dict[tuple[str, str], dict[str, str]] = {}
        for raw in reader:
            # Copy only the model-output allowlist. Human columns in the source
            # file are intentionally ignored.
            row = {field: str(raw.get(field) or "") for field in DECISION_COLUMNS}
            key = (row["query_id"], row["claim"])
            if not all(key) or key in decisions:
                raise ValueError(f"Duplicate or blank decision key: {key}")
            decisions[key] = row
    return decisions


def verification_from_dict(payload: dict[str, Any]) -> ClaimVerification:
    values = dict(payload)
    values["claim"] = AnswerClaim(**dict(values["claim"]))
    return ClaimVerification(**values)


def as_bool(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized not in {"yes", "no"}:
        raise ValueError(f"Malformed saved boolean decision: {value!r}")
    return normalized == "yes"


def response_decision(
    claim_id: str,
    row: dict[str, str],
) -> dict[str, Any]:
    if row["predicted_evidence_support"] == "not_adjudicated":
        raise ValueError(
            f"Current semantic case was not adjudicated in saved decisions: "
            f"{row['query_id']} / {row['claim']}"
        )
    return {
        "claim_id": claim_id,
        "evidence_support": row["predicted_evidence_support"],
        "query_relevance": row["predicted_query_relevance"],
        "intent_match": as_bool(row["predicted_intent_match"]),
        "concept_match": as_bool(row["predicted_concept_match"]),
        "anatomy_match": row["predicted_anatomy_match"],
        "answer_contribution": row["predicted_answer_contribution"],
        "clinical_relation_preserved": as_bool(
            row["predicted_clinical_relation_preserved"]
        ),
        "named_entity_identity_preserved": as_bool(
            row["predicted_named_entity_identity_preserved"]
        ),
        "patient_context_compatible": as_bool(
            row["predicted_patient_context_compatible"]
        ),
        "should_retain": as_bool(row["predicted_should_retain"]),
        "reason": row["reason"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build a zero-API replay cache from saved model decisions."
    )
    parser.add_argument("--source-run", type=Path, required=True)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model", default="openai/gpt-oss-20b")
    parser.add_argument(
        "--prompt-version",
        default="semantic_claim_adjudication_v2",
    )
    args = parser.parse_args()

    source_rows = read_jsonl(args.source_run.resolve())
    saved = read_decisions(args.predictions.resolve())
    config = load_final_config()
    adjudication_config = replace(
        config.claim_adjudication,
        enabled=True,
        model=args.model,
        prompt_version=args.prompt_version,
    )

    cache_rows: list[dict[str, Any]] = []
    cached_claims = 0
    for source in source_rows:
        query_id = str(source.get("query_id") or "")
        raw = dict(source.get("raw") or {})
        context = EvidenceContextBundle(**dict(raw["context"]))
        verifications = [
            verification_from_dict(item)
            for item in raw.get("verifications", [])
            if (
                query_id,
                str(dict(item.get("claim") or {}).get("claim") or ""),
            )
            in saved
        ]
        hardened, _ = apply_v5_hard_gates(verifications, context)
        cases, verification_by_id = build_adjudication_cases(
            hardened,
            context,
        )
        if not cases:
            continue
        decisions: list[dict[str, Any]] = []
        for case in cases:
            claim_id = str(case["claim_id"])
            claim = verification_by_id[claim_id].claim.claim
            row = saved.get((query_id, claim))
            if row is None:
                raise ValueError(
                    f"No saved model decision for {query_id} / {claim}"
                )
            decisions.append(response_decision(claim_id, row))
        fingerprint = adjudication_fingerprint(
            context,
            cases,
            adjudication_config,
        )
        cache_rows.append(
            {
                "fingerprint": fingerprint,
                "status": "ok",
                "query": context.query,
                "model": args.model,
                "prompt_version": args.prompt_version,
                "response": {"decisions": decisions},
            }
        )
        cached_claims += len(decisions)

    output = args.output.resolve()
    if output.exists():
        raise FileExistsError(f"Output already exists: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="\n") as handle:
        for row in cache_rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(
        json.dumps(
            {
                "status": "ok",
                "cache_rows": len(cache_rows),
                "cached_claims": cached_claims,
                "human_label_columns_read": False,
                "network_used": False,
                "output": str(output),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
