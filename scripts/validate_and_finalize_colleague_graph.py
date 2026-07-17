import argparse
import csv
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.request
from collections import defaultdict
from pathlib import Path


# %% [markdown]
# Final entity and relation validation
#
# The files in ``dah`` are immutable colleague hand-off files. This script
# cleans the entity layer, resumes strict relation validation, and writes only
# reusable final graph tables. Raw LLM responses are retained as an evaluation
# and resume cache; request payloads and markdown reports are not generated.

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.step08a_normalize_query import normalize_query

FINAL_DIR = ROOT / "outputs" / "final_graph"
PROVENANCE_DIR = FINAL_DIR / "provenance"
ENV_FILE = ROOT / ".env"

SOURCE_ENTITIES = PROVENANCE_DIR / "ahd_entities_llm_merged.csv"
SOURCE_MENTIONS = PROVENANCE_DIR / "ahd_entity_mentions_llm_merged.csv"
SOURCE_CANDIDATES = PROVENANCE_DIR / "ahd_relation_candidates_seed.csv"
SOURCE_VALIDATED = PROVENANCE_DIR / "ahd_llm_relation_validation_validated.jsonl"
RAW_CACHE = PROVENANCE_DIR / "relation_validation_raw.jsonl"

FINAL_ENTITIES = FINAL_DIR / "entities.csv"
FINAL_MENTIONS = FINAL_DIR / "entity_mentions.csv"
FINAL_DECISIONS = FINAL_DIR / "relation_decisions.csv"
FINAL_RELATIONS = FINAL_DIR / "relations.csv"
FINAL_BIDIRECTIONAL = FINAL_DIR / "relations_bidirectional.csv"
FROZEN_MANIFEST = FINAL_DIR / "graph_manifest.json"

ENTITY_TYPES = {"DiseaseCondition", "Symptom", "Treatment", "Test"}
RELATION_TYPES = {"HAS_SYMPTOM", "TREATED_BY", "DIAGNOSED_BY", "INVESTIGATED_BY"}
INVERSE_RELATIONS = {
    "HAS_SYMPTOM": "SYMPTOM_OF",
    "TREATED_BY": "TREATS",
    "DIAGNOSED_BY": "DIAGNOSES",
    "INVESTIGATED_BY": "INVESTIGATES",
}
MODEL = "qwen/qwen3-32b"
PROMPT_VERSION = "dah_relation_validation_v1"
# Six decisions keep Qwen's complete JSON response comfortably inside the
# current Groq 6K-token-per-minute allowance and reduce omitted relation IDs.
MAX_RELATIONS_PER_REQUEST = 6


# %% [markdown]
# Shared file, environment, and value handling


