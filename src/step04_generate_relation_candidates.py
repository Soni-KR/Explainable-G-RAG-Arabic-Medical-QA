import argparse
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from itertools import product
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent
ENTITY_DIR = BASE_DIR / "outputs" / "03_entity_extraction"
RELATION_DIR = BASE_DIR / "outputs" / "04_relation_extraction"
REPORTS_DIR = BASE_DIR / "reports"

ENTITIES_CSV = ENTITY_DIR / "entities.csv"

MENTIONS_CSV = ENTITY_DIR / "entity_mentions.csv"

RELATION_CANDIDATES_CSV = RELATION_DIR / "relation_candidates.csv"
RELATION_REQUESTS_JSONL = RELATION_DIR / "relation_validation_requests.jsonl"
REPORT_MD = REPORTS_DIR / "relation_candidate_report.md"

ARABIC_DIACRITICS_RE = re.compile(r"[\u064b-\u065f\u0670\u06d6-\u06ed]")
TATWEEL_RE = re.compile(r"\u0640+")
WHITESPACE_RE = re.compile(r"\s+")
ARABIC_LETTER_NORMALIZATION = str.maketrans(
    {
        "\u0623": "\u0627",
        "\u0625": "\u0627",
        "\u0622": "\u0627",
        "\u0671": "\u0627",
        "\u0649": "\u064a",
        "\u0626": "\u064a",
        "\u0624": "\u0648",
        "\u0629": "\u0647",
    }
)

ALLOWED_RELATION_TYPES = {
    "HAS_SYMPTOM",
    "TREATED_BY",
    "DIAGNOSED_BY",
    "INVESTIGATED_BY",
}


def relpath(path):
    return path.relative_to(BASE_DIR).as_posix()


def normalize_arabic(value):
    value = str(value or "")
    value = TATWEEL_RE.sub("", value)
    value = ARABIC_DIACRITICS_RE.sub("", value)
    value = value.translate(ARABIC_LETTER_NORMALIZATION)
    value = WHITESPACE_RE.sub(" ", value)
    return value.strip().lower()


def stable_entity_id(entity_type, canonical_name):
    normalized = normalize_arabic(canonical_name)
    digest = hashlib.sha1(f"{entity_type}::{normalized}".encode("utf-8")).hexdigest()[:12]
    return f"ent_{entity_type.lower()}_{digest}"


def stable_relation_id(source_entity_id, relation_type, target_entity_id, qa_id):
    key = f"{source_entity_id}|{relation_type}|{target_entity_id}|{qa_id}"
    digest = hashlib.sha1(key.encode("utf-8")).hexdigest()[:16]
    return f"rel_seed_{digest}"


# def read_jsonl(path):
#     if not path.exists():
#         return []
#     records = []
#     with path.open("r", encoding="utf-8") as handle:
#         for line in handle:
#             if line.strip():
#                 records.append(json.loads(line))
#     return records


def load_entity_metadata():
    metadata = {}
    if not ENTITIES_CSV.exists():
        return metadata
    with ENTITIES_CSV.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            key = (row["entity_type"], normalize_arabic(row["canonical_name"]))
            metadata[key] = row
    return metadata

