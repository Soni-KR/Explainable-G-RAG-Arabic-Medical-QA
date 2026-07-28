from __future__ import annotations

"""Selective semantic review for claims rejected by soft lexical gates.

The deterministic verifier remains the first and fallback authority. This
module only reviews claims whose evidence score passed and whose remaining
failures are limited to intent, concept, or anatomy heuristics.
"""

import hashlib
import json
import re
import time
import urllib.error
import urllib.request
from dataclasses import asdict, replace
from pathlib import Path
from time import monotonic, sleep
from typing import Any

from src.config import AppConfig, ClaimAdjudicationConfig
from src.evidence_policy import authoritative_evidence_texts
from src.models import (
    ClaimVerification,
    EvidenceContextBundle,
    SemanticClaimDecision,
)
from src.step12_generate_grounded_answer import (
    GROQ_CHAT_COMPLETIONS_URL,
    describe_http_error,
    parse_json_object,
)
from src.step14_verify_claims import evidence_candidates, support_score


SOFT_ADJUDICATION_CHECKS = {
    "intent_mismatch",
    "claim_query_concept_mismatch",
    "anatomy_mismatch",
}
EVIDENCE_SUPPORT_VALUES = {"supported", "partial", "unsupported"}
QUERY_RELEVANCE_VALUES = {"relevant", "partially_relevant", "irrelevant"}
ANATOMY_MATCH_VALUES = {"yes", "no", "not_applicable"}
ANSWER_CONTRIBUTION_VALUES = {
    "direct_answer",
    "partial_answer",
    "generic_advice",
    "restatement",
    "unrelated",
}
EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
URL_RE = re.compile(r"\b(?:https?://|www\.)\S+", re.IGNORECASE)
PHONE_OR_ID_RE = re.compile(r"(?<!\w)\+?(?:\d[\s().-]?){7,}\d(?!\w)")

ADJUDICATION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "decisions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "claim_id": {"type": "string"},
                    "evidence_support": {
                        "type": "string",
                        "enum": sorted(EVIDENCE_SUPPORT_VALUES),
                    },
                    "query_relevance": {
                        "type": "string",
                        "enum": sorted(QUERY_RELEVANCE_VALUES),
                    },
                    "intent_match": {"type": "boolean"},
                    "concept_match": {"type": "boolean"},
                    "anatomy_match": {
                        "type": "string",
                        "enum": sorted(ANATOMY_MATCH_VALUES),
                    },
                    "answer_contribution": {
                        "type": "string",
                        "enum": sorted(ANSWER_CONTRIBUTION_VALUES),
                    },
                    "clinical_relation_preserved": {"type": "boolean"},
                    "named_entity_identity_preserved": {"type": "boolean"},
                    "patient_context_compatible": {"type": "boolean"},
                    "should_retain": {"type": "boolean"},
                    "reason": {"type": "string"},
                },
                "required": [
                    "claim_id",
                    "evidence_support",
                    "query_relevance",
                    "intent_match",
                    "concept_match",
                    "anatomy_match",
                    "answer_contribution",
                    "clinical_relation_preserved",
                    "named_entity_identity_preserved",
                    "patient_context_compatible",
                    "should_retain",
                    "reason",
                ],
                "additionalProperties": False,
            },
        }
    },
    "required": ["decisions"],
    "additionalProperties": False,
}


class ClaimAdjudicationError(RuntimeError):
    """Base exception for a failed semantic adjudication request."""


class ClaimAdjudicationRateLimit(ClaimAdjudicationError):
    """Raised immediately when Groq reports HTTP 429."""


def eligible_for_semantic_adjudication(
    verification: ClaimVerification,
    *,
    support_floor: float = 0.40,
) -> bool:
    """Return true only for evidence-bearing soft-gate disputes."""
    failures = set(verification.failed_checks)
    return bool(
        verification.status == "unsupported"
        and verification.best_evidence_id
        and verification.support_score >= support_floor
        and failures
        and failures.issubset(SOFT_ADJUDICATION_CHECKS)
    )


