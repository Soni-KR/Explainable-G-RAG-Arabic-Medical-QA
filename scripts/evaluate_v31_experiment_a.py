from __future__ import annotations

"""Compare frozen v3 and v3.1 generation over identical Step 11 contexts.

This evaluator is deliberately offline. It reads completed Steps 12-17 runs,
checks that every candidate record reuses the exact baseline Step 11 context,
and exports only newly retained candidate claims for a separate safety review.
"""

import argparse
import json
from pathlib import Path
from typing import Any

from compare_evidence_adaptive_v4 import (
    add_latency_aggregate,
    aggregate,
    delta,
    differential_rows,
    load_jsonl,
    preserve_reviews,
    relative,
    require_complete_pair,
    resolve_run_file,
    review_summary,
    summarize_run,
    write_csv,
    write_json,
)


ROOT = Path(__file__).resolve().parents[1]
REVIEW_FIELDS = (
    "review_decision",
    "safety_error_types",
    "reviewer_notes",
    "reviewer_type",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate v3.1 against v3 over two exact frozen-context cohorts."
        )
    )
    parser.add_argument("--v3-cohort-a", type=Path, required=True)
    parser.add_argument("--v31-cohort-a", type=Path, required=True)
    parser.add_argument("--v3-cohort-b", type=Path, required=True)
    parser.add_argument("--v31-cohort-b", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def rename_differential_fields(
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Replace legacy v4 field names inherited from the shared comparator."""

    renamed: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        item["candidate_claim"] = item.pop("v4_claim")
        item["candidate_citations"] = item.pop("v4_citations")
        item["closest_baseline_claim"] = item.pop("closest_v3_claim")
        item["closest_baseline_similarity"] = item.pop(
            "closest_v3_similarity"
        )
        item["differential_type"] = (
            str(item.get("differential_type") or "")
            .replace("_from_v3", "_from_baseline")
            .replace("_by_v3", "_by_baseline")
        )
        renamed.append(item)
    return renamed


def acceptance_gates(
    baseline: dict[str, Any],
    candidate: dict[str, Any],
    review: dict[str, Any],
) -> dict[str, Any]:
    gates = {
        "substantive_answers_at_least_baseline": (
            candidate["substantive_answers"]
            >= baseline["substantive_answers"]
        ),
        "retained_claims_at_least_baseline": (
            candidate["surviving_claims"] >= baseline["surviving_claims"]
        ),
        "schema_failures_zero": candidate["schema_failures"] == 0,
        "citation_validity_one": candidate["citation_validity"] == 1.0,
        "differential_review_complete": review["review_complete"],
        "unsafe_differential_claims_zero": (
            review["review_complete"] and review["unsafe_claims"] == 0
        ),
    }
    return {
        "passed": all(gates.values()),
        "gates": gates,
    }


def report_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# Experiment A: Frozen v3 versus v3.1",
        "",
        "Only Steps 12-17 differ. Both variants use the exact same saved Step 11",
        "context for every query. Verifier v5, semantic adjudication, and retrieval",
        "rescue are disabled.",
        "",
        f"**Decision: {result['decision']}**",
        "",
        "## Results",
        "",
        "| Scope | Version | Substantive answers | Retained claims | "
        "Pre-mitigation support | Technical/schema failures | "
        "Citation validity | BERTScore F1 |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    labels = {
        "cohort_a": "AHD reference 100",
        "cohort_b": "Entity-GT 100",
        "aggregate_200": "Aggregate 200",
    }
    for scope in ("cohort_a", "cohort_b", "aggregate_200"):
        for version in ("v3", "v3_1"):
            summary = result[scope][version]
            lines.append(
                f"| {labels[scope]} | {version} | "
                f"{summary['substantive_answers']} | "
                f"{summary['surviving_claims']} | "
                f"{summary['pre_mitigation_claims']['supported_claim_rate']:.3f} | "
                f"{summary['technical_failures']}/{summary['schema_failures']} | "
                f"{summary['citation_validity']:.3f} | "
                f"{float(summary['bertscore'].get('bertscore_f1') or 0.0):.6f} |"
            )

    lines.extend(
        [
            "",
            "BERTScore covers substantive post-mitigation answers only.",
            "",
            "## Acceptance Gates",
            "",
        ]
    )
    for name, passed in result["acceptance"]["gates"].items():
        lines.append(f"- `{name}`: **{str(passed).lower()}**")

    review = result["differential_review"]
    lines.extend(
        [
            "",
            "## Differential Safety Review",
            "",
            f"- Candidate-only claims requiring review: "
            f"{review['differential_claims']}",
            f"- Review complete: {review['review_complete']}",
            f"- Unsafe claims confirmed: {review['unsafe_claims']}",
            f"- Automatically invalid citations: "
            f"{review['automatic_invalid_citations']}",
            "",
            "Review each queued claim for wrong drugs/diseases, changed clinical",
            "relations, anatomy/laterality errors, altered numbers or negation,",
            "and unsupported recommendations.",
            "",
            "## Artifacts",
            "",
        ]
    )
    for name, path in result["artifacts"].items():
        lines.append(f"- `{name}`: `{path}`")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    paths = {
        "v3_a": resolve_run_file(args.v3_cohort_a),
        "v31_a": resolve_run_file(args.v31_cohort_a),
        "v3_b": resolve_run_file(args.v3_cohort_b),
        "v31_b": resolve_run_file(args.v31_cohort_b),
    }
    records = {name: load_jsonl(path) for name, path in paths.items()}

    # This fails before creating outputs if query IDs or Step 11 contexts differ.
    require_complete_pair(
        "ahd_reference_100", records["v3_a"], records["v31_a"]
    )
    require_complete_pair(
        "entity_ground_truth_100", records["v3_b"], records["v31_b"]
    )

    summaries = {
        name: summarize_run(paths[name], records[name])
        for name in ("v3_a", "v31_a", "v3_b", "v31_b")
    }
    aggregate_v3 = aggregate([summaries["v3_a"], summaries["v3_b"]])
    aggregate_v31 = aggregate([summaries["v31_a"], summaries["v31_b"]])
    add_latency_aggregate(
        aggregate_v3, records["v3_a"] + records["v3_b"]
    )
    add_latency_aggregate(
        aggregate_v31, records["v31_a"] + records["v31_b"]
    )

    output_dir = (
        args.output_dir
        if args.output_dir.is_absolute()
        else ROOT / args.output_dir
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    audit_path = output_dir / "differential_claim_review_queue.csv"
    differential = rename_differential_fields(
        differential_rows(
            "ahd_reference_100", records["v3_a"], records["v31_a"]
        )
        + differential_rows(
            "entity_ground_truth_100",
            records["v3_b"],
            records["v31_b"],
        )
    )
    differential = preserve_reviews(audit_path, differential)
    review = review_summary(differential)
    acceptance = acceptance_gates(aggregate_v3, aggregate_v31, review)

    if acceptance["passed"]:
        decision = "ACCEPT_V3_1"
    elif not review["review_complete"]:
        decision = "PENDING_DIFFERENTIAL_REVIEW"
    else:
        decision = "KEEP_V3"

    metrics_path = output_dir / "comparison_metrics.json"
    report_path = output_dir / "EXPERIMENT_A.md"
    manifest_path = output_dir / "manifest.json"
    result = {
        "cohort_a": {
            "v3": summaries["v3_a"],
            "v3_1": summaries["v31_a"],
            "delta": delta(summaries["v3_a"], summaries["v31_a"]),
        },
        "cohort_b": {
            "v3": summaries["v3_b"],
            "v3_1": summaries["v31_b"],
            "delta": delta(summaries["v3_b"], summaries["v31_b"]),
        },
        "aggregate_200": {
            "v3": aggregate_v3,
            "v3_1": aggregate_v31,
            "delta": delta(aggregate_v3, aggregate_v31),
        },
        "differential_review": review,
        "acceptance": acceptance,
        "decision": decision,
        "artifacts": {
            "comparison_metrics": relative(metrics_path),
            "differential_claim_review_queue": relative(audit_path),
            "experiment_report": relative(report_path),
            "manifest": relative(manifest_path),
        },
    }

    fields = list(differential[0]) if differential else [
        "differential_id",
        *REVIEW_FIELDS,
    ]
    write_csv(audit_path, differential, fields)
    write_json(metrics_path, result)
    write_json(
        manifest_path,
        {
            "analysis_only": True,
            "pipeline_steps_rerun": [],
            "exact_frozen_context_required": True,
            "verifier_v5_enabled": False,
            "semantic_adjudication_enabled": False,
            "retrieval_rescue_enabled": False,
            "inputs": {name: relative(path) for name, path in paths.items()},
            "outputs": result["artifacts"],
        },
    )
    report_path.write_text(report_markdown(result), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": decision,
                "v3_substantive": aggregate_v3["substantive_answers"],
                "v31_substantive": aggregate_v31["substantive_answers"],
                "v3_claims": aggregate_v3["surviving_claims"],
                "v31_claims": aggregate_v31["surviving_claims"],
                "differential_claims": len(differential),
                "output_dir": relative(output_dir),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
