import argparse
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from itertools import product
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent if SCRIPT_DIR.name == "scripts" else SCRIPT_DIR
ENTITY_DIR = BASE_DIR / "outputs" / "03_entity_extraction"
RELATION_DIR = BASE_DIR / "outputs" / "04_relation_extraction"
REPORTS_DIR = BASE_DIR / "reports"

VALIDATED_JSONL = ENTITY_DIR / "ahd_llm_entity_extraction_validated.jsonl"
ENTITIES_CSV = ENTITY_DIR / "ahd_entities_llm.csv"
RELATION_CANDIDATES_CSV = RELATION_DIR / "ahd_relation_candidates_seed.csv"
RELATION_REQUESTS_JSONL = RELATION_DIR / "ahd_llm_relation_extraction_requests.jsonl"
REPORT_MD = REPORTS_DIR / "ahd_relation_extraction_report.md"

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


def read_jsonl(path):
    if not path.exists():
        return []
    records = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                records.append(json.loads(line))
    return records


def load_entity_metadata():
    metadata = {}
    if not ENTITIES_CSV.exists():
        return metadata
    with ENTITIES_CSV.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            key = (row["entity_type"], normalize_arabic(row["canonical_name"]))
            metadata[key] = row
    return metadata


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


def candidate_entities_by_qa(record, metadata, include_low_quality=False):
    grouped = defaultdict(dict)
    for entity in record.get("entities", []):
        key = entity_key(entity)
        meta = metadata.get(key, {})
        if not meta:
            continue
        if not include_low_quality:
            if meta.get("entity_quality") == "low":
                continue
            if meta.get("is_actionable_medical_entity") == "false":
                continue
        entity_id = meta.get("entity_id") or stable_entity_id(entity["entity_type"], entity["canonical_name"])
        item = {
            "entity_id": entity_id,
            "canonical_name": entity["canonical_name"],
            "entity_type": entity["entity_type"],
            "confidence": entity.get("confidence", 0),
            "mentions": [],
        }
        for mention in entity.get("mentions", []):
            qa_id = mention.get("qa_id", "")
            if not qa_id:
                continue
            if entity_id not in grouped[qa_id]:
                grouped[qa_id][entity_id] = {**item, "mentions": []}
            grouped[qa_id][entity_id]["mentions"].append(mention)
    return grouped


def build_relation_candidates(validated_records, metadata, include_low_quality=False, max_pairs_per_qa=25):
    rows = []
    request_records = []
    seen = set()

    for record in validated_records:
        chunk_id = record["chunk_id"]
        by_qa = candidate_entities_by_qa(record, metadata, include_low_quality=include_low_quality)
        request_qa_contexts = []

        for qa_id, entities_by_id in sorted(by_qa.items()):
            entities = list(entities_by_id.values())
            pairs = []
            for source, target in product(entities, entities):
                if source["entity_id"] == target["entity_id"]:
                    continue
                relation_type = relation_type_for(source["entity_type"], target["entity_type"])
                if not relation_type:
                    continue
                pair_key = (source["entity_id"], relation_type, target["entity_id"], qa_id)
                if pair_key in seen:
                    continue
                seen.add(pair_key)

                source_evidence = source["mentions"][0].get("evidence", "") if source["mentions"] else ""
                target_evidence = target["mentions"][0].get("evidence", "") if target["mentions"] else ""
                relation_id = stable_relation_id(source["entity_id"], relation_type, target["entity_id"], qa_id)
                row = {
                    "relation_id": relation_id,
                    "chunk_id": chunk_id,
                    "qa_id": qa_id,
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

            if pairs:
                request_qa_contexts.append(
                    {
                        "qa_id": qa_id,
                        "entities": [
                            {
                                "entity_id": entity["entity_id"],
                                "canonical_name": entity["canonical_name"],
                                "entity_type": entity["entity_type"],
                                "evidence": entity["mentions"][0].get("evidence", "") if entity["mentions"] else "",
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

        if request_qa_contexts:
            request_records.append(
                {
                    "request_id": f"relation_request_{chunk_id}",
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
                        "relations": [
                            {
                                "relation_id": "rel_seed_x",
                                "relation_type": "HAS_SYMPTOM|TREATED_BY|DIAGNOSED_BY|INVESTIGATED_BY",
                                "source_entity_id": "ent_x",
                                "target_entity_id": "ent_y",
                                "qa_id": "ahd5k_00001",
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


def write_report(validated_records, rows, request_records, include_low_quality):
    relation_counts = Counter(row["candidate_relation_type"] for row in rows)
    chunks_with_candidates = len({row["chunk_id"] for row in rows})
    qa_with_candidates = len({row["qa_id"] for row in rows})
    lines = [
        "# AHD Step 4 Relation Candidate Report",
        "",
        "## Purpose",
        "",
        "Step 4 tests whether the Step 3 entity layer can feed relation extraction.",
        "This is a candidate layer only: relation pairs still need LLM or manual validation before Neo4j import.",
        "",
        "## Current Test",
        "",
        f"- Validated entity chunks read: {len(validated_records)}",
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
            lines.append(f"- {relation_type}: {count}")
    else:
        lines.append("- No relation candidates generated.")

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
    for row in rows[:5]:
        lines.extend(
            [
                f"- `{row['candidate_relation_type']}`: {row['source_name']} -> {row['target_name']} "
                f"(`{row['chunk_id']}`, `{row['qa_id']}`)",
            ]
        )
    if not rows:
        lines.append("- No samples available.")

    lines.extend(
        [
            "",
            "## Next Command",
            "",
            "```powershell",
            "python scripts\\step04_prepare_relation_candidates.py --limit-chunks 200",
            "```",
        ]
    )
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8-sig")


def main():
    parser = argparse.ArgumentParser(description="Prepare Step 4 relation candidates from Step 3 entities.")
    parser.add_argument("--limit-chunks", type=int, default=0, help="Limit validated chunks for a Step 4 smoke test. 0 means all.")
    parser.add_argument("--include-low-quality", action="store_true")
    parser.add_argument("--max-pairs-per-qa", type=int, default=25)
    args = parser.parse_args()

    RELATION_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    validated_records = read_jsonl(VALIDATED_JSONL)
    if args.limit_chunks > 0:
        validated_records = validated_records[: args.limit_chunks]
    metadata = load_entity_metadata()
    rows, request_records = build_relation_candidates(
        validated_records,
        metadata,
        include_low_quality=args.include_low_quality,
        max_pairs_per_qa=args.max_pairs_per_qa,
    )
    write_csv(rows)
    write_requests(request_records)
    write_report(validated_records, rows, request_records, args.include_low_quality)

    print(
        json.dumps(
            {
                "validated_entity_chunks_read": len(validated_records),
                "candidate_relation_rows": len(rows),
                "relation_request_records": len(request_records),
                "relation_candidates_csv": relpath(RELATION_CANDIDATES_CSV),
                "relation_requests_jsonl": relpath(RELATION_REQUESTS_JSONL),
                "report_md": relpath(REPORT_MD),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

