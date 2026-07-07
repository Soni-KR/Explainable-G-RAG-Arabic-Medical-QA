import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TRIAL_DIR = ROOT / "outputs" / "05_trial_graph_v1"
IMPORT_DIR = TRIAL_DIR / "import"
STEP8_DIR = TRIAL_DIR / "query_understanding"
STEP9A_DIR = TRIAL_DIR / "semantic_retrieval"
STEP9C_DIR = TRIAL_DIR / "hybrid_retrieval"
REPORT_MD = ROOT / "reports" / "trial_graph_v1_step9c_hybrid_retrieval_report.md"

ENTITIES_CSV = IMPORT_DIR / "trial_graph_v1_entities.csv"
RELATIONS_CSV = IMPORT_DIR / "trial_graph_v1_bidirectional_relations.csv"
QA_CSV = IMPORT_DIR / "trial_graph_v1_qa_sources.csv"
QUERY_UNDERSTANDING_JSON = STEP8_DIR / "trial_graph_v1_query_understanding.json"
SEMANTIC_RETRIEVAL_JSON = STEP9A_DIR / "trial_graph_v1_semantic_retrieval_results.json"

HYBRID_RESULTS_JSON = STEP9C_DIR / "trial_graph_v1_hybrid_retrieval_results.json"
HYBRID_RELATIONS_CSV = STEP9C_DIR / "trial_graph_v1_hybrid_retrieval_relations.csv"
HYBRID_CONTEXTS_CSV = STEP9C_DIR / "trial_graph_v1_hybrid_retrieval_contexts.csv"

DETECTED_SEED_SCORES = {"exact": 1.0, "alias": 0.82}
SEMANTIC_CANDIDATE_SEED_SCORE = 0.55
SEMANTIC_ENTITY_SEED_SCALE = 0.55
FAMILY_EQUIVALENT_SEED_SCALE = 0.85

ARABIC_NORMALIZATION_MAP = str.maketrans(
    {
        "أ": "ا",
        "إ": "ا",
        "آ": "ا",
        "ٱ": "ا",
        "ى": "ي",
        "ئ": "ي",
        "ؤ": "و",
        "ة": "ه",
    }
)

CANONICAL_FAMILY_OVERRIDES = {
    "بلغم": "بلغم",
    "البلغم": "بلغم",
    "مرض السكري": "مرض السكري",
    "السكري": "مرض السكري",
    "سكري": "مرض السكري",
    "داء السكري": "مرض السكري",
    "فقر الدم": "فقر الدم",
    "فقر دم": "فقر الدم",
    "انيميا": "فقر الدم",
    "أنيميا": "فقر الدم",
    "ضيق تنفس": "ضيق تنفس",
    "ضيق النفس": "ضيق تنفس",
}


def relpath(path):
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def write_csv(path, rows, fieldnames):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_arabic(text):
    return " ".join((text or "").translate(ARABIC_NORMALIZATION_MAP).split())


def canonical_family(name):
    if not name:
        return ""
    if name in CANONICAL_FAMILY_OVERRIDES:
        return CANONICAL_FAMILY_OVERRIDES[name]
    normalized = normalize_arabic(name)
    for variant, family in CANONICAL_FAMILY_OVERRIDES.items():
        if normalize_arabic(variant) == normalized:
            return family
    return normalized


def load_graph():
    entities = {row["entity_id"]: row for row in read_csv(ENTITIES_CSV)}
    qa_sources = {row["qa_id"]: row for row in read_csv(QA_CSV)}
    relations = read_csv(RELATIONS_CSV)
    by_source = defaultdict(list)
    by_edge = {}
    family_to_entities = defaultdict(list)
    for row in entities.values():
        family = canonical_family(row.get("canonical_name", ""))
        if family:
            family_to_entities[family].append(row)
    for row in relations:
        by_source[row.get("source_entity_id", "")].append(row)
        by_edge[row.get("edge_id", "")] = row
    return entities, qa_sources, relations, by_source, by_edge, family_to_entities


