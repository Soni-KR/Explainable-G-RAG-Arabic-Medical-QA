"""Evaluate the frozen final run without rerunning the Graph-RAG pipeline.

The AHD source answer attached to each evaluation query is treated as a
dataset-reference answer for automatic metrics. It is not presented as
clinician-adjudicated gold.

The script has two independent parts:

1. BERTScore runs locally with multilingual BERT.
2. RAGAS uses a configurable evaluator LLM and local multilingual E5
   embeddings. Successful per-metric calls are append-cached and resumable.

No retrieval, reranking, context construction, generation, verification, or
Neo4j operation is performed here.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import platform
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path
from statistics import mean
from typing import Any

from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RUN_ID = "full_pipeline_retrieval_v2_targeted_fts_reranked_network_v1"
DEFAULT_INPUT = (
    ROOT
    / "outputs"
    / "evaluation"
    / "generation"
    / DEFAULT_RUN_ID
    / "full_pipeline.jsonl"
)
DEFAULT_OUTPUT = (
    ROOT
    / "outputs"
    / "evaluation"
    / "offline_metrics"
    / "final_run_ahd_reference_v1"
)

RAGAS_METRICS = (
    "context_recall",
    "context_precision",
    "faithfulness",
    "answer_relevancy",
)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL at {path}:{line_number}") from exc
    return rows


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")
        handle.flush()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def clean_text(value: Any) -> str:
    return str(value or "").strip()


def retrieved_contexts(row: dict[str, Any]) -> list[str]:
    context = ((row.get("raw") or {}).get("context") or {}).get("evidence_items") or []
    texts: list[str] = []
    for item in context:
        evidence = clean_text(item.get("evidence"))
        if not evidence:
            question = clean_text(item.get("source_question"))
            answer = clean_text(item.get("source_answer"))
            evidence = "\n".join(part for part in (question, answer) if part)
        if evidence and evidence not in texts:
            texts.append(evidence)
    return texts


def is_generated(row: dict[str, Any]) -> bool:
    return clean_text(row.get("generation_status")) == "generated"


def is_substantive(row: dict[str, Any]) -> bool:
    return bool(row.get("output_claims"))


def scope_for_row(row: dict[str, Any]) -> list[str]:
    scopes = ["all_100"]
    if is_generated(row):
        scopes.append("generated_66")
    if is_substantive(row):
        scopes.append("substantive_26")
    return scopes


def load_success_cache(path: Path) -> dict[tuple[str, str], dict[str, Any]]:
    if not path.exists():
        return {}
    cache: dict[tuple[str, str], dict[str, Any]] = {}
    for row in load_jsonl(path):
        if row.get("status") != "ok":
            continue
        key = (clean_text(row.get("query_id")), clean_text(row.get("metric")))
        cache[key] = row
    return cache


def extract_metric_value(result: Any) -> tuple[float, str]:
    value = getattr(result, "value", result)
    reason = clean_text(getattr(result, "reason", ""))
    return float(value), reason


def bertscore_records(
    rows: list[dict[str, Any]],
    model_type: str,
    batch_size: int,
) -> list[dict[str, Any]]:
    from bert_score import BERTScorer

    candidates = [clean_text(row.get("answer")) for row in rows]
    references = [clean_text((row.get("gold") or {}).get("reference_answer")) for row in rows]
    if any(not reference for reference in references):
        raise ValueError("Every frozen row must contain an AHD reference answer.")

    scorer = BERTScorer(
        model_type=model_type,
        lang="ar",
        rescale_with_baseline=False,
        device="cpu",
    )
    precision, recall, f1 = scorer.score(
        candidates,
        references,
        batch_size=batch_size,
    )
    records: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        records.append(
            {
                "query_id": clean_text(row.get("query_id")),
                "generation_status": clean_text(row.get("generation_status")),
                "substantive": is_substantive(row),
                "precision": round(float(precision[index]), 6),
                "recall": round(float(recall[index]), 6),
                "f1": round(float(f1[index]), 6),
                "model": model_type,
                "reference_type": "original_ahd_answer",
            }
        )
    return records


def summarize_bertscore(records: list[dict[str, Any]]) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    scope_predicates = {
        "all_100": lambda row: True,
        "generated_66": lambda row: row["generation_status"] == "generated",
        "substantive_26": lambda row: bool(row["substantive"]),
    }
    for scope, predicate in scope_predicates.items():
        selected = [row for row in records if predicate(row)]
        summary[scope] = {
            "evaluated_queries": len(selected),
            "precision": round(mean(row["precision"] for row in selected), 6),
            "recall": round(mean(row["recall"] for row in selected), 6),
            "f1": round(mean(row["f1"] for row in selected), 6),
        }
    return summary


def ragas_metric_arguments(
    metric_name: str,
    row: dict[str, Any],
    contexts: list[str],
) -> dict[str, Any]:
    query = clean_text(row.get("query"))
    answer = clean_text(row.get("answer"))
    reference = clean_text((row.get("gold") or {}).get("reference_answer"))
    if metric_name == "context_recall":
        return {
            "user_input": query,
            "retrieved_contexts": contexts,
            "reference": reference,
        }
    if metric_name == "context_precision":
        return {
            "user_input": query,
            "reference": reference,
            "retrieved_contexts": contexts,
        }
    if metric_name == "faithfulness":
        return {
            "user_input": query,
            "response": answer,
            "retrieved_contexts": contexts,
        }
    if metric_name == "answer_relevancy":
        return {"user_input": query, "response": answer}
    raise ValueError(f"Unsupported RAGAS metric: {metric_name}")


def metric_is_applicable(metric_name: str, row: dict[str, Any]) -> bool:
    if metric_name == "faithfulness":
        return is_substantive(row) and bool(retrieved_contexts(row))
    if metric_name == "answer_relevancy":
        return is_generated(row)
    return True


async def score_with_retries(
    scorer: Any,
    kwargs: dict[str, Any],
    retries: int,
    retry_delay_seconds: float,
) -> tuple[float, str, int]:
    attempts = 0
    while True:
        attempts += 1
        try:
            result = await scorer.ascore(**kwargs)
            value, reason = extract_metric_value(result)
            return value, reason, attempts
        except Exception:
            if attempts > retries:
                raise
            await asyncio.sleep(retry_delay_seconds)


def is_rate_limit_error(exc: Exception) -> bool:
    text = f"{type(exc).__name__}: {exc}".lower()
    return "429" in text or "rate limit" in text or "rate_limit" in text


async def run_ragas(
    rows: list[dict[str, Any]],
    output_dir: Path,
    metric_names: tuple[str, ...],
    evaluator_provider: str,
    evaluator_base_url: str,
    evaluator_api_key_env: str,
    evaluator_model: str,
    embedding_model: str,
    request_interval_seconds: float,
    max_retries: int,
    retry_delay_seconds: float,
    limit: int,
) -> dict[str, Any]:
    from openai import AsyncOpenAI
    from ragas.embeddings.base import embedding_factory
    from ragas.llms import llm_factory
    from ragas.metrics.collections import (
        AnswerRelevancy,
        ContextPrecision,
        ContextRecall,
        Faithfulness,
    )

    successes_path = output_dir / "ragas_success.jsonl"
    errors_path = output_dir / "ragas_errors.jsonl"
    cache = load_success_cache(successes_path)
    selected_rows = rows[:limit] if limit > 0 else rows
    deterministic_empty_context = 0

    # Empty retrieval context has zero context recall/precision by definition.
    # Materialize these rows before any evaluator call so quota failures cannot
    # hide the retrieval failures that require no LLM judgment.
    for row in selected_rows:
        query_id = clean_text(row.get("query_id"))
        contexts = retrieved_contexts(row)
        if contexts:
            continue
        for metric_name in metric_names:
            if metric_name not in {"context_recall", "context_precision"}:
                continue
            cache_key = (query_id, metric_name)
            if cache_key in cache:
                continue
            record = {
                "status": "ok",
                "query_id": query_id,
                "metric": metric_name,
                "value": 0.0,
                "reason": "No retrieved context.",
                "evaluation_method": "deterministic_empty_context",
                "model": "",
                "attempts": 0,
                "context_count": 0,
                "scopes": scope_for_row(row),
            }
            append_jsonl(successes_path, record)
            cache[cache_key] = record
            deterministic_empty_context += 1

    api_key = clean_text(os.getenv(evaluator_api_key_env))
    if not api_key:
        raise RuntimeError(
            f"{evaluator_api_key_env} is required for {evaluator_provider} "
            "RAGAS evaluator calls."
        )

    client = AsyncOpenAI(
        api_key=api_key,
        base_url=evaluator_base_url,
        timeout=120.0,
        max_retries=0,
    )
    evaluator_llm = llm_factory(
        evaluator_model,
        client=client,
        temperature=0.0,
    )
    local_embeddings = None
    if "answer_relevancy" in metric_names:
        os.environ.setdefault("HF_HUB_OFFLINE", "1")
        os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
        local_embeddings = embedding_factory(
            "huggingface",
            model=embedding_model,
            local_files_only=True,
        )
    scorers: dict[str, Any] = {}
    if "context_recall" in metric_names:
        scorers["context_recall"] = ContextRecall(llm=evaluator_llm)
    if "context_precision" in metric_names:
        scorers["context_precision"] = ContextPrecision(llm=evaluator_llm)
    if "faithfulness" in metric_names:
        scorers["faithfulness"] = Faithfulness(llm=evaluator_llm)
    if "answer_relevancy" in metric_names:
        scorers["answer_relevancy"] = AnswerRelevancy(
            llm=evaluator_llm,
            embeddings=local_embeddings,
            strictness=1,
        )

    calls_made = 0
    skipped_cached = 0
    stopped_on_rate_limit = False

    for row_index, row in enumerate(selected_rows, start=1):
        query_id = clean_text(row.get("query_id"))
        contexts = retrieved_contexts(row)
        for metric_name in metric_names:
            cache_key = (query_id, metric_name)
            if cache_key in cache:
                skipped_cached += 1
                continue
            if not metric_is_applicable(metric_name, row):
                continue
            if calls_made > 0 and request_interval_seconds > 0:
                await asyncio.sleep(request_interval_seconds)
            started = time.perf_counter()
            try:
                value, reason, attempts = await score_with_retries(
                    scorers[metric_name],
                    ragas_metric_arguments(metric_name, row, contexts),
                    retries=max_retries,
                    retry_delay_seconds=retry_delay_seconds,
                )
            except Exception as exc:
                error = {
                    "status": "error",
                    "query_id": query_id,
                    "metric": metric_name,
                    "error_type": type(exc).__name__,
                    "error": clean_text(exc),
                    "context_count": len(contexts),
                    "created_at_utc": datetime.now(timezone.utc).isoformat(),
                }
                append_jsonl(errors_path, error)
                print(
                    json.dumps(
                        {
                            "progress": f"{row_index}/{len(selected_rows)}",
                            "query_id": query_id,
                            "metric": metric_name,
                            "status": "error",
                            "error_type": type(exc).__name__,
                        },
                        ensure_ascii=False,
                    ),
                    flush=True,
                )
                if is_rate_limit_error(exc):
                    stopped_on_rate_limit = True
                    return {
                        "status": "rate_limited",
                        "calls_made": calls_made,
                        "skipped_cached": skipped_cached,
                        "deterministic_empty_context": deterministic_empty_context,
                        "stopped_on_rate_limit": stopped_on_rate_limit,
                    }
                continue

            calls_made += 1
            record = {
                "status": "ok",
                "query_id": query_id,
                "metric": metric_name,
                "value": round(value, 6),
                "reason": reason,
                "evaluation_method": "ragas_0_4_3",
                "model": evaluator_model,
                "attempts": attempts,
                "context_count": len(contexts),
                "latency_ms": round((time.perf_counter() - started) * 1000.0, 3),
                "scopes": scope_for_row(row),
            }
            append_jsonl(successes_path, record)
            cache[cache_key] = record
            print(
                json.dumps(
                    {
                        "progress": f"{row_index}/{len(selected_rows)}",
                        "query_id": query_id,
                        "metric": metric_name,
                        "status": "ok",
                        "value": record["value"],
                    },
                    ensure_ascii=False,
                ),
                flush=True,
            )

    return {
        "status": "complete",
        "calls_made": calls_made,
        "skipped_cached": skipped_cached,
        "deterministic_empty_context": deterministic_empty_context,
        "stopped_on_rate_limit": stopped_on_rate_limit,
    }


def summarize_ragas(path: Path) -> dict[str, Any]:
    records = list(load_success_cache(path).values())
    result: dict[str, Any] = {}
    for metric_name in RAGAS_METRICS:
        metric_rows = [row for row in records if row["metric"] == metric_name]
        metric_summary: dict[str, Any] = {
            "available_scores": len(metric_rows),
            "scopes": {},
        }
        for scope in ("all_100", "generated_66", "substantive_26"):
            selected = [row for row in metric_rows if scope in (row.get("scopes") or [])]
            metric_summary["scopes"][scope] = {
                "evaluated_queries": len(selected),
                "mean": (
                    round(mean(float(row["value"]) for row in selected), 6)
                    if selected
                    else None
                ),
            }
        result[metric_name] = metric_summary
    return result


def build_manifest(
    input_path: Path,
    rows: list[dict[str, Any]],
    args: argparse.Namespace,
) -> dict[str, Any]:
    return {
        "evaluation_name": "frozen_final_run_ahd_reference_v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "frozen_run_id": DEFAULT_RUN_ID,
        "input_path": str(input_path.relative_to(ROOT)),
        "input_sha256": sha256(input_path),
        "query_count": len(rows),
        "reference_type": "original_ahd_answer",
        "reference_status": (
            "dataset_reference_for_automatic_evaluation; not clinician-adjudicated"
        ),
        "pipeline_rerun": False,
        "retrieval_rerun": False,
        "generation_rerun": False,
        "bertscore_model": args.bertscore_model,
        "ragas_version": version("ragas"),
        "ragas_evaluator_provider": args.evaluator_provider,
        "ragas_evaluator_base_url": args.evaluator_base_url,
        "ragas_evaluator_api_key_env": args.evaluator_api_key_env,
        "ragas_evaluator_model": args.evaluator_model,
        "ragas_embedding_model": args.embedding_model,
        "ragas_metrics": list(args.metric),
        "ragas_metric_scopes": {
            "context_recall": "all_100; empty context is deterministically 0",
            "context_precision": "all_100; empty context is deterministically 0",
            "faithfulness": "substantive_26",
            "answer_relevancy": "generated_66",
        },
        "answer_relevancy_strictness": 1,
        "runtime": {
            "python": sys.version,
            "platform": platform.platform(),
            "executable": sys.executable,
            "bert_score": version("bert-score"),
            "ragas": version("ragas"),
            "sentence_transformers": version("sentence-transformers"),
        },
        "secrets_recorded": False,
    }


def main() -> int:
    load_dotenv(ROOT / ".env")
    parser = argparse.ArgumentParser(
        description="Offline BERTScore and RAGAS evaluation for the frozen final run."
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--metric",
        action="append",
        choices=RAGAS_METRICS,
        default=[],
        help="RAGAS metric to run; repeat. Defaults to all four.",
    )
    parser.add_argument("--skip-bertscore", action="store_true")
    parser.add_argument("--skip-ragas", action="store_true")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument(
        "--bertscore-model",
        default="bert-base-multilingual-cased",
    )
    parser.add_argument("--bertscore-batch-size", type=int, default=4)
    parser.add_argument(
        "--evaluator-model",
        default=os.getenv("RAGAS_EVALUATOR_MODEL", "openai/gpt-oss-20b"),
    )
    parser.add_argument(
        "--evaluator-provider",
        default=os.getenv("RAGAS_EVALUATOR_PROVIDER", "groq"),
    )
    parser.add_argument(
        "--evaluator-base-url",
        default=os.getenv(
            "RAGAS_EVALUATOR_BASE_URL",
            "https://api.groq.com/openai/v1",
        ),
    )
    parser.add_argument(
        "--evaluator-api-key-env",
        default=os.getenv("RAGAS_EVALUATOR_API_KEY_ENV", "GROQ_API_KEY"),
        help="Environment-variable name containing the evaluator key.",
    )
    parser.add_argument(
        "--embedding-model",
        default="intfloat/multilingual-e5-base",
    )
    parser.add_argument("--request-interval-seconds", type=float, default=8.0)
    parser.add_argument("--max-retries", type=int, default=0)
    parser.add_argument("--retry-delay-seconds", type=float, default=30.0)
    args = parser.parse_args()

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args.input = args.input.resolve()
    args.output_dir = args.output_dir.resolve()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    args.metric = tuple(args.metric or RAGAS_METRICS)

    rows = load_jsonl(args.input)
    if len(rows) != 100:
        raise ValueError(f"Expected the frozen 100-query run, found {len(rows)} rows.")
    manifest = build_manifest(args.input, rows, args)
    write_json(args.output_dir / "manifest.json", manifest)

    result: dict[str, Any] = {
        "status": "complete",
        "frozen_queries": len(rows),
        "reference_type": "original_ahd_answer",
    }
    bertscore_path = args.output_dir / "bertscore.jsonl"
    if not args.skip_bertscore:
        if bertscore_path.exists():
            bertscore = load_jsonl(bertscore_path)
        else:
            bertscore = bertscore_records(
                rows,
                model_type=args.bertscore_model,
                batch_size=args.bertscore_batch_size,
            )
            for row in bertscore:
                append_jsonl(bertscore_path, row)
        result["bertscore"] = summarize_bertscore(bertscore)

    if not args.skip_ragas:
        ragas_run = asyncio.run(
            run_ragas(
                rows=rows,
                output_dir=args.output_dir,
                metric_names=args.metric,
                evaluator_provider=args.evaluator_provider,
                evaluator_base_url=args.evaluator_base_url,
                evaluator_api_key_env=args.evaluator_api_key_env,
                evaluator_model=args.evaluator_model,
                embedding_model=args.embedding_model,
                request_interval_seconds=args.request_interval_seconds,
                max_retries=args.max_retries,
                retry_delay_seconds=args.retry_delay_seconds,
                limit=args.limit,
            )
        )
        result["ragas_run"] = ragas_run
        result["ragas"] = summarize_ragas(args.output_dir / "ragas_success.jsonl")
        if ragas_run["status"] != "complete":
            result["status"] = ragas_run["status"]

    write_json(args.output_dir / "metrics.json", result)
    print(
        json.dumps(
            {
                "status": result["status"],
                "metrics": str((args.output_dir / "metrics.json").relative_to(ROOT)),
                "manifest": str((args.output_dir / "manifest.json").relative_to(ROOT)),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if result["status"] == "complete" else 2


if __name__ == "__main__":
    raise SystemExit(main())
