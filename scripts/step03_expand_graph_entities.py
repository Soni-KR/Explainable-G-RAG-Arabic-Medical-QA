from __future__ import annotations

"""Resume the colleague Step 3 expansion with safe provider rotation.

The colleague checkout is treated as read-only provenance. This runner imports
its prompt, validation, canonicalization, and CSV export functions, while all
new caches and outputs are written under ``outputs/graph_expansion_v2``.
"""

import argparse
import contextlib
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import shutil
import sys
import time
from typing import Any

import requests


ROOT = Path(__file__).resolve().parents[1]
COLLEAGUE_ROOT = ROOT / "aziza-trial"
COLLEAGUE_SCRIPT = COLLEAGUE_ROOT / "scripts" / "step03_extract_entities.py"
SOURCE_CHUNKS = (
    COLLEAGUE_ROOT
    / "outputs"
    / "02_chunking"
    / "ahd_chunks_10000_expansion_v1.jsonl"
)
SOURCE_RAW_CACHE = (
    COLLEAGUE_ROOT
    / "outputs"
    / "03_entity_extraction"
    / "ahd_llm_entity_extraction_raw_responses_expansion_v1.jsonl"
)

EXPANSION_ROOT = ROOT / "outputs" / "graph_expansion_v2"
ENTITY_DIR = EXPANSION_ROOT / "03_entity_extraction"
REPORT_DIR = EXPANSION_ROOT / "reports"
RAW_RESPONSES = ENTITY_DIR / "entity_extraction_raw.jsonl"
VALIDATED = ENTITY_DIR / "entity_extraction_validated.jsonl"
ENTITIES = ENTITY_DIR / "entities_expansion.csv"
MENTIONS = ENTITY_DIR / "entity_mentions_expansion.csv"
ALIASES = ENTITY_DIR / "entity_aliases_expansion.csv"
ERRORS = ENTITY_DIR / "entity_extraction_errors.csv"
PROGRESS = ENTITY_DIR / "progress.json"
MANIFEST = ENTITY_DIR / "manifest.json"

DEFAULT_MODELS = "openai/gpt-oss-20b"
SAFE_RATE_HEADERS = {
    "retry-after",
    "x-ratelimit-limit-requests",
    "x-ratelimit-limit-tokens",
    "x-ratelimit-remaining-requests",
    "x-ratelimit-remaining-tokens",
    "x-ratelimit-reset-requests",
    "x-ratelimit-reset-tokens",
}


