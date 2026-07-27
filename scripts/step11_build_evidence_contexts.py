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
STEP10_DIR = TRIAL_DIR / "subgraph_reranking"
STEP11_DIR = TRIAL_DIR / "context_construction"
REPORT_MD = ROOT / "reports" / "trial_graph_v1_step11_context_construction_report.md"

QA_CSV = IMPORT_DIR / "trial_graph_v1_qa_sources.csv"
SUPPLEMENTAL_QA_CSV = SUPPLEMENTAL_DIR / "trial_graph_v1_supplemental_qa_sources.csv"
AHD_CSV = ROOT / "AHD.csv"
QUERY_UNDERSTANDING_JSON = STEP8_DIR / "trial_graph_v1_query_understanding.json"
RERANKED_RELATIONS_CSV = STEP10_DIR / "trial_graph_v1_reranked_relations.csv"
RERANKED_EVIDENCE_CSV = STEP10_DIR / "trial_graph_v1_reranked_evidence.csv"

CONTEXT_BUNDLES_JSON = STEP11_DIR / "trial_graph_v1_context_bundles.json"
CONTEXT_BUNDLES_CSV = STEP11_DIR / "trial_graph_v1_context_bundles.csv"
PROMPTS_JSON = STEP11_DIR / "trial_graph_v1_llm_prompts.json"
PROMPTS_JSONL = STEP11_DIR / "trial_graph_v1_llm_prompts.jsonl"
PROMPTS_MD = STEP11_DIR / "trial_graph_v1_llm_prompts.md"
TOKEN_RE = re.compile(r"[\w\u0600-\u06ff]+", re.UNICODE)
DIACRITICS_RE = re.compile(r"[\u064b-\u065f\u0670\u06d6-\u06ed]")
TATWEEL_RE = re.compile(r"\u0640+")
ARABIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")
ARABIC_LETTER_NORMALIZATION = str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ى": "ي", "ئ": "ي", "ؤ": "و", "ة": "ه"})
ARABIC_STOPWORDS = {
    "انا",
    "اني",
    "عندي",
    "عندها",
    "عنده",
    "عمري",
    "عمرى",
    "هل",
    "ما",
    "ماهو",
    "ماهي",
    "ماذا",
    "من",
    "في",
    "فى",
    "على",
    "عن",
    "مع",
    "الى",
    "الي",
    "او",
    "و",
    "ثم",
    "هذا",
    "هذه",
    "ذلك",
    "تلك",
    "هو",
    "هي",
    "كان",
    "كانت",
    "يكون",
    "يمكن",
    "ممكن",
    "السلام",
    "عليكم",
    "دكتور",
    "دكتوره",
    "ارجو",
    "شكرا",
    "جزاكم",
    "الله",
    "خير",
    "لو",
    "اذا",
    "بعد",
    "قبل",
    "منذ",
    "لدي",
    "لها",
    "له",
    "لديها",
    "لديه",
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


def clean_text(text):
    return " ".join((text or "").split())


def normalize_arabic(text):
    text = str(text or "").translate(ARABIC_DIGITS)
    text = TATWEEL_RE.sub("", text)
    text = DIACRITICS_RE.sub("", text)
    text = text.translate(ARABIC_LETTER_NORMALIZATION)
    return clean_text(text).lower()


def token_set(text, remove_stopwords=False):
    tokens = set(TOKEN_RE.findall(normalize_arabic(text)))
    if remove_stopwords:
        tokens = {token for token in tokens if token not in ARABIC_STOPWORDS}
    return tokens


def lexical_similarity(query_tokens, doc_tokens):
    if not query_tokens or not doc_tokens:
        return 0.0
    return len(query_tokens & doc_tokens) / ((len(query_tokens) * len(doc_tokens)) ** 0.5)


def overlap_count(query_tokens, doc_tokens):
    if not query_tokens or not doc_tokens:
        return 0
    return len(query_tokens & doc_tokens)


def shorten(text, max_chars):
    text = clean_text(text)
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3].rstrip() + "..."


def relation_key(row):
    return (
        row.get("query_id", ""),
        row.get("source_entity_id", ""),
        row.get("graph_relation_type", ""),
        row.get("target_entity_id", ""),
    )


