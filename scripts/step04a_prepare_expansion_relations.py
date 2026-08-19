"""Prepare evidence-bound relation candidates for the expansion-v2 graph.

The colleague's Step 4 relation vocabulary and stable-ID helpers remain the
source of truth.  This wrapper keeps ``aziza-trial`` immutable while fixing two
production concerns: entity-quality filtering and compact request batching.
No API calls are made here.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
from collections import defaultdict
from datetime import datetime, timezone
from itertools import product
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
COLLEAGUE_SCRIPT = ROOT / "aziza-trial" / "scripts" / "step04_prepare_relation_candidates.py"
ENTITY_DIR = ROOT / "outputs" / "graph_expansion_v2" / "03_entity_extraction"
RELATION_DIR = ROOT / "outputs" / "graph_expansion_v2" / "04_relation_extraction"

ENTITIES_CSV = ENTITY_DIR / "entities_expansion.csv"
MENTIONS_CSV = ENTITY_DIR / "entity_mentions_expansion.csv"
ENTITY_PROGRESS = ENTITY_DIR / "progress.json"
ENTITY_VALIDATED_JSONL = ENTITY_DIR / "entity_extraction_validated.jsonl"
RELATION_CANDIDATES_CSV = RELATION_DIR / "relation_candidates.csv"
RELATION_REQUESTS_JSONL = RELATION_DIR / "relation_validation_requests.jsonl"
MANIFEST_JSON = RELATION_DIR / "candidate_manifest.json"

GRAPH_VERSION = "expansion_v2"


def load_colleague_module() -> Any:
    """Load only reusable schema/normalization helpers from the frozen script."""
    spec = importlib.util.spec_from_file_location("aziza_step04_candidates", COLLEAGUE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load colleague Step 4 script: {COLLEAGUE_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def is_usable_entity(row: dict[str, str]) -> bool:
    """Keep graph-worthy entities; weak/raw terms remain available in Step 3 audit files."""
    quality = str(row.get("entity_quality", "")).strip().lower()
    actionable = str(row.get("is_actionable_medical_entity", "")).strip().lower()
    return quality != "low" and actionable not in {"false", "0", "no"}


def safe_confidence(value: Any) -> float:
    try:
        return min(1.0, max(0.0, float(value)))
    except (TypeError, ValueError):
        return 0.0


def ensure_entity_extraction_snapshot(expected_completed_chunks: int) -> dict[str, Any]:
    """Freeze either the full extraction or an explicitly bounded partial snapshot."""

    if not ENTITY_PROGRESS.exists():
        raise FileNotFoundError(ENTITY_PROGRESS)
    progress = json.loads(ENTITY_PROGRESS.read_text(encoding="utf-8"))
    completed = int(progress.get("completed_chunks", 0))
    total = int(progress.get("total_chunks", 0))
    if total <= 0:
        raise RuntimeError("Entity extraction progress has no valid total chunk count.")
    required = expected_completed_chunks if expected_completed_chunks > 0 else total
    if completed != required:
        raise RuntimeError(
            f"Entity snapshot mismatch: expected exactly {required} completed chunks, found {completed}/{total}."
        )
    if not ENTITY_VALIDATED_JSONL.exists():
        raise FileNotFoundError(ENTITY_VALIDATED_JSONL)
    validated_ids: list[str] = []
    with ENTITY_VALIDATED_JSONL.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            record = json.loads(line)
            chunk_id = str(record.get("chunk_id", "")).strip()
            if not chunk_id:
                raise ValueError("Validated entity record is missing chunk_id.")
            validated_ids.append(chunk_id)
    if len(validated_ids) != required or len(set(validated_ids)) != required:
        raise RuntimeError(
            f"Validated entity snapshot is inconsistent: rows={len(validated_ids)}, unique={len(set(validated_ids))}, expected={required}."
        )
    return {
        **progress,
        "snapshot_completed_chunks": required,
        "snapshot_is_full_source": required == total,
        "validated_chunk_ids_sha256": hashlib.sha256(
            "\n".join(sorted(validated_ids)).encode("utf-8")
        ).hexdigest(),
    }


def make_candidate_row(
    module: Any,
    *,
    chunk_id: str,
    qa_id: str,
    source_row_number: str,
    source: dict[str, Any],
    target: dict[str, Any],
    relation_type: str,
) -> dict[str, Any]:
    return {
        "relation_id": module.stable_relation_id(
            source["entity_id"], relation_type, target["entity_id"], qa_id
        ),
        "chunk_id": chunk_id,
        "qa_id": qa_id,
        "source_row_number": source_row_number,
        "candidate_relation_type": relation_type,
        "source_entity_id": source["entity_id"],
        "source_name": source["canonical_name"],
        "source_type": source["entity_type"],
        "target_entity_id": target["entity_id"],
        "target_name": target["canonical_name"],
        "target_type": target["entity_type"],
        "source_evidence": source["evidence"],
        "target_evidence": target["evidence"],
        "candidate_method": "entity_type_cooccurrence_same_qa",
        "needs_llm_validation": "true",
    }


def build_candidates(
    module: Any,
    entities: list[dict[str, str]],
    mentions: list[dict[str, str]],
    *,
    max_pairs_per_qa: int,
) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]], dict[str, int]]:
    entity_by_id = {row["entity_id"]: row for row in entities if row.get("entity_id")}
    usable_ids = {entity_id for entity_id, row in entity_by_id.items() if is_usable_entity(row)}

    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    dropped_unknown = 0
    dropped_low_quality = 0
    for mention in mentions:
        entity_id = str(mention.get("entity_id", "")).strip()
        if entity_id not in entity_by_id:
            dropped_unknown += 1
            continue
        if entity_id not in usable_ids:
            dropped_low_quality += 1
            continue
        qa_id = str(mention.get("qa_id", "")).strip()
        if not qa_id:
            continue
        grouped[(str(mention.get("chunk_id", "")).strip(), qa_id)].append(mention)

    rows: list[dict[str, Any]] = []
    contexts_by_chunk: dict[str, list[dict[str, Any]]] = defaultdict(list)
    seen_relation_ids: set[str] = set()

    for (chunk_id, qa_id), qa_mentions in sorted(grouped.items()):
        by_entity: dict[str, dict[str, Any]] = {}
        for mention in qa_mentions:
            entity_id = mention["entity_id"]
            current = by_entity.get(entity_id)
            confidence = safe_confidence(mention.get("confidence"))
            if current is None or confidence > current["confidence"]:
                by_entity[entity_id] = {
                    "entity_id": entity_id,
                    "canonical_name": mention["canonical_name"],
                    "entity_type": mention["entity_type"],
                    "confidence": confidence,
                    "evidence": str(mention.get("evidence", "")).strip(),
                }

        qa_entities = sorted(by_entity.values(), key=lambda item: item["entity_id"])
        qa_rows: list[dict[str, Any]] = []
        for source, target in product(qa_entities, qa_entities):
            if source["entity_id"] == target["entity_id"]:
                continue
            relation_type = module.relation_type_for(source["entity_type"], target["entity_type"])
            if not relation_type:
                continue
            row = make_candidate_row(
                module,
                chunk_id=chunk_id,
                qa_id=qa_id,
                source_row_number=str(qa_mentions[0].get("source_row_number", "")),
                source=source,
                target=target,
                relation_type=relation_type,
            )
            if row["relation_id"] in seen_relation_ids:
                continue
            seen_relation_ids.add(row["relation_id"])
            qa_rows.append(row)
            if len(qa_rows) >= max_pairs_per_qa:
                break

        if not qa_rows:
            continue
        rows.extend(qa_rows)
        contexts_by_chunk[chunk_id].append(
            {
                "qa_id": qa_id,
                "source_row_number": str(qa_mentions[0].get("source_row_number", "")),
                "entities": [
                    {
                        "entity_id": item["entity_id"],
                        "canonical_name": item["canonical_name"],
                        "entity_type": item["entity_type"],
                        "evidence": item["evidence"],
                    }
                    for item in qa_entities
                ],
                "candidate_pairs": [
                    {
                        "relation_id": row["relation_id"],
                        "candidate_relation_type": row["candidate_relation_type"],
                        "source_entity_id": row["source_entity_id"],
                        "source_name": row["source_name"],
                        "target_entity_id": row["target_entity_id"],
                        "target_name": row["target_name"],
                    }
                    for row in qa_rows
                ],
            }
        )

    stats = {
        "usable_entities": len(usable_ids),
        "dropped_low_quality_mentions": dropped_low_quality,
        "dropped_unknown_entity_mentions": dropped_unknown,
    }
    return rows, contexts_by_chunk, stats


def build_requests(
    contexts_by_chunk: dict[str, list[dict[str, Any]]],
    *,
    max_pairs_per_request: int,
    max_evidence_chars_per_request: int,
) -> list[dict[str, Any]]:
    packed_contexts: list[list[dict[str, Any]]] = []
    current: list[dict[str, Any]] = []
    current_pairs = 0
    current_evidence_chars = 0
    flattened: list[dict[str, Any]] = []
    for chunk_id, contexts in sorted(contexts_by_chunk.items()):
        for context in contexts:
            pairs = list(context.get("candidate_pairs", []))
            for start in range(0, len(pairs), max_pairs_per_request):
                flattened.append(
                    {
                        **context,
                        "chunk_id": chunk_id,
                        "candidate_pairs": pairs[start : start + max_pairs_per_request],
                    }
                )

    for context in flattened:
        context_pairs = len(context["candidate_pairs"])
        context_evidence_chars = sum(
            len(str(entity.get("evidence", "")))
            for entity in context.get("entities", [])
        )
        would_overflow = current and (
            current_pairs + context_pairs > max_pairs_per_request
            or current_evidence_chars + context_evidence_chars
            > max_evidence_chars_per_request
        )
        if would_overflow:
            packed_contexts.append(current)
            current = []
            current_pairs = 0
            current_evidence_chars = 0
        current.append(context)
        current_pairs += context_pairs
        current_evidence_chars += context_evidence_chars
    if current:
        packed_contexts.append(current)

    requests: list[dict[str, Any]] = []
    allowed = ["DIAGNOSED_BY", "HAS_SYMPTOM", "INVESTIGATED_BY", "TREATED_BY"]
    for batch_index, packed in enumerate(packed_contexts, start=1):
        request_id = f"relation_request_batch_{batch_index:06d}"
        requests.append(
            {
                "request_id": request_id,
                "chunk_id": f"relation_batch_{batch_index:06d}",
                "source_chunk_ids": sorted({context["chunk_id"] for context in packed}),
                "task": "Strictly validate Arabic medical relation candidates using only their QA evidence.",
                "allowed_relation_types": allowed,
                "qa_contexts": packed,
            }
        )
    return requests


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0]) if rows else []
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        if not fieldnames:
            return
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build", action="store_true", help="Write the frozen Step 4A artifacts.")
    parser.add_argument("--max-pairs-per-qa", type=int, default=25)
    parser.add_argument("--max-pairs-per-request", type=int, default=20)
    parser.add_argument("--max-evidence-chars-per-request", type=int, default=8000)
    parser.add_argument(
        "--expected-completed-chunks",
        type=int,
        default=0,
        help="Require this exact partial snapshot size; zero requires all source chunks.",
    )
    parser.add_argument("--force-overwrite", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.build:
        raise RuntimeError("No files are written without the explicit --build flag.")
    if args.expected_completed_chunks < 0:
        raise ValueError("--expected-completed-chunks must be non-negative.")
    entity_snapshot = ensure_entity_extraction_snapshot(args.expected_completed_chunks)
    protected = [RELATION_CANDIDATES_CSV, RELATION_REQUESTS_JSONL, MANIFEST_JSON]
    if not args.force_overwrite and any(path.exists() for path in protected):
        raise FileExistsError("Step 4A artifacts already exist; use --force-overwrite intentionally.")

    module = load_colleague_module()
    entities = read_csv(ENTITIES_CSV)
    mentions = read_csv(MENTIONS_CSV)
    candidates, contexts, quality_stats = build_candidates(
        module,
        entities,
        mentions,
        max_pairs_per_qa=args.max_pairs_per_qa,
    )
    requests = build_requests(
        contexts,
        max_pairs_per_request=args.max_pairs_per_request,
        max_evidence_chars_per_request=args.max_evidence_chars_per_request,
    )

    write_csv(RELATION_CANDIDATES_CSV, candidates)
    write_jsonl(RELATION_REQUESTS_JSONL, requests)
    manifest = {
        "graph_version": GRAPH_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_script": COLLEAGUE_SCRIPT.relative_to(ROOT).as_posix(),
        "entities_source": ENTITIES_CSV.relative_to(ROOT).as_posix(),
        "mentions_source": MENTIONS_CSV.relative_to(ROOT).as_posix(),
        "entities_sha256": file_sha256(ENTITIES_CSV),
        "mentions_sha256": file_sha256(MENTIONS_CSV),
        "entity_rows": len(entities),
        "mention_rows": len(mentions),
        "entity_source_total_chunks": entity_snapshot["total_chunks"],
        "entity_snapshot_completed_chunks": entity_snapshot["snapshot_completed_chunks"],
        "entity_snapshot_is_full_source": entity_snapshot["snapshot_is_full_source"],
        "validated_chunk_ids_sha256": entity_snapshot["validated_chunk_ids_sha256"],
        "entity_validated_jsonl_sha256": file_sha256(ENTITY_VALIDATED_JSONL),
        "candidate_rows": len(candidates),
        "request_rows": len(requests),
        "qa_contexts_with_candidates": sum(len(value) for value in contexts.values()),
        "max_pairs_per_qa": args.max_pairs_per_qa,
        "max_pairs_per_request": args.max_pairs_per_request,
        "max_evidence_chars_per_request": args.max_evidence_chars_per_request,
        **quality_stats,
    }
    MANIFEST_JSON.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
