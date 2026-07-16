import argparse
import json
from collections import Counter

from step13_17_utils import (
    CLAIMS_CSV,
    CLAIMS_JSON,
    INSUFFICIENT_EVIDENCE_AR,
    REPORT_DIR,
    answer_records,
    clean_text,
    is_insufficient_evidence_text,
    is_safety_disclaimer,
    parse_json_field,
    relpath,
    sentence_split,
    write_csv,
    write_json,
    write_report,
)


REPORT_MD = REPORT_DIR / "trial_graph_v1_step13_claim_extraction_report.md"


def normalize_list(value):
    if isinstance(value, list):
        return [clean_text(item) for item in value if clean_text(item)]
    if isinstance(value, str) and value.strip():
        return [clean_text(value)]
    return []


def claims_from_structured_answer(answer):
    rows = []
    claims = parse_json_field(answer.get("claims"), default=[])
    if not isinstance(claims, list):
        return rows
    for idx, claim in enumerate(claims, start=1):
        if not isinstance(claim, dict):
            continue
        claim_text = clean_text(claim.get("claim_ar") or claim.get("claim") or "")
        if not claim_text:
            continue
        if is_insufficient_evidence_text(claim_text) or is_safety_disclaimer(claim_text):
            continue
        rows.append(
            {
                "claim_rank": idx,
                "claim_ar": claim_text,
                "citations": normalize_list(claim.get("citations", [])),
                "source_qa_ids": normalize_list(claim.get("source_qa_ids", [])),
                "support_status_hint": clean_text(claim.get("support_status", "")),
                "extraction_source": "structured_llm_claims",
            }
        )
    return rows


def claims_from_answer_text(answer):
    answer_text = clean_text(answer.get("answer_ar", ""))
    if not answer_text or INSUFFICIENT_EVIDENCE_AR in answer_text:
        return []
    rows = []
    for idx, sentence in enumerate(sentence_split(answer_text), start=1):
        if is_insufficient_evidence_text(sentence) or is_safety_disclaimer(sentence):
            continue
        rows.append(
            {
                "claim_rank": idx,
                "claim_ar": sentence,
                "citations": [],
                "source_qa_ids": [],
                "support_status_hint": "",
                "extraction_source": "sentence_fallback",
            }
        )
    return rows


def extract_claims(limit=None):
    rows = []
    answers = answer_records()
    if limit:
        answers = answers[:limit]
    for answer in answers:
        query_id = answer.get("query_id", "")
        claims = claims_from_structured_answer(answer) or claims_from_answer_text(answer)
        for claim in claims:
            rows.append(
                {
                    "query_id": query_id,
                    "query": clean_text(answer.get("query", "")),
                    "claim_id": f"{query_id}_claim_{claim['claim_rank']:02d}",
                    "claim_rank": claim["claim_rank"],
                    "claim_ar": claim["claim_ar"],
                    "answer_ar": clean_text(answer.get("answer_ar", "")),
                    "citations": json.dumps(claim["citations"], ensure_ascii=False),
                    "source_qa_ids": json.dumps(claim["source_qa_ids"], ensure_ascii=False),
                    "used_relations": json.dumps(
                        parse_json_field(answer.get("used_relations"), default=[]),
                        ensure_ascii=False,
                    ),
                    "support_status_hint": claim["support_status_hint"],
                    "extraction_source": claim["extraction_source"],
                }
            )
    return rows


def main():
    parser = argparse.ArgumentParser(description="Step 13: extract answer claims for graph verification.")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    rows = extract_claims(limit=args.limit)
    fieldnames = [
        "query_id",
        "query",
        "claim_id",
        "claim_rank",
        "claim_ar",
        "answer_ar",
        "citations",
        "source_qa_ids",
        "used_relations",
        "support_status_hint",
        "extraction_source",
    ]
    write_json(CLAIMS_JSON, rows)
    write_csv(CLAIMS_CSV, rows, fieldnames)

    by_source = Counter(row["extraction_source"] for row in rows)
    query_count = len({row["query_id"] for row in rows})
    write_report(
        REPORT_MD,
        [
            "# Step 13 Claim Extraction Report",
            "",
            f"- Claims extracted: {len(rows)}",
            f"- Queries with claims: {query_count}",
            f"- Extraction sources: {dict(by_source)}",
            f"- Claims JSON: `{relpath(CLAIMS_JSON)}`",
            f"- Claims CSV: `{relpath(CLAIMS_CSV)}`",
        ],
    )
    print(
        json.dumps(
            {
                "claims": len(rows),
                "queries_with_claims": query_count,
                "claims_csv": relpath(CLAIMS_CSV),
                "claims_json": relpath(CLAIMS_JSON),
                "report_md": relpath(REPORT_MD),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
