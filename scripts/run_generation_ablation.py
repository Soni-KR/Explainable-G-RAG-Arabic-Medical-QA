from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.request
from dataclasses import asdict, replace
from pathlib import Path
from time import monotonic, perf_counter, sleep
from typing import Any

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from scripts.evaluation_common import (
    CLAIM_AUDIT_OUTPUT_ROOT,
    DEFAULT_GOLD_FILE,
    GENERATION_OUTPUT_ROOT,
    build_manifest,
    citation_validity,
    create_run_directory,
    ensure_run_available,
    load_gold_queries,
    macro_average,
    make_run_id,
    unavailable,
    write_json,
    write_jsonl,
)
from src.config import AppConfig, load_final_config
from src.evaluation_metrics import bertscore_f1, claim_grounding_metrics, efficiency_metrics
from src.models import (
    AnswerClaim,
    EvidenceContextBundle,
    ExtractedMedicalPhrase,
    GeneratedAnswer,
    HybridRetrievalBundle,
    LinkedMedicalEntity,
    QueryEntityLinkingResult,
    RetrievalPlanResult,
    RerankedSubgraph,
    RetrievedEvidence,
    RetrievedMedicalRelation,
    UnifiedQueryAnalysisResult,
)
from src.neo4j_repository import Neo4jRepository
from src.step06_build_embedding_indexes import load_model
from src.step08b_analyze_query import analyze_and_link_query
from src.step08d_plan_retrieval import build_retrieval_plan
from src.step09_hybrid_retrieval import (
    add_semantic_qa_fallback,
    retrieve_hybrid,
    select_relevance_phrases,
    semantic_qa_fallback_eligible,
)
from src.step09e_conditional_cross_encoder_rescue import (
    ConditionalCrossEncoderRescue,
)
from src.step10_rerank_subgraph import rerank_subgraph
from src.step11_build_evidence_context import build_evidence_context
from src.step12_generate_grounded_answer import (
    GROQ_CHAT_COMPLETIONS_URL,
    generate_grounded_answer,
    parse_json_object,
)
from src.step13_extract_claims import extract_claims
from src.step14_semantic_adjudication import SemanticClaimAdjudicator
from src.step14_verify_claims import verify_claims
from src.step14_verify_claims_v5 import (
    VERIFIER_V5_PROFILE,
    verify_claims_v5,
)
from src.step15_mitigate_hallucinations import mitigate_hallucinations
from src.step16_score_reliability import score_reliability


MODES = ("llm_only", "rag_before_mitigation", "full_pipeline")
CLAIM_VERIFIER_PROFILES = ("deterministic_v3", VERIFIER_V5_PROFILE)
GENERATION_CACHE_ROOT = GENERATION_OUTPUT_ROOT.parent / "cache"

LLM_ONLY_SCHEMA = {
    "type": "object",
    "properties": {
        "answer_ar": {"type": "string"},
        "claims": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"claim_ar": {"type": "string"}},
                "required": ["claim_ar"],
                "additionalProperties": False,
            },
        },
        "limitations_ar": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["answer_ar", "claims", "limitations_ar"],
    "additionalProperties": False,
}


class RequestPacer:
    """Apply one minimum interval across Step 8 and Step 12 API calls."""

    def __init__(self, interval_seconds: float) -> None:
        self.interval_seconds = max(0.0, interval_seconds)
        self.last_request_at: float | None = None

    def wait(self) -> None:
        if self.last_request_at is not None:
            remaining = self.interval_seconds - (monotonic() - self.last_request_at)
            if remaining > 0:
                sleep(remaining)
        self.last_request_at = monotonic()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
        handle.flush()


def analysis_from_dict(payload: dict[str, Any]) -> UnifiedQueryAnalysisResult:
    values = dict(payload)
    values["medical_phrases"] = [
        ExtractedMedicalPhrase(**item) for item in values.get("medical_phrases", [])
    ]
    return UnifiedQueryAnalysisResult(**values)


def linking_from_dict(payload: dict[str, Any]) -> QueryEntityLinkingResult:
    values = dict(payload)
    values["linked_entities"] = [
        LinkedMedicalEntity(**item) for item in values.get("linked_entities", [])
    ]
    return QueryEntityLinkingResult(**values)


def retrieval_plan_from_dict(payload: dict[str, Any]) -> RetrievalPlanResult:
    return RetrievalPlanResult(**dict(payload))


def generated_from_dict(payload: dict[str, Any]) -> GeneratedAnswer:
    values = dict(payload)
    values["claims"] = [AnswerClaim(**item) for item in values.get("claims", [])]
    return GeneratedAnswer(**values)


def run_claim_verification(
    claims: list[AnswerClaim],
    context: EvidenceContextBundle,
    config: AppConfig,
    semantic_adjudicator: SemanticClaimAdjudicator | None = None,
) -> tuple[list[Any], dict[str, Any]]:
    """Select the frozen verifier or the explicit v5 development profile."""
    profile = config.claim_adjudication.verifier_profile
    if profile == "deterministic_v3":
        return verify_claims(claims, context), {
            "profile": profile,
            "semantic_adjudication": {"enabled": False},
        }
    if profile != VERIFIER_V5_PROFILE:
        raise ValueError(f"Unsupported claim verifier profile: {profile}")
    if config.claim_adjudication.enabled and semantic_adjudicator is None:
        raise RuntimeError(
            "Semantic claim adjudication is enabled but no stateful "
            "adjudicator was provided."
        )
    return verify_claims_v5(
        claims,
        context,
        semantic_adjudicator=semantic_adjudicator,
    )


def claim_verifier_manifest(
    config: AppConfig,
    semantic_adjudicator: SemanticClaimAdjudicator | None,
) -> dict[str, Any]:
    return {
        "profile": config.claim_adjudication.verifier_profile,
        "semantic_adjudication_enabled": (
            config.claim_adjudication.enabled
        ),
        "semantic_model": (
            config.claim_adjudication.model
            if config.claim_adjudication.enabled
            else ""
        ),
        "semantic_prompt_version": (
            config.claim_adjudication.prompt_version
            if config.claim_adjudication.enabled
            else ""
        ),
        "semantic_api_calls": (
            semantic_adjudicator.api_calls
            if semantic_adjudicator is not None
            else 0
        ),
        "semantic_cache_hits": (
            semantic_adjudicator.cache_hits
            if semantic_adjudicator is not None
            else 0
        ),
    }


def cross_encoder_rescue_manifest(
    config: AppConfig,
    runtime: ConditionalCrossEncoderRescue | None,
) -> dict[str, Any]:
    return {
        "enabled": config.qa_corpus.cross_encoder_rescue_enabled,
        "model": (
            config.qa_corpus.cross_encoder_model
            if config.qa_corpus.cross_encoder_rescue_enabled
            else ""
        ),
        "candidate_k": config.qa_corpus.cross_encoder_candidate_k,
        "weight": config.qa_corpus.cross_encoder_weight,
        "minimum_score": config.qa_corpus.cross_encoder_min_score,
        "runtime_checks": runtime.calls if runtime is not None else 0,
        "triggered_queries": (
            runtime.triggered if runtime is not None else 0
        ),
        "total_latency_ms": (
            round(runtime.total_latency_ms, 3)
            if runtime is not None
            else 0.0
        ),
        "semantic_e5_fallback_disabled_for_ablation": bool(
            config.qa_corpus.cross_encoder_rescue_enabled
        ),
    }


def analysis_succeeded(payload: dict[str, Any]) -> bool:
    warnings = [str(item) for item in payload.get("warnings", [])]
    return not any("Unified LLM query analysis failed" in item for item in warnings)


