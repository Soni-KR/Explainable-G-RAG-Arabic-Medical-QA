import argparse
import json
from collections import Counter

from step13_17_utils import (
    FINAL_CSV,
    FINAL_JSON,
    FINAL_MD,
    INSUFFICIENT_EVIDENCE_AR,
    INSUFFICIENT_WITH_DISCLAIMER_AR,
    REFINED_JSON,
    RELIABILITY_JSON,
    REPORT_DIR,
    VERIFICATION_JSON,
    context_index,
    evidence_index_for_bundle,
    load_json,
    parse_json_field,
    relpath,
    truncate,
    write_csv,
    write_json,
    write_report,
)


REPORT_MD = REPORT_DIR / "trial_graph_v1_step17_final_output_report.md"


def reliability_index():
    payload = load_json(RELIABILITY_JSON, default={})
    rows = payload.get("rows", payload if isinstance(payload, list) else [])
    return {row["query_id"]: row for row in rows}


def verification_index():
    grouped = {}
    for row in load_json(VERIFICATION_JSON, default=[]):
        grouped.setdefault(row["query_id"], []).append(row)
    return grouped


def source_cards(query_id, contexts, max_sources=6):
    bundle = contexts.get(query_id, {})
    evidence_rows = evidence_index_for_bundle(bundle)
    cards = []
    seen = set()
    for row in evidence_rows:
        key = (row.get("qa_id"), row.get("evidence_text"))
        if key in seen:
            continue
        seen.add(key)
        cards.append(
            {
                "evidence_id": row.get("evidence_id", ""),
                "qa_id": row.get("qa_id", ""),
                "evidence_text": row.get("evidence_text", ""),
                "relation": row.get("relation", ""),
            }
        )
        if len(cards) >= max_sources:
            break
    return cards


def supporting_relations(claim_rows):
    relations = []
    seen = set()
    for row in claim_rows:
        if row.get("support_status") not in {"supported", "weakly_supported"}:
            continue
        for relation in parse_json_field(row.get("supporting_relations"), default=[]):
            if relation and relation not in seen:
                seen.add(relation)
                relations.append(relation)
    return relations


def explanation_for(row, relations, sources, reliability):
    if row["refined_answer_ar"] in {INSUFFICIENT_EVIDENCE_AR, INSUFFICIENT_WITH_DISCLAIMER_AR}:
        return "لم يتم إصدار إجابة طبية لأن الأدلة المسترجعة لا تدعم ادعاءات كافية. الجملة الخاصة باستشارة الطبيب تُعامل كتنبيه سلامة ثابت وليست ادعاءً طبياً محسوباً ضمن الأدلة."
    parts = []
    if row.get("answerability_label") == "partially_answerable":
        parts.append("تمت الإجابة فقط عن الجزء المدعوم بالأدلة، مع توضيح الجزء غير المدعوم.")
    if relations:
        parts.append(f"تم دعم الإجابة بواسطة {len(relations)} علاقة طبية مسترجعة.")
    if sources:
        parts.append(f"اعتمدت الإجابة على {len(sources)} أدلة مصدرية من قاعدة AHD.")
    if reliability:
        parts.append(
            "درجة الثقة حُسبت من دعم الادعاءات، تغطية الأدلة، ثقة العلاقات، موثوقية المصادر، ومعدل الهلوسة."
        )
    parts.append("تم حذف الادعاءات غير المدعومة قبل إخراج الإجابة النهائية.")
    return " ".join(parts)