def query_index():
    return {row["query_id"]: row for row in load_json(QUERY_UNDERSTANDING_JSON)}


def qa_index():
    return {row["qa_id"]: row for row in read_csv(QA_CSV) + read_csv(SUPPLEMENTAL_QA_CSV)}


def ahd_qa_index():
    rows = []
    if not AHD_CSV.exists():
        return rows
    for idx, row in enumerate(read_csv(AHD_CSV)):
        question = clean_text(row.get("Question", ""))
        answer = clean_text(row.get("Answer", ""))
        if not question or not answer:
            continue
        rows.append(
            {
                "qa_id": f"ahd_full_{idx:06d}",
                "question": question,
                "question_norm": normalize_arabic(question),
                "answer": answer,
                "category": row.get("Category", ""),
                "question_tokens": token_set(question),
                "answer_tokens": token_set(answer),
                "tokens": token_set(question + " " + answer),
                "question_tokens_filtered": token_set(question, remove_stopwords=True),
                "answer_tokens_filtered": token_set(answer, remove_stopwords=True),
                "tokens_filtered": token_set(question + " " + answer, remove_stopwords=True),
            }
        )
    return rows


def best_ahd_qa_fallback(
    query,
    ahd_rows,
    min_score,
    preferred_category="",
    category_bonus=0.0,
    scoring_mode="question",
    min_overlap_tokens=1,
):
    query_norm = normalize_arabic(query)
    query_tokens = token_set(query, remove_stopwords=scoring_mode == "question_answer")
    preferred_category_norm = normalize_arabic(preferred_category)
    best = None
    best_rank_score = 0.0
    for row in ahd_rows:
        if row["question_norm"] == query_norm:
            continue
        if scoring_mode == "question_answer":
            question_tokens = row.get("question_tokens_filtered", set())
            answer_tokens = row.get("answer_tokens_filtered", set())
            combined_tokens = row.get("tokens_filtered", set())
            question_score = lexical_similarity(query_tokens, question_tokens)
            answer_score = lexical_similarity(query_tokens, answer_tokens)
            combined_score = lexical_similarity(query_tokens, combined_tokens)
            score = max(question_score, 0.88 * answer_score, 0.72 * combined_score)
            common_overlap = max(
                overlap_count(query_tokens, question_tokens),
                overlap_count(query_tokens, answer_tokens),
                overlap_count(query_tokens, combined_tokens),
            )
        else:
            question_tokens = row.get("question_tokens", set())
            question_score = lexical_similarity(query_tokens, question_tokens)
            answer_score = lexical_similarity(query_tokens, row.get("answer_tokens", set()))
            combined_score = lexical_similarity(query_tokens, row.get("tokens", set()))
            score = question_score
            common_overlap = overlap_count(query_tokens, question_tokens)
        if common_overlap < min_overlap_tokens:
            continue
        category_match = bool(preferred_category_norm and normalize_arabic(row.get("category", "")) == preferred_category_norm)
        rank_score = score + (category_bonus if category_match else 0.0)
        if rank_score > best_rank_score:
            best = row
            best_rank_score = rank_score
            best_score = score
            best_category_match = category_match
            best_question_score = question_score
            best_answer_score = answer_score
            best_combined_score = combined_score
            best_overlap = common_overlap
    if not best or best_score < min_score:
        return None
    return {
        **best,
        "lexical_score": round(best_score, 6),
        "rank_score": round(best_rank_score, 6),
        "category_match": best_category_match,
        "question_score": round(best_question_score, 6),
        "answer_score": round(best_answer_score, 6),
        "combined_score": round(best_combined_score, 6),
        "overlap_tokens": best_overlap,
        "scoring_mode": scoring_mode,
    }


def reliability_label(edge, evidence_count):
    score = float(edge.get("rerank_score") or 0)
    if score >= 0.82 and evidence_count >= 2:
        return "strong"
    if score >= 0.75:
        return "medium"
    return "limited"


def build_relation_statement(edge):
    return f"{edge.get('source_name', '')} --{edge.get('graph_relation_type', '')}--> {edge.get('target_name', '')}"