def semantic_index_for_query(semantic_result):
    entity_scores = {}
    evidence_scores_by_entity = defaultdict(float)
    evidence_scores_by_qa = defaultdict(float)
    qa_scores = {}
    top_docs = []
    for doc_type, rows in semantic_result.get("results_by_type", {}).items():
        for row in rows:
            score = float(row.get("final_score") or 0)
            top_docs.append({**row, "doc_type": doc_type})
            if doc_type == "entity" and row.get("entity_id"):
                entity_scores[row["entity_id"]] = max(entity_scores.get(row["entity_id"], 0), score)
            elif doc_type == "evidence":
                if row.get("entity_id"):
                    evidence_scores_by_entity[row["entity_id"]] = max(evidence_scores_by_entity[row["entity_id"]], score)
                if row.get("qa_id"):
                    evidence_scores_by_qa[row["qa_id"]] = max(evidence_scores_by_qa[row["qa_id"]], score)
            elif doc_type == "qa" and row.get("qa_id"):
                qa_scores[row["qa_id"]] = max(qa_scores.get(row["qa_id"], 0), score)
    return entity_scores, evidence_scores_by_entity, evidence_scores_by_qa, qa_scores, top_docs


def add_family_equivalent_seeds(seeds, family_to_entities):
    additions = {}
    for seed in list(seeds.values()):
        family = canonical_family(seed.get("canonical_name", ""))
        if not family:
            continue
        for entity in family_to_entities.get(family, []):
            entity_id = entity.get("entity_id")
            if not entity_id or entity_id in seeds or entity_id in additions:
                continue
            additions[entity_id] = {
                "entity_id": entity_id,
                "canonical_name": entity.get("canonical_name", ""),
                "entity_type": entity.get("entity_type", ""),
                "seed_source": "family_equivalent",
                "seed_score": round(float(seed.get("seed_score") or 0) * FAMILY_EQUIVALENT_SEED_SCALE, 6),
            }
    seeds.update(additions)
    return seeds


def build_seed_entities(query_record, semantic_result, family_to_entities):
    seeds = {}
    for entity in query_record.get("detected_entities", []):
        entity_id = entity.get("entity_id")
        if not entity_id:
            continue
        match_type = entity.get("match_type", "")
        score = DETECTED_SEED_SCORES.get(match_type, 0.7)
        seeds[entity_id] = {
            "entity_id": entity_id,
            "canonical_name": entity.get("canonical_name", ""),
            "entity_type": entity.get("entity_type", ""),
            "seed_source": f"detected_{match_type}",
            "seed_score": max(seeds.get(entity_id, {}).get("seed_score", 0), score),
        }
    for entity in query_record.get("semantic_candidate_entities", []):
        entity_id = entity.get("entity_id")
        if entity_id and entity_id not in seeds:
            seeds[entity_id] = {
                "entity_id": entity_id,
                "canonical_name": entity.get("canonical_name", ""),
                "entity_type": entity.get("entity_type", ""),
                "seed_source": "semantic_candidate",
            "seed_score": SEMANTIC_CANDIDATE_SEED_SCORE,
            }
    seeds = add_family_equivalent_seeds(seeds, family_to_entities)
    if not seeds:
        for row in semantic_result.get("results_by_type", {}).get("entity", [])[:5]:
            entity_id = row.get("entity_id")
            if not entity_id or entity_id in seeds:
                continue
            semantic_seed_score = min(float(row.get("final_score") or 0) * SEMANTIC_ENTITY_SEED_SCALE, 0.45)
            seeds[entity_id] = {
                "entity_id": entity_id,
                "canonical_name": row.get("title", ""),
                "entity_type": "",
                "seed_source": "semantic_top_entity_fallback",
                "seed_score": semantic_seed_score,
            }
    return seeds


def relation_weight(row, relation_type_weights, default_weight):
    return float(relation_type_weights.get(row.get("graph_relation_type", ""), default_weight))


def score_relation(row, seed, relation_type_weights, default_weight, entity_scores, evidence_scores_by_entity, evidence_scores_by_qa, qa_scores):
    confidence = float(row.get("confidence") or 0)
    seed_score = float(seed.get("seed_score") or 0)
    rel_weight = relation_weight(row, relation_type_weights, default_weight)
    target_semantic = entity_scores.get(row.get("target_entity_id", ""), 0)
    source_semantic = entity_scores.get(row.get("source_entity_id", ""), 0)
    evidence_semantic = max(
        evidence_scores_by_entity.get(row.get("source_entity_id", ""), 0),
        evidence_scores_by_entity.get(row.get("target_entity_id", ""), 0),
        evidence_scores_by_qa.get(row.get("qa_id", ""), 0),
        qa_scores.get(row.get("qa_id", ""), 0),
    )
    semantic_support = max(target_semantic, source_semantic, evidence_semantic)
    direction_bonus = 0.04 if row.get("edge_direction") == "direct" else 0.0
    final_score = (
        0.35 * confidence
        + 0.25 * seed_score
        + 0.25 * rel_weight
        + 0.12 * semantic_support
        + direction_bonus
    )
    return {
        "hybrid_score": round(final_score, 6),
        "relation_confidence": round(confidence, 6),
        "seed_score": round(seed_score, 6),
        "relation_weight": round(rel_weight, 6),
        "semantic_support": round(semantic_support, 6),
        "direction_bonus": round(direction_bonus, 6),
    }


