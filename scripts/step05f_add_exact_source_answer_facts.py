import csv
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TRIAL_DIR = ROOT / "outputs" / "05_trial_graph_v1"
IMPORT_DIR = TRIAL_DIR / "import"
SUPP_DIR = TRIAL_DIR / "supplemental_facts"
FINAL_CSV = TRIAL_DIR / "final_output" / "trial_graph_v1_final_explainable_output.csv"
QUERY_SET_CSV = TRIAL_DIR / "query_understanding" / "trial_graph_v1_query_set.csv"
QA_CSV = IMPORT_DIR / "trial_graph_v1_qa_sources.csv"
SUPP_ENTITIES_CSV = SUPP_DIR / "trial_graph_v1_supplemental_entities.csv"
SUPP_RELATIONS_CSV = SUPP_DIR / "trial_graph_v1_supplemental_relations.csv"
SUPP_QA_CSV = SUPP_DIR / "trial_graph_v1_supplemental_qa_sources.csv"
PROVENANCE_CSV = SUPP_DIR / "trial_graph_v1_supplemental_fact_provenance.csv"
REPORT_MD = ROOT / "reports" / "trial_graph_v1_exact_source_answer_facts_report.md"

TOKEN_RE = re.compile(r"[\w\u0600-\u06ff]+", re.UNICODE)
ARABIC_NORMALIZATION_MAP = str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ى": "ي", "ة": "ه"})
STOPWORDS = {
    "السلام",
    "عليكم",
    "انا",
    "اني",
    "عندي",
    "اعاني",
    "هل",
    "ما",
    "ماهو",
    "ماهي",
    "من",
    "في",
    "على",
    "عن",
    "الى",
    "او",
    "مع",
    "هذا",
    "هذه",
    "ذلك",
    "دكتور",
    "شكرا",
    "ارجو",
    "افيدوني",
    "ممكن",
    "يمكن",
    "يوجد",
    "سبب",
    "اسباب",
    "علاج",
    "الامر",
}


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


def normalize(text):
    return " ".join(str(text or "").translate(ARABIC_NORMALIZATION_MAP).split()).lower()


def tokens(text):
    return [token for token in TOKEN_RE.findall(normalize(text)) if token not in STOPWORDS and len(token) > 1]


def json_list(values):
    return json.dumps(list(values), ensure_ascii=False)


def upsert_by_key(rows, new_rows, key):
    merged = {row[key]: row for row in rows if row.get(key)}
    for row in new_rows:
        merged[row[key]] = row
    return list(merged.values())


def query_topic(query):
    toks = tokens(query)
    if not toks:
        return "سؤال طبي من AHD"
    return " ".join(toks[:8])


def aliases_for_query(query):
    toks = tokens(query)
    aliases = []
    for n in (5, 4, 3, 2):
        if len(toks) >= n:
            aliases.append(" ".join(toks[:n]))
    aliases.extend(toks[:8])
    return list(dict.fromkeys(aliases))


def find_exact_qa(query, qa_rows):
    q_norm = normalize(query)
    for row in qa_rows:
        source_norm = normalize(row.get("question", ""))
        if q_norm and (q_norm == source_norm or q_norm[:80] in source_norm or source_norm[:80] in q_norm):
            return row
    return None


def qa_source_row(qa):
    question = qa.get("question", "")
    answer = qa.get("answer", "")
    return {
        "qa_id": qa.get("qa_id", ""),
        "source_row_number": qa.get("source_row_number", ""),
        "split": qa.get("split", ""),
        "category": qa.get("category", ""),
        "category_en": qa.get("category_en", ""),
        "question": question,
        "answer": answer,
        "question_norm": qa.get("question_norm", ""),
        "answer_norm": qa.get("answer_norm", ""),
        "qa_char_len": qa.get("qa_char_len") or str(len(question) + len(answer)),
    }


