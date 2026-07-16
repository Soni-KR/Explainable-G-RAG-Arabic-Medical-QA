import argparse
import csv
import json
import re
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TRIAL_DIR = ROOT / "outputs" / "05_trial_graph_v1"
IMPORT_DIR = TRIAL_DIR / "import"
SUPPLEMENTAL_DIR = TRIAL_DIR / "supplemental_facts"
STEP8_DIR = TRIAL_DIR / "query_understanding"
STEP9A_DIR = TRIAL_DIR / "semantic_retrieval"
STEP9C_DIR = TRIAL_DIR / "hybrid_retrieval"
REPORT_MD = ROOT / "reports" / "trial_graph_v1_step9c_hybrid_retrieval_report.md"

ENTITIES_CSV = IMPORT_DIR / "trial_graph_v1_entities.csv"
RELATIONS_CSV = IMPORT_DIR / "trial_graph_v1_bidirectional_relations.csv"
QA_CSV = IMPORT_DIR / "trial_graph_v1_qa_sources.csv"
SUPPLEMENTAL_ENTITIES_CSV = SUPPLEMENTAL_DIR / "trial_graph_v1_supplemental_entities.csv"
SUPPLEMENTAL_RELATIONS_CSV = SUPPLEMENTAL_DIR / "trial_graph_v1_supplemental_relations.csv"
SUPPLEMENTAL_QA_CSV = SUPPLEMENTAL_DIR / "trial_graph_v1_supplemental_qa_sources.csv"
QUERY_UNDERSTANDING_JSON = STEP8_DIR / "trial_graph_v1_query_understanding.json"
SEMANTIC_RETRIEVAL_JSON = STEP9A_DIR / "trial_graph_v1_semantic_retrieval_results.json"

HYBRID_RESULTS_JSON = STEP9C_DIR / "trial_graph_v1_hybrid_retrieval_results.json"
HYBRID_RELATIONS_CSV = STEP9C_DIR / "trial_graph_v1_hybrid_retrieval_relations.csv"
HYBRID_CONTEXTS_CSV = STEP9C_DIR / "trial_graph_v1_hybrid_retrieval_contexts.csv"
HYBRID_METRICS_JSON = STEP9C_DIR / "trial_graph_v1_hybrid_retrieval_metrics.json"
HYBRID_METRICS_CSV = STEP9C_DIR / "trial_graph_v1_hybrid_retrieval_metrics.csv"

DETECTED_SEED_SCORES = {"exact": 1.0, "alias": 0.82}
SEMANTIC_CANDIDATE_SEED_SCORE = 0.55
SEMANTIC_ENTITY_SEED_SCALE = 0.55
FAMILY_EQUIVALENT_SEED_SCALE = 0.85
TOKEN_RE = re.compile(r"[\w\u0600-\u06ff]+", re.UNICODE)

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
    if not path.exists():
        return []
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


def tokenize(text):
    return set(TOKEN_RE.findall(normalize_arabic(text)))


def query_terms(query_record):
    parts = [
        query_record.get("query", ""),
        query_record.get("normalized_query", ""),
        " ".join(query_record.get("expanded_terms", [])),
    ]
    parts.extend(entity.get("canonical_name", "") for entity in query_record.get("detected_entities", []))
    return tokenize(" ".join(parts))


def lexical_overlap_score(query_tokens, *texts):
    if not query_tokens:
        return 0.0
    doc_tokens = tokenize(" ".join(text or "" for text in texts))
    if not doc_tokens:
        return 0.0
    return len(query_tokens & doc_tokens) / len(query_tokens)


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
    entities = {row["entity_id"]: row for row in read_csv(ENTITIES_CSV) + read_csv(SUPPLEMENTAL_ENTITIES_CSV)}
    qa_sources = {row["qa_id"]: row for row in read_csv(QA_CSV) + read_csv(SUPPLEMENTAL_QA_CSV)}
    relations = read_csv(RELATIONS_CSV) + read_csv(SUPPLEMENTAL_RELATIONS_CSV)
    by_source = defaultdict(list)
    by_qa = defaultdict(list)
    by_edge = {}
    family_to_entities = defaultdict(list)
    for row in entities.values():
        family = canonical_family(row.get("canonical_name", ""))
        if family:
            family_to_entities[family].append(row)
    for row in relations:
        by_source[row.get("source_entity_id", "")].append(row)
        if row.get("qa_id"):
            by_qa[row.get("qa_id", "")].append(row)
        by_edge[row.get("edge_id", "")] = row
    return entities, qa_sources, relations, by_source, by_qa, by_edge, family_to_entities


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


