from __future__ import annotations

"""Compare frozen v3 and evidence-adaptive v4 runs without rerunning any stage."""

import argparse
import csv
import difflib
import json
import math
import re
import statistics
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
ARABIC_DIACRITICS = re.compile(r"[\u0610-\u061a\u064b-\u065f\u0670\u06d6-\u06ed]")
NON_WORD = re.compile(r"[^\w\u0600-\u06ff]+", re.UNICODE)
CITATION = re.compile(r"\[[A-Za-z]\d+\]")

REVIEW_FIELDS = (
    "review_decision",
    "safety_error_types",
    "reviewer_notes",
    "reviewer_type",
)
SAFE_DECISIONS = {"safe", "equivalent_to_v3_kept"}
UNSAFE_DECISION = "unsafe"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare two complete frozen v3/v4 cohort pairs offline."
    )
    parser.add_argument("--v3-cohort-a", type=Path, required=True)
    parser.add_argument("--v4-cohort-a", type=Path, required=True)
    parser.add_argument("--v3-cohort-b", type=Path, required=True)
    parser.add_argument("--v4-cohort-b", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def resolve_run_file(path: Path) -> Path:
    resolved = path if path.is_absolute() else ROOT / path
    if resolved.is_dir():
        resolved = resolved / "full_pipeline.jsonl"
    if not resolved.exists():
        raise FileNotFoundError(f"Missing frozen run: {resolved}")
    return resolved


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8-sig") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def normalize_text(value: Any) -> str:
    text = unicodedata.normalize("NFKC", str(value or ""))
    text = CITATION.sub(" ", text)
    text = ARABIC_DIACRITICS.sub("", text).replace("\u0640", "")
    text = text.translate(str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ى": "ي"}))
    return " ".join(NON_WORD.sub(" ", text).lower().split())


def claim_similarity(left: str, right: str) -> float:
    left_norm = normalize_text(left)
    right_norm = normalize_text(right)
    if not left_norm or not right_norm:
        return 0.0
    sequence = difflib.SequenceMatcher(None, left_norm, right_norm).ratio()
    left_tokens = set(left_norm.split())
    right_tokens = set(right_norm.split())
    overlap = len(left_tokens & right_tokens)
    token_f1 = (
        2.0 * overlap / (len(left_tokens) + len(right_tokens))
        if left_tokens and right_tokens
        else 0.0
    )
    return max(sequence, token_f1)


def percentile(values: list[float], fraction: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def distribution(values: Iterable[float]) -> dict[str, float]:
    materialized = [float(value) for value in values]
    if not materialized:
        return {"mean": 0.0, "median": 0.0, "p95": 0.0, "total": 0.0}
    return {
        "mean": round(statistics.fmean(materialized), 6),
        "median": round(statistics.median(materialized), 6),
        "p95": round(percentile(materialized, 0.95), 6),
        "total": round(sum(materialized), 6),
    }


def require_complete_pair(
    cohort: str,
    v3_records: list[dict[str, Any]],
    v4_records: list[dict[str, Any]],
) -> None:
    if len(v3_records) != 100 or len(v4_records) != 100:
        raise ValueError(
            f"{cohort} is incomplete: v3={len(v3_records)}, v4={len(v4_records)}; "
            "the comparison requires exactly 100 records per run."
        )
    v3_ids = [str(row.get("query_id") or "") for row in v3_records]
    v4_ids = [str(row.get("query_id") or "") for row in v4_records]
    if len(set(v3_ids)) != 100 or len(set(v4_ids)) != 100:
        raise ValueError(f"{cohort} contains duplicate or blank query IDs.")
    if set(v3_ids) != set(v4_ids):
        raise ValueError(f"{cohort} v3/v4 query IDs do not match.")

    v3_by_id = {str(row["query_id"]): row for row in v3_records}
    for v4_row in v4_records:
        query_id = str(v4_row["query_id"])
        v3_context = (v3_by_id[query_id].get("raw") or {}).get("context")
        v4_context = (v4_row.get("raw") or {}).get("context")
        if v3_context != v4_context:
            raise ValueError(
                f"{cohort} {query_id} does not reuse the exact frozen context."
            )


def failure_reason(record: dict[str, Any]) -> str:
    generated = dict((record.get("raw") or {}).get("generated") or {})
    return str(generated.get("fallback_reason") or "")


def is_technical_failure(record: dict[str, Any]) -> bool:
    generated = dict((record.get("raw") or {}).get("generated") or {})
    return str(generated.get("fallback_type") or "") == "technical_failure"


def summarize_run(run_file: Path, records: list[dict[str, Any]]) -> dict[str, Any]:
    status_counts = Counter(str(row.get("generation_status") or "") for row in records)
    answerability = Counter(str(row.get("answerability") or "") for row in records)
    verifications = [
        verification
        for row in records
        for verification in (row.get("raw") or {}).get("verifications") or []
    ]
    verification_status = Counter(
        str(item.get("status") or "unknown") for item in verifications
    )
    kept_claims = [
        claim for row in records for claim in row.get("output_claims") or []
    ]
    substantive = [row for row in records if row.get("output_claims")]
    technical = [row for row in records if is_technical_failure(row)]
    schema_failures = [
        row
        for row in technical
        if any(
            marker in failure_reason(row).lower()
            for marker in ("schema", "json_validate_failed", "missing properties")
        )
    ]

    citation_count = 0
    valid_citation_count = 0
    for row in records:
        context = dict((row.get("raw") or {}).get("context") or {})
        allowed = set(context.get("allowed_evidence_ids") or [])
        present = {
            str(item.get("evidence_id") or "")
            for item in context.get("evidence_items") or []
        }
        for claim in row.get("output_claims") or []:
            for citation in claim.get("citations") or []:
                citation_count += 1
                if citation in allowed and citation in present:
                    valid_citation_count += 1

    metrics_file = run_file.parent / "metrics.json"
    saved_metrics = load_json(metrics_file).get("full_pipeline", {})
    stage_names = sorted(
        {
            stage
            for row in records
            for stage in dict(row.get("timings_ms") or {})
        }
    )
    latencies = {
        stage: distribution(
            float((row.get("timings_ms") or {}).get(stage) or 0.0)
            for row in records
        )
        for stage in stage_names
    }
    pre_total = sum(verification_status.values())
    return {
        "run_file": relative(run_file),
        "queries": len(records),
        "generation_status": dict(sorted(status_counts.items())),
        "answerability": dict(sorted(answerability.items())),
        "substantive_answers": len(substantive),
        "surviving_claims": len(kept_claims),
        "pre_mitigation_claims": {
            "total": pre_total,
            "status_counts": dict(sorted(verification_status.items())),
            "supported_claim_rate": round(
                verification_status["supported"] / pre_total if pre_total else 0.0,
                6,
            ),
        },
        "technical_failures": len(technical),
        "schema_failures": len(schema_failures),
        "citation_validity": round(
            valid_citation_count / citation_count if citation_count else 0.0,
            6,
        ),
        "citation_count": citation_count,
        "bertscore": saved_metrics.get("bertscore", {}),
        "latency_ms": latencies,
    }


def aggregate(summaries: list[dict[str, Any]]) -> dict[str, Any]:
    pre_counts: Counter[str] = Counter()
    status: Counter[str] = Counter()
    answerability: Counter[str] = Counter()
    for summary in summaries:
        pre_counts.update(summary["pre_mitigation_claims"]["status_counts"])
        status.update(summary["generation_status"])
        answerability.update(summary["answerability"])
    pre_total = sum(pre_counts.values())
    bert_rows = [
        (
            int(summary["bertscore"].get("evaluated_query_count") or 0),
            float(summary["bertscore"].get("bertscore_f1") or 0.0),
        )
        for summary in summaries
        if summary["bertscore"].get("status") == "computed"
    ]
    bert_count = sum(count for count, _ in bert_rows)
    latency_stages = sorted(
        {
            stage
            for summary in summaries
            for stage in summary["latency_ms"]
        }
    )
    # Reconstruct aggregate distributions in compare_pair, where raw records exist.
    return {
        "queries": sum(summary["queries"] for summary in summaries),
        "generation_status": dict(sorted(status.items())),
        "answerability": dict(sorted(answerability.items())),
        "substantive_answers": sum(
            summary["substantive_answers"] for summary in summaries
        ),
        "surviving_claims": sum(summary["surviving_claims"] for summary in summaries),
        "pre_mitigation_claims": {
            "total": pre_total,
            "status_counts": dict(sorted(pre_counts.items())),
            "supported_claim_rate": round(
                pre_counts["supported"] / pre_total if pre_total else 0.0,
                6,
            ),
        },
        "technical_failures": sum(
            summary["technical_failures"] for summary in summaries
        ),
        "schema_failures": sum(summary["schema_failures"] for summary in summaries),
        "citation_validity": round(
            sum(summary["citation_count"] * summary["citation_validity"] for summary in summaries)
            / sum(summary["citation_count"] for summary in summaries)
            if sum(summary["citation_count"] for summary in summaries)
            else 0.0,
            6,
        ),
        "bertscore": {
            "status": "computed" if bert_count else "unavailable",
            "evaluated_query_count": bert_count,
            "bertscore_f1": round(
                sum(count * score for count, score in bert_rows) / bert_count
                if bert_count
                else 0.0,
                6,
            ),
        },
        "latency_stages": latency_stages,
    }


def closest_claim(
    claim: str,
    candidates: list[tuple[str, str]],
) -> tuple[str, str, float]:
    if not candidates:
        return "", "", 0.0
    scored = [
        (source, candidate, claim_similarity(claim, candidate))
        for source, candidate in candidates
    ]
    source, candidate, score = max(scored, key=lambda item: item[2])
    return source, candidate, score


def evidence_for_claim(
    record: dict[str, Any],
    citations: list[str],
) -> list[dict[str, Any]]:
    context = dict((record.get("raw") or {}).get("context") or {})
    by_id = {
        str(item.get("evidence_id") or ""): item
        for item in context.get("evidence_items") or []
    }
    return [by_id[citation] for citation in citations if citation in by_id]


def verification_for_claim(
    record: dict[str, Any],
    claim_text: str,
) -> dict[str, Any]:
    for verification in (record.get("raw") or {}).get("verifications") or []:
        candidate = str((verification.get("claim") or {}).get("claim") or "")
        if normalize_text(candidate) == normalize_text(claim_text):
            return dict(verification)
    return {}


def differential_rows(
    cohort: str,
    v3_records: list[dict[str, Any]],
    v4_records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    v3_by_id = {str(row["query_id"]): row for row in v3_records}
    output: list[dict[str, Any]] = []
    for v4_row in v4_records:
        query_id = str(v4_row["query_id"])
        v3_row = v3_by_id[query_id]
        v3_kept = [
            ("v3_kept", str(item.get("claim") or ""))
            for item in v3_row.get("output_claims") or []
        ]
        v3_all = [
            str(item.get("claim") or "")
            for item in (v3_row.get("raw") or {}).get("claims") or []
        ]
        kept_norms = {normalize_text(text) for _, text in v3_kept}
        v3_removed = [
            ("v3_removed", text)
            for text in v3_all
            if normalize_text(text) not in kept_norms
        ]
        all_v3 = v3_kept + v3_removed

        for position, claim in enumerate(v4_row.get("output_claims") or [], start=1):
            text = str(claim.get("claim") or "")
            kept_source, kept_text, kept_score = closest_claim(text, v3_kept)
            if kept_source and kept_score >= 0.82:
                continue
            source, closest_text, similarity = closest_claim(text, all_v3)
            differential_type = (
                "removed_or_rephrased_from_v3"
                if source == "v3_removed" and similarity >= 0.72
                else "not_produced_by_v3"
            )
            citations = [str(item) for item in claim.get("citations") or []]
            evidence_items = evidence_for_claim(v4_row, citations)
            verification = verification_for_claim(v4_row, text)
            context = dict((v4_row.get("raw") or {}).get("context") or {})
            allowed = set(context.get("allowed_evidence_ids") or [])
            present = {
                str(item.get("evidence_id") or "")
                for item in context.get("evidence_items") or []
            }
            stable_id = f"{cohort}:{query_id}:{position}"
            output.append(
                {
                    "differential_id": stable_id,
                    "cohort": cohort,
                    "query_id": query_id,
                    "query": str(v4_row.get("query") or ""),
                    "reference_answer": str(
                        (v4_row.get("gold") or {}).get("reference_answer") or ""
                    ),
                    "generation_mode": str(
                        ((v4_row.get("raw") or {}).get("generated") or {}).get(
                            "generation_mode"
                        )
                        or ""
                    ),
                    "v4_claim": text,
                    "v4_citations": " | ".join(citations),
                    "cited_evidence": "\n---\n".join(
                        str(item.get("evidence") or "") for item in evidence_items
                    ),
                    "evidence_qa_ids": " | ".join(
                        sorted(
                            {
                                str(item.get("qa_id") or "")
                                for item in evidence_items
                                if item.get("qa_id")
                            }
                        )
                    ),
                    "verification_status": str(verification.get("status") or ""),
                    "support_score": verification.get("support_score", ""),
                    "question_relevance": verification.get(
                        "question_relevance", ""
                    ),
                    "failed_checks": " | ".join(
                        str(item) for item in verification.get("failed_checks") or []
                    ),
                    "differential_type": differential_type,
                    "closest_v3_claim": closest_text,
                    "closest_v3_similarity": round(similarity, 6),
                    "automatic_citation_valid": str(
                        bool(citations)
                        and all(item in allowed and item in present for item in citations)
                    ).lower(),
                    "automatic_verifier_supported": str(
                        verification.get("status") == "supported"
                    ).lower(),
                    "review_decision": "",
                    "safety_error_types": "",
                    "reviewer_notes": "",
                    "reviewer_type": "",
                }
            )
    return output


def preserve_reviews(
    audit_path: Path,
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    previous: dict[str, dict[str, Any]] = {}
    if audit_path.exists():
        with audit_path.open("r", encoding="utf-8-sig", newline="") as handle:
            previous = {
                str(row.get("differential_id") or ""): row
                for row in csv.DictReader(handle)
            }
    decisions_path = audit_path.parent / "differential_review_decisions.json"
    decisions = load_json(decisions_path) if decisions_path.exists() else {}
    for row in rows:
        differential_id = str(row["differential_id"])
        prior = previous.get(differential_id, {})
        decision = dict(decisions.get(differential_id) or {})
        for field in REVIEW_FIELDS:
            row[field] = str(decision.get(field) or prior.get(field) or "")
        if decision and not row["reviewer_type"]:
            row["reviewer_type"] = "codex_evidence_fidelity_review"
    return rows


def review_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    decisions = Counter(str(row.get("review_decision") or "pending") for row in rows)
    invalid_citations = sum(
        str(row.get("automatic_citation_valid")) != "true" for row in rows
    )
    verifier_failures = sum(
        str(row.get("automatic_verifier_supported")) != "true" for row in rows
    )
    complete = all(
        str(row.get("review_decision") or "")
        in SAFE_DECISIONS | {UNSAFE_DECISION}
        for row in rows
    )
    return {
        "differential_claims": len(rows),
        "review_decisions": dict(sorted(decisions.items())),
        "automatic_invalid_citations": invalid_citations,
        "automatic_verifier_failures": verifier_failures,
        "review_complete": complete,
        "unsafe_claims": decisions[UNSAFE_DECISION],
    }


def relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path.resolve())


def add_latency_aggregate(
    target: dict[str, Any],
    records: list[dict[str, Any]],
) -> None:
    stages = sorted(
        {
            stage
            for row in records
            for stage in dict(row.get("timings_ms") or {})
        }
    )
    target["latency_ms"] = {
        stage: distribution(
            float((row.get("timings_ms") or {}).get(stage) or 0.0)
            for row in records
        )
        for stage in stages
    }


def delta(v3: dict[str, Any], v4: dict[str, Any]) -> dict[str, Any]:
    return {
        "substantive_answers": (
            v4["substantive_answers"] - v3["substantive_answers"]
        ),
        "surviving_claims": v4["surviving_claims"] - v3["surviving_claims"],
        "pre_mitigation_supported_claim_rate": round(
            v4["pre_mitigation_claims"]["supported_claim_rate"]
            - v3["pre_mitigation_claims"]["supported_claim_rate"],
            6,
        ),
        "technical_failures": (
            v4["technical_failures"] - v3["technical_failures"]
        ),
        "schema_failures": v4["schema_failures"] - v3["schema_failures"],
        "citation_validity": round(
            v4["citation_validity"] - v3["citation_validity"],
            6,
        ),
        "bertscore_f1": round(
            float(v4["bertscore"].get("bertscore_f1") or 0.0)
            - float(v3["bertscore"].get("bertscore_f1") or 0.0),
            6,
        ),
    }


def markdown_report(result: dict[str, Any]) -> str:
    lines = [
        "# Evidence-Adaptive Generation v4.2: Frozen v3 Comparison",
        "",
        "This report compares only Steps 12–17. Both versions use the exact same",
        "saved Step 11 context per query; Steps 8–11, `final_v1`, embeddings,",
        "retrieval, reranking, prompts outside Step 12, and verification thresholds",
        "were not rerun or changed.",
        "",
        "## Decision",
        "",
        f"**{result['decision']['status']}**",
        "",
        result["decision"]["reason"],
        "",
        "## Main Results",
        "",
        "| Scope | Version | Substantive answers | Surviving claims | "
        "Pre-mitigation support | Technical/schema failures | Citation validity | "
        "BERTScore F1 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for scope in ("cohort_a", "cohort_b", "aggregate_200"):
        display = {
            "cohort_a": "AHD reference 100",
            "cohort_b": "Entity-GT 100",
            "aggregate_200": "Aggregate 200",
        }[scope]
        for version in ("v3", "v4"):
            summary = result[scope][version]
            lines.append(
                f"| {display} | {version} | {summary['substantive_answers']} | "
                f"{summary['surviving_claims']} | "
                f"{summary['pre_mitigation_claims']['supported_claim_rate']:.3f} | "
                f"{summary['technical_failures']}/{summary['schema_failures']} | "
                f"{summary['citation_validity']:.3f} | "
                f"{float(summary['bertscore'].get('bertscore_f1') or 0.0):.6f} |"
            )
    lines.extend(
        [
            "",
            "BERTScore is scoped to substantive post-mitigation answers with an AHD",
            "reference; it is not a score over fallback/abstention text.",
            "",
            "## Differential Safety Review",
            "",
            f"- Differential v4 claims: "
            f"{result['differential_review']['differential_claims']}",
            f"- Evidence-fidelity review complete: "
            f"{result['differential_review']['review_complete']}",
            f"- Unsafe differential claims: "
            f"{result['differential_review']['unsafe_claims']}",
            f"- Invalid citations: "
            f"{result['differential_review']['automatic_invalid_citations']}",
            "",
            (
                "The review checked wrong drugs, changed clinical relations, "
                "anatomy errors, unsupported recommendations, negation/number "
                "errors, and invalid citations."
                if result["differential_review"]["review_complete"]
                else "The production decision remains pending until every "
                "differential claim receives the specified safety review."
            ),
            "",
            "## Outcome Breakdown",
            "",
            "| Version | Generated | Fallback | Fully answerable | Partially "
            "answerable | Supported but incomplete | Insufficient evidence | "
            "Generation unavailable |",
            "|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for version in ("v3", "v4"):
        summary = result["aggregate_200"][version]
        lines.append(
            f"| {version} | "
            f"{summary['generation_status'].get('generated', 0)} | "
            f"{summary['generation_status'].get('fallback', 0)} | "
            f"{summary['answerability'].get('fully_answerable', 0)} | "
            f"{summary['answerability'].get('partially_answerable', 0)} | "
            f"{summary['answerability'].get('supported_but_incomplete', 0)} | "
            f"{summary['answerability'].get('insufficient_evidence', 0)} | "
            f"{summary['answerability'].get('generation_unavailable', 0)} |"
        )
    lines.extend(
        [
            "",
            "## Claim Verification",
            "",
            "| Version | Claims before mitigation | Supported | Weak | Unsupported | "
            "Surviving |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for version in ("v3", "v4"):
        summary = result["aggregate_200"][version]
        counts = summary["pre_mitigation_claims"]["status_counts"]
        lines.append(
            f"| {version} | {summary['pre_mitigation_claims']['total']} | "
            f"{counts.get('supported', 0)} | "
            f"{counts.get('weakly_supported', 0)} | "
            f"{counts.get('unsupported', 0)} | "
            f"{summary['surviving_claims']} |"
        )
    lines.extend(
        [
            "",
            "## Latency",
            "",
            "| Version/stage | Mean ms | Median ms | p95 ms | Total ms |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for version in ("v3", "v4"):
        for stage in ("end_to_end", "step12_answer_generation"):
            values = result["aggregate_200"][version]["latency_ms"][stage]
            lines.append(
                f"| {version} `{stage}` | {values['mean']:.2f} | "
                f"{values['median']:.2f} | {values['p95']:.2f} | "
                f"{values['total']:.2f} |"
            )
    lines.extend(
        [
            "",
            "`end_to_end` includes runner pacing. `step12_answer_generation` is",
            "the cleaner provider/generation comparison.",
            "",
            "## Artifacts",
            "",
        ]
    )
    for name, path in result["artifacts"].items():
        lines.append(f"- `{name}`: `{path}`")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    paths = {
        "v3_a": resolve_run_file(args.v3_cohort_a),
        "v4_a": resolve_run_file(args.v4_cohort_a),
        "v3_b": resolve_run_file(args.v3_cohort_b),
        "v4_b": resolve_run_file(args.v4_cohort_b),
    }
    records = {name: load_jsonl(path) for name, path in paths.items()}
    require_complete_pair("cohort_a", records["v3_a"], records["v4_a"])
    require_complete_pair("cohort_b", records["v3_b"], records["v4_b"])

    summaries = {
        name: summarize_run(paths[name], records[name])
        for name in ("v3_a", "v4_a", "v3_b", "v4_b")
    }
    aggregate_v3 = aggregate([summaries["v3_a"], summaries["v3_b"]])
    aggregate_v4 = aggregate([summaries["v4_a"], summaries["v4_b"]])
    add_latency_aggregate(
        aggregate_v3,
        records["v3_a"] + records["v3_b"],
    )
    add_latency_aggregate(
        aggregate_v4,
        records["v4_a"] + records["v4_b"],
    )

    output_dir = args.output_dir if args.output_dir.is_absolute() else ROOT / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    audit_path = output_dir / "differential_safety_audit.csv"
    differential = differential_rows(
        "ahd_reference_100",
        records["v3_a"],
        records["v4_a"],
    ) + differential_rows(
        "entity_ground_truth_100",
        records["v3_b"],
        records["v4_b"],
    )
    differential = preserve_reviews(audit_path, differential)
    review = review_summary(differential)

    improvement = (
        aggregate_v4["substantive_answers"] > aggregate_v3["substantive_answers"]
        or aggregate_v4["surviving_claims"] > aggregate_v3["surviving_claims"]
    )
    safe = (
        review["review_complete"]
        and review["unsafe_claims"] == 0
        and review["automatic_invalid_citations"] == 0
        and aggregate_v4["citation_validity"] == 1.0
    )
    if safe and improvement:
        decision = {
            "status": "ACCEPT_V4_AS_FINAL",
            "reason": (
                "v4 improves substantive coverage or retained claims, every "
                "differential claim passed review, and citation validity remains 1.00."
            ),
        }
    elif review["review_complete"]:
        decision = {
            "status": "KEEP_V3_AS_FINAL",
            "reason": (
                f"v4 reduced substantive answers from "
                f"{aggregate_v3['substantive_answers']} to "
                f"{aggregate_v4['substantive_answers']} and surviving claims "
                f"from {aggregate_v3['surviving_claims']} to "
                f"{aggregate_v4['surviving_claims']}; the differential review "
                f"also found {review['unsafe_claims']} unsafe claims. Retain v3 "
                "and record v4 as an unsuccessful generation ablation."
            ),
        }
    else:
        decision = {
            "status": "PENDING_DIFFERENTIAL_REVIEW",
            "reason": (
                "The metric comparison is complete, but production acceptance "
                "requires review of every newly retained v4 claim."
            ),
        }

    fields = list(differential[0]) if differential else [
        "differential_id",
        *REVIEW_FIELDS,
    ]
    write_csv(audit_path, differential, fields)
    metrics_path = output_dir / "comparison_metrics.json"
    report_path = output_dir / "FINAL_COMPARISON.md"
    manifest_path = output_dir / "manifest.json"
    result = {
        "cohort_a": {
            "v3": summaries["v3_a"],
            "v4": summaries["v4_a"],
            "delta": delta(summaries["v3_a"], summaries["v4_a"]),
        },
        "cohort_b": {
            "v3": summaries["v3_b"],
            "v4": summaries["v4_b"],
            "delta": delta(summaries["v3_b"], summaries["v4_b"]),
        },
        "aggregate_200": {
            "v3": aggregate_v3,
            "v4": aggregate_v4,
            "delta": delta(aggregate_v3, aggregate_v4),
        },
        "differential_review": review,
        "decision": decision,
        "artifacts": {
            "comparison_metrics": relative(metrics_path),
            "differential_safety_audit": relative(audit_path),
            "differential_review_decisions": relative(
                output_dir / "differential_review_decisions.json"
            ),
            "final_comparison": relative(report_path),
            "manifest": relative(manifest_path),
        },
    }
    write_json(metrics_path, result)
    write_json(
        manifest_path,
        {
            "analysis_only": True,
            "pipeline_steps_rerun": [],
            "v3_untouched": True,
            "exact_frozen_context_required": True,
            "claim_equivalence_threshold": 0.82,
            "v3_removed_similarity_threshold": 0.72,
            "inputs": {name: relative(path) for name, path in paths.items()},
            "outputs": result["artifacts"],
            "review_scope": (
                "Codex evidence-fidelity and query-safety review; not a human "
                "clinical correctness annotation."
            ),
        },
    )
    report_path.write_text(markdown_report(result), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": decision["status"],
                "v3_substantive": aggregate_v3["substantive_answers"],
                "v4_substantive": aggregate_v4["substantive_answers"],
                "v3_claims": aggregate_v3["surviving_claims"],
                "v4_claims": aggregate_v4["surviving_claims"],
                "differential_claims": len(differential),
                "output_dir": relative(output_dir),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
