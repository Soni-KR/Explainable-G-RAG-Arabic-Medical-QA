from __future__ import annotations

"""Write the immutable pre-result manifest for the two-cohort final evaluation."""

import argparse
import csv
import hashlib
import importlib.metadata
import json
import subprocess
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.config import load_final_config
from src.neo4j_repository import Neo4jRepository


ROOT = Path(__file__).resolve().parents[1]
COHORTS = {
    "ahd_reference_100": {
        "gold": ROOT / "data" / "evaluation" / "retrieval_gold_annotations_100.csv",
        "step08_cache": (
            ROOT
            / "outputs"
            / "evaluation"
            / "retrieval"
            / "evaluation_v1_retrieval_fullhybrid_qacorpus_identityfix_100q_v1"
            / "full_hybrid.jsonl"
        ),
        "independent_retrieval_annotations": (
            ROOT
            / "data"
            / "evaluation"
            / "candidate_relevance_combined_pool_v2.csv"
        ),
    },
    "entity_ground_truth_100": {
        "gold": (
            ROOT
            / "data"
            / "evaluation"
            / "entity_ground_truth_trial_100.csv"
        ),
        "step08_cache": (
            ROOT
            / "outputs"
            / "evaluation"
            / "retrieval"
            / "entity_gt_trial_100_retrieval_v1"
            / "full_hybrid.jsonl"
        ),
        "independent_retrieval_annotations": (
            ROOT
            / "data"
            / "evaluation"
            / "entity_ground_truth_trial_100_mapping.csv"
        ),
    },
}

