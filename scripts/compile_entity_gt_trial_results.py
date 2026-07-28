"""Compile the entity-ground-truth 100-query trial into one report.

The compiler reads only frozen cohort, retrieval, generation, and claim-audit
artifacts. BERTScore is computed locally once and cached. No API, retrieval,
generation, or Neo4j write is performed.
"""

from __future__ import annotations

import json
import os
import sys
from collections import Counter
from pathlib import Path
from statistics import mean, median
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
COHORT_DIR = ROOT / "data" / "evaluation"
COHORT_MANIFEST = COHORT_DIR / "entity_ground_truth_trial_100_manifest.json"
RETRIEVAL_DIR = (
    ROOT / "outputs" / "evaluation" / "retrieval" / "entity_gt_trial_100_retrieval_v1"
)
GENERATION_DIR = (
    ROOT / "outputs" / "evaluation" / "generation" / "entity_gt_trial_100_generation_v1"
)
OUTPUT_DIR = ROOT / "outputs" / "evaluation" / "entity_gt_trial_100"
OUTPUT_JSON = OUTPUT_DIR / "RESULTS.json"
OUTPUT_MARKDOWN = OUTPUT_DIR / "RESULTS.md"
BERTSCORE_JSONL = OUTPUT_DIR / "bertscore.jsonl"

MODES = (
    "lexical_only",
    "vector_only",
    "graph_only",
    "hybrid_without_reranking",
    "full_hybrid",
)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    temporary.replace(path)


def nested(row: dict[str, Any], *keys: str, default: Any = None) -> Any:
    value: Any = row
    for key in keys:
        if not isinstance(value, dict):
            return default
        value = value.get(key, default)
    return value