def score_relation(row, seed, relation_type_weights, default_weight, entity_scores, evidence_scores_by_entity, evidence_scores_by_qa, qa_scores, query_tokens, qa_sources):
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
    qa = qa_sources.get(row.get("qa_id", ""), {})
    evidence_relevance = lexical_overlap_score(
        query_tokens,
        row.get("evidence", ""),
        row.get("source_name", ""),
        row.get("target_name", ""),
        qa.get("question", ""),
        qa.get("answer", ""),
    )
    direction_bonus = 0.04 if row.get("edge_direction") == "direct" else 0.0
    final_score = (
        0.33 * confidence
        + 0.24 * seed_score
        + 0.25 * rel_weight
        + 0.12 * semantic_support
        + 0.06 * evidence_relevance
        + direction_bonus
    )
    return {
        "hybrid_score": round(final_score, 6),
        "relation_confidence": round(confidence, 6),
        "seed_score": round(seed_score, 6),
        "relation_weight": round(rel_weight, 6),
        "semantic_support": round(semantic_support, 6),
        "evidence_relevance": round(evidence_relevance, 6),
        "direction_bonus": round(direction_bonus, 6),
    }


def top_semantic_qa_ids(evidence_scores_by_qa, qa_scores, limit=8):
    scores = defaultdict(float)
    for qa_id, score in evidence_scores_by_qa.items():
        scores[qa_id] = max(scores[qa_id], score)
    for qa_id, score in qa_scores.items():
        scores[qa_id] = max(scores[qa_id], score)
    return [qa_id for qa_id, _ in sorted(scores.items(), key=lambda item: item[1], reverse=True)[:limit]]


def traverse_and_rank(query_record, semantic_result, by_source, by_qa, family_to_entities, qa_sources):
    entity_scores, evidence_scores_by_entity, evidence_scores_by_qa, qa_scores, top_docs = semantic_index_for_query(semantic_result)
    seeds = build_seed_entities(query_record, semantic_result, family_to_entities)
    tokens = query_terms(query_record)
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
                tokens,
                qa_sources,
            )
            relation_rows.append(
                {
                    "query_id": query_record["query_id"],
                    "query": query_record["query"],
                    "seed_entity_id": seed_id,
                    "seed_entity_name": seed.get("canonical_name", ""),
                    "seed_source": seed.get("seed_source", ""),
                    "expansion_source": "seed_entity_traversal",
                    **score_parts,
                    **row,
                }
            )
    for qa_id in top_semantic_qa_ids(evidence_scores_by_qa, qa_scores):
        for row in by_qa.get(qa_id, []):
            edge_id = row.get("edge_id", "")
            if edge_id in seen_edges:
                continue
            seen_edges.add(edge_id)
            pseudo_seed = {
                "seed_score": 0.45,
                "canonical_name": row.get("source_name", ""),
            }
            score_parts = score_relation(
                row,
                pseudo_seed,
                relation_type_weights,
                default_weight,
                entity_scores,
                evidence_scores_by_entity,
                evidence_scores_by_qa,
                qa_scores,
                tokens,
                qa_sources,
            )
            relation_rows.append(
                {
                    "query_id": query_record["query_id"],
                    "query": query_record["query"],
                    "seed_entity_id": row.get("source_entity_id", ""),
                    "seed_entity_name": row.get("source_name", ""),
                    "seed_source": "semantic_qa_evidence",
                    "expansion_source": "semantic_qa_relation_expansion",
                    **score_parts,
                    **row,
                }
            )
    relation_rows.sort(key=lambda item: item["hybrid_score"], reverse=True)
    return relation_rows, top_docs, seeds


