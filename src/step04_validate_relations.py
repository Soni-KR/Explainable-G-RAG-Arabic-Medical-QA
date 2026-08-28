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
from datetime import timedelta
import requests

SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent
RELATION_DIR = BASE_DIR / "outputs" / "04_relation_extraction"
REPORTS_DIR = BASE_DIR / "reports"

ENV_FILE = BASE_DIR / ".env"
REQUESTS_JSONL = RELATION_DIR / "relation_validation_requests.jsonl"
CANDIDATES_CSV = RELATION_DIR / "relation_candidates.csv"
RAW_RESPONSES_JSONL = RELATION_DIR / "relation_validation_responses.jsonl"
VALIDATED_JSONL = RELATION_DIR / "relation_validation_validated.jsonl"
RELATIONS_CSV = RELATION_DIR / "relations.csv"
BIDIRECTIONAL_RELATIONS_CSV = RELATION_DIR / "relations_bidirectional.csv"
DECISIONS_CSV = RELATION_DIR / "relation_decisions.csv"
ERRORS_CSV = RELATION_DIR / "relation_validation_errors.csv"
REPORT_MD = REPORTS_DIR / "relation_validation_report.md"

DEFAULT_PROVIDER = "groq"
DEFAULT_GROQ_MODEL = "openai/gpt-oss-20b"
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

    messages = request_record.get("messages")

    if not messages:
        messages = make_messages(request_record)


    body = {
        "model": model,
        "messages": messages,
        "temperature": 0,
        "response_format": {"type": "json_object"},
    }

    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        json=body,
        timeout=120,
    )


    response.raise_for_status()


    payload = response.json()


    return payload["choices"][0]["message"]["content"]



def collect_http_error_details(exc):

    response = exc.response

    body = ""

    if response is not None:
        body = response.text

    headers = (
        dict(response.headers)
        if response is not None
        else {}
    )

    return {
        "http_status": (
            response.status_code
            if response is not None
            else None
        ),
        "http_reason": (
            response.reason
            if response is not None
            else ""
        ),
        "error_body": truncate_text(body, 2000),
        "retry_after": headers.get("Retry-After", ""),
        "rate_limit_headers": {
            k: v
            for k, v in headers.items()
            if k.lower().startswith("x-ratelimit")
        },
    }



