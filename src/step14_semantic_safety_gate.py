from __future__ import annotations

"""Deterministic safety checks for claims rescued by semantic adjudication.

These checks are deliberately narrow. They do not decide that a claim is
supported; they can only veto a semantic retain decision when a material detail
is visibly absent from the cited evidence.
"""

import re
import unicodedata
from collections.abc import Sequence

from src.step08a_normalize_query import normalize_query


ARABIC_OR_LATIN_TOKEN_RE = re.compile(r"[\u0621-\u064a]+|[A-Za-z0-9-]+")
PARENTHETICAL_IDENTIFIER_RE = re.compile(
    r"\(([A-Za-z][A-Za-z0-9-]{1,})\)"
)
CONDITION_MARKERS = ("في حال", "بشرط", "اذا", "عند")
DIRECTION_TERMS = {
    "ارتفاع",
    "انخفاض",
    "تحسين",
    "خفض",
    "رفع",
    "زياده",
    "يخفض",
    "يرفع",
    "يزيد",
    "يقلل",
}
BARE_REASSURANCE = {
    "اطمين",
    "اطميني",
    "لا داعي للقلق",
    "لا تقلق",
    "لا تقلقي",
}
CONTENT_STOPWORDS = {
    "اكثر",
    "اقل",
    "اذا",
    "التي",
    "الذي",
    "الي",
    "الى",
    "ان",
    "او",
    "اي",
    "بعض",
    "بشرط",
    "بها",
    "به",
    "بين",
    "ثم",
    "حتي",
    "حتى",
    "خلال",
    "علي",
    "على",
    "عن",
    "عند",
    "في",
    "قد",
    "كان",
    "كانت",
    "لدي",
    "لدى",
    "لكن",
    "ما",
    "مع",
    "من",
    "هذا",
    "هذه",
    "هناك",
    "هو",
    "هي",
    "وجود",
}


def _normal(text: str) -> str:
    return normalize_query(text).normalized_query


def _canonical_token(token: str) -> str:
    value = token.lower().strip("-")
    if value.startswith("وال") and len(value) > 5:
        value = value[3:]
    elif value.startswith("بال") and len(value) > 5:
        value = value[3:]
    elif value.startswith("ال") and len(value) > 4:
        value = value[2:]
    elif value.startswith("و") and len(value) > 4:
        value = value[1:]
    return value


def _tokens(text: str) -> list[str]:
    return [
        canonical
        for token in ARABIC_OR_LATIN_TOKEN_RE.findall(_normal(text))
        if (canonical := _canonical_token(token))
    ]


def _content_tokens(text: str) -> list[str]:
    return [
        token
        for token in _tokens(text)
        if token not in CONTENT_STOPWORDS and not token.isdigit()
    ]


def _combined_evidence(evidence_segments: Sequence[str]) -> str:
    return " ".join(str(item or "").strip() for item in evidence_segments)


def _unsupported_parenthetical_identifier(
    claim: str,
    evidence: str,
) -> bool:
    evidence_ascii = unicodedata.normalize("NFKC", evidence).lower()
    identifiers = PARENTHETICAL_IDENTIFIER_RE.findall(
        unicodedata.normalize("NFKC", claim)
    )
    return any(identifier.lower() not in evidence_ascii for identifier in identifiers)


def _bare_reassurance(claim: str) -> bool:
    normalized = _normal(claim).strip(" .,!?:;")
    return normalized in BARE_REASSURANCE


def _condition_clause(claim: str) -> str:
    normalized = _normal(claim)
    matches = [
        match
        for marker in CONDITION_MARKERS
        if (
            match := re.search(
                rf"(?<!\S){re.escape(marker)}(?!\S)",
                normalized,
            )
        )
    ]
    if not matches:
        return ""
    match = min(matches, key=lambda item: item.start())
    return normalized[match.end() :]


def _unsupported_condition(claim: str, evidence: str) -> bool:
    condition = _condition_clause(claim)
    # A generic umbrella such as "other symptoms" may be supported by an
    # evidence list of concrete symptoms even without lexical overlap.
    if re.search(r"\bب?اعراض\s+(?:اخري|اخرى)\b", condition):
        return False
    condition_tokens = set(_content_tokens(condition))
    if len(condition_tokens) < 2:
        return False
    evidence_tokens = set(_content_tokens(evidence))
    coverage = len(condition_tokens & evidence_tokens) / len(condition_tokens)
    return coverage < 0.50


def _unsupported_directional_outcome(claim: str, evidence: str) -> bool:
    claim_tokens = _tokens(claim)
    direction_indices = [
        index
        for index, token in enumerate(claim_tokens)
        if token in DIRECTION_TERMS
    ]
    if not direction_indices:
        return False
    # The final directional predicate normally governs the claimed outcome.
    outcome_tokens = {
        token
        for token in claim_tokens[direction_indices[-1] + 1 :]
        if token not in CONTENT_STOPWORDS and not token.isdigit()
    }
    if len(outcome_tokens) < 2:
        return False
    evidence_tokens = set(_content_tokens(evidence))
    return not bool(outcome_tokens & evidence_tokens)


def semantic_rescue_safety_failures(
    claim: str,
    evidence_segments: Sequence[str],
) -> list[str]:
    """Return non-overridable failures for a semantic retain candidate."""
    evidence = _combined_evidence(evidence_segments)
    failures: list[str] = []
    if _bare_reassurance(claim):
        failures.append("bare_reassurance_without_medical_answer")
    if _unsupported_parenthetical_identifier(claim, evidence):
        failures.append("unsupported_parenthetical_identifier")
    if _unsupported_condition(claim, evidence):
        failures.append("unsupported_condition_scope")
    if _unsupported_directional_outcome(claim, evidence):
        failures.append("unsupported_directional_outcome")
    return failures
