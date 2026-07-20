from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
ENV_FILE = ROOT_DIR / ".env"


def _load_dotenv(path: Path = ENV_FILE) -> None:
    """Load simple KEY=VALUE pairs without printing secret values."""
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default)


def _env_int(name: str, default: int) -> int:
    value = os.environ.get(name)
    if value is None or value == "":
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _env_float(name: str, default: float) -> float:
    value = os.environ.get(name)
    if value is None or value == "":
        return default
    try:
        return float(value)
    except ValueError:
        return default


def _env_bool(name: str, default: bool) -> bool:
    value = os.environ.get(name)
    if value is None or value == "":
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_project_path(name: str, default: Path) -> str:
    path = Path(_env(name, str(default))).expanduser()
    if not path.is_absolute():
        path = ROOT_DIR / path
    return str(path.resolve())


@dataclass(frozen=True)
class Neo4jConfig:
    uri: str = "bolt://localhost:7687"
    username: str = "neo4j"
    password: str = ""
    database: str = "neo4j"


@dataclass(frozen=True)
class EmbeddingConfig:
    model_name: str = "intfloat/multilingual-e5-base"
    dimension: int = 768
    entity_vector_index_name: str = "medical_entity_vector_index"
    evidence_vector_index_name: str = "evidence_mention_vector_index"
    qa_vector_index_name: str = "qa_record_vector_index"


@dataclass(frozen=True)
class QACorpusConfig:
    """External AHD QA retrieval corpus used beside the frozen graph."""

    enabled: bool = True
    index_path: str = str(ROOT_DIR / "data" / "retrieval" / "ahd_qa_train_v1.sqlite")
    corpus_version: str = "ahd_qa_train_v1"
    lexical_candidate_k: int = 80
    semantic_top_k: int = 8
    semantic_rerank_enabled: bool = False


@dataclass(frozen=True)
class RetrievalConfig:
    entity_top_k: int = 10
    evidence_top_k: int = 10
    qa_top_k: int = 5
    relation_top_k: int = 30
    context_top_k: int = 12
    context_max_items: int = 6
    context_min_score: float = 0.52
    context_semantic_min_score: float = 0.84
    context_relative_margin: float = 0.12
    max_hops: int = 1
    semantic_seed_threshold: float = 0.72
    semantic_weight: float = 0.45
    graph_weight: float = 0.35
    evidence_weight: float = 0.20


@dataclass(frozen=True)
class QueryAnalysisConfig:
    provider: str = "groq"
    model: str = "openai/gpt-oss-20b"
    reasoning_effort: str = "low"
    temperature: float = 0.0
    prompt_version: str = "query_analysis_v1"
    groq_api_key: str = ""


@dataclass(frozen=True)
class AnswerGenerationConfig:
    provider: str = "groq"
    model: str = "openai/gpt-oss-20b"
    reasoning_effort: str = "low"
    temperature: float = 0.0
    prompt_version: str = "grounded_answer_v2"
    max_attempts: int = 3
    retry_base_seconds: float = 2.0
    retry_max_seconds: float = 30.0
    groq_api_key: str = ""


@dataclass(frozen=True)
class AppConfig:
    graph_version: str = "final_v1"
    neo4j: Neo4jConfig = field(default_factory=Neo4jConfig)
    embeddings: EmbeddingConfig = field(default_factory=EmbeddingConfig)
    qa_corpus: QACorpusConfig = field(default_factory=QACorpusConfig)
    retrieval: RetrievalConfig = field(default_factory=RetrievalConfig)
    query_analysis: QueryAnalysisConfig = field(default_factory=QueryAnalysisConfig)
    answer_generation: AnswerGenerationConfig = field(default_factory=AnswerGenerationConfig)


