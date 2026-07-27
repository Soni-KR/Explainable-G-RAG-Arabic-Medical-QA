import argparse
import json
from collections import Counter, defaultdict

from step13_17_utils import (
    REFINED_JSON,
    RELIABILITY_CSV,
    RELIABILITY_JSON,
    REPORT_DIR,
    VERIFICATION_JSON,
    context_index,
    evidence_index_for_bundle,
    evaluation_index,
    load_json,
    parse_json_field,
    relpath,
    safe_divide,
    to_float,
    write_csv,
    write_json,
    write_report,
)


REPORT_MD = REPORT_DIR / "trial_graph_v1_step16_reliability_scoring_report.md"


def group_verifications():
    grouped = defaultdict(list)
    for row in load_json(VERIFICATION_JSON, default=[]):
        grouped[row["query_id"]].append(row)
    return grouped


def reliability_label(score):
    if score >= 0.8:
        return "high"
    if score >= 0.55:
        return "medium"
    return "low"


def evidence_coverage(query_id, claim_rows, contexts):
    bundle = contexts.get(query_id)
    if not bundle:
        return 0.0, 0
    evidence_rows = evidence_index_for_bundle(bundle)
    available_ids = {row["evidence_id"] for row in evidence_rows}
    cited = set()
    for row in claim_rows:
        cited.update(parse_json_field(row.get("valid_evidence_ids"), default=[]))
    return safe_divide(len(cited & available_ids), len(available_ids)), len(available_ids)


def relation_lookup(bundle):
    lookup = {}
    for relation in bundle.get("graph_context", []) or []:
        relation_text = relation.get("relation", "")
        if relation_text:
            lookup[relation_text] = relation
    return lookup


def relation_confidence(query_id, claim_rows, contexts):
    bundle = contexts.get(query_id)
    if not bundle:
        return 0.0, 0
    relations = relation_lookup(bundle)
    supported_relations = set()
    for claim in claim_rows:
        if claim.get("support_status") not in {"supported", "weakly_supported"}:
            continue
        supported_relations.update(parse_json_field(claim.get("supporting_relations"), default=[]))

    scores = []
    for relation_text in supported_relations:
        relation = relations.get(relation_text)
        if not relation:
            continue
        rerank_score = to_float(relation.get("rerank_score"), 0.0)
        reliability = relation.get("reliability", "")
        reliability_prior = {"strong": 1.0, "medium": 0.75, "weak": 0.45}.get(reliability, 0.5)
        evidence_bonus = min(1.0, to_float(relation.get("included_evidence_count") or relation.get("evidence_count"), 0.0) / 3.0)
        scores.append((0.70 * rerank_score) + (0.20 * reliability_prior) + (0.10 * evidence_bonus))
    return safe_divide(sum(scores), len(scores)), len(scores)


def source_reliability(query_id, claim_rows, contexts):
    bundle = contexts.get(query_id)
    if not bundle:
        return 0.0, 0
    evidence_rows = evidence_index_for_bundle(bundle)
    evidence_by_id = {row["evidence_id"]: row for row in evidence_rows}
    qa_ids = set()
    cited_evidence_ids = set()
    evidence_scores = []

    for claim in claim_rows:
        if claim.get("support_status") not in {"supported", "weakly_supported"}:
            continue
        cited_evidence_ids.update(parse_json_field(claim.get("valid_evidence_ids"), default=[]))
        qa_ids.update(parse_json_field(claim.get("valid_source_qa_ids"), default=[]))

    for evidence_id in cited_evidence_ids:
        evidence = evidence_by_id.get(evidence_id)
        if not evidence:
            continue
        relation_reliability = {"strong": 1.0, "medium": 0.75, "weak": 0.45}.get(evidence.get("reliability", ""), 0.5)
        relation_score = to_float(evidence.get("rerank_score"), 0.0)
        has_qa_source = 1.0 if evidence.get("qa_id") else 0.0
        has_evidence_text = 1.0 if evidence.get("evidence_text") else 0.0
        evidence_scores.append(
            (0.45 * has_qa_source)
            + (0.25 * has_evidence_text)
            + (0.20 * relation_reliability)
            + (0.10 * relation_score)
        )

    evidence_quality = safe_divide(sum(evidence_scores), len(evidence_scores))
    source_diversity = min(1.0, safe_divide(len(qa_ids), max(1, len(claim_rows))))
    return (0.70 * evidence_quality) + (0.30 * source_diversity), len(qa_ids)


