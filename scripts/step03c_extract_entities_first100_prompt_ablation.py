import argparse
import csv
import json
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = ROOT / ".env"
INPUT_CSV = ROOT / "ground_truth_entities_100.csv"
OUTPUT_ROOT = ROOT / "outputs" / "03_entity_extraction" / "prompt_ablation_first_100"
DEFAULT_MODEL = "openai/gpt-oss-20b"
ENTITY_TYPES = ["DiseaseCondition", "Treatment", "Symptom", "Test"]


PROMPT_CONFIGS = {
    "central_v1": {
        "title": "central entity extraction",
        "instructions": [
            "Extract exactly one central medical entity from the Arabic question and answer.",
            "The entity must be the main concept needed to answer the user's question.",
            "Return the shortest useful canonical name, not a long phrase.",
            "Choose one entity_type only from DiseaseCondition, Treatment, Symptom, Test.",
            "If several entities appear, choose the one most central to the question-answer pair.",
        ],
    },
    "anti_generic_v2": {
        "title": "central entity extraction with anti-generic constraints",
        "instructions": [
            "Extract exactly one central medical entity from the Arabic question and answer.",
            "Avoid generic entities such as مرض, علاج, دواء, التهاب, تحليل, فحص, ألم unless the text is truly about that generic concept.",
            "Prefer a specific drug, test, disease, symptom, procedure, or named clinical concept over a generic category.",
            "Return a concise canonical Arabic name. Keep drug/test names in Latin letters if the source uses Latin letters.",
            "Choose one entity_type only from DiseaseCondition, Treatment, Symptom, Test.",
            "Do not infer outside medical facts. Use only the provided question and answer.",
        ],
    },
    "candidate_rank_v3": {
        "title": "candidate extraction and centrality ranking",
        "instructions": [
            "List up to five candidate medical entities from the Arabic question and answer.",
            "Rank candidates by how directly they answer the user's question.",
            "Select exactly one best_entity.",
            "The best_entity should be specific, concise, and clinically central.",
            "Avoid selecting background diseases, broad symptoms, or generic words if a more specific treatment, test, disease, or symptom is the real focus.",
            "Choose entity_type only from DiseaseCondition, Treatment, Symptom, Test.",
            "Do not infer outside medical facts. Use only the provided question and answer.",
        ],
    },
}


def relpath(path):
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def safe_slug(value):
    value = str(value or "").strip().lower()
    value = re.sub(r"[^a-z0-9._-]+", "_", value)
    return value.strip("_") or "run"


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


def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def write_csv(path, rows, fieldnames):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def read_jsonl(path):
    if not path.exists():
        return []
    rows = []
    invalid_lines = []
    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                invalid_lines.append({"line_number": line_number, "text": truncate(line, 500)})
    if invalid_lines:
        invalid_path = path.with_suffix(".invalid_lines.json")
        invalid_path.write_text(json.dumps(invalid_lines, ensure_ascii=False, indent=2), encoding="utf-8")
    return rows


def truncate(value, limit):
    value = str(value or "")
    return value if len(value) <= limit else value[: limit - 3].rstrip() + "..."


