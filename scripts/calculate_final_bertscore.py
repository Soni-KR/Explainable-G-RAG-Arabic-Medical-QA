from __future__ import annotations

import csv
import json
import argparse
from pathlib import Path
from statistics import mean

from bert_score import score


ROOT = Path(__file__).resolve().parents[1]
FINAL_CSV = ROOT / "outputs/05_trial_graph_v1/final_output/trial_graph_v1_final_explainable_output.csv"
QA_SOURCES_CSV = ROOT / "outputs/05_trial_graph_v1/import/trial_graph_v1_qa_sources.csv"
OUT_DIR = ROOT / "outputs/05_trial_graph_v1/evaluation"
REPORT_MD = ROOT / "reports/trial_graph_v1_final_bertscore_report.md"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def main() -> None:
    parser = argparse.ArgumentParser(description="Calculate BERTScore for final Arabic answers.")
    parser.add_argument("--model-type", default="bert-base-multilingual-cased")
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--reference-csv", default=str(QA_SOURCES_CSV.relative_to(ROOT)))
    parser.add_argument("--reference-query-id-col", default="")
    parser.add_argument("--reference-query-col", default="question")
    parser.add_argument("--reference-answer-col", default="answer")
    parser.add_argument("--output-prefix", default="trial_graph_v1_final_bertscore")
    args = parser.parse_args()

    final_rows = read_csv(FINAL_CSV)
    reference_csv = ROOT / args.reference_csv if not Path(args.reference_csv).is_absolute() else Path(args.reference_csv)
    reference_rows = read_csv(reference_csv)
    answer_by_question = {
        row.get(args.reference_query_col, "").strip(): row.get(args.reference_answer_col, "").strip()
        for row in reference_rows
        if row.get(args.reference_query_col, "").strip()
    }
    answer_by_query_id = {}
    if args.reference_query_id_col:
        answer_by_query_id = {
            row.get(args.reference_query_id_col, "").strip(): row.get(args.reference_answer_col, "").strip()
            for row in reference_rows
            if row.get(args.reference_query_id_col, "").strip()
        }

    pairs: list[dict[str, str]] = []
    missing: list[str] = []
    for row in final_rows:
        query = row.get("query", "").strip()
        candidate = row.get("final_answer_ar", "").strip()
        reference = answer_by_query_id.get(row.get("query_id", "").strip(), "") or answer_by_question.get(query, "")
        if not reference:
            missing.append(row.get("query_id", ""))
            continue
        pairs.append(
            {
                "query_id": row.get("query_id", ""),
                "query": query,
                "candidate_answer": candidate,
                "reference_answer": reference,
            }
        )

    if not pairs:
        raise RuntimeError("No final answers could be matched to QA source references.")

    candidates = [row["candidate_answer"] for row in pairs]
    references = [row["reference_answer"] for row in pairs]
    precision, recall, f1 = score(
        candidates,
        references,
        model_type=args.model_type,
        lang="ar",
        batch_size=args.batch_size,
        verbose=True,
        rescale_with_baseline=False,
    )

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    per_row_path = OUT_DIR / f"{args.output_prefix}.csv"
    summary_path = OUT_DIR / f"{args.output_prefix}_summary.json"

    output_rows = []
    for row, p, r, f in zip(pairs, precision.tolist(), recall.tolist(), f1.tolist()):
        output_rows.append(
            {
                **row,
                "bertscore_precision": round(float(p), 6),
                "bertscore_recall": round(float(r), 6),
                "bertscore_f1": round(float(f), 6),
            }
        )

    with per_row_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(output_rows[0].keys()))
        writer.writeheader()
        writer.writerows(output_rows)

    summary = {
        "rows_total_final_output": len(final_rows),
        "rows_matched_to_reference": len(pairs),
        "rows_missing_reference": len(missing),
        "missing_query_ids": missing,
        "model_type": args.model_type,
        "reference_csv": str(reference_csv.relative_to(ROOT)),
        "lang": "ar",
        "rescale_with_baseline": False,
        "mean_bertscore_precision": round(mean(row["bertscore_precision"] for row in output_rows), 6),
        "mean_bertscore_recall": round(mean(row["bertscore_recall"] for row in output_rows), 6),
        "mean_bertscore_f1": round(mean(row["bertscore_f1"] for row in output_rows), 6),
        "per_question_csv": str(per_row_path.relative_to(ROOT)),
    }
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text(
        "\n".join(
            [
                "# Final Answer BERTScore Evaluation",
                "",
                f"- Candidate answers: `{FINAL_CSV.relative_to(ROOT)}`",
                f"- Reference answers: `{reference_csv.relative_to(ROOT)}`",
                f"- Matched rows: {summary['rows_matched_to_reference']} / {summary['rows_total_final_output']}",
                f"- Model: `{summary['model_type']}`",
                f"- Mean BERTScore Precision: {summary['mean_bertscore_precision']}",
                f"- Mean BERTScore Recall: {summary['mean_bertscore_recall']}",
                f"- Mean BERTScore F1: {summary['mean_bertscore_f1']}",
                "",
                f"Per-question results are saved to `{per_row_path.relative_to(ROOT)}`.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
