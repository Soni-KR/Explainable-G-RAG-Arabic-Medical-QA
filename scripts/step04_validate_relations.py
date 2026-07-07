import argparse
import csv
import json
import os
import sys
import time
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent if SCRIPT_DIR.name == "scripts" else SCRIPT_DIR
RELATION_DIR = BASE_DIR / "outputs" / "04_relation_extraction"
REPORTS_DIR = BASE_DIR / "reports"

ENV_FILE = BASE_DIR / ".env"
REQUESTS_JSONL = RELATION_DIR / "ahd_llm_relation_extraction_requests.jsonl"
CANDIDATES_CSV = RELATION_DIR / "ahd_relation_candidates_seed.csv"
RAW_RESPONSES_JSONL = RELATION_DIR / "ahd_llm_relation_validation_raw_responses.jsonl"
VALIDATED_JSONL = RELATION_DIR / "ahd_llm_relation_validation_validated.jsonl"
RELATIONS_CSV = RELATION_DIR / "ahd_relations_llm_validated.csv"
BIDIRECTIONAL_RELATIONS_CSV = RELATION_DIR / "ahd_relations_neo4j_bidirectional.csv"
DECISIONS_CSV = RELATION_DIR / "ahd_relation_validation_decisions.csv"
ERRORS_CSV = RELATION_DIR / "ahd_relation_validation_errors.csv"
REPORT_MD = REPORTS_DIR / "ahd_relation_validation_report.md"

DEFAULT_PROVIDER = "groq"
DEFAULT_GROQ_MODEL = "qwen/qwen3-32b"
MAX_MODEL_CALL_RETRIES = 1
MAX_RETRY_WAIT_SECONDS = 60

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


def relpath(path):
    return path.relative_to(BASE_DIR).as_posix()


def load_env_file(path=ENV_FILE):
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def read_jsonl(path):
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_candidates():
    candidates = {}
    with CANDIDATES_CSV.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            candidates[row["relation_id"]] = row
    return candidates


def select_requests(requests, args, completed_request_ids):
    if args.batch_size > 0:
        candidates = requests[args.batch_start : args.batch_start + args.batch_size]
    elif args.limit_requests > 0:
        candidates = requests[: args.limit_requests]
    else:
        candidates = requests
    if args.resume:
        selected = [request for request in candidates if request["request_id"] not in completed_request_ids]
    else:
        selected = candidates
    return candidates, selected


def load_existing_raw():
    records = read_jsonl(RAW_RESPONSES_JSONL)
    latest = {}
    for record in records:
        request_id = record.get("request_id", "")
        if request_id:
            latest[request_id] = record
    completed = {
        request_id
        for request_id, record in latest.items()
        if record.get("status") == "ok" and str(record.get("response_text", "")).strip()
    }
    errored = {request_id for request_id, record in latest.items() if request_id not in completed and record.get("status") != "ok"}
    return records, completed, errored


def truncate_text(value, limit=1600):
    value = str(value or "")
    return value if len(value) <= limit else value[:limit] + "...[truncated]"


