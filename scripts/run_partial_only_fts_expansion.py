from __future__ import annotations

"""Expand only partial-only queries against the held-out-safe SQLite FTS index."""

import argparse
import csv
import json
import re
import sqlite3
import sys
import zipfile
from collections import defaultdict
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Iterable, Sequence
from xml.etree import ElementTree

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.config import load_final_config
from src.step08a_normalize_query import normalize_query
from src.step09_hybrid_retrieval import is_generic_entity, normalized_content_terms
from src.step09a_qa_corpus import fts_terms, read_corpus_metadata


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_VARIANTS = (
    ROOT
    / "data"
    / "evaluation"
    / "partial_only_graph_guided_search_variants.xlsx"
)
DEFAULT_ANNOTATIONS = (
    ROOT
    / "data"
    / "evaluation"
    / "candidate_relevance_annotations_100_final.csv"
)
DEFAULT_OUTPUT = (
    ROOT
    / "outputs"
    / "evaluation"
    / "retrieval_expansion"
    / "partial_only_fts_candidates_v1.csv"
)

SHEET_NAME = "Search Variants"
VARIANTS = ("A", "B", "C")
RAW_EXPRESSION_RE = re.compile(r'"[^"]+"|\bAND\b|\bOR\b|[()\s]+', re.IGNORECASE)
CELL_REF_RE = re.compile(r"([A-Z]+)")
DRIFT_STOPWORDS = {
    "في",
    "من",
    "على",
    "عن",
    "الى",
    "او",
    "مع",
    "اثناء",
}

OUTPUT_FIELDS = (
    "expansion_version",
    "query_id",
    "original_query",
    "query_group",
    "primary_intent",
    "safety_mode",
    "safety_reason",
    "variant_c_query_source",
    "graph_aliases_added",
    "qa_id",
    "source_row_number",
    "question",
    "answer",
    "category",
    "matched_variants",
    "variant_a_rank",
    "variant_b_rank",
    "variant_c_rank",
    "best_variant_rank",
    "best_bm25_rank",
    "variant_support_count",
    "expansion_rank",
    "relevance_label",
    "error_reason",
    "secondary_error_reason",
    "annotator_id",
    "annotation_status",
    "annotation_notes",
)


# ---------------------------------------------------------------------------
# Minimal read-only XLSX ingestion
# ---------------------------------------------------------------------------


def _column_index(cell_reference: str) -> int:
    match = CELL_REF_RE.match(cell_reference)
    if not match:
        raise ValueError(f"Invalid XLSX cell reference: {cell_reference}")
    value = 0
    for character in match.group(1):
        value = (value * 26) + (ord(character) - ord("A") + 1)
    return value - 1


def _xml_text(node: ElementTree.Element) -> str:
    return "".join(node.itertext())


def read_xlsx_sheet(path: Path, sheet_name: str) -> list[dict[str, str]]:
    """Read static cell values without modifying the supplied workbook."""
    with zipfile.ZipFile(path, "r") as archive:
        workbook = ElementTree.fromstring(archive.read("xl/workbook.xml"))
        relationships = ElementTree.fromstring(
            archive.read("xl/_rels/workbook.xml.rels")
        )
        relationship_targets = {
            item.attrib["Id"]: item.attrib["Target"]
            for item in relationships
        }
        relation_namespace = (
            "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
        )
        target = ""
        for sheet in workbook.findall(".//{*}sheet"):
            if sheet.attrib.get("name") == sheet_name:
                relationship_id = sheet.attrib.get(relation_namespace, "")
                target = relationship_targets.get(relationship_id, "")
                break
        if not target:
            raise ValueError(f"Workbook does not contain sheet {sheet_name!r}.")
        sheet_path = target.lstrip("/")
        if not sheet_path.startswith("xl/"):
            sheet_path = f"xl/{sheet_path}"

        shared_strings: list[str] = []
        if "xl/sharedStrings.xml" in archive.namelist():
            shared_root = ElementTree.fromstring(
                archive.read("xl/sharedStrings.xml")
            )
            shared_strings = [
                _xml_text(item) for item in shared_root.findall(".//{*}si")
            ]

        sheet_root = ElementTree.fromstring(archive.read(sheet_path))
        matrix: list[list[str]] = []
        for row in sheet_root.findall(".//{*}sheetData/{*}row"):
            values: dict[int, str] = {}
            for cell in row.findall("{*}c"):
                column = _column_index(cell.attrib.get("r", ""))
                cell_type = cell.attrib.get("t", "")
                value_node = cell.find("{*}v")
                value = value_node.text if value_node is not None else ""
                if cell_type == "s" and value:
                    value = shared_strings[int(value)]
                elif cell_type == "inlineStr":
                    inline = cell.find("{*}is")
                    value = _xml_text(inline) if inline is not None else ""
                values[column] = str(value or "")
            if values:
                width = max(values) + 1
                matrix.append([values.get(index, "") for index in range(width)])

    if not matrix:
        return []
    headers = [str(value).strip() for value in matrix[0]]
    if not headers or any(not header for header in headers):
        raise ValueError("Variant workbook has blank or invalid headers.")
    return [
        {
            header: row[index] if index < len(row) else ""
            for index, header in enumerate(headers)
        }
        for row in matrix[1:]
        if any(str(value).strip() for value in row)
    ]


