from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".bsdeps"))

from bert_score import score as bert_score  # noqa: E402


TOKEN_RE = re.compile(r"[\w\u0600-\u06ff]+", re.UNICODE)
DIACRITICS_RE = re.compile(r"[\u064b-\u065f\u0670\u06d6-\u06ed]")
TATWEEL_RE = re.compile(r"\u0640+")
ARABIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")
ARABIC_LETTER_NORMALIZATION = str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ى": "ي", "ئ": "ي", "ؤ": "و", "ة": "ه"})


def normalize(text: str) -> str:
    text = str(text or "").translate(ARABIC_DIGITS)
    text = TATWEEL_RE.sub("", text)
    text = DIACRITICS_RE.sub("", text)
    text = text.translate(ARABIC_LETTER_NORMALIZATION)
    return " ".join(text.lower().split())


def tokens(text: str) -> set[str]:
    return set(TOKEN_RE.findall(normalize(text)))


def overlap(query_tokens: set[str], doc_tokens: set[str]) -> float:
    if not query_tokens or not doc_tokens:
        return 0.0
    return len(query_tokens & doc_tokens) / ((len(query_tokens) * len(doc_tokens)) ** 0.5)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def main() -> None:
    gold = read_csv(ROOT / "retrieval_gold_annotations_100.csv")
    ahd = read_csv(ROOT / "AHD.csv")
    indexed = []
    for idx, row in enumerate(ahd):
        question = row.get("Question", "")
        answer = row.get("Answer", "")
        if question and answer:
            indexed.append(
                {
                    "row_index": idx,
                    "question": question,
                    "question_norm": normalize(question),
                    "answer": answer,
                    "tokens": tokens(question),
                }
            )

    rows = []
    exact_matches = 0
    for item in gold:
        q = item["query"]
        q_norm = normalize(q)
        q_tokens = tokens(q)
        pool = [row for row in indexed if row["question_norm"] != q_norm]
        best = max(pool, key=lambda row: overlap(q_tokens, row["tokens"]))
        if normalize(best["question"]) == q_norm:
            exact_matches += 1
        rows.append(
            {
                "query_id": item["query_id"],
                "query": q,
                "candidate_answer": best["answer"],
                "reference_answer": item["reference_answer"],
                "selected_ahd_row_index": best["row_index"],
                "selected_ahd_question": best["question"],
                "lexical_score": round(overlap(q_tokens, best["tokens"]), 6),
                "exact_question_match": str(normalize(best["question"]) == q_norm).lower(),
            }
        )

    precision, recall, f1 = bert_score(
        [row["candidate_answer"] for row in rows],
        [row["reference_answer"] for row in rows],
        model_type="bert-base-multilingual-cased",
        lang="ar",
        batch_size=8,
        verbose=False,
        rescale_with_baseline=False,
    )
    for row, p, r, f in zip(rows, precision.tolist(), recall.tolist(), f1.tolist()):
        row["bertscore_precision"] = round(float(p), 6)
        row["bertscore_recall"] = round(float(r), 6)
        row["bertscore_f1"] = round(float(f), 6)

    out_dir = ROOT / "outputs/05_trial_graph_v1/evaluation/ahd_qa_fallback"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_csv = out_dir / "ahd_full_corpus_lexical_qa_fallback.csv"
    with out_csv.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    summary = {
        "rows": len(rows),
        "ahd_rows_indexed": len(indexed),
        "exact_question_matches": exact_matches,
        "mean_precision": round(sum(row["bertscore_precision"] for row in rows) / len(rows), 6),
        "mean_recall": round(sum(row["bertscore_recall"] for row in rows) / len(rows), 6),
        "mean_f1": round(sum(row["bertscore_f1"] for row in rows) / len(rows), 6),
        "per_question_csv": str(out_csv.relative_to(ROOT)),
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
