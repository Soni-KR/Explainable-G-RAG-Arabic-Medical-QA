import argparse
import csv
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TRIAL_DIR = ROOT / "outputs" / "05_trial_graph_v1"
STEP11_DIR = TRIAL_DIR / "context_construction"
STEP12_DIR = TRIAL_DIR / "answer_generation"
REPORT_MD = ROOT / "reports" / "trial_graph_v1_step12_answer_generation_report.md"
ENV_FILE = ROOT / ".env"

CONTEXT_BUNDLES_JSON = STEP11_DIR / "trial_graph_v1_context_bundles.json"
RAW_RESPONSES_JSONL = STEP12_DIR / "trial_graph_v1_answer_generation_raw_responses.jsonl"
ANSWERS_JSON = STEP12_DIR / "trial_graph_v1_answers.json"
ANSWERS_CSV = STEP12_DIR / "trial_graph_v1_answers.csv"
ERRORS_CSV = STEP12_DIR / "trial_graph_v1_answer_generation_errors.csv"

DEFAULT_PROVIDER = "groq"
DEFAULT_MODEL = "qwen/qwen3-32b"
MAX_RETRY_WAIT_SECONDS = 60


def relpath(path):
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


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


def write_csv(path, rows, fieldnames):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def truncate_text(value, limit):
    value = " ".join(str(value or "").split())
    return value if len(value) <= limit else value[: limit - 3].rstrip() + "..."


def load_context_bundles():
    return json.loads(CONTEXT_BUNDLES_JSON.read_text(encoding="utf-8"))


def load_existing_completed():
    latest = {}
    for record in read_jsonl(RAW_RESPONSES_JSONL):
        query_id = record.get("query_id", "")
        if query_id:
            latest[query_id] = record
    completed = {
        query_id
        for query_id, record in latest.items()
        if record.get("status") == "ok" and str(record.get("response_text", "")).strip()
    }
    return latest, completed


def select_bundles(bundles, args, completed_query_ids):
    candidates = bundles[: args.limit] if args.limit > 0 else bundles
    if args.resume:
        selected = [bundle for bundle in candidates if bundle["query_id"] not in completed_query_ids]
    else:
        selected = candidates
    return candidates, selected


def compact_context(bundle):
    graph_context = []
    for edge in bundle.get("graph_context", []):
        graph_context.append(
            {
                "rank": edge.get("rank", ""),
                "relation": edge.get("relation", ""),
                "reliability": edge.get("reliability", ""),
                "rerank_score": edge.get("rerank_score", ""),
                "rank_reason": edge.get("rank_reason", ""),
                "supporting_evidence": [
                    {
                        "qa_id": evidence.get("qa_id", ""),
                        "evidence_text": truncate_text(evidence.get("evidence_text", ""), 500),
                        "source_question": truncate_text(evidence.get("source_question", ""), 400),
                        "source_answer": truncate_text(evidence.get("source_answer", ""), 650),
                    }
                    for evidence in edge.get("supporting_evidence", [])
                ],
            }
        )
    return {
        "query_id": bundle["query_id"],
        "query": bundle["query"],
        "warnings": bundle.get("warnings", []),
        "detected_entities": [
            {
                "canonical_name": entity.get("canonical_name", ""),
                "entity_type": entity.get("entity_type", ""),
                "match_type": entity.get("match_type", ""),
            }
            for entity in bundle.get("detected_entities", [])
        ],
        "intents": bundle.get("intents", []),
        "graph_context": graph_context,
    }