def _best_evidence_segments(
    claim: str,
    row: dict[str, Any],
    relation_facts: list[str],
    *,
    limit: int = 4,
    max_chars: int = 1800,
) -> list[str]:
    """Keep the most claim-relevant cited segments and bound prompt size."""
    text_fields, _, _ = authoritative_evidence_texts(row, relation_facts)
    segments = {
        segment.strip()
        for text in text_fields
        for segment in evidence_candidates(text, claim)
        if segment.strip()
    }
    ranked = sorted(
        segments,
        key=lambda segment: (support_score(claim, segment), len(segment)),
        reverse=True,
    )
    return [segment[:max_chars] for segment in ranked[:limit]]


def build_adjudication_cases(
    verifications: list[ClaimVerification],
    context: EvidenceContextBundle,
    *,
    support_floor: float = 0.40,
) -> tuple[list[dict[str, Any]], dict[str, ClaimVerification]]:
    """Build one compact, citation-scoped case for every eligible claim."""
    evidence_by_id = {
        str(item.get("evidence_id") or ""): item for item in context.evidence_items
    }
    facts_by_id = {
        str(item.get("relation_id") or ""): str(item.get("fact") or "")
        for item in context.graph_facts
    }
    cases: list[dict[str, Any]] = []
    verification_by_claim_id: dict[str, ClaimVerification] = {}
    for verification in verifications:
        if not eligible_for_semantic_adjudication(verification):
            continue
        row = evidence_by_id.get(verification.best_evidence_id)
        if not row:
            continue
        relation_facts = [
            facts_by_id.get(str(relation_id), "")
            for relation_id in row.get("relation_ids", [])
            if facts_by_id.get(str(relation_id), "")
        ]
        segments = _best_evidence_segments(
            verification.claim.claim,
            row,
            relation_facts,
        )
        # A legacy verification score may have been calculated from a source
        # question before provenance metadata was available. Recheck the score
        # using only authoritative answer/relation segments before any API call.
        if (
            not segments
            or max(
                support_score(verification.claim.claim, segment)
                for segment in segments
            )
            < support_floor
        ):
            continue
        claim_id = f"C{len(cases) + 1}"
        cases.append(
            {
                "claim_id": claim_id,
                "claim": verification.claim.claim,
                "evidence_segments": segments,
            }
        )
        verification_by_claim_id[claim_id] = verification
    return cases, verification_by_claim_id


def build_messages(
    context: EvidenceContextBundle,
    cases: list[dict[str, Any]],
) -> list[dict[str, str]]:
    """Create a strict semantic-verification prompt without human labels."""
    system = """
You are a strict Arabic medical claim adjudicator. False acceptance is more
harmful than rejecting an uncertain claim.

For each claim, use only its cited evidence segments. The source question is
context, not factual evidence.

Decide these dimensions independently:
- evidence_support=supported only when the complete claim is explicitly
  entailed by the evidence. Use partial when only part is supported.
- query_relevance=relevant only when the claim directly helps answer the user.
- intent_match=true only when the claim answers the requested information type.
- concept_match=true only when diseases, symptoms, drugs, tests and their
  relationships match the query.
- anatomy_match=no for a wrong body location or a wrong named clinical entity;
  otherwise use yes or not_applicable.
- answer_contribution=direct_answer only when the claim materially answers the
  user's requested information. Use restatement when it merely repeats the
  symptoms/history, generic_advice for non-specific follow-up language,
  partial_answer for useful but incomplete information, and unrelated when it
  does not answer this case.
- clinical_relation_preserved=true only when the claim preserves the exact
  relationship in the evidence. A list of heart-disease categories or affected
  structures is not a list of causes. Possibility is not diagnosis; association
  is not causation; symptom relief is not cure.
- named_entity_identity_preserved=true only when every explicit drug, disease,
  test, and anatomy identity is compatible across query, claim, and evidence.
  Similar drugs are not interchangeable. For example, azithromycin and
  erythromycin must be treated as different named drugs.
- patient_context_compatible=true only when the cited passage applies to the
  user's condition and clinical situation. Evidence about a different disease,
  drug, anatomy, demographic, or scenario is incompatible unless the claim is
  explicitly general and directly applicable.

Reject:
- user-question restatements that add no answer;
- generic reassurance or follow-up advice that does not answer the query;
- partial support presented as a complete fact;
- changed causal or diagnostic relationships;
- merged alternatives presented as one treatment;
- wrong drugs, diseases, anatomy, negation, quantities or recommendation scope.

should_retain must be true only when evidence_support is supported,
query_relevance is relevant, intent_match and concept_match are true, and
anatomy_match is not no, answer_contribution is direct_answer,
clinical_relation_preserved is true, named_entity_identity_preserved is true,
and patient_context_compatible is true. If any required judgment is uncertain,
set should_retain=false. Do not answer the medical question. Return only the
required JSON.
""".strip()
    def redact(text: str) -> str:
        value = EMAIL_RE.sub("[REDACTED_EMAIL]", text)
        value = URL_RE.sub("[REDACTED_URL]", value)
        return PHONE_OR_ID_RE.sub("[REDACTED_IDENTIFIER]", value)

    user_payload = {
        "query": redact(context.query),
        "claims": [
            {
                "claim_id": str(case["claim_id"]),
                "claim": redact(str(case["claim"])),
                "evidence_segments": [
                    redact(str(segment))
                    for segment in case.get("evidence_segments", [])
                ],
            }
            for case in cases
        ],
    }
    return [
        {"role": "system", "content": system},
        {
            "role": "user",
            "content": json.dumps(user_payload, ensure_ascii=False),
        },
    ]