# ---------------------------------------------------------------------------
# Input integrity and reformulation safety
# ---------------------------------------------------------------------------


def read_annotations(
    path: Path,
) -> tuple[dict[str, list[dict[str, str]]], dict[str, set[str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    by_query: dict[str, list[dict[str, str]]] = defaultdict(list)
    existing_ids: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        query_id = str(row.get("query_id") or "")
        by_query[query_id].append(row)
        candidate_id = str(row.get("candidate_id") or "")
        qa_id = str(row.get("qa_id") or "")
        if candidate_id:
            existing_ids[query_id].add(candidate_id)
            existing_ids[query_id].add(candidate_id.removeprefix("qa::"))
        if qa_id:
            existing_ids[query_id].add(qa_id)
            existing_ids[query_id].add(f"qa::{qa_id}")
    return by_query, existing_ids


def partial_only_query_ids(
    annotations: dict[str, list[dict[str, str]]],
) -> set[str]:
    result: set[str] = set()
    for query_id, rows in annotations.items():
        labels = {
            str(row.get("relevance_label") or "").strip()
            for row in rows
        }
        if "1" in labels and "2" not in labels:
            result.add(query_id)
    return result


def validate_variant_rows(
    rows: Sequence[dict[str, str]],
    expected_query_ids: set[str],
) -> None:
    required = {
        "query_id",
        "original_query",
        "normalized_query",
        "corrected_query",
        "reformulated_query",
        "medical_phrase_normalized",
        "linked_graph_canonical_names",
        "fts_variant_A_phrase_intent",
        "fts_variant_B_graph_guided",
        "fts_variant_C_full_query",
        "runtime_safe",
    }
    if not rows:
        raise ValueError("Variant workbook contains no query rows.")
    missing = sorted(required.difference(rows[0]))
    if missing:
        raise ValueError(f"Variant workbook is missing columns: {missing}")
    query_ids = [str(row.get("query_id") or "").strip() for row in rows]
    if len(query_ids) != len(set(query_ids)):
        raise ValueError("Variant workbook contains duplicate query IDs.")
    if set(query_ids) != expected_query_ids:
        raise ValueError(
            "Variant workbook does not match the human-labeled partial-only cohort: "
            f"missing={sorted(expected_query_ids.difference(query_ids))}, "
            f"extra={sorted(set(query_ids).difference(expected_query_ids))}."
        )
    unsafe_rows = [
        query_id
        for query_id, row in zip(query_ids, rows)
        if str(row.get("runtime_safe") or "").strip().lower() != "yes"
    ]
    if unsafe_rows:
        raise ValueError(f"Workbook marks runtime-unsafe rows: {unsafe_rows}")


def _near_original(term: str, original_terms: set[str]) -> bool:
    if term in original_terms:
        return True
    if len(term) >= 3 and any(
        term in original or original in term
        for original in original_terms
        if len(original) >= 3
    ):
        return True
    return any(
        SequenceMatcher(None, term, original).ratio() >= 0.84
        for original in original_terms
    )


def reformulation_drift(row: dict[str, str]) -> tuple[bool, list[str]]:
    """Detect new medical words not grounded in the original query or graph link."""
    original_text = str(
        row.get("normalized_query") or row.get("original_query") or ""
    )
    normalized_original = normalize_query(original_text).normalized_query
    original_terms = normalized_content_terms(original_text)
    phrase_terms = normalized_content_terms(
        str(row.get("medical_phrase_normalized") or "")
    )
    linked_terms = normalized_content_terms(
        str(row.get("linked_graph_canonical_names") or "")
    )
    grounded_terms = original_terms | linked_terms
    added = sorted(
        term
        for term in phrase_terms
        if term not in DRIFT_STOPWORDS
        and not _near_original(term, grounded_terms)
        and not (
            term in {"ray", "اشعه"}
            and bool({"اكس", "راي"} & original_terms)
        )
        and not (
            term in {"الم", "الام"}
            and ("الم" in normalized_original or "الام" in normalized_original)
        )
    )
    return bool(added), added


def validate_raw_fts_expression(expression: str) -> str:
    expression = str(expression or "").strip()
    if not expression:
        return ""
    remainder = RAW_EXPRESSION_RE.sub("", expression)
    if remainder:
        raise ValueError(
            "Only quoted FTS phrases connected by AND/OR are allowed; "
            f"unexpected fragment: {remainder!r}"
        )
    if expression.count('"') % 2 or expression.count("(") != expression.count(")"):
        raise ValueError("Unbalanced quotes or parentheses in FTS expression.")
    return expression


def split_pipe_values(value: str) -> list[str]:
    return [
        item.strip()
        for item in str(value or "").split("|")
        if item.strip()
    ]


def load_graph_aliases(config: Any) -> dict[str, list[str]]:
    from src.neo4j_repository import Neo4jRepository

    aliases_by_canonical: dict[str, list[str]] = {}
    with Neo4jRepository(config) as repository:
        for entity in repository.get_entities():
            canonical = str(entity.get("canonical_name") or "").strip()
            canonical_norm = normalize_query(
                str(entity.get("canonical_name_norm") or canonical)
            ).normalized_query
            aliases = entity.get("aliases") or []
            if isinstance(aliases, str):
                aliases = split_pipe_values(aliases)
            clean: list[str] = []
            for alias in aliases:
                text = str(alias or "").strip()
                normalized = normalize_query(text).normalized_query
                if (
                    not text
                    or normalized == canonical_norm
                    or is_generic_entity(text)
                    or text in clean
                ):
                    continue
                clean.append(text)
            aliases_by_canonical[canonical_norm] = clean
    return aliases_by_canonical


def aliases_for_variant(
    row: dict[str, str],
    aliases_by_canonical: dict[str, list[str]],
    max_aliases: int = 6,
) -> list[str]:
    aliases: list[str] = []
    for canonical in split_pipe_values(
        row.get("linked_graph_canonical_names", "")
    ):
        key = normalize_query(canonical).normalized_query
        for alias in aliases_by_canonical.get(key, []):
            if alias not in aliases:
                aliases.append(alias)
            if len(aliases) >= max_aliases:
                return aliases
    return aliases


def expand_first_fts_group(expression: str, aliases: Sequence[str]) -> str:
    if not expression or not aliases:
        return expression
    match = re.match(r"^\((.*?)\)(.*)$", expression, flags=re.DOTALL)
    if not match:
        return expression
    existing_normalized = {
        normalize_query(item).normalized_query
        for item in re.findall(r'"([^"]+)"', match.group(1))
    }
    additions = [
        alias
        for alias in aliases
        if normalize_query(alias).normalized_query not in existing_normalized
    ]
    if not additions:
        return expression
    quoted = " OR ".join(
        f'"{alias.replace(chr(34), chr(34) * 2)}"' for alias in additions
    )
    return f"({match.group(1)} OR {quoted}){match.group(2)}"


# ---------------------------------------------------------------------------
# Read-only FTS execution and candidate deduplication
# ---------------------------------------------------------------------------


def natural_match_expression(query: str) -> str:
    terms = fts_terms(query)
    return " OR ".join(
        f'"{term.replace(chr(34), chr(34) * 2)}"' for term in terms
    )


def execute_fts(
    connection: sqlite3.Connection,
    match_expression: str,
    limit: int,
) -> list[dict[str, Any]]:
    if not match_expression:
        return []
    rows = connection.execute(
        """
SELECT q.qa_id, q.source_row_number, q.question, q.answer, q.category,
       bm25(qa_fts, 3.0, 1.0, 0.3) AS lexical_rank
FROM qa_fts
JOIN qa_records AS q ON q.rowid = qa_fts.rowid
WHERE qa_fts MATCH ?
ORDER BY lexical_rank
LIMIT ?
""".strip(),
        (match_expression, max(1, limit)),
    ).fetchall()
    return [dict(row) for row in rows]


def merge_new_candidates(
    query_id: str,
    row: dict[str, str],
    variant_results: dict[str, list[dict[str, Any]]],
    existing_ids: set[str],
    safety_mode: str,
    safety_reason: str,
    variant_c_query_source: str,
    graph_aliases_added: Sequence[str],
    max_new_per_query: int,
) -> tuple[list[dict[str, Any]], int]:
    merged: dict[str, dict[str, Any]] = {}
    excluded_existing = 0
    for variant, results in variant_results.items():
        for rank, result in enumerate(results, start=1):
            qa_id = str(result.get("qa_id") or "")
            if qa_id in existing_ids or f"qa::{qa_id}" in existing_ids:
                excluded_existing += 1
                continue
            candidate = merged.setdefault(
                qa_id,
                {
                    "expansion_version": "partial_only_fts_v1",
                    "query_id": query_id,
                    "original_query": row.get("original_query", ""),
                    "query_group": row.get("query_group", ""),
                    "primary_intent": row.get("primary_intent", ""),
                    "safety_mode": safety_mode,
                    "safety_reason": safety_reason,
                    "variant_c_query_source": variant_c_query_source,
                    "graph_aliases_added": "|".join(graph_aliases_added),
                    "qa_id": qa_id,
                    "source_row_number": result.get("source_row_number", ""),
                    "question": result.get("question", ""),
                    "answer": result.get("answer", ""),
                    "category": result.get("category", ""),
                    "matched_variants": [],
                    "variant_a_rank": "",
                    "variant_b_rank": "",
                    "variant_c_rank": "",
                    "best_variant_rank": rank,
                    "best_bm25_rank": float(result.get("lexical_rank") or 0.0),
                    "variant_support_count": 0,
                    "expansion_rank": "",
                    "relevance_label": "",
                    "error_reason": "",
                    "secondary_error_reason": "",
                    "annotator_id": "",
                    "annotation_status": "pending_human_annotation",
                    "annotation_notes": "",
                },
            )
            candidate["matched_variants"].append(variant)
            candidate[f"variant_{variant.lower()}_rank"] = rank
            candidate["best_variant_rank"] = min(
                int(candidate["best_variant_rank"]),
                rank,
            )
            candidate["best_bm25_rank"] = min(
                float(candidate["best_bm25_rank"]),
                float(result.get("lexical_rank") or 0.0),
            )
            candidate["variant_support_count"] = len(
                set(candidate["matched_variants"])
            )

    ordered = sorted(
        merged.values(),
        key=lambda item: (
            -int(item["variant_support_count"]),
            int(item["best_variant_rank"]),
            float(item["best_bm25_rank"]),
        ),
    )[: max(1, max_new_per_query)]
    for expansion_rank, item in enumerate(ordered, start=1):
        item["expansion_rank"] = expansion_rank
        item["matched_variants"] = "|".join(
            variant for variant in VARIANTS if variant in item["matched_variants"]
        )
        item["best_bm25_rank"] = round(float(item["best_bm25_rank"]), 6)
    return ordered, excluded_existing


def batched_rows(
    rows: Iterable[dict[str, Any]],
    limit: int,
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for row in rows:
        result.append(row)
        if limit > 0 and len(result) >= limit:
            break
    return result


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(
        description="Run targeted held-out-safe FTS expansion for partial-only queries."
    )
    parser.add_argument("--variants-xlsx", type=Path, default=DEFAULT_VARIANTS)
    parser.add_argument("--annotations", type=Path, default=DEFAULT_ANNOTATIONS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--per-variant-k", type=int, default=10)
    parser.add_argument("--max-new-per-query", type=int, default=20)
    parser.add_argument("--limit-queries", type=int, default=0)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument(
        "--expand-graph-aliases",
        action="store_true",
        help="Load final_v1 aliases from Neo4j and add them to Variant B.",
    )
    args = parser.parse_args()

    variants_path = args.variants_xlsx.resolve()
    annotations_path = args.annotations.resolve()
    variant_rows = read_xlsx_sheet(variants_path, SHEET_NAME)
    annotations, existing_ids = read_annotations(annotations_path)
    expected_query_ids = partial_only_query_ids(annotations)
    validate_variant_rows(variant_rows, expected_query_ids)
    selected_rows = batched_rows(variant_rows, max(0, args.limit_queries))

    drift_rows: dict[str, list[str]] = {}
    for row in selected_rows:
        drifted, added_terms = reformulation_drift(row)
        if drifted:
            drift_rows[str(row["query_id"])] = added_terms

    config = load_final_config()
    aliases_by_canonical = (
        load_graph_aliases(config) if args.expand_graph_aliases else {}
    )
    aliases_by_query = {
        str(row["query_id"]): aliases_for_variant(row, aliases_by_canonical)
        for row in selected_rows
    }
    index_path = Path(config.qa_corpus.index_path).resolve()
    metadata = read_corpus_metadata(index_path)
    if metadata.get("corpus_version") != config.qa_corpus.corpus_version:
        raise RuntimeError(
            "Held-out-safe index version mismatch: "
            f"configured={config.qa_corpus.corpus_version}, "
            f"indexed={metadata.get('corpus_version')}"
        )
    if metadata.get("holdout_policy") != "exclude all normalized eval_test questions":
        raise RuntimeError(
            "Refusing expansion because the index does not declare the eval_test "
            "exclusion policy."
        )

    preflight = {
        "partial_only_queries": len(expected_query_ids),
        "selected_queries": len(selected_rows),
        "reformulation_drift_queries": len(drift_rows),
        "drift_query_ids": sorted(drift_rows),
        "drift_terms_by_query": {
            query_id: drift_rows[query_id] for query_id in sorted(drift_rows)
        },
        "corpus_version": metadata.get("corpus_version"),
        "indexed_rows": metadata.get("indexed_rows"),
        "holdout_policy": metadata.get("holdout_policy"),
        "reference_answers_used": False,
        "human_labels_used_for_query_construction": False,
        "graph_alias_expansion_enabled": bool(args.expand_graph_aliases),
        "queries_with_graph_aliases_added": sum(
            bool(values) for values in aliases_by_query.values()
        ),
        "graph_aliases_added": sum(
            len(values) for values in aliases_by_query.values()
        ),
    }
    if args.dry_run:
        print(json.dumps(preflight, ensure_ascii=False))
        return 0

    output = args.output.resolve()
    summary_path = output.with_name(f"{output.stem}_summary.json")
    existing_outputs = [path for path in (output, summary_path) if path.exists()]
    if existing_outputs and not args.force:
        raise FileExistsError(
            "Expansion output already exists; use --force to replace it: "
            + ", ".join(str(path) for path in existing_outputs)
        )

    connection = sqlite3.connect(f"file:{index_path.as_posix()}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    all_candidates: list[dict[str, Any]] = []
    raw_hits = {variant: 0 for variant in VARIANTS}
    queries_with_hits = {variant: 0 for variant in VARIANTS}
    excluded_existing = 0
    try:
        for row in selected_rows:
            query_id = str(row["query_id"])
            drifted = query_id in drift_rows
            safety_mode = (
                "original_query_only_due_reformulation_drift"
                if drifted
                else "all_three_variants"
            )
            safety_reason = (
                "New medical phrase terms were not grounded in the original query "
                f"or a linked graph entity: {'|'.join(drift_rows[query_id])}"
                if drifted
                else ""
            )
            variant_c_query_source = (
                "original_query" if drifted else "fts_variant_C_full_query"
            )
            graph_aliases = aliases_by_query.get(query_id, [])
            variant_b_expression = (
                ""
                if drifted
                else expand_first_fts_group(
                    row.get("fts_variant_B_graph_guided", ""),
                    graph_aliases,
                )
            )
            expressions = {
                "A": ""
                if drifted
                else validate_raw_fts_expression(
                    row.get("fts_variant_A_phrase_intent", "")
                ),
                "B": ""
                if drifted
                else validate_raw_fts_expression(
                    variant_b_expression
                ),
                "C": natural_match_expression(
                    row.get("original_query", "")
                    if drifted
                    else row.get("fts_variant_C_full_query", "")
                ),
            }
            variant_results: dict[str, list[dict[str, Any]]] = {}
            for variant, expression in expressions.items():
                results = execute_fts(
                    connection,
                    expression,
                    max(1, args.per_variant_k),
                )
                variant_results[variant] = results
                raw_hits[variant] += len(results)
                if results:
                    queries_with_hits[variant] += 1
            candidates, excluded = merge_new_candidates(
                query_id,
                row,
                variant_results,
                existing_ids.get(query_id, set()),
                safety_mode,
                safety_reason,
                variant_c_query_source,
                graph_aliases,
                max_new_per_query=max(1, args.max_new_per_query),
            )
            excluded_existing += excluded
            all_candidates.extend(candidates)
    finally:
        connection.close()

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(all_candidates)

    candidate_queries = {str(row["query_id"]) for row in all_candidates}
    summary = {
        **preflight,
        "per_variant_k": max(1, args.per_variant_k),
        "max_new_per_query": max(1, args.max_new_per_query),
        "raw_hits_by_variant": raw_hits,
        "queries_with_hits_by_variant": queries_with_hits,
        "existing_hits_excluded": excluded_existing,
        "new_deduplicated_candidates": len(all_candidates),
        "queries_with_new_candidates": len(candidate_queries),
        "queries_without_new_candidates": len(selected_rows) - len(candidate_queries),
        "output": display_path(output),
    }
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                **summary,
                "summary": display_path(summary_path),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
