import argparse
import json
from collections import Counter, defaultdict

from step13_17_utils import (
    INSUFFICIENT_EVIDENCE_AR,
    INSUFFICIENT_WITH_DISCLAIMER_AR,
    REFINED_CSV,
    REFINED_JSON,
    REPORT_DIR,
    VERIFICATION_JSON,
    answer_records,
    clean_text,
    load_json,
    parse_json_field,
    relpath,
    safe_divide,
    truncate,
    write_csv,
    write_json,
    write_report,
)


REPORT_MD = REPORT_DIR / "trial_graph_v1_step15_hallucination_mitigation_report.md"


def group_verifications():
    grouped = defaultdict(list)
    for row in load_json(VERIFICATION_JSON, default=[]):
        grouped[row["query_id"]].append(row)
    for rows in grouped.values():
        rows.sort(key=lambda row: int(row.get("claim_rank") or 0))
    return grouped


def refined_answer_from_claims(claims, include_weak=False):
    kept_statuses = {"supported"}
    if include_weak:
        kept_statuses.add("weakly_supported")
    kept = [row for row in claims if row["support_status"] in kept_statuses]
    if not kept:
        return INSUFFICIENT_WITH_DISCLAIMER_AR, []
    sentences = []
    for row in kept:
        evidence_ids = parse_json_field(row.get("valid_evidence_ids"), default=[])
        qa_ids = parse_json_field(row.get("valid_source_qa_ids"), default=[])
        citation_bits = []
        if evidence_ids:
            citation_bits.append(",".join(evidence_ids))
        if qa_ids:
            citation_bits.append(",".join(qa_ids))
        citation = f" [{' | '.join(citation_bits)}]" if citation_bits else ""
        sentences.append(f"{clean_text(row['claim_ar'])}{citation}")
    return " ".join(sentences), kept


def answerability_label(claim_rows, kept, removed):
    if not kept:
        return "insufficient_evidence"
    if removed:
        return "partially_answerable"
    return "answerable"


def append_partial_limitation(refined_answer, removed):
    if not removed:
        return refined_answer
    missing = [clean_text(row["claim_ar"]) for row in removed if clean_text(row.get("claim_ar", ""))]
    if not missing:
        return refined_answer
    limitation = "لا توجد أدلة كافية في السياق المسترجع لدعم: " + "؛ ".join(missing[:2])
    return f"{refined_answer} {limitation}."


def mitigate(include_weak=False, limit=None):
    answers = answer_records()
    if limit:
        answers = answers[:limit]
    verifications = group_verifications()
    rows = []
    for answer in answers:
        query_id = answer.get("query_id", "")
        claim_rows = verifications.get(query_id, [])
        refined_answer, kept = refined_answer_from_claims(claim_rows, include_weak=include_weak)
        removed = [row for row in claim_rows if row not in kept]
        answerability = answerability_label(claim_rows, kept, removed)
        if answerability == "partially_answerable":
            refined_answer = append_partial_limitation(refined_answer, removed)
        supported_count = len([row for row in claim_rows if row["support_status"] in {"supported", "weakly_supported"}])
        unsupported_count = len([row for row in claim_rows if row["support_status"] == "unsupported"])
        rows.append(
            {
                "query_id": query_id,
                "query": clean_text(answer.get("query", "")),
                "original_answer_ar": clean_text(answer.get("answer_ar", "")),
                "refined_answer_ar": refined_answer,
                "kept_claims": json.dumps([row["claim_ar"] for row in kept], ensure_ascii=False),
                "removed_claims": json.dumps([row["claim_ar"] for row in removed], ensure_ascii=False),
                "limitations_ar": json.dumps(parse_json_field(answer.get("limitations_ar"), default=[]), ensure_ascii=False),
                "answerability_label": answerability,
                "claim_count": len(claim_rows),
                "kept_claim_count": len(kept),
                "removed_claim_count": len(removed),
                "claim_support_rate": round(safe_divide(supported_count, len(claim_rows)), 4),
                "hallucination_rate": round(safe_divide(unsupported_count, len(claim_rows)), 4),
                "mitigation_action": "removed_unsupported_claims" if removed else "no_claims_removed",
                "refined_preview": truncate(refined_answer, 320),
            }
        )
    return rows


def main():
    parser = argparse.ArgumentParser(description="Step 15: remove unsupported claims and create grounded refined answers.")
    parser.add_argument("--include-weak", action="store_true", help="Keep weakly-supported claims in the refined answer.")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    rows = mitigate(include_weak=args.include_weak, limit=args.limit)
    fieldnames = [
        "query_id",
        "query",
        "original_answer_ar",
        "refined_answer_ar",
        "kept_claims",
        "removed_claims",
        "limitations_ar",
        "answerability_label",
        "claim_count",
        "kept_claim_count",
        "removed_claim_count",
        "claim_support_rate",
        "hallucination_rate",
        "mitigation_action",
        "refined_preview",
    ]
    write_json(REFINED_JSON, rows)
    write_csv(REFINED_CSV, rows, fieldnames)

    total_claims = sum(int(row["claim_count"]) for row in rows)
    removed_claims = sum(int(row["removed_claim_count"]) for row in rows)
    average_support = safe_divide(sum(float(row["claim_support_rate"]) for row in rows), len(rows))
    average_hallucination = safe_divide(sum(float(row["hallucination_rate"]) for row in rows), len(rows))
    answerability_counts = Counter(row["answerability_label"] for row in rows)
    write_report(
        REPORT_MD,
        [
            "# Step 15 Hallucination Mitigation Report",
            "",
            f"- Answers refined: {len(rows)}",
            f"- Claims considered: {total_claims}",
            f"- Claims removed: {removed_claims}",
            f"- Answerability labels: {dict(answerability_counts)}",
            f"- Average claim-support rate: {average_support:.4f}",
            f"- Average hallucination rate: {average_hallucination:.4f}",
            f"- Refined answers JSON: `{relpath(REFINED_JSON)}`",
            f"- Refined answers CSV: `{relpath(REFINED_CSV)}`",
        ],
    )
    print(
        json.dumps(
            {
                "answers_refined": len(rows),
                "claims_considered": total_claims,
                "claims_removed": removed_claims,
                "answerability_labels": dict(answerability_counts),
                "average_claim_support_rate": round(average_support, 4),
                "average_hallucination_rate": round(average_hallucination, 4),
                "refined_csv": relpath(REFINED_CSV),
                "refined_json": relpath(REFINED_JSON),
                "report_md": relpath(REPORT_MD),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
