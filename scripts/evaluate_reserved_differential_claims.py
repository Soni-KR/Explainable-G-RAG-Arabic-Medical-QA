from __future__ import annotations

"""Evaluate the frozen semantic verifier on 50 reserved reviewed claims.

Human labels are used only after inference for scoring. The outbound semantic
payload contains only the question, candidate claim, and its cited evidence.
"""

import argparse
import csv
import hashlib
import json
import sys
from collections import Counter
from dataclasses import asdict, replace
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.config import load_final_config
from src.models import AnswerClaim, ClaimVerification, EvidenceContextBundle
from src.step14_semantic_adjudication import (
    ClaimAdjudicationError,
    ClaimAdjudicationRateLimit,
    SemanticClaimAdjudicator,
    build_adjudication_cases,
)
from src.step14_verify_claims_v5 import apply_v5_hard_gates


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REVIEW = (
    ROOT
    / "outputs"
    / "evaluation"
    / "generation"
    / "evidence_adaptive_v4_2_comparison_200q_20260729"
    / "differential_safety_audit.csv"
)
OUTPUT_ROOT = ROOT / "outputs" / "evaluation" / "claim_verifier"
CACHE_ROOT = ROOT / "outputs" / "evaluation" / "cache"
ALLOWED_REVIEW_DECISIONS = {"safe", "equivalent_to_v3_kept", "unsafe"}


