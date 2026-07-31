from __future__ import annotations

"""Run the frozen-context evidence-preserving extractive fallback ablation."""

import argparse
import copy
import csv
import hashlib
import json
import math
import statistics
import subprocess
import sys
from collections import Counter
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Any, Iterable

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from scripts.evaluation_common import citation_validity, unavailable
from src.evaluation_metrics import bertscore_f1, claim_grounding_metrics
from src.models import EvidenceContextBundle, GeneratedAnswer
from src.step12b_extractive_fallback import (
    FALLBACK_VERSION,
    MAX_SENTENCE_CHARS,
    MIN_ANSWER_RELEVANCE,
    MIN_INTENT_SUPPORT,
    MIN_ORIGINAL_QUESTION_RELEVANCE,
    MIN_QUERY_CONCEPT_COVERAGE,
    MIN_QUERY_CONSTRAINT_COVERAGE,
    MIN_SENTENCE_CHARS,
    MIN_SENTENCE_QUERY_RELEVANCE,
    MIN_SOURCE_RELIABILITY,
    fallback_audit_payload,
    fallback_eligible,
    select_extractive_fallback,
)
from src.step15_mitigate_hallucinations import mitigate_hallucinations
from src.step16_score_reliability import score_reliability


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_COHORT_A = Path(
    "outputs/evaluation/generation/"
    "expA_v31_ahd_reference_100_20260729/full_pipeline.jsonl"
)
DEFAULT_COHORT_B = Path(
    "outputs/evaluation/generation/"
    "expA_v31_entity_gt_100_20260729/full_pipeline.jsonl"
)
DEFAULT_OUTPUT_DIR = Path(
    "outputs/evaluation/generation/"
    "expD_evidence_preserving_extractive_200q_20260730"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate one-sentence exact extraction on frozen v3.1 Step 11 "
            "contexts without changing retrieval or the v3 verifier."
        )
    )
    parser.add_argument("--cohort-a", type=Path, default=DEFAULT_COHORT_A)
    parser.add_argument("--cohort-b", type=Path, default=DEFAULT_COHORT_B)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def resolved(path: Path) -> Path:
    return path if path.is_absolute() else ROOT / path


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8-sig") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write_json(path: Path, payload: Any) -> None:
    if path.exists():
        raise FileExistsError(f"Refusing to overwrite: {path}")
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    if path.exists():
        raise FileExistsError(f"Refusing to overwrite: {path}")
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_csv(
    path: Path,
    rows: list[dict[str, Any]],
    fields: list[str],
) -> None:
    if path.exists():
        raise FileExistsError(f"Refusing to overwrite: {path}")
    with path.open("x", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def context_from_record(record: dict[str, Any]) -> EvidenceContextBundle:
    payload = dict((record.get("raw") or {}).get("context") or {})
    return EvidenceContextBundle(
        query=str(payload.get("query") or record.get("query") or ""),
        reformulated_query=str(payload.get("reformulated_query") or ""),
        primary_intent=str(payload.get("primary_intent") or ""),
        query_medical_phrases=list(
            payload.get("query_medical_phrases") or []
        ),
        graph_facts=list(payload.get("graph_facts") or []),
        evidence_items=list(payload.get("evidence_items") or []),
        allowed_evidence_ids=list(
            payload.get("allowed_evidence_ids") or []
        ),
        allowed_qa_ids=list(payload.get("allowed_qa_ids") or []),
        warnings=list(payload.get("warnings") or []),
    )


def metric_payload(
    *,
    answer: str,
    reference_answer: str,
    claims: list[Any],
    verifications: list[Any],
    context: EvidenceContextBundle,
    timings: dict[str, float],
    answerability: str,
) -> dict[str, Any]:
    substantive = bool(claims) and answerability not in {
        "insufficient_evidence",
        "generation_unavailable",
    }
    output_statuses = [
        next(
            (
                verification.status
                for verification in verifications
                if verification.claim.claim == claim.claim
            ),
            "unsupported",
        )
        for claim in claims
    ]
    return {
        "bertscore": (
            bertscore_f1(answer, reference_answer)
            if substantive
            else unavailable(
                "BERTScore is not computed for an insufficient-evidence answer."
            )
        ),
        "claim_grounding": (
            {"status": "computed", **claim_grounding_metrics(output_statuses)}
            if claims
            else unavailable("The output contained no factual claims to score.")
        ),
        "pre_mitigation_claim_grounding": {
            "status": "computed",
            **claim_grounding_metrics(
                [verification.status for verification in verifications]
            ),
        },
        "citation_validity": (
            citation_validity(claims, context.allowed_evidence_ids)
            if substantive
            else unavailable(
                "Citation validity requires a substantive factual answer."
            )
        ),
        "latency": {
            "status": "computed",
            "end_to_end_latency_ms": timings["end_to_end"],
            "per_stage_latency_ms": {
                key: value
                for key, value in timings.items()
                if key != "end_to_end"
            },
        },
    }


def replace_with_fallback(
    record: dict[str, Any],
    context: EvidenceContextBundle,
    result: Any,
    elapsed_ms: float,
) -> dict[str, Any]:
    selected = result.selected
    if selected is None:
        return record

    claim = selected.claim
    verification = selected.verification
    generated = GeneratedAnswer(
        query=context.query,
        answer=claim.claim,
        claims=[claim],
        limitations=[
            "The answer is an exact sentence from one retrieved AHD answer."
        ],
        model="deterministic_exact_extraction",
        prompt_version=FALLBACK_VERSION,
        generation_mode="evidence_preserving_extractive_fallback",
        generation_evidence_ids=[selected.evidence_id],
        generation_mode_reason=(
            "A single authoritative answer sentence passed frozen relevance "
            "gates and the unchanged deterministic v3 verifier."
        ),
        generation_status="generated",
        attempt_count=0,
    )
    verifications = [verification]

    started = perf_counter()
    mitigated = mitigate_hallucinations(
        generated,
        verifications,
        context=context,
    )
    mitigation_ms = round((perf_counter() - started) * 1000.0, 3)
    started = perf_counter()
    reliability = score_reliability(mitigated, verifications, context)
    reliability_ms = round((perf_counter() - started) * 1000.0, 3)

    updated = copy.deepcopy(record)
    timings = dict(updated.get("timings_ms") or {})
    replaced_stages = (
        "step12_answer_generation",
        "step13_claim_extraction",
        "step14_claim_verification",
        "step15_hallucination_mitigation",
        "step16_reliability_scoring",
    )
    old_postprocessing = sum(
        float(timings.get(stage) or 0.0) for stage in replaced_stages
    )
    timings.update(
        {
            "step12_answer_generation": round(elapsed_ms, 3),
            "step13_claim_extraction": 0.0,
            "step14_claim_verification": 0.0,
            "step15_hallucination_mitigation": mitigation_ms,
            "step16_reliability_scoring": reliability_ms,
        }
    )
    timings["end_to_end"] = round(
        max(
            0.0,
            float(timings.get("end_to_end") or 0.0) - old_postprocessing,
        )
        + elapsed_ms
        + mitigation_ms
        + reliability_ms,
        3,
    )

    raw = dict(updated.get("raw") or {})
    raw.update(
        {
            "generated": asdict(generated),
            "claims": [asdict(claim)],
            "verifications": [asdict(verification)],
            "claim_verifier_audit": {
                "verifier": "deterministic_v3_unchanged",
                "semantic_adjudication_enabled": False,
                "semantic_safety_gate_enabled": False,
                "support_threshold": 0.40,
                "weak_threshold": 0.25,
            },
            "mitigated": asdict(mitigated),
            "reliability": asdict(reliability),
            "extractive_fallback": fallback_audit_payload(result),
            "frozen_context_reused": True,
        }
    )
    reference = str((updated.get("gold") or {}).get("reference_answer") or "")
    metrics = metric_payload(
        answer=mitigated.answer,
        reference_answer=reference,
        claims=mitigated.kept_claims,
        verifications=verifications,
        context=context,
        timings=timings,
        answerability=mitigated.answerability,
    )
    updated.update(
        {
            "generation_status": "generated",
            "answerability": mitigated.answerability,
            "query_coverage": mitigated.query_coverage,
            "missing_query_concepts": mitigated.missing_query_concepts,
            "answer": mitigated.answer,
            "output_claims": [
                asdict(item) for item in mitigated.kept_claims
            ],
            "metrics": metrics,
            "timings_ms": timings,
            "raw": raw,
            "warnings": list(
                dict.fromkeys(
                    [
                        *(updated.get("warnings") or []),
                        (
                            "Evidence-preserving fallback copied one exact "
                            "authoritative answer sentence."
                        ),
                    ]
                )
            ),
        }
    )
    return updated


def percentile(values: list[float], fraction: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] * (upper - position) + ordered[upper] * (
        position - lower
    )


def distribution(values: Iterable[float]) -> dict[str, float]:
    rows = [float(value) for value in values]
    if not rows:
        return {"mean": 0.0, "median": 0.0, "p95": 0.0, "total": 0.0}
    return {
        "mean": round(statistics.fmean(rows), 6),
        "median": round(statistics.median(rows), 6),
        "p95": round(percentile(rows, 0.95), 6),
        "total": round(sum(rows), 6),
    }


def summarize(records: list[dict[str, Any]]) -> dict[str, Any]:
    substantive = [row for row in records if row.get("output_claims")]
    claims = [
        claim for row in records for claim in row.get("output_claims") or []
    ]
    statuses = Counter(
        str(item.get("status") or "unknown")
        for row in records
        for item in (row.get("raw") or {}).get("verifications") or []
    )
    citations = [
        citation
        for row in records
        for claim in row.get("output_claims") or []
        for citation in claim.get("citations") or []
    ]
    valid_citations = 0
    for row in records:
        context = dict((row.get("raw") or {}).get("context") or {})
        allowed = set(context.get("allowed_evidence_ids") or [])
        present = {
            str(item.get("evidence_id") or "")
            for item in context.get("evidence_items") or []
        }
        for claim in row.get("output_claims") or []:
            valid_citations += sum(
                citation in allowed and citation in present
                for citation in claim.get("citations") or []
            )

    bert_rows = [
        float(row["metrics"]["bertscore"]["bertscore_f1"])
        for row in records
        if (row.get("metrics") or {}).get("bertscore", {}).get("status")
        == "computed"
    ]
    technical = [
        row
        for row in records
        if str(
            ((row.get("raw") or {}).get("generated") or {}).get(
                "fallback_type"
            )
            or ""
        )
        == "technical_failure"
    ]
    schema = [
        row
        for row in technical
        if any(
            marker
            in str(
                ((row.get("raw") or {}).get("generated") or {}).get(
                    "fallback_reason"
                )
                or ""
            ).lower()
            for marker in ("schema", "json_validate_failed", "missing properties")
        )
    ]
    timing_stages = sorted(
        {
            stage
            for row in records
            for stage in (row.get("timings_ms") or {})
        }
    )
    return {
        "queries": len(records),
        "substantive_answers": len(substantive),
        "retained_claims": len(claims),
        "answerability": dict(
            sorted(
                Counter(
                    str(row.get("answerability") or "unknown")
                    for row in records
                ).items()
            )
        ),
        "pre_mitigation_claims": {
            "total": sum(statuses.values()),
            "status_counts": dict(sorted(statuses.items())),
            "supported_claim_rate": round(
                statuses["supported"] / sum(statuses.values())
                if statuses
                else 0.0,
                6,
            ),
        },
        "citation_validity": round(
            valid_citations / len(citations) if citations else 0.0,
            6,
        ),
        "citation_count": len(citations),
        "technical_failures": len(technical),
        "schema_failures": len(schema),
        "bertscore": {
            "status": "computed" if bert_rows else "unavailable",
            "evaluated_query_count": len(bert_rows),
            "bertscore_f1": round(statistics.fmean(bert_rows), 6)
            if bert_rows
            else 0.0,
        },
        "latency_ms": {
            stage: distribution(
                float((row.get("timings_ms") or {}).get(stage) or 0.0)
                for row in records
            )
            for stage in timing_stages
        },
    }


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git_commit() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            capture_output=True,
            check=True,
            text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path.resolve())


