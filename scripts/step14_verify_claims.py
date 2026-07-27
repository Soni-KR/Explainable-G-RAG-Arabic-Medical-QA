import argparse
import json
from collections import Counter, defaultdict

from step13_17_utils import (
    CLAIMS_JSON,
    REPORT_DIR,
    VERIFICATION_CSV,
    VERIFICATION_JSON,
    context_index,
    evidence_index_for_bundle,
    evidence_text,
    lexical_overlap,
    load_json,
    parse_json_field,
    relpath,
    truncate,
    write_csv,
    write_json,
    write_report,
)


REPORT_MD = REPORT_DIR / "trial_graph_v1_step14_claim_verification_report.md"


def best_evidence_matches(claim, evidence_rows, cited_ids):
    pool = evidence_rows
    if cited_ids:
        cited_pool = [row for row in evidence_rows if row["evidence_id"] in cited_ids]
        if cited_pool:
            pool = cited_pool
    scored = []
    for row in pool:
        score = lexical_overlap(claim["claim_ar"], evidence_text(row))
        scored.append((score, row))
    scored.sort(key=lambda item: item[0], reverse=True)
    return scored[:3]


def verify_claim(claim, evidence_rows, support_threshold, weak_threshold):
    cited_ids = parse_json_field(claim.get("citations"), default=[])
    source_qa_ids = parse_json_field(claim.get("source_qa_ids"), default=[])
    available_evidence_ids = {row["evidence_id"] for row in evidence_rows}
    available_qa_ids = {row["qa_id"] for row in evidence_rows if row.get("qa_id")}

    valid_citations = [eid for eid in cited_ids if eid in available_evidence_ids]
    valid_qa_ids = [qa_id for qa_id in source_qa_ids if qa_id in available_qa_ids]
    matches = best_evidence_matches(claim, evidence_rows, valid_citations)
    best_score = matches[0][0] if matches else 0.0
    best_rows = [row for _, row in matches if _ > 0]

    is_fallback_claim = claim.get("extraction_source") == "sentence_fallback"
    citation_valid = bool(valid_citations) if cited_ids else is_fallback_claim
    qa_valid = bool(valid_qa_ids) if source_qa_ids else is_fallback_claim
    source_anchor_valid = citation_valid or qa_valid
    effective_support_threshold = 0.45 if is_fallback_claim else support_threshold
    effective_weak_threshold = 0.30 if is_fallback_claim else weak_threshold

    if best_score >= effective_support_threshold and source_anchor_valid:
        status = "supported"
        reason = "claim terms overlap retrieved evidence and cited/source ids are valid"
    elif (best_score >= effective_weak_threshold and source_anchor_valid) or valid_citations or valid_qa_ids:
        status = "weakly_supported"
        reason = "partial evidence match or partial source/citation support"
    else:
        status = "unsupported"
        reason = "no sufficient lexical evidence support in the retrieved subgraph"

    return {
        "query_id": claim["query_id"],
        "query": claim.get("query", ""),
        "claim_id": claim["claim_id"],
        "claim_rank": claim.get("claim_rank", ""),
        "claim_ar": claim["claim_ar"],
        "support_status": status,
        "support_score": round(best_score, 4),
        "citation_valid": citation_valid,
        "qa_valid": qa_valid,
        "cited_evidence_ids": json.dumps(cited_ids, ensure_ascii=False),
        "valid_evidence_ids": json.dumps(valid_citations, ensure_ascii=False),
        "source_qa_ids": json.dumps(source_qa_ids, ensure_ascii=False),
        "valid_source_qa_ids": json.dumps(valid_qa_ids, ensure_ascii=False),
        "supporting_relations": json.dumps([row.get("relation", "") for row in best_rows], ensure_ascii=False),
        "supporting_evidence": json.dumps(
            [
                {
                    "evidence_id": row["evidence_id"],
                    "qa_id": row.get("qa_id", ""),
                    "evidence_text": row.get("evidence_text", ""),
                    "relation": row.get("relation", ""),
                }
                for row in best_rows
            ],
            ensure_ascii=False,
        ),
        "verification_reason": reason,
        "best_evidence_preview": truncate(best_rows[0].get("evidence_text", "") if best_rows else "", 280),
    }


def verify_claims(support_threshold=0.08, weak_threshold=0.04, limit=None):
    claims = load_json(CLAIMS_JSON, default=[])
    if limit:
        claims = claims[:limit]
    contexts = context_index()
    rows = []
    missing_context = defaultdict(int)
    for claim in claims:
        bundle = contexts.get(claim["query_id"])
        if not bundle:
            missing_context[claim["query_id"]] += 1
            continue
        evidence_rows = evidence_index_for_bundle(bundle)
        rows.append(verify_claim(claim, evidence_rows, support_threshold, weak_threshold))
    return rows, missing_context


def main():
    parser = argparse.ArgumentParser(description="Step 14: verify extracted claims against retrieved graph evidence.")
    parser.add_argument("--support-threshold", type=float, default=0.08)
    parser.add_argument("--weak-threshold", type=float, default=0.04)
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    rows, missing_context = verify_claims(args.support_threshold, args.weak_threshold, args.limit)
    fieldnames = [
        "query_id",
        "query",
        "claim_id",
        "claim_rank",
        "claim_ar",
        "support_status",
        "support_score",
        "citation_valid",
        "qa_valid",
        "cited_evidence_ids",
        "valid_evidence_ids",
        "source_qa_ids",
        "valid_source_qa_ids",
        "supporting_relations",
        "supporting_evidence",
        "verification_reason",
        "best_evidence_preview",
    ]
    write_json(VERIFICATION_JSON, rows)
    write_csv(VERIFICATION_CSV, rows, fieldnames)

    status_counts = Counter(row["support_status"] for row in rows)
    supported = status_counts["supported"] + status_counts["weakly_supported"]
    support_rate = supported / len(rows) if rows else 0.0
    hallucination_rate = status_counts["unsupported"] / len(rows) if rows else 0.0
    write_report(
        REPORT_MD,
        [
            "# Step 14 Graph-Based Fact Verification Report",
            "",
            f"- Verified claims: {len(rows)}",
            f"- Status counts: {dict(status_counts)}",
            f"- Claim-support rate: {support_rate:.4f}",
            f"- Hallucination rate: {hallucination_rate:.4f}",
            f"- Missing context rows: {dict(missing_context)}",
            f"- Verification JSON: `{relpath(VERIFICATION_JSON)}`",
            f"- Verification CSV: `{relpath(VERIFICATION_CSV)}`",
        ],
    )
    print(
        json.dumps(
            {
                "verified_claims": len(rows),
                "status_counts": dict(status_counts),
                "claim_support_rate": round(support_rate, 4),
                "hallucination_rate": round(hallucination_rate, 4),
                "verification_csv": relpath(VERIFICATION_CSV),
                "verification_json": relpath(VERIFICATION_JSON),
                "report_md": relpath(REPORT_MD),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