def traverse_and_rank(query_record, semantic_result, by_source, family_to_entities):
    entity_scores, evidence_scores_by_entity, evidence_scores_by_qa, qa_scores, top_docs = semantic_index_for_query(semantic_result)
    seeds = build_seed_entities(query_record, semantic_result, family_to_entities)
    graph_plan = query_record.get("retrieval_plan", {}).get("graph_expansion", {})
    relation_type_weights = graph_plan.get("relation_type_weights", {})
    default_weight = float(graph_plan.get("default_relation_weight", -0.2))

    relation_rows = []
    seen_edges = set()
    for seed_id, seed in seeds.items():
        for row in by_source.get(seed_id, []):
            edge_id = row.get("edge_id", "")
            if edge_id in seen_edges:
                continue
            seen_edges.add(edge_id)
            score_parts = score_relation(
                row,
                seed,
                relation_type_weights,
                default_weight,
                entity_scores,
                evidence_scores_by_entity,
                evidence_scores_by_qa,
                qa_scores,
            )
            relation_rows.append(
                {
                    "query_id": query_record["query_id"],
                    "query": query_record["query"],
                    "seed_entity_id": seed_id,
                    "seed_entity_name": seed.get("canonical_name", ""),
                    "seed_source": seed.get("seed_source", ""),
                    **score_parts,
                    **row,
                }
            )
    relation_rows.sort(key=lambda item: item["hybrid_score"], reverse=True)
    return relation_rows, top_docs, seeds


def build_contexts(query_record, relation_rows, semantic_result, qa_sources, limit):
    contexts = []
    seen = set()
    for rank, row in enumerate(relation_rows[:limit], start=1):
        key = ("relation", row.get("edge_id", ""))
        if key in seen:
            continue
        seen.add(key)
        qa = qa_sources.get(row.get("qa_id", ""), {})
        contexts.append(
            {
                "query_id": query_record["query_id"],
                "query": query_record["query"],
                "context_rank": len(contexts) + 1,
                "context_type": "graph_relation",
                "score": row["hybrid_score"],
                "source_id": row.get("edge_id", ""),
                "relation": f"{row.get('source_name', '')} {row.get('graph_relation_type', '')} {row.get('target_name', '')}",
                "evidence": row.get("evidence", ""),
                "qa_id": row.get("qa_id", ""),
                "question": qa.get("question", ""),
                "answer": qa.get("answer", ""),
            }
        )
    semantic_contexts = []
    for doc_type in ["evidence", "qa"]:
        for row in semantic_result.get("results_by_type", {}).get(doc_type, [])[:limit]:
            key = (doc_type, row.get("doc_id", ""))
            if key in seen:
                continue
            seen.add(key)
            semantic_contexts.append(
                {
                    "query_id": query_record["query_id"],
                    "query": query_record["query"],
                    "context_rank": 0,
                    "context_type": f"semantic_{doc_type}",
                    "score": float(row.get("final_score") or 0),
                    "source_id": row.get("doc_id", ""),
                    "relation": "",
                    "evidence": row.get("title", ""),
                    "qa_id": row.get("qa_id", ""),
                    "question": "",
                    "answer": "",
                }
            )
    semantic_contexts.sort(key=lambda item: item["score"], reverse=True)
    contexts.extend(semantic_contexts[: max(0, limit - len(contexts))])
    for index, item in enumerate(contexts, start=1):
        item["context_rank"] = index
    return contexts[:limit]


