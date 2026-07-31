from __future__ import annotations

"""Opt-in cross-encoder reranking for empty or weak Step 11 contexts.

The normal retrieval path is unchanged. This module is called only after the
ordinary Step 9-11 pass has failed to produce a strong direct passage. It uses
held-out-safe QA candidates, preserves every source identifier, and returns the
rescored pool to the existing deterministic Step 10-11 filters.
"""

import math
from dataclasses import replace
from pathlib import Path
from time import perf_counter
from typing import Any, Protocol, Sequence

from src.config import AppConfig
from src.models import (
    EvidenceContextBundle,
    HybridRetrievalBundle,
    RetrievedEvidence,
    VectorSearchResult,
)
from src.step09_hybrid_retrieval import (
    collect_evidence,
    medical_identity_tokens,
)
from src.step09a_qa_corpus import search_qa_corpus


class CrossEncoderLike(Protocol):
    def predict(
        self,
        sentences: Sequence[Sequence[str]],
        *,
        batch_size: int,
        show_progress_bar: bool,
    ) -> Any:
        ...


class ConditionalCrossEncoderRescue:
    """Stateful wrapper that loads the local model at most once."""

    def __init__(
        self,
        config: AppConfig,
        *,
        raise_on_unavailable: bool = False,
    ) -> None:
        self.config = config
        self.raise_on_unavailable = raise_on_unavailable
        self.model: CrossEncoderLike | None = None
        self.calls = 0
        self.triggered = 0
        self.total_latency_ms = 0.0

    def apply(
        self,
        bundle: HybridRetrievalBundle,
        context: EvidenceContextBundle,
    ) -> tuple[HybridRetrievalBundle, dict[str, Any]]:
        rescued, audit, self.model = (
            apply_conditional_cross_encoder_rescue(
                bundle,
                context,
                self.config,
                model=self.model,
                raise_on_unavailable=self.raise_on_unavailable,
            )
        )
        self.calls += 1
        if audit["status"] == "ok":
            self.triggered += 1
        self.total_latency_ms += float(audit["latency_ms"])
        return rescued, audit


def _safe_float(value: Any) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _safe_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes"}


def has_strong_direct_context(
    context: EvidenceContextBundle,
) -> bool:
    """Return true when Step 11 already contains a strong answer passage."""
    for row in context.evidence_items:
        if (
            _safe_bool(row.get("anatomy_mismatch"))
            or _safe_bool(row.get("unrelated_condition_mismatch"))
            or _safe_bool(row.get("type_conflict"))
        ):
            continue
        direct_anchor = _safe_bool(row.get("direct_question_anchor"))
        if direct_anchor:
            return True
        if (
            _safe_float(row.get("answer_relevance")) >= 0.75
            and _safe_float(row.get("intent_support")) >= 0.50
            and _safe_float(row.get("entity_identity")) >= 0.50
        ):
            return True
    return False


def rescue_eligible(
    bundle: HybridRetrievalBundle,
    context: EvidenceContextBundle,
    config: AppConfig,
) -> tuple[bool, str]:
    """Gate the expensive reranker to identifiable weak medical queries."""
    rescue = config.qa_corpus
    if not rescue.cross_encoder_rescue_enabled:
        return False, "disabled"
    if bundle.plan.query_class in {"non_medical", "unclear"}:
        return False, "non_medical_or_unclear"
    if not bundle.plan.use_vector_search:
        return False, "vector_retrieval_disabled"
    if not (
        bundle.plan.primary_entity_ids
        or bundle.plan.unresolved_phrases
        or bundle.query_medical_phrases
        or medical_identity_tokens(bundle.reformulated_query)
    ):
        return False, "no_medical_anchor"
    if has_strong_direct_context(context):
        return False, "strong_context_already_available"
    return True, "empty_context" if not context.evidence_items else "weak_context"


def resolve_local_checkpoint(model_name: str) -> Path:
    """Resolve a local checkpoint without making a network request."""
    direct = Path(model_name)
    if direct.exists():
        return direct.resolve()
    cache_root = (
        Path.home()
        / ".cache"
        / "huggingface"
        / "hub"
        / f"models--{model_name.replace('/', '--')}"
        / "snapshots"
    )
    snapshots = sorted(
        (item for item in cache_root.glob("*") if item.is_dir()),
        key=lambda item: item.stat().st_mtime,
        reverse=True,
    )
    if not snapshots:
        raise FileNotFoundError(
            f"Cross-encoder checkpoint is not cached locally: {model_name}"
        )
    return snapshots[0].resolve()


def load_cross_encoder(config: AppConfig) -> CrossEncoderLike:
    """Load the configured checkpoint in strict local-only CPU mode."""
    from sentence_transformers import CrossEncoder

    checkpoint = resolve_local_checkpoint(
        config.qa_corpus.cross_encoder_model
    )
    return CrossEncoder(
        str(checkpoint),
        device="cpu",
        local_files_only=True,
        max_length=512,
    )


def _deduplicate_vectors(
    rows: list[VectorSearchResult],
) -> list[VectorSearchResult]:
    best: dict[tuple[str, str], VectorSearchResult] = {}
    for row in rows:
        key = (row.document_type, row.result_id)
        current = best.get(key)
        if current is None or row.score > current.score:
            best[key] = row
    return sorted(best.values(), key=lambda row: row.score, reverse=True)