def run_live_requests(requests_list, args):

    if args.provider != "groq":
        raise RuntimeError(
            "Only --provider groq is implemented for Step 4 relation validation."
        )

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key or api_key.lower().startswith("your_"):
        raise RuntimeError("GROQ_API_KEY is not set in .env")

    calls_made = 0
    stopped_on_rate_limit = False

    successful_requests = 0
    failed_requests = 0
    consecutive_failed_requests = 0
    last_successful_request = None

    run_start_time = time.time()

    mode = "a" if args.resume or args.append_raw else "w"

    with RAW_RESPONSES_JSONL.open(mode, encoding="utf-8") as handle:

        total_requests = len(requests_list)

        for index, request_record in enumerate(requests_list, start=1):

            elapsed = max(time.time() - run_start_time, 0)
            avg = elapsed / index if index else 0
            remaining = total_requests - index
            eta = avg * remaining

            print()
            print("=" * 70)
            print("RELATION VALIDATION")
            print("=" * 70)
            print(f"Request        : {index}/{total_requests}")
            print(f"Chunk ID       : {request_record['chunk_id']}")
            print(f"Request ID     : {request_record['request_id']}")
            print(f"Progress       : {100 * index / total_requests:.2f}%")
            print()
            print(f"Elapsed        : {timedelta(seconds=int(elapsed))}")
            print(f"Average/request: {avg:.2f} sec")
            print(f"ETA            : {timedelta(seconds=int(eta))}")
            print("=" * 70)

            status = "error"
            response_text = ""
            call_error = ""
            http_details = {}

            for attempt in range(MAX_MODEL_CALL_RETRIES + 1):

                try:

                    print(
                        f"[{request_record['request_id']}] Sending request to Groq..."
                    )

                    response_text = call_groq(
                        request_record,
                        api_key,
                        args.model,
                    )

                    status = "ok"
                    call_error = ""
                    http_details = {}

                    break

                except requests.exceptions.HTTPError as exc:

                    http_details = collect_http_error_details(exc)

                    status = (
                        exc.response.status_code
                        if exc.response is not None
                        else None
                    )

                    reason = (
                        exc.response.reason
                        if exc.response is not None
                        else str(exc)
                    )

                    call_error = f"HTTP Error {status}: {reason}"

                    if status == 429 and args.stop_on_rate_limit:

                        print()
                        print("=" * 70)
                        print("GROQ DAILY LIMIT REACHED")
                        print("=" * 70)
                        print(
                            f"Last successful request : {last_successful_request}"
                        )
                        print(
                            f"Current request         : {request_record['request_id']}"
                        )
                        print()
                        print("Progress has been saved.")
                        print()
                        print("Switch API key then run:")
                        print()
                        print(
                            "python step04_validate_relations.py --run-live --resume --stop-on-rate-limit"
                        )
                        print("=" * 70)

                        stopped_on_rate_limit = True
                        break

                    if (
                        status == 429
                        and attempt < MAX_MODEL_CALL_RETRIES
                    ):

                        retry_after = http_details.get("retry_after", "")

                        try:
                            wait_seconds = (
                                float(retry_after)
                                if retry_after
                                else 0
                            )
                        except ValueError:
                            wait_seconds = 0

                        wait_seconds = max(
                            wait_seconds,
                            args.sleep_seconds,
                            30,
                        )

                        wait_seconds = min(
                            wait_seconds,
                            MAX_RETRY_WAIT_SECONDS,
                        )

                        print(
                            f"Retrying after {wait_seconds:.1f} seconds..."
                        )

                        time.sleep(wait_seconds)

                        continue

                    break

                except requests.exceptions.RequestException as exc:

                    call_error = str(exc)

                    break

                except Exception as exc:

                    import traceback

                    trace = traceback.format_exc()
                    print(trace)

                    call_error = trace

                    break

            handle.write(
                json.dumps(
                    {
                        "request_number": index,
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

            handle.flush()

            calls_made += 1

            if status == "ok":

                successful_requests += 1
                consecutive_failed_requests = 0
                last_successful_request = request_record["request_id"]

            else:

                failed_requests += 1
                consecutive_failed_requests += 1

            print()
            print("=" * 70)
            print("RELATION VALIDATION")
            print("=" * 70)
            print(f"Completed request : {request_record['request_id']}")
            print(f"Successful        : {successful_requests}")
            print(f"Failed            : {failed_requests}")
            print("=" * 70)

            if stopped_on_rate_limit:
                return calls_made, True

            if args.stop_on_rate_limit and consecutive_failed_requests >= 5:
                print()
                print("=" * 70)
                print("STOPPED AFTER REPEATED FAILURES")
                print("=" * 70)
                print(
                    "Five consecutive requests failed. This usually means "
                    "the current API key is rate-limited or quota-limited."
                )
                print(f"Last successful request : {last_successful_request}")
                print(
                    f"Current request         : {request_record['request_id']}"
                )
                print("Progress has been saved; rerun with --resume.")
                print("=" * 70)
                return calls_made, True

            if (
                index < total_requests
                and args.sleep_seconds
            ):
                time.sleep(args.sleep_seconds)

    return calls_made, False

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
        if isinstance(parsed, list):
            if all(isinstance(item, dict) and "relation_id" in item for item in parsed):
                parsed = {"chunk_id": chunk_id, "relations": parsed}
            elif len(parsed) == 1 and isinstance(parsed[0], dict):
                parsed = parsed[0]
            else:
                error_rows.append({"chunk_id": chunk_id, "stage": "parse", "severity": "error", "error": "parsed JSON must be an object, got list"})
                continue
        if not isinstance(parsed, dict):
            error_rows.append({"chunk_id": chunk_id, "stage": "parse", "severity": "error", "error": f"parsed JSON must be an object, got {type(parsed).__name__}"})
            continue
        relations = parsed.get("relations", [])
        if not isinstance(relations, list):
            error_rows.append({"chunk_id": chunk_id, "stage": "validation", "severity": "error", "error": "relations must be a list"})
            continue

        validated_relations = []
        for relation in relations:
            if not isinstance(relation, dict):
                error_rows.append({"chunk_id": chunk_id, "stage": "validation", "severity": "warning", "error": "relation entry must be an object"})
                continue
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
    global REQUESTS_JSONL
    global CANDIDATES_CSV
    global RAW_RESPONSES_JSONL
    global VALIDATED_JSONL
    global RELATIONS_CSV
    global BIDIRECTIONAL_RELATIONS_CSV
    global DECISIONS_CSV
    global ERRORS_CSV
    global REPORT_MD

    load_env_file()

    parser = argparse.ArgumentParser(
        description="Step 4 LLM relation validation."
    )

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
    parser.add_argument(
        "--requests-jsonl",
        default=str(REQUESTS_JSONL),
        help="Relation validation request JSONL to use.",
    )
    parser.add_argument(
        "--candidates-csv",
        default=str(CANDIDATES_CSV),
        help="Relation candidate CSV to use.",
    )
    parser.add_argument(
        "--output-tag",
        default="",
        help="Optional output tag, e.g. refined, to avoid overwriting default relation validation outputs.",
    )

    args = parser.parse_args()

    REQUESTS_JSONL = Path(args.requests_jsonl)
    CANDIDATES_CSV = Path(args.candidates_csv)
    if args.output_tag:
        safe_tag = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in args.output_tag.strip())
        RAW_RESPONSES_JSONL = RELATION_DIR / f"ahd_llm_relation_validation_raw_responses_{safe_tag}.jsonl"
        VALIDATED_JSONL = RELATION_DIR / f"ahd_llm_relation_validation_validated_{safe_tag}.jsonl"
        RELATIONS_CSV = RELATION_DIR / f"ahd_relations_llm_validated_{safe_tag}.csv"
        BIDIRECTIONAL_RELATIONS_CSV = RELATION_DIR / f"ahd_relations_neo4j_bidirectional_{safe_tag}.csv"
        DECISIONS_CSV = RELATION_DIR / f"ahd_relation_validation_decisions_{safe_tag}.csv"
        ERRORS_CSV = RELATION_DIR / f"ahd_relation_validation_errors_{safe_tag}.csv"
        REPORT_MD = REPORTS_DIR / f"ahd_relation_validation_report_{safe_tag}.md"

    if args.resume and args.force_overwrite:
        raise RuntimeError(
            "Use either --resume or --force-overwrite, not both."
        )

    RELATION_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    requests = read_jsonl(REQUESTS_JSONL)

    (
        existing_records,
        completed_request_ids,
        errored_request_ids,
    ) = load_existing_raw()

    candidate_requests, selected_requests = select_requests(
        requests,
        args,
        completed_request_ids,
    )

    print(f"Already completed : {len(completed_request_ids)}")
    print(f"Already errored   : {len(errored_request_ids)}")
    print(f"Will process      : {len(selected_requests)}")
    print()

    candidates = load_candidates()

    calls_made = 0
    stopped_on_rate_limit = False

    if args.run_live:

        if (
            RAW_RESPONSES_JSONL.exists()
            and RAW_RESPONSES_JSONL.stat().st_size > 0
            and not args.resume
            and not args.force_overwrite
        ):
            raise RuntimeError(
                f"{relpath(RAW_RESPONSES_JSONL)} already exists. "
                "Use --resume or --force-overwrite."
            )

        calls_made, stopped_on_rate_limit = run_live_requests(
            selected_requests,
            args,
        )

        if stopped_on_rate_limit:

            print()
            print("=" * 70)
            print("STOPPED")
            print("=" * 70)
            print("Groq daily quota reached.")
            print()
            print("Change your API key then run:")
            print()
            print(
                "python step04_validate_relations.py --run-live --resume --stop-on-rate-limit"
            )
            print("=" * 70)

    elif not args.validate_existing:

        print(
            json.dumps(
                {
                    "selected_request_records": len(selected_requests),
                    "requests_jsonl": relpath(REQUESTS_JSONL),
                },
                ensure_ascii=False,
                indent=2,
            )
        )

    validated_records, kept_rows, decision_rows, error_rows, bidirectional_rows = (
        validate_existing(candidates)
    )

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
                "already_completed": len(completed_request_ids),
                "already_errored": len(errored_request_ids),
                "live_calls_made": calls_made,
                "stopped_on_rate_limit": stopped_on_rate_limit,
                "validated_chunks_with_decisions": len(validated_records),
                "relation_decisions": len(decision_rows),
                "kept_relations": len(kept_rows),
                "neo4j_bidirectional_relation_rows": len(
                    bidirectional_rows
                ),
                "errors": len(error_rows),
                "relations_csv": relpath(RELATIONS_CSV),
                "bidirectional_relations_csv": relpath(
                    BIDIRECTIONAL_RELATIONS_CSV
                ),
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