def process_cohort(
    cohort: str,
    records: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    if len(records) != 100:
        raise ValueError(f"{cohort} must contain exactly 100 records.")
    if len({str(row.get("query_id") or "") for row in records}) != 100:
        raise ValueError(f"{cohort} contains duplicate or blank query IDs.")

    output: list[dict[str, Any]] = []
    attempts: list[dict[str, Any]] = []
    differential: list[dict[str, Any]] = []
    for record in records:
        context = context_from_record(record)
        if not fallback_eligible(
            output_claims=list(record.get("output_claims") or []),
            context=context,
        ):
            output.append(copy.deepcopy(record))
            continue

        started = perf_counter()
        result = select_extractive_fallback(context)
        elapsed_ms = round((perf_counter() - started) * 1000.0, 3)
        selected = result.selected
        attempts.append(
            {
                "cohort": cohort,
                "query_id": str(record.get("query_id") or ""),
                "query": str(record.get("query") or ""),
                "status": result.status,
                "reason": result.reason,
                "candidate_count": result.candidate_count,
                "supported_candidate_count": result.supported_candidate_count,
                "selected_evidence_id": selected.evidence_id
                if selected
                else "",
                "selected_qa_id": selected.qa_id if selected else "",
                "selected_sentence": selected.claim.claim
                if selected
                else "",
                "selection_score": selected.selection_score
                if selected
                else "",
                "elapsed_ms": elapsed_ms,
            }
        )
        candidate = replace_with_fallback(
            record,
            context,
            result,
            elapsed_ms,
        )
        output.append(candidate)
        if selected:
            differential.append(
                {
                    "differential_id": (
                        f"{cohort}:{record.get('query_id')}:extractive-1"
                    ),
                    "cohort": cohort,
                    "query_id": str(record.get("query_id") or ""),
                    "query": str(record.get("query") or ""),
                    "reference_answer": str(
                        (record.get("gold") or {}).get(
                            "reference_answer"
                        )
                        or ""
                    ),
                    "claim": selected.claim.claim,
                    "evidence_id": selected.evidence_id,
                    "qa_id": selected.qa_id,
                    "source_answer": selected.source_answer,
                    "selection_score": selected.selection_score,
                    "support_score": selected.verification.support_score,
                    "question_relevance": (
                        selected.verification.question_relevance
                    ),
                    "query_concept_coverage": (
                        selected.verification.query_concept_coverage
                    ),
                    "exact_source_match": str(
                        selected.exact_source_match
                    ).lower(),
                    "citation_count": len(selected.claim.citations),
                    "automatic_v3_supported": str(
                        selected.verification.status == "supported"
                    ).lower(),
                    "wrong_drug": "",
                    "anatomy_error": "",
                    "negation_error": "",
                    "number_error": "",
                    "clinical_relation_error": "",
                    "unsupported_recommendation": "",
                    "wrong_clinical_scenario": "",
                    "review_decision": "",
                    "reviewer_notes": "",
                    "reviewer_type": "",
                }
            )
    return output, attempts, differential


def report_markdown(result: dict[str, Any]) -> str:
    baseline = result["aggregate"]["baseline"]
    candidate = result["aggregate"]["candidate"]
    gates = result["promotion"]["gates"]
    lines = [
        "# Evidence-Preserving Extractive Fallback",
        "",
        "This is a frozen-context internal development ablation. It reuses the",
        "completed v3.1 Step 11 contexts, changes no retrieval component, and",
        "uses the unchanged deterministic v3 claim verifier.",
        "",
        f"**Decision: {result['promotion']['status']}**",
        "",
        "## Aggregate Results",
        "",
        "| Metric | Frozen v3.1 | Extractive candidate |",
        "|---|---:|---:|",
        f"| Substantive answers | {baseline['substantive_answers']}/200 | "
        f"{candidate['substantive_answers']}/200 |",
        f"| Retained claims | {baseline['retained_claims']} | "
        f"{candidate['retained_claims']} |",
        f"| Citation validity | {baseline['citation_validity']:.3f} | "
        f"{candidate['citation_validity']:.3f} |",
        f"| Schema failures | {baseline['schema_failures']} | "
        f"{candidate['schema_failures']} |",
        f"| Technical failures | {baseline['technical_failures']} | "
        f"{candidate['technical_failures']} |",
        f"| BERTScore F1 | {baseline['bertscore']['bertscore_f1']:.6f} "
        f"({baseline['bertscore']['evaluated_query_count']}) | "
        f"{candidate['bertscore']['bertscore_f1']:.6f} "
        f"({candidate['bertscore']['evaluated_query_count']}) |",
        "",
        "## Frozen Gates",
        "",
    ]
    lines.extend(f"- `{name}`: `{value}`" for name, value in result["policy"].items())
    lines.extend(
        [
            "",
            "## Promotion Checks",
            "",
        ]
    )
    lines.extend(
        f"- `{name}`: **{'pass' if passed else 'fail'}**"
        for name, passed in gates.items()
    )
    lines.extend(
        [
            "",
            "The automatic checks establish exact extraction, one valid citation,",
            "and deterministic v3 support. They do not constitute external medical",
            "safety validation. Newly retained claims remain an internal development",
            "result until their differential review is completed.",
            "",
            "## Artifacts",
            "",
        ]
    )
    lines.extend(
        f"- `{name}`: `{path}`"
        for name, path in result["artifacts"].items()
    )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    cohort_a_path = resolved(args.cohort_a)
    cohort_b_path = resolved(args.cohort_b)
    output_dir = resolved(args.output_dir)
    if output_dir.exists():
        raise FileExistsError(
            f"Refusing to overwrite existing ablation: {output_dir}"
        )
    output_dir.mkdir(parents=True)

    baseline_a = load_jsonl(cohort_a_path)
    baseline_b = load_jsonl(cohort_b_path)
    candidate_a, attempts_a, differential_a = process_cohort(
        "ahd_reference_100",
        baseline_a,
    )
    candidate_b, attempts_b, differential_b = process_cohort(
        "entity_ground_truth_100",
        baseline_b,
    )
    attempts = attempts_a + attempts_b
    differential = differential_a + differential_b

    # The experiment was specified for the 85 frozen non-empty-context rows.
    if len(attempts) != 85:
        raise ValueError(
            f"Frozen eligibility changed: expected 85 rows, found {len(attempts)}."
        )
    for baseline, candidate in (
        (baseline_a, candidate_a),
        (baseline_b, candidate_b),
    ):
        baseline_by_id = {str(row["query_id"]): row for row in baseline}
        for row in candidate:
            source = baseline_by_id[str(row["query_id"])]
            if (row.get("raw") or {}).get("context") != (
                source.get("raw") or {}
            ).get("context"):
                raise ValueError(
                    f"Frozen Step 11 context changed for {row['query_id']}."
                )

    baseline_summary_a = summarize(baseline_a)
    baseline_summary_b = summarize(baseline_b)
    candidate_summary_a = summarize(candidate_a)
    candidate_summary_b = summarize(candidate_b)
    aggregate_baseline = summarize(baseline_a + baseline_b)
    aggregate_candidate = summarize(candidate_a + candidate_b)

    automatic_invariant_failures = sum(
        row["exact_source_match"] != "true"
        or row["citation_count"] != 1
        or row["automatic_v3_supported"] != "true"
        for row in differential
    )
    gates = {
        "substantive_answers_above_54": (
            aggregate_candidate["substantive_answers"] > 54
        ),
        "retained_claims_above_72": (
            aggregate_candidate["retained_claims"] > 72
        ),
        "citation_validity_one": (
            aggregate_candidate["citation_validity"] == 1.0
        ),
        "schema_failures_zero": (
            aggregate_candidate["schema_failures"] == 0
        ),
        "automatic_extractiveness_invariants_zero": (
            automatic_invariant_failures == 0
        ),
        "differential_medical_review_complete": False,
        "unsafe_differential_claims_zero": False,
    }
    automatic_pass = all(
        value
        for key, value in gates.items()
        if key
        not in {
            "differential_medical_review_complete",
            "unsafe_differential_claims_zero",
        }
    )
    status = (
        "AUTOMATIC_TARGETS_MET_PENDING_DIFFERENTIAL_REVIEW"
        if automatic_pass
        else "DO_NOT_PROMOTE_AUTOMATIC_TARGETS_NOT_MET"
    )

    cohort_a_output = output_dir / "ahd_reference_100.jsonl"
    cohort_b_output = output_dir / "entity_ground_truth_100.jsonl"
    attempts_output = output_dir / "fallback_attempts.jsonl"
    differential_output = output_dir / "differential_safety_review.csv"
    metrics_output = output_dir / "metrics.json"
    manifest_output = output_dir / "manifest.json"
    report_output = output_dir / "README.md"
    write_jsonl(cohort_a_output, candidate_a)
    write_jsonl(cohort_b_output, candidate_b)
    write_jsonl(attempts_output, attempts)
    differential_fields = list(differential[0]) if differential else [
        "differential_id",
        "review_decision",
        "reviewer_notes",
        "reviewer_type",
    ]
    write_csv(differential_output, differential, differential_fields)

    artifacts = {
        "cohort_a_candidate": relative(cohort_a_output),
        "cohort_b_candidate": relative(cohort_b_output),
        "fallback_attempts": relative(attempts_output),
        "differential_safety_review": relative(differential_output),
        "metrics": relative(metrics_output),
        "manifest": relative(manifest_output),
        "report": relative(report_output),
    }
    policy = {
        "fallback_version": FALLBACK_VERSION,
        "min_answer_relevance": MIN_ANSWER_RELEVANCE,
        "min_original_question_relevance": (
            MIN_ORIGINAL_QUESTION_RELEVANCE
        ),
        "min_intent_support": MIN_INTENT_SUPPORT,
        "min_query_concept_coverage": MIN_QUERY_CONCEPT_COVERAGE,
        "min_query_constraint_coverage": (
            MIN_QUERY_CONSTRAINT_COVERAGE
        ),
        "min_source_reliability": MIN_SOURCE_RELIABILITY,
        "min_sentence_query_relevance": (
            MIN_SENTENCE_QUERY_RELEVANCE
        ),
        "min_sentence_chars": MIN_SENTENCE_CHARS,
        "max_sentence_chars": MAX_SENTENCE_CHARS,
        "max_claims_per_query": 1,
        "citations_per_claim": 1,
        "semantic_override_enabled": False,
        "supplemental_graph_enabled": False,
        "verifier": "deterministic_v3_unchanged",
    }
    result = {
        "status": "ok",
        "cohorts": {
            "ahd_reference_100": {
                "baseline": baseline_summary_a,
                "candidate": candidate_summary_a,
            },
            "entity_ground_truth_100": {
                "baseline": baseline_summary_b,
                "candidate": candidate_summary_b,
            },
        },
        "aggregate": {
            "baseline": aggregate_baseline,
            "candidate": aggregate_candidate,
        },
        "fallback": {
            "eligible_queries": len(attempts),
            "selected_queries": len(differential),
            "no_supported_sentence": sum(
                row["status"] == "no_supported_sentence"
                for row in attempts
            ),
            "automatic_invariant_failures": automatic_invariant_failures,
        },
        "policy": policy,
        "promotion": {
            "status": status,
            "automatic_gates_passed": automatic_pass,
            "gates": gates,
            "scope_note": (
                "Internal development result only; medical safety is not "
                "externally confirmed without differential human review."
            ),
        },
        "artifacts": artifacts,
    }
    write_json(metrics_output, result)
    manifest = {
        "run_type": "frozen_context_extractive_fallback_ablation",
        "created_at_utc": datetime.now(UTC).isoformat(),
        "git_commit": git_commit(),
        "graph_version": "final_v1",
        "input_runs": {
            "ahd_reference_100": {
                "path": relative(cohort_a_path),
                "sha256": file_sha256(cohort_a_path),
            },
            "entity_ground_truth_100": {
                "path": relative(cohort_b_path),
                "sha256": file_sha256(cohort_b_path),
            },
        },
        "policy": policy,
        "frozen_components": [
            "final_v1",
            "embeddings",
            "Steps 8-11 contexts",
            "deterministic v3 verifier",
            "mitigation thresholds",
        ],
        "network_calls": 0,
        "api_keys_recorded": False,
        "artifacts": artifacts,
    }
    write_json(manifest_output, manifest)
    if report_output.exists():
        raise FileExistsError(f"Refusing to overwrite: {report_output}")
    report_output.write_text(
        report_markdown(result),
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "status": "ok",
                "eligible_queries": len(attempts),
                "selected_queries": len(differential),
                "baseline_substantive_answers": (
                    aggregate_baseline["substantive_answers"]
                ),
                "candidate_substantive_answers": (
                    aggregate_candidate["substantive_answers"]
                ),
                "baseline_retained_claims": (
                    aggregate_baseline["retained_claims"]
                ),
                "candidate_retained_claims": (
                    aggregate_candidate["retained_claims"]
                ),
                "citation_validity": (
                    aggregate_candidate["citation_validity"]
                ),
                "schema_failures": aggregate_candidate["schema_failures"],
                "decision": status,
                "output_dir": relative(output_dir),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
