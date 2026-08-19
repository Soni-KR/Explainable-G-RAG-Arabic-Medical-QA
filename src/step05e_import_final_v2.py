"""Dry-run or explicitly import final_v2 into its isolated Neo4j service."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.config import load_final_v2_config
from src.neo4j_repository import Neo4jRepository
from src.step05b_graph_import_utils import (
    DEFAULT_BATCH_SIZE,
    compare_counts,
    constraint_cypher_templates,
    execute_batch_import,
    execute_query,
    graph_record_count_queries,
    node_import_cypher_templates,
    node_rows,
    planned_counts,
    print_counts,
    read_counts,
    relationship_import_cypher_templates,
    relationship_rows,
    validation_queries,
)
from src.step05d_final_v2_adapter import load_final_v2_records


def dry_run(batch_size: int) -> int:
    config = load_final_v2_config()
    records, validation = load_final_v2_records()
    print("Final v2 Neo4j importer dry-run")
    print(f"uri: {config.neo4j.uri}")
    print(f"database: {config.neo4j.database}")
    print(f"graph_version: {config.graph_version}")
    print(f"batch_size: {batch_size}")
    for key, value in planned_counts(records).items():
        print(f"{key}: {value}")
    print(f"validation_errors: {len(validation.errors)}")
    print(f"validation_warnings: {len(validation.warnings)}")
    print("writes_executed: 0")
    print(f"status: {'ok' if validation.ok else 'failed'}")
    return 0 if validation.ok else 1


def execute_import(batch_size: int) -> int:
    config = load_final_v2_config()
    if config.graph_version != "final_v2":
        print(f"status: stopped_unexpected_graph_version_{config.graph_version}")
        return 1
    records, validation = load_final_v2_records()
    if validation.errors:
        print(f"adapter_validation: failed ({len(validation.errors)} errors)")
        return 1

    with Neo4jRepository(config=config) as repository:
        before = read_counts(repository, graph_record_count_queries())
        print_counts("pre_import_counts", before)
        if any(before.values()):
            print("status: stopped_existing_graph_records_found")
            return 1

        for query in constraint_cypher_templates():
            execute_query(repository, query)
        node_queries = node_import_cypher_templates()
        relationship_queries = relationship_import_cypher_templates()
        nodes = node_rows(records, config.graph_version)
        relationships = relationship_rows(records, config.graph_version)

        execute_batch_import(repository, node_queries["entities"], nodes["entities"], batch_size)
        execute_batch_import(repository, node_queries["mentions"], nodes["mentions"], batch_size)
        execute_batch_import(repository, node_queries["qa_records"], nodes["qa_records"], batch_size)
        execute_batch_import(
            repository, relationship_queries["mentioned_in"], relationships["mentioned_in"], batch_size
        )
        execute_batch_import(
            repository, relationship_queries["evidence_from"], relationships["evidence_from"], batch_size
        )
        execute_batch_import(
            repository,
            relationship_queries["medical_relations"],
            relationships["medical_relations"],
            batch_size,
        )

        actual = read_counts(repository, graph_record_count_queries())
        integrity = read_counts(repository, validation_queries())

    matches = compare_counts(actual, records)
    print("import_completed: true")
    print(f"database: {config.neo4j.database}")
    print(f"graph_version: {config.graph_version}")
    print_counts("post_import_counts", actual)
    print("count_validation")
    for key, ok in matches.items():
        print(f"{key}: {'ok' if ok else 'failed'}")
    print_counts("integrity_validation", integrity)
    status = all(matches.values()) and all(value == 0 for value in integrity.values())
    print(f"status: {'ok' if status else 'failed'}")
    return 0 if status else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
    args = parser.parse_args()
    if args.dry_run == args.execute:
        print("Choose exactly one of --dry-run or --execute.")
        return 2
    return execute_import(args.batch_size) if args.execute else dry_run(args.batch_size)


if __name__ == "__main__":
    raise SystemExit(main())
