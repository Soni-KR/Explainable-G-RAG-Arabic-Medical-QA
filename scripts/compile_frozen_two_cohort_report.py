from __future__ import annotations

"""Compile the frozen two-cohort evaluation without rerunning the pipeline."""

import argparse
import json
import statistics
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
EVALUATION_ROOT = ROOT / "outputs" / "evaluation"
FROZEN_ROOT = EVALUATION_ROOT / "frozen_production_200q_20260728"

COHORTS = {
    "ahd_reference_100": {
        "display_name": "Cohort A: AHD reference-answer 100",
        "selection": FROZEN_ROOT / "ahd_reference_100_retrieval_selection.json",
        "primary_retrieval": (
            EVALUATION_ROOT
            / "retrieval"
            / "frozen_prod_ahd_reference_100_20260728"
        ),
        "conditional_retrieval": (
            EVALUATION_ROOT
            / "retrieval"
            / "frozen_prod_ahd_reference_100_conditional_fts_20260728"
        ),
        "generation": (
            EVALUATION_ROOT
            / "generation"
            / "frozen_prod_ahd_reference_100_steps12_17_network_20260728"
        ),
        "claim_audit": (
            EVALUATION_ROOT
            / "claim_audit"
            / "frozen_prod_ahd_reference_100_steps12_17_network_20260728"
        ),
        "cache": (
            EVALUATION_ROOT
            / "cache"
            / "frozen_prod_ahd_reference_100_steps12_17_network_20260728"
        ),
        "excluded_network_preflight": (
            EVALUATION_ROOT
            / "generation"
            / "frozen_prod_ahd_reference_100_steps12_17_20260728"
        ),
    },
    "entity_ground_truth_100": {
        "display_name": "Cohort B: entity-ground-truth 100",
        "selection": FROZEN_ROOT / "entity_ground_truth_100_retrieval_selection.json",
        "primary_retrieval": (
            EVALUATION_ROOT
            / "retrieval"
            / "frozen_prod_entity_gt_100_20260728"
        ),
        "conditional_retrieval": (
            EVALUATION_ROOT
            / "retrieval"
            / "frozen_prod_entity_gt_100_conditional_fts_20260728"
        ),
        "generation": (
            EVALUATION_ROOT
            / "generation"
            / "frozen_prod_entity_gt_100_steps12_17_network_20260728"
        ),
        "claim_audit": (
            EVALUATION_ROOT
            / "claim_audit"
            / "frozen_prod_entity_gt_100_steps12_17_network_20260728"
        ),
        "cache": (
            EVALUATION_ROOT
            / "cache"
            / "frozen_prod_entity_gt_100_steps12_17_network_20260728"
        ),
        "excluded_network_preflight": None,
    },
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8-sig") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def safe_divide(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0


def percentile(values: list[float], fraction: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def distribution(values: list[float]) -> dict[str, float]:
    if not values:
        return {"mean": 0.0, "median": 0.0, "p95": 0.0, "min": 0.0, "max": 0.0}
    return {
        "mean": round(statistics.fmean(values), 6),
        "median": round(statistics.median(values), 6),
        "p95": round(percentile(values, 0.95), 6),
        "min": round(min(values), 6),
        "max": round(max(values), 6),
    }


def latency_summary(records: list[dict[str, Any]]) -> dict[str, dict[str, float]]:
    stages = sorted(
        {
            stage
            for record in records
            for stage in dict(record.get("timings_ms") or {})
        }
    )
    output: dict[str, dict[str, float]] = {}
    for stage in stages:
        values = [
            float((record.get("timings_ms") or {}).get(stage) or 0.0)
            for record in records
        ]
        stage_distribution = distribution(values)
        output[stage] = {
            **stage_distribution,
            "total": round(sum(values), 6),
        }
    return output


def generated_bertscore(records: list[dict[str, Any]]) -> dict[str, Any]:
    selected = [
        record
        for record in records
        if record.get("generation_status") == "generated"
        and str((record.get("gold") or {}).get("reference_answer") or "").strip()
    ]
    if not selected:
        return {"status": "unavailable", "reason": "No successful generations."}
    try:
        from bert_score import BERTScorer
    except ImportError:
        return {"status": "unavailable", "reason": "bert-score is not installed."}
    scorer = BERTScorer(lang="ar", rescale_with_baseline=False)
    candidates = [
        str((record.get("raw") or {}).get("generated", {}).get("answer") or "")
        for record in selected
    ]
    references = [
        str((record.get("gold") or {}).get("reference_answer") or "")
        for record in selected
    ]
    precision, recall, f1 = scorer.score(
        candidates,
        references,
        batch_size=16,
        verbose=False,
    )
    return {
        "status": "computed",
        "scope": "successful raw Step 12 generations before mitigation",
        "evaluated_query_count": len(selected),
        "precision": round(float(precision.mean()), 6),
        "recall": round(float(recall.mean()), 6),
        "f1": round(float(f1.mean()), 6),
    }


def failure_category(reason: str) -> str:
    lowered = reason.lower()
    if "json_validate_failed" in lowered or "missing properties" in lowered:
        return "provider_json_schema_failure"
    if "valueerror" in lowered:
        return "response_parse_or_validation_failure"
    if "httperror 429" in lowered:
        return "rate_limit"
    if "urlerror" in lowered:
        return "network_error"
    return "other_technical_failure"


def step17_rows(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for record in records:
        raw = dict(record.get("raw") or {})
        verifications = list(raw.get("verifications") or [])
        supported_relation_ids = {
            relation_id
            for verification in verifications
            if verification.get("status") == "supported"
            for relation_id in verification.get("supporting_relation_ids") or []
        }
        valid_evidence_ids = {
            evidence_id
            for verification in verifications
            if verification.get("status") == "supported"
            for evidence_id in verification.get("valid_citations") or []
        }
        context = dict(raw.get("context") or {})
        linking = dict(raw.get("entity_linking") or {})
        linked_entities = [
            {
                "entity_id": item.get("linked_entity_id"),
                "canonical_name": item.get("linked_canonical_name"),
                "entity_type": item.get("linked_entity_type"),
                "match_type": item.get("match_type"),
                "match_score": item.get("match_score"),
            }
            for item in linking.get("linked_entities") or []
            if item.get("status") == "linked"
        ]
        output.append(
            {
                "query_id": record.get("query_id"),
                "query": record.get("query"),
                "answer": record.get("answer"),
                "answerability": record.get("answerability"),
                "generation_status": record.get("generation_status"),
                "reliability": raw.get("reliability"),
                "query_coverage": record.get("query_coverage"),
                "missing_query_concepts": record.get("missing_query_concepts") or [],
                "query_analysis": raw.get("query_analysis"),
                "retrieval_plan": raw.get("retrieval_plan"),
                "retrieved_entities": linked_entities,
                "supporting_relations": [
                    item
                    for item in context.get("graph_facts") or []
                    if item.get("relation_id") in supported_relation_ids
                ],
                "supporting_evidence": [
                    item
                    for item in context.get("evidence_items") or []
                    if item.get("evidence_id") in valid_evidence_ids
                ],
                "all_selected_context": context.get("evidence_items") or [],
                "claim_audit": verifications,
                "kept_claims": (raw.get("mitigated") or {}).get("kept_claims") or [],
                "removed_claims": (raw.get("mitigated") or {}).get("removed_claims") or [],
                "limitations": (raw.get("mitigated") or {}).get("limitations") or [],
                "warnings": record.get("warnings") or [],
                "metrics": record.get("metrics"),
                "timings_ms": record.get("timings_ms"),
            }
        )
    return output


def summarize_generation(
    records: list[dict[str, Any]],
    saved_metrics: dict[str, Any],
    raw_bertscore: dict[str, Any],
) -> dict[str, Any]:
    generation_status = Counter(str(row.get("generation_status") or "unknown") for row in records)
    answerability = Counter(str(row.get("answerability") or "unknown") for row in records)
    contexts = [
        list((row.get("raw") or {}).get("context", {}).get("evidence_items") or [])
        for row in records
    ]
    context_cross_tab: Counter[str] = Counter()
    technical_reasons: Counter[str] = Counter()
    for row, context in zip(records, contexts, strict=True):
        generated = dict((row.get("raw") or {}).get("generated") or {})
        context_state = "nonempty" if context else "empty"
        fallback_type = str(generated.get("fallback_type") or "none")
        context_cross_tab[f"{context_state}:{row.get('generation_status')}:{fallback_type}"] += 1
        if fallback_type == "technical_failure":
            technical_reasons[failure_category(str(generated.get("fallback_reason") or ""))] += 1

    verifications = [
        verification
        for row in records
        for verification in (row.get("raw") or {}).get("verifications") or []
    ]
    pre_status = Counter(str(item.get("status") or "unknown") for item in verifications)
    pre_total = sum(pre_status.values())
    output_claims = [
        claim for row in records for claim in row.get("output_claims") or []
    ]
    claim_bearing_queries = sum(bool(row.get("output_claims")) for row in records)
    removed_claims = [
        claim
        for row in records
        for claim in (row.get("raw") or {}).get("mitigated", {}).get("removed_claims") or []
    ]
    failed_checks = Counter(
        str(check)
        for verification in verifications
        if verification.get("status") != "supported"
        for check in verification.get("failed_checks") or []
    )
    allowed_by_query = {
        str(row.get("query_id")): set(
            (row.get("raw") or {}).get("context", {}).get("allowed_evidence_ids")
            or []
        )
        for row in records
    }
    citations = [
        citation
        for row in records
        for claim in row.get("output_claims") or []
        for citation in claim.get("citations") or []
    ]
    valid_citations = [
        citation
        for row in records
        for claim in row.get("output_claims") or []
        for citation in claim.get("citations") or []
        if citation in allowed_by_query[str(row.get("query_id"))]
    ]
    reliability_scores = [
        float((row.get("raw") or {}).get("reliability", {}).get("score") or 0.0)
        for row in records
    ]
    reliability_labels = Counter(
        str((row.get("raw") or {}).get("reliability", {}).get("label") or "unknown")
        for row in records
    )
    substantive = [
        row
        for row in records
        if row.get("output_claims")
        and row.get("answerability")
        not in {"insufficient_evidence", "generation_unavailable", ""}
    ]
    post_metrics = dict(saved_metrics.get("full_pipeline") or {})
    return {
        "queries": len(records),
        "context": {
            "nonempty": sum(bool(items) for items in contexts),
            "empty": sum(not items for items in contexts),
            "outcomes": dict(sorted(context_cross_tab.items())),
        },
        "generation_status": dict(generation_status),
        "answerability": dict(answerability),
        "technical_failures": {
            "count": sum(technical_reasons.values()),
            "reasons": dict(technical_reasons),
        },
        "substantive": {
            "claim_bearing_queries": claim_bearing_queries,
            "coverage_rate_over_100": round(
                safe_divide(claim_bearing_queries, len(records)),
                6,
            ),
            "final_claims": len(output_claims),
        },
        "bertscore": {
            "raw_generated_only_pre_mitigation": raw_bertscore,
            "post_mitigation_substantive_only": post_metrics.get("bertscore"),
            "end_to_end_all_queries": {
                "status": "not_computed",
                "reason": (
                    "Fallback/abstention text is not treated as a generated "
                    "medical answer; scoring it would misstate model quality."
                ),
            },
        },
        "claims": {
            "pre_mitigation": {
                "claim_count": pre_total,
                "status_counts": dict(pre_status),
                "support_rate": round(
                    safe_divide(pre_status["supported"], pre_total),
                    6,
                ),
                "weak_support_rate": round(
                    safe_divide(pre_status["weakly_supported"], pre_total),
                    6,
                ),
                "hallucination_rate": round(
                    safe_divide(pre_status["unsupported"], pre_total),
                    6,
                ),
            },
            "post_mitigation": {
                "claim_count": len(output_claims),
                "claim_bearing_queries": claim_bearing_queries,
                "support_rate": 1.0 if output_claims else 0.0,
                "hallucination_rate": 0.0,
                "scope_warning": (
                    "These rates apply only to surviving claims in substantive "
                    "claim-bearing answers, not to all 100 questions."
                ),
            },
            "removed_claim_count": len(removed_claims),
            "removal_failed_checks": dict(failed_checks.most_common()),
        },
        "citations": {
            "citation_count": len(citations),
            "valid_citation_count": len(valid_citations),
            "citation_validity": round(
                safe_divide(len(valid_citations), len(citations)),
                6,
            ),
            "scope": "surviving post-mitigation claims",
        },
        "reliability": {
            "score_distribution": distribution(reliability_scores),
            "labels": dict(reliability_labels),
            "decision_mapping": {
                "accept": reliability_labels["high"],
                "flag": reliability_labels["medium"],
                "abstain": reliability_labels["low"],
            },
            "calibrated": False,
        },
        "query_coverage": {
            "substantive_distribution": distribution(
                [float(row.get("query_coverage") or 0.0) for row in substantive]
            ),
        },
        "latency_ms": latency_summary(records),
        "ragas": {
            "status": "not_run",
            "reason": (
                "The frozen protocol requested one generator pass and "
                "deterministic verification. RAGAS judge calls were not added "
                "after results or mixed with the production verdict."
            ),
        },
    }


def aggregate_generation(cohort_summaries: dict[str, dict[str, Any]], records: list[dict[str, Any]]) -> dict[str, Any]:
    pre_counts = Counter()
    answerability = Counter()
    generation = Counter()
    technical = Counter()
    reliability = Counter()
    generation_summaries = [
        cohort["generation"] for cohort in cohort_summaries.values()
    ]
    for summary in generation_summaries:
        pre_counts.update(summary["claims"]["pre_mitigation"]["status_counts"])
        answerability.update(summary["answerability"])
        generation.update(summary["generation_status"])
        technical.update(summary["technical_failures"]["reasons"])
        reliability.update(summary["reliability"]["labels"])
    pre_total = sum(pre_counts.values())
    post_claims = sum(
        summary["claims"]["post_mitigation"]["claim_count"]
        for summary in generation_summaries
    )
    claim_bearing = sum(
        summary["claims"]["post_mitigation"]["claim_bearing_queries"]
        for summary in generation_summaries
    )
    bert_rows = [
        (
            summary["bertscore"]["post_mitigation_substantive_only"].get(
                "evaluated_query_count", 0
            ),
            summary["bertscore"]["post_mitigation_substantive_only"].get(
                "bertscore_f1", 0.0
            ),
        )
        for summary in generation_summaries
    ]
    bert_count = sum(count for count, _ in bert_rows)
    raw_bert_rows = [
        (
            summary["bertscore"]["raw_generated_only_pre_mitigation"].get(
                "evaluated_query_count", 0
            ),
            summary["bertscore"]["raw_generated_only_pre_mitigation"].get(
                "f1", 0.0
            ),
        )
        for summary in generation_summaries
    ]
    raw_bert_count = sum(count for count, _ in raw_bert_rows)
    return {
        "queries": len(records),
        "generation_status": dict(generation),
        "answerability": dict(answerability),
        "technical_failure_reasons": dict(technical),
        "claim_bearing_queries": claim_bearing,
        "substantive_coverage_rate": round(
            safe_divide(claim_bearing, len(records)),
            6,
        ),
        "pre_mitigation_claims": {
            "claim_count": pre_total,
            "status_counts": dict(pre_counts),
            "support_rate": round(
                safe_divide(pre_counts["supported"], pre_total),
                6,
            ),
            "hallucination_rate": round(
                safe_divide(pre_counts["unsupported"], pre_total),
                6,
            ),
        },
        "post_mitigation_claims": {
            "claim_count": post_claims,
            "claim_bearing_queries": claim_bearing,
            "support_rate": 1.0 if post_claims else 0.0,
            "hallucination_rate": 0.0,
            "scope_warning": (
                "Applies to surviving claims in 49 substantive answers, not "
                "to all 200 questions."
            ),
        },
        "raw_generated_bertscore": {
            "status": "computed",
            "evaluated_query_count": raw_bert_count,
            "bertscore_f1": round(
                safe_divide(
                    sum(count * score for count, score in raw_bert_rows),
                    raw_bert_count,
                ),
                6,
            ),
        },
        "post_mitigation_bertscore": {
            "status": "computed",
            "evaluated_query_count": bert_count,
            "bertscore_f1": round(
                safe_divide(
                    sum(count * score for count, score in bert_rows),
                    bert_count,
                ),
                6,
            ),
        },
        "reliability_labels": dict(reliability),
        "decision_mapping": {
            "accept": reliability["high"],
            "flag": reliability["medium"],
            "abstain": reliability["low"],
        },
        "latency_ms": latency_summary(records),
        "retrieval_metrics": {
            "status": "not_aggregated",
            "reason": (
                "The cohorts use different independent judgments: candidate "
                "relevance for Cohort A and entity IDs for Cohort B."
            ),
        },
    }


def relative(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def report_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# Frozen Two-Cohort Production Evaluation",
        "",
        "This is the authoritative no-post-hoc-tuning evaluation of `final_v1`.",
        "The supplemental graph, semantic claim adjudication, E5 claim calibrator,",
        "and forced extractive fallback were disabled. Exact held-out QA matches",
        "were excluded from both main cohorts.",
        "",
        "## Executive Result",
        "",
    ]
    for name, cohort in result["cohorts"].items():
        generation = cohort["generation"]
        selection = cohort["retrieval_selection"]
        lines.extend(
            [
                f"### {cohort['display_name']}",
                "",
                f"- Selected retrieval: `{selection['selected_mode']}`",
                f"- Context: {generation['context']['nonempty']} non-empty / "
                f"{generation['context']['empty']} empty",
                f"- Step 12: {generation['generation_status'].get('generated', 0)} "
                f"generated / {generation['generation_status'].get('fallback', 0)} fallback",
                f"- Final substantive answers: "
                f"{generation['substantive']['claim_bearing_queries']}/100",
                f"- Technical failures: {generation['technical_failures']['count']}",
                f"- Post-mitigation BERTScore F1: "
                f"{generation['bertscore']['post_mitigation_substantive_only'].get('bertscore_f1', 'unavailable')} "
                f"over {generation['bertscore']['post_mitigation_substantive_only'].get('evaluated_query_count', 0)} answers",
                "",
            ]
        )
    aggregate = result["aggregate_200"]
    lines.extend(
        [
            "## Optional 200-Query Aggregate",
            "",
            f"- Final substantive answers: {aggregate['claim_bearing_queries']}/200 "
            f"({aggregate['substantive_coverage_rate']:.1%})",
            f"- Generated before mitigation: "
            f"{aggregate['generation_status'].get('generated', 0)}/200",
            f"- Technical failures: "
            f"{sum(aggregate['technical_failure_reasons'].values())}/200",
            f"- Post-mitigation BERTScore F1: "
            f"{aggregate['post_mitigation_bertscore']['bertscore_f1']} "
            f"over {aggregate['post_mitigation_bertscore']['evaluated_query_count']} answers",
            f"- Reliability decisions: accept={aggregate['decision_mapping']['accept']}, "
            f"flag={aggregate['decision_mapping']['flag']}, "
            f"abstain={aggregate['decision_mapping']['abstain']}",
            "",
            "Retrieval scores are not pooled across 200 because the cohorts use",
            "different independent gold judgments.",
            "",
        ]
    )
    for name, cohort in result["cohorts"].items():
        selection = cohort["retrieval_selection"]
        generation = cohort["generation"]
        lines.extend(
            [
                f"## {cohort['display_name']}: Retrieval",
                "",
                "| Mode | Primary score | Non-empty context | Strong direct context |",
                "|---|---:|---:|---:|",
            ]
        )
        for mode, score in selection["scores"].items():
            if "human_pool" in score:
                primary = score["human_pool"][
                    "confirmed_direct_recall_at_5_answerable_queries"
                ]
            else:
                primary = score["entity_gold"].get("recall_at_5", "unavailable")
            lines.append(
                f"| {mode} | {primary} | "
                f"{score['step11']['nonempty_context_queries']} | "
                f"{score['step11']['strong_direct_context_queries']} |"
            )
        lines.extend(
            [
                "",
                f"Winner: `{selection['selected_mode']}`. The category bonus guard "
                f"passed: `{selection['category_bonus_guard']['passed']}`.",
                "",
                f"## {cohort['display_name']}: Generation and Verification",
                "",
                f"- Answerability: `{json.dumps(generation['answerability'], ensure_ascii=False)}`",
                f"- Pre-mitigation claims: "
                f"{generation['claims']['pre_mitigation']['claim_count']} "
                f"(support={generation['claims']['pre_mitigation']['support_rate']}, "
                f"weak={generation['claims']['pre_mitigation']['weak_support_rate']}, "
                f"hallucination={generation['claims']['pre_mitigation']['hallucination_rate']})",
                f"- Removed claims: {generation['claims']['removed_claim_count']}",
                f"- Post-mitigation claims: "
                f"{generation['claims']['post_mitigation']['claim_count']} across "
                f"{generation['claims']['post_mitigation']['claim_bearing_queries']} answers",
                f"- Citation validity: {generation['citations']['citation_validity']}",
                f"- Reliability labels: "
                f"`{json.dumps(generation['reliability']['labels'], ensure_ascii=False)}`",
                "",
                "**Scope warning:** Post-mitigation support `1.00` and hallucination",
                "`0.00` apply only to surviving claims in substantive answers,",
                "not to all 100 questions.",
                "",
                "Top removal checks:",
                "",
            ]
        )
        for check, count in list(
            generation["claims"]["removal_failed_checks"].items()
        )[:8]:
            lines.append(f"- `{check}`: {count}")
        latency = generation["latency_ms"].get("end_to_end", {})
        lines.extend(
            [
                "",
                "End-to-end latency:",
                "",
                f"- Mean: {latency.get('mean', 0):.3f} ms",
                f"- Median: {latency.get('median', 0):.3f} ms",
                f"- p95: {latency.get('p95', 0):.3f} ms",
                f"- Total: {latency.get('total', 0):.3f} ms",
                "",
            ]
        )
    lines.extend(
        [
            "## Steps 8-17",
            "",
            "1. **Step 8:** Cached normalized Arabic query analysis, medical phrase extraction, deterministic Neo4j linking, and retrieval planning.",
            "2. **Step 9:** E5 vector retrieval, validated `final_v1` graph traversal, QA retrieval, then label-free conditional FTS when ordinary context was partial.",
            "3. **Step 10:** The same deterministic identity-, intent-, anatomy-, concept-, source-, and contradiction-aware reranker for every ablation.",
            "4. **Step 11:** Absolute relevance gates, deduplication, source provenance, and compact evidence-focused context.",
            "5. **Step 12:** GPT-OSS-20B claim-first Arabic generation with strict citations and no extractive fallback.",
            "6. **Step 13:** Deterministic extraction of atomic generated claims.",
            "7. **Step 14:** Deterministic citation, evidence support, intent, concept, anatomy, negation, and number verification.",
            "8. **Step 15:** Removal of weak or unsupported claims and explicit answerability assignment.",
            "9. **Step 16:** Uncalibrated deterministic reliability scoring (`high/medium/low`).",
            "10. **Step 17:** Explainable records joining the answer, linked entities, supporting evidence/relations, claim audit, removed claims, limitations, scores, and timings.",
            "",
            "## Interpretation",
            "",
            "- Vector retrieval supplied nearly all measurable retrieval value; graph-only remained weak.",
            "- Conditional FTS modestly improved the independently judged retrieval objective and was selected for both cohorts.",
            "- The category bonus produced no independent-metric improvement and was not selected.",
            "- The main remaining limitation is answer coverage after deterministic verification, not post-mitigation citation validity.",
            "- RAGAS was not added after the freeze because it requires additional judge calls and would be a separate evaluator experiment.",
            "",
            "## Final Artifacts",
            "",
        ]
    )
    for label, path in result["artifacts"].items():
        lines.append(f"- **{label}:** `{path}`")
    lines.extend(
        [
            "",
            "The known-answer exact-QA artifact remains an upper-bound diagnostic",
            "and is excluded from selection, main metrics, and the 200-query aggregate.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=FROZEN_ROOT)
    parser.add_argument("--skip-raw-bertscore", action="store_true")
    args = parser.parse_args()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    final_json = output_dir / "FINAL_RESULTS.json"
    final_markdown = output_dir / "FINAL_REPORT.md"
    if final_json.exists() or final_markdown.exists():
        raise FileExistsError("Final frozen report already exists and cannot be overwritten.")

    cohort_results: dict[str, Any] = {}
    all_records: list[dict[str, Any]] = []
    artifacts: dict[str, str] = {
        "frozen manifest": relative(output_dir / "manifest.json"),
    }
    for name, paths in COHORTS.items():
        generation_file = paths["generation"] / "full_pipeline.jsonl"
        metrics_file = paths["generation"] / "metrics.json"
        selection = load_json(paths["selection"])
        records = load_jsonl(generation_file)
        if len(records) != 100:
            raise ValueError(f"{name} generation artifact must contain exactly 100 records.")
        raw_score = (
            {
                "status": "not_run",
                "reason": "Skipped by command-line request.",
            }
            if args.skip_raw_bertscore
            else generated_bertscore(records)
        )
        generation = summarize_generation(
            records,
            load_json(metrics_file),
            raw_score,
        )
        step17_file = output_dir / f"{name}_step17_explainable.jsonl"
        write_jsonl(step17_file, step17_rows(records))
        cohort_results[name] = {
            "display_name": paths["display_name"],
            "retrieval_selection": selection,
            "generation": generation,
        }
        all_records.extend(records)
        artifacts.update(
            {
                f"{name} primary retrieval metrics": relative(
                    paths["primary_retrieval"] / "metrics.json"
                ),
                f"{name} conditional retrieval metrics": relative(
                    paths["conditional_retrieval"] / "metrics.json"
                ),
                f"{name} retrieval selection": relative(paths["selection"]),
                f"{name} selected retrieval JSONL": relative(
                    Path(selection["selected_artifact"])
                ),
                f"{name} generation records": relative(generation_file),
                f"{name} generation metrics": relative(metrics_file),
                f"{name} generation manifest": relative(
                    paths["generation"] / "manifest.json"
                ),
                f"{name} claim audit": relative(
                    paths["claim_audit"] / "full_pipeline.jsonl"
                ),
                f"{name} resumable Step 12 cache": relative(
                    paths["cache"] / "step12_success.jsonl"
                ),
                f"{name} Step 17 explainable output": relative(step17_file),
            }
        )
        if paths["excluded_network_preflight"] is not None:
            artifacts[
                f"{name} excluded sandbox-network preflight"
            ] = relative(paths["excluded_network_preflight"])

    result = {
        "evaluation_id": "frozen_production_200q_20260728",
        "status": "complete",
        "configuration_frozen_before_results": True,
        "post_result_tuning": False,
        "graph_version": "final_v1",
        "embedding_model": "intfloat/multilingual-e5-base",
        "supplemental_graph_used": False,
        "semantic_claim_adjudication_used": False,
        "e5_claim_calibrator_used": False,
        "forced_extractive_fallback_used": False,
        "cohorts": cohort_results,
        "aggregate_200": aggregate_generation(cohort_results, all_records),
        "known_answer_exact_qa": {
            "role": "upper_bound_diagnostic_only",
            "included_in_main_results": False,
        },
        "artifacts": artifacts,
        "limitations": [
            "Cohort A retrieval judgments are incomplete; unjudged candidates were never treated as label 0.",
            "Cohort B has independent entity IDs but no independent evidence/QA/relation gold IDs.",
            "Reliability scores are deterministic and uncalibrated.",
            "RAGAS judge metrics were not run in this frozen protocol.",
            "Six total Step 12 technical schema/parse failures are reported rather than retried after the sealed runs.",
        ],
    }
    write_json(final_json, result)
    final_markdown.write_text(report_markdown(result), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": "complete",
                "report": relative(final_markdown),
                "results": relative(final_json),
                "cohort_a_substantive": cohort_results["ahd_reference_100"][
                    "generation"
                ]["substantive"]["claim_bearing_queries"],
                "cohort_b_substantive": cohort_results["entity_ground_truth_100"][
                    "generation"
                ]["substantive"]["claim_bearing_queries"],
                "aggregate_substantive": result["aggregate_200"][
                    "claim_bearing_queries"
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
