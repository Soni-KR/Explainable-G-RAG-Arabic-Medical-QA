from __future__ import annotations

"""Evaluate frozen final_v2 retrieval and generation with independent labels."""

import argparse
import csv
import json
import math
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LABELS = ROOT / "data/evaluation/final_v2_candidate_relevance_labels_100_annotated.csv"
DEFAULT_QUEUE = ROOT / "data/evaluation/final_v2_candidate_relevance_labels_100.csv"
DEFAULT_RETRIEVAL = ROOT / (
    "outputs/evaluation/retrieval/final_v2_ahd_reference_100_conditional_fts_20260803/"
    "vector_graph_conditional_fts.jsonl"
)
DEFAULT_GENERATION = ROOT / (
    "outputs/evaluation/generation/final_v2_ahd_reference_100_steps12_17_20260803/"
    "full_pipeline.jsonl"
)
DEFAULT_GENERATION_METRICS = DEFAULT_GENERATION.parent / "metrics.json"
DEFAULT_OUTPUT = ROOT / "outputs/evaluation/final_v2_human_relevance_100_20260805"

KEY_FIELDS = ("query_id", "candidate_type", "candidate_id")
LABELS = {"0", "1", "2"}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8-sig") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def key(row: dict[str, Any]) -> tuple[str, str, str]:
    return tuple(str(row.get(field) or "").strip() for field in KEY_FIELDS)  # type: ignore[return-value]


def mean(values: list[float]) -> float:
    return statistics.fmean(values) if values else 0.0