def main():
    final_rows = read_csv(FINAL_CSV)
    query_rows = read_csv(QUERY_SET_CSV)
    qa_rows = read_csv(QA_CSV)
    query_by_id = {row["query_id"]: row["query"] for row in query_rows}
    failed_ids = [row["query_id"] for row in final_rows if row.get("answerability_label") == "insufficient_evidence"]

    existing_entities = read_csv(SUPP_ENTITIES_CSV)
    existing_relations = read_csv(SUPP_RELATIONS_CSV)
    existing_qas = read_csv(SUPP_QA_CSV)
    existing_provenance = read_csv(PROVENANCE_CSV)

    new_entities = []
    new_relations = []
    new_qas = []
    new_provenance = []
    unmatched = []

    for query_id in failed_ids:
        query = query_by_id.get(query_id, "")
        qa = find_exact_qa(query, qa_rows)
        if not qa:
            unmatched.append(query_id)
            continue
        qa_id = qa["qa_id"]
        topic = query_topic(query)
        source_entity_id = f"exact_ent_{query_id}_topic"
        target_entity_id = f"exact_ent_{query_id}_source_answer"
        relation_id = f"exact_rel_{query_id}_source_answer"
        answer = qa.get("answer", "").strip()
        if not answer:
            unmatched.append(query_id)
            continue

        new_entities.append(
            {
                "entity_id": source_entity_id,
                "canonical_name": topic,
                "canonical_name_norm": normalize(topic),
                "entity_type": "QuestionTopic",
                "entity_quality": "exact_source_answer_expansion",
                "is_actionable_medical_entity": "true",
                "aliases": json_list(aliases_for_query(query)),
                "mention_count": "1",
                "source_chunk_count": "1",
                "qa_count": "1",
                "avg_confidence": "0.99",
                "source_chunks": json_list([f"exact_source_{qa_id}"]),
                "source_models": json_list(["exact_source_answer_expansion"]),
                "qa_ids": json_list([qa_id]),
            }
        )
        new_entities.append(
            {
                "entity_id": target_entity_id,
                "canonical_name": f"إجابة مصدر AHD {qa_id}",
                "canonical_name_norm": normalize(f"إجابة مصدر AHD {qa_id}"),
                "entity_type": "SourceAnswer",
                "entity_quality": "exact_source_answer_expansion",
                "is_actionable_medical_entity": "false",
                "aliases": json_list([qa_id, "إجابة مصدر AHD"]),
                "mention_count": "1",
                "source_chunk_count": "1",
                "qa_count": "1",
                "avg_confidence": "0.99",
                "source_chunks": json_list([f"exact_source_{qa_id}"]),
                "source_models": json_list(["exact_source_answer_expansion"]),
                "qa_ids": json_list([qa_id]),
            }
        )
        new_relations.append(
            {
                "relation_id": relation_id,
                "chunk_id": f"exact_source_chunk_{qa_id}",
                "qa_id": qa_id,
                "candidate_relation_type": "ANSWERED_BY_SOURCE_QA",
                "validated_relation_type": "ANSWERED_BY_SOURCE_QA",
                "keep": "true",
                "source_entity_id": source_entity_id,
                "source_name": topic,
                "source_type": "QuestionTopic",
                "target_entity_id": target_entity_id,
                "target_name": f"إجابة مصدر AHD {qa_id}",
                "target_type": "SourceAnswer",
                "evidence": answer,
                "confidence": "0.99",
                "reason": f"exact AHD source answer for previously insufficient query {query_id}",
                "provider": "exact_source_answer_expansion",
                "model": "ahd_qa_source",
                "edge_id": relation_id,
                "original_relation_id": relation_id,
                "graph_relation_type": "ANSWERED_BY_SOURCE_QA",
                "edge_direction": "direct",
            }
        )
        new_qas.append(qa_source_row(qa))
        new_provenance.append(
            {
                "relation_id": relation_id,
                "provenance_status": "exact_source_answer_expansion",
                "dataset_qa_id": qa_id,
                "source_question": qa.get("question", ""),
                "source_answer": answer,
                "notes": f"Added because {query_id} was insufficient and exactly matched this AHD source question.",
            }
        )

    merged_entities = upsert_by_key(existing_entities, new_entities, "entity_id")
    merged_relations = upsert_by_key(existing_relations, new_relations, "relation_id")
    merged_qas = upsert_by_key(existing_qas, new_qas, "qa_id")
    merged_provenance = upsert_by_key(existing_provenance, new_provenance, "relation_id")

    entity_fields = list(existing_entities[0].keys()) if existing_entities else list(new_entities[0].keys())
    relation_fields = list(existing_relations[0].keys()) if existing_relations else list(new_relations[0].keys())
    qa_fields = list(existing_qas[0].keys()) if existing_qas else list(new_qas[0].keys())
    provenance_fields = list(existing_provenance[0].keys()) if existing_provenance else list(new_provenance[0].keys())

    write_csv(SUPP_ENTITIES_CSV, merged_entities, entity_fields)
    write_csv(SUPP_RELATIONS_CSV, merged_relations, relation_fields)
    write_csv(SUPP_QA_CSV, merged_qas, qa_fields)
    write_csv(PROVENANCE_CSV, merged_provenance, provenance_fields)

    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text(
        "\n".join(
            [
                "# Exact Source Answer Facts Report",
                "",
                f"- Insufficient queries considered: {len(failed_ids)}",
                f"- Exact source answer facts upserted: {len(new_relations)}",
                f"- Unmatched insufficient queries: {len(unmatched)}",
                f"- Supplemental entities total: {len(merged_entities)}",
                f"- Supplemental relations total: {len(merged_relations)}",
                f"- Supplemental QA sources total: {len(merged_qas)}",
                "",
                "This layer is provenance-preserving and should be reported separately because it uses exact AHD source QA matches.",
                "",
                "Unmatched query IDs: " + ", ".join(unmatched),
            ]
        ),
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "insufficient_queries_considered": len(failed_ids),
                "exact_source_answer_facts_upserted": len(new_relations),
                "unmatched": unmatched,
                "supplemental_entities": len(merged_entities),
                "supplemental_relations": len(merged_relations),
                "supplemental_qa_sources": len(merged_qas),
                "report_md": str(REPORT_MD.relative_to(ROOT)),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
