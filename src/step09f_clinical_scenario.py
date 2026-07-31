from __future__ import annotations

"""Deterministic clinical-scenario compatibility for QA retrieval.

The checker compares the user's query with the source question attached to an
AHD answer. It rejects only explicit conflicts and otherwise returns a graded,
auditable compatibility score. It never reads relevance labels or references.
"""

import re
from dataclasses import dataclass, field
from typing import Any

from src.query_relevance import (
    matched_query_concepts,
    query_concept_coverage,
    query_concepts,
)
from src.step08a_normalize_query import normalize_query
from src.step09_hybrid_retrieval import (
    anatomy_terms,
    medical_identity_similarity,
    medical_identity_tokens,
)


ARABIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
AGE_RE = re.compile(
    r"(?:عمر(?:ه|ها|ي)?\s*)?(\d{1,3})\s*"
    r"(سنه|سنة|سنوات|شهر|شهور|اشهر)"
)

CHILD_MARKERS = {
    "طفل",
    "طفله",
    "اطفال",
    "طفلي",
    "طفلتي",
    "ابني",
    "ابنتي",
    "رضيع",
    "رضيعه",
    "مولود",
}
ADULT_MARKERS = {
    "بالغ",
    "بالغه",
    "رجل",
    "سيده",
    "امراه",
    "شاب",
    "شابه",
    "زوجي",
    "زوجتي",
}
ELDERLY_MARKERS = {"مسن", "مسنه", "كبير السن", "كبيره السن"}

PREGNANCY_MARKERS = {
    "حامل",
    "الحمل",
    "اثناء الحمل",
    "خلال الحمل",
    "ولاده",
}
PREGNANCY_NEGATIONS = {
    "لست حامل",
    "ليست حامل",
    "غير حامل",
    "لا يوجد حمل",
    "عدم وجود حمل",
}
PREGNANCY_QUESTIONS = {
    "هل انا حامل",
    "هل هي حامل",
    "اختبار الحمل",
    "تحليل الحمل",
}

POST_PROCEDURE_MARKERS = {
    "بعد العمليه",
    "بعد الجراحه",
    "اجريت عمليه",
    "اجريت الجراحه",
    "بعد الاستئصال",
    "بعد الولاده",
    "بعد الاجهاض",
    "بعد المنظار",
}
PRE_PROCEDURE_MARKERS = {
    "قبل العمليه",
    "قبل الجراحه",
    "ساجري عمليه",
    "سوف اجري عمليه",
    "مقبل علي عمليه",
    "قبل المنظار",
}

ACUTE_DURATION_MARKERS = {
    "منذ يوم",
    "منذ يومين",
    "منذ ايام",
    "منذ اسبوع",
    "حاد",
    "مفاجئ",
}
CHRONIC_DURATION_MARKERS = {
    "منذ شهر",
    "منذ شهور",
    "منذ سنه",
    "منذ سنوات",
    "مزمن",
    "مستمر منذ",
}

TIMING_GROUPS = {
    "night": {"ليلا", "بالليل", "اثناء الليل", "عند النوم"},
    "morning": {"صباحا", "في الصباح", "عند الاستيقاظ"},
    "after_food": {"بعد الاكل", "بعد الطعام", "بعد الوجبه"},
    "before_food": {"قبل الاكل", "قبل الطعام", "علي الريق"},
    "after_effort": {"بعد المجهود", "بعد الجهد", "اثناء الرياضه"},
    "at_rest": {"اثناء الراحه", "في الراحه", "بدون مجهود"},
}

INTENT_MARKERS = {
    "treatment_request": {"علاج", "دواء", "ماذا افعل", "التخلص"},
    "symptom_request": {"اعراض", "علامات"},
    "diagnosis_request": {"تشخيص", "هل اعاني", "ما المرض"},
    "test_request": {"فحص", "تحليل", "تحاليل", "اشعه", "تصوير"},
    "cause_request": {"سبب", "اسباب", "لماذا", "ناتج"},
    "prevention_request": {"وقايه", "تجنب", "منع"},
    "medication_safety": {"هل الدواء", "امن", "امان", "اثار جانبيه"},
}


