from __future__ import annotations

"""Create a human annotation queue from frozen retrieval candidates.

This script never predicts a relevance label.  It copies the top candidates and
their interpretable features into one reviewable CSV while preserving any human
labels already entered during a later refresh.
"""

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RETRIEVAL = (
    ROOT
    / "outputs"
    / "evaluation"
    / "retrieval"
    / "evaluation_v1_retrieval_fullhybrid_qacorpus_identityfix_100q_v1"
    / "full_hybrid.jsonl"
)
DEFAULT_OUTPUT = ROOT / "data" / "evaluation" / "candidate_relevance_annotations_100.csv"
HUMAN_FIELDS = (
    "relevance_label",
    "error_reason",
    "secondary_error_reason",
    "annotator_id",
    "annotation_status",
    "annotation_notes",
)
FIELDS = (
    "annotation_version",
    "query_id",
    "query",
    "query_group",
    "reference_answer",
    "primary_intent",
    "candidate_type",
    "candidate_rank",
    "candidate_id",
    "qa_id",
    "source_quality",
    "retrieval_channel",
    "candidate_question",
    "candidate_answer_or_evidence",
    "relation_type",
    "source_entity_name",
    "target_entity_name",
    "retrieval_score",
    "answer_relevance",
    "query_concept_coverage",
    "query_constraint_coverage",
    "entity_identity",
    "intent_support",
    "source_reliability",
    "vector_similarity",
    "graph_support",
    "anatomy_mismatch",
    "unrelated_condition_mismatch",
    "matched_query_concepts",
    "missing_query_concepts",
    *HUMAN_FIELDS,
)

# Blinded review columns deliberately omit the reference answer, retrieval rank,
# model scores, Step 8 intent, and deterministic reranking features.
INDEPENDENT_FIELDS = (
    "annotation_version",
    "query_id",
    "query",
    "query_group",
    "candidate_type",
    "candidate_id",
    "qa_id",
    "source_quality",
    "retrieval_channel",
    "candidate_question",
    "candidate_answer_or_evidence",
    "relation_type",
    "source_entity_name",
    "target_entity_name",
    *HUMAN_FIELDS,
)


def compact(value: Any, limit: int = 2500) -> str:
    text = " ".join(str(value or "").split())
    return text if len(text) <= limit else text[: limit - 3].rstrip() + "..."


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8-sig") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def existing_human_labels(path: Path) -> dict[tuple[str, str, str], dict[str, str]]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = csv.DictReader(handle)
        return {
            (
                str(row.get("query_id") or ""),
                str(row.get("candidate_type") or ""),
                str(row.get("candidate_id") or ""),
            ): {field: str(row.get(field) or "") for field in HUMAN_FIELDS}
            for row in rows
        }


def feature_columns(features: dict[str, object]) -> dict[str, object]:
    return {
        "query_concept_coverage": features["query_concept_coverage"],
        "query_constraint_coverage": features["query_constraint_coverage"],
        "source_reliability": features["source_reliability"],
        "anatomy_mismatch": str(bool(features["anatomy_mismatch"])).lower(),
        "unrelated_condition_mismatch": str(
            bool(features["unrelated_condition_mismatch"])
        ).lower(),
        "matched_query_concepts": "|".join(features["matched_query_concepts"]),
        "missing_query_concepts": "|".join(features["missing_query_concepts"]),
    }


def record_medical_phrases(record: dict[str, Any]) -> list[str]:
    from src.step09_hybrid_retrieval import select_relevance_phrases

    analysis = dict(record.get("query_analysis") or {})
    return select_relevance_phrases(
        list(analysis.get("medical_phrases") or []),
        str(analysis.get("primary_intent") or ""),
    )


def evidence_row(record: dict[str, Any], item: dict[str, Any], rank: int) -> dict[str, object]:
    from src.query_relevance import candidate_relevance_features

    metadata = dict(item.get("metadata") or {})
    analysis = dict(record.get("query_analysis") or {})
    query = str(analysis.get("reformulated_query") or record.get("query") or "")
    question = str(item.get("question") or "")
    answer = str(item.get("answer") or item.get("text") or "")
    candidate_text = " ".join((question, answer, str(item.get("text") or "")))
    intent = float(metadata.get("intent_support") or 0.0)
    vector = float(metadata.get("vector_similarity") or 0.0)
    graph_support = 1.0 if item.get("relation_ids") else 0.0
    score = float(item.get("score") or 0.0)
    source_quality = str(item.get("source_quality") or "unknown")
    features = candidate_relevance_features(
        query,
        candidate_text,
        source_quality=source_quality,
        intent_support=intent,
        vector_similarity=vector,
        graph_support=graph_support,
        retrieval_score=score,
        query_medical_phrases=record_medical_phrases(record),
    )
    return {
        "candidate_type": "evidence",
        "candidate_rank": rank,
        "candidate_id": str(item.get("evidence_id") or item.get("source_id") or ""),
        "qa_id": str(item.get("qa_id") or ""),
        "source_quality": source_quality,
        "retrieval_channel": str(metadata.get("retrieval_channel") or "graph"),
        "candidate_question": compact(question),
        "candidate_answer_or_evidence": compact(answer),
        "relation_type": "",
        "source_entity_name": "",
        "target_entity_name": "",
        "retrieval_score": round(score, 6),
        "answer_relevance": round(float(metadata.get("answer_relevance") or 0.0), 6),
        "entity_identity": round(float(metadata.get("entity_identity") or 0.0), 6),
        "intent_support": round(intent, 6),
        "vector_similarity": round(vector, 6),
        "graph_support": graph_support,
        **feature_columns(features),
    }