RUNTIME_FILES = (
    "src/config.py",
    "src/evidence_policy.py",
    "src/models.py",
    "src/neo4j_repository.py",
    "src/query_relevance.py",
    "src/step06_build_embedding_indexes.py",
    "src/step08a_normalize_query.py",
    "src/step08b_analyze_query.py",
    "src/step08c_link_entities.py",
    "src/step08d_plan_retrieval.py",
    "src/step09_hybrid_retrieval.py",
    "src/step09a_qa_corpus.py",
    "src/step10_rerank_subgraph.py",
    "src/step11_build_evidence_context.py",
    "src/step12_generate_grounded_answer.py",
    "src/step13_extract_claims.py",
    "src/step14_verify_claims.py",
    "src/step15_mitigate_hallucinations.py",
    "src/step16_score_reliability.py",
    "src/step17_build_explainable_output.py",
    "scripts/run_retrieval_ablation.py",
    "scripts/build_conditional_fts_ablation.py",
    "scripts/select_frozen_retrieval.py",
    "scripts/run_generation_ablation.py",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def physical_line_count(path: Path) -> int:
    with path.open("r", encoding="utf-8-sig") as handle:
        return sum(1 for line in handle if line.strip())


def record_count(path: Path) -> int:
    if path.suffix.lower() == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return sum(1 for _ in csv.DictReader(handle))
    return physical_line_count(path)


def git_value(*args: str) -> str:
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        return completed.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def package_version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return "not_installed"


def safe_config(config: Any) -> dict[str, Any]:
    return {
        "graph_version": config.graph_version,
        "neo4j": {
            "uri": config.neo4j.uri,
            "database": config.neo4j.database,
            "credentials_configured": bool(
                config.neo4j.username and config.neo4j.password
            ),
        },
        "embeddings": asdict(config.embeddings),
        "qa_corpus": asdict(config.qa_corpus),
        "retrieval": asdict(config.retrieval),
        "query_analysis": {
            "provider": config.query_analysis.provider,
            "model": config.query_analysis.model,
            "reasoning_effort": config.query_analysis.reasoning_effort,
            "temperature": config.query_analysis.temperature,
            "prompt_version": config.query_analysis.prompt_version,
            "api_key_configured": bool(config.query_analysis.groq_api_key),
        },
        "answer_generation": {
            "provider": config.answer_generation.provider,
            "model": config.answer_generation.model,
            "reasoning_effort": config.answer_generation.reasoning_effort,
            "temperature": config.answer_generation.temperature,
            "prompt_version": config.answer_generation.prompt_version,
            "max_attempts": config.answer_generation.max_attempts,
            "api_key_configured": bool(config.answer_generation.groq_api_key),
        },
        "claim_adjudication": {
            "enabled": config.claim_adjudication.enabled,
            "model": config.claim_adjudication.model,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists():
        raise FileExistsError("Frozen manifest already exists and cannot be overwritten.")

    config = load_final_config()
    if config.graph_version != "final_v1":
        raise RuntimeError("The final evaluation requires graph_version=final_v1.")
    if config.claim_adjudication.enabled:
        raise RuntimeError("Semantic claim adjudication must remain disabled.")
    if not config.qa_corpus.enabled:
        raise RuntimeError("The held-out-safe QA corpus must be configured.")
    qa_index = Path(config.qa_corpus.index_path)
    if not qa_index.exists():
        raise FileNotFoundError(f"QA corpus index is missing: {qa_index}")

    calibrator = ROOT / "models" / "claim_verifier_e5_calibrator_v1.json"
    calibrator_payload = (
        json.loads(calibrator.read_text(encoding="utf-8"))
        if calibrator.exists()
        else {}
    )
    if bool(calibrator_payload.get("enabled")):
        raise RuntimeError("The E5 verifier calibrator must remain disabled.")

    cohort_payload: dict[str, Any] = {}
    for name, paths in COHORTS.items():
        for path in paths.values():
            if not path.exists():
                raise FileNotFoundError(f"Frozen cohort input is missing: {path}")
        cohort_payload[name] = {
            key: {
                "path": str(path.relative_to(ROOT)),
                "sha256": sha256(path),
                "record_count": record_count(path),
                "physical_nonempty_lines": physical_line_count(path),
            }
            for key, path in paths.items()
        }

    with Neo4jRepository(config=config) as repository:
        graph_counts = repository.get_graph_counts()
        health = repository.health_check()

    payload = {
        "evaluation_id": "frozen_production_200q_20260728",
        "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
        "purpose": (
            "No-post-hoc-tuning comparison of five retrieval configurations "
            "followed by one generation and deterministic verification run per cohort."
        ),
        "cohorts": cohort_payload,
        "production_config": safe_config(config),
        "graph": {
            "health": {
                "connection": health.get("connection"),
                "database": health.get("database"),
                "neo4j_version": health.get("neo4j_version"),
                "graph_version": health.get("graph_version"),
            },
            "counts": graph_counts,
            "supplemental_graph_used": False,
        },
        "qa_index": {
            "path": str(qa_index.relative_to(ROOT)),
            "sha256": sha256(qa_index),
            "corpus_version": config.qa_corpus.corpus_version,
        },
        "retrieval_modes": [
            "vector_only",
            "graph_only",
            "vector_graph",
            "vector_graph_conditional_fts",
            "vector_graph_conditional_fts_category_bonus",
        ],
        "conditional_fts": {
            "trigger": (
                "ordinary Step 11 context is nonempty and has no strong direct evidence"
            ),
            "query_variants": [
                "original_query",
                "reformulated_query",
                "medical_phrases",
            ],
            "per_variant_candidate_limit": 20,
            "maximum_new_candidates": 12,
            "exact_normalized_question_excluded": True,
            "human_labels_read": False,
        },
        "category_bonus": {
            "value": 0.05,
            "applies_to": "new conditional-FTS candidates only",
            "category_source": "weighted ordinary Step 11 selected context",
            "eligibility_rule": (
                "May be selected only if it strictly improves the cohort's "
                "primary independent retrieval metric over conditional FTS."
            ),
        },
        "selection_rules": {
            "ahd_reference_100": [
                "confirmed direct Recall@5 among queries with a label-2 candidate",
                "confirmed direct Recall@10",
                "confirmed direct MRR",
                "confirmed useful Hit@5",
                "strong direct Step 11 contexts",
                "non-empty Step 11 contexts",
                "lower mean latency",
            ],
            "entity_ground_truth_100": [
                "entity Recall@5",
                "entity nDCG@10",
                "entity MRR",
                "strong direct Step 11 contexts",
                "non-empty Step 11 contexts",
                "lower mean latency",
            ],
        },
        "generation_policy": {
            "one_selected_retrieval_configuration_per_cohort": True,
            "reuse_cached_step08_where_fingerprint_valid": True,
            "rerun_steps_9_to_17": True,
            "semantic_claim_adjudication": False,
            "e5_claim_calibrator": False,
            "forced_extractive_fallback": False,
            "deterministic_verification_only": True,
        },
        "known_answer_exact_qa_run": {
            "role": "upper_bound_diagnostic_only",
            "rerun": False,
            "eligible_for_selection": False,
        },
        "runtime_files_sha256": {
            relative: sha256(ROOT / relative) for relative in RUNTIME_FILES
        },
        "disabled_calibrator": {
            "path": str(calibrator.relative_to(ROOT)) if calibrator.exists() else "",
            "sha256": sha256(calibrator) if calibrator.exists() else "",
            "enabled": False,
        },
        "runtime": {
            "python": sys.version,
            "packages": {
                name: package_version(name)
                for name in (
                    "neo4j",
                    "sentence-transformers",
                    "torch",
                    "numpy",
                    "bert-score",
                )
            },
            "hf_hub_offline": True,
        },
        "git": {
            "commit": git_value("rev-parse", "HEAD"),
            "status_short": git_value("status", "--short").splitlines(),
        },
        "secrets": "No API key or database password is stored in this manifest.",
        "no_post_result_tuning": True,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "status": "frozen",
                "evaluation_id": payload["evaluation_id"],
                "cohorts": {
                    name: cohort["gold"]["record_count"]
                    for name, cohort in cohort_payload.items()
                },
                "graph_version": config.graph_version,
                "claim_adjudication": False,
                "e5_calibrator": False,
                "supplemental_graph": False,
                "output": str(output),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
