from __future__ import annotations

import csv
import hashlib
import importlib.metadata
import json
import platform
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable, Sequence


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GOLD_FILE = ROOT / "data" / "evaluation" / "retrieval_gold_annotations_100.csv"
RETRIEVAL_OUTPUT_ROOT = ROOT / "outputs" / "evaluation" / "retrieval"
GENERATION_OUTPUT_ROOT = ROOT / "outputs" / "evaluation" / "generation"
CLAIM_AUDIT_OUTPUT_ROOT = ROOT / "outputs" / "evaluation" / "claim_audit"
EVALUATION_VERSION = "evaluation-v1"

GOLD_COLUMNS = (
    "query_id",
    "query",
    "query_group",
    "reference_answer",
    "gold_entity_ids",
    "gold_evidence_ids",
    "gold_qa_ids",
    "gold_relation_ids",
    "answerable_from_final_graph",
    "annotation_notes",
)

FROZEN_RUNTIME_FILES = (
    "scripts/evaluation_common.py",
    "scripts/run_retrieval_ablation.py",
    "scripts/run_generation_ablation.py",
    "src/config.py",
    "src/models.py",
    "src/neo4j_repository.py",
    "src/step08a_normalize_query.py",
    "src/step08b_analyze_query.py",
    "src/step08c_link_entities.py",
    "src/step08d_plan_retrieval.py",
    "src/step09_hybrid_retrieval.py",
    "src/step10_rerank_subgraph.py",
    "src/step11_build_evidence_context.py",
    "src/step12_generate_grounded_answer.py",
    "src/step13_extract_claims.py",
    "src/step14_verify_claims.py",
    "src/step15_mitigate_hallucinations.py",
    "src/step16_score_reliability.py",
    "src/step17_build_explainable_output.py",
    "src/evaluation_metrics.py",
)


@dataclass(frozen=True)
class GoldQuery:
    query_id: str
    query: str
    query_group: str = ""
    reference_answer: str = ""
    gold_entity_ids: list[str] | None = None
    gold_evidence_ids: list[str] | None = None
    gold_qa_ids: list[str] | None = None
    gold_relation_ids: list[str] | None = None
    answerable_from_final_graph: bool | None = None
    annotation_status: str = ""
    annotator_id: str = ""
    adjudicator_id: str = ""
    annotation_notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def parse_id_list(value: Any) -> list[str]:
    """Parse JSON arrays or human-friendly pipe/semicolon-separated ID lists."""
    text = str(value or "").strip()
    if not text:
        return []
    if text.startswith("["):
        parsed = json.loads(text)
        if not isinstance(parsed, list):
            raise ValueError("Gold ID JSON values must be arrays.")
        values = parsed
    else:
        values = text.replace(";", "|").split("|")
    return list(dict.fromkeys(str(item).strip() for item in values if str(item).strip()))


def parse_optional_bool(value: Any) -> bool | None:
    text = str(value or "").strip().lower()
    if not text:
        return None
    if text in {"1", "true", "yes", "y"}:
        return True
    if text in {"0", "false", "no", "n"}:
        return False
    raise ValueError(f"Invalid answerable_from_final_graph value: {value}")


