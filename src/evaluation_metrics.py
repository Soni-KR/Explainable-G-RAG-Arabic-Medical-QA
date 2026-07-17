from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any, Hashable, Iterable, Sequence


_BERT_SCORERS: dict[str, Any] = {}


def _get_bert_scorer(lang: str) -> Any:
    """Load each language-specific BERTScore model once per evaluation process."""
    try:
        from bert_score import BERTScorer  # type: ignore[import-not-found]
    except ImportError:
        return None
    if lang not in _BERT_SCORERS:
        _BERT_SCORERS[lang] = BERTScorer(lang=lang, rescale_with_baseline=False)
    return _BERT_SCORERS[lang]


def _safe_divide(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0


def _rounded(value: float) -> float:
    return round(float(value), 6)


def precision_recall_f1(
    predicted: Iterable[Hashable],
    gold: Iterable[Hashable],
) -> dict[str, float | int]:
    """Compute exact-set precision, recall, and F1 without counting duplicates twice."""
    predicted_set = set(predicted)
    gold_set = set(gold)
    true_positives = len(predicted_set & gold_set)
    precision = _safe_divide(true_positives, len(predicted_set))
    recall = _safe_divide(true_positives, len(gold_set))
    f1 = _safe_divide(2 * precision * recall, precision + recall)
    return {
        "precision": _rounded(precision),
        "recall": _rounded(recall),
        "f1": _rounded(f1),
        "true_positives": true_positives,
        "predicted_count": len(predicted_set),
        "gold_count": len(gold_set),
    }


def entity_extraction_metrics(
    predicted_entities: Iterable[tuple[str, str]],
    gold_entities: Iterable[tuple[str, str]],
) -> dict[str, float | int]:
    """Score normalized `(entity_name, entity_type)` pairs against an annotated set."""
    return precision_recall_f1(predicted_entities, gold_entities)


def relation_extraction_metrics(
    candidate_triplets: Iterable[tuple[str, str, str]],
    predicted_triplets: Iterable[tuple[str, str, str]],
    gold_triplets: Iterable[tuple[str, str, str]],
) -> dict[str, Any]:
    """Compute candidate recall and exact validated-triplet precision/recall/F1."""
    candidates = set(candidate_triplets)
    gold = set(gold_triplets)
    candidate_recall = _safe_divide(len(candidates & gold), len(gold))
    triplet = precision_recall_f1(predicted_triplets, gold)
    return {"candidate_recall": _rounded(candidate_recall), "triplet": triplet}


def recall_at_k(
    ranked_ids: Sequence[Hashable],
    relevant_ids: Iterable[Hashable],
    k: int,
) -> float:
    relevant = set(relevant_ids)
    if not relevant:
        return 0.0
    return _safe_divide(len(set(ranked_ids[:k]) & relevant), len(relevant))


def reciprocal_rank(
    ranked_ids: Sequence[Hashable],
    relevant_ids: Iterable[Hashable],
) -> float:
    relevant = set(relevant_ids)
    for rank, item_id in enumerate(ranked_ids, start=1):
        if item_id in relevant:
            return 1.0 / rank
    return 0.0


def ndcg_at_k(
    ranked_ids: Sequence[Hashable],
    relevance_grades: dict[Hashable, float],
    k: int,
) -> float:
    def dcg(grades: Sequence[float]) -> float:
        return sum((2.0**grade - 1.0) / math.log2(rank + 2) for rank, grade in enumerate(grades))

    observed = [max(0.0, float(relevance_grades.get(item_id, 0.0))) for item_id in ranked_ids[:k]]
    ideal = sorted((max(0.0, float(value)) for value in relevance_grades.values()), reverse=True)[:k]
    return _safe_divide(dcg(observed), dcg(ideal))


def retrieval_metrics(
    ranked_ids: Sequence[Hashable],
    relevant_ids: Iterable[Hashable],
    relevance_grades: dict[Hashable, float] | None = None,
) -> dict[str, float | int | str]:
    """Evaluate one ranked retrieval result using independent relevance judgments."""
    relevant = set(relevant_ids)
    if not relevant:
        return {
            "status": "unavailable",
            "reason": "Independent relevant context IDs were not supplied.",
        }
    grades = relevance_grades or {item_id: 1.0 for item_id in relevant}
    return {
        "status": "computed",
        "recall_at_5": _rounded(recall_at_k(ranked_ids, relevant, 5)),
        "mrr": _rounded(reciprocal_rank(ranked_ids, relevant)),
        "ndcg_at_10": _rounded(ndcg_at_k(ranked_ids, grades, 10)),
        "ranked_count": len(ranked_ids),
        "relevant_count": len(relevant),
    }


def claim_grounding_metrics(statuses: Sequence[str]) -> dict[str, float | int]:
    """Measure deterministic claim support after Step 14 verification."""
    total = len(statuses)
    supported = sum(status == "supported" for status in statuses)
    weak = sum(status == "weakly_supported" for status in statuses)
    unsupported = sum(status == "unsupported" for status in statuses)
    return {
        "claim_count": total,
        "supported_claims": supported,
        "weakly_supported_claims": weak,
        "unsupported_claims": unsupported,
        "claim_support_rate": _rounded(_safe_divide(supported, total)),
        "hallucination_rate": _rounded(_safe_divide(unsupported, total)),
    }


def bertscore_f1(candidate: str, reference: str) -> dict[str, Any]:
    """Compute Arabic BERTScore when both a reference and the optional package exist."""
    if not reference.strip():
        return {"status": "unavailable", "reason": "A reference answer was not supplied."}
    scorer = _get_bert_scorer("ar")
    if scorer is None:
        return {"status": "unavailable", "reason": "The optional bert-score package is not installed."}
    _, _, f1 = scorer.score([candidate], [reference])
    return {"status": "computed", "bertscore_f1": _rounded(float(f1[0]))}


def entity_bertscore_f1(
    predicted_names: Sequence[str],
    gold_names: Sequence[str],
) -> dict[str, Any]:
    """Compute symmetric mean-best BERTScore for independently annotated entity names."""
    if not predicted_names or not gold_names:
        return {"status": "unavailable", "reason": "Predicted and gold entity names are required."}
    scorer = _get_bert_scorer("ar")
    if scorer is None:
        return {"status": "unavailable", "reason": "The optional bert-score package is not installed."}

    candidates = [candidate for candidate in predicted_names for _ in gold_names]
    references = [reference for _ in predicted_names for reference in gold_names]
    _, _, pair_f1 = scorer.score(candidates, references)
    matrix = [
        [float(pair_f1[row * len(gold_names) + column]) for column in range(len(gold_names))]
        for row in range(len(predicted_names))
    ]
    semantic_precision = sum(max(row) for row in matrix) / len(matrix)
    semantic_recall = sum(max(matrix[row][column] for row in range(len(matrix))) for column in range(len(gold_names))) / len(gold_names)
    semantic_f1 = _safe_divide(
        2 * semantic_precision * semantic_recall,
        semantic_precision + semantic_recall,
    )
    return {
        "status": "computed",
        "bertscore_precision": _rounded(semantic_precision),
        "bertscore_recall": _rounded(semantic_recall),
        "bertscore_f1": _rounded(semantic_f1),
    }


def ragas_metric_status(reference_available: bool) -> dict[str, Any]:
    """Describe why RAGAS scores are not silently approximated by local heuristics."""
    reasons = []
    if not reference_available:
        reasons.append("reference answers and annotated relevant contexts are required")
    try:
        import ragas  # type: ignore[import-not-found]  # noqa: F401
    except ImportError:
        reasons.append("the optional ragas package is not installed")
    if reasons:
        return {"status": "unavailable", "reason": "; ".join(reasons) + "."}
    return {
        "status": "not_run",
        "reason": "RAGAS requires an explicitly configured judge LLM and evaluation dataset.",
    }


def _validate_binary_samples(scores: Sequence[float], labels: Sequence[int]) -> None:
    if len(scores) != len(labels) or not scores:
        raise ValueError("Scores and labels must be non-empty and have the same length.")
    if any(label not in {0, 1} for label in labels):
        raise ValueError("Reliability labels must be binary values 0 or 1.")
    if any(not 0.0 <= score <= 1.0 for score in scores):
        raise ValueError("Reliability scores must be between 0 and 1.")
    if len(set(labels)) < 2:
        raise ValueError("AUROC/AUPRC require at least one positive and one negative label.")


def auroc(scores: Sequence[float], labels: Sequence[int]) -> float:
    """Compute AUROC using pairwise ordering with half credit for tied scores."""
    _validate_binary_samples(scores, labels)
    positives = [score for score, label in zip(scores, labels) if label == 1]
    negatives = [score for score, label in zip(scores, labels) if label == 0]
    wins = sum(
        1.0 if positive > negative else 0.5 if positive == negative else 0.0
        for positive in positives
        for negative in negatives
    )
    return wins / (len(positives) * len(negatives))


def auprc(scores: Sequence[float], labels: Sequence[int]) -> float:
    """Compute average precision, the step-wise area under the precision-recall curve."""
    _validate_binary_samples(scores, labels)
    ranked = sorted(zip(scores, labels), key=lambda item: item[0], reverse=True)
    positives = sum(labels)
    true_positives = 0
    precision_sum = 0.0
    for rank, (_, label) in enumerate(ranked, start=1):
        if label == 1:
            true_positives += 1
            precision_sum += true_positives / rank
    return precision_sum / positives


def calibration_analysis(
    scores: Sequence[float],
    labels: Sequence[int],
    bin_count: int = 10,
) -> dict[str, Any]:
    """Return Brier score and equal-width expected calibration error."""
    if len(scores) != len(labels) or not scores:
        raise ValueError("Scores and labels must be non-empty and have the same length.")
    if any(label not in {0, 1} for label in labels):
        raise ValueError("Calibration labels must be binary values 0 or 1.")
    brier = sum((score - label) ** 2 for score, label in zip(scores, labels)) / len(scores)
    bins = []
    ece = 0.0
    for index in range(bin_count):
        lower = index / bin_count
        upper = (index + 1) / bin_count
        members = [
            (score, label)
            for score, label in zip(scores, labels)
            if lower <= score <= upper and (index == bin_count - 1 or score < upper)
        ]
        if not members:
            continue
        mean_score = sum(score for score, _ in members) / len(members)
        observed_rate = sum(label for _, label in members) / len(members)
        ece += len(members) / len(scores) * abs(mean_score - observed_rate)
        bins.append(
            {
                "lower": _rounded(lower),
                "upper": _rounded(upper),
                "count": len(members),
                "mean_score": _rounded(mean_score),
                "observed_positive_rate": _rounded(observed_rate),
            }
        )
    return {"brier_score": _rounded(brier), "expected_calibration_error": _rounded(ece), "bins": bins}


def threshold_analysis(
    scores: Sequence[float],
    labels: Sequence[int],
    thresholds: Sequence[float] | None = None,
) -> list[dict[str, float | int]]:
    """Show precision/recall/F1/specificity trade-offs for reliability thresholds."""
    if len(scores) != len(labels) or not scores:
        raise ValueError("Scores and labels must be non-empty and have the same length.")
    thresholds = thresholds or [index / 10 for index in range(1, 10)]
    rows = []
    for threshold in thresholds:
        predicted = [int(score >= threshold) for score in scores]
        tp = sum(prediction == 1 and label == 1 for prediction, label in zip(predicted, labels))
        fp = sum(prediction == 1 and label == 0 for prediction, label in zip(predicted, labels))
        tn = sum(prediction == 0 and label == 0 for prediction, label in zip(predicted, labels))
        fn = sum(prediction == 0 and label == 1 for prediction, label in zip(predicted, labels))
        precision = _safe_divide(tp, tp + fp)
        recall = _safe_divide(tp, tp + fn)
        rows.append(
            {
                "threshold": _rounded(threshold),
                "precision": _rounded(precision),
                "recall": _rounded(recall),
                "f1": _rounded(_safe_divide(2 * precision * recall, precision + recall)),
                "specificity": _rounded(_safe_divide(tn, tn + fp)),
                "true_positives": tp,
                "false_positives": fp,
                "true_negatives": tn,
                "false_negatives": fn,
            }
        )
    return rows


def reliability_metrics(scores: Sequence[float], labels: Sequence[int]) -> dict[str, Any]:
    """Evaluate reliability ranking and calibration once human binary labels exist."""
    return {
        "auroc": _rounded(auroc(scores, labels)),
        "auprc": _rounded(auprc(scores, labels)),
        "calibration": calibration_analysis(scores, labels),
        "thresholds": threshold_analysis(scores, labels),
    }


def efficiency_metrics(stage_timings_ms: Sequence[dict[str, float]]) -> dict[str, Any]:
    """Aggregate latency dictionaries from repeated end-to-end runs."""
    if not stage_timings_ms:
        return {"status": "unavailable", "reason": "No timed runs were supplied."}
    keys = sorted({key for row in stage_timings_ms for key in row})
    averages = {
        key: _rounded(sum(row.get(key, 0.0) for row in stage_timings_ms) / len(stage_timings_ms))
        for key in keys
    }
    return {"status": "computed", "run_count": len(stage_timings_ms), "average_latency_ms": averages}


def load_reliability_jsonl(path: Path) -> tuple[list[float], list[int]]:
    scores: list[float] = []
    labels: list[int] = []
    with path.open("r", encoding="utf-8-sig") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            if not raw_line.strip():
                continue
            row = json.loads(raw_line)
            try:
                scores.append(float(row["score"]))
                labels.append(int(row["label"]))
            except (KeyError, TypeError, ValueError) as exc:
                raise ValueError(f"Invalid score/label at line {line_number}.") from exc
    return scores, labels


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate reliability scores against human binary labels.")
    parser.add_argument("--reliability-jsonl", type=Path, required=True, help="JSONL rows with score and label.")
    args = parser.parse_args()
    try:
        scores, labels = load_reliability_jsonl(args.reliability_jsonl)
        payload = reliability_metrics(scores, labels)
    except Exception as exc:
        payload = {"status": "failed", "error": str(exc)}
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 1
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
