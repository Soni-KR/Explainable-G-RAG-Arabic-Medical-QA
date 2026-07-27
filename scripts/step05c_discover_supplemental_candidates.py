import argparse
import csv
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TRIAL_DIR = ROOT / "outputs" / "05_trial_graph_v1"
IMPORT_DIR = TRIAL_DIR / "import"
FINAL_DIR = TRIAL_DIR / "final_output"
SUPP_DIR = TRIAL_DIR / "supplemental_facts"
REPORT_MD = ROOT / "reports" / "trial_graph_v1_supplemental_candidate_discovery_report.md"

QA_CSV = IMPORT_DIR / "trial_graph_v1_qa_sources.csv"
FINAL_CSV = FINAL_DIR / "trial_graph_v1_final_explainable_output.csv"
CANDIDATE_TOPICS_CSV = SUPP_DIR / "trial_graph_v1_supplemental_candidate_topics.csv"
CANDIDATE_EVIDENCE_CSV = SUPP_DIR / "trial_graph_v1_supplemental_candidate_evidence.csv"
CANDIDATE_REVIEW_CSV = SUPP_DIR / "trial_graph_v1_supplemental_candidate_review.csv"
CANDIDATE_JSON = SUPP_DIR / "trial_graph_v1_supplemental_candidate_discovery.json"

ARABIC_DIACRITICS_RE = re.compile(r"[\u064b-\u065f\u0670\u06d6-\u06ed]")
TATWEEL_RE = re.compile(r"\u0640+")
TOKEN_RE = re.compile(r"[\w\u0600-\u06ff]+", re.UNICODE)
ARABIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")
ARABIC_LETTER_NORMALIZATION = str.maketrans(
    {
        "أ": "ا",
        "إ": "ا",
        "آ": "ا",
        "ٱ": "ا",
        "ى": "ي",
        "ئ": "ي",
        "ؤ": "و",
        "ة": "ه",
    }
)

STOPWORDS = {
    "انا",
    "اني",
    "عندي",
    "عند",
    "علي",
    "على",
    "هل",
    "ما",
    "ماهو",
    "ماهي",
    "من",
    "في",
    "فى",
    "عن",
    "الى",
    "الي",
    "او",
    "ام",
    "مع",
    "هذا",
    "هذه",
    "ذلك",
    "لكم",
    "دكتور",
    "السلام",
    "عليكم",
    "شكرا",
    "ارجو",
    "الرد",
    "ممكن",
    "يمكن",
    "سبب",
    "اسباب",
    "علاج",
    "دواء",
    "الم",
    "الام",
    "اشعر",
    "اعاني",
    "لدي",
    "كان",
    "كانت",
    "بعد",
    "قبل",
    "منذ",
    "اليوم",
    "الان",
}

CATEGORY_PATTERNS = {
    "dental": [
        "ضرس",
        "اسنان",
        "الاسنان",
        "لثه",
        "اللثه",
        "حشوه",
        "تسوس",
        "زراعه",
        "برد",
    ],
    "pregnancy_obstetrics": [
        "حامل",
        "الحمل",
        "جنين",
        "الجنين",
        "مبايض",
        "حقن",
        "مجهري",
        "اسبوع",
        "الشهر",
    ],
    "drug_safety": [
        "دواء",
        "علاج",
        "cephadar",
        "بريمولوت",
        "زيت",
        "ابر",
        "الحديد",
        "تنشيط",
    ],
    "orthopedics_pain": [
        "ركبه",
        "مفصل",
        "رقبه",
        "كتف",
        "ظهر",
        "حوض",
        "شلل",
        "جنف",
    ],
    "labs": [
        "بروثرومبين",
        "تركيز",
        "تحليل",
        "فحص",
        "نسبه",
        "400",
    ],
    "nutrition": [
        "فقر",
        "دم",
        "اغذيه",
        "اكل",
        "طعام",
        "حديد",
    ],
    "surgery_urology": [
        "بواسير",
        "عمليه",
        "البول",
        "مثانه",
        "خصيتان",
    ],
    "respiratory_general": [
        "تنفس",
        "صعوبه",
        "ارهاق",
        "صدر",
        "القفص",
    ],
    "dermatology_hair": [
        "شعر",
        "يقع",
        "خفيف",
        "مناطق",
    ],
}


def relpath(path):
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def write_csv(path, rows, fieldnames):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def normalize_arabic(value):
    text = str(value or "").lower().translate(ARABIC_DIGITS).translate(ARABIC_LETTER_NORMALIZATION)
    text = ARABIC_DIACRITICS_RE.sub("", text)
    text = TATWEEL_RE.sub("", text)
    return text