def load_colleague_module():
    if not COLLEAGUE_SCRIPT.exists():
        raise FileNotFoundError(COLLEAGUE_SCRIPT)
    spec = importlib.util.spec_from_file_location(
        "aziza_step03_expansion",
        COLLEAGUE_SCRIPT,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load the colleague Step 3 module.")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # Reuse the colleague implementation, but redirect every writable path.
    module.CHUNKS_JSONL = SOURCE_CHUNKS
    module.ENTITY_DIR = ENTITY_DIR
    module.REPORTS_DIR = REPORT_DIR
    module.REQUESTS_JSONL = ENTITY_DIR / "_temporary_requests.jsonl"
    module.RAW_RESPONSES_JSONL = RAW_RESPONSES
    module.VALIDATED_JSONL = VALIDATED
    module.ENTITIES_CSV = ENTITIES
    module.MENTIONS_CSV = MENTIONS
    module.ALIASES_CSV = ALIASES
    module.ERRORS_CSV = ERRORS
    module.REPORT_MD = REPORT_DIR / "step03_entity_extraction.md"
    module.PROGRESS_JSON = PROGRESS
    module.ENV_FILE = COLLEAGUE_ROOT / ".env"
    # Observed smoke-test context words are not graph entities. Keep this
    # deterministic guard outside the frozen colleague source.
    module.CONTEXT_ONLY_TERMS.update(
        {
            "الشمس",
            "البرودة",
            "البرد",
            "الإضاءة",
        }
    )
    module.CONTEXT_ONLY_TERMS.update(
        {
            "\u0627\u0644\u062f\u0648\u0631\u0629 \u0627\u0644\u0634\u0647\u0631\u064a\u0629",  # normal menstruation
            "\u0627\u0644\u062a\u0628\u0648\u064a\u0636",  # normal ovulation
        }
    )
    module.BODY_PART_ONLY_TERMS.update(
        {
            "\u063a\u062f\u0629 \u0627\u0644\u0628\u0627\u0631\u062b\u0648\u0644\u064a\u0646",
            "\u063a\u062f\u0629 \u0628\u0627\u0631\u062b\u0648\u0644\u064a\u0646",
        }
    )
    module.FORCED_TYPE_OVERRIDES.update(
        {
            "\u0627\u0644\u0625\u062c\u0647\u0627\u0636": "DiseaseCondition",
            "\u0625\u062c\u0647\u0627\u0636": "DiseaseCondition",
        }
    )
    module.BROAD_LOW_QUALITY_TREATMENTS.update(
        {
            "\u0639\u0645\u0644\u064a\u0629 \u062c\u0631\u0627\u062d\u064a\u0629",
            "\u0634\u0627\u064a \u0627\u0644\u0643\u0631\u0627\u0648\u064a\u0629",
            "\u0634\u0627\u064a \u0627\u0644\u0646\u0639\u0646\u0627\u0639",
            "\u0639\u0633\u0644 \u0627\u0644\u0645\u0644\u0643\u0627\u062a",
        }
    )
    improve_colleague_prompt(module)
    # A failed retry must not hide a previously successful extraction. The
    # colleague script chooses the latest record regardless of status, so use
    # success-preserving cache readers for the resumable expansion.
    module.load_existing_raw_responses = load_existing_raw_responses_keep_success
    module.validate_raw_responses = lambda chunk_lookup: validate_raw_responses_keep_success(
        module, chunk_lookup
    )
    return module


def improve_colleague_prompt(module: Any) -> None:
    """Remove corrupted examples and add compact, conservative Arabic rules."""

    original_make_messages = module.make_messages

    def make_messages(chunk: dict[str, Any]) -> list[dict[str, str]]:
        messages = original_make_messages(chunk)
        payload = json.loads(messages[1]["content"])
        rules = [
            str(rule)
            for rule in payload.get("rules", [])
            if "Ø" not in str(rule) and "Ù" not in str(rule)
        ]
        rules.extend(
            [
                "Normalize only Arabic orthographic variants while preserving the explicit medical meaning.",
                "DiseaseCondition examples: \u062d\u0633\u0627\u0633\u064a\u0629, \u0631\u0628\u0648, \u0627\u0644\u062a\u0647\u0627\u0628, \u0646\u0632\u0644\u0629 \u0645\u0639\u0648\u064a\u0629.",
                "Symptom examples: \u062d\u0643\u0629, \u0633\u0639\u0627\u0644, \u0628\u0644\u063a\u0645, \u0636\u064a\u0642 \u062a\u0646\u0641\u0633, \u062a\u0639\u0628, \u0635\u062f\u0627\u0639.",
                "Test examples: \u062a\u062d\u0644\u064a\u0644 \u0627\u0644\u062d\u0633\u0627\u0633\u064a\u0629, RAST, \u062a\u062d\u0627\u0644\u064a\u0644 \u0645\u062e\u0628\u0631\u064a\u0629, \u0633\u0648\u0646\u0627\u0631.",
                "Ignore normal physiological processes and anatomy alone, including \u0627\u0644\u062f\u0648\u0631\u0629 \u0627\u0644\u0634\u0647\u0631\u064a\u0629, \u0627\u0644\u062a\u0628\u0648\u064a\u0636, and named glands, unless an abnormal condition is explicitly stated.",
                "Classify \u0627\u0644\u0625\u062c\u0647\u0627\u0636 as DiseaseCondition unless the text explicitly names a termination procedure as treatment.",
                "Use at most one mention per entity per QA field and keep evidence to the shortest supporting phrase, no more than 220 characters.",
                "Never emit duplicate canonical_name and entity_type pairs.",
            ]
        )
        payload["rules"] = rules
        messages[1]["content"] = json.dumps(payload, ensure_ascii=False)
        return messages

    module.make_messages = make_messages


def authoritative_raw_records(
    path: Path = RAW_RESPONSES,
) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    """Return all records and one authoritative record per chunk.

    The newest successful non-empty response wins. A newer error remains in
    the append-only audit log but cannot erase that success. For chunks with no
    success, the newest error remains authoritative and eligible for retry.
    """

    records: list[dict[str, Any]] = []
    latest_by_chunk: dict[str, dict[str, Any]] = {}
    latest_success_by_chunk: dict[str, dict[str, Any]] = {}
    if not path.exists():
        return records, {}

    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(record, dict):
                continue
            records.append(record)
            chunk_id = str(record.get("chunk_id", "")).strip()
            if not chunk_id:
                continue
            latest_by_chunk[chunk_id] = record
            if record.get("status") == "ok" and str(
                record.get("response_text", "")
            ).strip():
                latest_success_by_chunk[chunk_id] = record

    authoritative = {
        chunk_id: latest_success_by_chunk.get(chunk_id, latest)
        for chunk_id, latest in latest_by_chunk.items()
    }
    return records, authoritative


def load_existing_raw_responses_keep_success():
    records, authoritative = authoritative_raw_records()
    completed = {
        chunk_id
        for chunk_id, record in authoritative.items()
        if record.get("status") == "ok" and str(record.get("response_text", "")).strip()
    }
    errored = {
        chunk_id
        for chunk_id, record in authoritative.items()
        if chunk_id not in completed and record.get("status") != "ok"
    }
    return records, completed, errored


def validate_raw_responses_keep_success(
    module: Any,
    chunk_lookup: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Validate the newest success for each chunk without losing retry errors."""

    _, authoritative = authoritative_raw_records()
    validated_records: list[dict[str, Any]] = []
    error_rows: list[dict[str, Any]] = []
    for raw in authoritative.values():
        chunk_id = str(raw.get("chunk_id", ""))
        if raw.get("status") != "ok":
            if raw.get("http_status") != 429:
                module.error(
                    error_rows,
                    chunk_id,
                    "model_call",
                    module.format_raw_error(raw),
                )
            continue
        try:
            parsed = module.extract_json_object(raw.get("response_text", ""))
            validated = module.validate_extraction(parsed, chunk_lookup, error_rows)
        except Exception as exc:
            validated = None
            module.error(error_rows, chunk_id, "validation", str(exc))
        if validated:
            validated["provider"] = raw.get("provider", "")
            validated["model"] = raw.get("model", "")
            validated_records.append(validated)

    with module.VALIDATED_JSONL.open("w", encoding="utf-8", newline="\n") as handle:
        for record in validated_records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    return validated_records, error_rows


def read_env_file(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        name = name.strip()
        value = value.strip().strip('"').strip("'")
        if name and name not in os.environ:
            os.environ[name] = value


def natural_key(value: str) -> list[Any]:
    return [int(part) if part.isdigit() else part for part in re.split(r"(\d+)", value)]


def load_api_keys() -> list[str]:
    """Load a deduplicated key ring without logging any secret value."""

    read_env_file(ROOT / ".env")
    read_env_file(COLLEAGUE_ROOT / ".env")
    values: list[str] = []
    packed = os.getenv("GROQ_API_KEYS", "")
    if packed:
        values.extend(re.split(r"[,;\s]+", packed))
    names = sorted(
        (
            name
            for name in os.environ
            if name == "GROQ_API_KEY" or name.startswith("GROQ_API_KEY_")
        ),
        key=natural_key,
    )
    values.extend(os.getenv(name, "") for name in names)

    keys: list[str] = []
    seen: set[str] = set()
    for value in values:
        key = str(value or "").strip()
        if not key or key.lower().startswith("your_") or key in seen:
            continue
        seen.add(key)
        keys.append(key)
    return keys


def key_fingerprint(key: str) -> str:
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:10]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def strict_entity_schema() -> dict[str, Any]:
    mention = {
        "type": "object",
        "properties": {
            "qa_id": {"type": "string"},
            "source_row_number": {"type": ["string", "integer"]},
            "surface_form": {"type": "string"},
            "field": {"type": "string", "enum": ["question", "answer"]},
            "evidence": {"type": "string"},
        },
        "required": [
            "qa_id",
            "source_row_number",
            "surface_form",
            "field",
            "evidence",
        ],
        "additionalProperties": False,
    }
    entity = {
        "type": "object",
        "properties": {
            "local_entity_id": {"type": "string"},
            "canonical_name": {"type": "string"},
            "entity_type": {
                "type": "string",
                "enum": ["DiseaseCondition", "Symptom", "Treatment", "Test"],
            },
            "aliases": {"type": "array", "items": {"type": "string"}},
            "mentions": {"type": "array", "items": mention, "minItems": 1},
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        },
        "required": [
            "local_entity_id",
            "canonical_name",
            "entity_type",
            "aliases",
            "mentions",
            "confidence",
        ],
        "additionalProperties": False,
    }
    return {
        "type": "object",
        "properties": {
            "chunk_id": {"type": "string"},
            "entities": {"type": "array", "items": entity},
        },
        "required": ["chunk_id", "entities"],
        "additionalProperties": False,
    }


@dataclass
class ProviderSlot:
    key: str
    model: str
    fingerprint: str
    cooldown_until: float = 0.0
    disabled_reason: str = ""


class ProviderFailure(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        status: int = 0,
        body: str = "",
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(message)
        self.status = status
        self.body = body
        self.headers = headers or {}


def safe_headers(response: requests.Response) -> dict[str, str]:
    return {
        name.lower(): value
        for name, value in response.headers.items()
        if name.lower() in SAFE_RATE_HEADERS
    }


def request_body(request_record: dict[str, Any]) -> dict[str, Any]:
    model = str(request_record["model"])
    requested_completion_tokens = int(request_record.get("max_completion_tokens", 5000))
    model_completion_cap = 4096 if model == "allam-2-7b" else requested_completion_tokens
    body: dict[str, Any] = {
        "model": model,
        "messages": request_record["messages"],
        "temperature": 0,
        "max_completion_tokens": min(requested_completion_tokens, model_completion_cap),
    }
    if model.startswith("openai/gpt-oss-"):
        body["reasoning_effort"] = "low"
        body["include_reasoning"] = False
        body["response_format"] = {
            "type": "json_schema",
            "json_schema": {
                "name": "arabic_medical_entities",
                "strict": True,
                "schema": strict_entity_schema(),
            },
        }
    else:
        body["response_format"] = {"type": "json_object"}
        if model.startswith("qwen/"):
            body["reasoning_effort"] = "none"
    return body


def call_provider(
    request_record: dict[str, Any],
    key: str,
) -> tuple[str, dict[str, Any], dict[str, str]]:
    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        json=request_body(request_record),
        timeout=120,
    )
    headers = safe_headers(response)
    if response.status_code >= 400:
        raise ProviderFailure(
            f"HTTP {response.status_code}: {response.reason}",
            status=response.status_code,
            body=response.text[:2000],
            headers=headers,
        )
    payload = response.json()
    text = str(payload["choices"][0]["message"]["content"] or "").strip()
    if not text:
        raise ProviderFailure("Provider returned an empty response.")
    return text, dict(payload.get("usage") or {}), headers


def parse_retry_after(headers: dict[str, str]) -> float:
    try:
        return max(1.0, float(headers.get("retry-after", "0") or 0))
    except ValueError:
        return 15.0


def append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
        handle.flush()


def next_available_slot(
    slots: list[ProviderSlot],
    start_index: int,
) -> tuple[int | None, float]:
    now = time.time()
    earliest = 0.0
    for offset in range(len(slots)):
        index = (start_index + offset) % len(slots)
        slot = slots[index]
        if slot.disabled_reason:
            continue
        if slot.cooldown_until <= now:
            return index, 0.0
        if not earliest or slot.cooldown_until < earliest:
            earliest = slot.cooldown_until
    return None, max(0.0, earliest - now) if earliest else 0.0


def disable_key(slots: list[ProviderSlot], fingerprint: str, reason: str) -> None:
    for slot in slots:
        if slot.fingerprint == fingerprint:
            slot.disabled_reason = reason


def disable_model(slots: list[ProviderSlot], model: str, reason: str) -> None:
    for slot in slots:
        if slot.model == model:
            slot.disabled_reason = reason


def failure_payload(exc: ProviderFailure) -> dict[str, Any]:
    return {
        "http_status": exc.status,
        "error": str(exc),
        "error_body": exc.body,
        "rate_limit_headers": exc.headers,
    }


def is_daily_quota(exc: ProviderFailure) -> bool:
    body = exc.body.lower()
    return exc.status == 429 and (
        "tokens per day" in body or "tpd" in body or "requests per day" in body
    )


def configure_module_paths(module: Any) -> None:
    ENTITY_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    module.RAW_RESPONSES_JSONL = RAW_RESPONSES
    module.VALIDATED_JSONL = VALIDATED
    module.ENTITIES_CSV = ENTITIES
    module.MENTIONS_CSV = MENTIONS
    module.ALIASES_CSV = ALIASES
    module.ERRORS_CSV = ERRORS


def reconcile_validated_mentions(
    module: Any,
    validated: list[dict[str, Any]],
    chunks: list[dict[str, Any]],
) -> dict[str, int]:
    """Correct mention provenance from immutable source QA records.

    The LLM extracts the phrase, but it is not authoritative about whether the
    phrase occurred in the question or answer. Only unambiguous source-text
    matches are corrected; phrases present in both fields retain their model
    label. Source row numbers always come from the source QA record.
    """

    qa_lookup: dict[str, dict[str, Any]] = {}
    for chunk in chunks:
        records = module.parse_json(chunk.get("qa_records"), [])
        if not isinstance(records, list):
            continue
        for record in records:
            qa_id = str(record.get("subset_id") or record.get("qa_id") or "").strip()
            if qa_id:
                qa_lookup[qa_id] = record

    field_corrections = 0
    source_row_corrections = 0
    unresolved_fields = 0
    for chunk in validated:
        for entity in chunk.get("entities", []):
            for mention in entity.get("mentions", []):
                qa_id = str(mention.get("qa_id", "")).strip()
                source = qa_lookup.get(qa_id)
                if source is None:
                    unresolved_fields += 1
                    continue
                authoritative_row = str(source.get("source_row_number", "")).strip()
                if authoritative_row and str(mention.get("source_row_number", "")).strip() != authoritative_row:
                    mention["source_row_number"] = authoritative_row
                    source_row_corrections += 1

                question = module.normalize_arabic(source.get("question", ""))
                answer = module.normalize_arabic(source.get("answer", ""))
                evidence = module.normalize_arabic(mention.get("evidence", ""))
                surface = module.normalize_arabic(mention.get("surface_form", ""))
                probe = evidence or surface
                matches: set[str] = set()
                if probe and probe in question:
                    matches.add("question")
                if probe and probe in answer:
                    matches.add("answer")
                if not matches and surface:
                    if surface in question:
                        matches.add("question")
                    if surface in answer:
                        matches.add("answer")
                if len(matches) == 1:
                    authoritative_field = next(iter(matches))
                    if str(mention.get("field", "")).strip().lower() != authoritative_field:
                        mention["field"] = authoritative_field
                        field_corrections += 1
                elif not matches:
                    unresolved_fields += 1
    return {
        "mention_field_corrections": field_corrections,
        "mention_source_row_corrections": source_row_corrections,
        "mention_fields_unresolved_from_source": unresolved_fields,
    }


def validate_and_export(module: Any, chunks: list[dict[str, Any]]) -> dict[str, int]:
    configure_module_paths(module)
    lookup = {str(chunk["chunk_id"]): chunk for chunk in chunks}
    # The colleague validator prints every chunk; keep the production console concise.
    with contextlib.redirect_stdout(io.StringIO()):
        validated, errors = module.validate_raw_responses(lookup)
        provenance_stats = reconcile_validated_mentions(module, validated, chunks)
        with VALIDATED.open("w", encoding="utf-8") as handle:
            for record in validated:
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        entities, mentions, aliases = module.merge_validated_entities(validated)
        module.write_final_outputs(entities, mentions, aliases, errors)
    return {
        "validated_chunks": len(validated),
        "entities": len(entities),
        "mentions": len(mentions),
        "aliases": len(aliases),
        "validation_messages": len(errors),
        **provenance_stats,
    }


def current_completion(module: Any) -> tuple[set[str], set[str]]:
    _, completed, errored = module.load_existing_raw_responses()
    return completed, errored


def write_progress(
    *,
    total_chunks: int,
    completed: int,
    errored: int,
    new_successes: int,
    http_attempts: int,
    last_chunk: str,
    stopped_reason: str,
) -> None:
    payload = {
        "graph_version": "expansion_v2",
        "total_chunks": total_chunks,
        "completed_chunks": completed,
        "remaining_chunks": max(0, total_chunks - completed),
        "completion_percent": round(100.0 * completed / total_chunks, 2),
        "latest_run_new_successes": new_successes,
        "latest_run_http_attempts": http_attempts,
        "latest_run_errored_chunks": errored,
        "last_chunk": last_chunk,
        "stopped_reason": stopped_reason,
        "updated_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    PROGRESS.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def initialize_cache() -> None:
    ENTITY_DIR.mkdir(parents=True, exist_ok=True)
    if RAW_RESPONSES.exists():
        raise FileExistsError(
            f"Expansion cache already exists and will not be overwritten: {RAW_RESPONSES}"
        )
    if not SOURCE_RAW_CACHE.exists():
        raise FileNotFoundError(SOURCE_RAW_CACHE)
    shutil.copy2(SOURCE_RAW_CACHE, RAW_RESPONSES)


def split_chunk_for_provider(
    module: Any,
    chunk: dict[str, Any],
    *,
    max_compact_chars: int = 6000,
) -> list[dict[str, Any]]:
    """Split only long chunks at QA boundaries while preserving the chunk ID."""
    qa_records = module.parse_json(chunk.get("qa_records"), [])
    if not isinstance(qa_records, list) or len(qa_records) <= 1:
        return [chunk]

    groups: list[list[dict[str, Any]]] = []
    current: list[dict[str, Any]] = []
    current_chars = 0
    for record in qa_records:
        compact = module.compact_qa_records_for_prompt([record])
        record_chars = len(json.dumps(compact, ensure_ascii=False))
        if current and current_chars + record_chars > max_compact_chars:
            groups.append(current)
            current = []
            current_chars = 0
        current.append(record)
        current_chars += record_chars
    if current:
        groups.append(current)
    if len(groups) == 1:
        return [chunk]

    parts: list[dict[str, Any]] = []
    for group in groups:
        part = dict(chunk)
        part["qa_records"] = group
        part["qa_ids"] = [record.get("subset_id", "") for record in group]
        part["source_row_numbers"] = [
            record.get("source_row_number", "") for record in group
        ]
        parts.append(part)
    return parts


def add_usage(total: dict[str, int], usage: dict[str, Any]) -> None:
    for name in ("prompt_tokens", "completion_tokens", "total_tokens"):
        try:
            total[name] = total.get(name, 0) + int(usage.get(name, 0) or 0)
        except (TypeError, ValueError):
            continue


def run_live(
    module: Any,
    chunks: list[dict[str, Any]],
    *,
    models: list[str],
    limit: int,
    sleep_seconds: float,
    max_completion_tokens: int,
    max_compact_chars: int,
    only_chunk_ids: set[str] | None = None,
    force_reprocess: bool = False,
) -> dict[str, Any]:
    keys = load_api_keys()
    if not keys:
        raise RuntimeError(
            "No Groq key was loaded. Set GROQ_API_KEY or GROQ_API_KEYS privately."
        )
    slots = [
        ProviderSlot(
            key=key,
            model=model,
            fingerprint=key_fingerprint(key),
        )
        for key in keys
        for model in models
    ]
    completed, errored_ids = current_completion(module)
    selected = list(chunks) if force_reprocess else [
        chunk for chunk in chunks if str(chunk["chunk_id"]) not in completed
    ]
    if only_chunk_ids:
        selected = [
            chunk for chunk in selected if str(chunk["chunk_id"]) in only_chunk_ids
        ]
    if limit > 0:
        selected = selected[:limit]

    new_successes = 0
    http_attempts = 0
    slot_cursor = 0
    stopped_reason = ""
    last_chunk = ""
    for position, chunk in enumerate(selected, start=1):
        chunk_id = str(chunk["chunk_id"])
        last_chunk = chunk_id
        attempts: list[dict[str, Any]] = []
        success_record: dict[str, Any] | None = None
        chunk_started = time.perf_counter()
        parts = split_chunk_for_provider(
            module,
            chunk,
            max_compact_chars=max_compact_chars,
        )
        combined_entities: list[dict[str, Any]] = []
        combined_usage: dict[str, int] = {}
        successful_models: list[str] = []
        successful_fingerprints: list[str] = []
        last_headers: dict[str, str] = {}
        all_parts_succeeded = True

        for part_index, part in enumerate(parts, start=1):
            part_succeeded = False
            part_completion_tokens = min(
                max_completion_tokens,
                3000 if len(parts) > 1 else max_completion_tokens,
            )
            # TPM cooldowns and an occasional malformed JSON response can both
            # consume real provider attempts. Keep retrying this same chunk so
            # a transient failure does not force a new process invocation.
            max_attempts = max(10, len(slots) * 5)
            provider_attempts = 0
            idle_waits = 0
            while provider_attempts < max_attempts:
                slot_index, wait_seconds = next_available_slot(slots, slot_cursor)
                if slot_index is None:
                    if wait_seconds and wait_seconds <= 120 and idle_waits < 12:
                        time.sleep(wait_seconds + 1.0)
                        idle_waits += 1
                        continue
                    stopped_reason = "all_provider_slots_exhausted"
                    break
                slot = slots[slot_index]
                slot_cursor = (slot_index + 1) % len(slots)
                request_record = module.make_request_record(part, "groq", slot.model)
                request_record["max_completion_tokens"] = part_completion_tokens
                provider_attempts += 1
                http_attempts += 1
                try:
                    response_text, usage, headers = call_provider(
                        request_record,
                        slot.key,
                    )
                    parsed = module.extract_json_object(response_text)
                    entities = parsed.get("entities", []) if isinstance(parsed, dict) else []
                    if not isinstance(entities, list):
                        raise ValueError("Provider response entities must be a list.")
                    for entity in entities:
                        if isinstance(entity, dict):
                            entity = dict(entity)
                            entity["local_entity_id"] = (
                                f"P{part_index}_{entity.get('local_entity_id', '')}"
                            )
                            combined_entities.append(entity)
                    add_usage(combined_usage, usage)
                    successful_models.append(slot.model)
                    successful_fingerprints.append(slot.fingerprint)
                    last_headers = headers
                    part_succeeded = True
                    break
                except ValueError as exc:
                    attempts.append(
                        {
                            "part_index": part_index,
                            "model": slot.model,
                            "key_fingerprint": slot.fingerprint,
                            "http_status": 422,
                            "error": str(exc)[:1000],
                        }
                    )
                    continue
                except ProviderFailure as exc:
                    detail = {
                        "part_index": part_index,
                        "model": slot.model,
                        "key_fingerprint": slot.fingerprint,
                        **failure_payload(exc),
                    }
                    attempts.append(detail)
                    if is_daily_quota(exc):
                        slot.disabled_reason = "daily_quota"
                        continue
                    if exc.status == 429:
                        slot.cooldown_until = time.time() + parse_retry_after(exc.headers)
                        continue
                    if exc.status == 413:
                        if part_completion_tokens > 2200:
                            part_completion_tokens -= 500
                            continue
                        stopped_reason = "request_too_large_after_partition"
                        break
                    if exc.status == 401:
                        disable_key(slots, slot.fingerprint, "authentication_failed")
                        continue
                    if exc.status == 403:
                        slot.disabled_reason = "model_not_permitted"
                        continue
                    if exc.status in {404, 410}:
                        disable_model(slots, slot.model, "model_unavailable")
                        continue
                    if exc.status == 400 and "json_validate_failed" in exc.body:
                        continue
                    if exc.status >= 500 or exc.status == 0:
                        slot.cooldown_until = time.time() + 10.0
                        continue
                    stopped_reason = f"non_retryable_http_{exc.status}"
                    break
                except requests.RequestException as exc:
                    attempts.append(
                        {
                            "part_index": part_index,
                            "model": slot.model,
                            "key_fingerprint": slot.fingerprint,
                            "http_status": 0,
                            "error": str(exc),
                        }
                    )
                    slot.cooldown_until = time.time() + 10.0

            if not part_succeeded:
                if not stopped_reason:
                    stopped_reason = "provider_retry_budget_exhausted"
                all_parts_succeeded = False
                break

        if all_parts_succeeded:
            success_record = {
                "request_id": f"entity_request_{chunk_id}",
                "chunk_id": chunk_id,
                "provider": "groq",
                "model": "|".join(dict.fromkeys(successful_models)),
                "key_fingerprint": "|".join(
                    dict.fromkeys(successful_fingerprints)
                ),
                "status": "ok",
                "error": "",
                "http_status": 200,
                "rate_limit_headers": last_headers,
                "usage": combined_usage,
                "request_parts": len(parts),
                "attempts_before_success": attempts,
                "latency_ms": round(
                    (time.perf_counter() - chunk_started) * 1000.0,
                    3,
                ),
                "response_text": json.dumps(
                    {"chunk_id": chunk_id, "entities": combined_entities},
                    ensure_ascii=False,
                ),
            }

        if success_record is None:
            append_jsonl(
                RAW_RESPONSES,
                {
                    "request_id": f"entity_request_{chunk_id}",
                    "chunk_id": chunk_id,
                    "provider": "groq",
                    "model": "",
                    "status": "error",
                    "error": stopped_reason or "provider_slots_exhausted_for_chunk",
                    "attempts": attempts,
                    "response_text": "",
                },
            )
            break

        append_jsonl(RAW_RESPONSES, success_record)
        new_successes += 1
        completed.add(chunk_id)
        errored_ids.discard(chunk_id)
        write_progress(
            total_chunks=len(chunks),
            completed=len(completed),
            errored=len(errored_ids),
            new_successes=new_successes,
            http_attempts=http_attempts,
            last_chunk=chunk_id,
            stopped_reason="",
        )
        print(
            json.dumps(
                {
                    "progress": f"{position}/{len(selected)}",
                    "chunk_id": chunk_id,
                    "model": success_record["model"],
                    "completed_total": len(completed),
                    "remaining_total": len(chunks) - len(completed),
                },
                ensure_ascii=False,
            ),
            flush=True,
        )
        if sleep_seconds > 0:
            time.sleep(sleep_seconds)

    completed, errored_ids = current_completion(module)
    write_progress(
        total_chunks=len(chunks),
        completed=len(completed),
        errored=len(errored_ids),
        new_successes=new_successes,
        http_attempts=http_attempts,
        last_chunk=last_chunk,
        stopped_reason=stopped_reason,
    )
    return {
        "keys_loaded": len(keys),
        "key_fingerprints": [key_fingerprint(key) for key in keys],
        "models": models,
        "new_successes": new_successes,
        "http_attempts": http_attempts,
        "completed_chunks": len(completed),
        "remaining_chunks": len(chunks) - len(completed),
        "errored_chunks": len(errored_ids),
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Complete expansion-v2 Arabic medical entity extraction."
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--initialize-cache", action="store_true")
    mode.add_argument("--validate-existing", action="store_true")
    mode.add_argument("--run-live", action="store_true")
    parser.add_argument(
        "--models",
        default=DEFAULT_MODELS,
        help="Comma-separated Groq model IDs used as independent quota slots.",
    )
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--sleep-seconds", type=float, default=3.0)
    parser.add_argument(
        "--max-completion-tokens",
        type=int,
        default=3600,
        help="Per-request completion reservation; lower values improve TPM throughput.",
    )
    parser.add_argument(
        "--max-compact-chars",
        type=int,
        default=6000,
        help="Split long chunks at QA boundaries before provider submission.",
    )
    parser.add_argument(
        "--only-chunk-ids",
        default="",
        help="Comma-separated chunk IDs for a targeted run.",
    )
    parser.add_argument(
        "--force-reprocess",
        action="store_true",
        help="Reprocess targeted IDs even if a successful cache record exists.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if args.limit < 0 or args.sleep_seconds < 0:
        raise ValueError("--limit and --sleep-seconds must be non-negative.")
    if args.max_completion_tokens < 2200:
        raise ValueError("--max-completion-tokens must be at least 2200.")
    if args.max_compact_chars < 1000:
        raise ValueError("--max-compact-chars must be at least 1000.")
    only_chunk_ids = {
        value.strip() for value in args.only_chunk_ids.split(",") if value.strip()
    }
    if args.force_reprocess and not only_chunk_ids:
        raise ValueError("--force-reprocess requires --only-chunk-ids.")
    module = load_colleague_module()
    configure_module_paths(module)
    chunks = module.load_chunks()
    if args.initialize_cache:
        initialize_cache()
        print(
            json.dumps(
                {
                    "status": "initialized",
                    "source_cache": str(SOURCE_RAW_CACHE.relative_to(ROOT)),
                    "destination_cache": str(RAW_RESPONSES.relative_to(ROOT)),
                },
                indent=2,
            )
        )
        return 0

    live_summary: dict[str, Any] = {}
    if args.run_live:
        models = [
            value.strip()
            for value in args.models.split(",")
            if value.strip()
        ]
        if not models:
            raise ValueError("At least one model ID is required.")
        live_summary = run_live(
            module,
            chunks,
            models=models,
            limit=args.limit,
            sleep_seconds=args.sleep_seconds,
            max_completion_tokens=args.max_completion_tokens,
            max_compact_chars=args.max_compact_chars,
            only_chunk_ids=only_chunk_ids,
            force_reprocess=args.force_reprocess,
        )

    export_summary = validate_and_export(module, chunks)
    completed, errored = current_completion(module)
    manifest = {
        "graph_expansion_version": "expansion_v2",
        "source_pipeline": "aziza-trial Steps 1-3 expansion_v1",
        "source_chunks": str(SOURCE_CHUNKS.relative_to(ROOT)),
        "source_chunks_sha256": sha256(SOURCE_CHUNKS),
        "total_chunks": len(chunks),
        "completed_chunks": len(completed),
        "remaining_chunks": len(chunks) - len(completed),
        "errored_chunks": len(errored),
        "live_run": live_summary,
        "exports": export_summary,
        "updated_at_utc": datetime.now(timezone.utc).isoformat(),
        "secrets_persisted": False,
    }
    MANIFEST.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0 if not live_summary.get("stopped_reason") else 2


if __name__ == "__main__":
    raise SystemExit(main())