def load_config() -> AppConfig:
    """Build the runtime configuration from .env and process environment."""
    _load_dotenv()

    graph_version = _env("GRAPH_VERSION") or _env("AHD_GRAPH_VERSION", "final_v1")

    return AppConfig(
        graph_version=graph_version,
        neo4j=Neo4jConfig(
            uri=_env("NEO4J_URI", "bolt://localhost:7687"),
            username=_env("NEO4J_USERNAME", "neo4j"),
            password=_env("NEO4J_PASSWORD", ""),
            database=_env("NEO4J_DATABASE", "neo4j"),
        ),
        embeddings=EmbeddingConfig(
            model_name=_env(
                "AHD_EMBEDDING_MODEL",
                "intfloat/multilingual-e5-base",
            ),
            dimension=_env_int("AHD_EMBEDDING_DIMENSION", 768),
            entity_vector_index_name=_env(
                "AHD_ENTITY_VECTOR_INDEX",
                "medical_entity_vector_index",
            ),
            evidence_vector_index_name=_env(
                "AHD_EVIDENCE_VECTOR_INDEX",
                "evidence_mention_vector_index",
            ),
            qa_vector_index_name=_env(
                "AHD_QA_VECTOR_INDEX",
                "qa_record_vector_index",
            ),
        ),
        qa_corpus=QACorpusConfig(
            enabled=_env_bool("AHD_QA_CORPUS_ENABLED", True),
            index_path=_env_project_path(
                "AHD_QA_CORPUS_INDEX",
                ROOT_DIR / "data" / "retrieval" / "ahd_qa_train_v1.sqlite",
            ),
            corpus_version=_env("AHD_QA_CORPUS_VERSION", "ahd_qa_train_v1"),
            lexical_candidate_k=_env_int("AHD_QA_LEXICAL_CANDIDATE_K", 80),
            semantic_top_k=_env_int("AHD_QA_SEMANTIC_TOP_K", 8),
            semantic_rerank_enabled=_env_bool("AHD_QA_SEMANTIC_RERANK", False),
        ),
        retrieval=RetrievalConfig(
            entity_top_k=_env_int("AHD_ENTITY_TOP_K", 10),
            evidence_top_k=_env_int("AHD_EVIDENCE_TOP_K", 10),
            qa_top_k=_env_int("AHD_QA_TOP_K", 5),
            relation_top_k=_env_int("AHD_RELATION_TOP_K", 30),
            context_top_k=_env_int("AHD_CONTEXT_TOP_K", 12),
            context_max_items=_env_int("AHD_CONTEXT_MAX_ITEMS", 6),
            context_min_score=_env_float("AHD_CONTEXT_MIN_SCORE", 0.52),
            context_semantic_min_score=_env_float(
                "AHD_CONTEXT_SEMANTIC_MIN_SCORE",
                0.84,
            ),
            context_relative_margin=_env_float("AHD_CONTEXT_RELATIVE_MARGIN", 0.12),
            max_hops=_env_int("AHD_MAX_HOPS", 1),
            semantic_seed_threshold=_env_float("AHD_SEMANTIC_SEED_THRESHOLD", 0.72),
            semantic_weight=_env_float("AHD_SEMANTIC_WEIGHT", 0.45),
            graph_weight=_env_float("AHD_GRAPH_WEIGHT", 0.35),
            evidence_weight=_env_float("AHD_EVIDENCE_WEIGHT", 0.20),
        ),
        query_analysis=QueryAnalysisConfig(
            provider=_env("QUERY_ANALYSIS_PROVIDER", "groq"),
            model=_env("QUERY_ANALYSIS_MODEL", "openai/gpt-oss-20b"),
            reasoning_effort=_env("QUERY_ANALYSIS_REASONING_EFFORT", "low"),
            temperature=_env_float("QUERY_ANALYSIS_TEMPERATURE", 0.0),
            prompt_version=_env("QUERY_ANALYSIS_PROMPT_VERSION", "query_analysis_v1"),
            groq_api_key=_env("GROQ_API_KEY", ""),
        ),
        answer_generation=AnswerGenerationConfig(
            provider=_env("ANSWER_GENERATION_PROVIDER", "groq"),
            model=_env("ANSWER_GENERATION_MODEL", "openai/gpt-oss-20b"),
            reasoning_effort=_env("ANSWER_GENERATION_REASONING_EFFORT", "low"),
            temperature=_env_float("ANSWER_GENERATION_TEMPERATURE", 0.0),
            prompt_version=_env("ANSWER_GENERATION_PROMPT_VERSION", "grounded_answer_v2"),
            max_attempts=_env_int("ANSWER_GENERATION_MAX_ATTEMPTS", 3),
            retry_base_seconds=_env_float("ANSWER_GENERATION_RETRY_BASE_SECONDS", 2.0),
            retry_max_seconds=_env_float("ANSWER_GENERATION_RETRY_MAX_SECONDS", 30.0),
            groq_api_key=_env("GROQ_API_KEY", ""),
        ),
    )


def load_final_config() -> AppConfig:
    """Load the frozen final_v1 graph and its vector-index configuration."""
    _load_dotenv()
    base = load_config()
    return AppConfig(
        graph_version=_env("FINAL_GRAPH_VERSION", "final_v1"),
        neo4j=Neo4jConfig(
            uri=_env("FINAL_NEO4J_URI", "bolt://localhost:7688"),
            username=_env("FINAL_NEO4J_USERNAME", base.neo4j.username),
            password=_env("FINAL_NEO4J_PASSWORD", base.neo4j.password),
            database=_env("FINAL_NEO4J_DATABASE", "neo4j"),
        ),
        embeddings=EmbeddingConfig(
            model_name=_env("FINAL_EMBEDDING_MODEL", "intfloat/multilingual-e5-base"),
            dimension=_env_int("FINAL_EMBEDDING_DIMENSION", 768),
            entity_vector_index_name=_env("FINAL_ENTITY_VECTOR_INDEX", "final_medical_entity_vector_index"),
            evidence_vector_index_name=_env("FINAL_EVIDENCE_VECTOR_INDEX", "final_evidence_mention_vector_index"),
            qa_vector_index_name=_env("FINAL_QA_VECTOR_INDEX", "final_qa_record_vector_index"),
        ),
        qa_corpus=base.qa_corpus,
        retrieval=base.retrieval,
        query_analysis=base.query_analysis,
        answer_generation=base.answer_generation,
    )