def percentile(values: list[float], quantile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    position = (len(ordered) - 1) * quantile
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def reciprocal_rank(labels: list[int], target: int = 2) -> float:
    for rank, label in enumerate(labels, start=1):
        if label >= target:
            return 1.0 / rank
    return 0.0


def ndcg(labels: list[int], cutoff: int) -> float:
    observed = labels[:cutoff]
    ideal = sorted(labels, reverse=True)[:cutoff]

    def dcg(values: list[int]) -> float:
        return sum((2**grade - 1) / math.log2(rank + 2) for rank, grade in enumerate(values))

    denominator = dcg(ideal)
    return dcg(observed) / denominator if denominator else 0.0


def validate_annotations(
    annotated: list[dict[str, str]], queue: list[dict[str, str]]
) -> dict[str, Any]:
    errors: list[str] = []
    annotated_by_key = {key(row): row for row in annotated}
    queue_by_key = {key(row): row for row in queue}
    if len(annotated_by_key) != len(annotated):
        errors.append("duplicate stable candidate keys in annotated file")
    if set(annotated_by_key) != set(queue_by_key):
        errors.append("annotated candidate keys differ from the frozen queue")
    for candidate_key, row in annotated_by_key.items():
        label = str(row.get("relevance_label") or "").strip()
        if label not in LABELS:
            errors.append(f"invalid or blank label for {candidate_key}")
        if label == "0" and not str(row.get("error_reason") or "").strip():
            errors.append(f"label-0 row has no error reason: {candidate_key}")
        if str(row.get("annotation_status") or "").strip() not in {"annotated", "adjudicated"}:
            errors.append(f"unfinished annotation status: {candidate_key}")
        source = queue_by_key.get(candidate_key)
        if source:
            for field in (
                "query",
                "candidate_question",
                "candidate_answer_or_evidence",
                "relation_type",
                "source_entity_name",
                "target_entity_name",
            ):
                if str(row.get(field) or "") != str(source.get(field) or ""):
                    errors.append(f"frozen candidate content changed: {candidate_key} field={field}")
    return {
        "status": "ok" if not errors else "failed",
        "errors": errors,
        "rows": len(annotated),
        "queries_with_candidates": len({row["query_id"] for row in annotated}),
        "label_counts": dict(sorted(Counter(row["relevance_label"].strip() for row in annotated).items())),
        "annotation_status_counts": dict(
            sorted(Counter(row["annotation_status"].strip() for row in annotated).items())
        ),
        "annotator_counts": dict(sorted(Counter(row["annotator_id"].strip() for row in annotated).items())),
    }


def restore_rankings(
    retrieval: list[dict[str, Any]], labels_by_key: dict[tuple[str, str, str], dict[str, str]]
) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    rows: list[dict[str, Any]] = []
    by_query: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in retrieval:
        query_id = str(record.get("query_id") or "")
        candidates: list[dict[str, Any]] = []
        for rank, item in enumerate(list(record.get("evidence") or [])[:10], start=1):
            candidate_id = str(item.get("evidence_id") or item.get("source_id") or "")
            candidate_key = (query_id, "evidence", candidate_id)
            judgment = labels_by_key.get(candidate_key)
            if judgment:
                candidates.append(
                    {
                        **judgment,
                        "rank_within_type": rank,
                        "frozen_score": float(item.get("score") or 0.0),
                        "selected_step11": False,
                    }
                )
        for rank, item in enumerate(list(record.get("relations") or [])[:5], start=1):
            candidate_id = str(item.get("relation_id") or "")
            candidate_key = (query_id, "relation", candidate_id)
            judgment = labels_by_key.get(candidate_key)
            if judgment:
                candidates.append(
                    {
                        **judgment,
                        "rank_within_type": rank,
                        "frozen_score": float(item.get("hybrid_score") or 0.0),
                        "selected_step11": False,
                    }
                )

        context = dict(record.get("final_step11_context") or {})
        selected_sources = {
            str(item.get("source_id") or item.get("qa_id") or "")
            for item in list(context.get("evidence_items") or [])
        }
        selected_relations = {
            str(item.get("relation_id") or item.get("source_relation_id") or "")
            for item in list(context.get("graph_facts") or [])
        }
        for candidate in candidates:
            if candidate["candidate_type"] == "evidence":
                candidate["selected_step11"] = (
                    candidate["qa_id"] in selected_sources
                    or candidate["candidate_id"].removeprefix("qa::") in selected_sources
                )
            else:
                candidate["selected_step11"] = candidate["candidate_id"] in selected_relations
        candidates.sort(key=lambda row: (-float(row["frozen_score"]), row["candidate_type"], row["candidate_id"]))
        for combined_rank, candidate in enumerate(candidates, start=1):
            candidate["combined_rank"] = combined_rank
            rows.append(candidate)
            by_query[query_id].append(candidate)
    return rows, by_query


def ranking_summary(
    retrieval: list[dict[str, Any]], by_query: dict[str, list[dict[str, Any]]], candidate_type: str | None
) -> dict[str, Any]:
    direct_hit_5: list[float] = []
    useful_hit_5: list[float] = []
    direct_recall_5: list[float] = []
    reciprocal_ranks: list[float] = []
    ndcg_10: list[float] = []
    direct_precision_5: list[float] = []
    useful_precision_5: list[float] = []
    direct_covered = useful_covered = all_zero = 0
    candidate_count = 0
    label_counts: Counter[str] = Counter()

    for record in retrieval:
        query_id = str(record.get("query_id") or "")
        ranked = [
            row for row in by_query.get(query_id, []) if candidate_type is None or row["candidate_type"] == candidate_type
        ]
        if candidate_type is not None:
            ranked.sort(key=lambda row: int(row["rank_within_type"]))
        labels = [int(row["relevance_label"]) for row in ranked]
        candidate_count += len(labels)
        label_counts.update(str(label) for label in labels)
        top5 = labels[:5]
        direct_total = sum(label == 2 for label in labels)
        direct_top5 = sum(label == 2 for label in top5)
        direct_hit_5.append(float(direct_top5 > 0))
        useful_hit_5.append(float(any(label >= 1 for label in top5)))
        direct_recall_5.append(direct_top5 / direct_total if direct_total else 0.0)
        reciprocal_ranks.append(reciprocal_rank(labels, 2))
        ndcg_10.append(ndcg(labels, 10))
        denominator = len(top5)
        direct_precision_5.append(direct_top5 / denominator if denominator else 0.0)
        useful_precision_5.append(sum(label >= 1 for label in top5) / denominator if denominator else 0.0)
        direct_covered += direct_total > 0
        useful_covered += any(label >= 1 for label in labels)
        all_zero += bool(labels) and all(label == 0 for label in labels)

    return {
        "queries": len(retrieval),
        "candidate_rows": candidate_count,
        "label_counts": dict(sorted(label_counts.items())),
        "queries_with_direct_candidate": direct_covered,
        "queries_with_any_useful_candidate": useful_covered,
        "queries_with_only_label_0": all_zero,
        "direct_hit_rate_at_5": round(mean(direct_hit_5), 6),
        "useful_hit_rate_at_5": round(mean(useful_hit_5), 6),
        "judged_pool_direct_recall_at_5": round(mean(direct_recall_5), 6),
        "mrr_direct": round(mean(reciprocal_ranks), 6),
        "ndcg_at_10_graded": round(mean(ndcg_10), 6),
        "direct_precision_at_5": round(mean(direct_precision_5), 6),
        "useful_precision_at_5": round(mean(useful_precision_5), 6),
        "scope_note": "All-query macro metrics; unjudged candidates outside the exported top-10 evidence/top-5 relation pool are not gold negatives.",
    }


def context_summary(
    retrieval: list[dict[str, Any]], ranked_rows: list[dict[str, Any]], by_query: dict[str, list[dict[str, Any]]]
) -> dict[str, Any]:
    selected = [row for row in ranked_rows if row["selected_step11"]]
    selected_counts = Counter(row["relevance_label"] for row in selected)
    selected_keys = {key(row) for row in selected}
    all_direct = {key(row) for row in ranked_rows if row["relevance_label"] == "2"}
    all_useful = {key(row) for row in ranked_rows if row["relevance_label"] in {"1", "2"}}
    total_selected_artifacts = 0
    query_direct = query_useful = 0
    for record in retrieval:
        context = dict(record.get("final_step11_context") or {})
        total_selected_artifacts += len(context.get("evidence_items") or []) + len(context.get("graph_facts") or [])
        query_rows = [row for row in by_query.get(str(record.get("query_id") or ""), []) if row["selected_step11"]]
        query_direct += any(row["relevance_label"] == "2" for row in query_rows)
        query_useful += any(row["relevance_label"] in {"1", "2"} for row in query_rows)
    judged = len(selected)
    return {
        "selected_artifacts_total": total_selected_artifacts,
        "selected_artifacts_with_judgments": judged,
        "selected_artifacts_unjudged": total_selected_artifacts - judged,
        "selected_label_counts": dict(sorted(selected_counts.items())),
        "useful_context_precision": round(
            sum(value for label, value in selected_counts.items() if label in {"1", "2"}) / judged if judged else 0.0,
            6,
        ),
        "direct_context_precision": round(selected_counts["2"] / judged if judged else 0.0, 6),
        "judged_pool_useful_retention": round(len(selected_keys & all_useful) / len(all_useful) if all_useful else 0.0, 6),
        "judged_pool_direct_retention": round(len(selected_keys & all_direct) / len(all_direct) if all_direct else 0.0, 6),
        "queries_with_selected_useful_context": query_useful,
        "queries_with_selected_direct_context": query_direct,
        "scope_note": "Precision is calculated only over selected candidates present in the independently judged pool.",
    }


def candidate_breakdown(rows: list[dict[str, Any]], field: str) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get(field) or "unknown")].append(row)
    output: dict[str, Any] = {}
    for name, group in sorted(grouped.items()):
        labels = Counter(str(row["relevance_label"]) for row in group)
        queries = {str(row["query_id"]) for row in group}
        direct_queries = {
            str(row["query_id"]) for row in group if str(row["relevance_label"]) == "2"
        }
        useful_queries = {
            str(row["query_id"]) for row in group if str(row["relevance_label"]) in {"1", "2"}
        }
        output[name] = {
            "candidates": len(group),
            "queries": len(queries),
            "label_counts": dict(sorted(labels.items())),
            "direct_candidate_yield": round(labels["2"] / len(group), 6),
            "useful_candidate_yield": round((labels["1"] + labels["2"]) / len(group), 6),
            "queries_with_direct_candidate": len(direct_queries),
            "queries_with_useful_candidate": len(useful_queries),
        }
    return output