def build_rescue_candidates(
    bundle: HybridRetrievalBundle,
    config: AppConfig,
) -> tuple[list[VectorSearchResult], list[RetrievedEvidence]]:
    """Combine ordinary candidates with a larger lexical QA shortlist."""
    candidate_k = max(1, config.qa_corpus.cross_encoder_candidate_k)
    lexical_vectors = search_qa_corpus(
        bundle.query,
        bundle.reformulated_query,
        [],
        None,
        config,
        top_k=candidate_k,
        semantic_rerank=False,
        candidate_k=max(
            candidate_k,
            config.qa_corpus.lexical_candidate_k,
        ),
    )
    vectors = _deduplicate_vectors(
        [*bundle.vector_results, *lexical_vectors]
    )
    evidence = collect_evidence(
        bundle.relations,
        vectors,
        candidate_k,
    )
    return vectors, evidence


def _passage(item: RetrievedEvidence) -> str:
    answer = item.answer.strip() or item.text.strip()
    question = item.question.strip()
    if question and answer:
        return f"السؤال: {question}\nالإجابة: {answer}"
    return answer or question


def _normalized_score(value: Any) -> float:
    score = _safe_float(value)
    if 0.0 <= score <= 1.0:
        return score
    # Some cross-encoders return logits rather than probabilities.
    return 1.0 / (1.0 + math.exp(-max(-30.0, min(30.0, score))))


def rerank_candidates(
    bundle: HybridRetrievalBundle,
    candidates: list[RetrievedEvidence],
    model: CrossEncoderLike,
    config: AppConfig,
) -> list[RetrievedEvidence]:
    """Score query-passage pairs while preserving source provenance."""
    usable = [item for item in candidates if _passage(item)]
    if not usable:
        return []
    pairs = [
        [bundle.reformulated_query, _passage(item)]
        for item in usable
    ]
    raw_scores = model.predict(
        pairs,
        batch_size=max(1, config.qa_corpus.cross_encoder_batch_size),
        show_progress_bar=False,
    )
    weight = max(
        0.0,
        min(1.0, config.qa_corpus.cross_encoder_weight),
    )
    rescored: list[RetrievedEvidence] = []
    for item, raw_score in zip(usable, raw_scores, strict=True):
        cross_score = _normalized_score(raw_score)
        blended_score = (
            (1.0 - weight) * max(0.0, min(1.0, item.score))
            + weight * cross_score
        )
        metadata = {
            **item.metadata,
            "cross_encoder_rescue": True,
            "cross_encoder_model": config.qa_corpus.cross_encoder_model,
            "cross_encoder_score": round(cross_score, 6),
            "pre_cross_encoder_score": round(item.score, 6),
            "cross_encoder_blended_score": round(blended_score, 6),
        }
        rescored.append(
            replace(
                item,
                # Step 10 performs the configured blend after applying its
                # anatomy, intent, and concept safety features.
                score=round(item.score, 6),
                metadata=metadata,
            )
        )
    rescored.sort(
        key=lambda item: (
            _safe_float(item.metadata.get("cross_encoder_score")),
            _safe_float(item.metadata.get("cross_encoder_blended_score")),
        ),
        reverse=True,
    )
    return rescored


def apply_conditional_cross_encoder_rescue(
    bundle: HybridRetrievalBundle,
    context: EvidenceContextBundle,
    config: AppConfig,
    *,
    model: CrossEncoderLike | None = None,
    raise_on_unavailable: bool = False,
) -> tuple[HybridRetrievalBundle, dict[str, Any], CrossEncoderLike | None]:
    """Run one conditional rescue pass or return the original bundle."""
    eligible, trigger = rescue_eligible(bundle, context, config)
    audit: dict[str, Any] = {
        "enabled": config.qa_corpus.cross_encoder_rescue_enabled,
        "eligible": eligible,
        "trigger": trigger,
        "status": "not_run",
        "model": config.qa_corpus.cross_encoder_model,
        "candidate_count": 0,
        "rescored_count": 0,
        "latency_ms": 0.0,
        "error": "",
    }
    if not eligible:
        return bundle, audit, model

    started = perf_counter()
    try:
        vectors, candidates = build_rescue_candidates(bundle, config)
        audit["candidate_count"] = len(candidates)
        if model is None:
            model = load_cross_encoder(config)
        rescored = rerank_candidates(
            bundle,
            candidates,
            model,
            config,
        )
    except (FileNotFoundError, OSError, RuntimeError, ValueError) as exc:
        audit["status"] = "unavailable"
        audit["error"] = str(exc)
        audit["latency_ms"] = round(
            (perf_counter() - started) * 1000.0,
            3,
        )
        if raise_on_unavailable:
            raise
        warning = (
            "Conditional cross-encoder rescue was unavailable; ordinary "
            f"retrieval was preserved: {exc}"
        )
        return (
            replace(
                bundle,
                warnings=list(dict.fromkeys([*bundle.warnings, warning])),
            ),
            audit,
            model,
        )

    audit["status"] = "ok"
    audit["rescored_count"] = len(rescored)
    audit["latency_ms"] = round(
        (perf_counter() - started) * 1000.0,
        3,
    )
    rescued = replace(
        bundle,
        vector_results=vectors,
        evidence=rescored,
        warnings=list(
            dict.fromkeys(
                [
                    *bundle.warnings,
                    "Conditional cross-encoder rescue reranked a held-out-safe "
                    f"candidate pool after {trigger}.",
                ]
            )
        ),
    )
    return rescued, audit, model