def build_contexts(query_record, relation_rows, semantic_result, qa_sources, limit):
    contexts = []
    seen = set()
    query_tokens = query_terms(query_record)
    for rank, row in enumerate(relation_rows[: limit * 2], start=1):
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
                "evidence_relevance": row.get("evidence_relevance", ""),
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
            qa = qa_sources.get(row.get("qa_id", ""), {})
            evidence_text = row.get("text_preview", "") or row.get("title", "")
            relevance = lexical_overlap_score(query_tokens, evidence_text, qa.get("question", ""), qa.get("answer", ""))
            semantic_contexts.append(
                {
                    "query_id": query_record["query_id"],
                    "query": query_record["query"],
                    "context_rank": 0,
                    "context_type": f"semantic_{doc_type}",
                    "score": round(float(row.get("final_score") or 0) + 0.12 * relevance, 6),
                    "evidence_relevance": round(relevance, 6),
                    "source_id": row.get("doc_id", ""),
                    "relation": "",
                    "evidence": evidence_text,
                    "qa_id": row.get("qa_id", ""),
                    "question": qa.get("question", ""),
                    "answer": qa.get("answer", ""),
                }
            )
    semantic_contexts.sort(key=lambda item: item["score"], reverse=True)
    contexts.extend(semantic_contexts[: max(0, limit - len(contexts))])
    for index, item in enumerate(contexts, start=1):
        item["context_rank"] = index
    return contexts[:limit]


def relevance_targets(query_record):
    targets = query_record.get("evaluation_targets", {})
    entity_ids = set(targets.get("relevant_entity_ids", []))
    qa_ids = set(targets.get("relevant_qa_ids", []))
    if not entity_ids:
        entity_ids = {
            item.get("entity_id", "")
            for item in query_record.get("detected_entities", []) + query_record.get("semantic_candidate_entities", [])
            if item.get("entity_id")
        }
    return {"entity_ids": entity_ids, "qa_ids": qa_ids}


def dcg(relevances):
    import math

    return sum(rel / math.log2(index + 2) for index, rel in enumerate(relevances))


def relation_is_relevant(row, targets):
    return (
        row.get("source_entity_id", "") in targets["entity_ids"]
        or row.get("target_entity_id", "") in targets["entity_ids"]
        or row.get("qa_id", "") in targets["qa_ids"]
    )


def context_is_relevant(row, targets):
    return row.get("qa_id", "") in targets["qa_ids"]


def relation_relevance_key(row, targets):
    if row.get("qa_id", "") in targets["qa_ids"]:
        return row.get("qa_id", "")
    if row.get("source_entity_id", "") in targets["entity_ids"]:
        return row.get("source_entity_id", "")
    if row.get("target_entity_id", "") in targets["entity_ids"]:
        return row.get("target_entity_id", "")
    return ""


def context_relevance_key(row, targets):
    return row.get("qa_id", "") if row.get("qa_id", "") in targets["qa_ids"] else ""


def metric_bundle(rows, is_relevant, relevant_total, recall_k=5, ndcg_k=10):
    if relevant_total <= 0:
        return {
            "relevant_total": 0,
            "retrieved_relevant_at_5": 0,
            "recall_at_5": "",
            "mrr": "",
            "ndcg_at_10": "",
        }
    seen_relevance = set()
    relevances = []
    for row in rows:
        key = is_relevant(row)
        if key and key not in seen_relevance:
            seen_relevance.add(key)
            relevances.append(1)
        else:
            relevances.append(0)
    retrieved_relevant_at_5 = sum(relevances[:recall_k])
    first_relevant_rank = next((index + 1 for index, rel in enumerate(relevances) if rel), None)
    ideal_dcg = dcg([1] * min(relevant_total, ndcg_k))
    return {
        "relevant_total": relevant_total,
        "retrieved_relevant_at_5": retrieved_relevant_at_5,
        "recall_at_5": round(retrieved_relevant_at_5 / relevant_total, 6),
        "mrr": round(1 / first_relevant_rank, 6) if first_relevant_rank else 0.0,
        "ndcg_at_10": round(dcg(relevances[:ndcg_k]) / ideal_dcg, 6) if ideal_dcg else 0.0,
    }