def write_report(results):
    lines = [
        "# Trial Graph v1 Step 9C Hybrid Retrieval Report",
        "",
        "This combines Step 8 query understanding, Step 9A semantic retrieval, and graph traversal over the frozen bidirectional relation graph.",
        "",
        "## Scoring",
        "",
        "- Relation confidence from Step 4 validation",
        "- Seed strength from Step 8 hard detections and soft candidates",
        "- Intent-specific relation weights from Step 8",
        "- Semantic support from Step 9A entity/evidence/QA retrieval",
        "- Small bonus for original/direct graph edges",
        "- Query-time family-equivalent seeds for known duplicate families such as `سكري` / `مرض السكري`",
        "",
        "## Query Results",
        "",
    ]
    for result in results:
        lines.extend([f"### {result['query']}", ""])
        for warning in result.get("warnings", []):
            lines.append(f"- Warning: {warning}")
        if result.get("warnings"):
            lines.append("")
        lines.append("**Top hybrid graph relations**")
        for row in result.get("top_relations", [])[:8]:
            lines.append(
                f"- `{row['hybrid_score']}` {row['source_name']} --{row['graph_relation_type']}--> {row['target_name']} "
                f"(seed={row['seed_entity_name']}, relation_weight={row['relation_weight']})"
            )
        lines.extend(["", "**Top context bundle**"])
        for row in result.get("contexts", [])[:6]:
            label = row["relation"] if row["relation"] else row["evidence"]
            lines.append(f"- `{row['context_type']}` `{row['score']}` {label}")
        lines.append("")
    lines.extend(
        [
            "## Output Files",
            "",
            f"- Hybrid retrieval JSON: `{relpath(HYBRID_RESULTS_JSON)}`",
            f"- Hybrid relations CSV: `{relpath(HYBRID_RELATIONS_CSV)}`",
            f"- Hybrid contexts CSV: `{relpath(HYBRID_CONTEXTS_CSV)}`",
            "",
            "## Next Step From Mix.png",
            "",
            "Continue to Step 10: subgraph reranking, using these hybrid relation/context candidates.",
        ]
    )
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--top-relations", type=int, default=20)
    parser.add_argument("--top-contexts", type=int, default=10)
    args = parser.parse_args()

    STEP9C_DIR.mkdir(parents=True, exist_ok=True)
    _, qa_sources, _, by_source, _, family_to_entities = load_graph()
    query_records = {row["query_id"]: row for row in load_json(QUERY_UNDERSTANDING_JSON)}
    semantic_results = load_json(SEMANTIC_RETRIEVAL_JSON)

    all_relation_rows = []
    all_context_rows = []
    results = []
    for semantic_result in semantic_results:
        query_record = query_records[semantic_result["query_id"]]
        relation_rows, _, seeds = traverse_and_rank(query_record, semantic_result, by_source, family_to_entities)
        contexts = build_contexts(query_record, relation_rows, semantic_result, qa_sources, args.top_contexts)
        top_relations = relation_rows[: args.top_relations]
        all_relation_rows.extend(top_relations)
        all_context_rows.extend(contexts)
        results.append(
            {
                "query_id": query_record["query_id"],
                "query": query_record["query"],
                "warnings": query_record.get("warnings", []),
                "seed_entities": list(seeds.values()),
                "top_relations": top_relations,
                "contexts": contexts,
            }
        )

    HYBRID_RESULTS_JSON.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    write_csv(
        HYBRID_RELATIONS_CSV,
        all_relation_rows,
        [
            "query_id",
            "query",
            "hybrid_score",
            "relation_confidence",
            "seed_score",
            "relation_weight",
            "semantic_support",
            "direction_bonus",
            "seed_entity_id",
            "seed_entity_name",
            "seed_source",
            "edge_id",
            "original_relation_id",
            "edge_direction",
            "graph_relation_type",
            "source_entity_id",
            "source_name",
            "source_type",
            "target_entity_id",
            "target_name",
            "target_type",
            "qa_id",
            "evidence",
            "reason",
        ],
    )
    write_csv(
        HYBRID_CONTEXTS_CSV,
        all_context_rows,
        ["query_id", "query", "context_rank", "context_type", "score", "source_id", "relation", "evidence", "qa_id", "question", "answer"],
    )
    write_report(results)
    print(
        json.dumps(
            {
                "queries": len(results),
                "hybrid_retrieval_json": relpath(HYBRID_RESULTS_JSON),
                "hybrid_relations_csv": relpath(HYBRID_RELATIONS_CSV),
                "hybrid_contexts_csv": relpath(HYBRID_CONTEXTS_CSV),
                "report_md": relpath(REPORT_MD),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
