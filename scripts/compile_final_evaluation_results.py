"""Compile the retained evaluation artifacts into one reproducible summary.

This script is deliberately read-only with respect to the graph and pipeline. It
does not call an API, query Neo4j, rerun retrieval, or change any annotations.
It only aggregates existing JSON/JSONL artifacts and writes the two final
evaluation summaries.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path
from statistics import median
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
EVALUATION = ROOT / "outputs" / "evaluation"
FINAL_RUN_ID = "full_pipeline_retrieval_v2_targeted_fts_reranked_network_v1"

FINAL_GENERATION_DIR = EVALUATION / "generation" / FINAL_RUN_ID
FINAL_RECORDS = FINAL_GENERATION_DIR / "full_pipeline.jsonl"
FINAL_METRICS = FINAL_GENERATION_DIR / "metrics.json"
FINAL_MANIFEST = FINAL_GENERATION_DIR / "manifest.json"

EXPANSION_SUMMARY = (
    EVALUATION
    / "retrieval_expansion"
    / "combined_pool_v2_analysis_final"
    / "summary.json"
)
STEP11_REPLAY = (
    EVALUATION
    / "retrieval_expansion"
    / "targeted_fts_production_step11_replay_v2_metrics.json"
)
RETRIEVAL_ABLATION = EVALUATION / "retrieval" / "ablation_100q" / "metrics.json"
RETRIEVAL_V2_VALIDATION = (
    EVALUATION
    / "retrieval"
    / "evaluation_v1_retrieval_v2_targeted_fts"
    / "validation.json"
)
RETRIEVAL_V2_MANIFEST = (
    EVALUATION
    / "retrieval"
    / "evaluation_v1_retrieval_v2_targeted_fts"
    / "manifest.json"
)
RERANKER_MODEL = ROOT / "models" / "candidate_reranker_two_stage_v2_post_step11.json"
GRAPH_MANIFEST = ROOT / "outputs" / "final_graph" / "graph_manifest.json"
ORIGINAL_CANDIDATE_ANNOTATIONS = (
    ROOT / "data" / "evaluation" / "candidate_relevance_annotations_100_final.csv"
)
OFFLINE_METRICS_DIR = (
    EVALUATION / "offline_metrics" / "final_run_ahd_reference_v1"
)
OFFLINE_METRICS = OFFLINE_METRICS_DIR / "metrics.json"
OFFLINE_MANIFEST = OFFLINE_METRICS_DIR / "manifest.json"
OFFLINE_BERTSCORE = OFFLINE_METRICS_DIR / "bertscore.jsonl"

OUTPUT_JSON = EVALUATION / "FINAL_RESULTS.json"
OUTPUT_MARKDOWN = EVALUATION / "FINAL_RESULTS.md"


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


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


def candidate_channel_yields(path: Path) -> dict[str, dict[str, Any]]:
    channels: dict[str, Counter[str]] = {}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            channel = str(row.get("retrieval_channel") or "unknown")
            label = str(row.get("relevance_label") or "")
            channels.setdefault(channel, Counter())["candidates"] += 1
            channels[channel][f"label_{label}"] += 1
    results: dict[str, dict[str, Any]] = {}
    for channel, counts in sorted(channels.items()):
        candidates = counts["candidates"]
        direct = counts["label_2"]
        useful = counts["label_1"] + direct
        results[channel] = {
            "candidates": candidates,
            "label_0": counts["label_0"],
            "label_1": counts["label_1"],
            "label_2": direct,
            "useful_yield": round_value(useful / candidates if candidates else None),
            "direct_yield": round_value(direct / candidates if candidates else None),
        }
    return results


def nested(record: dict[str, Any], *keys: str, default: Any = None) -> Any:
    value: Any = record
    for key in keys:
        if not isinstance(value, dict):
            return default
        value = value.get(key, default)
    return value


def round_value(value: float | int | None, digits: int = 6) -> float | None:
    if value is None:
        return None
    return round(float(value), digits)


def percentile(values: list[float], percentile_value: float) -> float:
    """Return a linearly interpolated percentile without optional dependencies."""
    if not values:
        return 0.0
    ordered = sorted(values)
    position = (len(ordered) - 1) * percentile_value
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] + fraction * (ordered[upper] - ordered[lower])


def latency_summary(records: list[dict[str, Any]]) -> dict[str, dict[str, float]]:
    stage_names = sorted(
        {
            stage
            for row in records
            for stage in (row.get("timings_ms", {}) or {})
        }
    )
    summary: dict[str, dict[str, float]] = {}
    for stage in stage_names:
        values = [
            float((row.get("timings_ms", {}) or {}).get(stage, 0.0) or 0.0)
            for row in records
        ]
        summary[stage] = {
            "mean_ms": round_value(sum(values) / len(values)) or 0.0,
            "median_ms": round_value(median(values)) or 0.0,
            "p95_ms": round_value(percentile(values, 0.95)) or 0.0,
            "total_ms": round_value(sum(values)) or 0.0,
        }
    return summary


def offline_bertscore_summary(path: Path) -> dict[str, Any] | None:
    """Rebuild the completed local score if a partial RAGAS run rewrote metrics.json."""
    if not path.exists():
        return None
    records = load_jsonl(path)
    scopes = {
        "all_100": records,
        "generated_66": [
            row for row in records if row.get("generation_status") == "generated"
        ],
        "substantive_26": [row for row in records if row.get("substantive")],
    }
    return {
        scope: {
            "evaluated_queries": len(selected),
            "precision": round_value(
                sum(float(row["precision"]) for row in selected) / len(selected)
            ),
            "recall": round_value(
                sum(float(row["recall"]) for row in selected) / len(selected)
            ),
            "f1": round_value(
                sum(float(row["f1"]) for row in selected) / len(selected)
            ),
        }
        for scope, selected in scopes.items()
        if selected
    }


def outcome_summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    answerability = Counter(str(row.get("answerability", "unknown")) for row in records)
    post_claims = sum(len(row.get("output_claims", []) or []) for row in records)
    claim_bearing = sum(bool(row.get("output_claims")) for row in records)
    coverage = [float(row.get("query_coverage", 0.0) or 0.0) for row in records]
    return {
        "queries": len(records),
        "answerability": dict(answerability),
        "claim_bearing_queries": claim_bearing,
        "substantive_answer_rate": round_value(
            claim_bearing / len(records) if records else None
        ),
        "post_mitigation_claims": post_claims,
        "average_query_coverage": round_value(
            sum(coverage) / len(coverage) if coverage else None
        ),
        "latency": latency_summary(records),
    }


def aggregate_final_generation(records: list[dict[str, Any]]) -> dict[str, Any]:
    generation_status = Counter(str(row.get("generation_status", "unknown")) for row in records)
    answerability = Counter(str(row.get("answerability", "unknown")) for row in records)
    fallback_types = Counter(
        str(nested(row, "raw", "generated", "fallback_type", default="") or "none")
        for row in records
    )
    technical_failure_categories: Counter[str] = Counter()
    for row in records:
        if nested(row, "raw", "generated", "fallback_type", default="") != "technical_failure":
            continue
        reason = str(
            nested(row, "raw", "generated", "fallback_reason", default="") or ""
        )
        if "json_validate_failed" in reason or "missing properties" in reason:
            category = "provider_response_schema_validation_failed"
        elif "HTTPError 429" in reason:
            category = "rate_limit"
        elif "URLError" in reason:
            category = "network_error"
        else:
            category = "other_technical_failure"
        technical_failure_categories[category] += 1
    reliability_labels = Counter(
        str(nested(row, "raw", "reliability", "label", default="unknown"))
        for row in records
    )
    context_sizes = [
        len(nested(row, "raw", "context", "evidence_items", default=[]) or [])
        for row in records
    ]
    reliability_scores = [
        float(nested(row, "raw", "reliability", "score", default=0.0) or 0.0)
        for row in records
    ]

    verifications = [
        verification
        for row in records
        for verification in (nested(row, "raw", "verifications", default=[]) or [])
    ]
    verification_status = Counter(
        str(verification.get("status", "unknown")) for verification in verifications
    )
    removed_verifications = [
        verification
        for verification in verifications
        if verification.get("status") != "supported"
    ]
    removal_failed_checks = Counter(
        str(check)
        for verification in removed_verifications
        for check in (verification.get("failed_checks", []) or [])
    )
    removal_statuses = Counter(
        str(verification.get("status", "unknown"))
        for verification in removed_verifications
    )
    pre_claim_count = sum(
        len(nested(row, "raw", "claims", default=[]) or []) for row in records
    )
    post_claim_count = sum(len(row.get("output_claims", []) or []) for row in records)
    removed_claim_count = sum(
        len(nested(row, "raw", "mitigated", "removed_claims", default=[]) or [])
        for row in records
    )
    kept_query_count = sum(1 for row in records if row.get("output_claims"))
    query_coverage = [float(row.get("query_coverage", 0.0) or 0.0) for row in records]

    pre_supported = verification_status["supported"]
    pre_weak = verification_status["weakly_supported"]
    pre_unsupported = verification_status["unsupported"]
    generated_records = [
        row for row in records if str(row.get("generation_status")) == "generated"
    ]
    fallback_records = [
        row for row in records if str(row.get("generation_status")) == "fallback"
    ]
    empty_context_records = [
        row
        for row in records
        if not (nested(row, "raw", "context", "evidence_items", default=[]) or [])
    ]
    nonempty_context_records = [
        row
        for row in records
        if nested(row, "raw", "context", "evidence_items", default=[]) or []
    ]

    def context_outcomes(subset: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "queries": len(subset),
            "generation_status": dict(
                Counter(str(row.get("generation_status", "unknown")) for row in subset)
            ),
            "fallback_types": dict(
                Counter(
                    str(
                        nested(
                            row,
                            "raw",
                            "generated",
                            "fallback_type",
                            default="",
                        )
                        or "none"
                    )
                    for row in subset
                )
            ),
            "answerability": dict(
                Counter(str(row.get("answerability", "unknown")) for row in subset)
            ),
            "claim_bearing_queries": sum(bool(row.get("output_claims")) for row in subset),
        }

    return {
        "query_count": len(records),
        "generation_status": dict(generation_status),
        "fallback_types": dict(fallback_types),
        "answerability": dict(answerability),
        "queries_with_nonempty_context": sum(size > 0 for size in context_sizes),
        "queries_with_post_mitigation_claims": kept_query_count,
        "average_context_items": round_value(sum(context_sizes) / len(context_sizes)),
        "maximum_context_items": max(context_sizes, default=0),
        "pre_mitigation": {
            "claims": pre_claim_count,
            "supported": pre_supported,
            "weakly_supported": pre_weak,
            "unsupported": pre_unsupported,
            "support_or_weak_rate": round_value(
                (pre_supported + pre_weak) / pre_claim_count if pre_claim_count else None
            ),
            "unsupported_rate": round_value(
                pre_unsupported / pre_claim_count if pre_claim_count else None
            ),
        },
        "post_mitigation": {
            "claims": post_claim_count,
            "removed_claims": removed_claim_count,
            "claim_removal_rate": round_value(
                removed_claim_count / pre_claim_count if pre_claim_count else None
            ),
            "removed_verification_statuses": dict(removal_statuses),
            "removal_failed_checks": dict(removal_failed_checks.most_common()),
        },
        "average_query_coverage": round_value(
            sum(query_coverage) / len(query_coverage) if query_coverage else None
        ),
        "reliability": {
            "labels": dict(reliability_labels),
            "average_score": round_value(
                sum(reliability_scores) / len(reliability_scores)
                if reliability_scores
                else None
            ),
            "minimum_score": round_value(min(reliability_scores, default=0.0)),
            "maximum_score": round_value(max(reliability_scores, default=0.0)),
            "audit_disposition": {
                "accept": reliability_labels["high"],
                "flag": reliability_labels["medium"],
                "abstain": reliability_labels["low"],
                "mapping": {
                    "accept": "high reliability, score >= 0.80",
                    "flag": "medium reliability, 0.55 <= score < 0.80",
                    "abstain": "low reliability, score < 0.55",
                },
                "note": (
                    "This is an audit mapping of existing Step 16 labels, not a "
                    "new production threshold."
                ),
            },
            "calibration_status": "unavailable",
            "calibration_reason": (
                "No independent answer-correctness labels exist for AUROC, AUPRC, "
                "or calibration analysis."
            ),
        },
        "generated_only": outcome_summary(generated_records),
        "fallback_only": outcome_summary(fallback_records),
        "end_to_end": outcome_summary(records),
        "context_outcomes": {
            "empty": context_outcomes(empty_context_records),
            "nonempty": context_outcomes(nonempty_context_records),
        },
        "failure_attribution": {
            "retrieval_empty_context": len(empty_context_records),
            "api_or_generation_technical_failure": fallback_types["technical_failure"],
            "technical_failure_categories": dict(technical_failure_categories),
            "generated_but_no_claim_survived": sum(
                1
                for row in generated_records
                if not row.get("output_claims")
                and str(row.get("answerability")) == "insufficient_evidence"
            ),
            "substantive_claim_bearing_answer": kept_query_count,
        },
    }


def extract_historical_generation() -> list[dict[str, Any]]:
    run_ids = [
        "evaluation_v1_claimfirst_pilot_3q_v1",
        "evaluation_v1_e2e_full_hybrid_semanticfix_100q_v1",
        "evaluation_v1_e2e_full_hybrid_evidencelocal_100q_v1",
        "evaluation_v1_e2e_full_hybrid_verifierfix3_100q_v1",
        "evaluation_v1_e2e_full_hybrid_verifierfix4_100q_v1",
        "evaluation_v1_e2e_lexical_only_100q_v2",
        "pilot_15q",
    ]
    rows: list[dict[str, Any]] = []
    for run_id in run_ids:
        path = EVALUATION / "generation" / run_id / "metrics.json"
        if not path.exists():
            continue
        payload = load_json(path)
        mode_name, metrics = next(iter(payload.items()))
        bert = metrics.get("bertscore", {})
        grounding = metrics.get("claim_grounding", {})
        citation = metrics.get("citation_validity", {})
        efficiency = metrics.get("efficiency", {})
        rows.append(
            {
                "run_id": run_id,
                "mode": mode_name,
                "bertscore_f1": bert.get("bertscore_f1"),
                "bertscore_query_count": bert.get("evaluated_query_count"),
                "claim_support_rate": grounding.get("claim_support_rate"),
                "claim_query_count": grounding.get("evaluated_query_count"),
                "hallucination_rate": grounding.get("hallucination_rate"),
                "citation_validity": citation.get("citation_validity"),
                "citation_query_count": citation.get("evaluated_query_count"),
                "average_end_to_end_latency_ms": nested(
                    efficiency, "average_latency_ms", "end_to_end"
                ),
                "status": "historical_non_comparable",
            }
        )
    return rows


def build_summary() -> dict[str, Any]:
    final_records = load_jsonl(FINAL_RECORDS)
    final_metrics = load_json(FINAL_METRICS)
    final_manifest = load_json(FINAL_MANIFEST)
    expansion = load_json(EXPANSION_SUMMARY)
    step11 = load_json(STEP11_REPLAY)
    retrieval_ablation = load_json(RETRIEVAL_ABLATION)
    retrieval_v2_validation = load_json(RETRIEVAL_V2_VALIDATION)
    retrieval_v2_manifest = load_json(RETRIEVAL_V2_MANIFEST)
    reranker = load_json(RERANKER_MODEL)
    graph = load_json(GRAPH_MANIFEST)
    automatic_metrics = load_json(OFFLINE_METRICS) if OFFLINE_METRICS.exists() else {}
    automatic_manifest = (
        load_json(OFFLINE_MANIFEST) if OFFLINE_MANIFEST.exists() else {}
    )
    bertscore = automatic_metrics.get("bertscore") or offline_bertscore_summary(
        OFFLINE_BERTSCORE
    )

    final_generation = aggregate_final_generation(final_records)
    final_generation["reported_metrics"] = final_metrics["full_pipeline"]

    return {
        "status": "complete",
        "scope": (
            "Frozen final_v1 graph; human-confirmed candidate relevance; "
            "retrieval_v2 conditional targeted FTS; 100-query generation."
        ),
        "graph": graph,
        "retrieval": {
            "candidate_pool_and_expansion": expansion,
            "original_channel_yields": candidate_channel_yields(
                ORIGINAL_CANDIDATE_ANNOTATIONS
            ),
            "retrieval_v2_validation": retrieval_v2_validation,
            "retrieval_v2_configuration": retrieval_v2_manifest,
            "latency_ablation": retrieval_ablation,
        },
        "reranker_experiment": {
            "activation": reranker["activation"],
            "training_rows": reranker["training_rows"],
            "training_queries": reranker["training_queries"],
            "label_counts": reranker["label_counts"],
            "classification": reranker["cross_validated_classification"],
            "ranking": reranker["cross_validated_ranking"]["all_candidates"],
            "decision": (
                "Disabled. OOF ranking improved, but production-style context replay "
                "did not justify activation."
            ),
        },
        "step11_context": step11,
        "final_generation": final_generation,
        "automatic_reference_metrics": {
            "reference_type": "original_ahd_answer",
            "reference_status": (
                "dataset reference for automatic evaluation; not "
                "clinician-adjudicated"
            ),
            "bertscore": bertscore,
            "ragas": automatic_metrics.get("ragas"),
            "ragas_status": automatic_metrics.get("status", "not_run"),
            "manifest": automatic_manifest,
        },
        "final_runtime": {
            "run_id": FINAL_RUN_ID,
            "graph": final_manifest["graph"],
            "models": final_manifest["models"],
            "thresholds": final_manifest["thresholds"],
            "top_k": final_manifest["top_k"],
            "supplemental_graph_used": final_manifest["supplemental_graph_used"],
            "git": final_manifest["git"],
        },
        "historical_generation": extract_historical_generation(),
        "unavailable_metrics": {
            "entity_extraction_precision_recall_f1": (
                "Unavailable: independent entity-extraction ground truth was not "
                "completed in the retained evaluation artifacts."
            ),
            "relation_candidate_recall_triplet_precision_recall_f1": (
                "Unavailable: no independently annotated relation ground truth."
            ),
            "ragas_context_precision_recall": (
                "Incomplete: the offline RAGAS workflow is implemented and uses the "
                "original AHD answers, but the evaluator API quota stopped the full "
                "100-query judge run. Partial scores are not reported as final."
            ),
            "ragas_faithfulness_answer_relevancy": (
                "Incomplete: evaluator-LLM quota stopped the resumable offline run. "
                "No retrieval or generation rerun is required."
            ),
            "reliability_auroc_auprc_calibration": (
                "Unavailable: no independent binary correctness/reliability labels."
            ),
            "step08_accuracy": (
                "Unavailable: query correction, classification, phrase extraction, "
                "and linking do not yet have a human-confirmed Step 8 gold set."
            ),
        },
        "methodology_notes": [
            "All final candidate relevance rows are human-confirmed.",
            "Blank expansion labels were never converted to zero.",
            "The supplemental graph was not used.",
            "The learned reranker was evaluated but remains disabled.",
            "The retrieval_v2 trigger is deterministic and label-free, but its "
            "44-query candidate-availability cohort was identified during development.",
            "Historical generation scores are not directly comparable because prompts, "
            "retrieval, verification, and evaluated query counts changed.",
        ],
    }


def pct(value: float | None) -> str:
    return "unavailable" if value is None else f"{100.0 * value:.2f}%"


def num(value: float | int | None, digits: int = 4) -> str:
    if value is None:
        return "unavailable"
    if isinstance(value, int):
        return f"{value:,}"
    return f"{value:.{digits}f}"


def render_markdown(summary: dict[str, Any]) -> str:
    graph = summary["graph"]["counts"]
    expansion = summary["retrieval"]["candidate_pool_and_expansion"]
    ranking = expansion["ranking_by_pool_rank"]
    reranker = summary["reranker_experiment"]
    rerank_current = reranker["ranking"]["current_candidate_rank"]
    rerank_oof = reranker["ranking"]["two_stage_cross_validated"]
    step11 = summary["step11_context"]
    generation = summary["final_generation"]
    reported = generation["reported_metrics"]
    automatic = summary["automatic_reference_metrics"]
    bertscore = automatic.get("bertscore") or {}
    efficiency = reported["efficiency"]["average_latency_ms"]

    lines = [
        "# Final Evaluation Results",
        "",
        "This is the consolidated record for the frozen `final_v1` graph and the "
        "100-query `retrieval_v2` generation run. It is generated only from retained "
        "artifacts; no API, Neo4j, retrieval, or model call is made by the compiler.",
        "",
        "## Final graph",
        "",
        "| Artifact | Count |",
        "|---|---:|",
        f"| Medical entities | {graph['entities']:,} |",
        f"| Evidence mentions | {graph['entity_mentions']:,} |",
        f"| Relation decisions | {graph['relation_decisions']:,} |",
        f"| Direct relations | {graph['direct_relations']:,} |",
        f"| Bidirectional Neo4j relations | {graph['bidirectional_relations']:,} |",
        f"| QA records | {graph['qa_records_for_import']:,} |",
        "",
        "The 1,404 accepted direct relations came from 3,392 audited relation "
        f"decisions, an acceptance yield of "
        f"{pct(graph['direct_relations'] / graph['relation_decisions'])}. This is an "
        "extraction/validation yield, not Triplet Precision; independent relation gold "
        "does not yet exist.",
        "",
        "## Retrieval candidate coverage",
        "",
        "| Metric | Before expansion | After expansion |",
        "|---|---:|---:|",
        "| Queries with a direct label-2 candidate | 37/99 | 49/99 |",
        "| End-to-end direct candidate coverage | 37/100 | 49/100 |",
        "| Direct Recall@5 | "
        f"{pct(ranking['original_pool_at_5']['direct_recall_at_5_all_queries'])} | "
        f"{pct(ranking['combined_pool_at_5']['direct_recall_at_5_all_queries'])} |",
        "| Direct Recall@10 | not measured | "
        f"{pct(ranking['combined_pool_at_10']['direct_recall_at_10_all_queries'])} |",
        "| MRR, direct candidates | "
        f"{num(ranking['original_pool_at_5']['mrr_direct_all_queries'])} | "
        f"{num(ranking['combined_pool_at_5']['mrr_direct_all_queries'])} |",
        "| nDCG@5 by raw pool rank | "
        f"{num(ranking['original_pool_at_5']['ndcg_at_5_all_queries'])} | "
        f"{num(ranking['combined_pool_at_5']['ndcg_at_5_all_queries'])} |",
        "",
        "The nDCG@5 decrease is not interpreted as degradation because original and "
        "expansion pool ranks were produced by different retrieval passes and are not "
        "directly comparable. The targeted expansion reviewed 412 candidates, rescued "
        "12 of 44 partial-only queries, and achieved "
        f"{pct(expansion['expansion']['reviewed_useful_yield'])} useful yield and "
        f"{pct(expansion['expansion']['reviewed_direct_yield'])} direct yield.",
        "",
        "The frozen conditional artifact processed all 44 target queries, fired on "
        f"{summary['retrieval']['retrieval_v2_validation']['triggered_queries']} queries, "
        "used 483 available raw expansion candidates, and passed every integrity check. "
        "It used neither human labels during construction nor the supplemental graph.",
        "",
        "### Original retrieval-channel labels",
        "",
        "| Channel | Candidates | Label 0 | Label 1 | Label 2 | Useful yield | Direct yield |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for channel, values in summary["retrieval"]["original_channel_yields"].items():
        lines.append(
            f"| `{channel}` | {values['candidates']} | {values['label_0']} | "
            f"{values['label_1']} | {values['label_2']} | "
            f"{pct(values['useful_yield'])} | {pct(values['direct_yield'])} |"
        )
    lines.extend(
        [
        "",
        "FTS QA produced the highest direct yield. Neither graph channel produced a "
        "label-2 candidate in the original 540-candidate human review.",
        "",
        "## Retrieval latency ablation",
        "",
        "| Mode | Retrieval ms | End-to-end with shared Step 8 ms |",
        "|---|---:|---:|",
        ]
    )
    for mode, values in summary["retrieval"]["latency_ablation"].items():
        latency = values["efficiency"]["average_latency_ms"]
        lines.append(
            f"| `{mode}` | {latency['retrieval_mode']:.2f} | {latency['end_to_end']:.2f} |"
        )

    lines.extend(
        [
            "",
            "These ablation results measured latency only. Their Recall/MRR/nDCG fields "
            "were unavailable at run time because the human relevance pool had not yet "
            "been frozen.",
            "",
            "## Reranker experiment",
            "",
            "| Metric | Existing rank | Two-stage grouped OOF |",
            "|---|---:|---:|",
            f"| nDCG@5 | {rerank_current['ndcg_at_5_all_queries']:.4f} | "
            f"{rerank_oof['ndcg_at_5_all_queries']:.4f} |",
            f"| MRR | {rerank_current['mrr_direct_all_queries']:.4f} | "
            f"{rerank_oof['mrr_direct_all_queries']:.4f} |",
            f"| Direct at rank 1 | {rerank_current['direct_at_rank_1_count']} | "
            f"{rerank_oof['direct_at_rank_1_count']} |",
            f"| Useful at rank 1 | {rerank_current['useful_at_rank_1_count']} | "
            f"{rerank_oof['useful_at_rank_1_count']} |",
            f"| Direct retained in top 5 | {rerank_current['queries_retaining_direct_at_5']} | "
            f"{rerank_oof['queries_retaining_direct_at_5']} |",
            f"| Useful precision@3 | {rerank_current['useful_precision_at_3']:.4f} | "
            f"{rerank_oof['useful_precision_at_3']:.4f} |",
            "",
            "Classification scores: usable-vs-irrelevant AUROC "
            f"{reranker['classification']['usable_vs_irrelevant']['roc_auc']:.4f}, "
            "AUPRC "
            f"{reranker['classification']['usable_vs_irrelevant']['average_precision']:.4f}, "
            "F1 "
            f"{reranker['classification']['usable_vs_irrelevant']['f1_at_0_5']:.4f}; "
            "direct-vs-all AUROC "
            f"{reranker['classification']['direct_vs_all']['roc_auc']:.4f}, "
            "AUPRC "
            f"{reranker['classification']['direct_vs_all']['average_precision']:.4f}.",
            "",
            "**Decision:** the learned reranker remains disabled. OOF ranking improved, "
            "but production-style context replay did not demonstrate a sufficiently "
            "reliable gain.",
            "",
            "## Step 11 context selection",
            "",
            "| Metric | Baseline | Targeted FTS |",
            "|---|---:|---:|",
            f"| Queries with context | {step11['baseline']['queries_with_context']} | "
            f"{step11['targeted_expansion']['queries_with_context']} |",
            f"| Queries with known useful context | "
            f"{step11['baseline']['queries_with_known_useful_context']} | "
            f"{step11['targeted_expansion']['queries_with_known_useful_context']} |",
            f"| Queries with known direct context | "
            f"{step11['baseline']['queries_with_known_direct_context']} | "
            f"{step11['targeted_expansion']['queries_with_known_direct_context']} |",
            f"| Useful-candidate precision | "
            f"{pct(step11['baseline']['known_useful_precision'])} | "
            f"{pct(step11['targeted_expansion']['known_useful_precision'])} |",
            f"| Direct-candidate precision | "
            f"{pct(step11['baseline']['known_direct_precision'])} | "
            f"{pct(step11['targeted_expansion']['known_direct_precision'])} |",
            "",
            "Targeted FTS improved useful and direct query coverage. Direct-candidate "
            "precision decreased because more partial evidence was admitted, so Step 11 "
            "still needs better directness gating.",
            "",
        "## Final 100-query generation",
            "",
            f"Run: `{FINAL_RUN_ID}`",
            "",
            "| Metric | Result |",
            "|---|---:|",
            f"| Completed queries | {generation['query_count']} |",
            f"| LLM-generated responses | {generation['generation_status'].get('generated', 0)} |",
            f"| Fallback responses | {generation['generation_status'].get('fallback', 0)} |",
            f"| Insufficient-evidence fallbacks | "
            f"{generation['fallback_types'].get('insufficient_evidence', 0)} |",
            f"| Technical failures | {generation['fallback_types'].get('technical_failure', 0)} |",
            f"| Queries with non-empty Step 11 context | "
            f"{generation['queries_with_nonempty_context']} |",
            f"| Queries retaining verified claims | "
            f"{generation['queries_with_post_mitigation_claims']} |",
            f"| Fully answerable | {generation['answerability'].get('fully_answerable', 0)} |",
            f"| Supported but incomplete | "
            f"{generation['answerability'].get('supported_but_incomplete', 0)} |",
            f"| Partially answerable | "
            f"{generation['answerability'].get('partially_answerable', 0)} |",
            f"| Insufficient evidence | "
            f"{generation['answerability'].get('insufficient_evidence', 0)} |",
            f"| Generation unavailable | "
            f"{generation['answerability'].get('generation_unavailable', 0)} |",
            f"| Average query coverage, all 100 | "
            f"{pct(generation['average_query_coverage'])} |",
            f"| Average query coverage, substantive answers (n=26) | "
            f"{pct(reported['answer_completeness']['average_query_coverage'])} |",
            f"| Post-mitigation claim support | "
            f"{pct(reported['claim_grounding']['claim_support_rate'])} |",
            f"| Post-mitigation hallucination rate | "
            f"{pct(reported['claim_grounding']['hallucination_rate'])} |",
        f"| Citation validity | "
        f"{pct(reported['citation_validity']['citation_validity'])} |",
        f"| Claims with a valid citation | "
        f"{pct(reported['citation_validity']['claims_with_valid_citation_rate'])} |",
        "",
        "**Scope warning:** the post-mitigation claim-support rate of `1.00`, "
        "hallucination rate of `0.00`, and citation validity of `1.00` apply only "
        "to the **26 substantive claim-bearing answers**, containing 36 retained "
        "claims. They are not results over all 100 questions.",
        "",
        "Before mitigation, generation produced "
        f"{generation['pre_mitigation']['claims']} claims: "
        f"{generation['pre_mitigation']['supported']} supported, "
        f"{generation['pre_mitigation']['weakly_supported']} weakly supported, and "
            f"{generation['pre_mitigation']['unsupported']} unsupported. Step 15 removed "
            f"{generation['post_mitigation']['removed_claims']} claims "
            f"({pct(generation['post_mitigation']['claim_removal_rate'])}). This explains "
        "the high safety but low answer coverage.",
        "",
        "### Generated-only versus end-to-end",
        "",
        "| Metric | Generated-only | All 100 queries |",
        "|---|---:|---:|",
        f"| Queries | {generation['generated_only']['queries']} | "
        f"{generation['end_to_end']['queries']} |",
        f"| Queries retaining substantive claims | "
        f"{generation['generated_only']['claim_bearing_queries']} | "
        f"{generation['end_to_end']['claim_bearing_queries']} |",
        f"| Substantive-answer rate | "
        f"{pct(generation['generated_only']['substantive_answer_rate'])} | "
        f"{pct(generation['end_to_end']['substantive_answer_rate'])} |",
        f"| Retained claims | {generation['generated_only']['post_mitigation_claims']} | "
        f"{generation['end_to_end']['post_mitigation_claims']} |",
        f"| Average query coverage | "
        f"{pct(generation['generated_only']['average_query_coverage'])} | "
        f"{pct(generation['end_to_end']['average_query_coverage'])} |",
        f"| Mean end-to-end latency | "
        f"{generation['generated_only']['latency']['end_to_end']['mean_ms']:.2f} ms | "
        f"{generation['end_to_end']['latency']['end_to_end']['mean_ms']:.2f} ms |",
        f"| Median end-to-end latency | "
        f"{generation['generated_only']['latency']['end_to_end']['median_ms']:.2f} ms | "
        f"{generation['end_to_end']['latency']['end_to_end']['median_ms']:.2f} ms |",
        f"| p95 end-to-end latency | "
        f"{generation['generated_only']['latency']['end_to_end']['p95_ms']:.2f} ms | "
        f"{generation['end_to_end']['latency']['end_to_end']['p95_ms']:.2f} ms |",
        f"| Total recorded latency | "
        f"{generation['generated_only']['latency']['end_to_end']['total_ms']:.2f} ms | "
        f"{generation['end_to_end']['latency']['end_to_end']['total_ms']:.2f} ms |",
        f"| BERTScore F1 | "
        f"{num((bertscore.get('generated_66') or {}).get('f1'), 6)} | "
        f"{num((bertscore.get('all_100') or {}).get('f1'), 6)} |",
        "",
        "BERTScore uses the original AHD answer associated with each query as the "
        "dataset reference. It was calculated offline from the frozen answers; it did "
        "not rerun retrieval or generation. The references are not "
        "clinician-adjudicated.",
        "",
        "### Offline reference metrics",
        "",
        "| Scope | Queries | BERTScore precision | Recall | F1 |",
        "|---|---:|---:|---:|---:|",
        f"| All frozen outcomes | "
        f"{num((bertscore.get('all_100') or {}).get('evaluated_queries'))} | "
        f"{num((bertscore.get('all_100') or {}).get('precision'), 6)} | "
        f"{num((bertscore.get('all_100') or {}).get('recall'), 6)} | "
        f"{num((bertscore.get('all_100') or {}).get('f1'), 6)} |",
        f"| LLM-generated outcomes | "
        f"{num((bertscore.get('generated_66') or {}).get('evaluated_queries'))} | "
        f"{num((bertscore.get('generated_66') or {}).get('precision'), 6)} | "
        f"{num((bertscore.get('generated_66') or {}).get('recall'), 6)} | "
        f"{num((bertscore.get('generated_66') or {}).get('f1'), 6)} |",
        f"| Substantive claim-bearing answers | "
        f"{num((bertscore.get('substantive_26') or {}).get('evaluated_queries'))} | "
        f"{num((bertscore.get('substantive_26') or {}).get('precision'), 6)} | "
        f"{num((bertscore.get('substantive_26') or {}).get('recall'), 6)} | "
        f"{num((bertscore.get('substantive_26') or {}).get('f1'), 6)} |",
        "",
        "RAGAS context recall, context precision, faithfulness, and answer relevancy "
        "are implemented as a resumable post-hoc evaluation over the same frozen "
        "records. Their evaluator-LLM run is incomplete because the configured Groq "
        f"quota stopped it (`status={automatic.get('ragas_status', 'not_run')}`). "
        "Partial judge scores are intentionally not presented as final metrics.",
        "",
        "### Claim removal",
        "",
        "| Removal classification | Count |",
        "|---|---:|",
    ]
    )
    for status, count in generation["post_mitigation"][
        "removed_verification_statuses"
    ].items():
        lines.append(f"| `{status}` | {count} |")
    lines.extend(
        [
            "",
            "| Failed verification check | Removed claims affected |",
            "|---|---:|",
        ]
    )
    for reason, count in generation["post_mitigation"]["removal_failed_checks"].items():
        lines.append(f"| `{reason}` | {count} |")

    lines.extend(
        [
            "",
            "A removed claim can fail more than one check, so failed-check counts can "
            "sum to more than the 78 removed claims.",
            "",
            "### Empty versus non-empty context",
            "",
            "| Outcome | Empty context | Non-empty context |",
            "|---|---:|---:|",
            f"| Queries | {generation['context_outcomes']['empty']['queries']} | "
            f"{generation['context_outcomes']['nonempty']['queries']} |",
            f"| Generated | "
            f"{generation['context_outcomes']['empty']['generation_status'].get('generated', 0)} | "
            f"{generation['context_outcomes']['nonempty']['generation_status'].get('generated', 0)} |",
            f"| Fallback | "
            f"{generation['context_outcomes']['empty']['generation_status'].get('fallback', 0)} | "
            f"{generation['context_outcomes']['nonempty']['generation_status'].get('fallback', 0)} |",
            f"| Substantive claim-bearing answer | "
            f"{generation['context_outcomes']['empty']['claim_bearing_queries']} | "
            f"{generation['context_outcomes']['nonempty']['claim_bearing_queries']} |",
            f"| Final insufficient evidence | "
            f"{generation['context_outcomes']['empty']['answerability'].get('insufficient_evidence', 0)} | "
            f"{generation['context_outcomes']['nonempty']['answerability'].get('insufficient_evidence', 0)} |",
            f"| Generation unavailable | "
            f"{generation['context_outcomes']['empty']['answerability'].get('generation_unavailable', 0)} | "
            f"{generation['context_outcomes']['nonempty']['answerability'].get('generation_unavailable', 0)} |",
            "",
            "Failure attribution: "
            f"{generation['failure_attribution']['retrieval_empty_context']} queries "
            "failed upstream with empty retrieval context; "
            f"{generation['failure_attribution']['api_or_generation_technical_failure']} "
            "had API/generation technical failures despite context "
            f"({generation['failure_attribution']['technical_failure_categories'].get('provider_response_schema_validation_failed', 0)} "
            "provider response-schema validation failures); and "
            f"{generation['failure_attribution']['generated_but_no_claim_survived']} "
            "received generated text but no claim survived verification/mitigation.",
            "",
            "### Reliability and disposition",
            "",
            "| Reliability band | Audit disposition | Count |",
            "|---|---|---:|",
            f"| High, score >= 0.80 | accept | "
            f"{generation['reliability']['audit_disposition']['accept']} |",
            f"| Medium, 0.55 <= score < 0.80 | flag | "
            f"{generation['reliability']['audit_disposition']['flag']} |",
            f"| Low, score < 0.55 | abstain | "
            f"{generation['reliability']['audit_disposition']['abstain']} |",
            "",
            f"Mean reliability was {generation['reliability']['average_score']:.4f}; "
            f"minimum {generation['reliability']['minimum_score']:.4f}; maximum "
            f"{generation['reliability']['maximum_score']:.4f}. The accept/flag/abstain "
            "mapping is an audit interpretation of the existing high/medium/low bands, "
            "not a new pipeline rule. Scores are uncalibrated.",
            "",
            "### Final latency",
        "",
        "| Stage | Mean ms | Median ms | p95 ms | Total ms |",
        "|---|---:|---:|---:|---:|",
        ]
    )
    for stage, values in generation["end_to_end"]["latency"].items():
        lines.append(
            f"| `{stage}` | {values['mean_ms']:.2f} | {values['median_ms']:.2f} | "
            f"{values['p95_ms']:.2f} | {values['total_ms']:.2f} |"
        )

    lines.extend(
        [
            "",
            "The end-to-end timing includes local processing, API time, configured "
            "request pacing, and retries captured inside each query record. Reused frozen "
            "Step 8 and retrieval stages are recorded as zero in this generation-only run. "
            "The total is the sum of recorded per-query timings and excludes downtime "
            "between manual resume commands and waiting for daily quota resets.",
            "",
            "## Steps 8-17 in the frozen pipeline",
            "",
            "1. **Step 8, query understanding:** conservative Arabic normalization; one "
            "GPT-OSS-20B structured analysis call; deterministic exact/alias Neo4j "
            "linking; deterministic retrieval planning.",
            "2. **Step 9, hybrid retrieval:** vector entity/evidence/QA search, one-hop "
            "final_v1 graph traversal, direct held-out-safe QA FTS, deduplication, and "
            "conditional targeted FTS only when ordinary context is partial and lacks "
            "strong direct evidence.",
            "3. **Step 10, reranking:** deterministic identity, anatomy, intent, source, "
            "semantic, and concept-coverage scoring. The experimental learned reranker "
            "remains disabled.",
            "4. **Step 11, context construction:** absolute quality gates, concept and "
            "intent coverage checks, unrelated-condition filtering, deduplication, and a "
            "maximum of six focused evidence items.",
            "5. **Step 12, generation:** one evidence-grounded GPT-OSS-20B call using only "
            "the Step 11 context and requiring citations.",
            "6. **Step 13, claim extraction:** deterministic extraction of factual claims "
            "and citations from the generated response.",
            "7. **Step 14, verification:** each claim must be supported by a cited evidence "
            "item and relevant to the query's concepts and intent.",
            "8. **Step 15, hallucination mitigation:** unsupported and weak claims are "
            "removed; the system abstains when no substantive claim survives.",
            "9. **Step 16, reliability:** deterministic uncalibrated score combining claim "
            "support, evidence coverage, relation confidence, source quality, and "
            "answerability.",
            "10. **Step 17, explainable output:** final answer, answerability state, "
            "reliability, supporting entities/relations/evidence, claim audit, removed "
            "claims, warnings, and timing.",
            "",
            "## Historical generation scores",
            "",
            "These runs are retained for traceability, not head-to-head comparison.",
            "",
            "| Run | BERTScore F1 (n) | Claim support (n) | Hallucination | Citation validity (n) | E2E ms |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for row in summary["historical_generation"]:
        bert = (
            "unavailable"
            if row["bertscore_f1"] is None
            else f"{row['bertscore_f1']:.4f} ({row['bertscore_query_count']})"
        )
        support = (
            "unavailable"
            if row["claim_support_rate"] is None
            else f"{row['claim_support_rate']:.4f} ({row['claim_query_count']})"
        )
        hallucination = (
            "unavailable"
            if row["hallucination_rate"] is None
            else f"{row['hallucination_rate']:.4f}"
        )
        citation = (
            "unavailable"
            if row["citation_validity"] is None
            else f"{row['citation_validity']:.4f} ({row['citation_query_count']})"
        )
        latency = (
            "unavailable"
            if row["average_end_to_end_latency_ms"] is None
            else f"{row['average_end_to_end_latency_ms']:.2f}"
        )
        lines.append(
            f"| `{row['run_id']}` | {bert} | {support} | {hallucination} | "
            f"{citation} | {latency} |"
        )

    lines.extend(
        [
            "",
            "## Exact final artifact paths",
            "",
            "- Frozen graph: `outputs/final_graph/entities.csv`, "
            "`outputs/final_graph/entity_mentions.csv`, "
            "`outputs/final_graph/relation_decisions.csv`, "
            "`outputs/final_graph/relations.csv`, "
            "`outputs/final_graph/relations_bidirectional.csv`.",
            "- Graph manifest: `outputs/final_graph/graph_manifest.json`.",
            "- Neo4j backup with embeddings/index data: "
            "`neo4j_dump/step05_final_v1_neo4j.dump`.",
            "- Human candidate annotations: "
            "`data/evaluation/candidate_relevance_annotations_100_final.csv`.",
            "- Human-confirmed combined pool: "
            "`data/evaluation/candidate_relevance_combined_pool_v2.csv`.",
            "- Replay-ready combined pool: "
            "`data/evaluation/candidate_relevance_combined_pool_v2_replay_ready.csv`.",
            "- Retrieval-v2 candidates and final Step 11 states: "
            "`outputs/evaluation/retrieval/evaluation_v1_retrieval_v2_targeted_fts/"
            "full_hybrid_targeted_fts.jsonl`.",
            "- Retrieval-v2 manifest, validation, and decisions: "
            "`outputs/evaluation/retrieval/evaluation_v1_retrieval_v2_targeted_fts/"
            "manifest.json`, `validation.json`, and `decisions.csv`.",
            "- Targeted expansion analysis: "
            "`outputs/evaluation/retrieval_expansion/"
            "combined_pool_v2_analysis_final/summary.json`.",
            "- Step 11 production replay metrics: "
            "`outputs/evaluation/retrieval_expansion/"
            "targeted_fts_production_step11_replay_v2_metrics.json`.",
            "- Frozen final generation records: "
            f"`outputs/evaluation/generation/{FINAL_RUN_ID}/full_pipeline.jsonl`.",
            "- Frozen final generation metrics and manifest: "
            f"`outputs/evaluation/generation/{FINAL_RUN_ID}/metrics.json` and "
            f"`outputs/evaluation/generation/{FINAL_RUN_ID}/manifest.json`.",
            "- Final claim audit: "
            f"`outputs/evaluation/claim_audit/{FINAL_RUN_ID}/full_pipeline.jsonl` and "
            f"`outputs/evaluation/claim_audit/{FINAL_RUN_ID}/manifest.json`.",
            "- Append-only successful-call cache: "
            f"`outputs/evaluation/cache/{FINAL_RUN_ID}/`.",
            "- Offline BERTScore/RAGAS artifacts: "
            "`outputs/evaluation/offline_metrics/final_run_ahd_reference_v1/`.",
            "- Hallucination-mitigation seed and leakage manifest: "
            "`data/training/hallucination_mitigation_seed_v1/`.",
            "- Consolidated audit: `outputs/evaluation/FINAL_RESULTS.md` and "
            "`outputs/evaluation/FINAL_RESULTS.json`.",
            "",
            "## Metrics still unavailable",
            "",
        ]
    )
    for metric, reason in summary["unavailable_metrics"].items():
        lines.append(f"- `{metric}`: {reason}")

    lines.extend(
        [
            "",
            "## Current conclusion",
            "",
            "The strongest verified improvement is the conditional FTS fallback: direct "
            "candidate coverage rose from 37/99 to 49/99, while production Step 11 useful "
            "context coverage rose from 51 to 56 queries and direct context from 25 to 29. "
            "The final verifier achieved perfect support and citation validity on retained "
            "claims, but only 26/100 queries retained substantive claims. The next research "
            "priority is therefore retrieval/context coverage and verifier recall, not "
            "weakening hallucination controls or adding the supplemental graph.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    summary = build_summary()
    OUTPUT_JSON.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    OUTPUT_MARKDOWN.write_text(render_markdown(summary), encoding="utf-8")
    print(f"status: {summary['status']}")
    print(f"queries: {summary['final_generation']['query_count']}")
    print(f"json: {OUTPUT_JSON.relative_to(ROOT)}")
    print(f"markdown: {OUTPUT_MARKDOWN.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