def load_gold_queries(path: Path, limit: int = 0) -> list[GoldQuery]:
    """Load only human-authored gold rows; no pipeline output is consulted here."""
    if not path.exists():
        raise FileNotFoundError(f"Gold file not found: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = [column for column in GOLD_COLUMNS if column not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"Gold file is missing columns: {', '.join(missing)}")
        rows: list[GoldQuery] = []
        seen_ids: set[str] = set()
        for line_number, row in enumerate(reader, start=2):
            query_id = str(row.get("query_id") or "").strip()
            query = str(row.get("query") or "").strip()
            if not query_id and not query:
                continue
            if not query_id or not query:
                raise ValueError(f"Gold row {line_number} requires query_id and query.")
            if query_id in seen_ids:
                raise ValueError(f"Duplicate query_id in gold file: {query_id}")
            seen_ids.add(query_id)
            rows.append(
                GoldQuery(
                    query_id=query_id,
                    query=query,
                    query_group=str(row.get("query_group") or "").strip(),
                    reference_answer=str(row.get("reference_answer") or "").strip(),
                    gold_entity_ids=parse_id_list(row.get("gold_entity_ids")),
                    gold_evidence_ids=parse_id_list(row.get("gold_evidence_ids")),
                    gold_qa_ids=parse_id_list(row.get("gold_qa_ids")),
                    gold_relation_ids=parse_id_list(row.get("gold_relation_ids")),
                    answerable_from_final_graph=parse_optional_bool(
                        row.get("answerable_from_final_graph")
                    ),
                    annotation_status=str(row.get("annotation_status") or "").strip(),
                    annotator_id=str(row.get("annotator_id") or "").strip(),
                    adjudicator_id=str(row.get("adjudicator_id") or "").strip(),
                    annotation_notes=str(row.get("annotation_notes") or "").strip(),
                )
            )
            if limit > 0 and len(rows) >= limit:
                break
    return rows


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git_value(*args: str) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def package_versions(names: Iterable[str]) -> dict[str, str]:
    versions: dict[str, str] = {}
    for name in names:
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = "not_installed"
    return versions


def make_run_id(prefix: str) -> str:
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    commit = git_value("rev-parse", "--short", "HEAD")
    return f"{prefix}_{timestamp}_{commit if commit != 'unknown' else 'nogit'}"


def create_run_directory(root: Path, run_id: str) -> Path:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", run_id):
        raise ValueError("run_id may contain only letters, numbers, dot, underscore, and hyphen.")
    root.mkdir(parents=True, exist_ok=True)
    destination = root / run_id
    destination.mkdir(parents=False, exist_ok=False)
    return destination


def ensure_run_available(root: Path, run_id: str) -> None:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", run_id):
        raise ValueError("run_id may contain only letters, numbers, dot, underscore, and hyphen.")
    if (root / run_id).exists():
        raise FileExistsError(f"Evaluation run already exists and will not be overwritten: {root / run_id}")


def write_json(path: Path, payload: Any) -> None:
    if path.exists():
        raise FileExistsError(f"Refusing to overwrite evaluation output: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_jsonl(path: Path, records: Sequence[dict[str, Any]]) -> None:
    if path.exists():
        raise FileExistsError(f"Refusing to overwrite evaluation output: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def build_manifest(
    *,
    run_id: str,
    run_type: str,
    modes: Sequence[str],
    gold_path: Path,
    gold_count: int,
    config: Any,
    graph_counts: dict[str, int],
    arguments: dict[str, Any],
) -> dict[str, Any]:
    source_hashes = {
        relative: file_sha256(ROOT / relative)
        for relative in FROZEN_RUNTIME_FILES
        if (ROOT / relative).exists()
    }
    dirty_output = git_value("status", "--porcelain")
    try:
        gold_display_path = gold_path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        gold_display_path = str(gold_path.resolve())
    return {
        "evaluation_version": EVALUATION_VERSION,
        "run_id": run_id,
        "run_type": run_type,
        "created_at_utc": datetime.now(UTC).isoformat(),
        "modes": list(modes),
        "supplemental_graph_used": False,
        "gold": {
            "path": gold_display_path,
            "sha256": file_sha256(gold_path),
            "query_count": gold_count,
            "label_source": "human_confirmed_rows_only; provisional dataset labels are excluded",
        },
        "graph": {
            "graph_version": config.graph_version,
            "counts": graph_counts,
            "read_only": True,
        },
        "models": {
            "query_analysis_provider": config.query_analysis.provider,
            "query_analysis_model": config.query_analysis.model,
            "answer_provider": config.answer_generation.provider,
            "answer_model": config.answer_generation.model,
            "embedding_model": config.embeddings.model_name,
            "embedding_dimension": config.embeddings.dimension,
            "query_prompt_version": config.query_analysis.prompt_version,
            "answer_prompt_version": config.answer_generation.prompt_version,
            "query_reasoning_effort": config.query_analysis.reasoning_effort,
            "answer_reasoning_effort": config.answer_generation.reasoning_effort,
            "query_temperature": config.query_analysis.temperature,
            "answer_temperature": config.answer_generation.temperature,
        },
        "neo4j": {
            "uri": config.neo4j.uri,
            "database": config.neo4j.database,
            "credentials_recorded": False,
        },
        "thresholds": {
            "semantic_seed_threshold": config.retrieval.semantic_seed_threshold,
            "claim_support_threshold": 0.55,
            "claim_weak_threshold": 0.35,
        },
        "top_k": {
            "entity": config.retrieval.entity_top_k,
            "evidence": config.retrieval.evidence_top_k,
            "qa": config.retrieval.qa_top_k,
            "relation": config.retrieval.relation_top_k,
            "context": config.retrieval.context_top_k,
            "max_hops": config.retrieval.max_hops,
        },
        "retrieval_weights": {
            "semantic": config.retrieval.semantic_weight,
            "graph": config.retrieval.graph_weight,
            "evidence": config.retrieval.evidence_weight,
        },
        "vector_indexes": {
            "entity": config.embeddings.entity_vector_index_name,
            "evidence": config.embeddings.evidence_vector_index_name,
            "qa": config.embeddings.qa_vector_index_name,
        },
        "qa_retrieval_corpus": {
            "enabled": config.qa_corpus.enabled,
            "index_path": str(config.qa_corpus.index_path),
            "corpus_version": config.qa_corpus.corpus_version,
            "lexical_candidate_k": config.qa_corpus.lexical_candidate_k,
            "semantic_top_k": config.qa_corpus.semantic_top_k,
            "semantic_rerank_enabled": config.qa_corpus.semantic_rerank_enabled,
        },
        "git": {
            "commit": git_value("rev-parse", "HEAD"),
            "dirty": bool(dirty_output and dirty_output != "unknown"),
        },
        "runtime": {
            "python": sys.version,
            "executable": sys.executable,
            "platform": platform.platform(),
            "packages": package_versions(
                ("neo4j", "numpy", "sentence-transformers", "torch", "bert-score", "ragas")
            ),
            "arguments": arguments,
        },
        "frozen_runtime_sha256": source_hashes,
    }


def unavailable(reason: str) -> dict[str, str]:
    return {"status": "unavailable", "reason": reason}


def macro_average(metric_rows: Sequence[dict[str, Any]], keys: Sequence[str]) -> dict[str, Any]:
    computed = [row for row in metric_rows if row.get("status") == "computed"]
    if not computed:
        return unavailable("No independently annotated gold labels were available for this metric.")
    return {
        "status": "computed",
        "evaluated_query_count": len(computed),
        **{
            key: round(sum(float(row[key]) for row in computed) / len(computed), 6)
            for key in keys
        },
    }


def citation_validity(claims: Sequence[Any], allowed_evidence_ids: Iterable[str]) -> dict[str, Any]:
    allowed = set(allowed_evidence_ids)
    citations = [citation for claim in claims for citation in claim.citations]
    valid = [citation for citation in citations if citation in allowed]
    claim_count = len(claims)
    claims_with_valid_citation = sum(
        any(citation in allowed for citation in claim.citations) for claim in claims
    )
    return {
        "status": "computed",
        "claim_count": claim_count,
        "citation_count": len(citations),
        "valid_citation_count": len(valid),
        "citation_validity": round(len(valid) / len(citations), 6) if citations else 0.0,
        "claims_with_valid_citation_rate": (
            round(claims_with_valid_citation / claim_count, 6) if claim_count else 0.0
        ),
    }
