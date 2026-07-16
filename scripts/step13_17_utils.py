import csv
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TRIAL_DIR = ROOT / "outputs" / "05_trial_graph_v1"
REPORT_DIR = ROOT / "reports"

STEP11_DIR = TRIAL_DIR / "context_construction"
STEP12_DIR = TRIAL_DIR / "answer_generation"
STEP13_DIR = TRIAL_DIR / "claim_extraction"
STEP14_DIR = TRIAL_DIR / "claim_verification"
STEP15_DIR = TRIAL_DIR / "hallucination_mitigation"
STEP16_DIR = TRIAL_DIR / "reliability_scoring"
STEP17_DIR = TRIAL_DIR / "final_output"

CONTEXT_BUNDLES_JSON = STEP11_DIR / "trial_graph_v1_context_bundles.json"
ANSWERS_JSON = STEP12_DIR / "trial_graph_v1_answers.json"
ANSWERS_CSV = STEP12_DIR / "trial_graph_v1_answers.csv"
ANSWER_EVALUATION_CSV = STEP12_DIR / "trial_graph_v1_answer_evaluation.csv"

CLAIMS_JSON = STEP13_DIR / "trial_graph_v1_claims.json"
CLAIMS_CSV = STEP13_DIR / "trial_graph_v1_claims.csv"

VERIFICATION_JSON = STEP14_DIR / "trial_graph_v1_claim_verification.json"
VERIFICATION_CSV = STEP14_DIR / "trial_graph_v1_claim_verification.csv"

REFINED_JSON = STEP15_DIR / "trial_graph_v1_refined_answers.json"
REFINED_CSV = STEP15_DIR / "trial_graph_v1_refined_answers.csv"

RELIABILITY_JSON = STEP16_DIR / "trial_graph_v1_reliability_scores.json"
RELIABILITY_CSV = STEP16_DIR / "trial_graph_v1_reliability_scores.csv"

FINAL_JSON = STEP17_DIR / "trial_graph_v1_final_explainable_output.json"
FINAL_CSV = STEP17_DIR / "trial_graph_v1_final_explainable_output.csv"
FINAL_MD = STEP17_DIR / "trial_graph_v1_final_explainable_output.md"

TOKEN_RE = re.compile(r"[\w\u0600-\u06ff]+", re.UNICODE)
SENTENCE_SPLIT_RE = re.compile(r"[.!؟?؛;\n]+")
INSUFFICIENT_EVIDENCE_AR = "لا توجد أدلة كافية."
SAFETY_DISCLAIMER_AR = "يُنصح باستشارة طبيب مختص للحصول على تقييم دقيق."
INSUFFICIENT_WITH_DISCLAIMER_AR = f"{INSUFFICIENT_EVIDENCE_AR} {SAFETY_DISCLAIMER_AR}"


def is_insufficient_evidence_text(text):
    return "لا توجد أدلة كافية" in clean_text(text)


def is_safety_disclaimer(text):
    normalized = clean_text(text)
    return (
        "استشارة طبيب" in normalized
        or "استشارة الطبيب" in normalized
        or "طبيب مختص" in normalized
    )


def relpath(path):
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def ensure_parent(path):
    path.parent.mkdir(parents=True, exist_ok=True)


def read_csv(path):
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def write_csv(path, rows, fieldnames):
    ensure_parent(path)
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def load_json(path, default=None):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path, data):
    ensure_parent(path)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_report(path, lines):
    ensure_parent(path)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def parse_json_field(value, default=None):
    if default is None:
        default = []
    if value is None:
        return default
    if isinstance(value, (list, dict)):
        return value
    text = str(value).strip()
    if not text:
        return default
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return default


def clean_text(value):
    return " ".join(str(value or "").split())


def truncate(value, limit=240):
    text = clean_text(value)
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def tokens(text):
    return [token.lower() for token in TOKEN_RE.findall(str(text or ""))]


def token_set(text):
    return set(tokens(text))


def lexical_overlap(left, right):
    left_tokens = token_set(left)
    right_tokens = token_set(right)
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / max(1, len(left_tokens))


def sentence_split(text):
    parts = [clean_text(part) for part in SENTENCE_SPLIT_RE.split(str(text or ""))]
    return [part for part in parts if len(part) >= 8]


def answer_records():
    rows = load_json(ANSWERS_JSON, default=None)
    if isinstance(rows, list):
        return rows
    return read_csv(ANSWERS_CSV)


def context_index():
    bundles = load_json(CONTEXT_BUNDLES_JSON, default=[])
    return {row["query_id"]: row for row in bundles}


def evaluation_index():
    return {row["query_id"]: row for row in read_csv(ANSWER_EVALUATION_CSV)}


def evidence_index_for_bundle(bundle):
    evidence_rows = []
    evidence_number = 1
    for relation in bundle.get("graph_context", []) or []:
        relation_text = relation.get("relation", "")
        for evidence in relation.get("supporting_evidence", []) or []:
            evidence_id = f"E{evidence_number}"
            evidence_rows.append(
                {
                    "evidence_id": evidence_id,
                    "query_id": bundle.get("query_id", ""),
                    "qa_id": evidence.get("qa_id", ""),
                    "relation": relation_text,
                    "relation_type": relation.get("relation_type", ""),
                    "source_name": relation.get("source_name", ""),
                    "target_name": relation.get("target_name", ""),
                    "evidence_text": clean_text(evidence.get("evidence_text", "")),
                    "source_question": clean_text(evidence.get("source_question", "")),
                    "source_answer": clean_text(evidence.get("source_answer", "")),
                    "rerank_score": relation.get("rerank_score", ""),
                    "reliability": relation.get("reliability", ""),
                }
            )
            evidence_number += 1
    return evidence_rows


def evidence_text(row):
    return " ".join(
        part
        for part in [
            row.get("evidence_text", ""),
            row.get("source_question", ""),
            row.get("source_answer", ""),
            row.get("relation", ""),
        ]
        if part
    )


def to_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def safe_divide(numerator, denominator):
    return numerator / denominator if denominator else 0.0
