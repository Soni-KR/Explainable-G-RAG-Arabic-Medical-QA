import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TRIAL_DIR = ROOT / "outputs" / "05_trial_graph_v1"
RELATIONS_CSV = TRIAL_DIR / "import" / "trial_graph_v1_bidirectional_relations.csv"
RESULTS_CSV = TRIAL_DIR / "trial_graph_v1_retrieval_smoke_results.csv"
REPORT_MD = ROOT / "reports" / "trial_graph_v1_retrieval_smoke_report.md"


SMOKE_QUERIES = [
    {
        "query_id": "q01_allergy_treatments",
        "description": "Treatments connected to حساسية",
        "entity": "حساسية",
        "entity_side": "source",
        "relation_types": {"TREATED_BY"},
        "expected_any": {"مضاد الهيستامين", "نازونكس", "كورتيزون"},
    },
    {
        "query_id": "q02_allergy_symptoms",
        "description": "Symptoms connected to حساسية",
        "entity": "حساسية",
        "entity_side": "source",
        "relation_types": {"HAS_SYMPTOM"},
        "expected_any": {"سعال", "بلغم"},
    },
    {
        "query_id": "q03_allergy_tests",
        "description": "Tests connected to حساسية",
        "entity": "حساسية",
        "entity_side": "source",
        "relation_types": {"DIAGNOSED_BY", "INVESTIGATED_BY"},
        "expected_any": {"تحليل الحساسية", "RAST Test", "تحاليل مخبرية"},
    },
    {
        "query_id": "q04_anemia_tests",
        "description": "Tests connected to فقر الدم",
        "entity": "فقر الدم",
        "entity_side": "source",
        "relation_types": {"DIAGNOSED_BY", "INVESTIGATED_BY"},
        "expected_any": {"تحاليل مخبرية", "تحليل مخبري"},
    },
    {
        "query_id": "q05_headache_diseases",
        "description": "Diseases connected to صداع",
        "entity": "صداع",
        "entity_side": "source",
        "relation_types": {"SYMPTOM_OF"},
        "expected_any": set(),
    },
    {
        "query_id": "q06_stroke_treatments",
        "description": "Treatments connected to الجلطة الدماغية",
        "entity": "الجلطة الدماغية",
        "entity_side": "source",
        "relation_types": {"TREATED_BY"},
        "expected_any": set(),
    },
    {
        "query_id": "q07_arthritis_symptoms",
        "description": "Symptoms connected to التهاب المفاصل",
        "entity": "التهاب المفاصل",
        "entity_side": "source",
        "relation_types": {"HAS_SYMPTOM"},
        "expected_any": {"ألم المفاصل"},
    },
]


def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def write_csv(path, rows, fieldnames):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def relpath(path):
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def match_query(row, query):
    relation = row.get("graph_relation_type", "")
    if relation not in query["relation_types"]:
        return False
    if query["entity_side"] == "source":
        return row.get("source_name") == query["entity"]
    if query["entity_side"] == "target":
        return row.get("target_name") == query["entity"]
    return row.get("source_name") == query["entity"] or row.get("target_name") == query["entity"]


def neighbor_name(row, query):
    if row.get("source_name") == query["entity"]:
        return row.get("target_name", "")
    return row.get("source_name", "")


def main():
    relations = read_csv(RELATIONS_CSV)
    result_rows = []
    summary = []

    for query in SMOKE_QUERIES:
        matches = [row for row in relations if match_query(row, query)]
        matches.sort(key=lambda row: float(row.get("confidence") or 0), reverse=True)
        returned_neighbors = {neighbor_name(row, query) for row in matches}
        expected_hits = sorted(query["expected_any"] & returned_neighbors)

        summary.append(
            {
                "query_id": query["query_id"],
                "description": query["description"],
                "result_count": len(matches),
                "expected_hits": expected_hits,
                "status": "ok" if matches and (not query["expected_any"] or expected_hits) else "needs_review",
            }
        )

        for rank, row in enumerate(matches[:20], start=1):
            result_rows.append(
                {
                    "query_id": query["query_id"],
                    "description": query["description"],
                    "rank": rank,
                    "query_entity": query["entity"],
                    "graph_relation_type": row.get("graph_relation_type", ""),
                    "neighbor_name": neighbor_name(row, query),
                    "neighbor_type": row.get("target_type", "") if row.get("source_name") == query["entity"] else row.get("source_type", ""),
                    "confidence": row.get("confidence", ""),
                    "edge_direction": row.get("edge_direction", ""),
                    "original_relation_id": row.get("original_relation_id", ""),
                    "qa_id": row.get("qa_id", ""),
                    "evidence": row.get("evidence", ""),
                }
            )

    fields = [
        "query_id",
        "description",
        "rank",
        "query_entity",
        "graph_relation_type",
        "neighbor_name",
        "neighbor_type",
        "confidence",
        "edge_direction",
        "original_relation_id",
        "qa_id",
        "evidence",
    ]
    write_csv(RESULTS_CSV, result_rows, fields)

    lines = [
        "# Trial Graph v1 Retrieval Smoke Report",
        "",
        "This tests graph retrieval over the frozen CSV export before Neo4j answer generation.",
        "",
        "## Summary",
        "",
    ]
    for item in summary:
        hits = ", ".join(item["expected_hits"]) if item["expected_hits"] else "none checked/found"
        lines.append(
            f"- {item['query_id']} `{item['status']}`: {item['description']} -> {item['result_count']} results; expected hits: {hits}"
        )
    lines.extend(
        [
            "",
            "## Output",
            "",
            f"- Retrieval smoke results: `{relpath(RESULTS_CSV)}`",
            "",
            "## Notes",
            "",
            "- `needs_review` can mean the graph lacks that concept in this small trial, not necessarily that the pipeline is broken.",
            "- Use this before scaling Step 3/Step 4 to decide whether relation types and directions are useful.",
        ]
    )
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(
        json.dumps(
            {
                "queries": len(SMOKE_QUERIES),
                "result_rows": len(result_rows),
                "needs_review": [item["query_id"] for item in summary if item["status"] == "needs_review"],
                "results_csv": relpath(RESULTS_CSV),
                "report_md": relpath(REPORT_MD),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