def relation_row(record: dict[str, Any], item: dict[str, Any], rank: int) -> dict[str, object]:
    from src.query_relevance import candidate_relevance_features

    metadata = dict(item.get("metadata") or {})
    evidence_items = list(metadata.get("evidence_items") or [])
    evidence_text = " ".join(
        [
            str(item.get("evidence") or ""),
            *[
                " ".join(
                    (
                        str(row.get("question") or ""),
                        str(row.get("evidence") or ""),
                        str(row.get("answer") or ""),
                    )
                )
                for row in evidence_items
            ],
        ]
    )
    candidate_text = " ".join(
        (
            str(item.get("source_name") or ""),
            str(item.get("target_name") or ""),
            evidence_text,
        )
    )
    source_quality = str(
        next(
            (
                row.get("source_quality")
                for row in evidence_items
                if row.get("source_quality")
            ),
            "unknown",
        )
    )
    intent = float(metadata.get("intent_match") or 0.0)
    vector = float(item.get("semantic_support") or 0.0)
    score = float(item.get("hybrid_score") or 0.0)
    features = candidate_relevance_features(
        str(
            (record.get("query_analysis") or {}).get("reformulated_query")
            or record.get("query")
            or ""
        ),
        candidate_text,
        source_quality=source_quality,
        intent_support=intent,
        vector_similarity=vector,
        graph_support=1.0,
        retrieval_score=score,
        query_medical_phrases=record_medical_phrases(record),
    )
    return {
        "candidate_type": "relation",
        "candidate_rank": rank,
        "candidate_id": str(item.get("relation_id") or ""),
        "qa_id": str(item.get("qa_id") or ""),
        "source_quality": source_quality,
        "retrieval_channel": "graph_relation",
        "candidate_question": "",
        "candidate_answer_or_evidence": compact(evidence_text),
        "relation_type": str(item.get("relation_type") or ""),
        "source_entity_name": compact(item.get("source_name"), 300),
        "target_entity_name": compact(item.get("target_name"), 300),
        "retrieval_score": round(score, 6),
        "answer_relevance": round(float(item.get("evidence_relevance") or 0.0), 6),
        "entity_identity": round(float(metadata.get("medical_identity") or 0.0), 6),
        "intent_support": round(intent, 6),
        "vector_similarity": round(vector, 6),
        "graph_support": 1.0,
        **feature_columns(features),
    }


def build_rows(
    records: list[dict[str, Any]],
    *,
    evidence_top_k: int,
    relation_top_k: int,
    preserved: dict[tuple[str, str, str], dict[str, str]],
) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    for record in records:
        base = {
            "annotation_version": "candidate_relevance_v1",
            "query_id": str(record.get("query_id") or ""),
            "query": str(record.get("query") or ""),
            "query_group": str(record.get("query_group") or ""),
            "reference_answer": str((record.get("gold") or {}).get("reference_answer") or ""),
            "primary_intent": str((record.get("query_analysis") or {}).get("primary_intent") or ""),
        }
        candidates = [
            *[
                evidence_row(record, item, rank)
                for rank, item in enumerate(record.get("evidence") or [], start=1)
                if rank <= evidence_top_k
            ],
            *[
                relation_row(record, item, rank)
                for rank, item in enumerate(record.get("relations") or [], start=1)
                if rank <= relation_top_k
            ],
        ]
        for candidate in candidates:
            key = (
                base["query_id"],
                candidate["candidate_type"],
                candidate["candidate_id"],
            )
            human = preserved.get(
                key,
                {
                    "relevance_label": "",
                    "error_reason": "",
                    "secondary_error_reason": "",
                    "annotator_id": "",
                    "annotation_status": "pending_human_annotation",
                    "annotation_notes": "",
                },
            )
            output.append({**base, **candidate, **human})
    return output


def blinded_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    """Remove evaluation leakage and deterministically blind candidate order."""

    output = [{field: row.get(field, "") for field in INDEPENDENT_FIELDS} for row in rows]
    output.sort(
        key=lambda row: (
            str(row["query_id"]),
            hashlib.sha256(
                (
                    "final_v2_independent_relevance_v1|"
                    f"{row['query_id']}|{row['candidate_type']}|{row['candidate_id']}"
                ).encode("utf-8")
            ).hexdigest(),
        )
    )
    return output


