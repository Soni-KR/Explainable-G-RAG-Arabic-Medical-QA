from __future__ import annotations

"""Shared, interpretable query-to-candidate relevance features.

The production pipeline, human annotation queue, and future supervised reranker
must measure the same concepts.  This module deliberately avoids model calls and
does not assign relevance labels; it only exposes deterministic features.
"""

import re
from collections.abc import Iterable
from difflib import SequenceMatcher

from src.evidence_policy import source_reliability_prior
from src.step09_hybrid_retrieval import anatomy_terms, medical_identity_tokens, normalized_content_terms


NUMBER_RE = re.compile(r"\d+(?:[.,]\d+)?")

# Constraints matter clinically but are not always entity names.  Keeping them
# separate prevents a passage that mentions the right disease but the wrong age,
# duration, laterality, or polarity from looking fully query-specific.
CONSTRAINT_TERMS = {
    "منذ",
    "مستمر",
    "مستمره",
    "متكرر",
    "متكرره",
    "سابق",
    "سابقه",
    "طبيعي",
    "طبيعيه",
    "سلبي",
    "سلبيه",
    "ايجابي",
    "ايجابيه",
    "يمين",
    "يسار",
    "ايمن",
    "ايسر",
    "طفل",
    "طفلي",
    "رضيع",
    "حامل",
    "حمل",
    "رجل",
    "امراه",
    "ذكر",
    "انثي",
    "يوم",
    "ايام",
    "اسبوع",
    "اسابيع",
    "شهر",
    "شهور",
    "سنه",
    "سنوات",
    "عمر",
    "لا",
    "ليس",
    "ليست",
    "لم",
    "لن",
    "بدون",
    "غير",
}

# Small, conservative equivalence families improve Arabic wording coverage without
# turning semantic association into identity.  Every pair denotes the same concept.
CONCEPT_EQUIVALENTS = {
    "نظر": "نظر",
    "رؤيه": "نظر",
    "بصر": "نظر",
    "فمويه": "فم",
    "فموي": "فم",
    "كحه": "سعال",
    "دوار": "دوخه",
}


def _near_match(term: str, candidates: set[str]) -> bool:
    if term in candidates:
        return True
    return any(SequenceMatcher(None, term, candidate).ratio() >= 0.92 for candidate in candidates)


def _canonical_concepts(text: str) -> set[str]:
    return {
        CONCEPT_EQUIVALENTS.get(term, term)
        for term in (medical_identity_tokens(text) | anatomy_terms(text))
    }


def query_concepts(
    text: str,
    medical_phrases: Iterable[str] | None = None,
) -> set[str]:
    """Return query-denominated medical identity terms, not broad intent words."""
    phrases = [str(item or "").strip() for item in (medical_phrases or []) if str(item or "").strip()]
    if phrases:
        return set().union(*(_canonical_concepts(phrase) for phrase in phrases))
    return _canonical_concepts(text)


def matched_query_concepts(
    query: str,
    candidate: str,
    medical_phrases: Iterable[str] | None = None,
) -> set[str]:
    candidate_terms = _canonical_concepts(candidate)
    return {
        term
        for term in query_concepts(query, medical_phrases)
        if _near_match(term, candidate_terms)
    }


def query_concept_coverage(
    query: str,
    candidate: str,
    medical_phrases: Iterable[str] | None = None,
) -> float:
    concepts = query_concepts(query, medical_phrases)
    if not concepts:
        return 1.0
    return len(matched_query_concepts(query, candidate, medical_phrases)) / len(concepts)


def candidate_concept_precision(
    query: str,
    candidate: str,
    medical_phrases: Iterable[str] | None = None,
) -> float:
    candidate_terms = _canonical_concepts(candidate)
    if not candidate_terms:
        return 0.0
    matched = matched_query_concepts(query, candidate, medical_phrases)
    return len(matched) / len(candidate_terms)


def constraint_terms(text: str) -> set[str]:
    terms = normalized_content_terms(text)
    constraints = terms & CONSTRAINT_TERMS
    constraints.update(f"number:{value}" for value in NUMBER_RE.findall(text or ""))
    return constraints


def query_constraint_coverage(query: str, candidate: str) -> float:
    required = constraint_terms(query)
    if not required:
        return 1.0
    available = constraint_terms(candidate)
    return len(required & available) / len(required)


def minimum_candidate_concept_coverage(concept_count: int) -> float:
    """Require at least one query concept; Step 11 checks aggregate coverage too."""
    if concept_count <= 0:
        return 0.0
    return 1.0 / concept_count


def missing_query_concepts(
    query: str,
    candidate: str,
    medical_phrases: Iterable[str] | None = None,
) -> list[str]:
    return sorted(
        query_concepts(query, medical_phrases)
        - matched_query_concepts(query, candidate, medical_phrases)
    )


def candidate_relevance_features(
    query: str,
    candidate: str,
    *,
    source_quality: str = "unknown",
    intent_support: float = 0.0,
    vector_similarity: float = 0.0,
    graph_support: float = 0.0,
    retrieval_score: float = 0.0,
    query_medical_phrases: Iterable[str] | None = None,
) -> dict[str, object]:
    """Build features shared by rules, annotations, and supervised reranking."""
    concepts = query_concepts(query, query_medical_phrases)
    candidate_concepts = _canonical_concepts(candidate)
    matched = matched_query_concepts(query, candidate, query_medical_phrases)
    query_anatomy = anatomy_terms(query)
    candidate_anatomy = anatomy_terms(candidate)
    anatomy_mismatch = bool(
        query_anatomy and candidate_anatomy and query_anatomy.isdisjoint(candidate_anatomy)
    )
    concept_coverage = len(matched) / len(concepts) if concepts else 1.0
    concept_precision = len(matched) / len(candidate_concepts) if candidate_concepts else 0.0
    unrelated_condition_mismatch = bool(
        concepts
        and candidate_concepts
        and not matched
        and float(vector_similarity or 0.0) < 0.90
    )
    return {
        "query_concept_count": len(concepts),
        "candidate_concept_count": len(candidate_concepts),
        "matched_query_concepts": sorted(matched),
        "missing_query_concepts": sorted(concepts - matched),
        "query_concept_coverage": round(concept_coverage, 6),
        "candidate_concept_precision": round(concept_precision, 6),
        "query_constraint_coverage": round(query_constraint_coverage(query, candidate), 6),
        "query_anatomy": sorted(query_anatomy),
        "candidate_anatomy": sorted(candidate_anatomy),
        "anatomy_mismatch": anatomy_mismatch,
        "unrelated_condition_mismatch": unrelated_condition_mismatch,
        "source_reliability": round(source_reliability_prior(source_quality), 6),
        "intent_support": round(max(0.0, min(1.0, float(intent_support or 0.0))), 6),
        "vector_similarity": round(max(0.0, min(1.0, float(vector_similarity or 0.0))), 6),
        "graph_support": round(max(0.0, min(1.0, float(graph_support or 0.0))), 6),
        "retrieval_score": round(max(0.0, min(1.0, float(retrieval_score or 0.0))), 6),
    }
