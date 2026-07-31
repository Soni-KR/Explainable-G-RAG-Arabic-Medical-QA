from __future__ import annotations

"""Evaluate selective Step 14 semantic adjudication against human decisions."""

import argparse
import csv
import hashlib
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
OUTPUT_ROOT = ROOT / "outputs" / "evaluation" / "claim_verifier"
CACHE_ROOT = ROOT / "outputs" / "evaluation" / "cache"


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8-sig") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def read_review(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    required = {
        "query_id",
        "removed_claim",
        "human_evidence_support",
        "human_query_relevance",
        "human_intent_match",
        "human_concept_match",
        "human_anatomy_match",
        "human_should_retain",
    }
    missing = required - set(rows[0] if rows else {})
    if missing:
        raise ValueError(f"Human review is missing columns: {sorted(missing)}")
    if not rows:
        raise ValueError("Human review file is empty.")
    allowed = {
        "human_evidence_support": {"supported", "partial", "unsupported"},
        "human_query_relevance": {
            "relevant",
            "partially_relevant",
            "irrelevant",
        },
        "human_intent_match": {"yes", "no"},
        "human_concept_match": {"yes", "no"},
        "human_anatomy_match": {"yes", "no", "not_applicable"},
        "human_should_retain": {"yes", "no"},
    }
    for index, row in enumerate(rows, start=2):
        for field, values in allowed.items():
            if str(row.get(field) or "").strip() not in values:
                raise ValueError(f"Invalid {field} on review row {index}.")
    return rows


def verification_from_dict(payload: dict[str, Any]) -> ClaimVerification:
    values = dict(payload)
    values["claim"] = AnswerClaim(**dict(values["claim"]))
    return ClaimVerification(**values)


def stable_query_order(query_ids: set[str], seed: str) -> list[str]:
    return sorted(
        query_ids,
        key=lambda query_id: hashlib.sha256(
            f"{seed}:{query_id}".encode("utf-8")
        ).hexdigest(),
    )


def select_query_ids(
    rows: list[dict[str, str]],
    mode: str,
    negative_queries: int,
    positive_queries: int,
    seed: str,
) -> set[str]:
    all_ids = {row["query_id"] for row in rows}
    if mode == "all":
        return all_ids
    negative_ids = {
        row["query_id"] for row in rows if row["human_should_retain"] == "no"
    }
    positive_only = all_ids - negative_ids
    return set(stable_query_order(negative_ids, seed)[:negative_queries]) | set(
        stable_query_order(positive_only, seed)[:positive_queries]
    )


def confusion_metrics(targets: list[bool], predictions: list[bool]) -> dict[str, Any]:
    tp = sum(target and predicted for target, predicted in zip(targets, predictions))
    tn = sum(not target and not predicted for target, predicted in zip(targets, predictions))
    fp = sum(not target and predicted for target, predicted in zip(targets, predictions))
    fn = sum(target and not predicted for target, predicted in zip(targets, predictions))

    def divide(numerator: float, denominator: float) -> float:
        return numerator / denominator if denominator else 0.0

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


