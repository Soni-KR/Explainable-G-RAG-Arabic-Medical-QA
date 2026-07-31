from __future__ import annotations

"""Compare two completed claim-adjudication evaluations claim by claim."""

import argparse
import csv
import json
from pathlib import Path
from typing import Any


def read_csv(path: Path) -> dict[tuple[str, str], dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    indexed = {
        (
            str(row.get("query_id") or "").strip(),
            str(row.get("claim") or "").strip(),
        ): row
        for row in rows
    }
    if len(indexed) != len(rows) or any(not all(key) for key in indexed):
        raise ValueError(f"Duplicate or blank claim key in {path}.")
    return indexed


def read_metrics(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def retained(row: dict[str, str]) -> bool:
    return str(row.get("predicted_should_retain") or "").strip() == "yes"


def human_retain(row: dict[str, str]) -> bool:
    return str(row.get("human_should_retain") or "").strip() == "yes"


def claim_summary(key: tuple[str, str]) -> dict[str, str]:
    return {"query_id": key[0], "claim": key[1]}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compare completed semantic claim-adjudication runs."
    )
    parser.add_argument("--baseline-predictions", type=Path, required=True)
    parser.add_argument("--baseline-metrics", type=Path, required=True)
    parser.add_argument("--candidate-predictions", type=Path, required=True)
    parser.add_argument("--candidate-metrics", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    baseline = read_csv(args.baseline_predictions.resolve())
    candidate = read_csv(args.candidate_predictions.resolve())
    if set(baseline) != set(candidate):
        raise ValueError("The two runs do not contain the same reviewed claims.")
    if any(
        human_retain(baseline[key]) != human_retain(candidate[key])
        for key in baseline
    ):
        raise ValueError("Human labels differ between the two runs.")

    unsafe_fixed: list[dict[str, str]] = []
    unsafe_introduced: list[dict[str, str]] = []
    unsafe_persistent: list[dict[str, str]] = []
    valid_recovered: list[dict[str, str]] = []
    valid_lost: list[dict[str, str]] = []
    for key in sorted(baseline):
        expected = human_retain(baseline[key])
        before = retained(baseline[key])
        after = retained(candidate[key])
        if not expected and before and not after:
            unsafe_fixed.append(claim_summary(key))
        elif not expected and not before and after:
            unsafe_introduced.append(claim_summary(key))
        elif not expected and before and after:
            unsafe_persistent.append(claim_summary(key))
        elif expected and not before and after:
            valid_recovered.append(claim_summary(key))
        elif expected and before and not after:
            valid_lost.append(claim_summary(key))

    baseline_metrics = read_metrics(args.baseline_metrics.resolve())
    candidate_metrics = read_metrics(args.candidate_metrics.resolve())
    payload = {
        "status": "complete",
        "baseline": {
            "predictions": str(args.baseline_predictions.resolve()),
            "metrics": baseline_metrics["retain_decision"],
        },
        "candidate": {
            "predictions": str(args.candidate_predictions.resolve()),
            "metrics": candidate_metrics["retain_decision"],
        },
        "claim_changes": {
            "unsafe_fixed": unsafe_fixed,
            "unsafe_introduced": unsafe_introduced,
            "unsafe_persistent": unsafe_persistent,
            "valid_recovered": valid_recovered,
            "valid_lost": valid_lost,
        },
        "safety_gate": {
            "maximum_false_positives": 0,
            "candidate_passed": (
                candidate_metrics["retain_decision"]["false_positive"] == 0
            ),
        },
        "decision": "reject_candidate",
        "reason": (
            "The candidate retained four human-rejected claims and reduced "
            "valid-claim recall and F1."
        ),
    }
    if args.output.exists():
        raise FileExistsError(f"Output already exists: {args.output}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "status": "ok",
                "decision": payload["decision"],
                "unsafe_fixed": len(unsafe_fixed),
                "unsafe_introduced": len(unsafe_introduced),
                "unsafe_persistent": len(unsafe_persistent),
                "valid_recovered": len(valid_recovered),
                "valid_lost": len(valid_lost),
                "output": str(args.output.resolve()),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