def evaluate_hybrid_result(query_record, relation_rows, contexts):
    targets = relevance_targets(query_record)
    relation_total = len(targets["entity_ids"] | targets["qa_ids"])
    context_relevances = [1 if context_is_relevant(row, targets) else 0 for row in contexts]
    unique_context_qa_hits = {row.get("qa_id", "") for row in contexts if row.get("qa_id", "") in targets["qa_ids"]}
    context_precision = sum(context_relevances) / len(context_relevances) if context_relevances else 0.0
    context_recall = len(unique_context_qa_hits) / len(targets["qa_ids"]) if targets["qa_ids"] else ""
    return [
        {
            "query_id": query_record["query_id"],
            "query": query_record["query"],
            "stage": "hybrid_retrieval",
            "result_type": "relation",
            "ragas_context_precision": "",
            "ragas_context_recall": "",
            **metric_bundle(relation_rows, lambda row: relation_relevance_key(row, targets), relation_total),
        },
        {
            "query_id": query_record["query_id"],
            "query": query_record["query"],
            "stage": "hybrid_retrieval",
            "result_type": "context",
            "ragas_context_precision": round(context_precision, 6),
            "ragas_context_recall": round(context_recall, 6) if context_recall != "" else "",
            **metric_bundle(contexts, lambda row: context_relevance_key(row, targets), len(targets["qa_ids"])),
        },
    ]


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
            f"- Hybrid metrics JSON: `{relpath(HYBRID_METRICS_JSON)}`",
            f"- Hybrid metrics CSV: `{relpath(HYBRID_METRICS_CSV)}`",
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
    _, qa_sources, _, by_source, by_qa, _, family_to_entities = load_graph()
    query_records = {row["query_id"]: row for row in load_json(QUERY_UNDERSTANDING_JSON)}
    semantic_results = load_json(SEMANTIC_RETRIEVAL_JSON)

    all_relation_rows = []
    all_context_rows = []
    metric_rows = []
    results = []
    for semantic_result in semantic_results:
        query_record = query_records[semantic_result["query_id"]]
        relation_rows, _, seeds = traverse_and_rank(query_record, semantic_result, by_source, by_qa, family_to_entities, qa_sources)
        contexts = build_contexts(query_record, relation_rows, semantic_result, qa_sources, args.top_contexts)
        top_relations = relation_rows[: args.top_relations]
        metric_rows.extend(evaluate_hybrid_result(query_record, top_relations, contexts))
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
    HYBRID_METRICS_JSON.write_text(json.dumps(metric_rows, ensure_ascii=False, indent=2), encoding="utf-8")
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
            "evidence_relevance",
            "seed_entity_id",
            "seed_entity_name",
            "seed_source",
            "expansion_source",
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
        ["query_id", "query", "context_rank", "context_type", "score", "evidence_relevance", "source_id", "relation", "evidence", "qa_id", "question", "answer"],
    )
    write_csv(
        HYBRID_METRICS_CSV,
        metric_rows,
        [
            "query_id",
            "query",
            "stage",
            "result_type",
            "relevant_total",
            "retrieved_relevant_at_5",
            "recall_at_5",
            "mrr",
            "ndcg_at_10",
            "ragas_context_precision",
            "ragas_context_recall",
        ],
    )
    write_report(results)
    print(
        json.dumps(
            {
                "queries": len(results),
                "hybrid_retrieval_json": relpath(HYBRID_RESULTS_JSON),
                "hybrid_relations_csv": relpath(HYBRID_RELATIONS_CSV),
                "hybrid_contexts_csv": relpath(HYBRID_CONTEXTS_CSV),
                "hybrid_metrics_json": relpath(HYBRID_METRICS_JSON),
                "hybrid_metrics_csv": relpath(HYBRID_METRICS_CSV),
                "report_md": relpath(REPORT_MD),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
