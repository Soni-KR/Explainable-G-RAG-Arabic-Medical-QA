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
TRIAL_DIR = ROOT / "outputs" / "05_trial_graph_v1"
STEP11_DIR = TRIAL_DIR / "context_construction"
STEP12_DIR = TRIAL_DIR / "answer_generation"
REPORT_MD = ROOT / "reports" / "trial_graph_v1_step12_answer_generation_report.md"
ENV_FILE = ROOT / ".env"

CONTEXT_BUNDLES_JSON = STEP11_DIR / "trial_graph_v1_context_bundles.json"
PROMPTS_JSON = STEP11_DIR / "trial_graph_v1_llm_prompts.json"
RAW_RESPONSES_JSONL = STEP12_DIR / "trial_graph_v1_answer_generation_raw_responses.jsonl"
ANSWERS_JSON = STEP12_DIR / "trial_graph_v1_answers.json"
ANSWERS_CSV = STEP12_DIR / "trial_graph_v1_answers.csv"
ERRORS_CSV = STEP12_DIR / "trial_graph_v1_answer_generation_errors.csv"
EVALUATION_JSON = STEP12_DIR / "trial_graph_v1_answer_evaluation.json"
EVALUATION_CSV = STEP12_DIR / "trial_graph_v1_answer_evaluation.csv"

DEFAULT_PROVIDER = "extractive"
DEFAULT_MODEL = "qwen/qwen3-32b"
MAX_RETRY_WAIT_SECONDS = 60
MAX_GROQ_PROMPT_CHARS = 4200
TOKEN_RE = re.compile(r"[\w\u0600-\u06ff]+", re.UNICODE)
SENTENCE_SPLIT_RE = re.compile(r"[.!؟?؛;\n]+")


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


def load_prompt_records():
    if not PROMPTS_JSON.exists():
        return {}
    return {row["query_id"]: row for row in json.loads(PROMPTS_JSON.read_text(encoding="utf-8"))}


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


def build_evidence_text(bundle):
    parts = []
    for edge in bundle.get("graph_context", []):
        parts.append(edge.get("relation", ""))
        for evidence in edge.get("supporting_evidence", []):
            parts.extend(
                [
                    evidence.get("evidence_text", ""),
                    evidence.get("source_question", ""),
                    evidence.get("source_answer", ""),
                ]
            )
    return " ".join(part for part in parts if part)


def evidence_reference_index(bundle):
    evidence_ids = set()
    qa_ids = set()
    evidence_index = 1
    for edge in bundle.get("graph_context", []):
        for evidence in edge.get("supporting_evidence", []):
            evidence_ids.add(f"E{evidence_index}")
            if evidence.get("qa_id"):
                qa_ids.add(evidence.get("qa_id", ""))
            evidence_index += 1
    return evidence_ids, qa_ids


def compact_prompt_text(prompt_text, max_chars=MAX_GROQ_PROMPT_CHARS):
    prompt_text = str(prompt_text or "")
    if len(prompt_text) <= max_chars:
        return prompt_text
    instructions_index = prompt_text.rfind("\nInstructions:")
    instructions = prompt_text[instructions_index:] if instructions_index >= 0 else ""
    body = prompt_text[:instructions_index] if instructions_index >= 0 else prompt_text
    budget = max_chars - len(instructions) - len("\n\n[Context truncated to fit model request limit.]\n")
    return body[: max(500, budget)].rstrip() + "\n\n[Context truncated to fit model request limit.]\n" + instructions


