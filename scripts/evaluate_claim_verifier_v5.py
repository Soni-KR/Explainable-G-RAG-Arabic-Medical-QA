from __future__ import annotations

"""Offline audit for the opt-in hard/soft Verifier v5 profile.

This script never calls an API and never rewrites an existing run. It applies
the v5 hard gates to saved deterministic verification records, then reports:

- which of the 81 human-reviewed disputes remain semantically eligible;
- how the prior 20B pilot would change after the hard gates; and
- which claims in the v3.1 generation pilot trigger new hard failures.
"""

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.models import (
    AnswerClaim,
    ClaimVerification,
    EvidenceContextBundle,
)
from src.step14_verify_claims_v5 import apply_v5_hard_gates


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REVIEW = (
    ROOT
    / "outputs"
    / "evaluation"
    / "entity_gt_trial_100"
    / "known_answer_diagnosis"
    / "known_answer_removed_claim_review_queue_human_reviewed.csv"
)
DEFAULT_SOURCE = (
    ROOT
    / "outputs"
    / "evaluation"
    / "generation"
    / "entity_gt_trial_100_known_answer_generation_v1"
    / "full_pipeline.jsonl"
)
DEFAULT_SEMANTIC_PILOT = (
    ROOT
    / "outputs"
    / "evaluation"
    / "claim_verifier"
    / "semantic_claim_adjudication_pilot_v2"
    / "predictions.csv"
)
DEFAULT_V31_PILOT = (
    ROOT
    / "outputs"
    / "evaluation"
    / "generation"
    / "dev_v3_1_frozen_context_10q_20260729"
    / "full_pipeline.jsonl"
)
DEFAULT_OUTPUT = (
    ROOT
    / "outputs"
    / "evaluation"
    / "claim_verifier"
    / "verifier_v5_offline_audit"
)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8-sig") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0]) if rows else []
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        if fieldnames:
            writer.writeheader()
            writer.writerows(rows)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def verification_from_dict(payload: dict[str, Any]) -> ClaimVerification:
    values = dict(payload)
    values["claim"] = AnswerClaim(**dict(values["claim"]))
    return ClaimVerification(**values)