def format_detected_entities(query_record):
    rows = []
    seen = set()
    for entity in query_record.get("detected_entities", []):
        key = entity.get("entity_id", "") or entity.get("canonical_name", "")
        if not key or key in seen:
            continue
        seen.add(key)
        rows.append(
            {
                "entity_id": entity.get("entity_id", ""),
                "canonical_name": entity.get("canonical_name", ""),
                "entity_type": entity.get("entity_type", ""),
                "match_type": entity.get("match_type", ""),
            }
        )
    return rows


def build_prompt_text(bundle):
    lines = [
        "User Question:",
        bundle["query"],
        "",
        "Retrieved Entities:",
    ]
    entities = bundle.get("retrieved_entities", [])
    if entities:
        for entity in entities:
            lines.append(
                f"- {entity.get('canonical_name', '')} "
                f"({entity.get('entity_type', '')}; match={entity.get('match_type', '')}; id={entity.get('entity_id', '')})"
            )
    else:
        lines.append("- No retrieved entities.")

    lines.extend(["", "Retrieved Relations:"])
    relations = bundle.get("graph_context", [])
    if relations:
        for edge in relations:
            lines.append(
                f"- [{edge.get('rank', '')}] {edge.get('relation', '')} "
                f"(score={edge.get('rerank_score', '')}; reliability={edge.get('reliability', '')})"
            )
    else:
        lines.append("- No retrieved relations.")

    lines.extend(["", "Evidence Sentences:"])
    evidence_index = 1
    for edge in relations:
        for evidence in edge.get("supporting_evidence", []):
            lines.append(
                f"- E{evidence_index} | qa_id={evidence.get('qa_id', '')} | relation={edge.get('relation', '')}: "
                f"{evidence.get('evidence_text', '')}"
            )
            if evidence.get("source_question"):
                lines.append(f"  Source question: {evidence.get('source_question', '')}")
            if evidence.get("source_answer"):
                lines.append(f"  Source answer: {evidence.get('source_answer', '')}")
            evidence_index += 1
    if evidence_index == 1:
        lines.append("- No evidence sentences.")

    lines.extend(
        [
            "",
            "Instructions:",
            "- Answer in Arabic.",
            "- Answer ONLY using the provided evidence.",
            "- Every medical claim MUST cite at least one evidence id such as [E1] and source qa_id.",
            "- If a retrieved relation has type ANSWERED_BY_SOURCE_QA, treat its evidence sentence as direct AHD source-answer evidence for the user question and answer from it unless it is clearly irrelevant.",
            "- Never introduce diseases, drugs, symptoms, tests, treatments, causes, risks, or diagnoses that are absent from the retrieved entities, relations, and evidence sentences.",
            "- Do not generalize beyond the evidence. Do not add severity, dosage, urgency, diagnosis certainty, or treatment conditions unless directly stated in evidence.",
            "- If the evidence is insufficient for the user's question, say exactly: لا توجد أدلة كافية.",
            "- Mention uncertainty when relation reliability is limited.",
            "- Generate claim by claim. For each claim, include claim_ar, citations, source_qa_ids, and support_status.",
            "- Final answer must be composed only from supported claims.",
            "- Return valid JSON only using the requested Step 12 schema.",
        ]
    )
    return "\n".join(lines)


def build_prompt_records(bundles):
    records = []
    for bundle in bundles:
        records.append(
            {
                "query_id": bundle["query_id"],
                "query": bundle["query"],
                "prompt_version": "evidence_context_v2",
                "prompt_text": build_prompt_text(bundle),
                "context_policy": bundle.get("context_policy", {}),
            }
        )
    return records


def write_prompt_files(prompt_records):
    PROMPTS_JSON.write_text(json.dumps(prompt_records, ensure_ascii=False, indent=2), encoding="utf-8")
    with PROMPTS_JSONL.open("w", encoding="utf-8") as file:
        for record in prompt_records:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")
    lines = ["# Trial Graph v1 Step 11 LLM Prompts", ""]
    for record in prompt_records:
        lines.extend([f"## {record['query_id']}: {record['query']}", "", "```text", record["prompt_text"], "```", ""])
    PROMPTS_MD.write_text("\n".join(lines), encoding="utf-8")