def load_mentions():
    mentions = []

    if not MENTIONS_CSV.exists():
        return mentions

    with MENTIONS_CSV.open(
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as handle:

        for row in csv.DictReader(handle):
            mentions.append(row)

    return mentions


def relation_type_for(source_type, target_type):
    if source_type == "DiseaseCondition" and target_type == "Symptom":
        return "HAS_SYMPTOM"
    if source_type in {"DiseaseCondition", "Symptom"} and target_type == "Treatment":
        return "TREATED_BY"
    if source_type == "DiseaseCondition" and target_type == "Test":
        return "DIAGNOSED_BY"
    if source_type == "Symptom" and target_type == "Test":
        return "INVESTIGATED_BY"
    return ""


def entity_key(entity):
    return (entity["entity_type"], normalize_arabic(entity["canonical_name"]))


# def candidate_entities_by_qa(record, metadata, include_low_quality=False):
#     grouped = defaultdict(dict)
#     for entity in record.get("entities", []):
#         key = entity_key(entity)
#         meta = metadata.get(key, {})
#         if not meta:
#             continue
#         if not include_low_quality:
#             if meta.get("entity_quality") == "low":
#                 continue
#             if meta.get("is_actionable_medical_entity") == "false":
#                 continue
#         entity_id = meta.get("entity_id") or stable_entity_id(entity["entity_type"], entity["canonical_name"])
#         item = {
#             "entity_id": entity_id,
#             "canonical_name": entity["canonical_name"],
#             "entity_type": entity["entity_type"],
#             "confidence": entity.get("confidence", 0),
#             "mentions": [],
#         }
#         for mention in entity.get("mentions", []):
#             qa_id = mention.get("qa_id", "")
#             if not qa_id:
#                 continue
#             if entity_id not in grouped[qa_id]:
#                 grouped[qa_id][entity_id] = {**item, "mentions": []}
#             grouped[qa_id][entity_id]["mentions"].append(mention)
#     return grouped

def build_relation_candidates(
    mentions,
    metadata,
    include_low_quality=False,
    max_pairs_per_qa=25,
):
    rows = []
    request_records = []
    seen = set()

    # ----------------------------------------------------
    # Group all mentions by (chunk_id, qa_id)
    # ----------------------------------------------------

    grouped = defaultdict(list)

    for mention in mentions:

        chunk_id = mention.get("chunk_id", "")
        qa_id = mention.get("qa_id", "")

        if not qa_id:
            continue

        grouped[(chunk_id, qa_id)].append(mention)

    # ----------------------------------------------------
    # Process one QA at a time
    # ----------------------------------------------------

    for (chunk_id, qa_id), qa_mentions in sorted(grouped.items()):
        source_row_number = qa_mentions[0].get("source_row_number", "")

        request_qa_contexts = []

        entities = {}

        # --------------------------------------------
        # Merge mentions belonging to the same entity
        # --------------------------------------------

        for mention in qa_mentions:

            key = (
                mention["entity_id"],
                mention["entity_type"],
                normalize_arabic(mention["canonical_name"]),
            )

            if key not in entities:

                entities[key] = {
                    "entity_id": mention["entity_id"],
                    "canonical_name": mention["canonical_name"],
                    "entity_type": mention["entity_type"],
                    "confidence": float(mention.get("confidence", 0) or 0),
                    "source_row_number": mention.get("source_row_number", ""),
                    "mentions": [],
                }

            entities[key]["mentions"].append(mention)

        entities = list(entities.values())

        pairs = []

        # --------------------------------------------
        # Generate candidate pairs
        # --------------------------------------------

        for source, target in product(entities, entities):

            if source["entity_id"] == target["entity_id"]:
                continue

            relation_type = relation_type_for(
                source["entity_type"],
                target["entity_type"],
            )

            if not relation_type:
                continue

            pair_key = (
                source["entity_id"],
                relation_type,
                target["entity_id"],
                qa_id,
            )

            if pair_key in seen:
                continue

            seen.add(pair_key)

            source_evidence = (
                source["mentions"][0].get("evidence", "")
                if source["mentions"]
                else ""
            )

            target_evidence = (
                target["mentions"][0].get("evidence", "")
                if target["mentions"]
                else ""
            )

            relation_id = stable_relation_id(
                source["entity_id"],
                relation_type,
                target["entity_id"],
                qa_id,
            )

            row = {
                "relation_id": relation_id,
                "chunk_id": chunk_id,
                "qa_id": qa_id,
                "source_row_number": source_row_number,
                "candidate_relation_type": relation_type,
                "source_entity_id": source["entity_id"],
                "source_name": source["canonical_name"],
                "source_type": source["entity_type"],
                "target_entity_id": target["entity_id"],
                "target_name": target["canonical_name"],
                "target_type": target["entity_type"],
                "source_evidence": source_evidence,
                "target_evidence": target_evidence,
                "candidate_method": "entity_type_cooccurrence_same_qa",
                "needs_llm_validation": "true",
            }

            rows.append(row)
            pairs.append(row)

            if len(pairs) >= max_pairs_per_qa:
                break

        # --------------------------------------------
        # Build request payload
        # --------------------------------------------

        if pairs:

            request_qa_contexts.append(
                {
                    "qa_id": qa_id,
                    "source_row_number": source_row_number,
                    "entities": [
                        {
                            "entity_id": entity["entity_id"],
                            "canonical_name": entity["canonical_name"],
                            "entity_type": entity["entity_type"],
                            "evidence": (
                                entity["mentions"][0].get("evidence", "")
                                if entity["mentions"]
                                else ""
                            ),
                        }
                        for entity in entities
                    ],
                    "candidate_pairs": [
                        {
                            "relation_id": pair["relation_id"],
                            "candidate_relation_type": pair["candidate_relation_type"],
                            "source_entity_id": pair["source_entity_id"],
                            "source_name": pair["source_name"],
                            "target_entity_id": pair["target_entity_id"],
                            "target_name": pair["target_name"],
                        }
                        for pair in pairs
                    ],
                }
            )

            request_records.append(
                {
                    "request_id": f"relation_request_{chunk_id}_{qa_id}",
                    "chunk_id": chunk_id,
                    "task": "Validate candidate medical relations for Arabic Graph-RAG Step 4.",
                    "allowed_relation_types": sorted(ALLOWED_RELATION_TYPES),
                    "rules": [
                        "Validate only relations supported by the QA evidence.",
                        "Reject a candidate if source and target merely co-occur without a medical relation.",
                        "Return JSON only.",
                        "Do not create new entities.",
                    ],
                    "qa_contexts": request_qa_contexts,
                    "required_schema": {
                        "chunk_id": chunk_id,
                        "source_row_number": source_row_number,
                        "relations": [
                            {
                                "relation_id": "rel_seed_x",
                                "relation_type": "HAS_SYMPTOM|TREATED_BY|DIAGNOSED_BY|INVESTIGATED_BY",
                                "source_entity_id": "ent_x",
                                "target_entity_id": "ent_y",
                                "qa_id": qa_id,
                                "evidence": "short evidence phrase",
                                "confidence": 0.85,
                                "keep": True,
                            }
                        ],
                    },
                }
            )

    return rows, request_records


def write_csv(rows):
    fieldnames = [
        "relation_id",
        "chunk_id",
        "qa_id",
        "source_row_number",
        "candidate_relation_type",
        "source_entity_id",
        "source_name",
        "source_type",
        "target_entity_id",
        "target_name",
        "target_type",
        "source_evidence",
        "target_evidence",
        "candidate_method",
        "needs_llm_validation",
    ]
    with RELATION_CANDIDATES_CSV.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_requests(records):
    with RELATION_REQUESTS_JSONL.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def write_report(mentions, rows, request_records, include_low_quality):
    relation_counts = Counter(
        row["candidate_relation_type"]
        for row in rows
    )

    chunks_with_candidates = len(
        {
            row["chunk_id"]
            for row in rows
        }
    )

    qa_with_candidates = len(
        {
            row["qa_id"]
            for row in rows
        }
    )

    mention_count = len(mentions)

    unique_entities = set()

    for mention in mentions:
        entity_id = mention.get("entity_id", "")
        if entity_id:
            unique_entities.add(entity_id)

    lines = [
        "# AHD Step 4 Relation Candidate Report",
        "",
        "## Purpose",
        "",
        "Step 4 prepares candidate medical relations directly from the merged entity and mention tables.",
        "This stage no longer depends on the validated JSONL generated during Step 3.",
        "Candidate relations will later be validated by an LLM before Neo4j import.",
        "",
        "## Current Test",
        "",
        f"- Mention records read: {mention_count}",
        f"- Unique entities referenced: {len(unique_entities)}",
        f"- Candidate relation rows: {len(rows)}",
        f"- Chunks with candidates: {chunks_with_candidates}",
        f"- Q&A records with candidates: {qa_with_candidates}",
        f"- LLM relation request records: {len(request_records)}",
        f"- Included low-quality/non-actionable entities: `{include_low_quality}`",
        "",
        "## Candidate Relation Distribution",
        "",
    ]

    if relation_counts:

        for relation_type, count in sorted(relation_counts.items()):

            lines.append(
                f"- {relation_type}: {count}"
            )

    else:

        lines.append(
            "- No relation candidates generated."
        )

    lines.extend(
        [
            "",
            "## Output Files",
            "",
            f"- Relation candidates: `{relpath(RELATION_CANDIDATES_CSV)}`",
            f"- LLM relation requests: `{relpath(RELATION_REQUESTS_JSONL)}`",
            "",
            "## Sample Candidates",
            "",
        ]
    )

    if rows:

        for row in rows[:5]:

            lines.append(
                f"- `{row['candidate_relation_type']}`: "
                f"{row['source_name']} → {row['target_name']} "
                f"(`{row['chunk_id']}`, `{row['qa_id']}`)"
            )

    else:

        lines.append(
            "- No samples available."
        )

    lines.extend(
        [
            "",
            "## Next Command",
            "",
            "```powershell",
            "python scripts\\step05_validate_relations.py --run-live",
            "```",
        ]
    )

    REPORT_MD.write_text(
        "\n".join(lines),
        encoding="utf-8-sig",
    )


def main():
    global ENTITIES_CSV
    global MENTIONS_CSV
    global RELATION_CANDIDATES_CSV
    global RELATION_REQUESTS_JSONL
    global REPORT_MD

    parser = argparse.ArgumentParser(
        description="Prepare Step 4 relation candidates from validated Step 3 entities."
    )

    parser.add_argument(
        "--limit-chunks",
        type=int,
        default=0,
        help="Limit the number of chunks processed for smoke testing. 0 = process all.",
    )

    parser.add_argument(
        "--include-low-quality",
        action="store_true",
        help="Include entities marked as low quality or non-actionable.",
    )

    parser.add_argument(
        "--max-pairs-per-qa",
        type=int,
        default=25,
        help="Maximum candidate relation pairs generated for each QA.",
    )

    parser.add_argument(
        "--entities-csv",
        default=str(ENTITIES_CSV),
        help="Entity inventory CSV to use. Defaults to the Step 3 entity file.",
    )

    parser.add_argument(
        "--mentions-csv",
        default=str(MENTIONS_CSV),
        help="Entity mention CSV to use. Defaults to the Step 3 mention file.",
    )

    parser.add_argument(
        "--output-tag",
        default="",
        help="Optional output tag, e.g. refined, to avoid overwriting the default Step 4 files.",
    )

    args = parser.parse_args()

    ENTITIES_CSV = Path(args.entities_csv)
    MENTIONS_CSV = Path(args.mentions_csv)
    if args.output_tag:
        safe_tag = re.sub(r"[^A-Za-z0-9_-]+", "_", args.output_tag.strip())
        RELATION_CANDIDATES_CSV = RELATION_DIR / f"ahd_relation_candidates_seed_{safe_tag}.csv"
        RELATION_REQUESTS_JSONL = RELATION_DIR / f"ahd_llm_relation_extraction_requests_{safe_tag}.jsonl"
        REPORT_MD = REPORTS_DIR / f"ahd_relation_extraction_report_{safe_tag}.md"

    RELATION_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    # ----------------------------------------------------------
    # Load merged Step 3 outputs
    # ----------------------------------------------------------

    metadata = load_entity_metadata()
    mentions = load_mentions()

    # Optional smoke test
    if args.limit_chunks > 0:

        allowed_chunks = set()

        for mention in mentions:

            chunk_id = mention.get("chunk_id", "")

            if chunk_id not in allowed_chunks:

                allowed_chunks.add(chunk_id)

                if len(allowed_chunks) >= args.limit_chunks:
                    break

        mentions = [
            mention
            for mention in mentions
            if mention.get("chunk_id", "") in allowed_chunks
        ]

    # ----------------------------------------------------------
    # Build relation candidates
    # ----------------------------------------------------------

    rows, request_records = build_relation_candidates(
        mentions,
        metadata,
        include_low_quality=args.include_low_quality,
        max_pairs_per_qa=args.max_pairs_per_qa,
    )

    # ----------------------------------------------------------
    # Save outputs
    # ----------------------------------------------------------

    write_csv(rows)
    write_requests(request_records)
    write_report(
        mentions,
        rows,
        request_records,
        args.include_low_quality,
    )

    # ----------------------------------------------------------
    # Console summary
    # ----------------------------------------------------------

    print(
        json.dumps(
            {
                "mention_records_read": len(mentions),
                "unique_entities": len(
                    {
                        m["entity_id"]
                        for m in mentions
                        if m.get("entity_id")
                    }
                ),
                "candidate_relation_rows": len(rows),
                "relation_request_records": len(request_records),
                "relation_candidates_csv": relpath(
                    RELATION_CANDIDATES_CSV
                ),
                "relation_requests_jsonl": relpath(
                    RELATION_REQUESTS_JSONL
                ),
                "report_md": relpath(REPORT_MD),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
