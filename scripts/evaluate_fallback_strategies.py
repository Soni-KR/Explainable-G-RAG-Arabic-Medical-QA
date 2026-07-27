from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".bsdeps"))
sys.path.insert(0, str(ROOT / "scripts"))

from bert_score import score as bert_score  # noqa: E402
from step13_17_utils import lexical_overlap  # noqa: E402


CONTEXTS_JSON = ROOT / "outputs/05_trial_graph_v1/context_construction/trial_graph_v1_context_bundles.json"
ANSWERS_CSV = ROOT / "outputs/05_trial_graph_v1/answer_generation/trial_graph_v1_answers.csv"
RAW_RESPONSES_JSONL = ROOT / "outputs/05_trial_graph_v1/answer_generation/trial_graph_v1_answer_generation_raw_responses.jsonl"
REFERENCES_CSV = ROOT / "retrieval_gold_annotations_100.csv"
OUT_DIR = ROOT / "outputs/05_trial_graph_v1/evaluation/fallback_strategy_ablation"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def truncate_text(value: str, limit: int) -> str:
    value = " ".join(str(value or "").split())
    return value if len(value) <= limit else value[: limit - 3].rstrip() + "..."


def is_insufficient(answer: str) -> bool:
    return "لا توجد أدلة كافية" in answer or "الأدلة المسترجعة غير كافية" in answer


def raw_answers() -> dict[str, str]:
    latest = {}
    for line in RAW_RESPONSES_JSONL.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("status") != "ok":
            continue
        try:
            parsed = json.loads(row.get("response_text", ""))
        except json.JSONDecodeError:
            continue
        latest[row["query_id"]] = parsed.get("answer_ar", "")
    return latest


def evidence_candidates(bundle: dict) -> list[dict]:
    candidates = []
    evidence_number = 1
    query = bundle.get("query", "")
    for edge in bundle.get("graph_context", []) or []:
        relation_score = float(edge.get("rerank_score") or 0.0)
        relation_text = edge.get("relation", "")
        for evidence in edge.get("supporting_evidence", []) or []:
            source_answer = truncate_text(evidence.get("source_answer", ""), 700)
            evidence_text = truncate_text(evidence.get("evidence_text", ""), 450)
            source_question = evidence.get("source_question", "")
            text = source_answer or evidence_text
            if text:
                candidates.append(
                    {
                        "evidence_id": f"E{evidence_number}",
                        "qa_id": evidence.get("qa_id", ""),
                        "text": text,
                        "relation": relation_text,
                        "relation_score": relation_score,
                        "q_sq": lexical_overlap(query, source_question),
                        "q_sa": lexical_overlap(query, source_answer),
                        "q_ev": lexical_overlap(query, evidence_text),
                    }
                )
            evidence_number += 1
    return candidates


def choose_candidate(candidates: list[dict], strategy: str) -> dict:
    if not candidates:
        return {}
    if strategy == "top_rerank":
        key = lambda c: (c["relation_score"], len(c["text"]))
    elif strategy == "query_source_question":
        key = lambda c: (c["q_sq"], c["relation_score"], len(c["text"]))
    elif strategy == "query_source_answer":
        key = lambda c: (c["q_sa"], c["relation_score"], len(c["text"]))
    elif strategy == "query_evidence":
        key = lambda c: (c["q_ev"], c["relation_score"], len(c["text"]))
    elif strategy == "combined_query_weighted":
        key = lambda c: (
            (0.45 * c["q_sq"]) + (0.25 * c["q_sa"]) + (0.15 * c["q_ev"]) + (0.15 * c["relation_score"]),
            len(c["text"]),
        )
    else:
        raise ValueError(strategy)
    return max(candidates, key=key)


def fallback_answer(candidate: dict, answer_format: str) -> str:
    if not candidate:
        return "لا توجد أدلة كافية."
    if answer_format == "text_only":
        return candidate["text"]
    citation = candidate["evidence_id"]
    qa_id = candidate.get("qa_id", "")
    source_note = f" [{citation}" + (f" | {qa_id}]" if qa_id else "]")
    if answer_format == "text_with_citation":
        return f"{candidate['text']}{source_note}"
    return f"بحسب الأدلة المسترجعة من قاعدة AHD: {candidate['text']}{source_note}"


def main() -> None:
    contexts = {row["query_id"]: row for row in json.loads(CONTEXTS_JSON.read_text(encoding="utf-8"))}
    answers = raw_answers()
    refs = {row["query_id"]: row["reference_answer"] for row in read_csv(REFERENCES_CSV)}
    strategies = [
        "top_rerank",
        "query_source_question",
        "query_source_answer",
        "query_evidence",
        "combined_query_weighted",
    ]
    answer_formats = ["prefixed_cited", "text_with_citation", "text_only"]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    summary_rows = []
    for strategy in strategies:
        for answer_format in answer_formats:
            rows = []
            for query_id, reference in refs.items():
                original = answers.get(query_id, "")
                if original and not is_insufficient(original):
                    candidate_answer = original
                    selection = "original_llm_answer"
                else:
                    selected = choose_candidate(evidence_candidates(contexts.get(query_id, {})), strategy)
                    candidate_answer = fallback_answer(selected, answer_format)
                    selection = selected.get("qa_id", "")
                rows.append(
                    {
                        "query_id": query_id,
                        "candidate_answer": candidate_answer,
                        "reference_answer": reference,
                        "selection": selection,
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
            experiment = f"{strategy}_{answer_format}"
            with (OUT_DIR / f"{experiment}.csv").open("w", encoding="utf-8-sig", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
                writer.writeheader()
                writer.writerows(rows)
            summary_rows.append(
                {
                    "strategy": strategy,
                    "answer_format": answer_format,
                    "mean_precision": round(sum(row["bertscore_precision"] for row in rows) / len(rows), 6),
                    "mean_recall": round(sum(row["bertscore_recall"] for row in rows) / len(rows), 6),
                    "mean_f1": round(sum(row["bertscore_f1"] for row in rows) / len(rows), 6),
                }
            )
    summary_rows.sort(key=lambda row: row["mean_f1"], reverse=True)
    with (OUT_DIR / "summary.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(summary_rows[0].keys()))
        writer.writeheader()
        writer.writerows(summary_rows)
    print(json.dumps(summary_rows, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