@dataclass(frozen=True)
class ClinicalScenarioCompatibility:
    score: float
    hard_conflict: bool
    conflicts: list[str] = field(default_factory=list)
    matches: list[str] = field(default_factory=list)
    dimensions: dict[str, Any] = field(default_factory=dict)


def normalized(text: str) -> str:
    return normalize_query(
        str(text or "").translate(ARABIC_DIGITS)
    ).normalized_query


def contains_any(text: str, markers: set[str]) -> bool:
    return any(normalized(marker) in text for marker in markers)


def age_group(text: str) -> str:
    clean = normalized(text)
    match = AGE_RE.search(clean)
    if match:
        value = int(match.group(1))
        unit = match.group(2)
        if unit in {"شهر", "شهور", "اشهر"}:
            return "infant" if value <= 24 else "child"
        if value < 2:
            return "infant"
        if value < 18:
            return "child"
        if value >= 60:
            return "elderly"
        return "adult"
    if contains_any(clean, CHILD_MARKERS):
        return "child"
    if contains_any(clean, ELDERLY_MARKERS):
        return "elderly"
    if contains_any(clean, ADULT_MARKERS):
        return "adult"
    return "unknown"


def pregnancy_state(text: str) -> str:
    clean = normalized(text)
    if contains_any(clean, PREGNANCY_NEGATIONS):
        return "absent"
    if contains_any(clean, PREGNANCY_QUESTIONS):
        return "uncertain"
    if contains_any(clean, PREGNANCY_MARKERS):
        return "present"
    return "unknown"


def procedure_phase(text: str) -> str:
    clean = normalized(text)
    if contains_any(clean, POST_PROCEDURE_MARKERS):
        return "post"
    if contains_any(clean, PRE_PROCEDURE_MARKERS):
        return "pre"
    return "unknown"


def duration_class(text: str) -> str:
    clean = normalized(text)
    if contains_any(clean, CHRONIC_DURATION_MARKERS):
        return "chronic"
    if contains_any(clean, ACUTE_DURATION_MARKERS):
        return "acute"
    return "unknown"


def timing_markers(text: str) -> set[str]:
    clean = normalized(text)
    return {
        name
        for name, markers in TIMING_GROUPS.items()
        if contains_any(clean, markers)
    }


def intent_compatibility(primary_intent: str, source_question: str) -> float:
    markers = INTENT_MARKERS.get(primary_intent)
    if not markers:
        return 0.75
    return 1.0 if contains_any(normalized(source_question), markers) else 0.35


