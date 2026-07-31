from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, replace
from typing import Any

from src.config import AppConfig, load_final_config
from src.evidence_policy import ANSWER_EVIDENCE, infer_evidence_origin
from src.models import AnswerClaim, EvidenceContextBundle, GeneratedAnswer
from src.query_relevance import (
    minimum_candidate_concept_coverage,
    query_concept_coverage,
    query_concepts,
)


GROQ_CHAT_COMPLETIONS_URL = "https://api.groq.com/openai/v1/chat/completions"
STRONG_DIRECT_MODE = "strong_direct_evidence"
PARTIAL_EVIDENCE_MODE = "partial_or_mixed_evidence"
V31_STRUCTURED_MODE = "structured_claims_v3_1"
V31_PROMPT_VERSION = "grounded_claim_first_v3_1"
V31_MAX_CLAIMS = 3
V4_MAX_CLAIMS = 2

# These gates identify a small, high-precision subset. They do not change
# retrieval or Step 11; they only decide how much freedom Step 12 receives.
STRONG_MIN_ANSWER_RELEVANCE = 0.75
STRONG_MIN_ENTITY_IDENTITY = 0.50
STRONG_MIN_INTENT_SUPPORT = 0.75
STRONG_MIN_QUERY_CONCEPT_COVERAGE = 0.75
STRONG_MIN_SOURCE_RELIABILITY = 0.75
STRONG_MIN_QUERY_CONSTRAINT_COVERAGE = 1.0

ANSWER_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "claims": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "claim_ar": {"type": "string"},
                    "citations": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
                "required": ["claim_ar", "citations"],
                "additionalProperties": False,
            },
        },
        "limitations_ar": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
    "required": ["claims", "limitations_ar"],
    "additionalProperties": False,
}


@dataclass(frozen=True)
class GenerationModeDecision:
    """Deterministic Step 12 policy decision made from Step 11 metadata."""

    mode: str
    evidence_ids: list[str]
    reason: str