def context_fingerprint(context: EvidenceContextBundle, config: AppConfig) -> str:
    payload = {
        "context": asdict(context),
        "model": config.answer_generation.model,
        "prompt_version": config.answer_generation.prompt_version,
        "graph_version": config.graph_version,
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def evaluation_pipeline_fingerprint(
    retrieval_file: Path,
    config: AppConfig,
    rerank_frozen_retrieval: bool,
) -> str:
    """Bind resumable records to the exact evidence-selection implementation."""
    root = Path(__file__).resolve().parents[1]
    runtime_files = (
        root / "src" / "step10_rerank_subgraph.py",
        root / "src" / "step11_build_evidence_context.py",
        root / "src" / "step09e_conditional_cross_encoder_rescue.py",
        root / "src" / "step12_generate_grounded_answer.py",
        root / "src" / "step13_extract_claims.py",
        root / "src" / "step14_verify_claims.py",
        root / "src" / "step14_verify_claims_v5.py",
        root / "src" / "step14_semantic_adjudication.py",
        root / "src" / "step15_mitigate_hallucinations.py",
        root / "src" / "step16_score_reliability.py",
    )
    payload = {
        "retrieval_file_sha256": hashlib.sha256(retrieval_file.read_bytes()).hexdigest(),
        "runtime_sha256": {
            str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in runtime_files
        },
        "rerank_frozen_retrieval": rerank_frozen_retrieval,
        "graph_version": config.graph_version,
        "embedding_model": config.embeddings.model_name,
        "retrieval": asdict(config.retrieval),
        "qa_corpus": asdict(config.qa_corpus),
        "answer_model": config.answer_generation.model,
        "answer_prompt_version": config.answer_generation.prompt_version,
        "answer_temperature": config.answer_generation.temperature,
        "answer_reasoning_effort": config.answer_generation.reasoning_effort,
        "claim_verifier_profile": (
            config.claim_adjudication.verifier_profile
        ),
        "semantic_claim_adjudication": {
            "enabled": config.claim_adjudication.enabled,
            "model": config.claim_adjudication.model,
            "prompt_version": config.claim_adjudication.prompt_version,
            "temperature": config.claim_adjudication.temperature,
            "reasoning_effort": (
                config.claim_adjudication.reasoning_effort
            ),
        },
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def rate_limit_delay(base_seconds: float, attempt: int) -> float:
    return min(300.0, max(1.0, base_seconds) * (2 ** max(0, attempt - 1)))


def frozen_subgraph(
    record: dict[str, Any],
    primary_intent: str,
    *,
    rerank: bool = False,
    config: AppConfig | None = None,
) -> RerankedSubgraph:
    analysis_payload = dict(record.get("query_analysis") or {})
    query_medical_phrases = select_relevance_phrases(
        list(analysis_payload.get("medical_phrases") or []),
        primary_intent,
    )
    saved = RerankedSubgraph(
        query=str(record.get("query") or ""),
        primary_intent=primary_intent,
        query_medical_phrases=query_medical_phrases,
        relations=[RetrievedMedicalRelation(**item) for item in record.get("relations", [])],
        evidence=[RetrievedEvidence(**item) for item in record.get("evidence", [])],
        warnings=[str(item) for item in record.get("warnings", [])],
    )
    if not rerank:
        return saved

    plan_payload = dict(record.get("retrieval_plan") or {})
    if not plan_payload:
        raise ValueError("Frozen retrieval record is missing its retrieval plan.")
    plan = retrieval_plan_from_dict(plan_payload)
    bundle = HybridRetrievalBundle(
        query=saved.query,
        normalized_query=str(record.get("query_analysis", {}).get("normalized_query") or ""),
        reformulated_query=plan.reformulated_query,
        plan=plan,
        query_medical_phrases=query_medical_phrases,
        relations=saved.relations,
        evidence=saved.evidence,
        warnings=saved.warnings,
    )
    return rerank_subgraph(bundle, config=config)


def generate_llm_only(query: str, config: AppConfig) -> GeneratedAnswer:
    """Evaluation baseline: answer without graph/vector evidence or citations."""
    answer_config = config.answer_generation
    if answer_config.provider != "groq" or not answer_config.groq_api_key:
        return GeneratedAnswer(
            query=query,
            answer="تعذر تشغيل خط الأساس دون إعداد مزود النموذج.",
            model=answer_config.model,
            prompt_version="evaluation_llm_only_v1",
            generation_status="fallback",
            fallback_reason="LLM-only baseline was unavailable.",
            warnings=["LLM-only baseline was unavailable."],
        )
    payload = {
        "query": query,
        "task": "Answer the Arabic medical query using the model's internal knowledge only.",
        "rules": [
            "Answer in Arabic.",
            "Do not claim that graph retrieval or external evidence was used.",
            "Return atomic factual claims separately.",
            "State uncertainty and recommend professional care when appropriate.",
        ],
    }
    body: dict[str, Any] = {
        "model": answer_config.model,
        "messages": [
            {
                "role": "system",
                "content": "You are the ungrounded LLM-only baseline for an Arabic medical evaluation. Return strict JSON only.",
            },
            {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
        ],
        "temperature": answer_config.temperature,
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "evaluation_llm_only_answer",
                "strict": True,
                "schema": LLM_ONLY_SCHEMA,
            },
        },
    }
    if answer_config.reasoning_effort:
        body["reasoning_effort"] = answer_config.reasoning_effort
    request = urllib.request.Request(
        GROQ_CHAT_COMPLETIONS_URL,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {answer_config.groq_api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "AHD-GraphRAG-Evaluation/1.0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            response_payload = json.loads(response.read().decode("utf-8"))
        parsed = parse_json_object(response_payload["choices"][0]["message"]["content"])
        if not isinstance(parsed.get("answer_ar"), str) or not isinstance(parsed.get("claims"), list):
            raise ValueError("Malformed LLM-only structured response.")
        claims = [
            AnswerClaim(claim=str(item.get("claim_ar") or "").strip())
            for item in parsed["claims"]
            if isinstance(item, dict) and str(item.get("claim_ar") or "").strip()
        ]
        return GeneratedAnswer(
            query=query,
            answer=parsed["answer_ar"].strip(),
            claims=claims,
            limitations=[str(item).strip() for item in parsed.get("limitations_ar", []) if str(item).strip()],
            model=answer_config.model,
            prompt_version="evaluation_llm_only_v1",
            generation_status="generated",
            attempt_count=1,
        )
    except Exception as exc:
        return GeneratedAnswer(
            query=query,
            answer="تعذر توليد إجابة خط الأساس.",
            model=answer_config.model,
            prompt_version="evaluation_llm_only_v1",
            generation_status="fallback",
            fallback_reason=f"LLM-only generation failed: {type(exc).__name__}",
            attempt_count=1,
            warnings=[f"LLM-only generation failed: {type(exc).__name__}"],
        )


def timed_rag_artifacts(
    query: str,
    repository: Neo4jRepository | None,
    config: AppConfig,
    model: Any,
    semantic_adjudicator: SemanticClaimAdjudicator | None = None,
    cross_encoder_rescue: ConditionalCrossEncoderRescue | None = None,
) -> dict[str, Any]:
    timings: dict[str, float] = {}
    pipeline_started = perf_counter()

    started = perf_counter()
    analysis, linking = analyze_and_link_query(query, repository=repository, config=config)
    timings["step08_query_understanding"] = round((perf_counter() - started) * 1000.0, 3)

    started = perf_counter()
    plan = build_retrieval_plan(analysis, linking, config=config)
    timings["step08_retrieval_planning"] = round((perf_counter() - started) * 1000.0, 3)

    started = perf_counter()
    retrieval = retrieve_hybrid(
        analysis, linking, plan, repository=repository, config=config, model=model
    )
    timings["step09_hybrid_retrieval"] = round((perf_counter() - started) * 1000.0, 3)

    started = perf_counter()
    subgraph = rerank_subgraph(retrieval, config=config)
    timings["step10_subgraph_reranking"] = round((perf_counter() - started) * 1000.0, 3)

    started = perf_counter()
    context = build_evidence_context(subgraph, analysis.reformulated_query, config=config)
    timings["step11_context_construction"] = round((perf_counter() - started) * 1000.0, 3)

    cross_encoder_audit: dict[str, Any] = {
        "enabled": False,
        "eligible": False,
        "status": "not_run",
    }
    if cross_encoder_rescue is not None:
        started = perf_counter()
        retrieval, cross_encoder_audit = cross_encoder_rescue.apply(
            retrieval,
            context,
        )
        timings["step09_cross_encoder_rescue"] = round(
            (perf_counter() - started) * 1000.0,
            3,
        )
        if cross_encoder_audit.get("status") == "ok":
            started = perf_counter()
            subgraph = rerank_subgraph(retrieval, config=config)
            timings["step10_cross_encoder_reranking"] = round(
                (perf_counter() - started) * 1000.0,
                3,
            )
            started = perf_counter()
            context = build_evidence_context(
                subgraph,
                analysis.reformulated_query,
                config=config,
            )
            timings["step11_cross_encoder_context_construction"] = round(
                (perf_counter() - started) * 1000.0,
                3,
            )

    if semantic_qa_fallback_eligible(
        retrieval,
        context_has_evidence=bool(context.evidence_items),
        config=config,
    ):
        started = perf_counter()
        retrieval = add_semantic_qa_fallback(retrieval, config=config, model=model)
        timings["step09_semantic_qa_fallback"] = round(
            (perf_counter() - started) * 1000.0,
            3,
        )
        started = perf_counter()
        subgraph = rerank_subgraph(retrieval, config=config)
        timings["step10_fallback_reranking"] = round(
            (perf_counter() - started) * 1000.0,
            3,
        )
        started = perf_counter()
        context = build_evidence_context(
            subgraph,
            analysis.reformulated_query,
            config=config,
        )
        timings["step11_fallback_context_construction"] = round(
            (perf_counter() - started) * 1000.0,
            3,
        )

    started = perf_counter()
    generated = generate_grounded_answer(context, config=config)
    timings["step12_answer_generation"] = round((perf_counter() - started) * 1000.0, 3)
    before_mitigation_end_to_end = round((perf_counter() - pipeline_started) * 1000.0, 3)

    started = perf_counter()
    claims = extract_claims(generated)
    timings["step13_claim_extraction"] = round((perf_counter() - started) * 1000.0, 3)

    started = perf_counter()
    verifications, verifier_audit = run_claim_verification(
        claims,
        context,
        config,
        semantic_adjudicator,
    )
    timings["step14_claim_verification"] = round((perf_counter() - started) * 1000.0, 3)

    started = perf_counter()
    mitigated = mitigate_hallucinations(generated, verifications, context=context)
    timings["step15_hallucination_mitigation"] = round((perf_counter() - started) * 1000.0, 3)

    started = perf_counter()
    reliability = score_reliability(mitigated, verifications, context)
    timings["step16_reliability_scoring"] = round((perf_counter() - started) * 1000.0, 3)
    full_end_to_end = round((perf_counter() - pipeline_started) * 1000.0, 3)
    return {
        "analysis": analysis,
        "linking": linking,
        "plan": plan,
        "retrieval": retrieval,
        "subgraph": subgraph,
        "context": context,
        "generated": generated,
        "claims": claims,
        "verifications": verifications,
        "claim_verifier_audit": verifier_audit,
        "cross_encoder_rescue_audit": cross_encoder_audit,
        "mitigated": mitigated,
        "reliability": reliability,
        "timings": timings,
        "before_mitigation_end_to_end": before_mitigation_end_to_end,
        "full_end_to_end": full_end_to_end,
    }


def output_claim_metrics(statuses: list[str]) -> dict[str, Any]:
    if not statuses:
        return unavailable("The output contained no factual claims to score.")
    return {"status": "computed", **claim_grounding_metrics(statuses)}


def build_record(
    *,
    gold: Any,
    mode: str,
    answer: str,
    output_claims: list[AnswerClaim],
    verifications: list[Any],
    context: EvidenceContextBundle,
    timings: dict[str, float],
    raw: dict[str, Any],
    warnings: list[str],
    generation_status: str,
    answerability: str = "",
) -> tuple[dict[str, Any], dict[str, Any]]:
    status_by_claim = {item.claim.claim: item.status for item in verifications}
    output_statuses = [status_by_claim.get(claim.claim, "unsupported") for claim in output_claims]
    generation_succeeded = generation_status == "generated"
    substantive_output = generation_succeeded and answerability not in {
        "insufficient_evidence",
        "generation_unavailable",
    }
    mitigated_payload = dict(raw.get("mitigated") or {})
    metrics = {
        "bertscore": (
            bertscore_f1(answer, gold.reference_answer)
            if substantive_output
            else unavailable("BERTScore is not computed for a fallback or insufficient-evidence answer.")
        ),
        "claim_grounding": (
            output_claim_metrics(output_statuses)
            if generation_succeeded
            else unavailable("Claim grounding is not computed for an API fallback answer.")
        ),
        "pre_mitigation_claim_grounding": (
            output_claim_metrics([item.status for item in verifications])
            if generation_succeeded
            else unavailable("Claim grounding is not computed for an API fallback answer.")
        ),
        "citation_validity": (
            citation_validity(output_claims, context.allowed_evidence_ids)
            if substantive_output and output_claims
            else unavailable("Citation validity requires a substantive answer with factual claims.")
        ),
        "latency": {
            "status": "computed",
            "end_to_end_latency_ms": timings["end_to_end"],
            "per_stage_latency_ms": {
                key: value for key, value in timings.items() if key != "end_to_end"
            },
        },
    }
    record = {
        "evaluation_version": "evaluation-v1",
        "query_id": gold.query_id,
        "query": gold.query,
        "query_group": gold.query_group,
        "mode": mode,
        "generation_status": generation_status,
        "answerability": answerability,
        "query_coverage": float(mitigated_payload.get("query_coverage") or 0.0),
        "missing_query_concepts": list(
            mitigated_payload.get("missing_query_concepts") or []
        ),
        "gold": gold.to_dict(),
        "answer": answer,
        "output_claims": [asdict(item) for item in output_claims],
        "metrics": metrics,
        "timings_ms": timings,
        "raw": raw,
        "warnings": list(dict.fromkeys(warnings)),
    }
    audit = {
        "evaluation_version": "evaluation-v1",
        "query_id": gold.query_id,
        "mode": mode,
        "generation_status": generation_status,
        "answerability": answerability,
        "allowed_evidence_ids": context.allowed_evidence_ids,
        "allowed_qa_ids": context.allowed_qa_ids,
        "verifications": [asdict(item) for item in verifications],
        "citation_validity": metrics["citation_validity"],
    }
    return record, audit


def aggregate_mode(records: list[dict[str, Any]]) -> dict[str, Any]:
    bertscore = macro_average(
        [record["metrics"]["bertscore"] for record in records], ("bertscore_f1",)
    )
    grounding_rows = [
        record["metrics"]["claim_grounding"]
        for record in records
        if record["metrics"]["claim_grounding"].get("status") == "computed"
    ]
    grounding = (
        {
            "status": "computed",
            "evaluated_query_count": len(grounding_rows),
            "claim_support_rate": round(
                sum(row["claim_support_rate"] for row in grounding_rows) / len(grounding_rows), 6
            ),
            "hallucination_rate": round(
                sum(row["hallucination_rate"] for row in grounding_rows) / len(grounding_rows), 6
            ),
        }
        if grounding_rows
        else unavailable("No factual output claims were available to score.")
    )
    citation_rows = [
        record["metrics"]["citation_validity"]
        for record in records
        if record["metrics"]["citation_validity"].get("status") == "computed"
    ]
    citation = (
        {
            "status": "computed",
            "evaluated_query_count": len(citation_rows),
            "citation_validity": round(
                sum(row["citation_validity"] for row in citation_rows) / len(citation_rows), 6
            ),
            "claims_with_valid_citation_rate": round(
                sum(row["claims_with_valid_citation_rate"] for row in citation_rows)
                / len(citation_rows),
                6,
            ),
        }
        if citation_rows
        else unavailable("No successful generations were available for citation scoring.")
    )
    answerability_counts: dict[str, int] = {}
    for record in records:
        state = str(record.get("answerability") or "unknown")
        answerability_counts[state] = answerability_counts.get(state, 0) + 1
    substantive_coverages = [
        float(record.get("query_coverage") or 0.0)
        for record in records
        if record.get("answerability")
        not in {"insufficient_evidence", "generation_unavailable", ""}
    ]
    return {
        "bertscore": bertscore,
        "claim_grounding": grounding,
        "citation_validity": citation,
        "answer_completeness": {
            "status": "computed",
            "answerability_counts": answerability_counts,
            "average_query_coverage": round(
                sum(substantive_coverages) / len(substantive_coverages),
                6,
            )
            if substantive_coverages
            else 0.0,
        },
        "efficiency": efficiency_metrics([record["timings_ms"] for record in records]),
    }


def run_offline_reaudit(
    *,
    gold_queries: list[Any],
    source_directory: Path,
    config: AppConfig,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    """Rerun Steps 13-16 from saved generation/context data without API calls."""
    records_path = source_directory / "full_pipeline.jsonl"
    manifest_path = source_directory / "manifest.json"
    if not records_path.exists() or not manifest_path.exists():
        raise FileNotFoundError(
            "Re-audit source must contain full_pipeline.jsonl and manifest.json."
        )
    source_manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    source_records = {str(row.get("query_id") or ""): row for row in read_jsonl(records_path)}
    missing = [gold.query_id for gold in gold_queries if gold.query_id not in source_records]
    if missing:
        raise ValueError(f"Re-audit source is missing {len(missing)} requested query IDs.")

    records: list[dict[str, Any]] = []
    audits: list[dict[str, Any]] = []
    for index, gold in enumerate(gold_queries, start=1):
        source = source_records[gold.query_id]
        raw = dict(source.get("raw") or {})
        context_payload = raw.get("context")
        generated_payload = raw.get("generated")
        if not isinstance(context_payload, dict) or not isinstance(generated_payload, dict):
            raise ValueError(f"Re-audit source lacks context/generated data for {gold.query_id}.")
        context = EvidenceContextBundle(**context_payload)
        generated = generated_from_dict(generated_payload)

        started = perf_counter()
        claims = extract_claims(generated)
        claim_ms = round((perf_counter() - started) * 1000.0, 3)
        started = perf_counter()
        verifications, verifier_audit = run_claim_verification(
            claims,
            context,
            config,
        )
        verification_ms = round((perf_counter() - started) * 1000.0, 3)
        started = perf_counter()
        mitigated = mitigate_hallucinations(generated, verifications, context=context)
        mitigation_ms = round((perf_counter() - started) * 1000.0, 3)
        started = perf_counter()
        reliability = score_reliability(mitigated, verifications, context)
        reliability_ms = round((perf_counter() - started) * 1000.0, 3)

        timings = dict(source.get("timings_ms") or {})
        replaced_stages = {
            "step13_claim_extraction": claim_ms,
            "step14_claim_verification": verification_ms,
            "step15_hallucination_mitigation": mitigation_ms,
            "step16_reliability_scoring": reliability_ms,
        }
        old_postprocessing = sum(float(timings.get(key) or 0.0) for key in replaced_stages)
        new_postprocessing = sum(replaced_stages.values())
        timings.update(replaced_stages)
        timings["end_to_end"] = round(
            max(0.0, float(timings.get("end_to_end") or 0.0) - old_postprocessing)
            + new_postprocessing,
            3,
        )
        updated_raw = {
            **raw,
            "claims": [asdict(item) for item in claims],
            "verifications": [asdict(item) for item in verifications],
            "claim_verifier_audit": verifier_audit,
            "mitigated": asdict(mitigated),
            "reliability": asdict(reliability),
            "reaudit_source": str(records_path),
            "reaudited_steps": [13, 14, 15, 16],
        }
        record, audit = build_record(
            gold=gold,
            mode="full_pipeline",
            answer=mitigated.answer,
            output_claims=mitigated.kept_claims,
            verifications=verifications,
            context=context,
            timings=timings,
            raw=updated_raw,
            warnings=list(source.get("warnings") or []),
            generation_status=generated.generation_status,
            answerability=mitigated.answerability,
        )
        records.append(record)
        audits.append(audit)
        print(
            json.dumps(
                {
                    "progress": f"{index}/{len(gold_queries)}",
                    "query_id": gold.query_id,
                    "generation_status": generated.generation_status,
                    "answerability": mitigated.answerability,
                    "kept_claims": len(mitigated.kept_claims),
                },
                ensure_ascii=False,
            ),
            flush=True,
        )
    return records, audits, source_manifest


def run_resumable_frozen_generation(
    *,
    gold_queries: list[Any],
    retrieval_file: Path,
    step08_source_files: list[Path],
    run_id: str,
    repository: Neo4jRepository,
    config: AppConfig,
    request_interval_seconds: float,
    max_rate_limit_retries: int,
    retry_base_seconds: float,
    resume: bool,
    rerank_frozen_retrieval: bool,
    allow_live_step08: bool,
    frozen_context_file: Path | None = None,
    semantic_adjudicator: SemanticClaimAdjudicator | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, int]]:
    """Generate from frozen retrieval or exact frozen Step 11 contexts."""
    frozen_rows = {str(row["query_id"]): row for row in read_jsonl(retrieval_file)}
    expected_ids = {gold.query_id for gold in gold_queries}
    missing = sorted(expected_ids - set(frozen_rows))
    if missing:
        raise ValueError(f"Frozen retrieval run is missing {len(missing)} query IDs.")

    cache_directory = GENERATION_CACHE_ROOT / run_id
    if cache_directory.exists() and not resume:
        raise FileExistsError(
            f"Generation cache already exists; use --resume: {cache_directory}"
        )
    cache_directory.mkdir(parents=True, exist_ok=True)
    analysis_cache_path = cache_directory / "step08_success.jsonl"
    generation_cache_path = cache_directory / "step12_success.jsonl"
    records_path = cache_directory / "completed_records.jsonl"
    audits_path = cache_directory / "completed_audits.jsonl"
    pipeline_fingerprint = evaluation_pipeline_fingerprint(
        retrieval_file,
        config,
        rerank_frozen_retrieval,
    )

    analysis_cache: dict[str, dict[str, Any]] = {}
    for query_id, row in frozen_rows.items():
        raw = dict(row.get("raw") or {}) if frozen_context_file else row
        analysis_payload = dict(raw.get("query_analysis") or {})
        linking_payload = dict(raw.get("entity_linking") or {})
        # Frozen retrieval means frozen Step 8. Preserve the exact saved payload,
        # including warnings/fallback classifications, so modes remain comparable.
        if analysis_payload and linking_payload:
            analysis_cache[query_id] = {
                "query_id": query_id,
                "analysis": analysis_payload,
                "linking": linking_payload,
                "source": str(frozen_context_file or retrieval_file),
            }
    if allow_live_step08:
        for source_file in step08_source_files:
            for row in read_jsonl(source_file):
                analysis_payload = dict((row.get("raw") or {}).get("query_analysis") or {})
                linking_payload = dict((row.get("raw") or {}).get("entity_linking") or {})
                if analysis_payload and linking_payload and analysis_succeeded(analysis_payload):
                    analysis_cache[str(row["query_id"])] = {
                        "query_id": str(row["query_id"]),
                        "analysis": analysis_payload,
                        "linking": linking_payload,
                        "source": str(source_file),
                    }
    for row in read_jsonl(analysis_cache_path):
        if allow_live_step08 and analysis_succeeded(dict(row.get("analysis") or {})):
            analysis_cache[str(row["query_id"])] = row

    missing_frozen_analysis = sorted(expected_ids - set(analysis_cache))
    if missing_frozen_analysis and not allow_live_step08:
        raise ValueError(
            "Frozen retrieval is missing Step 8 analysis/linking for "
            f"{len(missing_frozen_analysis)} query IDs; use --allow-live-step08 only "
            "for a non-frozen experiment."
        )

    generation_cache: dict[tuple[str, str], dict[str, Any]] = {}
    for row in read_jsonl(generation_cache_path):
        generated_payload = dict(row.get("generated") or {})
        if generated_payload.get("generation_status") == "generated":
            generation_cache[(str(row["query_id"]), str(row["context_fingerprint"]))] = row

    completed_records = {
        str(row["query_id"]): row for row in read_jsonl(records_path)
    }
    existing_pipeline_fingerprints = {
        str((row.get("raw") or {}).get("pipeline_fingerprint") or "")
        for row in completed_records.values()
    }
    if completed_records and existing_pipeline_fingerprints != {pipeline_fingerprint}:
        raise RuntimeError(
            "Generation cache belongs to a different evaluation pipeline version; "
            "use a new --run-id instead of mixing pre-fix and post-fix records."
        )
    completed_audits = {
        str(row["query_id"]): row for row in read_jsonl(audits_path)
    }
    pacer = RequestPacer(request_interval_seconds)
    cache_stats = {
        "step08_reused": 0,
        "step08_called": 0,
        "step12_reused": 0,
        "step12_called": 0,
        "queries_resumed": len(completed_records),
    }

    for index, gold in enumerate(gold_queries, start=1):
        if gold.query_id in completed_records:
            continue
        frozen = frozen_rows[gold.query_id]
        pipeline_started = perf_counter()
        analysis_ms = 0.0
        cached_analysis = analysis_cache.get(gold.query_id)
        if cached_analysis is not None:
            analysis = analysis_from_dict(dict(cached_analysis["analysis"]))
            linking = linking_from_dict(dict(cached_analysis["linking"]))
            cache_stats["step08_reused"] += 1
        else:
            if not allow_live_step08:
                raise RuntimeError(
                    f"Frozen Step 8 payload is unavailable for {gold.query_id}; no live call was made."
                )
            if repository is None:
                raise RuntimeError("Live Step 8 requires a Neo4j repository.")
            last_warning = ""
            for attempt in range(1, max_rate_limit_retries + 1):
                pacer.wait()
                started = perf_counter()
                analysis, linking = analyze_and_link_query(
                    gold.query,
                    repository=repository,
                    config=config,
                )
                analysis_ms += (perf_counter() - started) * 1000.0
                cache_stats["step08_called"] += 1
                if not any(
                    "Unified LLM query analysis failed" in warning
                    for warning in analysis.warnings
                ):
                    cached_analysis = {
                        "query_id": gold.query_id,
                        "analysis": asdict(analysis),
                        "linking": asdict(linking),
                        "source": "live_api",
                        "attempt": attempt,
                    }
                    append_jsonl(analysis_cache_path, cached_analysis)
                    analysis_cache[gold.query_id] = cached_analysis
                    break
                last_warning = " | ".join(analysis.warnings)
                if "HTTPError 429" not in last_warning:
                    raise RuntimeError(
                        f"Step 8 failed for {gold.query_id}; cache preserved: {last_warning}"
                    )
                if attempt < max_rate_limit_retries:
                    sleep(rate_limit_delay(retry_base_seconds, attempt))
            else:
                raise RuntimeError(
                    f"Step 8 rate limit persisted for {gold.query_id}; rerun with --resume. "
                    f"Cache preserved at {cache_directory}."
                )

        if frozen_context_file:
            raw = dict(frozen.get("raw") or {})
            context_payload = raw.get("context")
            if not isinstance(context_payload, dict):
                raise ValueError(
                    f"Frozen context source lacks Step 11 context for {gold.query_id}."
                )
            context = EvidenceContextBundle(**context_payload)
            reranking_ms = 0.0
            context_ms = 0.0
            subgraph_warnings: list[str] = []
            retrieval_plan_payload = dict(raw.get("retrieval_plan") or {})
        else:
            started = perf_counter()
            subgraph = frozen_subgraph(
                frozen,
                analysis.primary_intent,
                rerank=rerank_frozen_retrieval,
                config=config,
            )
            reranking_ms = round((perf_counter() - started) * 1000.0, 3)
            started = perf_counter()
            context = build_evidence_context(
                subgraph,
                analysis.reformulated_query,
                config=config,
            )
            context_ms = round((perf_counter() - started) * 1000.0, 3)
            subgraph_warnings = list(subgraph.warnings)
            retrieval_plan_payload = dict(frozen.get("retrieval_plan") or {})
        fingerprint = context_fingerprint(context, config)
        cached_generation = generation_cache.get((gold.query_id, fingerprint))
        generation_ms = 0.0
        if cached_generation is not None:
            generated = generated_from_dict(dict(cached_generation["generated"]))
            cache_stats["step12_reused"] += 1
        else:
            for attempt in range(1, max_rate_limit_retries + 1):
                # Empty contexts return an immediate insufficient-evidence fallback
                # and never call the provider, so they must not consume API pacing.
                if context.evidence_items:
                    pacer.wait()
                started = perf_counter()
                generated = generate_grounded_answer(context, config=config)
                generation_ms += (perf_counter() - started) * 1000.0
                if context.evidence_items:
                    cache_stats["step12_called"] += 1
                if generated.generation_status == "generated":
                    cached_generation = {
                        "query_id": gold.query_id,
                        "context_fingerprint": fingerprint,
                        "generated": asdict(generated),
                        "source": "live_api",
                        "attempt": attempt,
                    }
                    append_jsonl(generation_cache_path, cached_generation)
                    generation_cache[(gold.query_id, fingerprint)] = cached_generation
                    break
                if generated.fallback_type == "insufficient_evidence":
                    break
                if "HTTPError 429" not in generated.fallback_reason:
                    break
                if attempt < max_rate_limit_retries:
                    sleep(rate_limit_delay(retry_base_seconds, attempt))
            else:
                raise RuntimeError(
                    f"Step 12 rate limit persisted for {gold.query_id}; rerun with --resume. "
                    f"Cache preserved at {cache_directory}. "
                    f"Provider details: {generated.fallback_reason}"
                )
            if (
                generated.generation_status != "generated"
                and "HTTPError 429" in generated.fallback_reason
            ):
                raise RuntimeError(
                    f"Step 12 rate limit persisted for {gold.query_id}; rerun with --resume. "
                    f"Cache preserved at {cache_directory}. "
                    f"Provider details: {generated.fallback_reason}"
                )

        started = perf_counter()
        claims = extract_claims(generated)
        claim_ms = round((perf_counter() - started) * 1000.0, 3)
        started = perf_counter()
        verifications, verifier_audit = run_claim_verification(
            claims,
            context,
            config,
            semantic_adjudicator,
        )
        verification_ms = round((perf_counter() - started) * 1000.0, 3)
        started = perf_counter()
        mitigated = mitigate_hallucinations(generated, verifications, context=context)
        mitigation_ms = round((perf_counter() - started) * 1000.0, 3)
        started = perf_counter()
        reliability = score_reliability(mitigated, verifications, context)
        reliability_ms = round((perf_counter() - started) * 1000.0, 3)
        timings = {
            "step08_query_understanding": round(analysis_ms, 3),
            "step08_retrieval_planning": 0.0,
            "step09_hybrid_retrieval": 0.0,
            "step10_subgraph_reranking": reranking_ms,
            "step11_context_construction": context_ms,
            "step12_answer_generation": round(generation_ms, 3),
            "step13_claim_extraction": claim_ms,
            "step14_claim_verification": verification_ms,
            "step15_hallucination_mitigation": mitigation_ms,
            "step16_reliability_scoring": reliability_ms,
            "end_to_end": round((perf_counter() - pipeline_started) * 1000.0, 3),
        }
        record, audit = build_record(
            gold=gold,
            mode="full_pipeline",
            answer=mitigated.answer,
            output_claims=mitigated.kept_claims,
            verifications=verifications,
            context=context,
            timings=timings,
            raw={
                "query_analysis": asdict(analysis),
                "entity_linking": asdict(linking),
                "retrieval_plan": retrieval_plan_payload,
                "context": asdict(context),
                "generated": asdict(generated),
                "claims": [asdict(item) for item in claims],
                "verifications": [asdict(item) for item in verifications],
                "claim_verifier_audit": verifier_audit,
                "mitigated": asdict(mitigated),
                "reliability": asdict(reliability),
                "frozen_retrieval_source": str(retrieval_file),
                "frozen_context_source": (
                    str(frozen_context_file) if frozen_context_file else ""
                ),
                "context_fingerprint": fingerprint,
                "pipeline_fingerprint": pipeline_fingerprint,
            },
            warnings=[*analysis.warnings, *subgraph_warnings, *generated.warnings],
            generation_status=generated.generation_status,
            answerability=mitigated.answerability,
        )
        append_jsonl(records_path, record)
        append_jsonl(audits_path, audit)
        completed_records[gold.query_id] = record
        completed_audits[gold.query_id] = audit
        print(
            json.dumps(
                {
                    "progress": f"{index}/{len(gold_queries)}",
                    "query_id": gold.query_id,
                    "generation_status": generated.generation_status,
                    "cached_step08": analysis_ms == 0.0,
                    "cached_step12": cached_generation is not None and generation_ms == 0.0,
                },
                ensure_ascii=False,
            ),
            flush=True,
        )

    ordered_records = [completed_records[gold.query_id] for gold in gold_queries]
    ordered_audits = [completed_audits[gold.query_id] for gold in gold_queries]
    return ordered_records, ordered_audits, cache_stats


def main() -> int:
    parser = argparse.ArgumentParser(description="Run independent answer-generation ablations on final_v1.")
    parser.add_argument("--gold-file", type=Path, default=DEFAULT_GOLD_FILE)
    parser.add_argument("--mode", action="append", choices=MODES, default=[])
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--run-id", default="")
    parser.add_argument(
        "--reuse-retrieval-run",
        type=Path,
        help="Reuse a completed full_hybrid.jsonl; Steps 9-10 are not rerun.",
    )
    parser.add_argument(
        "--reuse-context-run",
        type=Path,
        help=(
            "Reuse full_pipeline.jsonl from a completed generation run and rerun "
            "only Steps 12-17 from its exact frozen Step 11 contexts."
        ),
    )
    parser.add_argument(
        "--reaudit-generation-run",
        type=Path,
        help="Reuse a completed generation directory and rerun only Steps 13-16 offline.",
    )
    parser.add_argument(
        "--step08-source-run",
        type=Path,
        action="append",
        default=[],
        help="Optional prior generation JSONL containing successful Step 8 outputs.",
    )
    parser.add_argument("--resume", action="store_true")
    parser.add_argument(
        "--rerank-frozen-retrieval",
        action="store_true",
        help="Apply the production Step 10 reranker to saved retrieval candidates before Step 11.",
    )
    parser.add_argument(
        "--allow-live-step08",
        action="store_true",
        help="Permit new Step 8 calls when frozen analysis is missing (disabled by default).",
    )
    parser.add_argument("--request-interval-seconds", type=float, default=8.0)
    parser.add_argument("--max-rate-limit-retries", type=int, default=6)
    parser.add_argument("--rate-limit-backoff-seconds", type=float, default=30.0)
    parser.add_argument(
        "--answer-prompt-version",
        choices=(
            "grounded_claim_first_v3_1",
            "grounded_evidence_adaptive_v4_2",
        ),
        default="",
        help=(
            "Explicitly select the isolated Step 12 profile for a new run. "
            "Saved runs and caches remain bound to this value by fingerprint."
        ),
    )
    parser.add_argument(
        "--claim-verifier-profile",
        choices=CLAIM_VERIFIER_PROFILES,
        default="",
        help=(
            "Select deterministic_v3 or the opt-in hard_soft_v5 development "
            "profile. The frozen production default is deterministic_v3."
        ),
    )
    parser.add_argument(
        "--enable-claim-adjudication",
        action="store_true",
        help=(
            "Permit semantic review of v5 soft-gate disputes. This flag is "
            "required even when the environment setting is true."
        ),
    )
    parser.add_argument(
        "--enable-cross-encoder-rescue",
        action="store_true",
        help=(
            "Enable the local conditional reranker only for empty or weak "
            "Step 11 contexts. The semantic E5 fallback is disabled in this "
            "isolated ablation."
        ),
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    modes = args.mode or list(MODES)
    gold_path = args.gold_file.resolve()
    gold_queries = load_gold_queries(gold_path, args.limit)
    config = load_final_config()
    if args.answer_prompt_version:
        config = replace(
            config,
            answer_generation=replace(
                config.answer_generation,
                prompt_version=args.answer_prompt_version,
            ),
        )
    verifier_profile = (
        args.claim_verifier_profile
        or config.claim_adjudication.verifier_profile
    )
    if (
        args.enable_claim_adjudication
        and verifier_profile != VERIFIER_V5_PROFILE
    ):
        raise ValueError(
            "Semantic claim adjudication is available only with "
            "--claim-verifier-profile hard_soft_v5."
        )
    config = replace(
        config,
        claim_adjudication=replace(
            config.claim_adjudication,
            verifier_profile=verifier_profile,
            # Semantic retention always requires the explicit CLI flag.
            enabled=args.enable_claim_adjudication,
        ),
        qa_corpus=replace(
            config.qa_corpus,
            # Rescue always requires an explicit evaluation flag.
            cross_encoder_rescue_enabled=(
                args.enable_cross_encoder_rescue
            ),
            semantic_fallback_enabled=(
                False
                if args.enable_cross_encoder_rescue
                else config.qa_corpus.semantic_fallback_enabled
            ),
        ),
    )
    if config.graph_version != "final_v1":
        raise RuntimeError("Generation evaluation is restricted to frozen final_v1.")
    if args.dry_run:
        print(
            json.dumps(
                {
                    "status": "dry_run",
                    "queries": len(gold_queries),
                    "modes": modes,
                    "claim_verifier_profile": verifier_profile,
                    "semantic_claim_adjudication": (
                        config.claim_adjudication.enabled
                    ),
                    "cross_encoder_rescue": (
                        config.qa_corpus.cross_encoder_rescue_enabled
                    ),
                },
                indent=2,
            )
        )
        return 0
    if not gold_queries:
        raise RuntimeError("The gold template has no independently annotated query rows.")

    run_id = args.run_id or make_run_id("generation")
    ensure_run_available(GENERATION_OUTPUT_ROOT, run_id)
    ensure_run_available(CLAIM_AUDIT_OUTPUT_ROOT, run_id)
    semantic_adjudicator: SemanticClaimAdjudicator | None = None
    if config.claim_adjudication.enabled:
        semantic_adjudicator = SemanticClaimAdjudicator(
            config,
            cache_path=(
                GENERATION_CACHE_ROOT
                / run_id
                / "step14_semantic_adjudication.jsonl"
            ),
            raise_on_error=True,
        )
    cross_encoder_rescue: ConditionalCrossEncoderRescue | None = None
    if config.qa_corpus.cross_encoder_rescue_enabled:
        cross_encoder_rescue = ConditionalCrossEncoderRescue(
            config,
            raise_on_unavailable=True,
        )
    if args.reaudit_generation_run:
        if args.reuse_retrieval_run or args.reuse_context_run:
            raise ValueError(
                "Choose only one of --reaudit-generation-run, "
                "--reuse-retrieval-run, or --reuse-context-run."
            )
        if modes != ["full_pipeline"]:
            raise ValueError("Offline re-audit supports only --mode full_pipeline.")
        if config.claim_adjudication.enabled:
            raise ValueError(
                "Offline re-audit cannot make semantic adjudication API calls."
            )
        if config.qa_corpus.cross_encoder_rescue_enabled:
            raise ValueError(
                "Cross-encoder rescue requires a live Step 9-11 pass and is "
                "not available during an offline Step 13-16 re-audit."
            )
        source_directory = args.reaudit_generation_run.resolve()
        records, audits, source_manifest = run_offline_reaudit(
            gold_queries=gold_queries,
            source_directory=source_directory,
            config=config,
        )
        graph_counts = dict(source_manifest.get("graph", {}).get("counts") or {})
        aggregate = {"full_pipeline": aggregate_mode(records)}
        manifest = build_manifest(
            run_id=run_id,
            run_type="generation_offline_reaudit",
            modes=modes,
            gold_path=gold_path,
            gold_count=len(gold_queries),
            config=config,
            graph_counts=graph_counts,
            arguments={
                key: (
                    [str(item) for item in value]
                    if isinstance(value, list)
                    else str(value)
                    if isinstance(value, Path)
                    else value
                )
                for key, value in vars(args).items()
            },
        )
        manifest["reaudit"] = {
            "source_run_id": source_manifest.get("run_id", source_directory.name),
            "source_directory": str(source_directory),
            "source_answer_prompt_version": source_manifest.get("models", {}).get(
                "answer_prompt_version", "unknown"
            ),
            "current_verifier_runtime_prompt_version": config.answer_generation.prompt_version,
            "source_records_sha256": hashlib.sha256(
                (source_directory / "full_pipeline.jsonl").read_bytes()
            ).hexdigest(),
            "steps_rerun": [13, 14, 15, 16],
            "api_calls": 0,
            "retrieval_rerun": False,
            "generation_rerun": False,
        }
        manifest["claim_verifier"] = claim_verifier_manifest(
            config,
            semantic_adjudicator,
        )
        manifest["cross_encoder_rescue"] = (
            cross_encoder_rescue_manifest(
                config,
                cross_encoder_rescue,
            )
        )
        run_directory = create_run_directory(GENERATION_OUTPUT_ROOT, run_id)
        audit_directory = create_run_directory(CLAIM_AUDIT_OUTPUT_ROOT, run_id)
        write_jsonl(run_directory / "full_pipeline.jsonl", records)
        write_jsonl(audit_directory / "full_pipeline.jsonl", audits)
        write_json(run_directory / "metrics.json", aggregate)
        write_json(run_directory / "manifest.json", manifest)
        write_json(audit_directory / "manifest.json", manifest)
        print(
            json.dumps(
                {
                    "status": "ok",
                    "run_id": run_id,
                    "generation_output": str(run_directory),
                    "claim_audit_output": str(audit_directory),
                    "queries": len(gold_queries),
                    "api_calls": 0,
                    "steps_rerun": [13, 14, 15, 16],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    if args.reuse_retrieval_run or args.reuse_context_run:
        if modes != ["full_pipeline"]:
            raise ValueError("Frozen source reuse supports only --mode full_pipeline.")
        if args.max_rate_limit_retries <= 0:
            raise ValueError("max-rate-limit-retries must be positive.")
        if args.reuse_retrieval_run and args.reuse_context_run:
            raise ValueError(
                "Choose either --reuse-retrieval-run or --reuse-context-run."
            )
        if config.qa_corpus.cross_encoder_rescue_enabled:
            raise ValueError(
                "Cross-encoder rescue must be evaluated while building the "
                "retrieval run, not injected into a frozen retrieval/context "
                "artifact."
            )

        frozen_context_file: Path | None = None
        source_manifest: dict[str, Any] = {}
        if args.reuse_context_run:
            if args.rerank_frozen_retrieval:
                raise ValueError(
                    "--rerank-frozen-retrieval is incompatible with exact Step 11 "
                    "context replay."
                )
            if args.allow_live_step08 or args.step08_source_run:
                raise ValueError(
                    "Exact Step 11 context replay cannot make or substitute Step 8 calls."
                )
            context_source = args.reuse_context_run.resolve()
            frozen_context_file = (
                context_source / "full_pipeline.jsonl"
                if context_source.is_dir()
                else context_source
            )
            if not frozen_context_file.exists():
                raise FileNotFoundError(
                    f"Frozen context JSONL not found: {frozen_context_file}"
                )
            source_manifest_path = frozen_context_file.parent / "manifest.json"
            if source_manifest_path.exists():
                source_manifest = json.loads(
                    source_manifest_path.read_text(encoding="utf-8-sig")
                )
            graph_counts = dict(source_manifest.get("graph", {}).get("counts") or {})
            retrieval_file = frozen_context_file
            records, audits, cache_stats = run_resumable_frozen_generation(
                gold_queries=gold_queries,
                retrieval_file=retrieval_file,
                step08_source_files=[],
                run_id=run_id,
                repository=None,
                config=config,
                request_interval_seconds=args.request_interval_seconds,
                max_rate_limit_retries=args.max_rate_limit_retries,
                retry_base_seconds=args.rate_limit_backoff_seconds,
                resume=args.resume,
                rerank_frozen_retrieval=False,
                allow_live_step08=False,
                frozen_context_file=frozen_context_file,
                semantic_adjudicator=semantic_adjudicator,
            )
        else:
            retrieval_file = args.reuse_retrieval_run.resolve()
            if not retrieval_file.exists():
                raise FileNotFoundError(
                    f"Frozen retrieval JSONL not found: {retrieval_file}"
                )
            with Neo4jRepository(config=config) as repository:
                graph_counts = repository.get_graph_counts()
                records, audits, cache_stats = run_resumable_frozen_generation(
                    gold_queries=gold_queries,
                    retrieval_file=retrieval_file,
                    step08_source_files=[
                        path.resolve() for path in args.step08_source_run
                    ],
                    run_id=run_id,
                    repository=repository,
                    config=config,
                    request_interval_seconds=args.request_interval_seconds,
                    max_rate_limit_retries=args.max_rate_limit_retries,
                    retry_base_seconds=args.rate_limit_backoff_seconds,
                    resume=args.resume,
                    rerank_frozen_retrieval=args.rerank_frozen_retrieval,
                    allow_live_step08=args.allow_live_step08,
                    semantic_adjudicator=semantic_adjudicator,
                )
        aggregate = {"full_pipeline": aggregate_mode(records)}
        manifest = build_manifest(
            run_id=run_id,
            run_type=(
                "generation_ablation_frozen_context_steps12_17"
                if frozen_context_file
                else "generation_ablation_frozen_retrieval_resume"
            ),
            modes=modes,
            gold_path=gold_path,
            gold_count=len(gold_queries),
            config=config,
            graph_counts=graph_counts,
            arguments={
                key: (
                    [str(item) for item in value]
                    if isinstance(value, list)
                    else str(value)
                    if isinstance(value, Path)
                    else value
                )
                for key, value in vars(args).items()
            },
        )
        manifest["cache"] = {
            "directory": str((GENERATION_CACHE_ROOT / run_id).resolve()),
            "append_only": True,
            "successful_api_calls_only": True,
            **cache_stats,
        }
        manifest["claim_verifier"] = claim_verifier_manifest(
            config,
            semantic_adjudicator,
        )
        manifest["cross_encoder_rescue"] = (
            cross_encoder_rescue_manifest(
                config,
                cross_encoder_rescue,
            )
        )
        if frozen_context_file:
            manifest["frozen_context_replay"] = {
                "source_file": str(frozen_context_file),
                "source_sha256": hashlib.sha256(
                    frozen_context_file.read_bytes()
                ).hexdigest(),
                "source_run_id": source_manifest.get(
                    "run_id", frozen_context_file.parent.name
                ),
                "steps_rerun": [12, 13, 14, 15, 16, 17],
                "steps_not_rerun": [8, 9, 10, 11],
                "exact_step11_context_reused": True,
            }
        run_directory = create_run_directory(GENERATION_OUTPUT_ROOT, run_id)
        audit_directory = create_run_directory(CLAIM_AUDIT_OUTPUT_ROOT, run_id)
        write_jsonl(run_directory / "full_pipeline.jsonl", records)
        write_jsonl(audit_directory / "full_pipeline.jsonl", audits)
        write_json(run_directory / "metrics.json", aggregate)
        write_json(run_directory / "manifest.json", manifest)
        write_json(audit_directory / "manifest.json", manifest)
        print(
            json.dumps(
                {
                    "status": "ok",
                    "run_id": run_id,
                    "generation_output": str(run_directory),
                    "claim_audit_output": str(audit_directory),
                    "cache": str(GENERATION_CACHE_ROOT / run_id),
                    "queries": len(gold_queries),
                    "modes": modes,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    records_by_mode: dict[str, list[dict[str, Any]]] = {mode: [] for mode in modes}
    audits_by_mode: dict[str, list[dict[str, Any]]] = {mode: [] for mode in modes}
    needs_rag = any(mode in {"rag_before_mitigation", "full_pipeline"} for mode in modes)
    model = None
    if needs_rag:
        model, _, _ = load_model(config.embeddings.model_name, config.embeddings.dimension)

    with Neo4jRepository(config=config) as repository:
        graph_counts = repository.get_graph_counts()
        for gold in gold_queries:
            artifacts = (
                timed_rag_artifacts(
                    gold.query,
                    repository,
                    config,
                    model,
                    semantic_adjudicator,
                    cross_encoder_rescue,
                )
                if needs_rag
                else None
            )
            for mode in modes:
                if mode == "llm_only":
                    started = perf_counter()
                    generated = generate_llm_only(gold.query, config)
                    elapsed = round((perf_counter() - started) * 1000.0, 3)
                    context = EvidenceContextBundle(query=gold.query, reformulated_query=gold.query)
                    claims = extract_claims(generated)
                    verifications, verifier_audit = run_claim_verification(
                        claims,
                        context,
                        config,
                        semantic_adjudicator,
                    )
                    record, audit = build_record(
                        gold=gold,
                        mode=mode,
                        answer=generated.answer,
                        output_claims=claims,
                        verifications=verifications,
                        context=context,
                        timings={"step12_llm_only_generation": elapsed, "end_to_end": elapsed},
                        raw={
                            "generated": asdict(generated),
                            "claim_verifier_audit": verifier_audit,
                        },
                        warnings=generated.warnings,
                        generation_status=generated.generation_status,
                        answerability=(
                            "generation_unavailable"
                            if generated.generation_status != "generated"
                            else "answerable"
                        ),
                    )
                else:
                    assert artifacts is not None
                    generated = artifacts["generated"]
                    context = artifacts["context"]
                    verifications = artifacts["verifications"]
                    if mode == "rag_before_mitigation":
                        answer = generated.answer
                        output_claims = artifacts["claims"]
                        before_mitigation_stages = {
                            "step08_query_understanding",
                            "step08_retrieval_planning",
                            "step09_hybrid_retrieval",
                            "step10_subgraph_reranking",
                            "step11_context_construction",
                            "step12_answer_generation",
                        }
                        timings = {
                            **{
                                key: value
                                for key, value in artifacts["timings"].items()
                                if key in before_mitigation_stages
                            },
                            "end_to_end": artifacts["before_mitigation_end_to_end"],
                        }
                    else:
                        answer = artifacts["mitigated"].answer
                        output_claims = artifacts["mitigated"].kept_claims
                        timings = {
                            **artifacts["timings"],
                            "end_to_end": artifacts["full_end_to_end"],
                        }
                    record, audit = build_record(
                        gold=gold,
                        mode=mode,
                        answer=answer,
                        output_claims=output_claims,
                        verifications=verifications,
                        context=context,
                        timings=timings,
                        raw={
                            "query_analysis": asdict(artifacts["analysis"]),
                            "entity_linking": asdict(artifacts["linking"]),
                            "retrieval_plan": asdict(artifacts["plan"]),
                            "context": asdict(context),
                            "generated": asdict(generated),
                            "claims": [asdict(item) for item in artifacts["claims"]],
                            "verifications": [asdict(item) for item in verifications],
                            "claim_verifier_audit": artifacts[
                                "claim_verifier_audit"
                            ],
                            "cross_encoder_rescue_audit": artifacts[
                                "cross_encoder_rescue_audit"
                            ],
                            "mitigated": asdict(artifacts["mitigated"]),
                            "reliability": asdict(artifacts["reliability"]),
                        },
                        warnings=[
                            *artifacts["analysis"].warnings,
                            *artifacts["retrieval"].warnings,
                            *generated.warnings,
                        ],
                        generation_status=generated.generation_status,
                        answerability=(
                            "answerable"
                            if mode == "rag_before_mitigation"
                            and generated.generation_status == "generated"
                            else artifacts["mitigated"].answerability
                        ),
                    )
                records_by_mode[mode].append(record)
                audits_by_mode[mode].append(audit)

    aggregate = {mode: aggregate_mode(records) for mode, records in records_by_mode.items()}
    manifest = build_manifest(
        run_id=run_id,
        run_type="generation_ablation",
        modes=modes,
        gold_path=gold_path,
        gold_count=len(gold_queries),
        config=config,
        graph_counts=graph_counts,
        arguments={key: str(value) if isinstance(value, Path) else value for key, value in vars(args).items()},
    )
    manifest["claim_verifier"] = claim_verifier_manifest(
        config,
        semantic_adjudicator,
    )
    manifest["cross_encoder_rescue"] = cross_encoder_rescue_manifest(
        config,
        cross_encoder_rescue,
    )
    run_directory = create_run_directory(GENERATION_OUTPUT_ROOT, run_id)
    audit_directory = create_run_directory(CLAIM_AUDIT_OUTPUT_ROOT, run_id)
    for mode, records in records_by_mode.items():
        write_jsonl(run_directory / f"{mode}.jsonl", records)
        write_jsonl(audit_directory / f"{mode}.jsonl", audits_by_mode[mode])
    write_json(run_directory / "metrics.json", aggregate)
    write_json(run_directory / "manifest.json", manifest)
    write_json(audit_directory / "manifest.json", manifest)
    print(json.dumps({"status": "ok", "run_id": run_id, "generation_output": str(run_directory), "claim_audit_output": str(audit_directory), "queries": len(gold_queries), "modes": modes}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