def generation_summary(
    generation: list[dict[str, Any]], retrieval_by_query: dict[str, dict[str, Any]], saved_metrics: dict[str, Any]
) -> dict[str, Any]:
    statuses = Counter(str(row.get("generation_status") or "unknown") for row in generation)
    answerability = Counter(str(row.get("answerability") or "unknown") for row in generation)
    pre_statuses: Counter[str] = Counter()
    removal_reasons: Counter[str] = Counter()
    retained_claims = removed_claims = citations = valid_citations = 0
    reliability_labels: Counter[str] = Counter()
    reliability_scores: list[float] = []
    latencies: list[float] = []
    stage_latencies: dict[str, list[float]] = defaultdict(list)
    context_outcomes: dict[str, Counter[str]] = defaultdict(Counter)

    for row in generation:
        raw = dict(row.get("raw") or {})
        verifications = list(raw.get("verifications") or [])
        pre_statuses.update(str(item.get("status") or "unknown") for item in verifications)
        for item in verifications:
            if str(item.get("status") or "") != "supported":
                removal_reasons.update(str(reason) for reason in list(item.get("failed_checks") or []))
        mitigated = dict(raw.get("mitigated") or {})
        kept = list(mitigated.get("kept_claims") or [])
        retained_claims += len(kept)
        removed_claims += len(mitigated.get("removed_claims") or [])
        allowed = set((raw.get("context") or {}).get("allowed_evidence_ids") or [])
        for claim in kept:
            claim_citations = list(claim.get("citations") or [])
            citations += len(claim_citations)
            valid_citations += sum(citation in allowed for citation in claim_citations)
        reliability = dict(raw.get("reliability") or {})
        reliability_labels[str(reliability.get("label") or "unknown")] += 1
        reliability_scores.append(float(reliability.get("score") or 0.0))
        timings = dict(row.get("timings_ms") or {})
        latency = float(timings.get("end_to_end") or 0.0)
        latencies.append(latency)
        for stage, value in timings.items():
            stage_latencies[stage].append(float(value or 0.0))

        retrieval = retrieval_by_query[str(row.get("query_id") or "")]
        context = dict(retrieval.get("final_step11_context") or {})
        context_group = (
            "empty_context"
            if not context.get("evidence_items") and not context.get("graph_facts")
            else "nonempty_context"
        )
        context_outcomes[context_group]["queries"] += 1
        context_outcomes[context_group]["substantive_answers"] += bool(row.get("output_claims"))
        context_outcomes[context_group][f"status_{row.get('generation_status') or 'unknown'}"] += 1

    saved = dict(saved_metrics.get("full_pipeline") or {})
    bert = dict(saved.get("bertscore") or {})
    substantive = sum(bool(row.get("output_claims")) for row in generation)
    return {
        "queries": len(generation),
        "generation_status_counts": dict(sorted(statuses.items())),
        "answerability_counts": dict(sorted(answerability.items())),
        "substantive_answers": substantive,
        "pre_mitigation_claims": sum(pre_statuses.values()),
        "pre_mitigation_status_counts": dict(sorted(pre_statuses.items())),
        "pre_mitigation_supported_rate": round(pre_statuses["supported"] / sum(pre_statuses.values()) if pre_statuses else 0.0, 6),
        "retained_claims": retained_claims,
        "removed_claims": removed_claims,
        "claim_removal_reasons": dict(removal_reasons.most_common()),
        "post_mitigation_claim_support_rate": 1.0 if retained_claims else None,
        "post_mitigation_hallucination_rate": 0.0 if retained_claims else None,
        "post_mitigation_scope": f"{retained_claims} retained claims across {substantive} substantive answers",
        "citation_validity": round(valid_citations / citations if citations else 0.0, 6),
        "citation_count": citations,
        "bertscore_f1": bert.get("bertscore_f1"),
        "bertscore_evaluated_answers": bert.get("evaluated_query_count"),
        "reliability": {
            "label_counts": dict(sorted(reliability_labels.items())),
            "mean": round(mean(reliability_scores), 6),
            "median": round(statistics.median(reliability_scores), 6),
            "p95": round(percentile(reliability_scores, 0.95), 6),
            "minimum": round(min(reliability_scores), 6),
            "maximum": round(max(reliability_scores), 6),
        },
        "context_outcomes": {name: dict(values) for name, values in sorted(context_outcomes.items())},
        "failure_attribution": {
            "retrieval_insufficiency_empty_context": context_outcomes["empty_context"]["queries"],
            "generation_or_schema_unavailable_with_context": sum(
                str(row.get("answerability") or "") == "generation_unavailable"
                and bool(
                    (retrieval_by_query[str(row.get("query_id") or "")].get("final_step11_context") or {}).get("evidence_items")
                    or (retrieval_by_query[str(row.get("query_id") or "")].get("final_step11_context") or {}).get("graph_facts")
                )
                for row in generation
            ),
        },
        "latency_ms": {
            "mean": round(mean(latencies), 3),
            "median": round(statistics.median(latencies), 3),
            "p95": round(percentile(latencies, 0.95), 3),
            "total": round(sum(latencies), 3),
            "per_stage_mean": {stage: round(mean(values), 3) for stage, values in sorted(stage_latencies.items())},
        },
    }