def make_messages(bundle):
    payload = {
        "task": "Step 12 Arabic medical Graph-RAG answer generation.",
        "important_boundary": [
            "Use only the provided graph_context and source evidence.",
            "Do not add outside medical facts.",
            "If evidence is weak or missing, say the trial graph evidence is limited.",
            "Do not perform Step 13 claim extraction or Step 14 verification.",
            "Return valid JSON only.",
        ],
        "style": [
            "Answer in Arabic.",
            "Be concise and evidence-aware.",
            "Mention that this is not a substitute for a clinician when the question asks for treatment/diagnosis.",
        ],
        "required_schema": {
            "query_id": bundle["query_id"],
            "answer_ar": "Arabic answer grounded only in retrieved evidence.",
            "evidence_summary_ar": ["short Arabic bullet based on one retrieved edge/evidence"],
            "used_relations": ["relation string copied from graph_context"],
            "limitations_ar": ["limitations or missing relation types, if any"],
            "next_step_note_ar": "brief safety or follow-up note, not a verification score",
        },
        "context_bundle": compact_context(bundle),
    }
    return [
        {
            "role": "system",
            "content": "You are an evidence-grounded Arabic medical Graph-RAG answer generator. Return JSON only.",
        },
        {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
    ]


def call_groq(bundle, api_key, model):
    body = {
        "model": model,
        "messages": make_messages(bundle),
        "temperature": 0,
        "response_format": {"type": "json_object"},
    }
    request = urllib.request.Request(
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
    with urllib.request.urlopen(request, timeout=120) as response:
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


def run_live(bundles, args):
    if args.provider != "groq":
        raise RuntimeError("Only --provider groq is implemented for Step 12 answer generation.")
    load_env_file()
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or api_key.lower().startswith("your_"):
        raise RuntimeError("GROQ_API_KEY is not set in .env")

    mode = "a" if args.resume or args.append_raw else "w"
    calls_made = 0
    stopped_on_rate_limit = False
    STEP12_DIR.mkdir(parents=True, exist_ok=True)
    with RAW_RESPONSES_JSONL.open(mode, encoding="utf-8") as handle:
        for bundle in bundles:
            status = "error"
            response_text = ""
            call_error = ""
            http_details = {}
            try:
                response_text = call_groq(bundle, api_key, args.model)
                status = "ok"
            except urllib.error.HTTPError as exc:
                http_details = collect_http_error_details(exc)
                call_error = f"HTTP Error {exc.code}: {exc.reason}"
                if exc.code == 429 and args.stop_on_rate_limit:
                    stopped_on_rate_limit = True
            except Exception as exc:
                call_error = str(exc)

            handle.write(
                json.dumps(
                    {
                        "query_id": bundle["query_id"],
                        "query": bundle["query"],
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
            if stopped_on_rate_limit:
                break
            if args.sleep_seconds > 0:
                time.sleep(args.sleep_seconds)
    return calls_made, stopped_on_rate_limit


def parse_json_object(text):
    text = str(text or "").strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:].strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            return json.loads(text[start : end + 1])
        raise


def validate_outputs(raw_records, bundles_by_id):
    latest = {}
    for raw in raw_records:
        query_id = raw.get("query_id", "")
        if query_id:
            latest[query_id] = raw

    answer_records = []
    error_rows = []
    for query_id, raw in latest.items():
        if raw.get("status") != "ok":
            error_rows.append(
                {
                    "query_id": query_id,
                    "stage": "model_call",
                    "error": raw.get("error", ""),
                    "http_status": raw.get("http_status", ""),
                    "error_body": raw.get("error_body", ""),
                }
            )
            continue
        try:
            parsed = parse_json_object(raw.get("response_text", ""))
        except Exception as exc:
            error_rows.append({"query_id": query_id, "stage": "json_parse", "error": str(exc), "http_status": "", "error_body": ""})
            continue
        bundle = bundles_by_id.get(query_id, {})
        answer_records.append(
            {
                "query_id": query_id,
                "query": raw.get("query", bundle.get("query", "")),
                "answer_ar": parsed.get("answer_ar", ""),
                "evidence_summary_ar": json.dumps(parsed.get("evidence_summary_ar", []), ensure_ascii=False),
                "used_relations": json.dumps(parsed.get("used_relations", []), ensure_ascii=False),
                "limitations_ar": json.dumps(parsed.get("limitations_ar", []), ensure_ascii=False),
                "next_step_note_ar": parsed.get("next_step_note_ar", ""),
                "provider": raw.get("provider", ""),
                "model": raw.get("model", ""),
            }
        )
    answer_records.sort(key=lambda item: item["query_id"])
    return answer_records, error_rows


def write_report(args, candidates_count, selected_count, calls_made, stopped_on_rate_limit, answer_rows, error_rows):
    lines = [
        "# Trial Graph v1 Step 12 Answer Generation Report",
        "",
        "This step generates Arabic answers from Step 11 evidence-focused context bundles.",
        "It intentionally stops before Step 13 claim extraction and verification.",
        "",
        "## Run Summary",
        "",
        f"- Provider: `{args.provider}`",
        f"- Model: `{args.model}`",
        f"- Candidate queries: {candidates_count}",
        f"- New LLM calls made: {calls_made}",
        f"- Successful generated answers after validation: {len(answer_rows)}",
        f"- Errors: {len(error_rows)}",
        f"- Resume mode: {args.resume}",
        f"- Stopped on rate limit: {stopped_on_rate_limit}",
        "",
        "## Generated Answers",
        "",
    ]
    for row in answer_rows:
        lines.extend(
            [
                f"### {row['query']}",
                "",
                row["answer_ar"],
                "",
            ]
        )
    if error_rows:
        lines.extend(["## Errors", ""])
        for row in error_rows[:10]:
            lines.append(f"- `{row.get('query_id', '')}` {row.get('stage', '')}: {row.get('error', '')}")
        lines.append("")
    lines.extend(
        [
            "## Output Files",
            "",
            f"- Raw responses JSONL: `{relpath(RAW_RESPONSES_JSONL)}`",
            f"- Answers JSON: `{relpath(ANSWERS_JSON)}`",
            f"- Answers CSV: `{relpath(ANSWERS_CSV)}`",
            f"- Errors CSV: `{relpath(ERRORS_CSV)}`",
            "",
            "## Stop Point",
            "",
            "Stop here for this run. The next mix.png step would be Step 13 claim extraction, but it was not executed.",
        ]
    )
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", choices=["groq"], default=DEFAULT_PROVIDER)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--run-live", action="store_true")
    parser.add_argument("--validate-existing", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--append-raw", action="store_true")
    parser.add_argument("--force-overwrite", action="store_true")
    parser.add_argument("--sleep-seconds", type=float, default=3.0)
    parser.add_argument("--stop-on-rate-limit", action="store_true")
    args = parser.parse_args()

    if args.run_live == args.validate_existing:
        raise RuntimeError("Choose exactly one mode: --run-live or --validate-existing")

    STEP12_DIR.mkdir(parents=True, exist_ok=True)
    bundles = load_context_bundles()
    bundles_by_id = {bundle["query_id"]: bundle for bundle in bundles}
    _, completed_query_ids = load_existing_completed()
    candidates, selected = select_bundles(bundles, args, completed_query_ids)

    if args.run_live and RAW_RESPONSES_JSONL.exists() and not (args.resume or args.force_overwrite or args.append_raw):
        raise RuntimeError("Raw Step 12 responses already exist. Use --resume, --append-raw, or --force-overwrite.")

    calls_made = 0
    stopped_on_rate_limit = False
    if args.run_live:
        calls_made, stopped_on_rate_limit = run_live(selected, args)

    raw_records = read_jsonl(RAW_RESPONSES_JSONL)
    answer_rows, error_rows = validate_outputs(raw_records, bundles_by_id)
    ANSWERS_JSON.write_text(json.dumps(answer_rows, ensure_ascii=False, indent=2), encoding="utf-8")
    write_csv(
        ANSWERS_CSV,
        answer_rows,
        [
            "query_id",
            "query",
            "answer_ar",
            "evidence_summary_ar",
            "used_relations",
            "limitations_ar",
            "next_step_note_ar",
            "provider",
            "model",
        ],
    )
    write_csv(ERRORS_CSV, error_rows, ["query_id", "stage", "error", "http_status", "error_body"])
    write_report(args, len(candidates), len(selected), calls_made, stopped_on_rate_limit, answer_rows, error_rows)
    print(
        json.dumps(
            {
                "candidate_queries": len(candidates),
                "selected_new_queries": len(selected),
                "calls_made": calls_made,
                "answers": len(answer_rows),
                "errors": len(error_rows),
                "stopped_on_rate_limit": stopped_on_rate_limit,
                "answers_csv": relpath(ANSWERS_CSV),
                "report_md": relpath(REPORT_MD),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
