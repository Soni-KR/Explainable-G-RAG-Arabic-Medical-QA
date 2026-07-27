from __future__ import annotations

import csv
import itertools
import json
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GOLD_CSV = ROOT / "retrieval_gold_annotations_100.csv"
HYBRID_RELATIONS_CSV = ROOT / "outputs/05_trial_graph_v1/hybrid_retrieval/trial_graph_v1_hybrid_retrieval_relations.csv"
OUT_DIR = ROOT / "outputs/05_trial_graph_v1/evaluation/retrieval_gold100_tuning"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def split_ids(value: str) -> set[str]:
    return {part.strip() for part in str(value or "").split("|") if part.strip()}


def to_float(row: dict, key: str) -> float:
    try:
        return float(row.get(key) or 0)
    except ValueError:
        return 0.0


def is_relevant(row: dict, gold: dict) -> bool:
    entities = split_ids(gold.get("gold_entity_ids", ""))
    qa_ids = split_ids(gold.get("gold_qa_ids", ""))
    rel_ids = split_ids(gold.get("gold_relation_ids", ""))
    return bool(
        entities & {row.get("source_entity_id", ""), row.get("target_entity_id", "")}
        or qa_ids & {row.get("qa_id", "")}
        or rel_ids & {row.get("edge_id", ""), row.get("original_relation_id", "")}
    )


def score_row(row: dict, weights: dict) -> float:
    seed_source = row.get("seed_source", "")
    seed_penalty = {
        "semantic_top_entity_fallback": -0.18,
        "family_equivalent": -0.05,
        "semantic_candidate": -0.02,
        "semantic_qa_evidence": 0.08,
    }.get(seed_source, 0.0)
    reviewed_bonus = 0.08 if str(row.get("edge_id", "")).startswith(("target_rel_", "focus_rel_", "supp_rel_", "exact_rel_")) else 0.0
    return (
        weights["confidence"] * to_float(row, "relation_confidence")
        + weights["seed"] * to_float(row, "seed_score")
        + weights["relation"] * to_float(row, "relation_weight")
        + weights["semantic"] * to_float(row, "semantic_support")
        + weights["evidence"] * to_float(row, "evidence_relevance")
        + weights["direction"] * to_float(row, "direction_bonus")
        + seed_penalty
        + reviewed_bonus
    )


def evaluate(rows_by_query: dict[str, list[dict]], gold_rows: list[dict], weights: dict) -> dict:
    mrr = []
    hits = {1: 0, 3: 0, 5: 0, 10: 0}
    for gold in gold_rows:
        rows = sorted(rows_by_query.get(gold["query_id"], []), key=lambda row: score_row(row, weights), reverse=True)
        first = 0
        rels = []
        for idx, row in enumerate(rows, start=1):
            relevant = is_relevant(row, gold)
            rels.append(relevant)
            if relevant and not first:
                first = idx
        mrr.append(1 / first if first else 0.0)
        for k in hits:
            hits[k] += int(any(rels[:k]))
    n = len(gold_rows)
    return {
        **weights,
        "mean_mrr": round(sum(mrr) / n, 6),
        "hit_at_1": round(hits[1] / n, 6),
        "hit_at_3": round(hits[3] / n, 6),
        "hit_at_5": round(hits[5] / n, 6),
        "hit_at_10": round(hits[10] / n, 6),
    }


def main() -> None:
    gold_rows = read_csv(GOLD_CSV)
    rows = read_csv(HYBRID_RELATIONS_CSV)
    rows_by_query = defaultdict(list)
    for row in rows:
        rows_by_query[row["query_id"]].append(row)

    grid = []
    for confidence, seed, relation, semantic, evidence, direction in itertools.product(
        [0.05, 0.10, 0.18],
        [0.05, 0.12, 0.20],
        [0.05, 0.12, 0.20],
        [0.08, 0.16, 0.24],
        [0.15, 0.30, 0.45, 0.60],
        [0.02, 0.05],
    ):
        total = confidence + seed + relation + semantic + evidence + direction
        grid.append(
            {
                "confidence": confidence / total,
                "seed": seed / total,
                "relation": relation / total,
                "semantic": semantic / total,
                "evidence": evidence / total,
                "direction": direction / total,
            }
        )
    baseline = {
        "confidence": 0.33,
        "seed": 0.24,
        "relation": 0.25,
        "semantic": 0.12,
        "evidence": 0.06,
        "direction": 1.0,
    }
    results = [evaluate(rows_by_query, gold_rows, weights) for weights in grid]
    results.append({"experiment": "baseline_current_components", **evaluate(rows_by_query, gold_rows, baseline)})
    results.sort(key=lambda row: (row["mean_mrr"], row["hit_at_5"], row["hit_at_10"]), reverse=True)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with (OUT_DIR / "hybrid_weight_search.csv").open("w", encoding="utf-8-sig", newline="") as f:
        fieldnames = sorted({key for row in results for key in row.keys()})
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(results)
    (OUT_DIR / "hybrid_weight_search_top20.json").write_text(
        json.dumps(results[:20], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(results[:10], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