def clinical_scenario_compatibility(
    query: str,
    source_question: str,
    *,
    primary_intent: str = "",
    query_medical_phrases: list[str] | None = None,
) -> ClinicalScenarioCompatibility:
    """Compare explicit query/source-question scenario dimensions."""

    phrases = [
        str(value or "").strip()
        for value in (query_medical_phrases or [])
        if str(value or "").strip()
    ]
    query_anatomy = anatomy_terms(query)
    source_anatomy = anatomy_terms(source_question)
    query_age = age_group(query)
    source_age = age_group(source_question)
    query_pregnancy = pregnancy_state(query)
    source_pregnancy = pregnancy_state(source_question)
    query_procedure = procedure_phase(query)
    source_procedure = procedure_phase(source_question)
    query_duration = duration_class(query)
    source_duration = duration_class(source_question)
    query_timing = timing_markers(query)
    source_timing = timing_markers(source_question)

    query_concept_set = query_concepts(query, phrases)
    matched_concepts = matched_query_concepts(
        query,
        source_question,
        phrases,
    )
    concept_coverage = query_concept_coverage(
        query,
        source_question,
        phrases,
    )
    identity_similarity = medical_identity_similarity(
        " ".join(phrases) or query,
        source_question,
    )
    identity_score = max(concept_coverage, identity_similarity)

    conflicts: list[str] = []
    matches: list[str] = []
    hard_conflicts: list[str] = []

    if query_anatomy and source_anatomy:
        if query_anatomy.isdisjoint(source_anatomy):
            conflicts.append("anatomy_conflict")
            hard_conflicts.append("anatomy_conflict")
            anatomy_score = 0.0
        else:
            matches.append("anatomy_match")
            anatomy_score = 1.0
    else:
        anatomy_score = 0.75

    child_groups = {"infant", "child"}
    adult_groups = {"adult", "elderly"}
    if query_age != "unknown" and source_age != "unknown":
        if (
            query_age in child_groups
            and source_age in adult_groups
        ) or (
            query_age in adult_groups
            and source_age in child_groups
        ):
            conflicts.append("age_group_conflict")
            hard_conflicts.append("age_group_conflict")
            age_score = 0.0
        else:
            matches.append("age_group_match")
            age_score = 1.0
    else:
        age_score = 0.75

    if {
        query_pregnancy,
        source_pregnancy,
    } == {"present", "absent"}:
        conflicts.append("pregnancy_conflict")
        hard_conflicts.append("pregnancy_conflict")
        pregnancy_score = 0.0
    elif (
        query_pregnancy != "unknown"
        and source_pregnancy != "unknown"
    ):
        matches.append("pregnancy_context_match")
        pregnancy_score = 1.0
    else:
        pregnancy_score = 0.75

    if (
        query_procedure != "unknown"
        and source_procedure != "unknown"
        and query_procedure != source_procedure
    ):
        conflicts.append("procedure_phase_conflict")
        hard_conflicts.append("procedure_phase_conflict")
        procedure_score = 0.0
    elif (
        query_procedure != "unknown"
        and source_procedure != "unknown"
    ):
        matches.append("procedure_phase_match")
        procedure_score = 1.0
    else:
        procedure_score = 0.75

    if (
        query_duration != "unknown"
        and source_duration != "unknown"
        and query_duration != source_duration
    ):
        conflicts.append("duration_mismatch")
        duration_score = 0.25
    elif (
        query_duration != "unknown"
        and source_duration != "unknown"
    ):
        matches.append("duration_match")
        duration_score = 1.0
    else:
        duration_score = 0.75

    if query_timing and source_timing:
        if query_timing.isdisjoint(source_timing):
            conflicts.append("timing_mismatch")
            timing_score = 0.25
        else:
            matches.append("timing_match")
            timing_score = 1.0
    else:
        timing_score = 0.75

    if query_concept_set and not matched_concepts:
        conflicts.append("medical_identity_unmatched")
    else:
        matches.append("medical_identity_match")

    intent_score = intent_compatibility(
        primary_intent,
        source_question,
    )
    if intent_score >= 0.75:
        matches.append("intent_match")
    else:
        conflicts.append("intent_mismatch")

    score = (
        0.30 * identity_score
        + 0.18 * anatomy_score
        + 0.14 * age_score
        + 0.12 * pregnancy_score
        + 0.10 * procedure_score
        + 0.07 * duration_score
        + 0.04 * timing_score
        + 0.05 * intent_score
    )
    if "medical_identity_unmatched" in conflicts:
        score -= 0.20
    score = max(0.0, min(1.0, score))
    return ClinicalScenarioCompatibility(
        score=round(score, 6),
        hard_conflict=bool(hard_conflicts),
        conflicts=list(dict.fromkeys(conflicts)),
        matches=list(dict.fromkeys(matches)),
        dimensions={
            "query_age_group": query_age,
            "source_age_group": source_age,
            "query_pregnancy": query_pregnancy,
            "source_pregnancy": source_pregnancy,
            "query_procedure_phase": query_procedure,
            "source_procedure_phase": source_procedure,
            "query_duration": query_duration,
            "source_duration": source_duration,
            "query_timing": sorted(query_timing),
            "source_timing": sorted(source_timing),
            "query_anatomy": sorted(query_anatomy),
            "source_anatomy": sorted(source_anatomy),
            "query_concepts": sorted(query_concept_set),
            "matched_query_concepts": sorted(matched_concepts),
            "identity_score": round(identity_score, 6),
            "intent_score": round(intent_score, 6),
        },
    )
