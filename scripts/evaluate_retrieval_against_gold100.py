from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GOLD_CSV = ROOT / "retrieval_gold_annotations_100.csv"
HYBRID_RELATIONS_CSV = ROOT / "outputs/05_trial_graph_v1/hybrid_retrieval/trial_graph_v1_hybrid_retrieval_relations.csv"
CONTEXTS_CSV = ROOT / "outputs/05_trial_graph_v1/context_construction/trial_graph_v1_context_bundles.csv"
RERANKED_RELATIONS_CSV = ROOT / "outputs/05_trial_graph_v1/subgraph_reranking/trial_graph_v1_reranked_relations.csv"
OUT_DIR = ROOT / "outputs/05_trial_graph_v1/evaluation/retrieval_gold100"


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def split_ids(value: str) -> set[str]:
    return {item.strip() for item in str(value or "").split("|") if item.strip()}


def dcg(values: list[int]) -> float:
    import math

    return sum(value / math.log2(index + 2) for index, value in enumerate(values))


def metrics_for(rows: list[dict], gold: dict, k_values=(1, 3, 5, 10)) -> dict:
    gold_entities = split_ids(gold.get("gold_entity_ids", ""))
    gold_qa = split_ids(gold.get("gold_qa_ids", ""))
    gold_rel = split_ids(gold.get("gold_relation_ids", ""))
    has_gold = bool(gold_entities or gold_qa or gold_rel)

    relevances = []
    first_rank = None
    for idx, row in enumerate(rows, start=1):
        row_entities = {row.get("source_entity_id", ""), row.get("target_entity_id", "")}
        row_qa = {row.get("qa_id", "")}
        row_rel = {row.get("edge_id", ""), row.get("original_relation_id", "")}
        relevant = bool(
            (gold_entities & row_entities)
            or (gold_qa & row_qa)
            or (gold_rel & row_rel)
        )
        relevances.append(1 if relevant else 0)
        if relevant and first_rank is None:
            first_rank = idx

    out = {
        "has_gold": has_gold,
        "retrieved": len(rows),
        "first_relevant_rank": first_rank or 0,
        "mrr": round(1 / first_rank, 6) if first_rank else 0.0,
    }
    for k in k_values:
        out[f"hit_at_{k}"] = int(any(relevances[:k]))
        out[f"relevant_count_at_{k}"] = sum(relevances[:k])
    ideal = dcg([1] * min(sum(relevances), 10))
    out["ndcg_at_10"] = round(dcg(relevances[:10]) / ideal, 6) if ideal else 0.0
    return out


def evaluate_file(rows: list[dict], name: str, rank_field: str = "") -> tuple[list[dict], dict]:
    gold_rows = read_csv(GOLD_CSV)
    by_query = {}
    for row in rows:
        by_query.setdefault(row.get("query_id", ""), []).append(row)
    if rank_field:
        for query_rows in by_query.values():
            query_rows.sort(key=lambda row: float(row.get(rank_field) or 0))
    result_rows = []
    for gold in gold_rows:
        query_id = gold["query_id"]
        metrics = metrics_for(by_query.get(query_id, []), gold)
        result_rows.append(
            {
                "query_id": query_id,
                "answerable_from_final_graph": gold.get("answerable_from_final_graph", ""),
                **metrics,
            }
        )
    summary = {
        "name": name,
        "queries": len(result_rows),
        "mean_mrr": round(sum(row["mrr"] for row in result_rows) / len(result_rows), 6),
        "hit_at_1": round(sum(row["hit_at_1"] for row in result_rows) / len(result_rows), 6),
        "hit_at_3": round(sum(row["hit_at_3"] for row in result_rows) / len(result_rows), 6),
        "hit_at_5": round(sum(row["hit_at_5"] for row in result_rows) / len(result_rows), 6),
        "hit_at_10": round(sum(row["hit_at_10"] for row in result_rows) / len(result_rows), 6),
        "mean_ndcg_at_10": round(sum(row["ndcg_at_10"] for row in result_rows) / len(result_rows), 6),
    }
    return result_rows, summary


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    experiments = [
        ("hybrid_relations", read_csv(HYBRID_RELATIONS_CSV), ""),
        ("reranked_relations", read_csv(RERANKED_RELATIONS_CSV), "subgraph_rank"),
    ]
    summaries = []
    for name, rows, rank_field in experiments:
        result_rows, summary = evaluate_file(rows, name, rank_field)
        write_csv(OUT_DIR / f"{name}.csv", result_rows)
        summaries.append(summary)
    write_csv(OUT_DIR / "summary.csv", summaries)
    (OUT_DIR / "summary.json").write_text(json.dumps(summaries, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summaries, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
