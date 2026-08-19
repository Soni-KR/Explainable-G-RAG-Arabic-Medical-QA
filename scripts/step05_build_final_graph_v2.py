"""Merge frozen final_v1 with the validated expansion into final_v2.

This is a versioned build: final_v1 and all expansion audit caches remain
untouched. The command accepts either a complete entity run or an explicitly
bounded entity snapshot, and refuses to build until every relation candidate
from that exact snapshot has a validated decision.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import step03_expand_graph_entities as step03


ROOT = Path(__file__).resolve().parents[1]
FINAL_V1 = ROOT / "outputs" / "final_graph"
EXPANSION = ROOT / "outputs" / "graph_expansion_v2"
ENTITY_EXPANSION = EXPANSION / "03_entity_extraction"
RELATION_EXPANSION = EXPANSION / "04_relation_extraction"
FINAL_V2 = ROOT / "outputs" / "final_graph_v2"

RAW_AHD = ROOT / "data" / "raw" / "AHD.csv"
OLD_QA_SOURCE = FINAL_V1 / "provenance" / "qa_records_source_5000.csv"
EXPANSION_QA_SOURCE = (
    ROOT
    / "aziza-trial"
    / "outputs"
    / "01_preprocessing"
    / "ahd_subset_10000_preprocessed_expansion_v1.csv"
)

GRAPH_VERSION = "final_v2"
INVERSE_RELATION_TYPES = {
    "HAS_SYMPTOM": "SYMPTOM_OF",
    "TREATED_BY": "TREATS",
    "DIAGNOSED_BY": "DIAGNOSES",
    "INVESTIGATED_BY": "INVESTIGATES",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def clean(value: Any) -> str:
    return str(value or "").strip()


def safe_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def safe_int(value: Any) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def parse_aliases(value: Any) -> list[str]:
    text = clean(value)
    if not text:
        return []
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        parsed = [part.strip() for part in text.split("|")]
    if not isinstance(parsed, list):
        parsed = [parsed]
    return sorted({clean(item) for item in parsed if clean(item)})


def normalize_entity_name(value: Any) -> str:
    module = normalize_entity_name.module
    if module is None:
        module = step03.load_colleague_module()
        normalize_entity_name.module = module
    return module.normalize_arabic(value)


normalize_entity_name.module = None  # type: ignore[attr-defined]


def usable_expansion_entity(row: dict[str, str]) -> bool:
    quality = clean(row.get("entity_quality")).lower()
    actionable = clean(row.get("is_actionable_medical_entity")).lower()
    return quality != "low" and actionable not in {"false", "0", "no"}


def require_complete_progress(path: Path, total_field: str, completed_field: str) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    total = int(payload.get(total_field, 0))
    completed = int(payload.get(completed_field, 0))
    if total <= 0 or completed != total:
        raise RuntimeError(f"Incomplete stage at {path}: {completed}/{total}")
    return payload


def require_entity_snapshot(path: Path, expected_completed: int) -> dict[str, Any]:
    """Validate a full run or an explicitly requested immutable partial snapshot."""

    if not path.exists():
        raise FileNotFoundError(path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    total = int(payload.get("total_chunks", 0))
    completed = int(payload.get("completed_chunks", 0))
    if total <= 0 or completed <= 0 or completed > total:
        raise RuntimeError(f"Invalid entity progress at {path}: {completed}/{total}")
    if expected_completed > 0:
        if completed != expected_completed:
            raise RuntimeError(
                f"Entity snapshot mismatch at {path}: expected "
                f"{expected_completed}, found {completed}"
            )
    elif completed != total:
        raise RuntimeError(
            "Entity extraction is partial; pass --expected-entity-chunks with "
            "the exact frozen snapshot size."
        )
    return payload


def validate_snapshot_manifest(
    entity_progress: dict[str, Any],
    candidate_manifest: dict[str, Any],
) -> None:
    """Bind Step 5 to the entity files used to generate Step 4 candidates."""

    completed = int(entity_progress["completed_chunks"])
    manifest_completed = int(candidate_manifest.get("entity_snapshot_completed_chunks", -1))
    if manifest_completed != completed:
        raise RuntimeError(
            "Relation candidates were not built from the requested entity snapshot: "
            f"manifest={manifest_completed}, entity_progress={completed}"
        )
    expected_hashes = {
        ENTITY_EXPANSION / "entities_expansion.csv": candidate_manifest.get("entities_sha256"),
        ENTITY_EXPANSION / "entity_mentions_expansion.csv": candidate_manifest.get("mentions_sha256"),
        ENTITY_EXPANSION / "entity_extraction_validated.jsonl": candidate_manifest.get(
            "entity_validated_jsonl_sha256"
        ),
    }
    for path, expected_hash in expected_hashes.items():
        if not expected_hash or file_sha256(path) != expected_hash:
            raise RuntimeError(f"Frozen entity snapshot hash mismatch: {path}")


def merge_entities(
    old_entities: list[dict[str, str]],
    expansion_entities: list[dict[str, str]],
) -> tuple[list[dict[str, Any]], dict[str, str], dict[str, int]]:
    merged: dict[tuple[str, str], dict[str, Any]] = {}
    id_to_key: dict[str, tuple[str, str]] = {}

    for row in old_entities:
        norm = clean(row.get("canonical_name_norm")) or normalize_entity_name(row.get("canonical_name"))
        key = (clean(row.get("entity_type")), norm)
        entity_id = clean(row.get("entity_id"))
        if not entity_id or key in merged or entity_id in id_to_key:
            raise ValueError(f"Invalid or duplicate final_v1 entity: {entity_id} {key}")
        merged[key] = {
            "entity_id": entity_id,
            "canonical_name": clean(row.get("canonical_name")),
            "canonical_name_norm": norm,
            "entity_type": key[0],
            "aliases_set": set(parse_aliases(row.get("aliases"))),
            "confidence_values": [(safe_float(row.get("confidence")), max(1, safe_int(row.get("mention_count"))))],
            "providers": {clean(row.get("provider"))} - {""},
            "models": {clean(row.get("model"))} - {""},
            "source_graph_versions": {"final_v1"},
        }
        id_to_key[entity_id] = key

    expansion_id_map: dict[str, str] = {}
    added = 0
    merged_into_existing = 0
    filtered = 0
    for row in expansion_entities:
        source_id = clean(row.get("entity_id"))
        if not usable_expansion_entity(row):
            filtered += 1
            continue
        norm = clean(row.get("canonical_name_norm")) or normalize_entity_name(row.get("canonical_name"))
        key = (clean(row.get("entity_type")), norm)
        existing = merged.get(key)
        if existing is None:
            entity_id = source_id
            if entity_id in id_to_key and id_to_key[entity_id] != key:
                digest = hashlib.sha1(f"{key[0]}::{key[1]}".encode("utf-8")).hexdigest()[:16]
                entity_id = f"ent_v2_{digest}"
            existing = {
                "entity_id": entity_id,
                "canonical_name": clean(row.get("canonical_name")),
                "canonical_name_norm": norm,
                "entity_type": key[0],
                "aliases_set": set(),
                "confidence_values": [],
                "providers": set(),
                "models": set(),
                "source_graph_versions": set(),
            }
            merged[key] = existing
            id_to_key[entity_id] = key
            added += 1
        else:
            merged_into_existing += 1
        expansion_id_map[source_id] = existing["entity_id"]
        existing["aliases_set"].update(parse_aliases(row.get("aliases")))
        existing["aliases_set"].add(clean(row.get("canonical_name")))
        existing["confidence_values"].append(
            (safe_float(row.get("avg_confidence")), max(1, safe_int(row.get("mention_count"))))
        )
        existing["providers"].add("groq")
        existing["models"].update(
            part.strip() for part in clean(row.get("source_models")).replace(";", "|").split("|") if part.strip()
        )
        existing["source_graph_versions"].add("expansion_v2")

    rows: list[dict[str, Any]] = []
    for value in merged.values():
        weighted_total = sum(score * weight for score, weight in value["confidence_values"])
        weight = sum(item_weight for _, item_weight in value["confidence_values"])
        aliases = sorted(
            alias
            for alias in value["aliases_set"]
            if alias and normalize_entity_name(alias) != value["canonical_name_norm"]
        )
        rows.append(
            {
                "entity_id": value["entity_id"],
                "canonical_name": value["canonical_name"],
                "canonical_name_norm": value["canonical_name_norm"],
                "entity_type": value["entity_type"],
                "aliases": json.dumps(aliases, ensure_ascii=False),
                "confidence": f"{(weighted_total / weight if weight else 0.0):.6f}",
                "mention_count": 0,
                "provider": "|".join(sorted(value["providers"])),
                "model": "|".join(sorted(value["models"])),
                "source_graph_versions": "|".join(sorted(value["source_graph_versions"])),
                "graph_version": GRAPH_VERSION,
            }
        )
    rows.sort(key=lambda row: row["entity_id"])
    return rows, expansion_id_map, {
        "expansion_entities_added": added,
        "expansion_entities_merged": merged_into_existing,
        "expansion_entities_filtered": filtered,
    }


def merge_mentions(
    entities: list[dict[str, Any]],
    old_mentions: list[dict[str, str]],
    expansion_mentions: list[dict[str, str]],
    expansion_id_map: dict[str, str],
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    entity_by_id = {row["entity_id"]: row for row in entities}
    rows: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    def append(row: dict[str, str], source_version: str, mapped_entity_id: str) -> None:
        mention_id = clean(row.get("mention_id"))
        if not mention_id or mention_id in seen_ids:
            raise ValueError(f"Duplicate or missing mention_id: {mention_id}")
        entity = entity_by_id.get(mapped_entity_id)
        if not entity:
            raise ValueError(f"Mention endpoint does not exist: {mapped_entity_id}")
        seen_ids.add(mention_id)
        rows.append(
            {
                "mention_id": mention_id,
                "entity_id": mapped_entity_id,
                "canonical_name": entity["canonical_name"],
                "entity_type": entity["entity_type"],
                "chunk_id": clean(row.get("chunk_id")),
                "qa_id": clean(row.get("qa_id")),
                "source_row_number": clean(row.get("source_row_number")),
                "surface_form": clean(row.get("surface_form")),
                "field": clean(row.get("field")),
                "evidence": clean(row.get("evidence")),
                "extraction_method": clean(row.get("extraction_method")) or "llm",
                "provider": clean(row.get("provider")),
                "model": clean(row.get("model")),
                "confidence": clean(row.get("confidence")),
                "llm_confidence": clean(row.get("llm_confidence")) or clean(row.get("confidence")),
                "prompt_version": clean(row.get("prompt_version")) or "expansion_v2_entity_prompt",
                "source_graph_version": source_version,
                "graph_version": GRAPH_VERSION,
            }
        )

    for row in old_mentions:
        append(row, "final_v1", clean(row.get("entity_id")))
    kept_expansion = 0
    filtered_expansion = 0
    for row in expansion_mentions:
        mapped = expansion_id_map.get(clean(row.get("entity_id")))
        if not mapped:
            filtered_expansion += 1
            continue
        append(row, "expansion_v2", mapped)
        kept_expansion += 1

    mention_counts = Counter(row["entity_id"] for row in rows)
    for entity in entities:
        entity["mention_count"] = mention_counts.get(entity["entity_id"], 0)
    rows.sort(key=lambda row: row["mention_id"])
    return rows, {
        "expansion_mentions_added": kept_expansion,
        "expansion_mentions_filtered": filtered_expansion,
    }


def stable_v2_relation_id(source_id: str, relation_type: str, target_id: str, qa_id: str) -> str:
    key = f"{source_id}|{relation_type}|{target_id}|{qa_id}"
    return "rel_v2_" + hashlib.sha1(key.encode("utf-8")).hexdigest()[:16]


def merge_relation_decisions(
    old_decisions: list[dict[str, str]],
    expansion_decisions: list[dict[str, str]],
    expansion_id_map: dict[str, str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, int]]:
    decisions: list[dict[str, Any]] = []
    relation_ids: set[str] = set()
    kept_keys: set[tuple[str, str, str, str]] = set()
    filtered_endpoints = 0

    def normalized_row(
        row: dict[str, str],
        *,
        source_version: str,
        relation_id: str,
        source_id: str,
        target_id: str,
    ) -> dict[str, Any]:
        return {
            "relation_id": relation_id,
            "source_relation_id": clean(row.get("source_relation_id")) or clean(row.get("relation_id")),
            "chunk_id": clean(row.get("chunk_id")),
            "qa_id": clean(row.get("qa_id")),
            "source_row_number": clean(row.get("source_row_number")),
            "source_entity_id": source_id,
            "source_name": clean(row.get("source_name")),
            "source_type": clean(row.get("source_type")),
            "target_entity_id": target_id,
            "target_name": clean(row.get("target_name")),
            "target_type": clean(row.get("target_type")),
            "candidate_relation_type": clean(row.get("candidate_relation_type")),
            "validated_relation_type": clean(row.get("validated_relation_type")),
            "keep": clean(row.get("keep")).lower(),
            "confidence": clean(row.get("confidence")),
            "evidence": clean(row.get("evidence")),
            "reason": clean(row.get("reason")),
            "provider": clean(row.get("provider")),
            "model": clean(row.get("model")),
            "prompt_version": clean(row.get("prompt_version")) or (
                "expansion_v2_relation_prompt" if source_version == "expansion_v2" else ""
            ),
            "source_graph_version": source_version,
            "graph_version": GRAPH_VERSION,
        }

    for row in old_decisions:
        relation_id = clean(row.get("relation_id"))
        if not relation_id or relation_id in relation_ids:
            raise ValueError(f"Duplicate final_v1 relation decision ID: {relation_id}")
        relation_ids.add(relation_id)
        decisions.append(
            normalized_row(
                row,
                source_version="final_v1",
                relation_id=relation_id,
                source_id=clean(row.get("source_entity_id")),
                target_id=clean(row.get("target_entity_id")),
            )
        )

    for row in expansion_decisions:
        source_id = expansion_id_map.get(clean(row.get("source_entity_id")))
        target_id = expansion_id_map.get(clean(row.get("target_entity_id")))
        if not source_id or not target_id:
            filtered_endpoints += 1
            continue
        relation_type = clean(row.get("validated_relation_type"))
        relation_id = stable_v2_relation_id(source_id, relation_type, target_id, clean(row.get("qa_id")))
        if relation_id in relation_ids:
            raise ValueError(f"Expansion relation ID collision: {relation_id}")
        relation_ids.add(relation_id)
        decisions.append(
            normalized_row(
                row,
                source_version="expansion_v2",
                relation_id=relation_id,
                source_id=source_id,
                target_id=target_id,
            )
        )

    direct: list[dict[str, Any]] = []
    for row in decisions:
        if row["keep"] != "true":
            continue
        key = (
            row["source_entity_id"],
            row["validated_relation_type"],
            row["target_entity_id"],
            row["qa_id"],
        )
        if key in kept_keys:
            continue
        kept_keys.add(key)
        direct.append(row)

    bidirectional: list[dict[str, Any]] = []
    for row in direct:
        relation_type = row["validated_relation_type"]
        inverse_type = INVERSE_RELATION_TYPES.get(relation_type)
        if not inverse_type:
            raise ValueError(f"No inverse mapping for {relation_type}")
        direct_edge = dict(row)
        direct_edge.update(
            {
                "edge_id": row["relation_id"],
                "graph_relation_type": relation_type,
                "direction": "direct",
            }
        )
        inverse_edge = dict(row)
        inverse_edge.update(
            {
                "edge_id": row["relation_id"] + "__inverse",
                "graph_relation_type": inverse_type,
                "direction": "inverse",
                "source_entity_id": row["target_entity_id"],
                "source_name": row["target_name"],
                "source_type": row["target_type"],
                "target_entity_id": row["source_entity_id"],
                "target_name": row["source_name"],
                "target_type": row["source_type"],
            }
        )
        bidirectional.extend([direct_edge, inverse_edge])

    decisions.sort(key=lambda row: row["relation_id"])
    direct.sort(key=lambda row: row["relation_id"])
    bidirectional.sort(key=lambda row: row["edge_id"])
    return decisions, direct, bidirectional, {
        "expansion_relation_decisions_filtered_endpoints": filtered_endpoints,
        "duplicate_kept_relation_keys_removed": sum(row["keep"] == "true" for row in decisions) - len(direct),
    }


def build_qa_records(
    mentions: list[dict[str, Any]],
    relations: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    reference_source_rows: dict[str, set[str]] = defaultdict(set)
    source_versions: dict[str, set[str]] = defaultdict(set)
    for row in [*mentions, *relations]:
        qa_id = clean(row.get("qa_id"))
        if not qa_id:
            continue
        if clean(row.get("source_row_number")):
            reference_source_rows[qa_id].add(clean(row.get("source_row_number")))
        source_versions[qa_id].add(clean(row.get("source_graph_version")))

    known: dict[str, dict[str, str]] = {}
    for source_path in (OLD_QA_SOURCE, EXPANSION_QA_SOURCE):
        for row in read_csv(source_path):
            qa_id = clean(row.get("subset_id"))
            if qa_id:
                known[qa_id] = row

    referenced_qa_ids = set(source_versions)
    missing_ids = sorted(referenced_qa_ids - set(known))
    ambiguous_missing = {
        qa_id: reference_source_rows[qa_id]
        for qa_id in missing_ids
        if len(reference_source_rows[qa_id]) != 1
    }
    if ambiguous_missing:
        first = next(iter(ambiguous_missing.items()))
        raise ValueError(f"Unresolved QA ID maps to ambiguous source rows: {first}")
    wanted_rows = {
        safe_int(next(iter(reference_source_rows[qa_id])))
        for qa_id in missing_ids
        if reference_source_rows[qa_id]
    }
    raw_by_row: dict[int, dict[str, str]] = {}
    if wanted_rows:
        with RAW_AHD.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            for source_row_number, row in enumerate(reader, start=2):
                if source_row_number in wanted_rows:
                    raw_by_row[source_row_number] = row
                    if len(raw_by_row) == len(wanted_rows):
                        break

    rows: list[dict[str, Any]] = []
    authoritative_mismatches = 0
    for qa_id in sorted(referenced_qa_ids):
        source = known.get(qa_id)
        if source:
            source_row = safe_int(source.get("source_row_number"))
            question = clean(source.get("question"))
            answer = clean(source.get("answer"))
            category = clean(source.get("category"))
            quality = "preprocessed_source"
            observed = {safe_int(value) for value in reference_source_rows[qa_id]}
            authoritative_mismatches += sum(
                value > 0 and value != source_row for value in observed
            )
        else:
            source_row = safe_int(next(iter(reference_source_rows[qa_id])))
            raw = raw_by_row.get(source_row)
            if raw is None:
                raise ValueError(f"Cannot reconstruct QA {qa_id} at AHD source row {source_row}")
            question = clean(raw.get("Question"))
            answer = clean(raw.get("Answer"))
            category = clean(raw.get("Category"))
            quality = "raw_ahd_source_row"
        rows.append(
            {
                "qa_id": qa_id,
                "question": question,
                "answer": answer,
                "category": category,
                "source_row_number": source_row,
                "source_quality": quality,
                "source_graph_versions": "|".join(sorted(source_versions[qa_id] - {""})),
                "graph_version": GRAPH_VERSION,
            }
        )
    return rows, {
        "qa_ids_with_multiple_observed_source_rows": sum(
            len(values) > 1 for values in reference_source_rows.values()
        ),
        "observed_source_rows_disagreeing_with_authoritative_source": authoritative_mismatches,
        "qa_records_reconstructed_from_raw_ahd": sum(
            row["source_quality"] == "raw_ahd_source_row" for row in rows
        ),
    }


def duplicate_count(rows: Iterable[dict[str, Any]], field: str) -> int:
    values = [clean(row.get(field)) for row in rows]
    return len(values) - len(set(values))


def validate_final_graph(
    entities: list[dict[str, Any]],
    mentions: list[dict[str, Any]],
    qa_records: list[dict[str, Any]],
    decisions: list[dict[str, Any]],
    relations: list[dict[str, Any]],
    bidirectional: list[dict[str, Any]],
) -> dict[str, int]:
    entity_ids = {row["entity_id"] for row in entities}
    qa_ids = {row["qa_id"] for row in qa_records}
    metrics = {
        "duplicate_entity_ids": duplicate_count(entities, "entity_id"),
        "duplicate_entity_keys": len(entities)
        - len({(row["entity_type"], row["canonical_name_norm"]) for row in entities}),
        "duplicate_mention_ids": duplicate_count(mentions, "mention_id"),
        "duplicate_qa_ids": duplicate_count(qa_records, "qa_id"),
        "duplicate_relation_decision_ids": duplicate_count(decisions, "relation_id"),
        "duplicate_direct_relation_ids": duplicate_count(relations, "relation_id"),
        "duplicate_edge_ids": duplicate_count(bidirectional, "edge_id"),
        "mentions_missing_entity": sum(row["entity_id"] not in entity_ids for row in mentions),
        "mentions_missing_qa": sum(row["qa_id"] not in qa_ids for row in mentions),
        "relations_missing_source": sum(row["source_entity_id"] not in entity_ids for row in relations),
        "relations_missing_target": sum(row["target_entity_id"] not in entity_ids for row in relations),
        "relations_missing_qa": sum(row["qa_id"] not in qa_ids for row in relations),
        "bidirectional_count_mismatch": abs(len(bidirectional) - (2 * len(relations))),
    }
    if any(metrics.values()):
        raise ValueError(f"final_v2 validation failed: {metrics}")
    return metrics


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--force-overwrite", action="store_true")
    parser.add_argument(
        "--expected-entity-chunks",
        type=int,
        default=0,
        help=(
            "Exact completed entity-chunk count for a bounded snapshot. "
            "Omit only when entity extraction is complete."
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.build:
        raise RuntimeError("No final graph files are written without --build.")
    if args.expected_entity_chunks < 0:
        raise ValueError("--expected-entity-chunks must be non-negative.")
    entity_progress = require_entity_snapshot(
        ENTITY_EXPANSION / "progress.json", args.expected_entity_chunks
    )
    candidate_manifest = json.loads(
        (RELATION_EXPANSION / "candidate_manifest.json").read_text(encoding="utf-8")
    )
    validate_snapshot_manifest(entity_progress, candidate_manifest)
    relation_progress = require_complete_progress(
        RELATION_EXPANSION / "progress.json", "total_requests", "completed_requests"
    )
    relation_manifest = json.loads(
        (RELATION_EXPANSION / "manifest.json").read_text(encoding="utf-8")
    )
    if relation_manifest.get("exports", {}).get("candidate_decisions_missing") != 0:
        raise RuntimeError("Expansion relation validation has missing decisions.")
    expected_candidates = int(candidate_manifest.get("candidate_rows", -1))
    exported_decisions = int(relation_manifest.get("exports", {}).get("relation_decisions", -1))
    if expected_candidates <= 0 or exported_decisions != expected_candidates:
        raise RuntimeError(
            "Expansion relation decision count does not match the frozen candidate pool: "
            f"expected={expected_candidates}, exported={exported_decisions}"
        )
    if FINAL_V2.exists() and any(FINAL_V2.iterdir()) and not args.force_overwrite:
        raise FileExistsError("outputs/final_graph_v2 already exists; use --force-overwrite intentionally.")
    FINAL_V2.mkdir(parents=True, exist_ok=True)

    old_entities = read_csv(FINAL_V1 / "entities.csv")
    expansion_entities = read_csv(ENTITY_EXPANSION / "entities_expansion.csv")
    entities, expansion_id_map, entity_stats = merge_entities(old_entities, expansion_entities)

    mentions, mention_stats = merge_mentions(
        entities,
        read_csv(FINAL_V1 / "entity_mentions.csv"),
        read_csv(ENTITY_EXPANSION / "entity_mentions_expansion.csv"),
        expansion_id_map,
    )
    decisions, relations, bidirectional, relation_stats = merge_relation_decisions(
        read_csv(FINAL_V1 / "relation_decisions.csv"),
        read_csv(RELATION_EXPANSION / "relation_decisions.csv"),
        expansion_id_map,
    )
    qa_records, qa_stats = build_qa_records(mentions, relations)
    validation = validate_final_graph(
        entities, mentions, qa_records, decisions, relations, bidirectional
    )

    entity_fields = [
        "entity_id", "canonical_name", "canonical_name_norm", "entity_type",
        "aliases", "confidence", "mention_count", "provider", "model",
        "source_graph_versions", "graph_version",
    ]
    mention_fields = [
        "mention_id", "entity_id", "canonical_name", "entity_type", "chunk_id",
        "qa_id", "source_row_number", "surface_form", "field", "evidence",
        "extraction_method", "provider", "model", "confidence", "llm_confidence",
        "prompt_version", "source_graph_version", "graph_version",
    ]
    relation_fields = [
        "relation_id", "source_relation_id", "chunk_id", "qa_id",
        "source_row_number", "source_entity_id", "source_name", "source_type",
        "target_entity_id", "target_name", "target_type", "candidate_relation_type",
        "validated_relation_type", "keep", "confidence", "evidence", "reason",
        "provider", "model", "prompt_version", "source_graph_version", "graph_version",
    ]
    write_csv(FINAL_V2 / "entities.csv", entities, entity_fields)
    write_csv(FINAL_V2 / "entity_mentions.csv", mentions, mention_fields)
    write_csv(
        FINAL_V2 / "qa_records.csv",
        qa_records,
        [
            "qa_id", "question", "answer", "category", "source_row_number",
            "source_quality", "source_graph_versions", "graph_version",
        ],
    )
    write_csv(FINAL_V2 / "relation_decisions.csv", decisions, relation_fields)
    write_csv(FINAL_V2 / "relations.csv", relations, relation_fields)
    write_csv(
        FINAL_V2 / "relations_bidirectional.csv",
        bidirectional,
        relation_fields + ["edge_id", "graph_relation_type", "direction"],
    )

    manifest = {
        "graph_version": GRAPH_VERSION,
        "parent_graph_version": "final_v1",
        "expansion_version": "expansion_v2",
        "entity_snapshot_completed_chunks": entity_progress["completed_chunks"],
        "entity_source_total_chunks": entity_progress["total_chunks"],
        "entity_snapshot_is_full_source": (
            entity_progress["completed_chunks"] == entity_progress["total_chunks"]
        ),
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "counts": {
            "entities": len(entities),
            "entity_mentions": len(mentions),
            "qa_records": len(qa_records),
            "relation_decisions": len(decisions),
            "direct_relations": len(relations),
            "bidirectional_relations": len(bidirectional),
        },
        "entity_types": dict(Counter(row["entity_type"] for row in entities)),
        "relation_types": dict(Counter(row["validated_relation_type"] for row in relations)),
        "qa_source_quality": dict(Counter(row["source_quality"] for row in qa_records)),
        "merge_statistics": {
            **entity_stats,
            **mention_stats,
            **relation_stats,
            **qa_stats,
        },
        "validation": validation,
        "sources": {
            "final_v1_manifest": (FINAL_V1 / "graph_manifest.json").relative_to(ROOT).as_posix(),
            "expansion_entity_manifest": (ENTITY_EXPANSION / "manifest.json").relative_to(ROOT).as_posix(),
            "expansion_relation_manifest": (RELATION_EXPANSION / "manifest.json").relative_to(ROOT).as_posix(),
            "expansion_candidate_manifest": (
                RELATION_EXPANSION / "candidate_manifest.json"
            ).relative_to(ROOT).as_posix(),
            "final_v1_entities_sha256": file_sha256(FINAL_V1 / "entities.csv"),
            "expansion_entities_sha256": file_sha256(ENTITY_EXPANSION / "entities_expansion.csv"),
            "expansion_relations_sha256": file_sha256(RELATION_EXPANSION / "relations_expansion.csv"),
            "relation_progress_completed": relation_progress["completed_requests"],
        },
        "frozen_parent_modified": False,
        "supplemental_graph_used": False,
        "secrets_persisted": False,
    }
    (FINAL_V2 / "graph_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    readme = f"""# AHD Final Graph v2