def _score(value: Any) -> float:
    try:
        return max(0.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        return 0.0


def _flag(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _evidence_origin(item: dict[str, Any]) -> str:
    return infer_evidence_origin(
        evidence_origin=item.get("evidence_origin"),
        field=item.get("field"),
        source_quality=item.get("source_quality"),
        evidence=item.get("evidence"),
        source_question=item.get("source_question"),
        source_answer=item.get("source_answer"),
    )


def is_strong_direct_evidence(item: dict[str, Any]) -> bool:
    """Return True only for direct, answer-bearing, query-compatible evidence."""
    direct_anchor = _flag(item.get("direct_question_anchor"))
    entity_identity = _score(item.get("entity_identity"))
    return bool(
        str(item.get("evidence") or "").strip()
        and _evidence_origin(item) == ANSWER_EVIDENCE
        and not _flag(item.get("question_text_excluded"))
        and _score(item.get("answer_relevance")) >= STRONG_MIN_ANSWER_RELEVANCE
        and _score(item.get("intent_support")) >= STRONG_MIN_INTENT_SUPPORT
        and _score(item.get("query_concept_coverage"))
        >= STRONG_MIN_QUERY_CONCEPT_COVERAGE
        and _score(item.get("query_constraint_coverage"))
        >= STRONG_MIN_QUERY_CONSTRAINT_COVERAGE
        and _score(item.get("source_reliability")) >= STRONG_MIN_SOURCE_RELIABILITY
        and not _flag(item.get("anatomy_mismatch"))
        and not _flag(item.get("unrelated_condition_mismatch"))
        and (direct_anchor or entity_identity >= STRONG_MIN_ENTITY_IDENTITY)
    )


def select_generation_mode(
    context: EvidenceContextBundle,
    prompt_version: str = "",
) -> GenerationModeDecision:
    """Choose the generation policy without changing the saved Step 11 context."""
    if prompt_version == V31_PROMPT_VERSION:
        return GenerationModeDecision(
            mode=V31_STRUCTURED_MODE,
            evidence_ids=[
                str(item.get("evidence_id") or "")
                for item in context.evidence_items
                if str(item.get("evidence_id") or "")
            ],
            reason=(
                "V3.1 keeps the complete selected Step 11 context and requests up "
                "to three independently supported structured claims."
            ),
        )

    strong_items = [
        item for item in context.evidence_items if is_strong_direct_evidence(item)
    ]
    if strong_items:
        selected = max(
            strong_items,
            key=lambda item: (
                _flag(item.get("direct_question_anchor")),
                _score(item.get("answer_relevance")),
                _score(item.get("query_concept_coverage")),
                _score(item.get("entity_identity")),
                _score(item.get("retrieval_score")),
                str(item.get("evidence_id") or ""),
            ),
        )
        evidence_id = str(selected.get("evidence_id") or "")
        return GenerationModeDecision(
            mode=STRONG_DIRECT_MODE,
            evidence_ids=[evidence_id],
            reason=(
                "One answer-origin passage passed the strict identity, intent, "
                "concept, constraint, anatomy, and source-quality gates."
            ),
        )
    return GenerationModeDecision(
        mode=PARTIAL_EVIDENCE_MODE,
        evidence_ids=[
            str(item.get("evidence_id") or "")
            for item in context.evidence_items
            if str(item.get("evidence_id") or "")
        ],
        reason=(
            "No single answer-origin passage passed every strong-direct gate; "
            "generation is limited to independently cited claims."
        ),
    )


def prepare_generation_context(
    context: EvidenceContextBundle,
    decision: GenerationModeDecision,
) -> EvidenceContextBundle:
    """Narrow strong-direct generation to one passage without changing retrieval."""
    if decision.mode != STRONG_DIRECT_MODE:
        return context
    selected_ids = set(decision.evidence_ids)
    selected = [
        item
        for item in context.evidence_items
        if str(item.get("evidence_id") or "") in selected_ids
    ]
    allowed_qa_ids = [
        str(item.get("qa_id") or "")
        for item in selected
        if str(item.get("qa_id") or "")
    ]
    return replace(
        context,
        graph_facts=[],
        evidence_items=selected,
        allowed_evidence_ids=list(decision.evidence_ids),
        allowed_qa_ids=list(dict.fromkeys(allowed_qa_ids)),
    )


def _generation_evidence_items(
    context: EvidenceContextBundle,
) -> list[dict[str, str]]:
    """Send only authoritative text and its citation handle to the model."""
    return [
        {
            "evidence_id": str(item.get("evidence_id") or ""),
            "evidence": str(item.get("evidence") or ""),
        }
        for item in context.evidence_items
        if str(item.get("evidence_id") or "")
        and str(item.get("evidence") or "").strip()
    ]


def _generation_graph_facts(
    context: EvidenceContextBundle,
) -> list[dict[str, str]]:
    """Keep graph orientation compact; graph facts are never citation substitutes."""
    return [
        {
            "relation_id": str(item.get("relation_id") or ""),
            "fact": str(item.get("fact") or ""),
        }
        for item in context.graph_facts
        if str(item.get("fact") or "").strip()
    ]


def fallback_answer(
    context: EvidenceContextBundle,
    warning: str,
    config: AppConfig,
    attempt_count: int = 0,
    fallback_type: str = "insufficient_evidence",
    decision: GenerationModeDecision | None = None,
) -> GeneratedAnswer:
    technical_failure = fallback_type != "insufficient_evidence"
    return GeneratedAnswer(
        query=context.query,
        answer=(
            "تعذر توليد الإجابة بسبب مشكلة تقنية في خدمة التوليد، رغم توفر أدلة مسترجعة. يُرجى المحاولة لاحقاً."
            if technical_failure
            else "لا توجد أدلة كافية ضمن المصادر المسترجعة للإجابة بثقة. يُنصح باستشارة طبيب مختص."
        ),
        limitations=[
            "لم تُنشأ إجابة طبية؛ هذا فشل تقني وليس حكماً بعدم كفاية الأدلة."
            if technical_failure
            else "الأدلة المسترجعة غير كافية لتوليد إجابة موثوقة."
        ],
        model=config.answer_generation.model,
        prompt_version=config.answer_generation.prompt_version,
        generation_mode=decision.mode if decision else "",
        generation_evidence_ids=list(decision.evidence_ids) if decision else [],
        generation_mode_reason=decision.reason if decision else "",
        generation_status="fallback",
        fallback_type=fallback_type,
        fallback_reason=warning,
        attempt_count=attempt_count,
        warnings=[*context.warnings, warning],
    )


def build_messages(
    context: EvidenceContextBundle,
    decision: GenerationModeDecision | None = None,
    prompt_version: str = "",
) -> list[dict[str, str]]:
    decision = decision or select_generation_mode(context, prompt_version)
    context = prepare_generation_context(context, decision)
    if decision.mode == V31_STRUCTURED_MODE:
        mode_rules = [
            "Use the complete selected Step 11 context; do not switch to a single-passage mode.",
            "Return at most three self-contained atomic claims.",
            "Aim to cover the primary request and additional supported parts of the query.",
            "Each claim must be supported by exactly one evidence item.",
            "Different claims may cite different passages, but never merge facts from separate passages into one claim.",
            "Do not return a claim that only repeats the user's symptoms, medications, or question without answering it.",
            "Reject evidence about a different drug, disease, symptom, anatomy, patient history, or clinical relationship.",
            "When only part of the question is supported, answer that part and record the remaining gap in limitations_ar.",
        ]
    elif decision.mode == STRONG_DIRECT_MODE:
        mode_rules = [
            "Use only the single supplied evidence passage.",
            "Write a near-extractive answer: preserve its medical meaning and wording closely.",
            "Return one or at most two self-contained atomic claims.",
        ]
    else:
        mode_rules = [
            "Return at most two self-contained atomic claims.",
            "Each claim must be supported by exactly one evidence item.",
            "Never combine treatments, tests, causes, or relationships from separate passages.",
            "Answer only the supported part; put any remaining gap in limitations_ar.",
        ]
    payload = {
        "query": context.query,
        "reformulated_query": context.reformulated_query,
        "generation_mode": decision.mode,
        "generation_mode_reason": decision.reason,
        "graph_facts": _generation_graph_facts(context),
        "evidence_items": _generation_evidence_items(context),
        "allowed_evidence_ids": context.allowed_evidence_ids,
        "rules": mode_rules
        + [
            "Work claim-first and return no free-form answer outside the claims.",
            "Answer in Arabic using only the supplied graph facts and evidence items.",
            "Do not add outside medical knowledge or infer a diagnosis.",
            "Every factual medical claim must cite exactly one allowed evidence_id.",
            "Keep claims atomic: separate different organs, tests, treatments, causes, and recommendations into different claims.",
            "Each claim must contain the query's relevant disease, symptom, treatment, test, or anatomical subject so it is self-contained.",
            "Preserve drug names, diseases, anatomy, negation, numbers, and clinical relations exactly.",
            "Do not silently correct or reinterpret an unfamiliar, noisy, or possibly misspelled medical term in the evidence; omit that fragment when its meaning is unclear.",
            "Copy evidence IDs exactly; never invent citations, ages, durations, doses, or test values.",
            "Graph facts may orient selection but cannot support a claim without one cited evidence passage.",
            "When evidence is insufficient or conflicting, state that limitation clearly.",
            "Limitations may only state that evidence is incomplete; never name uncited treatments, tests, diseases, doses, or alternatives there.",
            "Do not present this output as a substitute for examination by a qualified clinician.",
        ],
        "required_json": {
            "claims": [
                {
                    "claim_ar": "one self-contained atomic factual medical claim",
                    "citations": ["E1"],
                }
            ],
            "limitations_ar": ["one concise evidence-coverage limitation, or an empty list"],
        },
    }
    return [
        {
            "role": "system",
            "content": "You generate claim-first, evidence-grounded Arabic medical answers. Return one strict JSON object only.",
        },
        {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
    ]


def parse_json_object(text: str) -> dict[str, Any]:
    text = str(text or "").strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:].strip()
    parsed = json.loads(text)
    if not isinstance(parsed, dict):
        raise ValueError("Answer response is not a JSON object.")
    return parsed


def validate_answer_payload(
    payload: dict[str, Any],
    context: EvidenceContextBundle,
    config: AppConfig,
    attempt_count: int = 1,
    decision: GenerationModeDecision | None = None,
) -> GeneratedAnswer:
    decision = decision or select_generation_mode(
        context,
        config.answer_generation.prompt_version,
    )
    required = {"claims", "limitations_ar"}
    missing = sorted(required - payload.keys())
    if missing:
        raise ValueError(f"Missing answer fields: {', '.join(missing)}")
    unexpected = sorted(payload.keys() - required)
    if unexpected:
        raise ValueError(f"Unexpected answer fields: {', '.join(unexpected)}")
    if not isinstance(payload["claims"], list):
        raise ValueError("claims must be a list.")
    max_claims = (
        V31_MAX_CLAIMS
        if decision.mode == V31_STRUCTURED_MODE
        else V4_MAX_CLAIMS
    )
    if len(payload["claims"]) > max_claims:
        if decision.mode == V31_STRUCTURED_MODE:
            raise ValueError("claims must contain at most 3 items.")
        raise ValueError("claims must contain at most two items.")
    if not isinstance(payload["limitations_ar"], list):
        raise ValueError("limitations_ar must be a list.")
    if len(payload["limitations_ar"]) > 1:
        raise ValueError("limitations_ar must contain at most one item.")

    evidence_by_id = {
        str(item.get("evidence_id") or ""): item
        for item in context.evidence_items
        if str(item.get("evidence_id") or "")
    }
    allowed_evidence = set(context.allowed_evidence_ids) & set(evidence_by_id)
    allowed_qa = set(context.allowed_qa_ids)
    query_text = context.reformulated_query or context.query
    query_phrases = context.query_medical_phrases
    concept_count = len(query_concepts(query_text, query_phrases))
    minimum_concept_coverage = minimum_candidate_concept_coverage(concept_count)
    warnings = list(context.warnings)
    claims: list[AnswerClaim] = []
    seen: set[str] = set()
    used_relations: list[str] = []
    generation_evidence_ids: list[str] = []
    for index, item in enumerate(payload["claims"], start=1):
        if not isinstance(item, dict):
            raise ValueError(f"Claim {index} is not an object.")
        if set(item) != {"claim_ar", "citations"}:
            raise ValueError(f"Claim {index} has unexpected or missing fields.")
        claim = str(item.get("claim_ar") or "").strip()
        citations_raw = item.get("citations")
        if not claim or not isinstance(citations_raw, list):
            raise ValueError(f"Claim {index} has malformed text or citations.")
        if len(citations_raw) != 1:
            raise ValueError(f"Claim {index} must cite exactly one evidence item.")
        citation = str(citations_raw[0])
        if citation not in allowed_evidence:
            raise ValueError(f"Claim {index} cites unavailable evidence: {citation}")
        if (
            concept_count
            and query_concept_coverage(query_text, claim, query_phrases)
            < minimum_concept_coverage
        ):
            warnings.append(
                f"Claim {index}: no deterministic query-concept match; "
                "Step 14 must decide query relevance."
            )

        evidence_item = evidence_by_id[citation]
        qa_id = str(evidence_item.get("qa_id") or "")
        qa_ids = [qa_id] if qa_id and qa_id in allowed_qa else []
        normalized = " ".join(claim.split())
        if normalized not in seen:
            claims.append(
                AnswerClaim(
                    claim=normalized,
                    citations=[citation],
                    source_qa_ids=qa_ids,
                )
            )
            generation_evidence_ids.append(citation)
            used_relations.extend(
                str(value)
                for value in evidence_item.get("relation_ids", [])
                if str(value)
            )
            seen.add(normalized)

    raw_limitations = [str(value).strip() for value in payload["limitations_ar"] if str(value).strip()]

    # The model only signals incompleteness. Python renders fixed wording so an
    # uncited medical recommendation cannot be smuggled into a limitation.
    limitations = []
    if raw_limitations or not claims:
        limitations = [
            "الإجابة محدودة بالأدلة المسترجعة، ولم تتوفر أدلة كافية لتغطية بقية السؤال."
        ]
    answer = "\n".join(claim.claim for claim in claims)
    if not answer:
        answer = "لا توجد أدلة كافية ضمن المصادر المسترجعة للإجابة بثقة."

    return GeneratedAnswer(
        query=context.query,
        answer=answer,
        claims=claims,
        used_relations=list(dict.fromkeys(used_relations)),
        limitations=limitations,
        model=config.answer_generation.model,
        prompt_version=config.answer_generation.prompt_version,
        generation_mode=decision.mode,
        generation_evidence_ids=list(dict.fromkeys(generation_evidence_ids)),
        generation_mode_reason=decision.reason,
        generation_status="generated",
        attempt_count=attempt_count,
        warnings=list(dict.fromkeys(warnings)),
    )


def retry_delay_seconds(exc: Exception, attempt: int, config: AppConfig) -> float:
    """Honor a numeric Retry-After header, bounded by the configured maximum."""
    delay = config.answer_generation.retry_base_seconds * (2 ** max(0, attempt - 1))
    if isinstance(exc, urllib.error.HTTPError):
        retry_after = exc.headers.get("Retry-After") if exc.headers else None
        try:
            delay = max(delay, float(retry_after)) if retry_after else delay
        except (TypeError, ValueError):
            pass
    return max(0.0, min(delay, config.answer_generation.retry_max_seconds))


def retryable_generation_error(exc: Exception) -> bool:
    if isinstance(exc, urllib.error.HTTPError):
        return exc.code == 429 or exc.code >= 500
    return isinstance(exc, (urllib.error.URLError, TimeoutError, ValueError, KeyError, json.JSONDecodeError))


def describe_http_error(exc: urllib.error.HTTPError) -> str:
    """Return useful rate-limit diagnostics without exposing request credentials."""
    selected_headers: list[str] = []
    if exc.headers:
        for name, value in exc.headers.items():
            lowered = name.lower()
            if lowered == "retry-after" or lowered.startswith("x-ratelimit-"):
                selected_headers.append(f"{lowered}={value}")
    try:
        body = " ".join(exc.read().decode("utf-8", errors="replace").split())
    except Exception:
        body = ""
    parts = [f"HTTPError {exc.code}", *selected_headers]
    if body:
        parts.append(f"body={body[:500]}")
    return "; ".join(parts)


def generate_grounded_answer(
    context: EvidenceContextBundle,
    config: AppConfig | None = None,
) -> GeneratedAnswer:
    config = config or load_final_config()
    if not context.evidence_items:
        return fallback_answer(context, "Generation skipped because no evidence was retrieved.", config)
    answer_config = config.answer_generation
    decision = select_generation_mode(context, answer_config.prompt_version)
    generation_context = prepare_generation_context(context, decision)
    if answer_config.provider != "groq":
        return fallback_answer(
            generation_context,
            f"Unsupported answer provider: {answer_config.provider}",
            config,
            fallback_type="configuration_error",
            decision=decision,
        )
    if not answer_config.groq_api_key:
        return fallback_answer(
            generation_context,
            "GROQ_API_KEY is not configured.",
            config,
            fallback_type="configuration_error",
            decision=decision,
        )

    body: dict[str, Any] = {
        "model": answer_config.model,
        "messages": build_messages(
            generation_context,
            decision,
            answer_config.prompt_version,
        ),
        "temperature": answer_config.temperature,
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": (
                    "structured_grounded_medical_answer_v3_1"
                    if decision.mode == V31_STRUCTURED_MODE
                    else "evidence_adaptive_medical_answer"
                ),
                "strict": True,
                "schema": ANSWER_JSON_SCHEMA,
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
            "User-Agent": "AHD-GraphRAG/1.0",
        },
        method="POST",
    )
    max_attempts = max(1, answer_config.max_attempts)
    last_error: Exception | None = None
    last_error_detail = ""
    attempts_made = 0
    for attempt in range(1, max_attempts + 1):
        attempts_made = attempt
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                response_payload = json.loads(response.read().decode("utf-8"))
            payload = parse_json_object(response_payload["choices"][0]["message"]["content"])
            return validate_answer_payload(
                payload,
                generation_context,
                config,
                attempt_count=attempt,
                decision=decision,
            )
        except Exception as exc:
            last_error = exc
            if isinstance(exc, urllib.error.HTTPError):
                last_error_detail = describe_http_error(exc)
            if attempt >= max_attempts or not retryable_generation_error(exc):
                break
            time.sleep(retry_delay_seconds(exc, attempt, config))

    error_name = type(last_error).__name__ if last_error else "UnknownError"
    if isinstance(last_error, urllib.error.HTTPError):
        error_name = last_error_detail or f"HTTPError {last_error.code}"
    elif last_error:
        detail = " ".join(str(last_error).split())
        if detail:
            error_name = f"{error_name}: {detail[:300]}"
    return fallback_answer(
        generation_context,
        f"Grounded answer generation failed after {attempts_made} attempt(s): {error_name}",
        config,
        attempt_count=attempts_made,
        fallback_type="technical_failure",
        decision=decision,
    )