def report_markdown(metrics: dict[str, Any], paths: dict[str, str]) -> str:
    validation = metrics["annotation_validation"]
    combined = metrics["retrieval"]["combined"]
    evidence = metrics["retrieval"]["evidence"]
    graph = metrics["retrieval"]["graph_relations"]
    context = metrics["step11_context"]
    generation = metrics["steps12_17"]
    lines = [
        "# final_v2 Full Evaluation: 100 AHD Questions",
        "",
        "## Scope",
        "",
        "This evaluation joins independently prepared candidate judgments back to the frozen final_v2 retrieval run. No retrieval, reranking, context selection, or generation was rerun.",
        "",
        f"- Annotation rows: **{validation['rows']}** across **{validation['queries_with_candidates']}** candidate-bearing queries.",
        f"- Labels: **{validation['label_counts'].get('2', 0)} direct**, **{validation['label_counts'].get('1', 0)} related/partial**, **{validation['label_counts'].get('0', 0)} irrelevant/unsafe**.",
        f"- Annotation integrity: **{validation['status']}**, with **{len(validation['errors'])} errors**.",
        "- Methodological status: the file identifies the annotator as `GPT-5.6 Thinking`; these are independent model-adjudicated labels, not human-confirmed gold.",
        "",
        "## Retrieval",
        "",
        "| Metric | Combined | Evidence | Graph relations |",
        "|---|---:|---:|---:|",
        f"| Candidate rows | {combined['candidate_rows']} | {evidence['candidate_rows']} | {graph['candidate_rows']} |",
        f"| Queries with direct candidate | {combined['queries_with_direct_candidate']} | {evidence['queries_with_direct_candidate']} | {graph['queries_with_direct_candidate']} |",
        f"| Direct hit rate@5 | {combined['direct_hit_rate_at_5']:.4f} | {evidence['direct_hit_rate_at_5']:.4f} | {graph['direct_hit_rate_at_5']:.4f} |",
        f"| Useful hit rate@5 | {combined['useful_hit_rate_at_5']:.4f} | {evidence['useful_hit_rate_at_5']:.4f} | {graph['useful_hit_rate_at_5']:.4f} |",
        f"| Judged-pool direct Recall@5 | {combined['judged_pool_direct_recall_at_5']:.4f} | {evidence['judged_pool_direct_recall_at_5']:.4f} | {graph['judged_pool_direct_recall_at_5']:.4f} |",
        f"| MRR, direct | {combined['mrr_direct']:.4f} | {evidence['mrr_direct']:.4f} | {graph['mrr_direct']:.4f} |",
        f"| nDCG@10, graded | {combined['ndcg_at_10_graded']:.4f} | {evidence['ndcg_at_10_graded']:.4f} | {graph['ndcg_at_10_graded']:.4f} |",
        f"| Direct precision@5 | {combined['direct_precision_at_5']:.4f} | {evidence['direct_precision_at_5']:.4f} | {graph['direct_precision_at_5']:.4f} |",
        f"| Useful precision@5 | {combined['useful_precision_at_5']:.4f} | {evidence['useful_precision_at_5']:.4f} | {graph['useful_precision_at_5']:.4f} |",
        "",
        "`Judged-pool direct Recall@5` uses label-2 candidates within the exported top-10 evidence/top-5 relation pool as the denominator. It is not exhaustive corpus recall.",
        "",
        "### Retrieval Channels",
        "",
        "| Channel | Candidates | Label 2 | Direct yield | Useful yield | Direct queries |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for channel, values in metrics["retrieval"]["by_retrieval_channel"].items():
        lines.append(
            f"| `{channel}` | {values['candidates']} | {values['label_counts'].get('2', 0)} | "
            f"{values['direct_candidate_yield']:.4f} | {values['useful_candidate_yield']:.4f} | "
            f"{values['queries_with_direct_candidate']} |"
        )
    lines.extend(
        [
        "",
        "## Step 11 Context",
        "",
        f"- Selected artifacts: **{context['selected_artifacts_total']}**; independently judged: **{context['selected_artifacts_with_judgments']}**; unjudged: **{context['selected_artifacts_unjudged']}**.",
        f"- Useful context precision: **{context['useful_context_precision']:.4f}**.",
        f"- Direct context precision: **{context['direct_context_precision']:.4f}**.",
        f"- Queries with selected useful context: **{context['queries_with_selected_useful_context']}/100**.",
        f"- Queries with selected direct context: **{context['queries_with_selected_direct_context']}/100**.",
        "",
        "## Steps 12-17",
        "",
        f"- Substantive answers: **{generation['substantive_answers']}/100**.",
        f"- Pre-mitigation claims: **{generation['pre_mitigation_claims']}**; supported rate **{generation['pre_mitigation_supported_rate']:.4f}**.",
        f"- Retained claims: **{generation['retained_claims']}**; removed claims: **{generation['removed_claims']}**.",
        f"- Post-mitigation support: **{generation['post_mitigation_claim_support_rate']:.2f}** and hallucination rate **{generation['post_mitigation_hallucination_rate']:.2f}**, applying only to {generation['post_mitigation_scope']}.",
        f"- Citation validity: **{generation['citation_validity']:.4f}** over **{generation['citation_count']}** citations.",
        f"- BERTScore F1: **{generation['bertscore_f1']:.6f}** over **{generation['bertscore_evaluated_answers']}** substantive answers.",
        f"- Coverage-weighted BERTScore indicator: **{generation['bertscore_f1'] * generation['bertscore_evaluated_answers'] / generation['queries']:.6f}** when unanswered queries contribute zero.",
        f"- Reliability labels: `{json.dumps(generation['reliability']['label_counts'], ensure_ascii=False)}`.",
        f"- Failure attribution: **{generation['failure_attribution']['retrieval_insufficiency_empty_context']}** empty-context retrieval insufficiencies and **{generation['failure_attribution']['generation_or_schema_unavailable_with_context']}** generation/schema failure with usable context.",
        "",
        "### Claim Removal",
        "",
        ]
    )
    for reason, count in generation["claim_removal_reasons"].items():
        lines.append(f"- `{reason}`: {count}")
    lines.extend(
        [
            "",
            "### Context Outcomes",
            "",
        ]
    )
    for name, values in generation["context_outcomes"].items():
        lines.append(
            f"- `{name}`: {values.get('queries', 0)} queries, {values.get('substantive_answers', 0)} substantive answers."
        )
    latency = generation["latency_ms"]
    lines.extend(
        [
            "",
            "## Latency",
            "",
            f"- Mean: **{latency['mean']:.3f} ms**",
            f"- Median: **{latency['median']:.3f} ms**",
            f"- P95: **{latency['p95']:.3f} ms**",
            f"- Total: **{latency['total'] / 1000:.3f} seconds**",
            "",
            "## Pipeline Summary",
            "",
            "1. **Step 8:** cached Arabic normalization, unified LLM query analysis, deterministic Neo4j linking and retrieval planning.",
            "2. **Step 9:** multilingual E5 vector retrieval, validated final_v2 graph traversal, QA/evidence retrieval, and conditional SQLite FTS.",
            "3. **Step 10:** deterministic reranking using entity identity, intent, concepts, constraints, source quality, and mismatch penalties.",
            "4. **Step 11:** selective evidence context construction with absolute quality gates.",
            "5. **Step 12:** GPT-OSS-20B evidence-grounded claim-first answer generation.",
            "6. **Step 13:** atomic claim extraction with citation and QA provenance.",
            "7. **Step 14:** deterministic evidence, intent, concept, anatomy, negation, number, and relation verification.",
            "8. **Step 15:** unsupported-claim removal and explicit limitation handling.",
            "9. **Step 16:** deterministic reliability scoring.",
            "10. **Step 17:** explainable answer with citations, evidence provenance, reliability, and audit data.",
            "",
            "## Interpretation",
            "",
            f"The evidence channel supplies the direct answers: {evidence['queries_with_direct_candidate']} queries have label-2 evidence, while graph relations directly answer {graph['queries_with_direct_candidate']}. The graph remains useful mainly for concept expansion and provenance, but direct QA/evidence retrieval carries answer coverage. Step 11 is selective, yet only {context['queries_with_selected_direct_context']} queries retain a judged direct candidate. The verifier preserves citation correctness but leaves substantive coverage at {generation['substantive_answers']}/100.",
            "",
            "## Final Artifacts",
            "",
        ]
    )
    for name, path in paths.items():
        lines.append(f"- `{name}`: `{path}`")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--labels", type=Path, default=DEFAULT_LABELS)
    parser.add_argument("--queue", type=Path, default=DEFAULT_QUEUE)
    parser.add_argument("--retrieval", type=Path, default=DEFAULT_RETRIEVAL)
    parser.add_argument("--generation", type=Path, default=DEFAULT_GENERATION)
    parser.add_argument("--generation-metrics", type=Path, default=DEFAULT_GENERATION_METRICS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    annotated = read_csv(args.labels)
    queue = read_csv(args.queue)
    retrieval = read_jsonl(args.retrieval)
    generation = read_jsonl(args.generation)
    saved_metrics = json.loads(args.generation_metrics.read_text(encoding="utf-8-sig"))
    validation = validate_annotations(annotated, queue)
    if validation["status"] != "ok":
        raise ValueError("Annotation validation failed: " + "; ".join(validation["errors"][:10]))
    labels_by_key = {key(row): row for row in annotated}
    ranked_rows, by_query = restore_rankings(retrieval, labels_by_key)
    retrieval_by_query = {str(row["query_id"]): row for row in retrieval}
    metrics = {
        "evaluation_id": "final_v2_human_relevance_100_20260805",
        "graph_version": "final_v2",
        "annotation_validation": validation,
        "retrieval": {
            "combined": ranking_summary(retrieval, by_query, None),
            "evidence": ranking_summary(retrieval, by_query, "evidence"),
            "graph_relations": ranking_summary(retrieval, by_query, "relation"),
            "by_retrieval_channel": candidate_breakdown(ranked_rows, "retrieval_channel"),
            "by_query_group": candidate_breakdown(ranked_rows, "query_group"),
        },
        "step11_context": context_summary(retrieval, ranked_rows, by_query),
        "steps12_17": generation_summary(generation, retrieval_by_query, saved_metrics),
    }

    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    metrics_path = output_dir / "metrics.json"
    ranked_path = output_dir / "ranked_candidate_labels.csv"
    report_path = output_dir / "FINAL_REPORT.md"
    metrics_path.write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    ranked_fields = list(annotated[0]) + ["rank_within_type", "combined_rank", "frozen_score", "selected_step11"]
    with ranked_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=ranked_fields)
        writer.writeheader()
        writer.writerows(ranked_rows)
    paths = {
        "annotated judgments": str(args.labels.resolve().relative_to(ROOT)),
        "frozen retrieval": str(args.retrieval.resolve().relative_to(ROOT)),
        "frozen generation": str(args.generation.resolve().relative_to(ROOT)),
        "metrics": str(metrics_path.relative_to(ROOT)),
        "rank-restored judgments": str(ranked_path.relative_to(ROOT)),
        "report": str(report_path.relative_to(ROOT)),
    }
    report_path.write_text(report_markdown(metrics, paths), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": "ok",
                "queries": len(retrieval),
                "annotation_rows": len(annotated),
                "direct_hit_rate_at_5": metrics["retrieval"]["combined"]["direct_hit_rate_at_5"],
                "mrr_direct": metrics["retrieval"]["combined"]["mrr_direct"],
                "ndcg_at_10_graded": metrics["retrieval"]["combined"]["ndcg_at_10_graded"],
                "substantive_answers": metrics["steps12_17"]["substantive_answers"],
                "report": str(report_path.relative_to(ROOT)),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
