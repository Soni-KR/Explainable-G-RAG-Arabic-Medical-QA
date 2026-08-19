"""Submit and merge GPT-OSS entity extraction through the Groq Batch API.

The batch path uses the same prompts, strict schema, chunk partitioning, and
local validator as the synchronous expansion runner.  It never stores API keys.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

import step03_expand_graph_entities as expansion


ROOT = Path(__file__).resolve().parents[1]
BATCH_ROOT = (
    ROOT
    / "outputs"
    / "graph_expansion_v2"
    / "03_entity_extraction"
    / "batch_jobs"
)
API_ROOT = "https://api.groq.com/openai/v1"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL at {path}:{line_number}: {exc}") from exc
    return records


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def api_key() -> str:
    keys = expansion.load_api_keys()
    if not keys:
        raise RuntimeError("No Groq API key was loaded.")
    return keys[0]


def auth_headers(key: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {key}"}


def raise_for_api(response: requests.Response) -> dict[str, Any]:
    if response.status_code >= 400:
        body = response.text[:3000]
        raise RuntimeError(f"Groq Batch API HTTP {response.status_code}: {body}")
    payload = response.json()
    if not isinstance(payload, dict):
        raise RuntimeError("Groq Batch API returned a non-object response.")
    return payload


def prepare_job(
    *,
    job_id: str,
    model: str,
    only_chunk_ids: set[str],
    force_reprocess: bool,
    batch_start: int,
    limit_chunks: int,
) -> Path:
    module = expansion.load_colleague_module()
    chunks = module.load_chunks()
    completed, _ = expansion.current_completion(module)
    selected = list(chunks) if force_reprocess else [
        chunk for chunk in chunks if str(chunk["chunk_id"]) not in completed
    ]
    if only_chunk_ids:
        selected = [
            chunk for chunk in selected if str(chunk["chunk_id"]) in only_chunk_ids
        ]
    selected = selected[batch_start:]
    if limit_chunks > 0:
        selected = selected[:limit_chunks]
    if not selected:
        raise RuntimeError("No chunks were selected for this batch job.")

    job_dir = BATCH_ROOT / job_id
    if job_dir.exists() and any(job_dir.iterdir()):
        raise FileExistsError(f"Batch job directory already exists: {job_dir}")
    job_dir.mkdir(parents=True, exist_ok=True)
    input_path = job_dir / "input.jsonl"
    request_map: dict[str, dict[str, Any]] = {}
    request_count = 0
    with input_path.open("w", encoding="utf-8", newline="\n") as handle:
        for chunk in selected:
            chunk_id = str(chunk["chunk_id"])
            parts = expansion.split_chunk_for_provider(module, chunk)
            for part_index, part in enumerate(parts, start=1):
                request_record = module.make_request_record(part, "groq", model)
                request_record["max_completion_tokens"] = 4000 if len(parts) > 1 else 5000
                body = expansion.request_body(request_record)
                custom_id = f"entity__{chunk_id}__p{part_index:03d}"
                line = {
                    "custom_id": custom_id,
                    "method": "POST",
                    "url": "/v1/chat/completions",
                    "body": body,
                }
                handle.write(json.dumps(line, ensure_ascii=False) + "\n")
                request_map[custom_id] = {
                    "chunk_id": chunk_id,
                    "part_index": part_index,
                    "part_count": len(parts),
                }
                request_count += 1

    write_json(job_dir / "request_map.json", request_map)
    state = {
        "job_id": job_id,
        "status": "prepared",
        "model": model,
        "graph_version": "expansion_v2",
        "selected_chunks": len(selected),
        "request_count": request_count,
        "batch_start": batch_start,
        "limit_chunks": limit_chunks,
        "force_reprocess": force_reprocess,
        "only_chunk_ids": sorted(only_chunk_ids),
        "input_sha256": sha256(input_path),
        "prepared_at_utc": datetime.now(timezone.utc).isoformat(),
        "secrets_persisted": False,
    }
    write_json(job_dir / "state.json", state)
    print(json.dumps(state, ensure_ascii=False, indent=2))
    return job_dir


def load_state(job_dir: Path) -> dict[str, Any]:
    path = job_dir / "state.json"
    if not path.exists():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def submit_job(job_dir: Path, completion_window: str) -> dict[str, Any]:
    state = load_state(job_dir)
    if state.get("status") != "prepared":
        raise RuntimeError(f"Job is not prepared: {state.get('status')}")
    input_path = job_dir / "input.jsonl"
    if sha256(input_path) != state["input_sha256"]:
        raise RuntimeError("Batch input hash changed after preparation.")
    key = api_key()
    with input_path.open("rb") as handle:
        upload = requests.post(
            f"{API_ROOT}/files",
            headers=auth_headers(key),
            data={"purpose": "batch"},
            files={"file": (input_path.name, handle, "application/jsonl")},
            timeout=180,
        )
    file_payload = raise_for_api(upload)
    create = requests.post(
        f"{API_ROOT}/batches",
        headers={**auth_headers(key), "Content-Type": "application/json"},
        json={
            "input_file_id": file_payload["id"],
            "endpoint": "/v1/chat/completions",
            "completion_window": completion_window,
        },
        timeout=120,
    )
    batch_payload = raise_for_api(create)
    state.update(
        {
            "status": str(batch_payload.get("status", "submitted")),
            "input_file_id": file_payload["id"],
            "batch_id": batch_payload["id"],
            "key_fingerprint": expansion.key_fingerprint(key),
            "completion_window": completion_window,
            "submitted_at_utc": datetime.now(timezone.utc).isoformat(),
        }
    )
    write_json(job_dir / "state.json", state)
    print(
        json.dumps(
            {
                "job_id": state["job_id"],
                "batch_id": state["batch_id"],
                "status": state["status"],
                "request_count": state["request_count"],
                "key_fingerprint": state["key_fingerprint"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return state


def retrieve_batch(key: str, batch_id: str) -> dict[str, Any]:
    response = requests.get(
        f"{API_ROOT}/batches/{batch_id}",
        headers=auth_headers(key),
        timeout=120,
    )
    return raise_for_api(response)


def download_file(key: str, file_id: str, path: Path) -> None:
    response = requests.get(
        f"{API_ROOT}/files/{file_id}/content",
        headers=auth_headers(key),
        timeout=300,
    )
    if response.status_code >= 400:
        raise RuntimeError(
            f"Groq file download HTTP {response.status_code}: {response.text[:2000]}"
        )
    path.write_bytes(response.content)


def poll_job(job_dir: Path, *, wait: bool, poll_seconds: float) -> dict[str, Any]:
    state = load_state(job_dir)
    if not state.get("batch_id"):
        raise RuntimeError("The batch has not been submitted.")
    key = api_key()
    terminal = {"completed", "failed", "expired", "cancelled"}
    while True:
        payload = retrieve_batch(key, state["batch_id"])
        status = str(payload.get("status", ""))
        counts = payload.get("request_counts") or {}
        state.update(
            {
                "status": status,
                "request_counts": counts,
                "output_file_id": payload.get("output_file_id"),
                "error_file_id": payload.get("error_file_id"),
                "last_polled_at_utc": datetime.now(timezone.utc).isoformat(),
            }
        )
        write_json(job_dir / "state.json", state)
        print(
            json.dumps(
                {
                    "job_id": state["job_id"],
                    "status": status,
                    "request_counts": counts,
                },
                ensure_ascii=False,
            ),
            flush=True,
        )
        if status in terminal or not wait:
            break
        time.sleep(poll_seconds)

    if status == "completed":
        if state.get("output_file_id"):
            download_file(key, state["output_file_id"], job_dir / "output.jsonl")
        if state.get("error_file_id"):
            download_file(key, state["error_file_id"], job_dir / "errors.jsonl")
    return state


def merge_job(job_dir: Path) -> dict[str, Any]:
    state = load_state(job_dir)
    if state.get("status") != "completed":
        raise RuntimeError(f"Batch is not complete: {state.get('status')}")
    request_map = json.loads((job_dir / "request_map.json").read_text(encoding="utf-8"))
    output_records = read_jsonl(job_dir / "output.jsonl")
    outputs_by_id = {str(row.get("custom_id", "")): row for row in output_records}
    module = expansion.load_colleague_module()

    parts_by_chunk: dict[str, list[dict[str, Any]]] = {}
    errors: list[dict[str, Any]] = []
    for custom_id, mapping in request_map.items():
        output = outputs_by_id.get(custom_id)
        if not output:
            errors.append({"custom_id": custom_id, "error": "missing_batch_output"})
            continue
        response = output.get("response") or {}
        if int(response.get("status_code", 0)) != 200:
            errors.append(
                {
                    "custom_id": custom_id,
                    "error": f"batch_http_{response.get('status_code')}",
                }
            )
            continue
        body = response.get("body") or {}
        try:
            text = str(body["choices"][0]["message"]["content"] or "").strip()
            parsed = module.extract_json_object(text)
            entities = parsed.get("entities", [])
            if not isinstance(entities, list):
                raise ValueError("entities is not a list")
        except (KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError) as exc:
            errors.append({"custom_id": custom_id, "error": str(exc)[:1000]})
            continue
        parts_by_chunk.setdefault(mapping["chunk_id"], []).append(
            {
                "part_index": int(mapping["part_index"]),
                "part_count": int(mapping["part_count"]),
                "entities": entities,
                "usage": body.get("usage") or {},
                "model": clean_model(body.get("model") or state.get("model")),
            }
        )

    merged_chunks = 0
    for chunk_id, parts in sorted(parts_by_chunk.items()):
        expected = parts[0]["part_count"]
        if len(parts) != expected or {part["part_index"] for part in parts} != set(
            range(1, expected + 1)
        ):
            errors.append({"chunk_id": chunk_id, "error": "incomplete_chunk_parts"})
            continue
        entities: list[dict[str, Any]] = []
        usage: dict[str, int] = {}
        models: list[str] = []
        for part in sorted(parts, key=lambda item: item["part_index"]):
            models.append(part["model"])
            expansion.add_usage(usage, part["usage"])
            for entity in part["entities"]:
                if isinstance(entity, dict):
                    item = dict(entity)
                    item["local_entity_id"] = (
                        f"P{part['part_index']}_{item.get('local_entity_id', '')}"
                    )
                    entities.append(item)
        expansion.append_jsonl(
            expansion.RAW_RESPONSES,
            {
                "request_id": f"entity_request_{chunk_id}",
                "chunk_id": chunk_id,
                "provider": "groq_batch",
                "model": "|".join(dict.fromkeys(models)),
                "key_fingerprint": state.get("key_fingerprint", ""),
                "status": "ok",
                "error": "",
                "http_status": 200,
                "usage": usage,
                "request_parts": expected,
                "batch_id": state["batch_id"],
                "batch_job_id": state["job_id"],
                "response_text": json.dumps(
                    {"chunk_id": chunk_id, "entities": entities}, ensure_ascii=False
                ),
            },
        )
        merged_chunks += 1

    error_path = job_dir / "merge_errors.json"
    write_json(error_path, errors)
    chunks = module.load_chunks()
    export_summary = expansion.validate_and_export(module, chunks)
    completed, errored = expansion.current_completion(module)
    expansion.write_progress(
        total_chunks=len(chunks),
        completed=len(completed),
        errored=len(errored),
        new_successes=merged_chunks,
        http_attempts=0,
        last_chunk=max(parts_by_chunk) if parts_by_chunk else "",
        stopped_reason="" if not errors else "batch_merge_has_errors",
    )
    state.update(
        {
            "status": "merged" if not errors else "merged_with_errors",
            "merged_chunks": merged_chunks,
            "merge_errors": len(errors),
            "merged_at_utc": datetime.now(timezone.utc).isoformat(),
            "completed_chunks_after_merge": len(completed),
            "remaining_chunks_after_merge": len(chunks) - len(completed),
            "exports": export_summary,
        }
    )
    write_json(job_dir / "state.json", state)
    print(json.dumps(state, ensure_ascii=False, indent=2))
    return state


def clean_model(value: Any) -> str:
    return str(value or "").strip()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--prepare", action="store_true")
    mode.add_argument("--submit", action="store_true")
    mode.add_argument("--poll", action="store_true")
    mode.add_argument("--merge", action="store_true")
    parser.add_argument("--job-id", required=True)
    parser.add_argument("--model", default="openai/gpt-oss-20b")
    parser.add_argument("--only-chunk-ids", default="")
    parser.add_argument("--force-reprocess", action="store_true")
    parser.add_argument("--batch-start", type=int, default=0)
    parser.add_argument("--limit-chunks", type=int, default=0)
    parser.add_argument("--completion-window", default="24h")
    parser.add_argument("--wait", action="store_true")
    parser.add_argument("--poll-seconds", type=float, default=30.0)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if args.batch_start < 0 or args.limit_chunks < 0 or args.poll_seconds <= 0:
        raise ValueError("Batch offsets must be non-negative and polling must be positive.")
    only_chunk_ids = {
        value.strip() for value in args.only_chunk_ids.split(",") if value.strip()
    }
    if args.force_reprocess and not only_chunk_ids:
        raise ValueError("--force-reprocess requires --only-chunk-ids.")
    job_dir = BATCH_ROOT / args.job_id
    if args.prepare:
        prepare_job(
            job_id=args.job_id,
            model=args.model,
            only_chunk_ids=only_chunk_ids,
            force_reprocess=args.force_reprocess,
            batch_start=args.batch_start,
            limit_chunks=args.limit_chunks,
        )
    elif args.submit:
        submit_job(job_dir, args.completion_window)
    elif args.poll:
        poll_job(job_dir, wait=args.wait, poll_seconds=args.poll_seconds)
    else:
        merge_job(job_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