def read_review(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    required = {
        "differential_id",
        "cohort",
        "query_id",
        "query",
        "v4_claim",
        "cited_evidence",
        "evidence_qa_ids",
        "support_score",
        "question_relevance",
        "review_decision",
        "safety_error_types",
    }
    missing = required - set(rows[0] if rows else {})
    if missing:
        raise ValueError(f"Reserved review lacks columns: {sorted(missing)}")
    if len(rows) != 50:
        raise ValueError(f"Expected 50 reserved claims, found {len(rows)}.")
    identifiers = [row["differential_id"].strip() for row in rows]
    if any(not identifier for identifier in identifiers):
        raise ValueError("Reserved review contains a blank differential ID.")
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("Reserved review contains duplicate differential IDs.")
    for line_number, row in enumerate(rows, start=2):
        decision = row["review_decision"].strip()
        if decision not in ALLOWED_REVIEW_DECISIONS:
            raise ValueError(
                f"Invalid review_decision on line {line_number}: {decision!r}"
            )
        if not row["query"].strip() or not row["v4_claim"].strip():
            raise ValueError(f"Blank query or claim on line {line_number}.")
        if not row["cited_evidence"].strip():
            raise ValueError(f"Blank cited evidence on line {line_number}.")
    distribution = Counter(row["review_decision"].strip() for row in rows)
    if distribution != Counter(
        {"safe": 11, "equivalent_to_v3_kept": 26, "unsafe": 13}
    ):
        raise ValueError(
            f"Unexpected reserved-label distribution: {dict(distribution)}"
        )
    return rows


def safe_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def split_values(value: str) -> list[str]:
    return [
        item.strip()
        for item in str(value or "").replace(",", "|").split("|")
        if item.strip()
    ]


def group_rows(rows: list[dict[str, str]]) -> list[list[dict[str, str]]]:
    grouped: dict[tuple[str, str], list[dict[str, str]]] = {}
    for row in rows:
        grouped.setdefault((row["cohort"], row["query_id"]), []).append(row)
    return list(grouped.values())


def build_query_inputs(
    rows: list[dict[str, str]],
) -> tuple[
    EvidenceContextBundle,
    list[ClaimVerification],
    dict[str, dict[str, str]],
]:
    evidence_items: list[dict[str, Any]] = []
    verifications: list[ClaimVerification] = []
    source_by_claim: dict[str, dict[str, str]] = {}
    allowed_qa_ids: list[str] = []
    for index, row in enumerate(rows, start=1):
        evidence_id = f"R{index}"
        qa_ids = split_values(row["evidence_qa_ids"])
        qa_id = qa_ids[0] if qa_ids else ""
        allowed_qa_ids.extend(qa_ids)
        evidence_items.append(
            {
                "evidence_id": evidence_id,
                "qa_id": qa_id,
                "evidence": row["cited_evidence"].strip(),
                "source_answer": row["cited_evidence"].strip(),
                "source_question": "",
                "evidence_origin": "answer",
                "field": "answer",
                "source_quality": "preprocessed_source_row",
                "relation_ids": [],
            }
        )
        claim = row["v4_claim"].strip()
        verifications.append(
            ClaimVerification(
                claim=AnswerClaim(
                    claim=claim,
                    citations=[evidence_id],
                    source_qa_ids=qa_ids,
                ),
                status="unsupported",
                support_score=safe_float(row["support_score"]),
                question_relevance=safe_float(row["question_relevance"]),
                valid_citations=[],
                valid_qa_ids=[],
                best_evidence_id=evidence_id,
                failed_checks=["intent_mismatch"],
                reason="Reserved semantic-verifier safety evaluation.",
            )
        )
        source_by_claim[claim] = row
    query = rows[0]["query"].strip()
    context = EvidenceContextBundle(
        query=query,
        reformulated_query=query,
        evidence_items=evidence_items,
        allowed_evidence_ids=[
            str(item["evidence_id"]) for item in evidence_items
        ],
        allowed_qa_ids=list(dict.fromkeys(allowed_qa_ids)),
    )
    return context, verifications, source_by_claim


def confusion_metrics(
    targets: list[bool],
    predictions: list[bool],
) -> dict[str, Any]:
    tp = sum(target and predicted for target, predicted in zip(targets, predictions))
    tn = sum(
        not target and not predicted for target, predicted in zip(targets, predictions)
    )
    fp = sum(
        not target and predicted for target, predicted in zip(targets, predictions)
    )
    fn = sum(target and not predicted for target, predicted in zip(targets, predictions))

    def divide(left: float, right: float) -> float:
        return left / right if right else 0.0

    precision = divide(tp, tp + fp)
    recall = divide(tp, tp + fn)
    return {
        "rows": len(targets),
        "true_positive": tp,
        "true_negative": tn,
        "false_positive": fp,
        "false_negative": fn,
        "accuracy": round(divide(tp + tn, len(targets)), 6),
        "precision_retain": round(precision, 6),
        "recall_retain": round(recall, 6),
        "f1_retain": round(
            divide(2 * precision * recall, precision + recall),
            6,
        ),
        "specificity_remove": round(divide(tn, tn + fp), 6),
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def count_successful_cache_records(path: Path) -> int:
    if not path.exists():
        return 0
    count = 0
    with path.open("r", encoding="utf-8-sig") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("status") == "ok" and row.get("fingerprint"):
                count += 1
    return count


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate the frozen verifier on 50 reserved claims."
    )
    parser.add_argument("--review-file", type=Path, default=DEFAULT_REVIEW)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--request-interval-seconds", type=float, default=8.0)
    parser.add_argument("--model", default="openai/gpt-oss-20b")
    parser.add_argument(
        "--prompt-version",
        default="semantic_claim_adjudication_v2",
    )
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--cache-only", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    review_path = args.review_file.resolve()
    rows = read_review(review_path)
    groups = group_rows(rows)
    if args.dry_run:
        print(
            json.dumps(
                {
                    "status": "dry_run",
                    "claims": len(rows),
                    "queries": len(groups),
                    "safe_or_equivalent": sum(
                        row["review_decision"] != "unsafe" for row in rows
                    ),
                    "unsafe": sum(
                        row["review_decision"] == "unsafe" for row in rows
                    ),
                    "human_labels_sent_to_model": False,
                    "gate_rules_modified": False,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    output_directory = OUTPUT_ROOT / args.run_id
    if output_directory.exists() and not args.resume:
        raise FileExistsError(
            f"Run exists; choose another run-id or use --resume: {output_directory}"
        )
    output_directory.mkdir(parents=True, exist_ok=True)
    cache_path = (
        CACHE_ROOT / args.run_id / "semantic_claim_adjudication.jsonl"
    )

    config = load_final_config()
    config = replace(
        config,
        claim_adjudication=replace(
            config.claim_adjudication,
            enabled=True,
            model=args.model,
            prompt_version=args.prompt_version,
            request_interval_seconds=args.request_interval_seconds,
            max_attempts=1,
        ),
    )
    adjudicator = SemanticClaimAdjudicator(
        config,
        cache_path=cache_path,
        raise_on_error=True,
        allow_api_calls=not args.cache_only,
    )

    predictions: list[dict[str, Any]] = []
    stopped_error = ""
    completed_groups = 0
    for group_index, group in enumerate(groups, start=1):
        context, verifications, source_by_claim = build_query_inputs(group)
        hardened, hard_audit = apply_v5_hard_gates(verifications, context)
        hard_by_claim = {
            str(row["claim"]): row for row in hard_audit
        }
        cases, verification_by_id = build_adjudication_cases(
            hardened,
            context,
        )
        claim_by_id = {
            claim_id: verification.claim.claim
            for claim_id, verification in verification_by_id.items()
        }
        try:
            final, semantic_audit = adjudicator.adjudicate(
                hardened,
                context,
            )
        except ClaimAdjudicationRateLimit as exc:
            stopped_error = str(exc)
            print(
                json.dumps(
                    {
                        "status": "stopped_rate_limit",
                        "progress": f"{group_index}/{len(groups)}",
                        "query_id": group[0]["query_id"],
                        "cache": str(cache_path),
                        "error": stopped_error,
                    },
                    ensure_ascii=False,
                ),
                flush=True,
            )
            break
        except ClaimAdjudicationError as exc:
            stopped_error = str(exc)
            print(
                json.dumps(
                    {
                        "status": "stopped_adjudication_error",
                        "progress": f"{group_index}/{len(groups)}",
                        "query_id": group[0]["query_id"],
                        "cache": str(cache_path),
                        "error": stopped_error,
                    },
                    ensure_ascii=False,
                ),
                flush=True,
            )
            break

        decisions = {
            claim_by_id.get(str(row.get("claim_id") or ""), ""): row
            for row in semantic_audit.get("decisions", [])
        }
        post_gate_by_claim = {
            str(row.get("claim") or ""): list(row.get("failures") or [])
            for row in semantic_audit.get("post_safety_gate", [])
        }
        final_by_claim = {item.claim.claim: item for item in final}
        for claim, source in source_by_claim.items():
            decision = decisions.get(claim, {})
            hard = hard_by_claim.get(claim, {})
            verification = final_by_claim[claim]
            human_retain = source["review_decision"] != "unsafe"
            predicted_retain = verification.status == "supported"
            predictions.append(
                {
                    "differential_id": source["differential_id"],
                    "cohort": source["cohort"],
                    "query_id": source["query_id"],
                    "claim": claim,
                    "review_decision": source["review_decision"],
                    "safety_error_types": source["safety_error_types"],
                    "human_should_retain": (
                        "yes" if human_retain else "no"
                    ),
                    "predicted_should_retain": (
                        "yes" if predicted_retain else "no"
                    ),
                    "correct_retain_decision": (
                        "yes" if human_retain == predicted_retain else "no"
                    ),
                    "hard_failures": " | ".join(
                        str(item) for item in hard.get("hard_failures", [])
                    ),
                    "semantic_evidence_support": str(
                        decision.get("evidence_support") or "not_adjudicated"
                    ),
                    "semantic_query_relevance": str(
                        decision.get("query_relevance") or "not_adjudicated"
                    ),
                    "semantic_intent_match": decision.get("intent_match", ""),
                    "semantic_concept_match": decision.get("concept_match", ""),
                    "semantic_anatomy_match": str(
                        decision.get("anatomy_match") or "not_adjudicated"
                    ),
                    "semantic_answer_contribution": str(
                        decision.get("answer_contribution")
                        or "not_adjudicated"
                    ),
                    "post_safety_gate_failures": " | ".join(
                        post_gate_by_claim.get(claim, [])
                    ),
                    "final_status": verification.status,
                    "final_reason": verification.reason,
                    "model": config.claim_adjudication.model,
                    "prompt_version": config.claim_adjudication.prompt_version,
                    "cache_hit": bool(semantic_audit.get("cache_hit")),
                }
            )
        completed_groups += 1
        print(
            json.dumps(
                {
                    "status": "ok",
                    "progress": f"{group_index}/{len(groups)}",
                    "query_id": group[0]["query_id"],
                    "claims": len(group),
                    "semantic_cases": len(cases),
                    "cache_hit": bool(semantic_audit.get("cache_hit")),
                },
                ensure_ascii=False,
            ),
            flush=True,
        )

    targets = [row["human_should_retain"] == "yes" for row in predictions]
    predicted = [
        row["predicted_should_retain"] == "yes" for row in predictions
    ]
    scores = confusion_metrics(targets, predicted)
    unsafe_retained = [
        row
        for row in predictions
        if (
            row["human_should_retain"] == "no"
            and row["predicted_should_retain"] == "yes"
        )
    ]
    safety_type_retained: Counter[str] = Counter()
    for row in unsafe_retained:
        safety_type_retained.update(
            split_values(str(row["safety_error_types"]))
        )
    safe_retained = sum(
        row["review_decision"] == "safe"
        and row["predicted_should_retain"] == "yes"
        for row in predictions
    )
    equivalent_retained = sum(
        row["review_decision"] == "equivalent_to_v3_kept"
        and row["predicted_should_retain"] == "yes"
        for row in predictions
    )
    complete = len(predictions) == len(rows) and not stopped_error
    acceptance = {
        "all_13_unsafe_rejected": bool(
            complete and not unsafe_retained
        ),
        "unsafe_retained": len(unsafe_retained),
        "wrong_drug_dose_anatomy_relation_or_recommendation_retained": sum(
            safety_type_retained.values()
        ),
        "passed": bool(complete and not unsafe_retained),
    }
    metrics = {
        "status": "complete" if complete else "partial",
        "claims": len(rows),
        "completed_claims": len(predictions),
        "queries": len(groups),
        "completed_queries": completed_groups,
        "human_safe_or_equivalent": 37,
        "human_unsafe": 13,
        "retain_decision": scores,
        "safe_retained": safe_retained,
        "safe_total": 11,
        "equivalent_retained": equivalent_retained,
        "equivalent_total": 26,
        "safe_or_equivalent_retention_rate": round(
            (safe_retained + equivalent_retained) / 37,
            6,
        ),
        "unsafe_retained_by_error_type": dict(
            sorted(safety_type_retained.items())
        ),
        "acceptance_gate": acceptance,
        "human_labels_sent_to_model": False,
        "gate_rules_modified": False,
        "successful_semantic_responses_cached": (
            count_successful_cache_records(cache_path)
        ),
        "api_calls_this_invocation": adjudicator.api_calls,
        "cache_hits_this_invocation": adjudicator.cache_hits,
        "stopped_error": stopped_error,
    }
    manifest = {
        "run_id": args.run_id,
        "purpose": "reserved 50-claim safety regression",
        "review_file": str(review_path),
        "review_sha256": hashlib.sha256(review_path.read_bytes()).hexdigest(),
        "graph_version": config.graph_version,
        "model": config.claim_adjudication.model,
        "prompt_version": config.claim_adjudication.prompt_version,
        "temperature": config.claim_adjudication.temperature,
        "reasoning_effort": config.claim_adjudication.reasoning_effort,
        "request_interval_seconds": args.request_interval_seconds,
        "cache_only": args.cache_only,
        "cache": str(cache_path),
        "human_labels_sent_to_model": False,
        "gate_rules_modified": False,
    }
    if predictions:
        write_csv(output_directory / "predictions.csv", predictions)
    write_json(output_directory / "metrics.json", metrics)
    write_json(output_directory / "manifest.json", manifest)
    print(
        json.dumps(
            {
                "status": metrics["status"],
                "output": str(output_directory),
                "metrics": scores,
                "acceptance_gate": acceptance,
                "successful_semantic_responses_cached": (
                    metrics["successful_semantic_responses_cached"]
                ),
                "api_calls_this_invocation": adjudicator.api_calls,
                "cache_hits_this_invocation": adjudicator.cache_hits,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if complete else 1


if __name__ == "__main__":
    raise SystemExit(main())