def tokenize(value):
    tokens = []
    for token in TOKEN_RE.findall(normalize_arabic(value)):
        if len(token) < 3 or token in STOPWORDS:
            continue
        tokens.append(token)
    return tokens


def classify_topic(tokens):
    token_set = set(tokens)
    scores = {
        category: len(token_set.intersection(patterns))
        for category, patterns in CATEGORY_PATTERNS.items()
    }
    best_category, best_score = max(scores.items(), key=lambda item: item[1])
    return best_category if best_score else "other"


def snippet(value, limit=260):
    text = " ".join(str(value or "").split())
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def prepare_qa_rows(rows):
    prepared = []
    for row in rows:
        text = f"{row.get('question', '')} {row.get('answer', '')}"
        tokens = tokenize(text)
        prepared.append(
            {
                **row,
                "_tokens": set(tokens),
                "_text_norm": normalize_arabic(text),
            }
        )
    return prepared


def score_candidate(query_tokens, qa_row):
    query_set = set(query_tokens)
    overlap = query_set.intersection(qa_row["_tokens"])
    if not overlap:
        return 0.0, []
    overlap_score = len(overlap) / max(1, math.sqrt(len(query_set)))
    answer_bonus = 0.2 if any(token in normalize_arabic(qa_row.get("answer", "")) for token in overlap) else 0.0
    return round(overlap_score + answer_bonus, 4), sorted(overlap)


def recommendation_for(row, min_review_score):
    score = float(row.get("candidate_score") or 0.0)
    if row.get("leakage_warning"):
        return "reject_eval_leakage"
    if row.get("candidate_topic") == "other":
        return "reject_generic_topic"
    if score < min_review_score:
        return "reject_low_similarity"
    return "recommended_for_human_review"


def discover_candidates(final_rows, qa_rows, top_k, min_review_score):
    qa_prepared = prepare_qa_rows(qa_rows)
    failed_rows = [
        row
        for row in final_rows
        if row.get("answerability_label") in {"insufficient_evidence", "partially_answerable"}
        or row.get("reliability_label") == "low"
    ]

    topic_rows = []
    evidence_rows = []
    discovery_json = []

    for row in failed_rows:
        query_norm = normalize_arabic(row.get("query", ""))
        query_tokens = tokenize(row.get("query", ""))
        topic = classify_topic(query_tokens)
        candidates = []
        for qa_row in qa_prepared:
            score, overlap = score_candidate(query_tokens, qa_row)
            if score <= 0:
                continue
            candidates.append((score, overlap, qa_row))
        candidates.sort(key=lambda item: (item[0], len(item[1])), reverse=True)
        top_candidates = candidates[:top_k]

        topic_rows.append(
            {
                "query_id": row.get("query_id", ""),
                "query": row.get("query", ""),
                "answerability_label": row.get("answerability_label", ""),
                "reliability_label": row.get("reliability_label", ""),
                "overall_reliability_score": row.get("overall_reliability_score") or row.get("reliability_score", ""),
                "candidate_topic": topic,
                "key_terms": json.dumps(Counter(query_tokens).most_common(12), ensure_ascii=False),
                "candidate_evidence_count": str(len(top_candidates)),
                "review_status": "needs_review",
            }
        )

        json_candidates = []
        for rank, (score, overlap, qa_row) in enumerate(top_candidates, start=1):
            source_question_norm = normalize_arabic(qa_row.get("question", ""))
            leakage_warning = ""
            if source_question_norm == query_norm:
                leakage_warning = "exact_eval_question_match"
            elif query_norm and (query_norm in source_question_norm or source_question_norm in query_norm):
                leakage_warning = "near_exact_eval_question_match"
            evidence_row = {
                "query_id": row.get("query_id", ""),
                "rank": str(rank),
                "candidate_topic": topic,
                "candidate_score": str(score),
                "overlap_terms": json.dumps(overlap, ensure_ascii=False),
                "qa_id": qa_row.get("qa_id", ""),
                "category": qa_row.get("category", ""),
                "source_question": snippet(qa_row.get("question", "")),
                "source_answer": snippet(qa_row.get("answer", "")),
                "leakage_warning": leakage_warning,
                "review_status": "needs_review",
                "suggested_action": "approve_if_medically_relevant_then_convert_to_supplemental_fact",
            }
            evidence_row["recommendation"] = recommendation_for(evidence_row, min_review_score)
            evidence_rows.append(evidence_row)
            json_candidates.append(evidence_row)

        discovery_json.append(
            {
                "query_id": row.get("query_id", ""),
                "query": row.get("query", ""),
                "candidate_topic": topic,
                "candidates": json_candidates,
            }
        )

    return failed_rows, topic_rows, evidence_rows, discovery_json