def load_env() -> None:
    if not ENV_FILE.exists():
        return
    for raw_line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def read_csv(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    records = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL in {path} at line {line_number}: {exc}") from exc
    return records


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def safe_float(value, default: float = 0.0) -> float:
    try:
        return min(1.0, max(0.0, float(value)))
    except (TypeError, ValueError):
        return default


def normalize(value: str) -> str:
    # Reuse the exact Step 8/project normalization rather than introducing a
    # second normalization contract for final graph IDs and aliases.
    return normalize_query(str(value or "")).normalized_query


def unique_strings(values: list[str]) -> list[str]:
    seen = set()
    result = []
    for value in values:
        text = str(value or "").strip()
        key = normalize(text)
        if text and key and key not in seen:
            seen.add(key)
            result.append(text)
    return result


# %% [markdown]
# Entity validation and canonical table construction


TYPE_MARKERS = {
    "Test": ("تحليل", "تحاليل", "فحص", "اختبار", "اشعه", "تصوير", "قياس"),
    "Treatment": ("دواء", "علاج", "مرهم", "كريم", "حقن", "جراح", "مضاد", "باراسيتامول"),
    "Symptom": (
        "الم",
        "دوخه",
        "صداع",
        "سعال",
        "حمي",
        "غثيان",
        "قيء",
        "تعب",
        "حكه",
        "ضيق تنفس",
        "اسهال",
        "امساك",
    ),
    "DiseaseCondition": (
        "التهاب",
        "سرطان",
        "متلازمه",
        "حساسيه",
        "عدوي",
        "قصور",
        "فشل",
        "سكري",
        "ربو",
        "فقر الدم",
    ),
}
TYPE_PRIORITY = {"DiseaseCondition": 4, "Symptom": 3, "Treatment": 2, "Test": 1}


def inferred_type(name_norm: str) -> str | None:
    for entity_type in ("Test", "Treatment", "Symptom", "DiseaseCondition"):
        if any(marker in name_norm for marker in TYPE_MARKERS[entity_type]):
            return entity_type
    return None


def mention_confidence(mention: dict) -> float:
    return safe_float(mention.get("confidence") or mention.get("llm_confidence"), 0.0)


def choose_type_conflict_winner(rows: list[dict], mentions_by_entity: dict[str, list[dict]]) -> dict:
    marker_type = inferred_type(rows[0]["canonical_name_norm"])
    if marker_type:
        marked = [row for row in rows if row["entity_type"] == marker_type]
        if marked:
            return marked[0]

    def score(row: dict) -> tuple:
        mentions = mentions_by_entity.get(row["entity_id"], [])
        confidences = [mention_confidence(item) for item in mentions]
        evidence_score = sum(confidences) + 0.25 * len(mentions)
        return evidence_score, len(mentions), TYPE_PRIORITY[row["entity_type"]]

    return max(rows, key=score)


def build_final_entities(source_entities: list[dict], source_mentions: list[dict]) -> tuple[list[dict], list[dict], set[str]]:
    mentions_by_entity = defaultdict(list)
    for mention in source_mentions:
        mentions_by_entity[mention["entity_id"]].append(mention)

    eligible = []
    for entity in source_entities:
        entity_type = entity.get("entity_type", "").strip()
        name = entity.get("canonical_name", "").strip()
        name_norm = normalize(name)
        if entity_type not in ENTITY_TYPES or not name or not name_norm:
            continue
        if not mentions_by_entity.get(entity["entity_id"]):
            continue
        eligible.append({**entity, "canonical_name_norm": name_norm})

    # A normalized medical concept receives one graph type. Conflicts are
    # resolved by conservative lexical markers, then mention evidence strength.
    groups = defaultdict(list)
    for entity in eligible:
        groups[entity["canonical_name_norm"]].append(entity)

    accepted = []
    for rows in groups.values():
        types = {row["entity_type"] for row in rows}
        accepted.append(rows[0] if len(types) == 1 else choose_type_conflict_winner(rows, mentions_by_entity))

    accepted_ids = {row["entity_id"] for row in accepted}
    final_entities = []
    for entity in sorted(accepted, key=lambda row: row["entity_id"]):
        mentions = mentions_by_entity[entity["entity_id"]]
        aliases = unique_strings([entity["canonical_name"], *[item.get("surface_form", "") for item in mentions]])
        confidences = [mention_confidence(item) for item in mentions]
        usable_confidences = [value for value in confidences if value > 0]
        confidence = sum(usable_confidences) / len(usable_confidences) if usable_confidences else 0.0
        final_entities.append(
            {
                "entity_id": entity["entity_id"],
                "canonical_name": entity["canonical_name"].strip(),
                "canonical_name_norm": entity["canonical_name_norm"],
                "entity_type": entity["entity_type"],
                "aliases": json.dumps(aliases, ensure_ascii=False),
                "confidence": f"{confidence:.3f}",
                "mention_count": len(mentions),
                "provider": entity.get("provider", ""),
                "model": entity.get("model", ""),
            }
        )

    final_mentions = []
    for mention in source_mentions:
        if mention["entity_id"] not in accepted_ids:
            continue
        row = dict(mention)
        row["confidence"] = f"{mention_confidence(mention):.3f}"
        final_mentions.append(row)
    return final_entities, final_mentions, accepted_ids


# %% [markdown]
# Existing and resumable relation decisions


def clean_legacy_text(value: str) -> str:
    text = str(value or "")
    if "Ø" not in text and "Ù" not in text:
        return text
    try:
        return text.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return text


def load_legacy_decisions(candidates: dict[str, dict]) -> dict[str, dict]:
    latest = {}
    for record in read_jsonl(SOURCE_VALIDATED):
        for decision in record.get("relations", []):
            relation_id = str(decision.get("relation_id", "")).strip()
            if relation_id in candidates:
                latest[relation_id] = {
                    "keep": str(decision.get("keep", "false")).lower() == "true",
                    "relation_type": decision.get("validated_relation_type") or decision.get("relation_type"),
                    "confidence": safe_float(decision.get("confidence")),
                    "evidence": clean_legacy_text(decision.get("evidence", "")),
                    "reason": clean_legacy_text(decision.get("reason", "")),
                    "provider": decision.get("provider", record.get("provider", "")),
                    "model": decision.get("model", record.get("model", "")),
                    "prompt_version": "colleague_validation",
                }
    return latest


def extract_json_object(text: str) -> dict:
    value = str(text or "").strip()
    if value.startswith("```"):
        value = value.strip("`").strip()
        if value.startswith("json"):
            value = value[4:].strip()
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        start, end = value.find("{"), value.rfind("}")
        if start >= 0 and end > start:
            return json.loads(value[start : end + 1])
        raise


def relation_list_from_payload(parsed) -> list[dict]:
    """Accept the requested object wrapper and a recoverable top-level list."""
    if isinstance(parsed, dict):
        relations = parsed.get("relations", [])
    elif isinstance(parsed, list):
        relations = parsed
    else:
        relations = []
    return [row for row in relations if isinstance(row, dict)]


def validated_response_decisions(raw: dict, candidates: dict[str, dict]) -> dict[str, dict]:
    # An incomplete response is not a completed request, but each well-formed
    # decision it did return is still independently usable. Keep those IDs and
    # reschedule only the omitted candidates on the next run.
    if not raw.get("response_text"):
        return {}
    try:
        parsed = extract_json_object(raw["response_text"])
    except (json.JSONDecodeError, TypeError):
        return {}
    result = {}
    for decision in relation_list_from_payload(parsed):
        relation_id = str(decision.get("relation_id", "")).strip()
        if relation_id not in candidates:
            continue
        relation_type = str(decision.get("relation_type") or candidates[relation_id]["candidate_relation_type"])
        if relation_type not in RELATION_TYPES:
            relation_type = candidates[relation_id]["candidate_relation_type"]
        result[relation_id] = {
            "keep": decision.get("keep") is True or str(decision.get("keep", "")).lower() == "true",
            "relation_type": relation_type,
            "confidence": safe_float(decision.get("confidence")),
            "evidence": str(decision.get("evidence", "")).strip(),
            "reason": str(decision.get("reason", "")).strip(),
            "provider": raw.get("provider", "groq"),
            "model": raw.get("model", MODEL),
            "prompt_version": raw.get("prompt_version", PROMPT_VERSION),
        }
    return result


def load_all_decisions(candidates: dict[str, dict]) -> dict[str, dict]:
    decisions = load_legacy_decisions(candidates)
    for raw in read_jsonl(RAW_CACHE):
        decisions.update(validated_response_decisions(raw, candidates))
    return decisions


def build_requests(candidates: list[dict], decided_ids: set[str], accepted_entity_ids: set[str]) -> list[dict]:
    by_chunk = defaultdict(list)
    for candidate in candidates:
        if candidate["relation_id"] in decided_ids:
            continue
        if candidate["source_entity_id"] not in accepted_entity_ids or candidate["target_entity_id"] not in accepted_entity_ids:
            continue
        by_chunk[candidate["chunk_id"]].append(candidate)

    requests = []
    for chunk_id in sorted(by_chunk):
        rows = by_chunk[chunk_id]
        for offset in range(0, len(rows), MAX_RELATIONS_PER_REQUEST):
            batch = rows[offset : offset + MAX_RELATIONS_PER_REQUEST]
            relation_ids = [row["relation_id"] for row in batch]
            digest = hashlib.sha1("|".join(relation_ids).encode("utf-8")).hexdigest()[:16]
            requests.append({"request_id": f"dah_relval_{digest}", "chunk_id": chunk_id, "candidates": batch})
    return requests


# %% [markdown]
# Strict Groq relation validation


def make_messages(request_record: dict) -> list[dict]:
    qa_groups = defaultdict(lambda: {"evidence_snippets": [], "candidates": []})
    for row in request_record["candidates"]:
        group = qa_groups[row["qa_id"]]
        for evidence in (row["source_evidence"], row["target_evidence"]):
            evidence = str(evidence or "").strip()
            if evidence and evidence not in group["evidence_snippets"]:
                group["evidence_snippets"].append(evidence[:500])
        group["candidates"].append(
            {
                "relation_id": row["relation_id"],
                "candidate_relation_type": row["candidate_relation_type"],
                "source": {"name": row["source_name"], "type": row["source_type"]},
                "target": {"name": row["target_name"], "type": row["target_type"]},
            }
        )
    qa_contexts = [
        {
            "qa_id": qa_id,
            "evidence_snippets": group["evidence_snippets"][:3],
            "candidates": group["candidates"],
        }
        for qa_id, group in qa_groups.items()
    ]
    payload = {
        "task": "Validate Arabic medical graph relation candidates using only the supplied QA evidence.",
        "allowed_relation_types": sorted(RELATION_TYPES),
        "rules": [
            "Return exactly one decision for every supplied relation_id.",
            "Keep only relations directly supported by the evidence; co-occurrence alone is insufficient.",
            "Reject background medication, allergens, triggers, history, and generic advice as treatment relations.",
            "Reject generic tests that are not directly linked to the source condition or symptom.",
            "Do not create entities, relation IDs, facts, or unsupported medical inference.",
            "Preserve the candidate direction and use one allowed relation type.",
            "Return JSON only.",
        ],
        "qa_contexts": qa_contexts,
        "schema": {
            "relations": [
                {
                    "relation_id": "supplied ID",
                    "keep": True,
                    "relation_type": "allowed type",
                    "confidence": 0.0,
                    "evidence": "short direct evidence",
                    "reason": "short validation reason",
                }
            ]
        },
    }
    return [
        {"role": "system", "content": "You are a strict Arabic medical relation validator. Return valid JSON only."},
        {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
    ]


def call_groq(request_record: dict, api_key: str, model: str) -> str:
    body = {
        "model": model,
        "messages": make_messages(request_record),
        "temperature": 0,
        "max_completion_tokens": 1200,
        "response_format": {"type": "json_object"},
    }
    request = urllib.request.Request(
        "https://api.groq.com/openai/v1/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json", "User-Agent": "AHD-GraphRAG/1.0"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return payload["choices"][0]["message"]["content"]


def response_is_complete(response_text: str, request_record: dict) -> bool:
    try:
        parsed = extract_json_object(response_text)
    except (json.JSONDecodeError, TypeError):
        return False
    expected = {row["relation_id"] for row in request_record["candidates"]}
    returned = {str(row.get("relation_id", "")).strip() for row in relation_list_from_payload(parsed)}
    return expected == returned


def run_live(requests: list[dict], args) -> tuple[int, bool]:
    load_env()
    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key or api_key.lower().startswith("your_"):
        raise RuntimeError("GROQ_API_KEY is not configured in .env")

    calls, rate_limited = 0, False
    with RAW_CACHE.open("a", encoding="utf-8") as handle:
        for index, request_record in enumerate(requests[: args.batch_size], start=1):
            status, error, response_text = "error", "", ""
            try:
                response_text = call_groq(request_record, api_key, args.model)
                if response_is_complete(response_text, request_record):
                    status = "ok"
                else:
                    error = "Malformed or incomplete relation decision set"
            except urllib.error.HTTPError as exc:
                body = exc.read().decode("utf-8", errors="replace")
                retry_after = exc.headers.get("Retry-After", "") if exc.headers else ""
                error = f"HTTP {exc.code}: {exc.reason}; retry_after={retry_after}; body={body[:1000]}"
                rate_limited = exc.code == 429
            except Exception as exc:
                error = str(exc)

            handle.write(
                json.dumps(
                    {
                        "request_id": request_record["request_id"],
                        "chunk_id": request_record["chunk_id"],
                        "candidate_relation_ids": [row["relation_id"] for row in request_record["candidates"]],
                        "provider": "groq",
                        "model": args.model,
                        "prompt_version": PROMPT_VERSION,
                        "status": status,
                        "error": error,
                        "response_text": response_text,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
            handle.flush()
            calls += 1
            print(f"validated request {index}/{min(len(requests), args.batch_size)}: {status}", flush=True)
            if rate_limited:
                break
            if index < min(len(requests), args.batch_size) and args.sleep_seconds > 0:
                time.sleep(args.sleep_seconds)
    return calls, rate_limited


# %% [markdown]
# Final relation tables and concise command-line workflow


def build_relation_tables(candidates: list[dict], decisions: dict[str, dict], accepted_entity_ids: set[str]) -> tuple[list[dict], list[dict], list[dict]]:
    decision_rows, kept_rows = [], []
    for candidate in candidates:
        decision = decisions.get(candidate["relation_id"])
        if not decision:
            continue
        if candidate["source_entity_id"] not in accepted_entity_ids or candidate["target_entity_id"] not in accepted_entity_ids:
            continue
        relation_type = decision["relation_type"] if decision["relation_type"] in RELATION_TYPES else candidate["candidate_relation_type"]
        row = {
            "relation_id": candidate["relation_id"],
            "chunk_id": candidate["chunk_id"],
            "qa_id": candidate["qa_id"],
            "source_row_number": candidate.get("source_row_number", ""),
            "source_entity_id": candidate["source_entity_id"],
            "source_name": candidate["source_name"],
            "source_type": candidate["source_type"],
            "target_entity_id": candidate["target_entity_id"],
            "target_name": candidate["target_name"],
            "target_type": candidate["target_type"],
            "candidate_relation_type": candidate["candidate_relation_type"],
            "validated_relation_type": relation_type,
            "keep": str(bool(decision["keep"])).lower(),
            "confidence": f"{safe_float(decision['confidence']):.3f}",
            "evidence": decision["evidence"] or candidate["source_evidence"] or candidate["target_evidence"],
            "reason": decision["reason"],
            "provider": decision["provider"],
            "model": decision["model"],
            "prompt_version": decision["prompt_version"],
        }
        decision_rows.append(row)
        if decision["keep"]:
            kept_rows.append(row)

    bidirectional = []
    for row in kept_rows:
        direct = {
            **row,
            "edge_id": row["relation_id"],
            "source_relation_id": row["relation_id"],
            "graph_relation_type": row["validated_relation_type"],
            "direction": "original",
        }
        bidirectional.append(direct)
        inverse_type = INVERSE_RELATIONS.get(row["validated_relation_type"])
        if inverse_type:
            inverse = {
                **direct,
                "edge_id": f"{row['relation_id']}__inverse",
                "source_entity_id": row["target_entity_id"],
                "source_name": row["target_name"],
                "source_type": row["target_type"],
                "target_entity_id": row["source_entity_id"],
                "target_name": row["source_name"],
                "target_type": row["source_type"],
                "graph_relation_type": inverse_type,
                "direction": "inverse",
            }
            bidirectional.append(inverse)
    return decision_rows, kept_rows, bidirectional


def export_final_tables(entities, mentions, decision_rows, kept_rows, bidirectional) -> None:
    if FROZEN_MANIFEST.exists():
        raise RuntimeError(
            "final_v1 is frozen by outputs/final_graph/graph_manifest.json; "
            "remove the manifest explicitly before rebuilding it."
        )
    write_csv(FINAL_ENTITIES, entities, ["entity_id", "canonical_name", "canonical_name_norm", "entity_type", "aliases", "confidence", "mention_count", "provider", "model"])
    mention_fields = list(mentions[0].keys()) if mentions else ["mention_id", "entity_id"]
    write_csv(FINAL_MENTIONS, mentions, mention_fields)
    relation_fields = list(decision_rows[0].keys()) if decision_rows else ["relation_id", "keep"]
    write_csv(FINAL_DECISIONS, decision_rows, relation_fields)
    write_csv(FINAL_RELATIONS, kept_rows, relation_fields)
    bidirectional_fields = list(bidirectional[0].keys()) if bidirectional else ["edge_id", "source_relation_id"]
    write_csv(FINAL_BIDIRECTIONAL, bidirectional, bidirectional_fields)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate and finalize the colleague's DAH entity/relation extraction.")
    parser.add_argument("--run-live", action="store_true", help="Call Groq for the next unresolved relation batch.")
    parser.add_argument("--batch-size", type=int, default=50, help="Maximum LLM requests in this run (default: 50).")
    parser.add_argument("--sleep-seconds", type=float, default=15.0)
    parser.add_argument("--model", default=MODEL)
    args = parser.parse_args()
    if args.batch_size <= 0:
        raise ValueError("--batch-size must be greater than zero")

    source_entities = read_csv(SOURCE_ENTITIES)
    source_mentions = read_csv(SOURCE_MENTIONS)
    candidates_list = read_csv(SOURCE_CANDIDATES)
    candidates = {row["relation_id"]: row for row in candidates_list}

    entities, mentions, accepted_entity_ids = build_final_entities(source_entities, source_mentions)
    decisions = load_all_decisions(candidates)
    requests = build_requests(candidates_list, set(decisions), accepted_entity_ids)

    calls, rate_limited = 0, False
    if args.run_live and requests:
        calls, rate_limited = run_live(requests, args)
        decisions = load_all_decisions(candidates)
        requests = build_requests(candidates_list, set(decisions), accepted_entity_ids)

    decision_rows, kept_rows, bidirectional = build_relation_tables(candidates_list, decisions, accepted_entity_ids)
    export_final_tables(entities, mentions, decision_rows, kept_rows, bidirectional)

    print(f"entities: {len(entities)}")
    print(f"mentions: {len(mentions)}")
    print(f"relation candidates: {len(candidates_list)}")
    print(f"relation decisions: {len(decision_rows)}")
    print(f"kept direct relations: {len(kept_rows)}")
    print(f"bidirectional relation rows: {len(bidirectional)}")
    print(f"unresolved validation requests: {len(requests)}")
    print(f"LLM calls this run: {calls}")
    print(f"stopped on rate limit: {str(rate_limited).lower()}")
    print(f"final output: {FINAL_DIR.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
