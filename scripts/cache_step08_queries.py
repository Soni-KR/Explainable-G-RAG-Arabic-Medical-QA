"""Create a resumable Step 8 cache for an evaluation cohort.

This utility calls the unchanged production query-analysis/linking/planning
components. Successful rows are appended immediately, so a provider limit never
forces completed queries to be analyzed again.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path
from time import monotonic, sleep

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from scripts.evaluation_common import load_gold_queries
from src.config import load_final_config
from src.neo4j_repository import Neo4jRepository
from src.step08a_normalize_query import normalize_query
from src.step08b_analyze_query import analyze_and_link_query
from src.step08d_plan_retrieval import build_retrieval_plan


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GOLD = ROOT / "data" / "evaluation" / "entity_ground_truth_trial_100.csv"
DEFAULT_OUTPUT = (
    ROOT
    / "outputs"
    / "evaluation"
    / "cache"
    / "entity_ground_truth_trial_100"
    / "step08_success.jsonl"
)


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def append_jsonl(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
        handle.flush()


class RequestPacer:
    def __init__(self, interval_seconds: float) -> None:
        self.interval_seconds = max(0.0, interval_seconds)
        self.last_request_at: float | None = None

    def wait(self) -> None:
        if self.last_request_at is not None:
            remaining = self.interval_seconds - (monotonic() - self.last_request_at)
            if remaining > 0:
                sleep(remaining)
        self.last_request_at = monotonic()


def failed_warning(warnings: list[str]) -> str:
    return next(
        (
            warning
            for warning in warnings
            if "Unified LLM query analysis failed" in warning
        ),
        "",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Cache Step 8 for a gold query file.")
    parser.add_argument("--gold-file", type=Path, default=DEFAULT_GOLD)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--seed-cache",
        type=Path,
        default=None,
        help=(
            "Seed a new cache with compatible successful rows. Rows whose "
            "saved normalization differs from the current normalizer are skipped."
        ),
    )
    parser.add_argument("--request-interval-seconds", type=float, default=8.0)
    parser.add_argument("--max-rate-limit-retries", type=int, default=1)
    parser.add_argument("--rate-limit-backoff-seconds", type=float, default=60.0)
    args = parser.parse_args()

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    gold_queries = load_gold_queries(args.gold_file.resolve())
    output = args.output.resolve()
    if args.seed_cache and not output.exists():
        gold_by_id = {gold.query_id: gold for gold in gold_queries}
        for row in read_jsonl(args.seed_cache.resolve()):
            query_id = str(row.get("query_id") or "")
            gold = gold_by_id.get(query_id)
            analysis = dict(row.get("query_analysis") or {})
            if (
                gold
                and str(analysis.get("normalized_query") or "")
                == normalize_query(gold.query).normalized_query
            ):
                append_jsonl(output, row)
    existing_rows = read_jsonl(output)
    completed = {
        str(row.get("query_id")): row
        for row in existing_rows
        if row.get("query_id")
    }
    pacer = RequestPacer(args.request_interval_seconds)
    config = load_final_config()
    if config.graph_version != "final_v1":
        raise RuntimeError("Step 8 evaluation cache is restricted to final_v1.")

    new_calls = 0
    with Neo4jRepository(config=config) as repository:
        for index, gold in enumerate(gold_queries, start=1):
            if gold.query_id in completed:
                continue
            last_failure = ""
            for attempt in range(1, args.max_rate_limit_retries + 2):
                pacer.wait()
                analysis, linking = analyze_and_link_query(
                    gold.query,
                    repository=repository,
                    config=config,
                )
                new_calls += 1
                last_failure = failed_warning(analysis.warnings)
                if not last_failure:
                    plan = build_retrieval_plan(analysis, linking, config=config)
                    record = {
                        "query_id": gold.query_id,
                        "query_analysis": asdict(analysis),
                        "entity_linking": asdict(linking),
                        "retrieval_plan": asdict(plan),
                        "source": "live_production_step08",
                        "attempt": attempt,
                    }
                    append_jsonl(output, record)
                    completed[gold.query_id] = record
                    print(
                        json.dumps(
                            {
                                "progress": f"{index}/{len(gold_queries)}",
                                "query_id": gold.query_id,
                                "status": "ok",
                                "cached": False,
                            },
                            ensure_ascii=False,
                        ),
                        flush=True,
                    )
                    break
                if "HTTPError 429" not in last_failure:
                    raise RuntimeError(
                        f"Step 8 failed for {gold.query_id}: {last_failure}"
                    )
                if attempt <= args.max_rate_limit_retries:
                    sleep(args.rate_limit_backoff_seconds * attempt)
            else:
                print(
                    json.dumps(
                        {
                            "status": "rate_limited",
                            "completed": len(completed),
                            "remaining": len(gold_queries) - len(completed),
                            "failed_query_id": gold.query_id,
                            "cache": str(output.relative_to(ROOT)),
                        },
                        ensure_ascii=False,
                        indent=2,
                    )
                )
                return 2

    print(
        json.dumps(
            {
                "status": "complete",
                "queries": len(gold_queries),
                "cached_total": len(completed),
                "new_calls": new_calls,
                "output": str(output.relative_to(ROOT)),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