def score_records():
    refined_rows = load_json(REFINED_JSON, default=[])
    grouped = group_verifications()
    contexts = context_index()
    evals = evaluation_index()
    rows = []
    for refined in refined_rows:
        query_id = refined["query_id"]
        claim_rows = grouped.get(query_id, [])
        claim_count = len(claim_rows)
        answerability = refined.get("answerability_label", "")
        kept_claims = parse_json_field(refined.get("kept_claims"), default=[])
        supported = len(kept_claims)
        unsupported = len([row for row in claim_rows if row["support_status"] == "unsupported"])
        support_rate = safe_divide(supported, claim_count)
        hallucination_rate = safe_divide(unsupported, claim_count)
        supported_claim_rows = [row for row in claim_rows if row.get("claim_ar") in set(kept_claims)]
        mean_support_score = safe_divide(
            sum(to_float(row.get("support_score")) for row in supported_claim_rows),
            len(supported_claim_rows),
        )
        coverage, evidence_count = evidence_coverage(query_id, claim_rows, contexts)
        rel_confidence, supporting_relation_count = relation_confidence(query_id, claim_rows, contexts)
        src_reliability, unique_source_count = source_reliability(query_id, claim_rows, contexts)
        if answerability == "insufficient_evidence":
            support_rate = 0.0
            mean_support_score = 0.0
            coverage = 0.0
            rel_confidence = 0.0
            src_reliability = 0.0
            supporting_relation_count = 0
            unique_source_count = 0
        eval_row = evals.get(query_id, {})
        context_signal = max(
            0.0,
            min(
                1.0,
                to_float(eval_row.get("ragas_faithfulness"), 0.0)
                if eval_row
                else support_rate,
            ),
        )
        score = (
            0.30 * support_rate
            + 0.20 * (1.0 - hallucination_rate)
            + 0.15 * coverage
            + 0.15 * rel_confidence
            + 0.15 * src_reliability
            + 0.05 * context_signal
        )
        if answerability == "insufficient_evidence":
            score = min(score, 0.2)
        rows.append(
            {
                "query_id": query_id,
                "query": refined.get("query", ""),
                "answerability_label": answerability,
                "overall_reliability_score": round(score, 4),
                "reliability_score": round(score, 4),
                "reliability_label": reliability_label(score),
                "claim_support_rate": round(support_rate, 4),
                "hallucination_rate": round(hallucination_rate, 4),
                "mean_support_score": round(mean_support_score, 4),
                "evidence_coverage": round(coverage, 4),
                "relation_confidence": round(rel_confidence, 4),
                "source_reliability": round(src_reliability, 4),
                "evidence_count": evidence_count,
                "supporting_relation_count": supporting_relation_count,
                "unique_source_count": unique_source_count,
                "claim_count": claim_count,
                "context_signal": round(context_signal, 4),
                "calibration_bin": f"{int(score * 10) / 10:.1f}-{min(1.0, int(score * 10) / 10 + 0.1):.1f}",
                "auroc": "not_available_no_gold_labels",
                "auprc": "not_available_no_gold_labels",
                "average_latency_seconds": "not_available_no_timing_trace",
            }
        )
    return rows


def calibration_summary(rows):
    grouped = defaultdict(list)
    for row in rows:
        grouped[row["calibration_bin"]].append(row)
    summary = []
    for bin_name in sorted(grouped):
        group = grouped[bin_name]
        summary.append(
            {
                "bin": bin_name,
                "count": len(group),
                "mean_reliability": round(safe_divide(sum(row["reliability_score"] for row in group), len(group)), 4),
                "mean_claim_support_rate": round(
                    safe_divide(sum(row["claim_support_rate"] for row in group), len(group)), 4
                ),
                "mean_hallucination_rate": round(
                    safe_divide(sum(row["hallucination_rate"] for row in group), len(group)), 4
                ),
            }
        )
    return summary


def main():
    parser = argparse.ArgumentParser(description="Step 16: score reliability from verified claims and evidence coverage.")
    parser.parse_args()

    rows = score_records()
    fieldnames = [
        "query_id",
        "query",
        "answerability_label",
        "overall_reliability_score",
        "reliability_score",
        "reliability_label",
        "claim_support_rate",
        "hallucination_rate",
        "mean_support_score",
        "evidence_coverage",
        "relation_confidence",
        "source_reliability",
        "evidence_count",
        "supporting_relation_count",
        "unique_source_count",
        "claim_count",
        "context_signal",
        "calibration_bin",
        "auroc",
        "auprc",
        "average_latency_seconds",
    ]
    payload = {"rows": rows, "calibration_summary": calibration_summary(rows)}
    write_json(RELIABILITY_JSON, payload)
    write_csv(RELIABILITY_CSV, rows, fieldnames)

    labels = Counter(row["reliability_label"] for row in rows)
    answerability_counts = Counter(row.get("answerability_label", "") for row in rows)
    mean_score = safe_divide(sum(row["reliability_score"] for row in rows), len(rows))
    write_report(
        REPORT_MD,
        [
            "# Step 16 Reliability Scoring Report",
            "",
            f"- Answers scored: {len(rows)}",
            f"- Mean reliability score: {mean_score:.4f}",
            f"- Reliability labels: {dict(labels)}",
            f"- Answerability labels: {dict(answerability_counts)}",
            "- Score formula: 0.30 claim support + 0.20 non-hallucination + 0.15 evidence coverage + 0.15 relation confidence + 0.15 source reliability + 0.05 context signal.",
            "- Relation confidence uses rerank score, relation reliability label, and evidence count for relations supporting verified claims.",
            "- Source reliability uses cited QA source presence, evidence text presence, relation reliability, relation score, and source diversity.",
            "- AUROC/AUPRC: not available because no gold-supported/unsupported answer labels are present.",
            "- Calibration: proxy bins are reported; true calibration needs gold labels.",
            "- Average latency: not available because Step 12 raw timing traces are not stored.",
            f"- Reliability JSON: `{relpath(RELIABILITY_JSON)}`",
            f"- Reliability CSV: `{relpath(RELIABILITY_CSV)}`",
        ],
    )
    print(
        json.dumps(
            {
                "answers_scored": len(rows),
                "mean_reliability_score": round(mean_score, 4),
                "reliability_labels": dict(labels),
                "answerability_labels": dict(answerability_counts),
                "reliability_csv": relpath(RELIABILITY_CSV),
                "reliability_json": relpath(RELIABILITY_JSON),
                "report_md": relpath(REPORT_MD),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
