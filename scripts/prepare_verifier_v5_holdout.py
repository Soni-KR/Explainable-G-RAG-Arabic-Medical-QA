from __future__ import annotations

"""Build a blank, query-grouped human holdout from cached v3.1 claims.

The script exports every pre-mitigation claim from the supplied runs. Existing
verifier decisions are retained only as audit metadata and never copied into a
human label field.
"""

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
HUMAN_FIELDS = (
    "human_evidence_support",
    "human_query_relevance",
    "human_intent_match",
    "human_concept_match",
    "human_anatomy_match",
    "human_numbers_durations_preserved",
    "human_negation_safety_preserved",
    "human_clinical_relation_preserved",
    "human_recommendation_supported",
    "human_same_clinical_scenario",
    "human_should_retain",
    "human_error_reason",
    "human_notes",
    "annotator_id",
    "adjudicator_id",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a blank verifier-v5 human claim holdout."
    )
    parser.add_argument(
        "--run",
        type=Path,
        action="append",
        required=True,
        help="Completed generation directory or full_pipeline.jsonl.",
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--fold-count", type=int, default=5)
    return parser.parse_args()


def resolve_run(path: Path) -> Path:
    resolved = path if path.is_absolute() else ROOT / path
    if resolved.is_dir():
        resolved = resolved / "full_pipeline.jsonl"
    if not resolved.exists():
        raise FileNotFoundError(f"Generation run not found: {resolved}")
    return resolved.resolve()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8-sig") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def stable_fold(query_id: str, fold_count: int) -> int:
    digest = hashlib.sha256(query_id.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big") % fold_count + 1


def stable_claim_id(cohort: str, query_id: str, index: int, claim: str) -> str:
    payload = f"{cohort}|{query_id}|{index}|{claim}".encode("utf-8")
    return "v5hold_" + hashlib.sha256(payload).hexdigest()[:16]


def cited_evidence(
    record: dict[str, Any], citations: list[str]
) -> tuple[str, str]:
    context = dict((record.get("raw") or {}).get("context") or {})
    by_id = {
        str(item.get("evidence_id") or ""): item
        for item in context.get("evidence_items") or []
    }
    items = [by_id[item] for item in citations if item in by_id]
    evidence = "\n---\n".join(str(item.get("evidence") or "") for item in items)
    qa_ids = " | ".join(
        sorted(
            {
                str(item.get("qa_id") or "")
                for item in items
                if item.get("qa_id")
            }
        )
    )
    return evidence, qa_ids


def review_focus(status: str, failed_checks: list[str]) -> str:
    focus: list[str] = []
    failures = set(failed_checks)
    if failures and failures <= {
        "intent_mismatch",
        "claim_query_concept_mismatch",
    }:
        focus.append("possible_valid_paraphrase")
    if status == "weakly_supported":
        focus.append("partial_but_useful")
    mappings = {
        "anatomy_mismatch": "anatomy_or_laterality",
        "number_mismatch": "dose_number_or_duration",
        "negation_mismatch": "negation_or_safety_condition",
        "recommendation_not_supported": "unsupported_recommendation",
        "intent_mismatch": "clinical_relation_or_intent",
        "claim_query_concept_mismatch": "wrong_disease_or_symptom",
        "support_below_weak_threshold": "different_clinical_scenario",
    }
    for failure, label in mappings.items():
        if failure in failures:
            focus.append(label)
    # Named-drug/disease identity and scenario compatibility always need human
    # inspection even when no deterministic check explicitly fired.
    focus.extend(("drug_disease_identity", "same_clinical_scenario"))
    return " | ".join(dict.fromkeys(focus))


def claim_rows(
    run_file: Path,
    cohort: str,
    fold_count: int,
) -> list[dict[str, Any]]:
    records = load_jsonl(run_file)
    if len(records) != 100:
        raise ValueError(
            f"{cohort} must contain exactly 100 queries; found {len(records)}."
        )
    output: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for record in records:
        query_id = str(record.get("query_id") or "")
        raw = dict(record.get("raw") or {})
        claims = list(raw.get("claims") or [])
        verifications = list(raw.get("verifications") or [])
        if len(claims) != len(verifications):
            raise ValueError(
                f"{query_id}: claims/verifications length mismatch "
                f"({len(claims)} != {len(verifications)})."
            )
        for index, (claim, verification) in enumerate(
            zip(claims, verifications, strict=True),
            start=1,
        ):
            claim_text = str(claim.get("claim") or "")
            claim_id = stable_claim_id(
                cohort, query_id, index, claim_text
            )
            if claim_id in seen_ids:
                raise ValueError(f"Duplicate stable claim ID: {claim_id}")
            seen_ids.add(claim_id)
            citations = [str(item) for item in claim.get("citations") or []]
            evidence, qa_ids = cited_evidence(record, citations)
            failed_checks = [
                str(item) for item in verification.get("failed_checks") or []
            ]
            row: dict[str, Any] = {
                "claim_id": claim_id,
                "query_fold": stable_fold(query_id, fold_count),
                "cohort": cohort,
                "query_id": query_id,
                "query": str(record.get("query") or ""),
                "reference_answer": str(
                    (record.get("gold") or {}).get("reference_answer") or ""
                ),
                "claim": claim_text,
                "citations": " | ".join(citations),
                "cited_qa_ids": qa_ids,
                "cited_evidence": evidence,
                "deterministic_status": str(
                    verification.get("status") or ""
                ),
                "support_score": verification.get("support_score", ""),
                "question_relevance": verification.get(
                    "question_relevance", ""
                ),
                "query_concept_coverage": verification.get(
                    "query_concept_coverage", ""
                ),
                "failed_checks": " | ".join(failed_checks),
                "review_focus": review_focus(
                    str(verification.get("status") or ""), failed_checks
                ),
                "annotation_status": "pending_human_annotation",
            }
            row.update({field: "" for field in HUMAN_FIELDS})
            output.append(row)
    return output


def annotation_guide() -> str:
    return """# Verifier v5 Claim Holdout

Review every row using only the question, claim, and cited evidence. The AHD
reference answer is context for medical intent, not automatic proof that the
claim is supported by its citation.

## Labels

- Evidence support: `yes`, `partial`, or `no`.
- Query relevance and each preservation field: `yes`, `no`, or `not_applicable`.
- Should retain: `yes` only when the claim is evidence-supported, answers the
  query, preserves entity/anatomy/number/negation/relation details, and makes no
  unsupported recommendation.
- Error reason: use one or more of `wrong_drug`, `wrong_disease`,
  `wrong_symptom`, `wrong_anatomy`, `wrong_laterality`, `number_or_duration`,
  `negation_or_safety`, `changed_relation`, `unsupported_recommendation`,
  `different_clinical_scenario`, `irrelevant`, `insufficient_evidence`, or
  `other`.

## Leakage Control

All claims sharing a `query_id` have the same `query_fold`. Never split rows
from one query across training and evaluation. Deterministic verifier status,
scores, failed checks, and `review_focus` are audit metadata only; annotators
must not copy them into human labels.

The prior 81 suspected false rejections are not included as holdout truth.
"""


def main() -> int:
    args = parse_args()
    if args.fold_count < 2:
        raise ValueError("fold-count must be at least 2.")
    output_dir = (
        args.output_dir
        if args.output_dir.is_absolute()
        else ROOT / args.output_dir
    ).resolve()
    if output_dir.exists():
        raise FileExistsError(
            f"Refusing to overwrite holdout directory: {output_dir}"
        )

    run_files = [resolve_run(path) for path in args.run]
    rows: list[dict[str, Any]] = []
    for run_file in run_files:
        cohort = run_file.parent.name
        rows.extend(claim_rows(run_file, cohort, args.fold_count))
    if not 200 <= len(rows) <= 300:
        raise ValueError(
            f"Holdout must contain 200-300 claims; found {len(rows)}."
        )
    claim_ids = [str(row["claim_id"]) for row in rows]
    if len(claim_ids) != len(set(claim_ids)):
        raise ValueError("Holdout contains duplicate claim IDs.")

    output_dir.mkdir(parents=True)
    csv_path = output_dir / "claims_pending_human_review.csv"
    fields = list(rows[0])
    with csv_path.open("x", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    (output_dir / "ANNOTATION_GUIDE.md").write_text(
        annotation_guide(), encoding="utf-8"
    )
    status_counts = Counter(str(row["deterministic_status"]) for row in rows)
    fold_counts = Counter(str(row["query_fold"]) for row in rows)
    manifest = {
        "status": "pending_human_annotation",
        "claim_count": len(rows),
        "query_count": len({str(row["query_id"]) for row in rows}),
        "query_grouped_folds": args.fold_count,
        "fold_claim_counts": dict(sorted(fold_counts.items())),
        "deterministic_status_counts_are_metadata_only": dict(
            sorted(status_counts.items())
        ),
        "source_runs": [
            str(path.relative_to(ROOT)).replace("\\", "/")
            for path in run_files
        ],
        "prior_81_labels_included": False,
        "human_label_fields_blank": all(
            not str(row[field]).strip()
            for row in rows
            for field in HUMAN_FIELDS
        ),
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(manifest, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