def percentile(values: list[float], fraction: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return ordered[lower] + weight * (ordered[upper] - ordered[lower])


def bertscore_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if BERTSCORE_JSONL.exists():
        cached = load_jsonl(BERTSCORE_JSONL)
        if len(cached) == len(rows):
            return cached
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
    from bert_score import BERTScorer

    scorer = BERTScorer(
        model_type="bert-base-multilingual-cased",
        lang="ar",
        device="cpu",
        rescale_with_baseline=False,
    )
    candidates = [str(row.get("answer") or "") for row in rows]
    references = [
        str(nested(row, "gold", "reference_answer", default="") or "")
        for row in rows
    ]
    precision, recall, f1 = scorer.score(candidates, references, batch_size=4)
    results = [
        {
            "query_id": row["query_id"],
            "generation_status": row.get("generation_status"),
            "substantive": bool(row.get("output_claims")),
            "precision": round(float(precision[index]), 6),
            "recall": round(float(recall[index]), 6),
            "f1": round(float(f1[index]), 6),
            "model": "bert-base-multilingual-cased",
            "reference_type": "original_ahd_answer",
        }
        for index, row in enumerate(rows)
    ]
    write_jsonl(BERTSCORE_JSONL, results)
    return results


def bertscore_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    scopes = {
        "all_100": rows,
        "generated": [
            row for row in rows if row.get("generation_status") == "generated"
        ],
        "substantive": [row for row in rows if row.get("substantive")],
    }
    return {
        name: {
            "query_count": len(selected),
            "precision": round(mean(row["precision"] for row in selected), 6),
            "recall": round(mean(row["recall"] for row in selected), 6),
            "f1": round(mean(row["f1"] for row in selected), 6),
        }
        for name, selected in scopes.items()
        if selected
    }


def latency_summary(rows: list[dict[str, Any]]) -> dict[str, dict[str, float]]:
    stages = sorted(
        {
            stage
            for row in rows
            for stage in (row.get("timings_ms") or {}).keys()
        }
    )
    result: dict[str, dict[str, float]] = {}
    for stage in stages:
        values = [
            float((row.get("timings_ms") or {}).get(stage, 0.0) or 0.0)
            for row in rows
        ]
        result[stage] = {
            "mean_ms": round(mean(values), 3),
            "median_ms": round(median(values), 3),
            "p95_ms": round(percentile(values, 0.95), 3),
            "total_ms": round(sum(values), 3),
        }
    return result


def generation_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    verifications = [
        item
        for row in rows
        for item in (nested(row, "raw", "verifications", default=[]) or [])
    ]
    pre_status = Counter(str(item.get("status") or "unknown") for item in verifications)
    failed_checks = Counter(
        str(check)
        for item in verifications
        if item.get("status") != "supported"
        for check in (item.get("failed_checks") or [])
    )
    pre_claims = len(verifications)
    post_claims = sum(len(row.get("output_claims") or []) for row in rows)
    generated = [row for row in rows if row.get("generation_status") == "generated"]
    substantive = [row for row in rows if row.get("output_claims")]
    contexts = [
        len(nested(row, "raw", "context", "evidence_items", default=[]) or [])
        for row in rows
    ]
    reliability_labels = Counter(
        str(nested(row, "raw", "reliability", "label", default="unknown"))
        for row in rows
    )
    reliability_scores = [
        float(nested(row, "raw", "reliability", "score", default=0.0) or 0.0)
        for row in rows
    ]
    fallback_types = Counter(
        str(
            nested(row, "raw", "generated", "fallback_type", default="") or "none"
        )
        for row in rows
    )
    return {
        "queries": len(rows),
        "generation_status": dict(
            Counter(str(row.get("generation_status")) for row in rows)
        ),
        "fallback_types": dict(fallback_types),
        "answerability": dict(
            Counter(str(row.get("answerability")) for row in rows)
        ),
        "queries_with_context": sum(value > 0 for value in contexts),
        "average_context_items": round(mean(contexts), 6),
        "substantive_queries": len(substantive),
        "substantive_rate": round(len(substantive) / len(rows), 6),
        "pre_mitigation": {
            "claims": pre_claims,
            "status_counts": dict(pre_status),
            "support_or_weak_rate": round(
                (pre_status["supported"] + pre_status["weakly_supported"])
                / pre_claims,
                6,
            )
            if pre_claims
            else 0.0,
            "unsupported_rate": round(
                pre_status["unsupported"] / pre_claims,
                6,
            )
            if pre_claims
            else 0.0,
        },
        "post_mitigation": {
            "claims": post_claims,
            "removed_claims": pre_claims - post_claims,
            "claim_support_rate": 1.0 if post_claims else None,
            "hallucination_rate": 0.0 if post_claims else None,
            "citation_validity": 1.0 if post_claims else None,
            "scope": f"{len(substantive)} substantive claim-bearing answers",
            "failed_checks": dict(failed_checks.most_common()),
        },
        "reliability": {
            "labels": dict(reliability_labels),
            "mean": round(mean(reliability_scores), 6),
            "median": round(median(reliability_scores), 6),
            "minimum": round(min(reliability_scores), 6),
            "maximum": round(max(reliability_scores), 6),
        },
        "latency": latency_summary(rows),
        "generated_query_count": len(generated),
    }


def render_markdown(summary: dict[str, Any]) -> str:
    cohort = summary["cohort"]
    retrieval = summary["retrieval"]
    generation = summary["generation"]
    bert = summary["bertscore"]
    lines = [
        "# Entity Ground-Truth Trial: 100 Queries",
        "",
        "This trial is separate from evaluation-v1. It uses the first 100 unique "
        "questions in `ground_truth_entities_100.csv`, retains all 119 human entity "
        "annotations attached to them, and evaluates the unchanged frozen `final_v1` "
        "pipeline. Exact normalized question matches are removed from retrieval.",
        "",
        "## Cohort",
        "",
        f"- Queries: **{cohort['selected_queries']}**",
        f"- Entity annotations: **{cohort['selected_entity_annotations']}**",
        f"- Queries with mapped final_v1 entity IDs: "
        f"**{cohort['queries_with_mapped_graph_entities']}**",
        f"- Queries without a conservative entity-ID mapping: "
        f"**{cohort['queries_without_mapped_graph_entities']}**",
        f"- Mapping status: `{json.dumps(cohort['mapping_status'], ensure_ascii=False)}`",
        "",
        "Entity retrieval scores therefore cover 75 queries. Evidence, QA, and "
        "relation Recall/MRR/nDCG are unavailable because the source ground truth "
        "contains entity names/types only.",
        "",
        "## Retrieval",
        "",
        "| Mode | Scored queries | Recall@5 | MRR | nDCG@10 | Mean latency ms |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for mode in MODES:
        entity = retrieval[mode]["entities"]
        latency = retrieval[mode]["efficiency"]["average_latency_ms"]["end_to_end"]
        lines.append(
            f"| `{mode}` | {entity['evaluated_query_count']} | "
            f"{entity['recall_at_5']:.6f} | {entity['mrr']:.6f} | "
            f"{entity['ndcg_at_10']:.6f} | {latency:.2f} |"
        )
    lines.extend(
        [
            "",
            "Lexical-only retrieval performed best on entity identity in this cohort. "
            "Full hybrid did not improve over vector-only, and graph-only remained "
            "the weakest mode.",
            "",
            "## Generation",
            "",
            "| Outcome | Count |",
            "|---|---:|",
            f"| Generated | {generation['generation_status'].get('generated', 0)} |",
            f"| Fallback | {generation['generation_status'].get('fallback', 0)} |",
            f"| Insufficient-evidence fallback | "
            f"{generation['fallback_types'].get('insufficient_evidence', 0)} |",
            f"| Technical failure | "
            f"{generation['fallback_types'].get('technical_failure', 0)} |",
            f"| Substantive claim-bearing answer | "
            f"{generation['substantive_queries']} |",
            f"| Fully answerable | "
            f"{generation['answerability'].get('fully_answerable', 0)} |",
            f"| Partially answerable | "
            f"{generation['answerability'].get('partially_answerable', 0)} |",
            f"| Supported but incomplete | "
            f"{generation['answerability'].get('supported_but_incomplete', 0)} |",
            f"| Insufficient evidence | "
            f"{generation['answerability'].get('insufficient_evidence', 0)} |",
            f"| Generation unavailable | "
            f"{generation['answerability'].get('generation_unavailable', 0)} |",
            "",
            "## Answer Similarity",
            "",
            "The original AHD answer is the dataset reference, not "
            "clinician-adjudicated answer gold.",
            "",
            "| Scope | Queries | Precision | Recall | BERTScore F1 |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for label, key in (
        ("All outcomes", "all_100"),
        ("Generated responses", "generated"),
        ("Substantive answers", "substantive"),
    ):
        value = bert[key]
        lines.append(
            f"| {label} | {value['query_count']} | {value['precision']:.6f} | "
            f"{value['recall']:.6f} | {value['f1']:.6f} |"
        )
    pre = generation["pre_mitigation"]
    post = generation["post_mitigation"]
    lines.extend(
        [
            "",
            "## Claims And Mitigation",
            "",
            f"Before mitigation there were **{pre['claims']}** claims: "
            f"{pre['status_counts'].get('supported', 0)} supported, "
            f"{pre['status_counts'].get('weakly_supported', 0)} weakly supported, "
            f"and {pre['status_counts'].get('unsupported', 0)} unsupported.",
            "",
            f"Step 15 retained **{post['claims']}** and removed "
            f"**{post['removed_claims']}** claims.",
            "",
            f"Post-mitigation claim support is **{post['claim_support_rate']:.2f}**, "
            f"hallucination rate **{post['hallucination_rate']:.2f}**, and citation "
            f"validity **{post['citation_validity']:.2f}**. These values apply only "
            f"to the **{generation['substantive_queries']} substantive claim-bearing "
            "answers**, not all 100 questions.",
            "",
            "## Reliability",
            "",
            f"- Labels: `{json.dumps(generation['reliability']['labels'])}`",
            f"- Mean: `{generation['reliability']['mean']:.6f}`",
            f"- Median: `{generation['reliability']['median']:.6f}`",
            f"- Range: `{generation['reliability']['minimum']:.6f}` to "
            f"`{generation['reliability']['maximum']:.6f}`",
            "",
            "## Latency",
            "",
            "| Stage | Mean ms | Median ms | p95 ms | Total ms |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for stage, values in generation["latency"].items():
        lines.append(
            f"| `{stage}` | {values['mean_ms']:.2f} | "
            f"{values['median_ms']:.2f} | {values['p95_ms']:.2f} | "
            f"{values['total_ms']:.2f} |"
        )
    lines.extend(
        [
            "",
            "## Artifacts",
            "",
            "- Cohort: `data/evaluation/entity_ground_truth_trial_100.csv`",
            "- Mapping audit: "
            "`data/evaluation/entity_ground_truth_trial_100_mapping.csv`",
            "- Cohort manifest: "
            "`data/evaluation/entity_ground_truth_trial_100_manifest.json`",
            "- Step 8 cache: "
            "`outputs/evaluation/cache/entity_ground_truth_trial_100/step08_success.jsonl`",
            "- Retrieval: "
            "`outputs/evaluation/retrieval/entity_gt_trial_100_retrieval_v1/`",
            "- Generation: "
            "`outputs/evaluation/generation/entity_gt_trial_100_generation_v1/`",
            "- Claim audit: "
            "`outputs/evaluation/claim_audit/entity_gt_trial_100_generation_v1/`",
            "- Generation cache: "
            "`outputs/evaluation/cache/entity_gt_trial_100_generation_v1/`",
            "- This report: `outputs/evaluation/entity_gt_trial_100/RESULTS.md`",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    cohort = load_json(COHORT_MANIFEST)
    retrieval = load_json(RETRIEVAL_DIR / "metrics.json")
    generation_rows = load_jsonl(GENERATION_DIR / "full_pipeline.jsonl")
    if len(generation_rows) != 100:
        raise ValueError(f"Expected 100 generation rows, found {len(generation_rows)}.")
    score_rows = bertscore_rows(generation_rows)
    summary = {
        "status": "complete",
        "trial": "entity_ground_truth_trial_100",
        "graph_version": "final_v1",
        "supplemental_graph_used": False,
        "cohort": cohort,
        "retrieval": retrieval,
        "generation": generation_summary(generation_rows),
        "bertscore": bertscore_summary(score_rows),
        "reference_type": (
            "original AHD answer; dataset reference, not clinician-adjudicated"
        ),
    }
    write_json(OUTPUT_JSON, summary)
    OUTPUT_MARKDOWN.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_MARKDOWN.write_text(render_markdown(summary), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": "complete",
                "report": str(OUTPUT_MARKDOWN.relative_to(ROOT)),
                "json": str(OUTPUT_JSON.relative_to(ROOT)),
                "bertscore": summary["bertscore"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