def make_messages(row, prompt_version):
    config = PROMPT_CONFIGS[prompt_version]
    schema = {
        "canonical_name": "one concise central medical entity",
        "entity_type": "DiseaseCondition | Treatment | Symptom | Test",
        "candidates": [
            {
                "canonical_name": "candidate entity",
                "entity_type": "DiseaseCondition | Treatment | Symptom | Test",
                "centrality_rank": 1,
                "reason": "short reason",
            }
        ],
        "selection_reason": "short reason why the selected entity is central",
    }
    payload = {
        "task": config["title"],
        "allowed_entity_types": ENTITY_TYPES,
        "instructions": config["instructions"],
        "question": row["question"],
        "answer": row["answer"],
        "required_json_schema": schema,
    }
    return [
        {
            "role": "system",
            "content": (
                "You are an Arabic medical entity extraction evaluator. "
                "Return one valid JSON object only. Do not include markdown."
            ),
        },
        {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
    ]


def call_groq(row, api_key, model, prompt_version):
    body = {
        "model": model,
        "messages": make_messages(row, prompt_version),
        "temperature": 0,
    }
    request = urllib.request.Request(
        "https://api.groq.com/openai/v1/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "AHD-EntityPromptAblation/0.1",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return payload["choices"][0]["message"]["content"]


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
    raise ValueError("Could not parse JSON object from model response")


def extract_partial_json_field(text, field):
    pattern = rf'"{re.escape(field)}"\s*:\s*"((?:[^"\\]|\\.)*)"'
    match = re.search(pattern, str(text or ""))
    if not match:
        return ""
    try:
        return json.loads(f'"{match.group(1)}"')
    except json.JSONDecodeError:
        return match.group(1)


def extract_partial_prediction(text):
    canonical_name = extract_partial_json_field(text, "canonical_name")
    entity_type = normalize_entity_type(extract_partial_json_field(text, "entity_type"))
    return canonical_name.strip(), entity_type


def normalize_entity_type(value):
    value = str(value or "").strip()
    aliases = {
        "disease": "DiseaseCondition",
        "condition": "DiseaseCondition",
        "diseasecondition": "DiseaseCondition",
        "treatment": "Treatment",
        "drug": "Treatment",
        "procedure": "Treatment",
        "symptom": "Symptom",
        "test": "Test",
        "measurement": "Test",
    }
    key = value.replace("_", "").replace(" ", "").lower()
    return aliases.get(key, value if value in ENTITY_TYPES else "")


def prediction_from_response(row, raw_record):
    response_text = raw_record.get("response_text", "")
    if raw_record.get("status") != "ok" and not response_text:
        return {
            "question": row["question"],
            "answer": row["answer"],
            "entity_type": "",
            "canonical_name": "",
        }
    try:
        payload = parse_json_object(response_text)
    except Exception:
        canonical_name, entity_type = extract_partial_prediction(response_text)
        if canonical_name or entity_type:
            return {
                "question": row["question"],
                "answer": row["answer"],
                "entity_type": entity_type,
                "canonical_name": canonical_name,
            }
        return {
            "question": row["question"],
            "answer": row["answer"],
            "entity_type": "",
            "canonical_name": "",
        }
    canonical_name = str(payload.get("canonical_name") or "").strip()
    entity_type = normalize_entity_type(payload.get("entity_type"))
    if not canonical_name and isinstance(payload.get("best_entity"), dict):
        best = payload["best_entity"]
        canonical_name = str(best.get("canonical_name") or "").strip()
        entity_type = normalize_entity_type(best.get("entity_type"))
    if not canonical_name and isinstance(payload.get("candidates"), list) and payload["candidates"]:
        first = payload["candidates"][0]
        if isinstance(first, dict):
            canonical_name = str(first.get("canonical_name") or "").strip()
            entity_type = normalize_entity_type(first.get("entity_type"))
    return {
        "question": row["question"],
        "answer": row["answer"],
        "entity_type": entity_type,
        "canonical_name": canonical_name,
    }


def collect_http_error_details(exc):
    body = ""
    try:
        body = exc.read().decode("utf-8", errors="replace")
    except Exception:
        body = ""
    headers = dict(exc.headers.items()) if exc.headers else {}
    return {
        "http_code": exc.code,
        "http_reason": exc.reason,
        "error_body": truncate(body, 1000),
        "retry_after": headers.get("Retry-After", ""),
        "rate_limit_headers": {key: value for key, value in headers.items() if key.lower().startswith("x-ratelimit")},
    }


def load_completed(raw_path):
    latest = {}
    for record in read_jsonl(raw_path):
        row_id = record.get("row_id")
        if row_id:
            latest[int(row_id)] = record
    return latest


def run_live(rows, args, output_dir):
    load_env_file()
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or api_key.lower().startswith("your_"):
        raise RuntimeError("GROQ_API_KEY is not set in .env")

    raw_path = output_dir / "raw_responses.jsonl"
    completed = load_completed(raw_path) if args.resume else {}
    mode = "a" if args.resume else "w"
    calls_made = 0
    stopped_on_rate_limit = False
    output_dir.mkdir(parents=True, exist_ok=True)

    with raw_path.open(mode, encoding="utf-8") as handle:
        for index, row in enumerate(rows, start=1):
            if index in completed and completed[index].get("status") == "ok":
                continue
            status = "error"
            response_text = ""
            error = ""
            http_details = {}
            try:
                response_text = call_groq(row, api_key, args.model, args.prompt_version)
                parse_json_object(response_text)
                status = "ok"
            except urllib.error.HTTPError as exc:
                http_details = collect_http_error_details(exc)
                error = f"HTTP Error {exc.code}: {exc.reason}"
                if exc.code == 429 and args.stop_on_rate_limit:
                    stopped_on_rate_limit = True
            except Exception as exc:
                error = str(exc)

            handle.write(
                json.dumps(
                    {
                        "row_id": index,
                        "provider": "groq",
                        "model": args.model,
                        "prompt_version": args.prompt_version,
                        "status": status,
                        "error": error,
                        "http_details": http_details,
                        "question": row["question"],
                        "answer": row["answer"],
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


def build_predictions(rows, output_dir):
    latest = load_completed(output_dir / "raw_responses.jsonl")
    predictions = []
    errors = []
    for index, row in enumerate(rows, start=1):
        raw = latest.get(index, {})
        pred = prediction_from_response(row, raw)
        predictions.append(pred)
        if raw.get("status") != "ok":
            errors.append(
                {
                    "row_id": index,
                    "status": raw.get("status", "missing"),
                    "error": raw.get("error", ""),
                    "question": row["question"],
                }
            )
    return predictions, errors


def write_report(path, args, calls_made, stopped_on_rate_limit, predictions, errors):
    lines = [
        f"# Step 03C Prompt Ablation - {args.run_name}",
        "",
        "This run generates first-100 entity predictions for prompt/model-level entity-extraction ablation.",
        "",
        "## Run Summary",
        "",
        f"- Input rows: `{args.limit}`",
        f"- Model: `{args.model}`",
        f"- Prompt version: `{args.prompt_version}`",
        f"- Calls made: `{calls_made}`",
        f"- Predictions written: `{len(predictions)}`",
        f"- Errors/missing rows: `{len(errors)}`",
        f"- Stopped on rate limit: `{stopped_on_rate_limit}`",
        "",
        "## Prompt Instructions",
        "",
    ]
    for item in PROMPT_CONFIGS[args.prompt_version]["instructions"]:
        lines.append(f"- {item}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args():
    parser = argparse.ArgumentParser(description="Run first-100 entity extraction prompt/model ablations.")
    parser.add_argument("--input-csv", type=Path, default=INPUT_CSV)
    parser.add_argument("--prompt-version", choices=sorted(PROMPT_CONFIGS), required=True)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument(
        "--run-name",
        default="",
        help="Optional output folder/report suffix. Defaults to the prompt version for backward compatibility.",
    )
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--sleep-seconds", type=float, default=1.0)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--stop-on-rate-limit", action="store_true")
    args = parser.parse_args()
    args.run_name = safe_slug(args.run_name or args.prompt_version)
    return args


def main():
    args = parse_args()
    rows = read_csv(args.input_csv)[: args.limit]
    output_dir = OUTPUT_ROOT / args.run_name
    calls_made, stopped_on_rate_limit = run_live(rows, args, output_dir)
    predictions, errors = build_predictions(rows, output_dir)

    predictions_csv = output_dir / "predictions.csv"
    errors_csv = output_dir / "errors.csv"
    report_md = ROOT / "reports" / f"step03c_prompt_ablation_{args.run_name}.md"
    write_csv(predictions_csv, predictions, ["question", "answer", "entity_type", "canonical_name"])
    write_csv(errors_csv, errors, ["row_id", "status", "error", "question"])
    write_report(report_md, args, calls_made, stopped_on_rate_limit, predictions, errors)
    print(
        json.dumps(
            {
                "prompt_version": args.prompt_version,
                "run_name": args.run_name,
                "model": args.model,
                "rows": len(rows),
                "calls_made": calls_made,
                "predictions": len(predictions),
                "errors": len(errors),
                "stopped_on_rate_limit": stopped_on_rate_limit,
                "predictions_csv": relpath(predictions_csv),
                "errors_csv": relpath(errors_csv),
                "report_md": relpath(report_md),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