def build_independent_rows(
    records: list[dict[str, Any]], *, evidence_top_k: int, relation_top_k: int
) -> list[dict[str, object]]:
    """Build the blinded queue without importing retrieval or Neo4j code."""

    rows: list[dict[str, object]] = []
    for record in records:
        base = {
            "annotation_version": "final_v2_independent_relevance_v1",
            "query_id": str(record.get("query_id") or ""),
            "query": str(record.get("query") or ""),
            "query_group": str(record.get("query_group") or ""),
        }
        for item in list(record.get("evidence") or [])[:evidence_top_k]:
            metadata = dict(item.get("metadata") or {})
            rows.append(
                {
                    **base,
                    "candidate_type": "evidence",
                    "candidate_id": str(item.get("evidence_id") or item.get("source_id") or ""),
                    "qa_id": str(item.get("qa_id") or ""),
                    "source_quality": str(item.get("source_quality") or "unknown"),
                    "retrieval_channel": str(metadata.get("retrieval_channel") or "unknown"),
                    "candidate_question": compact(item.get("question")),
                    "candidate_answer_or_evidence": compact(item.get("answer") or item.get("text")),
                    "relation_type": "",
                    "source_entity_name": "",
                    "target_entity_name": "",
                    "relevance_label": "",
                    "error_reason": "",
                    "secondary_error_reason": "",
                    "annotator_id": "",
                    "annotation_status": "pending_human_annotation",
                    "annotation_notes": "",
                }
            )
        for item in list(record.get("relations") or [])[:relation_top_k]:
            metadata = dict(item.get("metadata") or {})
            evidence_items = list(metadata.get("evidence_items") or [])
            evidence = " ".join(
                [
                    str(item.get("evidence") or ""),
                    *[
                        str(source.get("evidence") or source.get("answer") or "")
                        for source in evidence_items
                    ],
                ]
            )
            rows.append(
                {
                    **base,
                    "candidate_type": "relation",
                    "candidate_id": str(item.get("relation_id") or ""),
                    "qa_id": str(item.get("qa_id") or ""),
                    "source_quality": str(
                        next(
                            (source.get("source_quality") for source in evidence_items if source.get("source_quality")),
                            "unknown",
                        )
                    ),
                    "retrieval_channel": "graph_relation",
                    "candidate_question": "",
                    "candidate_answer_or_evidence": compact(evidence),
                    "relation_type": str(item.get("relation_type") or ""),
                    "source_entity_name": compact(item.get("source_name"), 300),
                    "target_entity_name": compact(item.get("target_name"), 300),
                    "relevance_label": "",
                    "error_reason": "",
                    "secondary_error_reason": "",
                    "annotator_id": "",
                    "annotation_status": "pending_human_annotation",
                    "annotation_notes": "",
                }
            )
    return blinded_rows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare human relevance labels for frozen candidates.")
    parser.add_argument("--retrieval-jsonl", type=Path, default=DEFAULT_RETRIEVAL)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--evidence-top-k", type=int, default=5)
    parser.add_argument("--relation-top-k", type=int, default=3)
    parser.add_argument(
        "--independent",
        action="store_true",
        help="Create a blinded queue without references, ranks, scores, or model features.",
    )
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Rebuild candidate features while preserving existing human fields by candidate ID.",
    )
    args = parser.parse_args()
    retrieval_path = args.retrieval_jsonl.resolve()
    output_path = args.output.resolve()
    if output_path.exists() and not args.refresh:
        raise FileExistsError(f"Annotation file already exists; use --refresh: {output_path}")
    records = read_jsonl(retrieval_path)
    preserved = existing_human_labels(output_path) if args.refresh else {}
    if args.independent:
        rows = build_independent_rows(
            records,
            evidence_top_k=max(0, args.evidence_top_k),
            relation_top_k=max(0, args.relation_top_k),
        )
        fields = INDEPENDENT_FIELDS
    else:
        rows = build_rows(
            records,
            evidence_top_k=max(0, args.evidence_top_k),
            relation_top_k=max(0, args.relation_top_k),
            preserved=preserved,
        )
        fields = FIELDS
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    query_ids_with_candidates = {row["query_id"] for row in rows}
    print(
        json.dumps(
            {
                "queries": len(records),
                "queries_with_candidates": len(query_ids_with_candidates),
                "queries_without_candidates": len(records) - len(query_ids_with_candidates),
                "candidate_rows": len(rows),
                "evidence_rows": sum(row["candidate_type"] == "evidence" for row in rows),
                "relation_rows": sum(row["candidate_type"] == "relation" for row in rows),
                "human_labels_preserved": sum(
                    bool(row.get("relevance_label")) for row in rows
                ),
                "output": str(output_path.relative_to(ROOT)),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