def write_report(failed_rows, topic_rows, evidence_rows, review_rows):
    topic_counts = Counter(row["candidate_topic"] for row in topic_rows)
    recommendation_counts = Counter(row["recommendation"] for row in evidence_rows)
    lines = [
        "# Supplemental Candidate Discovery Report",
        "",
        "This report proposes dataset-backed evidence candidates for low-evidence or low-reliability answers.",
        "It does not import anything into Neo4j. Every candidate still needs human review before becoming a supplemental fact.",
        "",
        f"- Failed or weak rows analyzed: {len(failed_rows)}",
        f"- Candidate evidence rows: {len(evidence_rows)}",
        f"- High-precision review rows: {len(review_rows)}",
        f"- Candidate topics CSV: `{relpath(CANDIDATE_TOPICS_CSV)}`",
        f"- Candidate evidence CSV: `{relpath(CANDIDATE_EVIDENCE_CSV)}`",
        f"- Candidate review CSV: `{relpath(CANDIDATE_REVIEW_CSV)}`",
        "",
        "## Topic Counts",
        "",
    ]
    for topic, count in topic_counts.most_common():
        lines.append(f"- {topic}: {count}")
    lines.extend(["", "## Recommendation Counts", ""])
    for recommendation, count in recommendation_counts.most_common():
        lines.append(f"- {recommendation}: {count}")
    lines.extend(["", "## Review Workflow", ""])
    lines.append("1. Open the candidate review CSV first.")
    lines.append("2. For each failed query, approve only rows whose source answer truly supports the missing fact.")
    lines.append("3. Convert approved rows into supplemental entities/relations.")
    lines.append("4. Re-run provenance, import into Neo4j, then rerun retrieval and generation.")
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--top-k", type=int, default=5, help="Candidate QA evidence rows per failed query.")
    parser.add_argument(
        "--min-review-score",
        type=float,
        default=1.0,
        help="Minimum lexical score for rows copied into the high-precision review CSV.",
    )
    args = parser.parse_args()

    final_rows = read_csv(FINAL_CSV)
    qa_rows = read_csv(QA_CSV)
    failed_rows, topic_rows, evidence_rows, discovery_json = discover_candidates(
        final_rows,
        qa_rows,
        args.top_k,
        args.min_review_score,
    )
    review_rows = [
        row
        for row in evidence_rows
        if row["recommendation"] == "recommended_for_human_review"
    ]

    write_csv(
        CANDIDATE_TOPICS_CSV,
        topic_rows,
        [
            "query_id",
            "query",
            "answerability_label",
            "reliability_label",
            "overall_reliability_score",
            "candidate_topic",
            "key_terms",
            "candidate_evidence_count",
            "review_status",
        ],
    )
    write_csv(
        CANDIDATE_EVIDENCE_CSV,
        evidence_rows,
        [
            "query_id",
            "rank",
            "candidate_topic",
            "candidate_score",
            "overlap_terms",
            "qa_id",
            "category",
            "source_question",
            "source_answer",
            "leakage_warning",
            "recommendation",
            "review_status",
            "suggested_action",
        ],
    )
    write_csv(
        CANDIDATE_REVIEW_CSV,
        review_rows,
        [
            "query_id",
            "rank",
            "candidate_topic",
            "candidate_score",
            "overlap_terms",
            "qa_id",
            "category",
            "source_question",
            "source_answer",
            "leakage_warning",
            "recommendation",
            "review_status",
            "suggested_action",
        ],
    )
    CANDIDATE_JSON.write_text(json.dumps(discovery_json, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(failed_rows, topic_rows, evidence_rows, review_rows)

    print(
        json.dumps(
            {
                "failed_or_weak_rows": len(failed_rows),
                "candidate_evidence_rows": len(evidence_rows),
                "candidate_review_rows": len(review_rows),
                "candidate_topics_csv": relpath(CANDIDATE_TOPICS_CSV),
                "candidate_evidence_csv": relpath(CANDIDATE_EVIDENCE_CSV),
                "candidate_review_csv": relpath(CANDIDATE_REVIEW_CSV),
                "candidate_json": relpath(CANDIDATE_JSON),
                "report_md": relpath(REPORT_MD),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