def exact_agreement(rows: list[dict[str, Any]], predicted: str, human: str) -> float:
    if not rows:
        return 0.0
    return round(
        sum(str(row[predicted]) == str(row[human]) for row in rows) / len(rows),
        6,
    )


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0]) if rows else []
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate cached semantic claim adjudication against human review."
    )
    parser.add_argument("--review-file", type=Path, default=DEFAULT_REVIEW)
    parser.add_argument("--source-run", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--mode", choices=["pilot", "all"], default="pilot")
    parser.add_argument("--pilot-negative-queries", type=int, default=8)
    parser.add_argument("--pilot-positive-queries", type=int, default=4)
    parser.add_argument("--selection-seed", default="20260728")
    parser.add_argument("--request-interval-seconds", type=float, default=None)
    parser.add_argument("--model", default="")
    parser.add_argument("--reasoning-effort", default="")
    parser.add_argument(
        "--prompt-version",
        default="",
        help=(
            "Override the semantic-adjudication prompt version so prompt-only "
            "ablations receive an independent cache fingerprint."
        ),
    )
    parser.add_argument(
        "--apply-v5-hard-gates",
        action="store_true",
        help=(
            "Apply verifier-v5 non-overridable gates before semantic "
            "adjudication. This affects only this evaluation run."
        ),
    )
    parser.add_argument(
        "--cache-only",
        action="store_true",
        help="Fail on a cache miss instead of making a semantic API call.",
    )
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    review_path = args.review_file.resolve()
    source_path = args.source_run.resolve()
    rows = read_review(review_path)
    source_records = {
        str(row.get("query_id") or ""): row for row in read_jsonl(source_path)
    }
    selected_ids = select_query_ids(
        rows,
        args.mode,
        args.pilot_negative_queries,
        args.pilot_positive_queries,
        args.selection_seed,
    )
    selected_rows = [row for row in rows if row["query_id"] in selected_ids]
    missing_sources = sorted(selected_ids - set(source_records))
    if missing_sources:
        raise ValueError(f"Source generation run is missing queries: {missing_sources}")

    selected_positive = sum(
        row["human_should_retain"] == "yes" for row in selected_rows
    )
    selected_negative = len(selected_rows) - selected_positive
    if args.dry_run:
        print(
            json.dumps(
                {
                    "status": "dry_run",
                    "mode": args.mode,
                    "queries": len(selected_ids),
                    "claims": len(selected_rows),
                    "human_retain": selected_positive,
                    "human_remove": selected_negative,
                    "source_run": str(source_path),
                    "human_labels_sent_to_model": False,
                    "v5_hard_gates": args.apply_v5_hard_gates,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    output_directory = OUTPUT_ROOT / args.run_id
    if output_directory.exists() and not args.resume:
        raise FileExistsError(
            f"Run already exists; choose another run-id or use --resume: "
            f"{output_directory}"
        )
    output_directory.mkdir(parents=True, exist_ok=True)
    cache_path = CACHE_ROOT / args.run_id / "semantic_claim_adjudication.jsonl"

    config = load_final_config()
    adjudication_config = replace(
        config.claim_adjudication,
        enabled=True,
        model=args.model or config.claim_adjudication.model,
        reasoning_effort=(
            args.reasoning_effort
            or config.claim_adjudication.reasoning_effort
        ),
        prompt_version=(
            args.prompt_version
            or config.claim_adjudication.prompt_version
        ),
        request_interval_seconds=(
            args.request_interval_seconds
            if args.request_interval_seconds is not None
            else config.claim_adjudication.request_interval_seconds
        ),
    )
    config = replace(config, claim_adjudication=adjudication_config)
    adjudicator = SemanticClaimAdjudicator(
        config,
        cache_path=cache_path,
        raise_on_error=True,
        allow_api_calls=not args.cache_only,
    )

    review_by_query: dict[str, list[dict[str, str]]] = {}
    for row in selected_rows:
        review_by_query.setdefault(row["query_id"], []).append(row)

    predictions: list[dict[str, Any]] = []
    deterministic_guard_claims = 0
    stopped_error = ""
    for index, query_id in enumerate(stable_query_order(selected_ids, args.selection_seed), start=1):
        source = source_records[query_id]
        raw = dict(source.get("raw") or {})
        context = EvidenceContextBundle(**dict(raw["context"]))
        raw_verifications = [
            verification_from_dict(item)
            for item in raw.get("verifications", [])
        ]
        wanted_claims = {
            row["removed_claim"] for row in review_by_query[query_id]
        }
        selected_verifications = [
            item
            for item in raw_verifications
            if item.claim.claim in wanted_claims
        ]
        deterministic_by_claim = {
            item.claim.claim: item for item in selected_verifications
        }
        gate_rows: list[dict[str, Any]] = []
        if args.apply_v5_hard_gates:
            adjudication_input, gate_rows = apply_v5_hard_gates(
                selected_verifications,
                context,
            )
        else:
            adjudication_input = selected_verifications
            gate_rows = [
                {
                    "claim": item.claim.claim,
                    "status_after_hard_gates": item.status,
                    "hard_failures": [],
                    "soft_failures": [],
                    "semantic_eligible": True,
                }
                for item in selected_verifications
            ]
        hardened_by_claim = {
            item.claim.claim: item for item in adjudication_input
        }
        gate_by_claim = {
            str(item.get("claim") or ""): item for item in gate_rows
        }
        found_claims = {item.claim.claim for item in selected_verifications}
        missing_claims = wanted_claims - found_claims
        if missing_claims:
            raise ValueError(
                f"Could not match {len(missing_claims)} reviewed claims for {query_id}."
            )
        cases, verification_by_claim_id = build_adjudication_cases(
            adjudication_input,
            context,
        )
        claim_by_id = {
            claim_id: verification.claim.claim
            for claim_id, verification in verification_by_claim_id.items()
        }
        claim_id_by_text = {
            claim: claim_id for claim_id, claim in claim_by_id.items()
        }
        try:
            final_verifications, audit = adjudicator.adjudicate(
                adjudication_input,
                context,
            )
        except ClaimAdjudicationRateLimit as exc:
            stopped_error = str(exc)
            print(
                json.dumps(
                    {
                        "status": "stopped_rate_limit",
                        "progress": f"{index}/{len(selected_ids)}",
                        "query_id": query_id,
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
                        "progress": f"{index}/{len(selected_ids)}",
                        "query_id": query_id,
                        "cache": str(cache_path),
                        "error": stopped_error,
                    },
                    ensure_ascii=False,
                ),
                flush=True,
            )
            break
        decisions = {
            str(item["claim_id"]): item for item in audit.get("decisions", [])
        }
        if set(decisions) != set(claim_by_id):
            raise ValueError(f"Incomplete semantic decisions for {query_id}.")
        human_by_claim = {
            row["removed_claim"]: row for row in review_by_query[query_id]
        }
        final_by_claim = {
            item.claim.claim: item for item in final_verifications
        }
        for verification_index, verification in enumerate(
            selected_verifications,
            start=1,
        ):
            claim = verification.claim.claim
            claim_id = claim_id_by_text.get(claim, f"D{verification_index}")
            decision = decisions.get(claim_id)
            human = human_by_claim[claim]
            semantic_decision = decision is not None
            deterministic = deterministic_by_claim[claim]
            hardened = hardened_by_claim[claim]
            final = final_by_claim[claim]
            gate = gate_by_claim.get(claim, {})
            if not semantic_decision:
                deterministic_guard_claims += 1
            predictions.append(
                {
                    "query_id": query_id,
                    "claim_id": claim_id,
                    "claim": claim,
                    "deterministic_v3_status": deterministic.status,
                    "deterministic_v3_should_retain": (
                        "yes" if deterministic.status == "supported" else "no"
                    ),
                    "v5_hard_status": hardened.status,
                    "v5_hard_should_retain": (
                        "yes" if hardened.status == "supported" else "no"
                    ),
                    "v5_hard_failures": " | ".join(
                        str(item) for item in gate.get("hard_failures", [])
                    ),
                    "v5_soft_failures": " | ".join(
                        str(item) for item in gate.get("soft_failures", [])
                    ),
                    "v5_semantic_eligible": bool(
                        gate.get("semantic_eligible")
                    ),
                    "adjudication_status": (
                        "semantic"
                        if semantic_decision
                        else "deterministic_provenance_guard"
                    ),
                    "predicted_evidence_support": (
                        decision["evidence_support"]
                        if semantic_decision
                        else "not_adjudicated"
                    ),
                    "human_evidence_support": human["human_evidence_support"],
                    "predicted_query_relevance": (
                        decision["query_relevance"]
                        if semantic_decision
                        else "not_adjudicated"
                    ),
                    "human_query_relevance": human["human_query_relevance"],
                    "predicted_intent_match": (
                        "yes"
                        if semantic_decision and decision["intent_match"]
                        else "no"
                    ),
                    "human_intent_match": human["human_intent_match"],
                    "predicted_concept_match": (
                        "yes"
                        if semantic_decision and decision["concept_match"]
                        else "no"
                    ),
                    "human_concept_match": human["human_concept_match"],
                    "predicted_anatomy_match": (
                        decision["anatomy_match"]
                        if semantic_decision
                        else "not_adjudicated"
                    ),
                    "human_anatomy_match": human["human_anatomy_match"],
                    "predicted_answer_contribution": (
                        decision["answer_contribution"]
                        if semantic_decision
                        else "not_adjudicated"
                    ),
                    "predicted_clinical_relation_preserved": (
                        "yes"
                        if semantic_decision
                        and decision["clinical_relation_preserved"]
                        else "no"
                    ),
                    "predicted_named_entity_identity_preserved": (
                        "yes"
                        if semantic_decision
                        and decision["named_entity_identity_preserved"]
                        else "no"
                    ),
                    "predicted_patient_context_compatible": (
                        "yes"
                        if semantic_decision
                        and decision["patient_context_compatible"]
                        else "no"
                    ),
                    "predicted_should_retain": (
                        "yes" if final.status == "supported" else "no"
                    ),
                    "human_should_retain": human["human_should_retain"],
                    "correct_retain_decision": (
                        (
                            final.status == "supported"
                        )
                        == (human["human_should_retain"] == "yes")
                    ),
                    "reason": (
                        decision["reason"]
                        if semantic_decision
                        else (
                            "Not sent: authoritative answer/relation evidence "
                            "did not satisfy the semantic-review support floor."
                        )
                    ),
                    "cached": (
                        bool(decision["cached"]) if semantic_decision else False
                    ),
                }
            )
        print(
            json.dumps(
                {
                    "status": "ok",
                    "progress": f"{index}/{len(selected_ids)}",
                    "query_id": query_id,
                    "claims": len(cases),
                    "cache_hit": audit["cache_hit"],
                },
                ensure_ascii=False,
            ),
            flush=True,
        )

    targets = [row["human_should_retain"] == "yes" for row in predictions]
    deterministic_predictions = [
        row["deterministic_v3_should_retain"] == "yes"
        for row in predictions
    ]
    hard_predictions = [
        row["v5_hard_should_retain"] == "yes" for row in predictions
    ]
    predicted = [row["predicted_should_retain"] == "yes" for row in predictions]
    deterministic_metrics = confusion_metrics(
        targets,
        deterministic_predictions,
    )
    hard_metrics = confusion_metrics(targets, hard_predictions)
    retain_metrics = confusion_metrics(targets, predicted)
    retained_query_ids = {
        row["query_id"]
        for row in predictions
        if row["predicted_should_retain"] == "yes"
    }
    source_substantive_ids = {
        query_id
        for query_id, source in source_records.items()
        if list(source.get("output_claims") or [])
    }
    newly_substantive_ids = retained_query_ids - source_substantive_ids
    existing_retained_claims = sum(
        len(list(source.get("output_claims") or []))
        for source in source_records.values()
    )
    recovered_claims = sum(predicted)
    coverage_impact = {
        "scope": (
            "reviewed development replay; not an independent production score"
        ),
        "source_queries": len(source_records),
        "source_substantive_queries": len(source_substantive_ids),
        "source_retained_claims": existing_retained_claims,
        "semantically_recovered_claims": recovered_claims,
        "queries_with_recovered_claims": len(retained_query_ids),
        "newly_substantive_queries": len(newly_substantive_ids),
        "projected_substantive_queries": len(
            source_substantive_ids | retained_query_ids
        ),
        "projected_retained_claims": (
            existing_retained_claims + recovered_claims
        ),
    }
    pilot_gate = {
        "maximum_false_positives": 0,
        "minimum_retain_recall": 0.80,
        "passed": bool(
            not stopped_error
            and retain_metrics["false_positive"] == 0
            and retain_metrics["recall_retain"] >= 0.80
        ),
    }
    metrics = {
        "status": "partial" if stopped_error else "complete",
        "mode": args.mode,
        "selected_queries": len(selected_ids),
        "completed_queries": len({row["query_id"] for row in predictions}),
        "selected_claims": len(selected_rows),
        "completed_claims": len(predictions),
        "retain_decision": retain_metrics,
        "coverage_impact": coverage_impact,
        "experiment_b": {
            "deterministic_v3": deterministic_metrics,
            "v5_hard_gates_only": hard_metrics,
            "v5_hard_plus_semantic": retain_metrics,
        },
        "v5_gate_counts": {
            "hard_blocked": sum(
                bool(row["v5_hard_failures"]) for row in predictions
            ),
            "semantically_eligible": sum(
                bool(row["v5_semantic_eligible"]) for row in predictions
            ),
            "semantic_retain": sum(predicted),
        },
        "deterministic_provenance_guard_claims": deterministic_guard_claims,
        "pilot_safety_gate": pilot_gate,
        "dimension_exact_agreement": {
            "evidence_support": exact_agreement(
                predictions,
                "predicted_evidence_support",
                "human_evidence_support",
            ),
            "query_relevance": exact_agreement(
                predictions,
                "predicted_query_relevance",
                "human_query_relevance",
            ),
            "intent_match": exact_agreement(
                predictions,
                "predicted_intent_match",
                "human_intent_match",
            ),
            "concept_match": exact_agreement(
                predictions,
                "predicted_concept_match",
                "human_concept_match",
            ),
            "anatomy_match": exact_agreement(
                predictions,
                "predicted_anatomy_match",
                "human_anatomy_match",
            ),
        },
        "api_calls": adjudicator.api_calls,
        "cache_hits": adjudicator.cache_hits,
        "stopped_error": stopped_error,
    }
    manifest = {
        "run_id": args.run_id,
        "purpose": "development evaluation of disputed-claim semantic adjudication",
        "review_file": str(review_path),
        "review_sha256": hashlib.sha256(review_path.read_bytes()).hexdigest(),
        "source_run": str(source_path),
        "source_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
        "human_labels_sent_to_model": False,
        "cache_only": args.cache_only,
        "v5_hard_gates": args.apply_v5_hard_gates,
        "pilot_safety_gate": pilot_gate,
        "selection": {
            "mode": args.mode,
            "seed": args.selection_seed,
            "pilot_negative_queries": args.pilot_negative_queries,
            "pilot_positive_queries": args.pilot_positive_queries,
        },
        "model": adjudication_config.model,
        "prompt_version": adjudication_config.prompt_version,
        "temperature": adjudication_config.temperature,
        "reasoning_effort": adjudication_config.reasoning_effort,
        "request_interval_seconds": adjudication_config.request_interval_seconds,
        "cache": str(cache_path),
    }
    write_csv(output_directory / "predictions.csv", predictions)
    write_json(output_directory / "metrics.json", metrics)
    write_json(output_directory / "manifest.json", manifest)
    print(
        json.dumps(
            {
                "status": metrics["status"],
                "output": str(output_directory),
                "cache": str(cache_path),
                "metrics": metrics["retain_decision"],
                "api_calls": adjudicator.api_calls,
                "cache_hits": adjudicator.cache_hits,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 2 if stopped_error else 0


if __name__ == "__main__":
    raise SystemExit(main())