def metadata_index(path, id_col, category_col):
    if not path:
        return {}
    rows = read_csv(ROOT / path)
    return {
        row.get(id_col, ""): {
            "category": row.get(category_col, ""),
        }
        for row in rows
        if row.get(id_col, "")
    }


def build_context_bundles(
    max_edges,
    max_evidence_per_edge,
    max_answer_chars,
    max_context_chars,
    qa_fallback_min_score,
    query_metadata,
    qa_fallback_category_bonus,
    qa_fallback_scoring_mode,
    qa_fallback_min_overlap_tokens,
):
    queries = query_index()
    qas = qa_index()
    ahd_rows = ahd_qa_index() if qa_fallback_min_score > 0 else []
    relations_by_query = defaultdict(list)
    for row in read_csv(RERANKED_RELATIONS_CSV):
        relations_by_query[row.get("query_id", "")].append(row)

    evidence_by_relation = defaultdict(list)
    for row in read_csv(RERANKED_EVIDENCE_CSV):
        evidence_by_relation[relation_key(row)].append(row)

    bundles = []
    flat_rows = []
    for query_id, query_record in queries.items():
        context_chars = 0
        selected_edges = []
        for edge in sorted(relations_by_query.get(query_id, []), key=lambda item: float(item.get("rerank_score") or 0), reverse=True):
            if len(selected_edges) >= max_edges:
                break
            key = relation_key(edge)
            evidence_rows = sorted(evidence_by_relation.get(key, []), key=lambda item: int(item.get("evidence_rank") or 99))
            supporting_evidence = []
            for evidence in evidence_rows[:max_evidence_per_edge]:
                qa = qas.get(evidence.get("qa_id", ""), {})
                item = {
                    "qa_id": evidence.get("qa_id", ""),
                    "evidence_text": clean_text(evidence.get("evidence", "")),
                    "source_question": shorten(qa.get("question", ""), 220),
                    "source_answer": shorten(qa.get("answer", ""), max_answer_chars),
                    "edge_direction": evidence.get("edge_direction", ""),
                    "hybrid_score": evidence.get("hybrid_score", ""),
                }
                added_chars = sum(len(item.get(field, "")) for field in ["evidence_text", "source_question", "source_answer"])
                if context_chars + added_chars > max_context_chars and supporting_evidence:
                    break
                supporting_evidence.append(item)
                context_chars += added_chars

            edge_bundle = {
                "rank": int(edge.get("subgraph_rank") or len(selected_edges) + 1),
                "relation": build_relation_statement(edge),
                "rerank_score": float(edge.get("rerank_score") or 0),
                "source_name": edge.get("source_name", ""),
                "source_type": edge.get("source_type", ""),
                "relation_type": edge.get("graph_relation_type", ""),
                "target_name": edge.get("target_name", ""),
                "target_type": edge.get("target_type", ""),
                "evidence_count": int(edge.get("evidence_count") or len(supporting_evidence)),
                "included_evidence_count": len(supporting_evidence),
                "reliability": reliability_label(edge, int(edge.get("evidence_count") or len(supporting_evidence))),
                "rank_reason": edge.get("rank_reason", ""),
                "supporting_evidence": supporting_evidence,
            }
            selected_edges.append(edge_bundle)

            for evidence_rank, evidence in enumerate(supporting_evidence, start=1):
                flat_rows.append(
                    {
                        "query_id": query_id,
                        "query": query_record["query"],
                        "context_rank": len(flat_rows) + 1,
                        "edge_rank": edge_bundle["rank"],
                        "relation": edge_bundle["relation"],
                        "rerank_score": edge_bundle["rerank_score"],
                        "reliability": edge_bundle["reliability"],
                        "evidence_rank": evidence_rank,
                        "qa_id": evidence["qa_id"],
                        "evidence_text": evidence["evidence_text"],
                        "source_question": evidence["source_question"],
                        "source_answer": evidence["source_answer"],
                    }
                )

        query_meta = query_metadata.get(query_id, {})
        fallback = best_ahd_qa_fallback(
            query_record["query"],
            ahd_rows,
            qa_fallback_min_score,
            preferred_category=query_meta.get("category", ""),
            category_bonus=qa_fallback_category_bonus,
            scoring_mode=qa_fallback_scoring_mode,
            min_overlap_tokens=qa_fallback_min_overlap_tokens,
        )
        if fallback:
            fallback_edge = {
                "rank": len(selected_edges) + 1,
                "relation": f"{query_record['query']} --ANSWERED_BY_AHD_QA_FALLBACK--> {fallback['qa_id']}",
                "rerank_score": fallback["rank_score"],
                "source_name": query_record["query"],
                "source_type": "Question",
                "relation_type": "ANSWERED_BY_AHD_QA_FALLBACK",
                "target_name": fallback["qa_id"],
                "target_type": "AHDSourceAnswer",
                "evidence_count": 1,
                "included_evidence_count": 1,
                "reliability": "medium" if fallback["lexical_score"] >= 0.50 else "limited",
                "rank_reason": (
                    f"nearest non-exact AHD QA fallback by {fallback['scoring_mode']} lexical similarity"
                    + (" with same-category preference" if fallback.get("category_match") else "")
                ),
                "supporting_evidence": [
                    {
                        "qa_id": fallback["qa_id"],
                        "evidence_text": shorten(fallback["answer"], max_answer_chars),
                        "source_question": shorten(fallback["question"], 220),
                        "source_answer": shorten(fallback["answer"], max_answer_chars),
                        "edge_direction": "direct",
                        "hybrid_score": fallback["rank_score"],
                    }
                ],
            }
            selected_edges.append(fallback_edge)
            flat_rows.append(
                {
                    "query_id": query_id,
                    "query": query_record["query"],
                    "context_rank": len(flat_rows) + 1,
                    "edge_rank": fallback_edge["rank"],
                    "relation": fallback_edge["relation"],
                    "rerank_score": fallback_edge["rerank_score"],
                    "reliability": fallback_edge["reliability"],
                    "evidence_rank": 1,
                    "qa_id": fallback["qa_id"],
                    "evidence_text": fallback_edge["supporting_evidence"][0]["evidence_text"],
                    "source_question": fallback_edge["supporting_evidence"][0]["source_question"],
                    "source_answer": fallback_edge["supporting_evidence"][0]["source_answer"],
                }
            )

        bundle = {
            "query_id": query_id,
            "query": query_record["query"],
            "warnings": query_record.get("warnings", []),
            "detected_entities": query_record.get("detected_entities", []),
            "retrieved_entities": format_detected_entities(query_record),
            "intents": query_record.get("intents", []),
            "context_policy": {
                "use_only_retrieved_evidence": True,
                "no_answer_generation_in_step_11": True,
                "max_edges": max_edges,
                "max_evidence_per_edge": max_evidence_per_edge,
                "max_context_chars": max_context_chars,
                "qa_fallback_min_score": qa_fallback_min_score,
                "qa_fallback_category_bonus": qa_fallback_category_bonus,
                "qa_fallback_scoring_mode": qa_fallback_scoring_mode,
                "qa_fallback_min_overlap_tokens": qa_fallback_min_overlap_tokens,
                "query_category": query_meta.get("category", ""),
                "used_context_chars_estimate": context_chars,
            },
            "graph_context": selected_edges,
        }
        bundles.append(bundle)
    return bundles, flat_rows


