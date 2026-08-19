"""Prepare a leakage-audited retrieval/generation cohort from entity ground truth.

The source CSV is entity-shaped: one row per annotated entity, so its first 100
rows are not necessarily 100 distinct questions. This adapter selects the first
100 unique questions in source order and retains every entity annotation attached
to those questions.

Graph IDs are derived only by conservative name/type matching against frozen
``final_v1`` entities. The mapping audit records every ambiguity and unresolved
concept; source annotations are never changed.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.step08a_normalize_query import normalize_query


DEFAULT_SOURCE = (
    ROOT
    / "data"
    / "evaluation"
    / "entity_extraction"
    / "ground_truth_entities_100.csv"
)
DEFAULT_ENTITIES = ROOT / "outputs" / "final_graph" / "entities.csv"
DEFAULT_OUTPUT = ROOT / "data" / "evaluation" / "entity_ground_truth_trial_100.csv"
DEFAULT_AUDIT = (
    ROOT / "data" / "evaluation" / "entity_ground_truth_trial_100_mapping.csv"
)
DEFAULT_MANIFEST = (
    ROOT / "data" / "evaluation" / "entity_ground_truth_trial_100_manifest.json"
)

GOLD_COLUMNS = [
    "query_id",
    "query",
    "query_group",
    "reference_answer",
    "gold_entity_ids",
    "gold_evidence_ids",
    "gold_qa_ids",
    "gold_relation_ids",
    "answerable_from_final_graph",
    "annotation_status",
    "annotator_id",
    "adjudicator_id",
    "annotation_notes",
]

AUDIT_COLUMNS = [
    "query_id",
    "source_entity_row",
    "canonical_name",
    "canonical_name_norm",
    "entity_type",
    "mapping_status",
    "match_type",
    "selected_entity_id",
    "selected_canonical_name",
    "candidate_entity_ids",
    "candidate_count",
]


def normalized(value: Any) -> str:
    return normalize_query(str(value or "")).normalized_query


def without_article(value: str) -> str:
    text = normalized(value)
    return text[2:].strip() if text.startswith("ال") and len(text) > 2 else text


def parse_aliases(value: Any) -> list[str]:
    text = str(value or "").strip()
    if not text:
        return []
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return [part.strip() for part in text.split("|") if part.strip()]
    if isinstance(parsed, list):
        return [str(item).strip() for item in parsed if str(item).strip()]
    return []


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_csv(path: Path, columns: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def entity_indexes(
    rows: list[dict[str, str]],
) -> tuple[
    dict[tuple[str, str], list[dict[str, Any]]],
    dict[tuple[str, str], list[dict[str, Any]]],
    dict[tuple[str, str], list[dict[str, Any]]],
]:
    canonical: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    aliases: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    article: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        prepared = {
            **row,
            "_mention_count": int(float(row.get("mention_count") or 0)),
            "_confidence": float(row.get("confidence") or 0.0),
        }
        entity_type = str(row.get("entity_type") or "").strip()
        canonical_terms = {
            normalized(row.get("canonical_name")),
            normalized(row.get("canonical_name_norm")),
        }
        alias_terms = {normalized(value) for value in parse_aliases(row.get("aliases"))}
        for term in canonical_terms - {""}:
            canonical[(term, entity_type)].append(prepared)
            article[(without_article(term), entity_type)].append(prepared)
        for term in alias_terms - {""}:
            aliases[(term, entity_type)].append(prepared)
            article[(without_article(term), entity_type)].append(prepared)
    return canonical, aliases, article


def unique_candidates(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id = {str(row["entity_id"]): row for row in rows}
    return sorted(
        by_id.values(),
        key=lambda row: (
            -int(row["_mention_count"]),
            -float(row["_confidence"]),
            str(row["entity_id"]),
        ),
    )


def map_entity(
    canonical_name: str,
    entity_type: str,
    indexes: tuple[
        dict[tuple[str, str], list[dict[str, Any]]],
        dict[tuple[str, str], list[dict[str, Any]]],
        dict[tuple[str, str], list[dict[str, Any]]],
    ],
) -> tuple[str, str, dict[str, Any] | None, list[dict[str, Any]]]:
    name_norm = normalized(canonical_name)
    canonical, aliases, article = indexes
    search = (
        ("exact_canonical", canonical.get((name_norm, entity_type), [])),
        ("exact_alias", aliases.get((name_norm, entity_type), [])),
        (
            "article_normalized",
            article.get((without_article(name_norm), entity_type), []),
        ),
    )
    for match_type, raw_candidates in search:
        candidates = unique_candidates(raw_candidates)
        if not candidates:
            continue
        status = "mapped" if len(candidates) == 1 else "duplicate_family_resolved"
        return status, match_type, candidates[0], candidates
    return "unresolved", "none", None, []


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Prepare the 100-query entity-ground-truth trial cohort."
    )
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--entities", type=Path, default=DEFAULT_ENTITIES)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--mapping-audit", type=Path, default=DEFAULT_AUDIT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--query-count", type=int, default=100)
    args = parser.parse_args()

    source = args.source.resolve()
    entities_path = args.entities.resolve()
    output = args.output.resolve()
    audit_path = args.mapping_audit.resolve()
    manifest_path = args.manifest.resolve()
    for path in (output, audit_path, manifest_path):
        if path.exists():
            raise FileExistsError(f"Refusing to overwrite existing artifact: {path}")

    source_rows = read_csv(source)
    required = {"question", "answer", "entity_type", "canonical_name"}
    missing = required - set(source_rows[0] if source_rows else {})
    if missing:
        raise ValueError(f"Ground-truth source is missing columns: {sorted(missing)}")

    questions: list[str] = []
    rows_by_question: dict[str, list[tuple[int, dict[str, str]]]] = defaultdict(list)
    for source_row, row in enumerate(source_rows, start=2):
        question = str(row.get("question") or "").strip()
        answer = str(row.get("answer") or "").strip()
        if not question or not answer:
            continue
        if question not in rows_by_question:
            questions.append(question)
        rows_by_question[question].append((source_row, row))
    selected_questions = questions[: args.query_count]
    if len(selected_questions) != args.query_count:
        raise ValueError(
            f"Requested {args.query_count} unique questions, found "
            f"{len(selected_questions)}."
        )

    indexes = entity_indexes(read_csv(entities_path))
    gold_rows: list[dict[str, Any]] = []
    audit_rows: list[dict[str, Any]] = []
    status_counts: Counter[str] = Counter()
    selected_source_entity_rows = 0
    queries_with_mapped_entities = 0

    for query_number, question in enumerate(selected_questions, start=1):
        query_id = f"entitygtv1_{query_number:03d}"
        annotations = rows_by_question[question]
        selected_source_entity_rows += len(annotations)
        reference_answers = {str(row["answer"]).strip() for _, row in annotations}
        if len(reference_answers) != 1:
            raise ValueError(f"Inconsistent reference answers for {query_id}.")
        mapped_ids: list[str] = []
        entity_types: list[str] = []
        unresolved_names: list[str] = []

        for source_row, annotation in annotations:
            entity_type = str(annotation["entity_type"]).strip()
            canonical_name = str(annotation["canonical_name"]).strip()
            entity_types.append(entity_type)
            status, match_type, selected, candidates = map_entity(
                canonical_name,
                entity_type,
                indexes,
            )
            status_counts[status] += 1
            if selected is not None:
                entity_id = str(selected["entity_id"])
                if entity_id not in mapped_ids:
                    mapped_ids.append(entity_id)
            else:
                unresolved_names.append(canonical_name)
            audit_rows.append(
                {
                    "query_id": query_id,
                    "source_entity_row": source_row,
                    "canonical_name": canonical_name,
                    "canonical_name_norm": normalized(canonical_name),
                    "entity_type": entity_type,
                    "mapping_status": status,
                    "match_type": match_type,
                    "selected_entity_id": (
                        str(selected["entity_id"]) if selected is not None else ""
                    ),
                    "selected_canonical_name": (
                        str(selected["canonical_name"]) if selected is not None else ""
                    ),
                    "candidate_entity_ids": "|".join(
                        str(candidate["entity_id"]) for candidate in candidates
                    ),
                    "candidate_count": len(candidates),
                }
            )

        if mapped_ids:
            queries_with_mapped_entities += 1
        notes = [
            "Human entity name/type ground truth from ground_truth_entities_100.csv.",
            "Graph IDs mapped deterministically by normalized name and entity type.",
            "Exact-question QA artifacts must be removed by the evaluation leakage guard.",
            f"source_entity_rows={len(annotations)}",
            f"mapped_graph_entities={len(mapped_ids)}",
        ]
        if unresolved_names:
            notes.append("unresolved_entities=" + "|".join(unresolved_names))
        gold_rows.append(
            {
                "query_id": query_id,
                "query": question,
                "query_group": "entity_ground_truth",
                "reference_answer": next(iter(reference_answers)),
                "gold_entity_ids": "|".join(mapped_ids),
                "gold_evidence_ids": "",
                "gold_qa_ids": "",
                "gold_relation_ids": "",
                "answerable_from_final_graph": "",
                "annotation_status": "annotated",
                "annotator_id": "source_entity_ground_truth",
                "adjudicator_id": "",
                "annotation_notes": " ".join(notes),
            }
        )

    write_csv(output, GOLD_COLUMNS, gold_rows)
    write_csv(audit_path, AUDIT_COLUMNS, audit_rows)
    manifest = {
        "cohort": "entity_ground_truth_trial_100",
        "created_at_utc": datetime.now(UTC).isoformat(),
        "selection": "first 100 unique questions in source order",
        "source": str(source.relative_to(ROOT)),
        "source_sha256": sha256(source),
        "frozen_entities": str(entities_path.relative_to(ROOT)),
        "frozen_entities_sha256": sha256(entities_path),
        "graph_version": "final_v1",
        "source_rows": len(source_rows),
        "source_unique_questions": len(questions),
        "selected_queries": len(gold_rows),
        "selected_entity_annotations": selected_source_entity_rows,
        "mapping_status": dict(status_counts),
        "queries_with_mapped_graph_entities": queries_with_mapped_entities,
        "queries_without_mapped_graph_entities": (
            len(gold_rows) - queries_with_mapped_entities
        ),
        "mapping_policy": (
            "same entity type; exact canonical, exact alias, then definite-article "
            "normalization; duplicate graph families resolve to highest mention_count, "
            "then confidence, then entity_id"
        ),
        "metric_scope_warning": (
            "Entity retrieval metrics cover only queries with a mapped final_v1 "
            "entity ID. Evidence, QA, and relation relevance IDs were not annotated."
        ),
        "qa_leakage_policy": (
            "run_retrieval_ablation.py removes normalized exact-question artifacts "
            "from every retrieval mode before ranking"
        ),
        "output": str(output.relative_to(ROOT)),
        "mapping_audit": str(audit_path.relative_to(ROOT)),
    }
    write_json(manifest_path, manifest)
    print(
        json.dumps(
            {
                "status": "ok",
                "queries": len(gold_rows),
                "entity_annotations": selected_source_entity_rows,
                "mapping_status": dict(status_counts),
                "queries_with_mapped_entities": queries_with_mapped_entities,
                "output": str(output.relative_to(ROOT)),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