def make_messages(request_record):
    compact_contexts = []
    for qa_context in request_record.get("qa_contexts", []):
        compact_contexts.append(
            {
                "qa_id": qa_context.get("qa_id", ""),
                "entities": [
                    {
                        "entity_id": entity.get("entity_id", ""),
                        "canonical_name": entity.get("canonical_name", ""),
                        "entity_type": entity.get("entity_type", ""),
                        "evidence": truncate_text(entity.get("evidence", ""), 700),
                    }
                    for entity in qa_context.get("entities", [])
                ],
                "candidate_pairs": qa_context.get("candidate_pairs", []),
            }
        )
    payload = {
        "task": "Strict Arabic medical relation validation for Graph-RAG Step 4.",
        "chunk_id": request_record["chunk_id"],
        "allowed_relation_types": sorted(ALLOWED_RELATION_TYPES),
        "rules": [
            "Keep a relation only if the QA evidence directly supports the source-target relation.",
            "Reject if entities only co-occur in the same QA.",
            "Reject if the treatment is background medication, allergen, trigger, or patient history rather than a recommended/causal treatment.",
            "Reject if the test is only generic advice and not linked to the source condition/symptom.",
            "Reject directionally wrong relations.",
            "Do not create new entities or relation_ids.",
            "Return every candidate relation_id with keep true or false.",
            "Return valid JSON only.",
        ],
        "qa_contexts": compact_contexts,
        "required_schema": {
            "chunk_id": request_record["chunk_id"],
            "relations": [
                {
                    "relation_id": "existing relation_id",
                    "keep": True,
                    "relation_type": "HAS_SYMPTOM|TREATED_BY|DIAGNOSED_BY|INVESTIGATED_BY",
                    "evidence": "short evidence phrase",
                    "confidence": 0.85,
                    "reason": "brief reason",
                }
            ],
        },
    }
    return [
        {"role": "system", "content": "You are a strict medical relation validator. Return JSON only."},
        {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
    ]


def call_groq(request_record, api_key, model):
    body = {
        "model": model,
        "messages": make_messages(request_record),
        "temperature": 0,
        "response_format": {"type": "json_object"},
    }
    req = urllib.request.Request(
        "https://api.groq.com/openai/v1/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "AHD-GraphRAG/0.1",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return payload["choices"][0]["message"]["content"]


def collect_http_error_details(exc):
    try:
        body = exc.read().decode("utf-8", errors="replace")
    except Exception:
        body = ""
    headers = dict(exc.headers.items()) if exc.headers else {}
    return {
        "http_status": exc.code,
        "http_reason": exc.reason,
        "error_body": truncate_text(body, 2000),
        "retry_after": headers.get("Retry-After", ""),
        "rate_limit_headers": {key: value for key, value in headers.items() if key.lower().startswith("x-ratelimit")},
    }


def run_live_requests(requests, args):
    if args.provider != "groq":
        raise RuntimeError("Only --provider groq is implemented for Step 4 relation validation.")
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or api_key.lower().startswith("your_"):
        raise RuntimeError("GROQ_API_KEY is not set in .env")

    calls_made = 0
    stopped_on_rate_limit = False
    mode = "a" if args.resume or args.append_raw else "w"
    with RAW_RESPONSES_JSONL.open(mode, encoding="utf-8") as handle:
        for index, request_record in enumerate(requests, start=1):
            status = "error"
            response_text = ""
            call_error = ""
            http_details = {}
            for attempt in range(MAX_MODEL_CALL_RETRIES + 1):
                try:
                    response_text = call_groq(request_record, api_key, args.model)
                    status = "ok"
                    call_error = ""
                    http_details = {}
                    break
                except urllib.error.HTTPError as exc:
                    http_details = collect_http_error_details(exc)
                    call_error = f"HTTP Error {exc.code}: {exc.reason}"
                    if exc.code == 429 and args.stop_on_rate_limit:
                        stopped_on_rate_limit = True
                        break
                    if exc.code == 429 and attempt < MAX_MODEL_CALL_RETRIES:
                        try:
                            wait_seconds = float(http_details.get("retry_after") or 0)
                        except ValueError:
                            wait_seconds = 0
                        wait_seconds = min(max(wait_seconds, args.sleep_seconds, 30), MAX_RETRY_WAIT_SECONDS)
                        time.sleep(wait_seconds)
                        continue
                    break
                except Exception as exc:
                    call_error = str(exc)
                    break
            handle.write(
                json.dumps(
                    {
                        "request_id": request_record["request_id"],
                        "chunk_id": request_record["chunk_id"],
                        "provider": args.provider,
                        "model": args.model,
                        "status": status,
                        "error": call_error,
                        **http_details,
                        "response_text": response_text,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
            calls_made += 1
            if stopped_on_rate_limit:
                break
            if index < len(requests) and args.sleep_seconds:
                time.sleep(args.sleep_seconds)
    return calls_made, stopped_on_rate_limit


def extract_json_object(text):
    text = str(text or "").strip()
    if text.startswith("```"):
        text = text.strip("`").strip()
        if text.startswith("json"):
            text = text[4:].strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            return json.loads(text[start : end + 1])
    raise ValueError("Could not parse JSON object")


def format_raw_error(raw):
    parts = [raw.get("error", "unknown error")]
    if raw.get("http_status"):
        parts.append(f"HTTP status: {raw.get('http_status')}")
    if raw.get("rate_limit_headers"):
        parts.append(f"x-ratelimit headers: {json.dumps(raw.get('rate_limit_headers'), ensure_ascii=False)}")
    if raw.get("error_body"):
        parts.append(f"body: {truncate_text(raw.get('error_body'), 1000)}")
    return " | ".join(part for part in parts if part)


def make_bidirectional_rows(kept_rows):
    rows = []
    for row in kept_rows:
        direct = dict(row)
        direct["edge_id"] = row["relation_id"]
        direct["original_relation_id"] = row["relation_id"]
        direct["graph_relation_type"] = row["validated_relation_type"]
        direct["edge_direction"] = "direct"
        rows.append(direct)

        inverse_type = INVERSE_RELATION_TYPES.get(row["validated_relation_type"])
        if not inverse_type:
            continue
        inverse = dict(row)
        inverse["edge_id"] = f"{row['relation_id']}__inverse"
        inverse["original_relation_id"] = row["relation_id"]
        inverse["graph_relation_type"] = inverse_type
        inverse["edge_direction"] = "inverse"
        inverse["source_entity_id"], inverse["target_entity_id"] = row["target_entity_id"], row["source_entity_id"]
        inverse["source_name"], inverse["target_name"] = row["target_name"], row["source_name"]
        inverse["source_type"], inverse["target_type"] = row["target_type"], row["source_type"]
        rows.append(inverse)
    return rows


def validate_existing(candidates):
    raw_records = read_jsonl(RAW_RESPONSES_JSONL)
    latest = {}
    for raw in raw_records:
        if raw.get("request_id"):
            latest[raw["request_id"]] = raw

    validated_records = []
    kept_rows = []
    decision_rows = []
    error_rows = []

    for raw in latest.values():
        chunk_id = raw.get("chunk_id", "")
        if raw.get("status") != "ok":
            error_rows.append({"chunk_id": chunk_id, "stage": "model_call", "severity": "error", "error": format_raw_error(raw)})
            continue
        try:
            parsed = extract_json_object(raw.get("response_text", ""))
        except Exception as exc:
            error_rows.append({"chunk_id": chunk_id, "stage": "parse", "severity": "error", "error": str(exc)})
            continue
        relations = parsed.get("relations", [])
        if not isinstance(relations, list):
            error_rows.append({"chunk_id": chunk_id, "stage": "validation", "severity": "error", "error": "relations must be a list"})
            continue

        validated_relations = []
        for relation in relations:
            relation_id = str(relation.get("relation_id", "")).strip()
            candidate = candidates.get(relation_id)
            if not candidate:
                error_rows.append({"chunk_id": chunk_id, "stage": "validation", "severity": "warning", "error": f"Unknown relation_id: {relation_id}"})
                continue
            keep = bool(relation.get("keep", False))
            relation_type = str(relation.get("relation_type") or candidate["candidate_relation_type"]).strip()
            if relation_type not in ALLOWED_RELATION_TYPES:
                relation_type = candidate["candidate_relation_type"]
            try:
                confidence = float(relation.get("confidence", 0.0))
            except (TypeError, ValueError):
                confidence = 0.0
            confidence = min(1.0, max(0.0, confidence))
            decision = {
                "relation_id": relation_id,
                "chunk_id": candidate["chunk_id"],
                "qa_id": candidate["qa_id"],
                "candidate_relation_type": candidate["candidate_relation_type"],
                "validated_relation_type": relation_type,
                "keep": str(keep).lower(),
                "source_entity_id": candidate["source_entity_id"],
                "source_name": candidate["source_name"],
                "source_type": candidate["source_type"],
                "target_entity_id": candidate["target_entity_id"],
                "target_name": candidate["target_name"],
                "target_type": candidate["target_type"],
                "evidence": str(relation.get("evidence", "")).strip(),
                "confidence": f"{confidence:.3f}",
                "reason": str(relation.get("reason", "")).strip(),
                "provider": raw.get("provider", ""),
                "model": raw.get("model", ""),
            }
            decision_rows.append(decision)
            validated_relations.append(decision)
            if keep:
                kept_rows.append(decision)
        validated_records.append({"chunk_id": chunk_id, "relations": validated_relations, "provider": raw.get("provider", ""), "model": raw.get("model", "")})

    with VALIDATED_JSONL.open("w", encoding="utf-8") as handle:
        for record in validated_records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    bidirectional_rows = make_bidirectional_rows(kept_rows)
    write_csv(DECISIONS_CSV, decision_rows)
    write_csv(RELATIONS_CSV, kept_rows)
    write_csv(BIDIRECTIONAL_RELATIONS_CSV, bidirectional_rows)
    write_csv(ERRORS_CSV, error_rows, fieldnames=["chunk_id", "stage", "severity", "error"])
    return validated_records, kept_rows, decision_rows, error_rows, bidirectional_rows


def write_csv(path, rows, fieldnames=None):
    if fieldnames is None:
        fieldnames = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        if not fieldnames:
            handle.write("")
            return
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_report(
    args,
    candidate_requests,
    selected_requests,
    calls_made,
    stopped_on_rate_limit,
    validated_records,
    kept_rows,
    decision_rows,
    error_rows,
    bidirectional_rows,
):
    keep_counts = Counter(row["keep"] for row in decision_rows)
    relation_counts = Counter(row["validated_relation_type"] for row in kept_rows)
    lines = [
        "# AHD Step 4 Relation Validation Report",
        "",
        "## Current Run",
        "",
        f"- Provider: `{args.provider}`",
        f"- Model: `{args.model}`",
        f"- Candidate request records before resume filtering: {len(candidate_requests)}",
        f"- New request records selected: {len(selected_requests)}",
        f"- Live LLM calls made: {calls_made}",
        f"- Stopped on rate limit: `{stopped_on_rate_limit}`",
        f"- Validated chunks with decisions: {len(validated_records)}",
        f"- Relation decisions: {len(decision_rows)}",
        f"- Kept relations: {len(kept_rows)}",
        f"- Neo4j bidirectional relation rows: {len(bidirectional_rows)}",
        f"- Rejected relations: {keep_counts.get('false', 0)}",
        f"- Errors/warnings: {len(error_rows)}",
        "",
        "## Kept Relation Distribution",
        "",
    ]
    if relation_counts:
        for relation_type, count in sorted(relation_counts.items()):
            lines.append(f"- {relation_type}: {count}")
    else:
        lines.append("- No kept relations yet.")
    lines.extend(
        [
            "",
            "## Output Files",
            "",
            f"- Raw responses: `{relpath(RAW_RESPONSES_JSONL)}`",
            f"- Validated JSONL: `{relpath(VALIDATED_JSONL)}`",
            f"- Decisions CSV: `{relpath(DECISIONS_CSV)}`",
            f"- Kept relations CSV: `{relpath(RELATIONS_CSV)}`",
            f"- Neo4j bidirectional relations CSV: `{relpath(BIDIRECTIONAL_RELATIONS_CSV)}`",
            f"- Errors CSV: `{relpath(ERRORS_CSV)}`",
        ]
    )
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8-sig")


def main():
    load_env_file()
    parser = argparse.ArgumentParser(description="Small Step 4 LLM relation validation test.")
    parser.add_argument("--provider", choices=["groq"], default=DEFAULT_PROVIDER)
    parser.add_argument("--model", default=DEFAULT_GROQ_MODEL)
    parser.add_argument("--limit-requests", type=int, default=10)
    parser.add_argument("--batch-start", type=int, default=0)
    parser.add_argument("--batch-size", type=int, default=0)
    parser.add_argument("--sleep-seconds", type=float, default=15.0)
    parser.add_argument("--run-live", action="store_true")
    parser.add_argument("--validate-existing", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--append-raw", action="store_true")
    parser.add_argument("--force-overwrite", action="store_true")
    parser.add_argument("--stop-on-rate-limit", action="store_true")
    args = parser.parse_args()

    if args.resume and args.force_overwrite:
        raise RuntimeError("Use either --resume or --force-overwrite, not both.")
    RELATION_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    requests = read_jsonl(REQUESTS_JSONL)
    _, completed_request_ids, _ = load_existing_raw()
    candidate_requests, selected_requests = select_requests(requests, args, completed_request_ids)
    candidates = load_candidates()

    calls_made = 0
    stopped_on_rate_limit = False
    if args.run_live:
        if RAW_RESPONSES_JSONL.exists() and RAW_RESPONSES_JSONL.stat().st_size > 0 and not args.resume and not args.force_overwrite:
            raise RuntimeError(f"{relpath(RAW_RESPONSES_JSONL)} exists. Use --resume or --force-overwrite.")
        calls_made, stopped_on_rate_limit = run_live_requests(selected_requests, args)
    elif not args.validate_existing:
        print(json.dumps({"selected_request_records": len(selected_requests), "requests_jsonl": relpath(REQUESTS_JSONL)}, ensure_ascii=False, indent=2))

    validated_records, kept_rows, decision_rows, error_rows, bidirectional_rows = validate_existing(candidates)
    write_report(
        args,
        candidate_requests,
        selected_requests,
        calls_made,
        stopped_on_rate_limit,
        validated_records,
        kept_rows,
        decision_rows,
        error_rows,
        bidirectional_rows,
    )
    print(
        json.dumps(
            {
                "candidate_request_records": len(candidate_requests),
                "selected_request_records": len(selected_requests),
                "live_calls_made": calls_made,
                "stopped_on_rate_limit": stopped_on_rate_limit,
                "validated_chunks_with_decisions": len(validated_records),
                "relation_decisions": len(decision_rows),
                "kept_relations": len(kept_rows),
                "neo4j_bidirectional_relation_rows": len(bidirectional_rows),
                "errors": len(error_rows),
                "relations_csv": relpath(RELATIONS_CSV),
                "bidirectional_relations_csv": relpath(BIDIRECTIONAL_RELATIONS_CSV),
                "decisions_csv": relpath(DECISIONS_CSV),
                "report_md": relpath(REPORT_MD),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