def build_outputs():
    refined_rows = load_json(REFINED_JSON, default=[])
    reliabilities = reliability_index()
    verifications = verification_index()
    contexts = context_index()
    rows = []
    for refined in refined_rows:
        query_id = refined["query_id"]
        claim_rows = verifications.get(query_id, [])
        reliability = reliabilities.get(query_id, {})
        relations = supporting_relations(claim_rows)
        sources = source_cards(query_id, contexts)
        rows.append(
            {
                "query_id": query_id,
                "query": refined.get("query", ""),
                "final_answer_ar": refined.get("refined_answer_ar", ""),
                "explanation_ar": explanation_for(refined, relations, sources, reliability),
                "answerability_label": reliability.get(
                    "answerability_label", refined.get("answerability_label", "")
                ),
                "supporting_relations": json.dumps(relations, ensure_ascii=False),
                "sources_and_evidence": json.dumps(sources, ensure_ascii=False),
                "overall_reliability_score": reliability.get(
                    "overall_reliability_score", reliability.get("reliability_score", "")
                ),
                "reliability_score": reliability.get("reliability_score", ""),
                "reliability_label": reliability.get("reliability_label", ""),
                "relation_confidence": reliability.get("relation_confidence", ""),
                "source_reliability": reliability.get("source_reliability", ""),
                "evidence_coverage": reliability.get("evidence_coverage", ""),
                "claim_support_rate": reliability.get("claim_support_rate", refined.get("claim_support_rate", "")),
                "hallucination_rate": reliability.get("hallucination_rate", refined.get("hallucination_rate", "")),
                "supporting_relation_count": reliability.get("supporting_relation_count", ""),
                "unique_source_count": reliability.get("unique_source_count", ""),
                "removed_claims": refined.get("removed_claims", "[]"),
                "limitations_ar": refined.get("limitations_ar", "[]"),
            }
        )
    return rows


def write_markdown(rows):
    lines = ["# Trial Graph V1 Final Explainable Output", ""]
    for row in rows:
        sources = parse_json_field(row["sources_and_evidence"], default=[])
        relations = parse_json_field(row["supporting_relations"], default=[])
        removed = parse_json_field(row["removed_claims"], default=[])
        lines.extend(
            [
                f"## {row['query_id']}",
                "",
                f"**Question:** {row['query']}",
                "",
                f"**Final answer:** {row['final_answer_ar']}",
                "",
                f"**Explanation:** {row['explanation_ar']}",
                "",
                f"**Answerability:** {row['answerability_label']}",
                "",
                f"**Reliability:** {row['reliability_score']} ({row['reliability_label']})",
                "",
                "**Reliability components:**",
                f"- Claim support rate: {row['claim_support_rate']}",
                f"- Evidence coverage: {row['evidence_coverage']}",
                f"- Relation confidence: {row['relation_confidence']}",
                f"- Source reliability: {row['source_reliability']}",
                f"- Hallucination rate: {row['hallucination_rate']}",
                "",
                "**Supporting relations:**",
            ]
        )
        if relations:
            lines.extend([f"- {relation}" for relation in relations[:8]])
        else:
            lines.append("- لا توجد علاقات داعمة كافية.")
        lines.extend(["", "**Sources and evidence:**"])
        if sources:
            for source in sources:
                lines.append(
                    f"- {source.get('evidence_id', '')} / {source.get('qa_id', '')}: "
                    f"{truncate(source.get('evidence_text', ''), 260)}"
                )
        else:
            lines.append("- لا توجد أدلة كافية.")
        if removed:
            lines.extend(["", "**Removed unsupported claims:**"])
            lines.extend([f"- {claim}" for claim in removed])
        lines.append("")
    write_report(FINAL_MD, lines)


def main():
    parser = argparse.ArgumentParser(description="Step 17: build final explainable Graph-RAG outputs.")
    parser.parse_args()

    rows = build_outputs()
    fieldnames = [
        "query_id",
        "query",
        "final_answer_ar",
        "explanation_ar",
        "answerability_label",
        "supporting_relations",
        "sources_and_evidence",
        "overall_reliability_score",
        "reliability_score",
        "reliability_label",
        "relation_confidence",
        "source_reliability",
        "evidence_coverage",
        "claim_support_rate",
        "hallucination_rate",
        "supporting_relation_count",
        "unique_source_count",
        "removed_claims",
        "limitations_ar",
    ]
    write_json(FINAL_JSON, rows)
    write_csv(FINAL_CSV, rows, fieldnames)
    write_markdown(rows)
    write_report(
        REPORT_MD,
        [
            "# Step 17 Final Explainable Output Report",
            "",
            f"- Final outputs: {len(rows)}",
            f"- Answerability labels: {dict(Counter(row['answerability_label'] for row in rows))}",
            f"- Final JSON: `{relpath(FINAL_JSON)}`",
            f"- Final CSV: `{relpath(FINAL_CSV)}`",
            f"- Final Markdown: `{relpath(FINAL_MD)}`",
        ],
    )
    print(
        json.dumps(
            {
                "final_outputs": len(rows),
                "final_csv": relpath(FINAL_CSV),
                "final_json": relpath(FINAL_JSON),
                "final_md": relpath(FINAL_MD),
                "report_md": relpath(REPORT_MD),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
