from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from typing import Any

from src.config import AppConfig, load_final_config
from src.models import AnswerClaim, EvidenceContextBundle, GeneratedAnswer


GROQ_CHAT_COMPLETIONS_URL = "https://api.groq.com/openai/v1/chat/completions"

ANSWER_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "answer_ar": {"type": "string"},
        "claims": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "claim_ar": {"type": "string"},
                    "citations": {"type": "array", "items": {"type": "string"}},
                    "source_qa_ids": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["claim_ar", "citations", "source_qa_ids"],
                "additionalProperties": False,
            },
        },
        "used_relation_ids": {"type": "array", "items": {"type": "string"}},
        "limitations_ar": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["answer_ar", "claims", "used_relation_ids", "limitations_ar"],
    "additionalProperties": False,
}


def fallback_answer(
    context: EvidenceContextBundle,
    warning: str,
    config: AppConfig,
    attempt_count: int = 0,
    fallback_type: str = "insufficient_evidence",
) -> GeneratedAnswer:
    technical_failure = fallback_type != "insufficient_evidence"
    return GeneratedAnswer(
        query=context.query,
        answer=(
            "تعذر توليد الإجابة بسبب مشكلة تقنية في خدمة التوليد، رغم توفر أدلة مسترجعة. يُرجى المحاولة لاحقاً."
            if technical_failure
            else "لا توجد أدلة كافية في الرسم الطبي للإجابة بثقة. يُنصح باستشارة طبيب مختص."
        ),
        limitations=[
            "لم تُنشأ إجابة طبية؛ هذا فشل تقني وليس حكماً بعدم كفاية الأدلة."
            if technical_failure
            else "الأدلة المسترجعة غير كافية لتوليد إجابة موثوقة."
        ],
        model=config.answer_generation.model,
        prompt_version=config.answer_generation.prompt_version,
        generation_status="fallback",
        fallback_type=fallback_type,
        fallback_reason=warning,
        attempt_count=attempt_count,
        warnings=[*context.warnings, warning],
    )