`final_v2` extends the frozen `final_v1` graph with an explicitly frozen
{entity_progress['completed_chunks']}-chunk slice of the disjoint AHD training
expansion. The parent graph was not modified.

## Build decisions

- Entity and relation extraction reuse the Aziza Step 1-4 schema and prompts.
- Only medium/high-quality actionable expansion entities enter the graph.
- Canonical duplicates merge by `(entity_type, canonical_name_norm)` while old
  `final_v1` IDs remain stable.
- Relation candidates come only from same-QA co-occurrence and every edge is
  retained only after strict evidence validation.
- The entity files are hash-bound to the Step 4 candidate manifest; every
  candidate in that snapshot has exactly one validation decision.
- Direct and inverse edges remain distinguishable through `direction`.
- QA text is resolved from preprocessed provenance or the original AHD source
  row; there are no orphan mentions or relation endpoints.
- The unvalidated supplemental graph is not used.

## Counts

- Medical entities: {len(entities)}
- Evidence mentions: {len(mentions)}
- QA records: {len(qa_records)}
- Validated direct relations: {len(relations)}
- Bidirectional relation rows: {len(bidirectional)}

See `graph_manifest.json` for hashes, merge statistics, and validation results.
"""
    (FINAL_V2 / "README.md").write_text(readme, encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