def make_messages(bundle, prompt_record=None):
    prompt_text = compact_prompt_text((prompt_record or {}).get("prompt_text", ""))
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
            "claims": [
                {
                    "claim_ar": "one atomic Arabic medical claim",
                    "citations": ["E1"],
                    "source_qa_ids": ["qa id copied from evidence"],
                    "support_status": "supported | insufficient",
                }
            ],
            "evidence_summary_ar": ["short Arabic bullet based on one retrieved edge/evidence"],
            "used_relations": ["relation string copied from graph_context"],
            "limitations_ar": ["limitations or missing relation types, if any"],
            "next_step_note_ar": "brief safety or follow-up note, not a verification score",
        },
        "evidence_prompt": prompt_text,
    }
    if not prompt_text:
        payload["context_bundle"] = compact_context(bundle)
    return [
        {
            "role": "system",
            "content": "You are an evidence-grounded Arabic medical Graph-RAG answer generator. Return JSON only.",
        },
        {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
    ]


def call_groq(bundle, api_key, model, prompt_record=None):
    body = {
        "model": model,
        "messages": make_messages(bundle, prompt_record),
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


def generate_extractive_answer(bundle):
    evidence_items = []
    used_relations = []
    for edge in bundle.get("graph_context", []):
        relation = edge.get("relation", "")
        if relation and relation not in used_relations:
            used_relations.append(relation)
        for evidence in edge.get("supporting_evidence", []):
            text = truncate_text(evidence.get("evidence_text", ""), 280)
            if text:
                evidence_items.append(
                    {
                        "relation": relation,
                        "qa_id": evidence.get("qa_id", ""),
                        "text": text,
                        "reliability": edge.get("reliability", ""),
                    }
                )
    top_items = evidence_items[:5]
    if not top_items:
        answer = "الأدلة المسترجعة غير كافية للإجابة عن السؤال."
        limitations = ["لا توجد جمل أدلة كافية في السياق المسترجع."]
    else:
        bullets = []
        for item in top_items:
            bullets.append(f"- بحسب الدليل ({item['qa_id']}): {item['text']}")
        answer = (
            "اعتمادا فقط على الأدلة المسترجعة، يمكن تلخيص الإجابة كما يلي:\n"
            + "\n".join(bullets)
            + "\nهذه الإجابة مبنية على سياق مسترجع محدود ولا تغني عن مراجعة طبيب مختص."
        )
        limitations = [
            "الإجابة تستخدم الأدلة المسترجعة فقط.",
            "قد تكون الأدلة غير كافية إذا لم تغط كل تفاصيل السؤال.",
        ]
    return json.dumps(
        {
            "query_id": bundle["query_id"],
            "answer_ar": answer,
            "evidence_summary_ar": [item["text"] for item in top_items],
            "used_relations": used_relations[:8],
            "limitations_ar": limitations,
            "next_step_note_ar": "ينبغي التحقق من كل ادعاء في خطوة claim verification قبل اعتبار الإجابة نهائية.",
        },
        ensure_ascii=False,
    )


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


def run_live(bundles, args, prompts_by_id):
    api_key = ""
    if args.provider == "groq":
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
                if args.provider == "extractive":
                    response_text = generate_extractive_answer(bundle)
                else:
                    response_text = call_groq(bundle, api_key, args.model, prompts_by_id.get(bundle["query_id"]))
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
                "claims": json.dumps(parsed.get("claims", []), ensure_ascii=False),
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


def normalize_text(value):
    return " ".join(str(value or "").lower().split())


def tokens(value):
    return TOKEN_RE.findall(normalize_text(value))


def lcs_len(a, b):
    previous = [0] * (len(b) + 1)
    for token_a in a:
        current = [0]
        for index_b, token_b in enumerate(b, start=1):
            if token_a == token_b:
                current.append(previous[index_b - 1] + 1)
            else:
                current.append(max(previous[index_b], current[-1]))
        previous = current
    return previous[-1]


def rouge_l_f1(candidate, reference):
    cand = tokens(candidate)
    ref = tokens(reference)
    if not cand or not ref:
        return 0.0
    lcs = lcs_len(cand, ref)
    precision = lcs / len(cand)
    recall = lcs / len(ref)
    return round((2 * precision * recall / (precision + recall)) if precision + recall else 0.0, 6)


def lexical_similarity(a, b):
    a_tokens = set(tokens(a))
    b_tokens = set(tokens(b))
    if not a_tokens or not b_tokens:
        return 0.0
    return round(len(a_tokens & b_tokens) / ((len(a_tokens) * len(b_tokens)) ** 0.5), 6)


def split_claims(answer):
    claims = []
    for part in SENTENCE_SPLIT_RE.split(answer or ""):
        claim = " ".join(part.split())
        claim = claim.removeprefix("-").strip()
        if claim.startswith("اعتمادا فقط على الأدلة"):
            continue
        if "لا تغني عن مراجعة طبيب" in claim:
            continue
        if claim.startswith("هذه الإجابة مبنية على سياق"):
            continue
        if len(tokens(claim)) >= 3:
            claims.append(claim)
    return claims


def claim_support_score(claim, evidence_text):
    return lexical_similarity(claim, evidence_text)


def evaluate_answer_row(row, bundle):
    answer = row.get("answer_ar", "")
    query = row.get("query", "")
    evidence_text = build_evidence_text(bundle)
    reference_text = evidence_text
    evidence_ids, evidence_qa_ids = evidence_reference_index(bundle)
    structured_claims = []
    try:
        parsed_claims = json.loads(row.get("claims", "[]"))
        if isinstance(parsed_claims, list):
            structured_claims = [claim for claim in parsed_claims if isinstance(claim, dict)]
    except json.JSONDecodeError:
        structured_claims = []

    if structured_claims:
        claims = [claim.get("claim_ar", "") for claim in structured_claims if claim.get("claim_ar")]
        supported_claims = []
        unsupported_claims = []
        for claim in structured_claims:
            claim_text = claim.get("claim_ar", "")
            citations = {str(item).strip() for item in claim.get("citations", [])}
            source_qa_ids = {str(item).strip() for item in claim.get("source_qa_ids", [])}
            status = str(claim.get("support_status", "")).lower()
            citation_ok = bool(citations & evidence_ids)
            qa_ok = not source_qa_ids or bool(source_qa_ids & evidence_qa_ids)
            lexical_ok = claim_support_score(claim_text, evidence_text) >= 0.08
            if status == "supported" and citation_ok and qa_ok and lexical_ok:
                supported_claims.append(claim_text)
            else:
                unsupported_claims.append(claim_text)
    else:
        claims = split_claims(answer)
        if not claims and "لا توجد أدلة كافية" in answer:
            claims = []
            supported_claims = []
            unsupported_claims = []
        else:
            supported_claims = [claim for claim in claims if claim_support_score(claim, evidence_text) >= 0.10]
            unsupported_claims = [claim for claim in claims if claim not in supported_claims]

    claim_support_rate = len(supported_claims) / len(claims) if claims else 0.0
    hallucination_rate = len(unsupported_claims) / len(claims) if claims else 0.0
    if not claims and "لا توجد أدلة كافية" in answer:
        claim_support_rate = 1.0
        hallucination_rate = 0.0
    faithfulness = claim_support_rate
    answer_relevancy = lexical_similarity(query, answer)
    refined_answer = " ".join(claim for claim in claims if claim in supported_claims)
    if not refined_answer:
        refined_answer = "لا توجد أدلة كافية."
    return {
        "query_id": row.get("query_id", ""),
        "query": query,
        "bertscore_f1": "",
        "rouge_l": rouge_l_f1(answer, reference_text),
        "e5_similarity": "",
        "e5_similarity_proxy": lexical_similarity(answer, reference_text),
        "ragas_faithfulness": round(faithfulness, 6),
        "ragas_answer_relevancy": answer_relevancy,
        "claim_count": len(claims),
        "supported_claim_count": len(supported_claims),
        "unsupported_claim_count": len(unsupported_claims),
        "claim_support_rate": round(claim_support_rate, 6),
        "hallucination_rate": round(hallucination_rate, 6),
        "refined_answer_ar": refined_answer,
        "unsupported_claims": json.dumps(unsupported_claims, ensure_ascii=False),
        "metric_mode": "lexical_proxy_without_external_metric_models",
    }


def evaluate_answers(answer_rows, bundles_by_id):
    return [evaluate_answer_row(row, bundles_by_id.get(row["query_id"], {})) for row in answer_rows]


def write_report(args, candidates_count, selected_count, calls_made, stopped_on_rate_limit, answer_rows, error_rows, evaluation_rows):
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
        f"- Evaluation rows: {len(evaluation_rows)}",
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
            f"- Evaluation JSON: `{relpath(EVALUATION_JSON)}`",
            f"- Evaluation CSV: `{relpath(EVALUATION_CSV)}`",
            "",
            "## Evaluation Note",
            "",
            "ROUGE-L and grounding metrics are computed locally. BERTScore and full E5/RAGAS model-based scores are left blank unless a later metric-model integration is added; `e5_similarity_proxy`, faithfulness, answer relevancy, claim-support rate, and hallucination rate use lexical evidence-overlap proxies.",
            "",
            "## Stop Point",
            "",
            "Stop here for this run. The next mix.png step would be Step 13 claim extraction, but it was not executed.",
        ]
    )
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", choices=["extractive", "groq"], default=DEFAULT_PROVIDER)
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
    prompts_by_id = load_prompt_records()
    bundles_by_id = {bundle["query_id"]: bundle for bundle in bundles}
    _, completed_query_ids = load_existing_completed()
    candidates, selected = select_bundles(bundles, args, completed_query_ids)

    if args.run_live and RAW_RESPONSES_JSONL.exists() and not (args.resume or args.force_overwrite or args.append_raw):
        raise RuntimeError("Raw Step 12 responses already exist. Use --resume, --append-raw, or --force-overwrite.")

    calls_made = 0
    stopped_on_rate_limit = False
    if args.run_live:
        calls_made, stopped_on_rate_limit = run_live(selected, args, prompts_by_id)

    raw_records = read_jsonl(RAW_RESPONSES_JSONL)
    answer_rows, error_rows = validate_outputs(raw_records, bundles_by_id)
    evaluation_rows = evaluate_answers(answer_rows, bundles_by_id)
    ANSWERS_JSON.write_text(json.dumps(answer_rows, ensure_ascii=False, indent=2), encoding="utf-8")
    EVALUATION_JSON.write_text(json.dumps(evaluation_rows, ensure_ascii=False, indent=2), encoding="utf-8")
    write_csv(
        ANSWERS_CSV,
        answer_rows,
        [
            "query_id",
            "query",
            "answer_ar",
            "claims",
            "evidence_summary_ar",
            "used_relations",
            "limitations_ar",
            "next_step_note_ar",
            "provider",
            "model",
        ],
    )
    write_csv(ERRORS_CSV, error_rows, ["query_id", "stage", "error", "http_status", "error_body"])
    write_csv(
        EVALUATION_CSV,
        evaluation_rows,
        [
            "query_id",
            "query",
            "bertscore_f1",
            "rouge_l",
            "e5_similarity",
            "e5_similarity_proxy",
            "ragas_faithfulness",
            "ragas_answer_relevancy",
            "claim_count",
            "supported_claim_count",
            "unsupported_claim_count",
            "claim_support_rate",
            "hallucination_rate",
            "refined_answer_ar",
            "unsupported_claims",
            "metric_mode",
        ],
    )
    write_report(args, len(candidates), len(selected), calls_made, stopped_on_rate_limit, answer_rows, error_rows, evaluation_rows)
    print(
        json.dumps(
            {
                "candidate_queries": len(candidates),
                "selected_new_queries": len(selected),
                "calls_made": calls_made,
                "answers": len(answer_rows),
                "errors": len(error_rows),
                "evaluation_rows": len(evaluation_rows),
                "stopped_on_rate_limit": stopped_on_rate_limit,
                "answers_csv": relpath(ANSWERS_CSV),
                "evaluation_csv": relpath(EVALUATION_CSV),
                "report_md": relpath(REPORT_MD),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
