from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean


ROOT = Path(__file__).resolve().parents[1]
TOKEN_RE = re.compile(r"[\w\u0600-\u06ff]+", re.UNICODE)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def normalize(value: str) -> str:
    value = str(value or "").strip()
    value = re.sub(r"[\u064b-\u0652\u0670]", "", value)
    value = value.translate(str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ى": "ي", "ة": "ه"}))
    return value.lower()


def tokens(value: str) -> set[str]:
    return {tok for tok in TOKEN_RE.findall(normalize(value)) if len(tok) > 2}


def overlap(a: str, b: str) -> float:
    left = tokens(a)
    right = tokens(b)
    if not left or not right:
        return 0.0
    return len(left & right) / len(left)


def parse_json_list(value: str) -> list:
    try:
        parsed = json.loads(value or "[]")
        return parsed if isinstance(parsed, list) else []
    except json.JSONDecodeError:
        return []


def short(value: str, limit: int = 220) -> str:
    value = " ".join(str(value or "").split())
    return value if len(value) <= limit else value[: limit - 3].rstrip() + "..."


def classify(row: dict[str, str]) -> str:
    bert = float(row["bertscore_f1"])
    reliability = float(row["overall_reliability_score"])
    evidence_coverage = float(row["evidence_coverage"])
    source_reliability = float(row["source_reliability"])
    context_ref_overlap = float(row["reference_context_overlap"])
    answer_ref_overlap = float(row["answer_reference_overlap"])
    fallback_used = row["qa_fallback_used"] == "yes"

    if bert >= 0.64:
        return "acceptable_similarity"
    if context_ref_overlap < 0.12 and evidence_coverage < 0.25:
        return "retrieval_coverage_gap"
    if fallback_used and context_ref_overlap < 0.18:
        return "weak_or_irrelevant_qa_fallback"
    if reliability >= 0.75 and answer_ref_overlap < 0.18:
        return "reference_mismatch_or_answer_wording"
    if source_reliability < 0.6:
        return "source_reliability_gap"
    return "mixed_case_review_needed"


def category_summary(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[row.get("category", "") or "Uncategorized"].append(row)
    out = []
    for category, items in grouped.items():
        out.append(
            {
                "category": category,
                "count": str(len(items)),
                "mean_bertscore_f1": f"{mean(float(r['bertscore_f1']) for r in items):.6f}",
                "min_bertscore_f1": f"{min(float(r['bertscore_f1']) for r in items):.6f}",
                "mean_reliability": f"{mean(float(r['overall_reliability_score']) for r in items):.6f}",
            }
        )
    return sorted(out, key=lambda r: (float(r["mean_bertscore_f1"]), -int(r["count"])))


def load_run(reference_csv: Path, bert_csv: Path, final_csv: Path) -> list[dict[str, str]]:
    references = {row["query_id"]: row for row in read_csv(reference_csv)}
    final = {row["query_id"]: row for row in read_csv(final_csv)}
    rows = []
    for bert in read_csv(bert_csv):
        query_id = bert["query_id"]
        ref = references.get(query_id, {})
        fin = final.get(query_id, {})
        context_text = " ".join(
            [
                fin.get("supporting_relations", ""),
                fin.get("sources_and_evidence", ""),
                fin.get("explanation_ar", ""),
            ]
        )
        relation_text = fin.get("supporting_relations", "")
        row = {
            "query_id": query_id,
            "category": ref.get("category", ""),
            "bertscore_precision": bert.get("bertscore_precision", ""),
            "bertscore_recall": bert.get("bertscore_recall", ""),
            "bertscore_f1": bert.get("bertscore_f1", ""),
            "overall_reliability_score": fin.get("overall_reliability_score", "0"),
            "reliability_label": fin.get("reliability_label", ""),
            "answerability_label": fin.get("answerability_label", ""),
            "evidence_coverage": fin.get("evidence_coverage", "0"),
            "relation_confidence": fin.get("relation_confidence", "0"),
            "source_reliability": fin.get("source_reliability", "0"),
            "claim_support_rate": fin.get("claim_support_rate", "0"),
            "hallucination_rate": fin.get("hallucination_rate", "0"),
            "qa_fallback_used": "yes" if "ANSWERED_BY_AHD_QA_FALLBACK" in relation_text else "no",
            "answer_reference_overlap": f"{overlap(bert.get('candidate_answer', ''), bert.get('reference_answer', '')):.6f}",
            "reference_context_overlap": f"{overlap(bert.get('reference_answer', ''), context_text):.6f}",
            "query": short(bert.get("query", "")),
            "candidate_answer": short(bert.get("candidate_answer", "")),
            "reference_answer": short(bert.get("reference_answer", "")),
        }
        row["issue_label"] = classify(row)
        rows.append(row)
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze unseen Graph-RAG answer quality.")
    parser.add_argument("--first-reference", default="retrieval_gold_annotations_unseen_100_random.csv")
    parser.add_argument("--first-bert", default="outputs/05_trial_graph_v1/evaluation/unseen100_random_live_groq_full_100_t042.csv")
    parser.add_argument("--first-final", default="outputs/05_trial_graph_v1/evaluation/unseen100_random_live_groq_full_100_final_output_t042.csv")
    parser.add_argument("--second-reference", default="retrieval_gold_annotations_unseen_100_random_seed20260727.csv")
    parser.add_argument("--second-bert", default="outputs/05_trial_graph_v1/evaluation/unseen100_random_seed20260727_live_groq_full_100_t042.csv")
    parser.add_argument("--second-final", default="outputs/05_trial_graph_v1/evaluation/unseen100_random_seed20260727_live_groq_full_100_final_output_t042.csv")
    parser.add_argument("--output-dir", default="outputs/05_trial_graph_v1/evaluation/error_analysis")
    parser.add_argument("--report-md", default="reports/unseen100_random_error_analysis_report.md")
    args = parser.parse_args()

    output_dir = ROOT / args.output_dir
    first_rows = load_run(ROOT / args.first_reference, ROOT / args.first_bert, ROOT / args.first_final)
    second_rows = load_run(ROOT / args.second_reference, ROOT / args.second_bert, ROOT / args.second_final)

    write_csv(output_dir / "first_unseen_analysis.csv", first_rows)
    write_csv(output_dir / "second_unseen_analysis.csv", second_rows)
    write_csv(output_dir / "first_unseen_category_summary.csv", category_summary(first_rows))
    write_csv(output_dir / "second_unseen_category_summary.csv", category_summary(second_rows))

    low_second = sorted(second_rows, key=lambda r: float(r["bertscore_f1"]))[:15]
    write_csv(output_dir / "second_unseen_lowest_15.csv", low_second)

    second_issues = Counter(row["issue_label"] for row in second_rows)
    first_issues = Counter(row["issue_label"] for row in first_rows)
    lines = [
        "# Unseen 100 Error Analysis",
        "",
        "## Run Summary",
        "",
        "| Run | Mean BERTScore F1 | Mean reliability | QA fallback queries | Main issue count |",
        "|---|---:|---:|---:|---|",
        (
            f"| First unseen 100 | {mean(float(r['bertscore_f1']) for r in first_rows):.6f} | "
            f"{mean(float(r['overall_reliability_score']) for r in first_rows):.6f} | "
            f"{sum(1 for r in first_rows if r['qa_fallback_used'] == 'yes')} | {dict(first_issues)} |"
        ),
        (
            f"| Second unseen 100 | {mean(float(r['bertscore_f1']) for r in second_rows):.6f} | "
            f"{mean(float(r['overall_reliability_score']) for r in second_rows):.6f} | "
            f"{sum(1 for r in second_rows if r['qa_fallback_used'] == 'yes')} | {dict(second_issues)} |"
        ),
        "",
        "## Lowest Second-Unseen Questions",
        "",
        "| Query ID | Category | BERTScore F1 | Reliability | QA fallback | Issue label |",
        "|---|---|---:|---:|---|---|",
    ]
    for row in low_second:
        lines.append(
            f"| {row['query_id']} | {row['category']} | {row['bertscore_f1']} | "
            f"{row['overall_reliability_score']} | {row['qa_fallback_used']} | {row['issue_label']} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The second unseen set has lower BERTScore than the first, while reliability and hallucination metrics remain stable. "
            "The lowest-score cases should be reviewed first to decide whether the next change should target retrieval coverage, "
            "QA fallback selection, or answer wording.",
            "",
            "## Output Files",
            "",
            f"- First analysis: `{(output_dir / 'first_unseen_analysis.csv').relative_to(ROOT)}`",
            f"- Second analysis: `{(output_dir / 'second_unseen_analysis.csv').relative_to(ROOT)}`",
            f"- Second lowest 15: `{(output_dir / 'second_unseen_lowest_15.csv').relative_to(ROOT)}`",
            f"- First category summary: `{(output_dir / 'first_unseen_category_summary.csv').relative_to(ROOT)}`",
            f"- Second category summary: `{(output_dir / 'second_unseen_category_summary.csv').relative_to(ROOT)}`",
        ]
    )
    report_path = ROOT / args.report_md
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "first_rows": len(first_rows),
                "second_rows": len(second_rows),
                "first_mean_f1": round(mean(float(r["bertscore_f1"]) for r in first_rows), 6),
                "second_mean_f1": round(mean(float(r["bertscore_f1"]) for r in second_rows), 6),
                "first_issues": dict(first_issues),
                "second_issues": dict(second_issues),
                "report_md": str(report_path.relative_to(ROOT)),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