def validate_response(
    payload: dict[str, Any],
    expected_claim_ids: set[str],
    config: ClaimAdjudicationConfig,
) -> list[SemanticClaimDecision]:
    """Reject missing, duplicate, inconsistent, or malformed decisions."""
    raw_decisions = payload.get("decisions")
    if not isinstance(raw_decisions, list):
        raise ValueError("Semantic adjudication response lacks decisions list.")
    decisions: list[SemanticClaimDecision] = []
    seen: set[str] = set()
    for raw in raw_decisions:
        if not isinstance(raw, dict):
            raise ValueError("Each semantic adjudication decision must be an object.")
        claim_id = str(raw.get("claim_id") or "").strip()
        evidence_support = str(raw.get("evidence_support") or "").strip()
        query_relevance = str(raw.get("query_relevance") or "").strip()
        anatomy_match = str(raw.get("anatomy_match") or "").strip()
        answer_contribution = str(
            raw.get("answer_contribution") or ""
        ).strip()
        intent_match = raw.get("intent_match")
        concept_match = raw.get("concept_match")
        clinical_relation_preserved = raw.get(
            "clinical_relation_preserved"
        )
        named_entity_identity_preserved = raw.get(
            "named_entity_identity_preserved"
        )
        patient_context_compatible = raw.get(
            "patient_context_compatible"
        )
        should_retain = raw.get("should_retain")
        reason = " ".join(str(raw.get("reason") or "").split()).strip()
        if claim_id not in expected_claim_ids or claim_id in seen:
            raise ValueError(f"Unexpected or duplicate claim_id: {claim_id!r}")
        if evidence_support not in EVIDENCE_SUPPORT_VALUES:
            raise ValueError(f"Invalid evidence_support for {claim_id}.")
        if query_relevance not in QUERY_RELEVANCE_VALUES:
            raise ValueError(f"Invalid query_relevance for {claim_id}.")
        if anatomy_match not in ANATOMY_MATCH_VALUES:
            raise ValueError(f"Invalid anatomy_match for {claim_id}.")
        if answer_contribution not in ANSWER_CONTRIBUTION_VALUES:
            raise ValueError(f"Invalid answer_contribution for {claim_id}.")
        if not all(
            isinstance(value, bool)
            for value in (
                intent_match,
                concept_match,
                clinical_relation_preserved,
                named_entity_identity_preserved,
                patient_context_compatible,
                should_retain,
            )
        ):
            raise ValueError(f"Boolean fields are malformed for {claim_id}.")
        expected_retain = bool(
            evidence_support == "supported"
            and query_relevance == "relevant"
            and intent_match
            and concept_match
            and anatomy_match != "no"
            and answer_contribution == "direct_answer"
            and clinical_relation_preserved
            and named_entity_identity_preserved
            and patient_context_compatible
        )
        # Python is the final authority. A contradictory model summary can
        # only turn into a rejection; it can never bypass a failed dimension.
        if should_retain != expected_retain:
            should_retain = False
            reason = (
                f"{reason} Python fail-closed: the summary flag conflicted "
                "with the structured dimensions."
            )
        if not reason:
            raise ValueError(f"Missing adjudication reason for {claim_id}.")
        seen.add(claim_id)
        decisions.append(
            SemanticClaimDecision(
                claim_id=claim_id,
                evidence_support=evidence_support,
                query_relevance=query_relevance,
                intent_match=intent_match,
                concept_match=concept_match,
                anatomy_match=anatomy_match,
                answer_contribution=answer_contribution,
                clinical_relation_preserved=clinical_relation_preserved,
                named_entity_identity_preserved=(
                    named_entity_identity_preserved
                ),
                patient_context_compatible=patient_context_compatible,
                should_retain=should_retain,
                reason=reason[:500],
                model=config.model,
                prompt_version=config.prompt_version,
            )
        )
    if seen != expected_claim_ids:
        missing = sorted(expected_claim_ids - seen)
        raise ValueError(f"Semantic adjudication omitted claim IDs: {missing}")
    return decisions