def build_messages(context: EvidenceContextBundle) -> list[dict[str, str]]:
    payload = {
        "query": context.query,
        "reformulated_query": context.reformulated_query,
        "graph_facts": context.graph_facts,
        "evidence_items": context.evidence_items,
        "allowed_evidence_ids": context.allowed_evidence_ids,
        "allowed_qa_ids": context.allowed_qa_ids,
        "rules": [
            "Answer in Arabic using only the supplied graph facts and evidence items.",
            "Do not add outside medical knowledge or infer a diagnosis.",
            "Every factual medical claim must cite at least one allowed evidence_id.",
            "Keep claims atomic: separate different organs, tests, treatments, causes, and recommendations into different claims.",
            "Copy QA IDs exactly; never invent citations, QA IDs, ages, durations, doses, or test values.",
            "When evidence is insufficient or conflicting, state that limitation clearly.",
            "Limitations may only state that evidence is incomplete; never name uncited treatments, tests, diseases, doses, or alternatives there.",
            "Do not present this output as a substitute for examination by a qualified clinician.",
        ],
        "required_json": {
            "answer_ar": "concise grounded Arabic answer",
            "claims": [
                {
                    "claim_ar": "one atomic factual medical claim",
                    "citations": ["E1"],
                    "source_qa_ids": ["exact QA ID"],
                }
            ],
            "used_relation_ids": ["R1"],
            "limitations_ar": ["explicit limitation"],
        },
    }
    return [
        {
            "role": "system",
            "content": "You generate evidence-grounded Arabic medical answers. Return one strict JSON object only.",
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
) -> GeneratedAnswer:
    required = {"answer_ar", "claims", "used_relation_ids", "limitations_ar"}
    missing = sorted(required - payload.keys())
    if missing:
        raise ValueError(f"Missing answer fields: {', '.join(missing)}")
    if not isinstance(payload["answer_ar"], str) or not payload["answer_ar"].strip():
        raise ValueError("answer_ar must be a non-empty string.")
    if not isinstance(payload["claims"], list):
        raise ValueError("claims must be a list.")
    if not isinstance(payload["used_relation_ids"], list):
        raise ValueError("used_relation_ids must be a list.")
    if not isinstance(payload["limitations_ar"], list):
        raise ValueError("limitations_ar must be a list.")

    allowed_evidence = set(context.allowed_evidence_ids)
    allowed_qa = set(context.allowed_qa_ids)
    allowed_relations = {str(item.get("relation_id") or "") for item in context.graph_facts}
    warnings = list(context.warnings)
    claims: list[AnswerClaim] = []
    seen: set[str] = set()
    for index, item in enumerate(payload["claims"], start=1):
        if not isinstance(item, dict):
            warnings.append(f"Skipped claim {index}: claim is not an object.")
            continue
        claim = str(item.get("claim_ar") or "").strip()
        citations_raw = item.get("citations") or []
        qa_raw = item.get("source_qa_ids") or []
        if not claim or not isinstance(citations_raw, list) or not isinstance(qa_raw, list):
            warnings.append(f"Skipped claim {index}: malformed text or source lists.")
            continue
        citations = [str(value) for value in citations_raw if str(value) in allowed_evidence]
        qa_ids = [str(value) for value in qa_raw if str(value) in allowed_qa]
        if len(citations) != len(citations_raw):
            warnings.append(f"Claim {index}: removed invented or unavailable evidence citations.")
        if len(qa_ids) != len(qa_raw):
            warnings.append(f"Claim {index}: removed invented or unavailable QA IDs.")
        normalized = " ".join(claim.split())
        if normalized not in seen:
            claims.append(AnswerClaim(claim=normalized, citations=citations, source_qa_ids=qa_ids))
            seen.add(normalized)

    used_relations = [
        str(value) for value in payload["used_relation_ids"] if str(value) in allowed_relations
    ]
    raw_limitations = [str(value).strip() for value in payload["limitations_ar"] if str(value).strip()]
    # Model-written limitations can otherwise smuggle in uncited medical facts.
    # Keep the signal that evidence was limited, but render it with fixed wording.
    limitations = (
        ["الإجابة محدودة بالأدلة المسترجعة ولا تمثل خطة علاج كاملة."]
        if raw_limitations
        else []
    )
    return GeneratedAnswer(
        query=context.query,
        answer=payload["answer_ar"].strip(),
        claims=claims,
        used_relations=list(dict.fromkeys(used_relations)),
        limitations=limitations,
        model=config.answer_generation.model,
        prompt_version=config.answer_generation.prompt_version,
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


def generate_grounded_answer(
    context: EvidenceContextBundle,
    config: AppConfig | None = None,
) -> GeneratedAnswer:
    config = config or load_final_config()
    if not context.evidence_items:
        return fallback_answer(context, "Generation skipped because no evidence was retrieved.", config)
    answer_config = config.answer_generation
    if answer_config.provider != "groq":
        return fallback_answer(
            context,
            f"Unsupported answer provider: {answer_config.provider}",
            config,
            fallback_type="configuration_error",
        )
    if not answer_config.groq_api_key:
        return fallback_answer(
            context,
            "GROQ_API_KEY is not configured.",
            config,
            fallback_type="configuration_error",
        )

    body: dict[str, Any] = {
        "model": answer_config.model,
        "messages": build_messages(context),
        "temperature": answer_config.temperature,
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "grounded_medical_answer",
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
    attempts_made = 0
    for attempt in range(1, max_attempts + 1):
        attempts_made = attempt
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                response_payload = json.loads(response.read().decode("utf-8"))
            payload = parse_json_object(response_payload["choices"][0]["message"]["content"])
            return validate_answer_payload(payload, context, config, attempt_count=attempt)
        except Exception as exc:
            last_error = exc
            if attempt >= max_attempts or not retryable_generation_error(exc):
                break
            time.sleep(retry_delay_seconds(exc, attempt, config))

    error_name = type(last_error).__name__ if last_error else "UnknownError"
    if isinstance(last_error, urllib.error.HTTPError):
        error_name = f"HTTPError {last_error.code}"
    return fallback_answer(
        context,
        f"Grounded answer generation failed after {attempts_made} attempt(s): {error_name}",
        config,
        attempt_count=attempts_made,
        fallback_type="technical_failure",
    )
