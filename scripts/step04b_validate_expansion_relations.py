"""Validate expansion-v2 medical relations with resumable Groq rotation.

Every candidate must receive exactly one decision.  A kept relation must quote
evidence found in its source QA excerpts; co-occurrence alone is rejected.
Successful responses are appended immediately so a stopped run can resume.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import time
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

import step03_expand_graph_entities as batch


ROOT = Path(__file__).resolve().parents[1]
RELATION_DIR = ROOT / "outputs" / "graph_expansion_v2" / "04_relation_extraction"
REQUESTS_JSONL = RELATION_DIR / "relation_validation_requests.jsonl"
CANDIDATES_CSV = RELATION_DIR / "relation_candidates.csv"
ENTITY_MENTIONS_CSV = (
    ROOT
    / "outputs"
    / "graph_expansion_v2"
    / "03_entity_extraction"
    / "entity_mentions_expansion.csv"
)
RAW_RESPONSES = RELATION_DIR / "relation_validation_raw.jsonl"
VALIDATED_JSONL = RELATION_DIR / "relation_validation_validated.jsonl"
DECISIONS_CSV = RELATION_DIR / "relation_decisions.csv"
RELATIONS_CSV = RELATION_DIR / "relations_expansion.csv"
BIDIRECTIONAL_CSV = RELATION_DIR / "relations_bidirectional_expansion.csv"
ERRORS_CSV = RELATION_DIR / "relation_validation_errors.csv"
PROGRESS_JSON = RELATION_DIR / "progress.json"
MANIFEST_JSON = RELATION_DIR / "manifest.json"

GRAPH_VERSION = "expansion_v2"
ALLOWED_RELATION_TYPES = {
    "HAS_SYMPTOM",
    "TREATED_BY",
    "DIAGNOSED_BY",
    "INVESTIGATED_BY",
}
INVERSE_RELATION_TYPES = {
    "HAS_SYMPTOM": "SYMPTOM_OF",
    "TREATED_BY": "TREATS",
    "DIAGNOSED_BY": "DIAGNOSES",
    "INVESTIGATED_BY": "INVESTIGATES",
}
REASON_CODES = {
    "direct_support",
    "cooccurrence_only",
    "background_context",
    "generic_advice",
    "wrong_direction",
    "insufficient_evidence",
}
GENERIC_TREATMENT_TERMS = (
    "استشاره",
    "مراجعه",
    "زياره طبيب",
    "كشف علي",
    "فحص",
    "تحليل",
)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(path)
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL at {path}:{line_number}: {exc}") from exc
    return records


def read_candidates() -> dict[str, dict[str, str]]:
    if not CANDIDATES_CSV.exists():
        raise FileNotFoundError(CANDIDATES_CSV)
    with CANDIDATES_CSV.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    candidates = {row["relation_id"]: row for row in rows}
    if len(candidates) != len(rows):
        raise ValueError("Duplicate relation_id values exist in relation_candidates.csv")
    return candidates


def relation_schema() -> dict[str, Any]:
    decision = {
        "type": "object",
        "properties": {
            "relation_id": {"type": "string"},
            "keep": {"type": "boolean"},
            "evidence_index": {"type": "integer", "minimum": -1},
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
            "reason_code": {"type": "string", "enum": sorted(REASON_CODES)},
        },
        "required": [
            "relation_id",
            "keep",
            "evidence_index",
            "confidence",
            "reason_code",
        ],
        "additionalProperties": False,
    }
    return {
        "type": "object",
        "properties": {
            "chunk_id": {"type": "string"},
            "decisions": {"type": "array", "items": decision},
        },
        "required": ["chunk_id", "decisions"],
        "additionalProperties": False,
    }


def truncate(value: Any, limit: int = 1200) -> str:
    text = str(value or "")
    return text if len(text) <= limit else text[:limit] + "...[truncated]"


def make_messages(request_record: dict[str, Any]) -> list[dict[str, str]]:
    contexts = []
    for context in request_record.get("qa_contexts", []):
        evidence_snippets: list[str] = []
        seen_evidence: set[str] = set()
        evidence_chars = 0
        for entity in context.get("entities", []):
            evidence = truncate(entity.get("evidence", ""), 900)
            normalized = normalize_evidence(evidence)
            if not normalized or normalized in seen_evidence:
                continue
            if evidence_snippets and evidence_chars + len(evidence) > 3600:
                break
            seen_evidence.add(normalized)
            evidence_snippets.append(evidence)
            evidence_chars += len(evidence)
        contexts.append(
            {
                "chunk_id": context.get("chunk_id", ""),
                "qa_id": context.get("qa_id", ""),
                "source_row_number": context.get("source_row_number", ""),
                "entities": [
                    {
                        "entity_id": entity.get("entity_id", ""),
                        "canonical_name": entity.get("canonical_name", ""),
                        "entity_type": entity.get("entity_type", ""),
                    }
                    for entity in context.get("entities", [])
                ],
                "evidence_snippets": evidence_snippets,
                "candidate_pairs": context.get("candidate_pairs", []),
            }
        )
    payload = {
        "task": "Strict Arabic medical relation validation for an evidence-grounded Graph-RAG graph.",
        "chunk_id": request_record["chunk_id"],
        "allowed_relation_types": sorted(ALLOWED_RELATION_TYPES),
        "rules": [
            "Return every candidate relation_id exactly once, even when rejected.",
            "Keep only a relation directly stated or unambiguously supported by that same QA evidence.",
            "Reject mere co-occurrence, patient history, allergens/triggers, and unrelated background medication.",
            "Reject generic test advice unless it is explicitly linked to the source condition or symptom.",
            "Preserve every supplied relation_id; do not return relation types or free-text evidence.",
            "For keep=true, evidence_index must identify one supplied evidence_snippets item that directly supports the complete source-relation-target claim.",
            "For keep=false, evidence_index must be -1.",
            "Use only the allowed reason codes.",
            "Do not create entities, relations, IDs, treatments, tests, diagnoses, or facts.",
        ],
        "required_output": {
            "chunk_id": request_record["chunk_id"],
            "decisions": [
                {
                    "relation_id": "copy supplied ID",
                    "keep": False,
                    "evidence_index": -1,
                    "confidence": 0.2,
                    "reason_code": "cooccurrence_only",
                }
            ],
        },
        "qa_contexts": contexts,
    }
    return [
        {
            "role": "system",
            "content": "You are a conservative medical relation validator. Output only the requested JSON.",
        },
        {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
    ]


def request_body(
    request_record: dict[str, Any],
    model: str,
    max_completion_tokens: int,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "model": model,
        "messages": make_messages(request_record),
        "temperature": 0,
        "max_completion_tokens": max_completion_tokens,
    }
    if model.startswith("openai/gpt-oss-"):
        body["reasoning_effort"] = "low"
        body["include_reasoning"] = False
        body["response_format"] = {
            "type": "json_schema",
            "json_schema": {
                "name": "arabic_medical_relation_decisions",
                "strict": True,
                "schema": relation_schema(),
            },
        }
    else:
        body["response_format"] = {"type": "json_object"}
        if model.startswith("qwen/"):
            body["reasoning_effort"] = "none"
    return body


def call_provider(
    request_record: dict[str, Any],
    *,
    key: str,
    model: str,
    max_completion_tokens: int,
) -> tuple[str, dict[str, Any], dict[str, str]]:
    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        json=request_body(request_record, model, max_completion_tokens),
        timeout=150,
    )
    headers = batch.safe_headers(response)
    if response.status_code >= 400:
        raise batch.ProviderFailure(
            f"HTTP {response.status_code}: {response.reason}",
            status=response.status_code,
            body=response.text[:2000],
            headers=headers,
        )
    payload = response.json()
    response_text = str(payload["choices"][0]["message"]["content"] or "").strip()
    if not response_text:
        raise batch.ProviderFailure("Provider returned an empty response.")
    return response_text, dict(payload.get("usage") or {}), headers


def normalize_evidence(value: Any) -> str:
    return " ".join(str(value or "").split()).strip().lower()


def normalize_guard_text(value: Any) -> str:
    text = unicodedata.normalize("NFKC", str(value or ""))
    text = re.sub(r"[\u064b-\u065f\u0670\u06d6-\u06ed]", "", text)
    text = text.replace("ـ", "").translate(
        str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ى": "ي", "ة": "ه"})
    )
    return " ".join(text.casefold().split())


def load_guard_context(
    candidates: dict[str, dict[str, str]],
) -> tuple[dict[tuple[str, str, str], set[str]], dict[tuple[str, str], set[str]]]:
    """Load mention fields and ambiguity groups used by deterministic guards."""

    if not ENTITY_MENTIONS_CSV.exists():
        raise FileNotFoundError(ENTITY_MENTIONS_CSV)
    fields: dict[tuple[str, str, str], set[str]] = defaultdict(set)
    with ENTITY_MENTIONS_CSV.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            key = (
                str(row.get("qa_id", "")),
                str(row.get("entity_id", "")),
                normalize_evidence(row.get("evidence", "")),
            )
            fields[key].add(str(row.get("field", "")).strip().lower())

    source_groups: dict[tuple[str, str], set[str]] = defaultdict(set)
    for candidate in candidates.values():
        source_groups[
            (candidate["qa_id"], candidate["candidate_relation_type"])
        ].add(candidate["source_entity_id"])
    return fields, source_groups


def deterministic_guard_reason(
    candidate: dict[str, str],
    fields: dict[tuple[str, str, str], set[str]],
    source_groups: dict[tuple[str, str], set[str]],
) -> str:
    """Return a conservative rejection reason, or an empty string to retain."""

    relation_type = candidate["candidate_relation_type"]
    source_evidence = normalize_evidence(candidate.get("source_evidence", ""))
    target_evidence = normalize_evidence(candidate.get("target_evidence", ""))
    source_fields = fields.get(
        (candidate["qa_id"], candidate["source_entity_id"], source_evidence), set()
    )
    target_fields = fields.get(
        (candidate["qa_id"], candidate["target_entity_id"], target_evidence), set()
    )

    if (
        relation_type in {"TREATED_BY", "DIAGNOSED_BY", "INVESTIGATED_BY"}
        and target_fields
        and "answer" not in target_fields
    ):
        return "deterministic_target_not_in_answer"

    target_name = normalize_guard_text(candidate.get("target_name", ""))
    if relation_type == "TREATED_BY" and any(
        term in target_name for term in GENERIC_TREATMENT_TERMS
    ):
        return "deterministic_generic_action_not_treatment"

    source_name = normalize_guard_text(candidate.get("source_name", ""))
    target_name = normalize_guard_text(candidate.get("target_name", ""))
    source_evidence_match = normalize_guard_text(candidate.get("source_evidence", ""))
    target_evidence_match = normalize_guard_text(candidate.get("target_evidence", ""))
    explicit_pair = (
        source_evidence_match == target_evidence_match
        or bool(source_name and source_name in target_evidence_match)
        or bool(target_name and target_name in source_evidence_match)
    )
    source_count = len(source_groups[(candidate["qa_id"], relation_type)])
    if (
        source_count > 1
        and "answer" in source_fields
        and "answer" in target_fields
        and not explicit_pair
    ):
        return "deterministic_ambiguous_cross_pair"
    return ""


def expected_candidate_ids(request_record: dict[str, Any]) -> list[str]:
    return [
        str(pair["relation_id"])
        for context in request_record.get("qa_contexts", [])
        for pair in context.get("candidate_pairs", [])
    ]


def evidence_by_relation_id(request_record: dict[str, Any]) -> dict[str, str]:
    result: dict[str, str] = {}
    for context in request_record.get("qa_contexts", []):
        evidence = " ".join(
            str(entity.get("evidence", "")) for entity in context.get("entities", [])
        )
        for pair in context.get("candidate_pairs", []):
            result[str(pair["relation_id"])] = normalize_evidence(evidence)
    return result


def evidence_options_by_relation_id(
    request_record: dict[str, Any],
) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for context in request_record.get("qa_contexts", []):
        options: list[str] = []
        seen: set[str] = set()
        for entity in context.get("entities", []):
            evidence = " ".join(str(entity.get("evidence", "")).split()).strip()
            normalized = normalize_evidence(evidence)
            if evidence and normalized not in seen:
                seen.add(normalized)
                options.append(evidence)
        for pair in context.get("candidate_pairs", []):
            result[str(pair["relation_id"])] = options
    return result


def candidate_evidence_text(candidate: dict[str, str]) -> str:
    """Return immutable, candidate-specific evidence for a kept relation.

    A relation can be supported across a question and its answer, so exporting
    only one mention-level snippet can omit either the condition or the linked
    symptom/treatment/test. The compact LLM response still has to point at a
    real context snippet, while the persisted provenance is reconstructed from
    the exact source and target evidence that created the candidate.
    """

    snippets: list[str] = []
    seen: set[str] = set()
    for field in ("source_evidence", "target_evidence"):
        evidence = " ".join(str(candidate.get(field, "")).split()).strip()
        normalized = normalize_evidence(evidence)
        if evidence and normalized not in seen:
            seen.add(normalized)
            snippets.append(evidence)
    return " | ".join(snippets)


def parse_and_validate_response(
    response_text: str,
    request_record: dict[str, Any],
    candidates: dict[str, dict[str, str]],
) -> dict[str, Any]:
    try:
        parsed = json.loads(response_text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Malformed JSON response: {exc}") from exc
    if not isinstance(parsed, dict):
        raise ValueError("Response must be a JSON object.")

    # Keep legacy parsing for existing audit fixtures/caches, while all new
    # provider requests use the compact decisions contract below.
    if isinstance(parsed.get("relations"), list):
        return parse_legacy_response(parsed, request_record, candidates)
    if not isinstance(parsed.get("decisions"), list):
        raise ValueError("Response must contain a decisions list.")

    expected = expected_candidate_ids(request_record)
    returned = [
        str(item.get("relation_id", ""))
        for item in parsed["decisions"]
        if isinstance(item, dict)
    ]
    if len(returned) != len(set(returned)):
        raise ValueError("The response contains duplicate relation_id decisions.")
    if set(returned) != set(expected):
        missing = sorted(set(expected) - set(returned))
        unknown = sorted(set(returned) - set(expected))
        raise ValueError(f"Incomplete decision set; missing={missing[:5]}, unknown={unknown[:5]}")

    evidence_options = evidence_options_by_relation_id(request_record)
    cleaned: list[dict[str, Any]] = []
    for item in parsed["decisions"]:
        if not isinstance(item, dict):
            raise ValueError("Every relation decision must be an object.")
        relation_id = str(item["relation_id"])
        candidate = candidates[relation_id]
        relation_type = candidate["candidate_relation_type"]
        if not isinstance(item.get("keep"), bool):
            raise ValueError(f"keep must be boolean for {relation_id}.")
        try:
            confidence = float(item.get("confidence"))
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Invalid confidence for {relation_id}.") from exc
        if not 0.0 <= confidence <= 1.0:
            raise ValueError(f"Confidence outside [0,1] for {relation_id}.")
        try:
            evidence_index = int(item.get("evidence_index"))
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Invalid evidence_index for {relation_id}.") from exc
        reason_code = str(item.get("reason_code", "")).strip()
        if reason_code not in REASON_CODES:
            reason_code = "direct_support" if item["keep"] else "insufficient_evidence"
        options = evidence_options.get(relation_id, [])
        if item["keep"]:
            if evidence_index < 0 or evidence_index >= len(options):
                raise ValueError(f"Kept relation has invalid evidence_index: {relation_id}.")
            evidence = candidate_evidence_text(candidate)
            if not evidence:
                raise ValueError(f"Kept relation lacks candidate evidence: {relation_id}.")
            if reason_code != "direct_support":
                raise ValueError(f"Kept relation is not marked direct_support: {relation_id}.")
        else:
            evidence = ""
            if evidence_index != -1:
                raise ValueError(f"Rejected relation must use evidence_index=-1: {relation_id}.")
        cleaned.append(
            {
                "relation_id": relation_id,
                "keep": item["keep"],
                "relation_type": relation_type,
                "evidence": evidence,
                "confidence": confidence,
                "reason": reason_code,
            }
        )
    return {"chunk_id": request_record["chunk_id"], "relations": cleaned}


def parse_legacy_response(
    parsed: dict[str, Any],
    request_record: dict[str, Any],
    candidates: dict[str, dict[str, str]],
) -> dict[str, Any]:
    expected = expected_candidate_ids(request_record)
    returned = [
        str(item.get("relation_id", ""))
        for item in parsed["relations"]
        if isinstance(item, dict)
    ]
    if len(returned) != len(set(returned)) or set(returned) != set(expected):
        raise ValueError("Incomplete decision set in legacy response.")
    available_evidence = evidence_by_relation_id(request_record)
    cleaned: list[dict[str, Any]] = []
    for item in parsed["relations"]:
        relation_id = str(item["relation_id"])
        candidate = candidates[relation_id]
        relation_type = str(item.get("relation_type", ""))
        if relation_type != candidate["candidate_relation_type"]:
            raise ValueError(f"Relation type changed for {relation_id}.")
        if not isinstance(item.get("keep"), bool):
            raise ValueError(f"keep must be boolean for {relation_id}.")
        confidence = float(item.get("confidence"))
        if not 0.0 <= confidence <= 1.0:
            raise ValueError(f"Confidence outside [0,1] for {relation_id}.")
        evidence = " ".join(str(item.get("evidence", "")).split()).strip()
        if item["keep"]:
            quote = normalize_evidence(evidence)
            reconstructed = normalize_evidence(candidate_evidence_text(candidate))
            is_candidate_provenance = bool(reconstructed) and quote == reconstructed
            is_legacy_verbatim = bool(quote) and quote in available_evidence[relation_id]
            if not (is_candidate_provenance or is_legacy_verbatim):
                raise ValueError(f"Kept relation lacks verbatim evidence: {relation_id}.")
        else:
            evidence = ""
        cleaned.append(
            {
                "relation_id": relation_id,
                "keep": item["keep"],
                "relation_type": relation_type,
                "evidence": evidence,
                "confidence": confidence,
                "reason": str(item.get("reason", "")).strip(),
            }
        )
    return {"chunk_id": request_record["chunk_id"], "relations": cleaned}


def load_latest_raw() -> tuple[dict[str, dict[str, Any]], set[str], set[str]]:
    if not RAW_RESPONSES.exists():
        return {}, set(), set()
    latest: dict[str, dict[str, Any]] = {}
    latest_success: dict[str, dict[str, Any]] = {}
    for record in read_jsonl(RAW_RESPONSES):
        request_id = str(record.get("request_id", ""))
        if request_id:
            latest[request_id] = record
            if record.get("status") == "ok" and str(record.get("response_text", "")).strip():
                latest_success[request_id] = record
    latest = {
        request_id: latest_success.get(request_id, record)
        for request_id, record in latest.items()
    }
    completed = {
        request_id
        for request_id, record in latest.items()
        if record.get("status") == "ok" and str(record.get("response_text", "")).strip()
    }
    return latest, completed, set(latest) - completed


def write_progress(
    *,
    total: int,
    completed: int,
    new_successes: int,
    attempts: int,
    last_request: str,
    stopped_reason: str,
) -> None:
    payload = {
        "graph_version": GRAPH_VERSION,
        "total_requests": total,
        "completed_requests": completed,
        "remaining_requests": max(0, total - completed),
        "completion_percent": round(100.0 * completed / total, 2) if total else 100.0,
        "latest_run_new_successes": new_successes,
        "latest_run_http_attempts": attempts,
        "last_request": last_request,
        "stopped_reason": stopped_reason,
        "updated_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    PROGRESS_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def select_requests_for_live(
    requests_list: list[dict[str, Any]],
    latest_raw: dict[str, dict[str, Any]],
    *,
    revalidate_models: set[str],
    limit: int,
) -> tuple[list[dict[str, Any]], int]:
    """Select missing requests plus explicitly targeted model replacements."""

    selected: list[dict[str, Any]] = []
    revalidation_count = 0
    for request_record in requests_list:
        request_id = str(request_record["request_id"])
        existing = latest_raw.get(request_id)
        completed = bool(
            existing
            and existing.get("status") == "ok"
            and str(existing.get("response_text", "")).strip()
        )
        replace = completed and str(existing.get("model", "")) in revalidate_models
        if not completed or replace:
            selected.append(request_record)
            revalidation_count += int(replace)
    if limit > 0:
        selected = selected[:limit]
        selected_ids = {str(row["request_id"]) for row in selected}
        revalidation_count = sum(
            str(latest_raw.get(request_id, {}).get("model", "")) in revalidate_models
            for request_id in selected_ids
        )
    return selected, revalidation_count


def run_live(
    requests_list: list[dict[str, Any]],
    candidates: dict[str, dict[str, str]],
    *,
    models: list[str],
    limit: int,
    sleep_seconds: float,
    max_completion_tokens: int,
    revalidate_models: set[str],
) -> dict[str, Any]:
    keys = batch.load_api_keys()
    if not keys:
        raise RuntimeError("No Groq key was loaded.")
    slots = [
        batch.ProviderSlot(key=key, model=model, fingerprint=batch.key_fingerprint(key))
        for key in keys
        for model in models
    ]
    latest_raw, completed, _ = load_latest_raw()
    selected, revalidation_count = select_requests_for_live(
        requests_list,
        latest_raw,
        revalidate_models=revalidate_models,
        limit=limit,
    )

    new_successes = 0
    http_attempts = 0
    cursor = 0
    stopped_reason = ""
    last_request = ""
    for position, request_record in enumerate(selected, start=1):
        request_id = str(request_record["request_id"])
        last_request = request_id
        attempt_log: list[dict[str, Any]] = []
        success: dict[str, Any] | None = None
        max_attempts = max(10, len(slots) * 5)
        provider_attempts = 0
        idle_waits = 0
        while provider_attempts < max_attempts:
            slot_index, wait_seconds = batch.next_available_slot(slots, cursor)
            if slot_index is None:
                if wait_seconds and wait_seconds <= 120 and idle_waits < 12:
                    time.sleep(wait_seconds + 1.0)
                    idle_waits += 1
                    continue
                stopped_reason = "all_provider_slots_exhausted"
                break
            slot = slots[slot_index]
            cursor = (slot_index + 1) % len(slots)
            started = time.perf_counter()
            provider_attempts += 1
            http_attempts += 1
            try:
                response_text, usage, headers = call_provider(
                    request_record,
                    key=slot.key,
                    model=slot.model,
                    max_completion_tokens=max_completion_tokens,
                )
                parsed = parse_and_validate_response(response_text, request_record, candidates)
                success = {
                    "request_id": request_id,
                    "chunk_id": request_record["chunk_id"],
                    "provider": "groq",
                    "model": slot.model,
                    "key_fingerprint": slot.fingerprint,
                    "status": "ok",
                    "http_status": 200,
                    "rate_limit_headers": headers,
                    "usage": usage,
                    "attempts_before_success": attempt_log,
                    "latency_ms": round((time.perf_counter() - started) * 1000.0, 3),
                    "response_text": json.dumps(parsed, ensure_ascii=False),
                }
                break
            except ValueError as exc:
                attempt_log.append(
                    {
                        "model": slot.model,
                        "key_fingerprint": slot.fingerprint,
                        "http_status": 422,
                        "error": str(exc)[:1000],
                    }
                )
                continue
            except batch.ProviderFailure as exc:
                attempt_log.append(
                    {
                        "model": slot.model,
                        "key_fingerprint": slot.fingerprint,
                        **batch.failure_payload(exc),
                    }
                )
                if batch.is_daily_quota(exc):
                    slot.disabled_reason = "daily_quota"
                elif exc.status == 429:
                    slot.cooldown_until = time.time() + batch.parse_retry_after(exc.headers)
                elif exc.status == 401:
                    batch.disable_key(slots, slot.fingerprint, "authentication_failed")
                elif exc.status == 403:
                    slot.disabled_reason = "model_not_permitted"
                elif exc.status in {404, 410}:
                    batch.disable_model(slots, slot.model, "model_unavailable")
                elif exc.status == 400 and "json_validate_failed" in exc.body:
                    pass
                elif exc.status >= 500 or exc.status == 0:
                    slot.cooldown_until = time.time() + 10.0
                else:
                    stopped_reason = f"non_retryable_http_{exc.status}"
                    break
            except requests.RequestException as exc:
                attempt_log.append(
                    {
                        "model": slot.model,
                        "key_fingerprint": slot.fingerprint,
                        "http_status": 0,
                        "error": str(exc)[:1000],
                    }
                )
                slot.cooldown_until = time.time() + 10.0

        if success is None:
            if not stopped_reason:
                stopped_reason = "provider_retry_budget_exhausted"
            batch.append_jsonl(
                RAW_RESPONSES,
                {
                    "request_id": request_id,
                    "chunk_id": request_record["chunk_id"],
                    "provider": "groq",
                    "model": "",
                    "status": "error",
                    "error": stopped_reason or "provider_slots_exhausted_for_request",
                    "attempts": attempt_log,
                    "response_text": "",
                },
            )
            break

        batch.append_jsonl(RAW_RESPONSES, success)
        new_successes += 1
        completed.add(request_id)
        write_progress(
            total=len(requests_list),
            completed=len(completed),
            new_successes=new_successes,
            attempts=http_attempts,
            last_request=request_id,
            stopped_reason="",
        )
        print(
            json.dumps(
                {
                    "progress": f"{position}/{len(selected)}",
                    "request_id": request_id,
                    "model": success["model"],
                    "completed_total": len(completed),
                    "remaining_total": len(requests_list) - len(completed),
                },
                ensure_ascii=False,
            ),
            flush=True,
        )
        if sleep_seconds:
            time.sleep(sleep_seconds)

    _, completed, _ = load_latest_raw()
    write_progress(
        total=len(requests_list),
        completed=len(completed),
        new_successes=new_successes,
        attempts=http_attempts,
        last_request=last_request,
        stopped_reason=stopped_reason,
    )
    return {
        "keys_loaded": len(keys),
        "key_fingerprints": [batch.key_fingerprint(key) for key in keys],
        "models": models,
        "new_successes": new_successes,
        "targeted_revalidation_requests": revalidation_count,
        "http_attempts": http_attempts,
        "completed_requests": len(completed),
        "remaining_requests": len(requests_list) - len(completed),
        "stopped_reason": stopped_reason,
        "disabled_slots": [
            {
                "model": slot.model,
                "key_fingerprint": slot.fingerprint,
                "reason": slot.disabled_reason,
            }
            for slot in slots
            if slot.disabled_reason
        ],
    }


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def validate_and_export(
    requests_list: list[dict[str, Any]],
    candidates: dict[str, dict[str, str]],
) -> dict[str, Any]:
    latest, completed, _ = load_latest_raw()
    request_by_id = {row["request_id"]: row for row in requests_list}
    validated_records: list[dict[str, Any]] = []
    decisions: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    decided_relation_ids: set[str] = set()
    guard_rejections: Counter[str] = Counter()
    guard_fields, source_groups = load_guard_context(candidates)

    for request_id in sorted(request_by_id):
        raw = latest.get(request_id)
        if not raw or request_id not in completed:
            continue
        try:
            parsed = parse_and_validate_response(
                str(raw["response_text"]), request_by_id[request_id], candidates
            )
        except ValueError as exc:
            errors.append({"request_id": request_id, "stage": "validation", "error": str(exc)})
            continue
        guarded_relations: list[dict[str, Any]] = []
        for relation in parsed["relations"]:
            guarded = dict(relation)
            if guarded["keep"]:
                guard_reason = deterministic_guard_reason(
                    candidates[guarded["relation_id"]], guard_fields, source_groups
                )
                if guard_reason:
                    guard_rejections[guard_reason] += 1
                    guarded.update(
                        {
                            "keep": False,
                            "evidence": "",
                            "confidence": min(float(guarded["confidence"]), 0.2),
                            "reason": guard_reason,
                        }
                    )
            guarded_relations.append(guarded)
        parsed["relations"] = guarded_relations
        validated_records.append(
            {
                "request_id": request_id,
                "chunk_id": parsed["chunk_id"],
                "relations": parsed["relations"],
                "provider": raw.get("provider", ""),
                "model": raw.get("model", ""),
            }
        )
        for decision in parsed["relations"]:
            relation_id = decision["relation_id"]
            if relation_id in decided_relation_ids:
                errors.append(
                    {"request_id": request_id, "stage": "validation", "error": f"Duplicate decision: {relation_id}"}
                )
                continue
            decided_relation_ids.add(relation_id)
            candidate = candidates[relation_id]
            decisions.append(
                {
                    "relation_id": relation_id,
                    "chunk_id": candidate["chunk_id"],
                    "qa_id": candidate["qa_id"],
                    "source_row_number": candidate["source_row_number"],
                    "candidate_relation_type": candidate["candidate_relation_type"],
                    "validated_relation_type": decision["relation_type"],
                    "keep": str(decision["keep"]).lower(),
                    "source_entity_id": candidate["source_entity_id"],
                    "source_name": candidate["source_name"],
                    "source_type": candidate["source_type"],
                    "target_entity_id": candidate["target_entity_id"],
                    "target_name": candidate["target_name"],
                    "target_type": candidate["target_type"],
                    "evidence": decision["evidence"],
                    "confidence": f"{decision['confidence']:.3f}",
                    "reason": decision["reason"],
                    "provider": raw.get("provider", ""),
                    "model": raw.get("model", ""),
                    "graph_version": GRAPH_VERSION,
                }
            )

    kept = [row for row in decisions if row["keep"] == "true"]
    bidirectional: list[dict[str, Any]] = []
    for row in kept:
        direct = dict(row)
        direct.update(
            {
                "edge_id": row["relation_id"],
                "source_relation_id": row["relation_id"],
                "graph_relation_type": row["validated_relation_type"],
                "direction": "direct",
            }
        )
        bidirectional.append(direct)
        inverse = dict(row)
        inverse.update(
            {
                "edge_id": row["relation_id"] + "__inverse",
                "source_relation_id": row["relation_id"],
                "graph_relation_type": INVERSE_RELATION_TYPES[row["validated_relation_type"]],
                "direction": "inverse",
                "source_entity_id": row["target_entity_id"],
                "source_name": row["target_name"],
                "source_type": row["target_type"],
                "target_entity_id": row["source_entity_id"],
                "target_name": row["source_name"],
                "target_type": row["source_type"],
            }
        )
        bidirectional.append(inverse)

    with VALIDATED_JSONL.open("w", encoding="utf-8") as handle:
        for row in validated_records:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    decision_fields = [
        "relation_id", "chunk_id", "qa_id", "source_row_number",
        "candidate_relation_type", "validated_relation_type", "keep",
        "source_entity_id", "source_name", "source_type", "target_entity_id",
        "target_name", "target_type", "evidence", "confidence", "reason",
        "provider", "model", "graph_version",
    ]
    write_csv(DECISIONS_CSV, decisions, decision_fields)
    write_csv(RELATIONS_CSV, kept, decision_fields)
    write_csv(
        BIDIRECTIONAL_CSV,
        bidirectional,
        decision_fields + ["edge_id", "source_relation_id", "graph_relation_type", "direction"],
    )
    write_csv(ERRORS_CSV, errors, ["request_id", "stage", "error"])
    return {
        "validated_requests": len(validated_records),
        "relation_decisions": len(decisions),
        "kept_relations": len(kept),
        "bidirectional_relations": len(bidirectional),
        "validation_errors": len(errors),
        "candidate_decisions_missing": len(candidates) - len(decided_relation_ids),
        "deterministic_guard_rejections": sum(guard_rejections.values()),
        "deterministic_guard_rejections_by_reason": dict(sorted(guard_rejections.items())),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--run-live", action="store_true")
    mode.add_argument("--validate-existing", action="store_true")
    parser.add_argument("--models", default="openai/gpt-oss-20b,openai/gpt-oss-120b")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--sleep-seconds", type=float, default=3.0)
    parser.add_argument("--max-completion-tokens", type=int, default=3000)
    parser.add_argument(
        "--revalidate-models",
        default="",
        help=(
            "Comma-separated source model IDs whose successful cached requests "
            "must be replaced. Empty by default."
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if args.limit < 0 or args.sleep_seconds < 0:
        raise ValueError("--limit and --sleep-seconds must be non-negative.")
    if args.max_completion_tokens < 1200:
        raise ValueError("--max-completion-tokens must be at least 1200.")
    RELATION_DIR.mkdir(parents=True, exist_ok=True)
    requests_list = read_jsonl(REQUESTS_JSONL)
    candidates = read_candidates()
    live_summary: dict[str, Any] = {}
    if args.run_live:
        models = [value.strip() for value in args.models.split(",") if value.strip()]
        revalidate_models = {
            value.strip()
            for value in args.revalidate_models.split(",")
            if value.strip()
        }
        if not models:
            raise ValueError("At least one model is required.")
        live_summary = run_live(
            requests_list,
            candidates,
            models=models,
            limit=args.limit,
            sleep_seconds=args.sleep_seconds,
            max_completion_tokens=args.max_completion_tokens,
            revalidate_models=revalidate_models,
        )
    exports = validate_and_export(requests_list, candidates)
    _, completed, errored = load_latest_raw()
    manifest = {
        "graph_version": GRAPH_VERSION,
        "total_requests": len(requests_list),
        "completed_requests": len(completed),
        "remaining_requests": len(requests_list) - len(completed),
        "errored_requests": len(errored),
        "candidate_relations": len(candidates),
        "live_run": live_summary,
        "exports": exports,
        "decision_types": dict(Counter(row["candidate_relation_type"] for row in candidates.values())),
        "updated_at_utc": datetime.now(timezone.utc).isoformat(),
        "secrets_persisted": False,
    }
    MANIFEST_JSON.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0 if not live_summary.get("stopped_reason") else 2


if __name__ == "__main__":
    raise SystemExit(main())