def adjudication_fingerprint(
    context: EvidenceContextBundle,
    cases: list[dict[str, Any]],
    config: ClaimAdjudicationConfig,
) -> str:
    payload = {
        "query": context.query,
        "reformulated_query": context.reformulated_query,
        "primary_intent": context.primary_intent,
        "cases": cases,
        "model": config.model,
        "prompt_version": config.prompt_version,
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _load_cache(path: Path | None) -> dict[str, dict[str, Any]]:
    if path is None or not path.exists():
        return {}
    cache: dict[str, dict[str, Any]] = {}
    with path.open("r", encoding="utf-8-sig") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            fingerprint = str(row.get("fingerprint") or "")
            if fingerprint and row.get("status") == "ok":
                cache[fingerprint] = row
    return cache


def _append_cache(path: Path | None, row: dict[str, Any]) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")
        handle.flush()


class SemanticClaimAdjudicator:
    """Stateful, paced, append-only semantic adjudication client."""

    def __init__(
        self,
        config: AppConfig,
        *,
        cache_path: Path | None = None,
        raise_on_error: bool = False,
    ) -> None:
        self.app_config = config
        self.config = config.claim_adjudication
        self.cache_path = cache_path
        self.raise_on_error = raise_on_error
        self.cache = _load_cache(cache_path)
        self.last_request_at: float | None = None
        self.api_calls = 0
        self.cache_hits = 0

    def _wait(self) -> None:
        interval = max(0.0, self.config.request_interval_seconds)
        if self.last_request_at is not None:
            remaining = interval - (monotonic() - self.last_request_at)
            if remaining > 0:
                sleep(remaining)
        self.last_request_at = monotonic()

    def _call_api(
        self,
        context: EvidenceContextBundle,
        cases: list[dict[str, Any]],
    ) -> list[SemanticClaimDecision]:
        if self.config.provider != "groq":
            raise ClaimAdjudicationError(
                f"Unsupported claim adjudication provider: {self.config.provider}"
            )
        if not self.config.groq_api_key:
            raise ClaimAdjudicationError("GROQ_API_KEY is not configured.")
        body: dict[str, Any] = {
            "model": self.config.model,
            "messages": build_messages(context, cases),
            "temperature": self.config.temperature,
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "semantic_claim_adjudication",
                    "strict": True,
                    "schema": ADJUDICATION_SCHEMA,
                },
            },
        }
        if self.config.reasoning_effort:
            body["reasoning_effort"] = self.config.reasoning_effort
        request = urllib.request.Request(
            GROQ_CHAT_COMPLETIONS_URL,
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.config.groq_api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "AHD-GraphRAG/1.0",
            },
            method="POST",
        )
        last_error: Exception | None = None
        for attempt in range(1, max(1, self.config.max_attempts) + 1):
            self._wait()
            self.api_calls += 1
            try:
                with urllib.request.urlopen(request, timeout=120) as response:
                    response_payload = json.loads(response.read().decode("utf-8"))
                parsed = parse_json_object(
                    response_payload["choices"][0]["message"]["content"]
                )
                return validate_response(
                    parsed,
                    {str(case["claim_id"]) for case in cases},
                    self.config,
                )
            except urllib.error.HTTPError as exc:
                detail = describe_http_error(exc)
                if exc.code == 429:
                    raise ClaimAdjudicationRateLimit(detail) from exc
                last_error = ClaimAdjudicationError(detail)
            except Exception as exc:
                last_error = exc
            if attempt < max(1, self.config.max_attempts):
                time.sleep(min(2.0**attempt, 8.0))
        raise ClaimAdjudicationError(
            f"Semantic claim adjudication failed: {last_error or 'unknown error'}"
        )

    def adjudicate(
        self,
        verifications: list[ClaimVerification],
        context: EvidenceContextBundle,
    ) -> tuple[list[ClaimVerification], dict[str, Any]]:
        cases, verification_by_claim_id = build_adjudication_cases(
            verifications,
            context,
        )
        audit: dict[str, Any] = {
            "enabled": self.config.enabled,
            "eligible_claims": len(cases),
            "adjudicated_claims": 0,
            "retained_claims": 0,
            "cache_hit": False,
            "model": self.config.model,
            "prompt_version": self.config.prompt_version,
            "error": "",
            "decisions": [],
        }
        if not self.config.enabled or not cases:
            return verifications, audit
        fingerprint = adjudication_fingerprint(context, cases, self.config)
        try:
            cached = self.cache.get(fingerprint)
            if cached:
                decisions = validate_response(
                    dict(cached.get("response") or {}),
                    set(verification_by_claim_id),
                    self.config,
                )
                decisions = [replace(item, cached=True) for item in decisions]
                self.cache_hits += 1
                audit["cache_hit"] = True
            else:
                decisions = self._call_api(context, cases)
                response = {
                    "decisions": [
                        {
                            key: value
                            for key, value in asdict(item).items()
                            if key not in {"model", "prompt_version", "cached"}
                        }
                        for item in decisions
                    ]
                }
                cache_row = {
                    "fingerprint": fingerprint,
                    "status": "ok",
                    "query": context.query,
                    "model": self.config.model,
                    "prompt_version": self.config.prompt_version,
                    "response": response,
                }
                _append_cache(self.cache_path, cache_row)
                self.cache[fingerprint] = cache_row
        except Exception as exc:
            audit["error"] = str(exc)
            if self.raise_on_error:
                raise
            return verifications, audit

        evidence_by_id = {
            str(item.get("evidence_id") or ""): item
            for item in context.evidence_items
        }
        decision_by_claim = {
            verification_by_claim_id[item.claim_id].claim.claim: item
            for item in decisions
        }
        updated: list[ClaimVerification] = []
        for verification in verifications:
            decision = decision_by_claim.get(verification.claim.claim)
            if decision is None or not decision.should_retain:
                updated.append(verification)
                continue
            row = evidence_by_id.get(verification.best_evidence_id, {})
            qa_id = str(row.get("qa_id") or "")
            valid_qa_ids = [
                item
                for item in verification.claim.source_qa_ids
                if item in context.allowed_qa_ids and item == qa_id
            ]
            relation_ids = [
                str(item)
                for item in row.get("relation_ids", [])
                if str(item)
            ]
            updated.append(
                replace(
                    verification,
                    status="supported",
                    valid_citations=[verification.best_evidence_id],
                    valid_qa_ids=valid_qa_ids,
                    supporting_relation_ids=list(dict.fromkeys(relation_ids)),
                    failed_checks=[],
                    reason=(
                        "Semantic adjudication retained this evidence-supported "
                        f"claim: {decision.reason}"
                    ),
                )
            )
        audit["adjudicated_claims"] = len(decisions)
        audit["retained_claims"] = sum(item.should_retain for item in decisions)
        audit["decisions"] = [asdict(item) for item in decisions]
        return updated, audit