def write_report(bundles):
    lines = [
        "# Trial Graph v1 Step 11 Evidence-Focused Context Construction Report",
        "",
        "This step converts Step 10 reranked subgraphs into compact evidence bundles for later LLM answer generation.",
        "It still does not generate medical answers.",
        "",
        "## Context Rules",
        "",
        "- Keep graph relation, rerank score, and reliability label",
        "- Attach source Q&A evidence snippets",
        "- Preserve Step 8 warnings, especially missing CAUSES relation warnings",
        "- Enforce a simple character budget so prompts can stay controllable",
        "",
        "## Query Context Summary",
        "",
    ]
    for bundle in bundles:
        evidence_count = sum(edge["included_evidence_count"] for edge in bundle["graph_context"])
        lines.extend(
            [
                f"### {bundle['query']}",
                "",
                f"- Graph edges included: {len(bundle['graph_context'])}",
                f"- Evidence snippets included: {evidence_count}",
            ]
        )
        for warning in bundle.get("warnings", []):
            lines.append(f"- Warning: {warning}")
        for edge in bundle["graph_context"][:5]:
            lines.append(f"- `{edge['reliability']}` `{edge['rerank_score']}` {edge['relation']}")
        lines.append("")
    lines.extend(
        [
            "## Output Files",
            "",
            f"- Context bundles JSON: `{relpath(CONTEXT_BUNDLES_JSON)}`",
            f"- Context bundles CSV: `{relpath(CONTEXT_BUNDLES_CSV)}`",
            f"- LLM prompts JSON: `{relpath(PROMPTS_JSON)}`",
            f"- LLM prompts JSONL: `{relpath(PROMPTS_JSONL)}`",
            f"- LLM prompts Markdown: `{relpath(PROMPTS_MD)}`",
            "",
            "## Next Step From Mix.png",
            "",
            "Continue to Step 12: LLM generation using only these evidence-focused context bundles.",
        ]
    )
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-edges", type=int, default=6)
    parser.add_argument("--max-evidence-per-edge", type=int, default=2)
    parser.add_argument("--max-answer-chars", type=int, default=700)
    parser.add_argument("--max-context-chars", type=int, default=6000)
    parser.add_argument(
        "--qa-fallback-min-score",
        type=float,
        default=0.42,
        help="Add nearest non-exact AHD QA fallback evidence when lexical question similarity is at least this value. Use 0 to disable.",
    )
    parser.add_argument("--query-metadata-csv", default="")
    parser.add_argument("--query-metadata-id-col", default="query_id")
    parser.add_argument("--query-metadata-category-col", default="category")
    parser.add_argument(
        "--qa-fallback-category-bonus",
        type=float,
        default=0.0,
        help="Ranking bonus for non-exact AHD QA fallback rows from the same query category.",
    )
    parser.add_argument(
        "--qa-fallback-scoring-mode",
        choices=["question", "question_answer"],
        default="question",
        help="Score fallback rows using source question only, or the maximum of source question/source answer/combined text.",
    )
    parser.add_argument(
        "--qa-fallback-min-overlap-tokens",
        type=int,
        default=1,
        help="Minimum number of non-stopword query tokens that must overlap with fallback source text.",
    )
    args = parser.parse_args()

    STEP11_DIR.mkdir(parents=True, exist_ok=True)
    query_metadata = metadata_index(args.query_metadata_csv, args.query_metadata_id_col, args.query_metadata_category_col)
    bundles, flat_rows = build_context_bundles(
        args.max_edges,
        args.max_evidence_per_edge,
        args.max_answer_chars,
        args.max_context_chars,
        args.qa_fallback_min_score,
        query_metadata,
        args.qa_fallback_category_bonus,
        args.qa_fallback_scoring_mode,
        args.qa_fallback_min_overlap_tokens,
    )
    CONTEXT_BUNDLES_JSON.write_text(json.dumps(bundles, ensure_ascii=False, indent=2), encoding="utf-8")
    prompt_records = build_prompt_records(bundles)
    write_prompt_files(prompt_records)
    write_csv(
        CONTEXT_BUNDLES_CSV,
        flat_rows,
        [
            "query_id",
            "query",
            "context_rank",
            "edge_rank",
            "relation",
            "rerank_score",
            "reliability",
            "evidence_rank",
            "qa_id",
            "evidence_text",
            "source_question",
            "source_answer",
        ],
    )
    write_report(bundles)
    print(
        json.dumps(
            {
                "queries": len(bundles),
                "context_rows": len(flat_rows),
                "context_bundles_json": relpath(CONTEXT_BUNDLES_JSON),
                "context_bundles_csv": relpath(CONTEXT_BUNDLES_CSV),
                "prompts_json": relpath(PROMPTS_JSON),
                "prompts_md": relpath(PROMPTS_MD),
                "report_md": relpath(REPORT_MD),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
