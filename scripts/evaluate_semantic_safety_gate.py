from __future__ import annotations

"""Evaluate the deterministic post-semantic safety gate on reviewed claims."""

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.step14_semantic_safety_gate import semantic_rescue_safety_failures


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def metrics(labels: list[bool], predictions: list[bool]) -> dict[str, Any]:
    tp = sum(label and prediction for label, prediction in zip(labels, predictions))
    tn = sum(not label and not prediction for label, prediction in zip(labels, predictions))
    fp = sum(not label and prediction for label, prediction in zip(labels, predictions))
    fn = sum(label and not prediction for label, prediction in zip(labels, predictions))

    def divide(left: float, right: float) -> float:
        return left / right if right else 0.0

    precision = divide(tp, tp + fp)
    recall = divide(tp, tp + fn)
    return {
        "rows": len(labels),
        "true_positive": tp,
        "true_negative": tn,
        "false_positive": fp,
        "false_negative": fn,
        "accuracy": round(divide(tp + tn, len(labels)), 6),
        "precision_retain": round(precision, 6),
        "recall_retain": round(recall, 6),
        "f1_retain": round(
            divide(2 * precision * recall, precision + recall),
            6,
        ),
        "specificity_remove": round(divide(tn, tn + fp), 6),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate deterministic safety gates after semantic review."
    )
    parser.add_argument("--review-file", type=Path, required=True)
    parser.add_argument("--semantic-predictions", type=Path, required=True)
    parser.add_argument("--output-directory", type=Path, required=True)
    args = parser.parse_args()

    review_rows = read_csv(args.review_file.resolve())
    semantic_rows = read_csv(args.semantic_predictions.resolve())
    review = {
        (
            str(row.get("query_id") or ""),
            str(row.get("removed_claim") or ""),
        ): row
        for row in review_rows
    }
    semantic = {
        (
            str(row.get("query_id") or ""),
            str(row.get("claim") or ""),
        ): row
        for row in semantic_rows
    }
    if set(review) != set(semantic):
        raise ValueError("Review and semantic files do not contain identical claims.")

    output_rows: list[dict[str, Any]] = []
    labels: list[bool] = []
    before: list[bool] = []
    after: list[bool] = []
    failure_counts: Counter[str] = Counter()
    for key in sorted(review):
        human = review[key]
        prediction = semantic[key]
        label = str(human.get("human_should_retain") or "") == "yes"
        semantic_retain = (
            str(prediction.get("predicted_should_retain") or "") == "yes"
        )
        failures = (
            semantic_rescue_safety_failures(
                key[1],
                [str(human.get("cited_evidence") or "")],
            )
            if semantic_retain
            else []
        )
        failure_counts.update(failures)
        final_retain = semantic_retain and not failures
        labels.append(label)
        before.append(semantic_retain)
        after.append(final_retain)
        output_rows.append(
            {
                "query_id": key[0],
                "claim": key[1],
                "human_should_retain": "yes" if label else "no",
                "semantic_should_retain": "yes" if semantic_retain else "no",
                "safety_failures": " | ".join(failures),
                "final_should_retain": "yes" if final_retain else "no",
                "correct_final_decision": (
                    "yes" if final_retain == label else "no"
                ),
            }
        )

    before_metrics = metrics(labels, before)
    after_metrics = metrics(labels, after)
    payload = {
        "status": "complete",
        "review_file": str(args.review_file.resolve()),
        "semantic_predictions": str(args.semantic_predictions.resolve()),
        "baseline_metrics": before_metrics,
        "post_safety_gate_metrics": after_metrics,
        "gate_counts": dict(sorted(failure_counts.items())),
        "development_gate": {
            "maximum_false_positives": 0,
            "minimum_retain_recall": 0.80,
            "passed": bool(
                after_metrics["false_positive"] == 0
                and after_metrics["recall_retain"] >= 0.80
            ),
        },
        "network_used": False,
        "human_labels_used_only_for_scoring": True,
        "production_enabled": False,
    }
    output_directory = args.output_directory.resolve()
    if output_directory.exists():
        raise FileExistsError(f"Output already exists: {output_directory}")
    output_directory.mkdir(parents=True)
    with (output_directory / "predictions.csv").open(
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=list(output_rows[0]))
        writer.writeheader()
        writer.writerows(output_rows)
    (output_directory / "metrics.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