def source_records_by_query(
    records: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    return {
        str(row.get("query_id") or ""): row
        for row in records
        if str(row.get("query_id") or "")
    }


def find_verification(
    source: dict[str, Any],
    claim: str,
) -> ClaimVerification:
    for payload in dict(source.get("raw") or {}).get("verifications", []):
        if str(dict(payload.get("claim") or {}).get("claim") or "") == claim:
            return verification_from_dict(payload)
    raise ValueError(
        f"Could not match reviewed claim for {source.get('query_id')}: {claim}"
    )


def human_label(value: str) -> bool:
    return value.strip().lower() == "yes"


def confusion(rows: list[dict[str, Any]], prediction_field: str) -> dict[str, Any]:
    tp = sum(row["human_should_retain"] and row[prediction_field] for row in rows)
    tn = sum(
        not row["human_should_retain"] and not row[prediction_field]
        for row in rows
    )
    fp = sum(
        not row["human_should_retain"] and row[prediction_field]
        for row in rows
    )
    fn = sum(
        row["human_should_retain"] and not row[prediction_field]
        for row in rows
    )
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    specificity = tn / (tn + fp) if tn + fp else 0.0
    return {
        "claims": len(rows),
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn,
        "precision": round(precision, 6),
        "recall": round(recall, 6),
        "specificity": round(specificity, 6),
    }


def build_review_audit(
    review_rows: list[dict[str, str]],
    source_by_query: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    audit: list[dict[str, Any]] = []
    for human in review_rows:
        query_id = str(human.get("query_id") or "")
        source = source_by_query.get(query_id)
        if source is None:
            raise ValueError(f"Missing source generation record: {query_id}")
        raw = dict(source.get("raw") or {})
        context = EvidenceContextBundle(**dict(raw["context"]))
        verification = find_verification(
            source,
            str(human.get("removed_claim") or ""),
        )
        hardened, gate_rows = apply_v5_hard_gates(
            [verification],
            context,
        )
        gate = gate_rows[0]
        audit.append(
            {
                "query_id": query_id,
                "claim": verification.claim.claim,
                "human_should_retain": human_label(
                    str(human.get("human_should_retain") or "")
                ),
                "original_failed_checks": "|".join(
                    verification.failed_checks
                ),
                "v5_hard_failures": "|".join(gate["hard_failures"]),
                "v5_soft_failures": "|".join(gate["soft_failures"]),
                "v5_semantic_eligible": bool(gate["semantic_eligible"]),
                "v5_status_after_hard_gates": hardened[0].status,
                "support_score": verification.support_score,
            }
        )
    return audit


def build_pilot_audit(
    semantic_rows: list[dict[str, str]],
    review_audit: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    review_by_key = {
        (row["query_id"], row["claim"]): row for row in review_audit
    }
    rows: list[dict[str, Any]] = []
    for semantic in semantic_rows:
        key = (
            str(semantic.get("query_id") or ""),
            str(semantic.get("claim") or ""),
        )
        review = review_by_key.get(key)
        if review is None:
            raise ValueError(f"Semantic pilot row has no reviewed claim: {key}")
        original_prediction = human_label(
            str(semantic.get("predicted_should_retain") or "")
        )
        v5_prediction = bool(
            original_prediction
            and review["v5_semantic_eligible"]
            and not review["v5_hard_failures"]
        )
        rows.append(
            {
                **review,
                "v2_predicted_should_retain": original_prediction,
                "v5_gated_predicted_should_retain": v5_prediction,
                "semantic_reason": str(semantic.get("reason") or ""),
            }
        )
    return rows


def build_v31_audit(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source in records:
        raw = dict(source.get("raw") or {})
        if not raw.get("context") or not raw.get("verifications"):
            continue
        context = EvidenceContextBundle(**dict(raw["context"]))
        verifications = [
            verification_from_dict(payload)
            for payload in raw.get("verifications", [])
        ]
        _, gate_rows = apply_v5_hard_gates(verifications, context)
        for verification, gate in zip(verifications, gate_rows):
            rows.append(
                {
                    "query_id": str(source.get("query_id") or ""),
                    "claim": verification.claim.claim,
                    "original_status": verification.status,
                    "support_score": verification.support_score,
                    "v5_hard_failures": "|".join(gate["hard_failures"]),
                    "v5_soft_failures": "|".join(gate["soft_failures"]),
                    "v5_semantic_eligible": bool(
                        gate["semantic_eligible"]
                    ),
                }
            )
    return rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit Verifier v5 against saved, human-reviewed claims."
    )
    parser.add_argument("--review-file", type=Path, default=DEFAULT_REVIEW)
    parser.add_argument("--source-run", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument(
        "--semantic-pilot",
        type=Path,
        default=DEFAULT_SEMANTIC_PILOT,
    )
    parser.add_argument("--v31-pilot", type=Path, default=DEFAULT_V31_PILOT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    review_rows = read_csv(args.review_file)
    source_rows = read_jsonl(args.source_run)
    source_by_query = source_records_by_query(source_rows)
    review_audit = build_review_audit(review_rows, source_by_query)

    semantic_rows = read_csv(args.semantic_pilot)
    pilot_audit = build_pilot_audit(semantic_rows, review_audit)
    v31_audit = build_v31_audit(read_jsonl(args.v31_pilot))

    valid_rows = [
        row for row in review_audit if row["human_should_retain"]
    ]
    invalid_rows = [
        row for row in review_audit if not row["human_should_retain"]
    ]
    metrics = {
        "status": "development_only",
        "api_calls": 0,
        "human_reviewed_claims": len(review_audit),
        "human_valid_claims": len(valid_rows),
        "human_invalid_claims": len(invalid_rows),
        "v5_hard_gate": {
            "valid_claims_blocked": sum(
                bool(row["v5_hard_failures"]) for row in valid_rows
            ),
            "invalid_claims_blocked": sum(
                bool(row["v5_hard_failures"]) for row in invalid_rows
            ),
            "valid_claims_semantically_eligible": sum(
                row["v5_semantic_eligible"] for row in valid_rows
            ),
            "invalid_claims_semantically_eligible": sum(
                row["v5_semantic_eligible"] for row in invalid_rows
            ),
        },
        "prior_20b_pilot": {
            "before_v5": confusion(
                pilot_audit,
                "v2_predicted_should_retain",
            ),
            "after_v5_hard_gates": confusion(
                pilot_audit,
                "v5_gated_predicted_should_retain",
            ),
        },
        "v31_pilot": {
            "claims": len(v31_audit),
            "claims_with_new_hard_failures": sum(
                bool(row["v5_hard_failures"]) for row in v31_audit
            ),
            "clinical_relation_mismatches": sum(
                "clinical_relation_mismatch"
                in row["v5_hard_failures"]
                for row in v31_audit
            ),
        },
        "limitations": [
            "The 81 reviewed disputes are development data, not a fresh test set.",
            "The post-v5 20B result is an offline gate replay, not a new API run.",
            "V5 remains disabled until a fresh claim-level holdout passes.",
        ],
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(args.output_dir / "reviewed_claims_v5_audit.csv", review_audit)
    write_csv(args.output_dir / "pilot_v2_post_v5.csv", pilot_audit)
    write_csv(args.output_dir / "v31_pilot_v5_audit.csv", v31_audit)
    write_json(args.output_dir / "metrics.json", metrics)
    before = metrics["prior_20b_pilot"]["before_v5"]
    after = metrics["prior_20b_pilot"]["after_v5_hard_gates"]
    gates = metrics["v5_hard_gate"]
    v31 = metrics["v31_pilot"]
    (args.output_dir / "README.md").write_text(
        "\n".join(
            [
                "# Verifier v5 Offline Audit",
                "",
                "This is a development-only, zero-API replay.",
                "",
                "The frozen production verifier and all saved v3/v4 runs are unchanged.",
                "V5 adds non-overridable hard gates before optional semantic review.",
                "Only intent/concept relevance disputes can reach semantic review.",
                "",
                "## Human-reviewed development set",
                "",
                f"- Reviewed claims: {len(review_audit)}",
                f"- Human-valid claims: {len(valid_rows)}",
                f"- Human-invalid claims: {len(invalid_rows)}",
                f"- Valid claims hard-blocked: {gates['valid_claims_blocked']}",
                f"- Invalid claims hard-blocked: {gates['invalid_claims_blocked']}",
                (
                    "- Valid claims eligible for semantic review: "
                    f"{gates['valid_claims_semantically_eligible']}"
                ),
                (
                    "- Invalid claims eligible for semantic review: "
                    f"{gates['invalid_claims_semantically_eligible']}"
                ),
                "",
                "## Prior 20B pilot replay",
                "",
                (
                    f"- Before v5: TP={before['tp']}, TN={before['tn']}, "
                    f"FP={before['fp']}, FN={before['fn']}"
                ),
                (
                    f"- After v5 gates: TP={after['tp']}, TN={after['tn']}, "
                    f"FP={after['fp']}, FN={after['fn']}"
                ),
                (
                    f"- Post-gate precision={after['precision']:.4f}, "
                    f"recall={after['recall']:.4f}"
                ),
                "",
                "## V3.1 pilot",
                "",
                f"- Claims audited: {v31['claims']}",
                (
                    "- Claims with new hard failures: "
                    f"{v31['claims_with_new_hard_failures']}"
                ),
                (
                    "- Clinical-relation mismatches caught: "
                    f"{v31['clinical_relation_mismatches']}"
                ),
                "",
                "## Decision",
                "",
                "V5 remains disabled. The apparent zero false-positive pilot result",
                "is useful development evidence, but the same reviewed claims helped",
                "shape the gates. A fresh claim-level holdout is required.",
                "",
                "See `metrics.json` for the aggregate result and the CSV files for",
                "claim-level provenance.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "status": "ok",
                "output_dir": str(args.output_dir),
                "human_reviewed_claims": len(review_audit),
                "semantic_pilot_claims": len(pilot_audit),
                "v31_pilot_claims": len(v31_audit),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
