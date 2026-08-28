from __future__ import annotations

import argparse
import difflib
import json
import sys
import urllib.error
import urllib.request
from dataclasses import asdict
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.config import AppConfig, load_config
from src.models import ExtractedMedicalPhrase, QueryEntityLinkingResult, UnifiedQueryAnalysisResult
from src.neo4j_repository import Neo4jRepository
from src.step08_normalize_query import normalize_query
from src.step08_link_entities import GENERIC_PHRASES, link_extracted_phrases


PROMPT_VERSION = "query_analysis_v1"
GROQ_CHAT_COMPLETIONS_URL = "https://api.groq.com/openai/v1/chat/completions"
ALLOWED_ENTITY_TYPES = frozenset({"DiseaseCondition", "Symptom", "Treatment", "Test"})
ALLOWED_PHRASE_SOURCES = frozenset({"corrected_query", "reformulated_query"})
ALLOWED_QUERY_CLASSES = frozenset({"simple_medical", "complex_medical", "non_medical", "unclear"})
ALLOWED_COMPLEXITIES = frozenset({"low", "medium", "high"})
HORMONE_MEASUREMENT_MARKERS = (
    "نسبه",
    "نسبة",
    "مستوى",
    "معدل",
    "ارتفاع",
    "انخفاض",
    "تحليل",
    "فحص",
)
ALLOWED_INTENTS = frozenset(
    {
        "treatment_request",
        "symptom_request",
        "diagnosis_request",
        "test_request",
        "cause_request",
        "prevention_request",
        "medication_safety",
        "general_medical_advice",
        "comparison",
        "unclear_intent",
        "non_medical",
    }
)
RELATION_TYPES_BY_INTENT = {
    "treatment_request": ["TREATED_BY", "TREATS"],
    "symptom_request": ["HAS_SYMPTOM", "SYMPTOM_OF"],
    "diagnosis_request": ["DIAGNOSED_BY", "DIAGNOSES"],
    "test_request": ["INVESTIGATED_BY", "INVESTIGATES"],
}
UNSUPPORTED_GRAPH_INTENTS = {"cause_request", "prevention_request", "medication_safety"}
EXPLICIT_QUESTION_MARKERS = {
    "?", "؟", "ما", "ماذا", "هل", "كيف", "متى", "لماذا", "شنوا", "شنو", "اش", "إيش", "ايش",
}
SPECIFIC_INTENT_TERMS = {
    "سبب", "السبب", "اسباب", "الأسباب", "تشخيص", "اشخص", "علاج", "اعالج", "دواء", "تحاليل",
    "تحليل", "فحص", "فحوصات",
}


SYSTEM_PROMPT = """You are the unified Step 8 query-analysis component for an Arabic medical Graph-RAG system.

Analyze one normalized Arabic user query.

You must do only these tasks:
- correct obvious spelling or dialect phrasing
- reformulate the query into clear Modern Standard Arabic
- classify the query
- detect the user's intent
- extract explicit medical phrases

Allowed query_class values:
- simple_medical
- complex_medical
- non_medical
- unclear

Allowed complexity values:
- low
- medium
- high

Allowed intent values:
- treatment_request
- symptom_request
- diagnosis_request
- test_request
- cause_request
- prevention_request
- medication_safety
- general_medical_advice
- comparison
- unclear_intent
- non_medical

Allowed medical phrase entity_type values:
- DiseaseCondition
- Symptom
- Treatment
- Test

Allowed medical phrase source values:
- corrected_query
- reformulated_query

Meaning preservation rules:
- Preserve symptoms, diseases, treatments, tests, negation, uncertainty, duration, age, gender, severity, and question intent.
- Do not answer the query.
- Do not diagnose the patient.
- Do not add symptoms, diseases, treatments, tests, age, gender, duration, or severity that are not present.
- Do not infer diseases from symptoms.
- Do not assign Neo4j entity IDs.
- Do not perform retrieval.
- Do not choose hop depth.

Phrase extraction rules:
- Extract only phrases explicitly present in corrected_query or reformulated_query.
- Do not replace phrases with graph canonical names.
- Do not perform alias matching.
- A negated phrase may be extracted, but do not treat it as a positive claim.

Return strict JSON only with this schema:
{
  "corrected_query": "string",
  "reformulated_query": "string",
  "query_class": "simple_medical|complex_medical|non_medical|unclear",
  "complexity": "low|medium|high",
  "primary_intent": "one allowed intent",
  "secondary_intents": ["allowed intent"],
  "medical_phrases": [
    {
      "surface_form": "string",
      "normalized_form": "string",
      "entity_type": "DiseaseCondition|Symptom|Treatment|Test",
      "source": "corrected_query|reformulated_query",
      "confidence": 0.0
    }
  ],
  "confidence": 0.0,
  "warnings": ["string"]
}
"""


def make_messages(original_query: str, normalized_query: str) -> list[dict[str, str]]:
    user_prompt = {
        "original_query": original_query,
        "normalized_query": normalized_query,
        "instructions": [
            "Return one strict JSON object only.",
            "Do not answer the medical question.",
            "Extract explicit medical phrases only.",
            "Do not assign graph entity IDs or relation types.",
        ],
    }
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": json.dumps(user_prompt, ensure_ascii=False)},
    ]


def parse_json_object(content: str) -> dict[str, Any]:
    """Parse one strict JSON object, tolerating an accidental Markdown fence."""
    text = (content or "").strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:].strip()
    parsed = json.loads(text)
    if not isinstance(parsed, dict):
        raise ValueError("LLM response is not a JSON object.")
    return parsed


def call_groq_json(messages: list[dict[str, str]], config: AppConfig) -> dict[str, Any]:
    """Call the configured Groq chat model and return its JSON object."""
    query_config = config.query_analysis
    if not query_config.groq_api_key:
        raise RuntimeError("GROQ_API_KEY is not set.")

    body: dict[str, Any] = {
        "model": query_config.model,
        "messages": messages,
        "temperature": query_config.temperature,
        "response_format": {"type": "json_object"},
    }
    if query_config.reasoning_effort:
        body["reasoning_effort"] = query_config.reasoning_effort

    request = urllib.request.Request(
        GROQ_CHAT_COMPLETIONS_URL,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {query_config.groq_api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "AHD-GraphRAG/0.1",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=90) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return parse_json_object(payload["choices"][0]["message"]["content"])


def has_explicit_question_intent(query: str) -> bool:
    tokens = set(query.replace("؟", " ? ").replace("?", " ? ").split())
    return bool(tokens.intersection(EXPLICIT_QUESTION_MARKERS))


def introduces_specific_intent(original_query: str, reformulated_query: str) -> bool:
    original_normalized = normalize_query(original_query).normalized_query
    reformulated_normalized = normalize_query(reformulated_query).normalized_query
    for term in SPECIFIC_INTENT_TERMS:
        normalized_term = normalize_query(term).normalized_query
        if normalized_term and normalized_term in reformulated_normalized and normalized_term not in original_normalized:
            return True
    return False


def enforce_meaning_preservation(
    original_query: str,
    corrected_query: str,
    reformulated_query: str,
) -> tuple[str, list[str]]:
    """Keep Python as the final authority when reformulation adds a new intent."""
    if has_explicit_question_intent(original_query):
        return reformulated_query, []
    if not introduces_specific_intent(original_query, reformulated_query):
        return reformulated_query, []
    neutral = f"ما التوجيه الطبي المناسب بخصوص: {corrected_query}؟"
    return neutral, ["Blocked a newly introduced specific intent to preserve the original query meaning."]


def phrase_exists(surface_form: str, source_text: str) -> bool:
    if surface_form in source_text:
        return True
    normalized_surface = normalize_query(surface_form).normalized_query
    normalized_source = normalize_query(source_text).normalized_query
    return bool(normalized_surface and normalized_surface in normalized_source)


def dedupe_phrases(phrases: list[ExtractedMedicalPhrase]) -> list[ExtractedMedicalPhrase]:
    """Prefer the longest explicit phrase and remove normalized near-duplicates."""
    kept: list[ExtractedMedicalPhrase] = []
    seen: set[str] = set()
    source_priority = {"corrected_query": 0, "reformulated_query": 1}
    ordered = sorted(phrases, key=lambda item: (source_priority.get(item.source, 9), -len(item.normalized_form)))
    for phrase in ordered:
        normalized = phrase.normalized_form
        if not normalized or normalized in seen:
            continue
        if any(normalized in existing.normalized_form for existing in kept):
            continue
        if any(
            phrase.entity_type == existing.entity_type
            and difflib.SequenceMatcher(None, normalized, existing.normalized_form).ratio() >= 0.78
            for existing in kept
        ):
            continue
        kept.append(phrase)
        seen.add(normalized)
    return kept


def validate_phrase_payload(
    payload: dict[str, Any],
    corrected_query: str,
    reformulated_query: str,
) -> tuple[list[ExtractedMedicalPhrase], list[str]]:
    """Validate explicit phrases without inferring concepts or graph identifiers."""
    if "medical_phrases" not in payload or "warnings" not in payload:
        raise ValueError("Missing required medical_phrases or warnings fields.")
    if not isinstance(payload["medical_phrases"], list):
        raise ValueError("medical_phrases must be a list.")
    if not isinstance(payload["warnings"], list) or not all(isinstance(item, str) for item in payload["warnings"]):
        raise ValueError("warnings must be a list of strings.")

    warnings = [item.strip() for item in payload["warnings"] if item.strip()]
    phrases: list[ExtractedMedicalPhrase] = []
    source_texts = {"corrected_query": corrected_query, "reformulated_query": reformulated_query}
    for index, item in enumerate(payload["medical_phrases"], start=1):
        if not isinstance(item, dict):
            warnings.append(f"Skipped phrase {index}: item is not an object.")
            continue
        surface_form = str(item.get("surface_form", "")).strip()
        normalized_form = str(item.get("normalized_form", "")).strip()
        entity_type = str(item.get("entity_type", "")).strip()
        source = str(item.get("source", "")).strip()
        try:
            confidence = float(item["confidence"])
        except (KeyError, TypeError, ValueError):
            warnings.append(f"Skipped phrase {index}: missing or invalid confidence.")
            continue

        expected_normalized = normalize_query(surface_form).normalized_query
        if not surface_form:
            warnings.append(f"Skipped phrase {index}: missing surface_form.")
        elif entity_type not in ALLOWED_ENTITY_TYPES:
            warnings.append(f"Skipped phrase {index}: invalid entity_type={entity_type}.")
        elif source not in ALLOWED_PHRASE_SOURCES:
            warnings.append(f"Skipped phrase {index}: invalid source={source}.")
        elif not 0.0 <= confidence <= 1.0:
            warnings.append(f"Skipped phrase {index}: confidence outside 0..1.")
        elif not phrase_exists(surface_form, source_texts[source]):
            warnings.append(f"Skipped phrase {index}: surface_form not found in {source}.")
        else:
            if normalized_form != expected_normalized:
                warnings.append(f"Adjusted phrase {index}: normalized_form replaced with project normalization.")
            corrected_entity_type = entity_type
            normalized_query_text = normalize_query(corrected_query).normalized_query
            if (
                entity_type == "Treatment"
                and expected_normalized.startswith("هرمون ")
                and any(marker in normalized_query_text for marker in HORMONE_MEASUREMENT_MARKERS)
            ):
                corrected_entity_type = "DiseaseCondition"
                warnings.append(
                    f"Adjusted phrase {index}: measured hormone concept retyped for graph compatibility."
                )
            phrases.append(
                ExtractedMedicalPhrase(
                    surface_form=surface_form,
                    normalized_form=expected_normalized,
                    entity_type=corrected_entity_type,
                    source=source,
                    confidence=confidence,
                )
            )
    return dedupe_phrases(phrases), warnings


def relation_types_for_intents(primary_intent: str, secondary_intents: list[str]) -> list[str]:
    relation_types: list[str] = []
    for intent in [primary_intent, *secondary_intents]:
        for relation_type in RELATION_TYPES_BY_INTENT.get(intent, []):
            if relation_type not in relation_types:
                relation_types.append(relation_type)
    return relation_types


def deterministic_intent_from_text(text: str, query_class: str) -> tuple[str, list[str], float] | None:
    normalized = normalize_query(text).normalized_query
    if any(term in normalized for term in {"طقس", "الطقس", "جو اليوم"}):
        return "non_medical", [], 0.9
    if query_class == "non_medical":
        return "non_medical", [], 0.9
    if any(term in normalized for term in {"وقايه", "اقي", "احمي", "تجنب"}):
        return "prevention_request", [], 0.85
    if any(term in normalized for term in {"دواء", "الدوا", "الدواء"}):
        if any(term in normalized for term in {"بسبب", "من الدواء", "من الدوا", "اثر", "تداخل"}):
            return "medication_safety", ["cause_request"], 0.85
    if any(term in normalized for term in {"تحاليل", "تحليل", "فحص", "فحوصات", "اشعه", "اختبار"}):
        return "test_request", [], 0.9
    if "تشخيص" in normalized or "يشخص" in normalized:
        return "diagnosis_request", [], 0.9
    if "اعراض" in normalized or "عرض" in normalized:
        return "symptom_request", [], 0.9
    if "علاج" in normalized or "اعالج" in normalized:
        return "treatment_request", [], 0.9
    if "بسبب" in normalized or "سبب" in normalized:
        secondary = ["comparison"] if " ام " in f" {normalized} " else []
        return "cause_request", secondary, 0.8
    return None


def graph_support_warnings(primary_intent: str, secondary_intents: list[str]) -> list[str]:
    warnings: list[str] = []
    for intent in [primary_intent, *secondary_intents]:
        if intent in UNSUPPORTED_GRAPH_INTENTS:
            warnings.append(
                f"{intent} is not directly represented by current graph relation types; vector/evidence retrieval will be needed."
            )
    return warnings


def generic_link_warnings(result: QueryEntityLinkingResult) -> list[str]:
    warnings: list[str] = []
    for entity in result.linked_entities:
        normalized = normalize_query(entity.normalized_form).normalized_query
        stripped = normalized[2:] if normalized.startswith("ال") else normalized
        if entity.status == "linked" and (normalized in GENERIC_PHRASES or stripped in GENERIC_PHRASES):
            warnings.append(
                f"Linked generic concept '{entity.surface_form}' is low-specificity and should not be a strong retrieval seed."
            )
    return warnings


def _validate_allowed_value(value: Any, allowed: frozenset[str], field_name: str) -> str:
    cleaned = str(value or "").strip()
    if cleaned not in allowed:
        raise ValueError(f"Invalid {field_name}: {cleaned}")
    return cleaned


def validate_analysis_payload(
    payload: dict[str, Any],
    original_query: str,
    normalized_query: str,
) -> tuple[dict[str, Any], list[str]]:
    required = [
        "corrected_query",
        "reformulated_query",
        "query_class",
        "complexity",
        "primary_intent",
        "secondary_intents",
        "medical_phrases",
        "confidence",
        "warnings",
    ]
    missing = [field for field in required if field not in payload]
    if missing:
        raise ValueError(f"Missing required fields: {', '.join(missing)}")

    corrected_query = str(payload["corrected_query"]).strip() or normalized_query
    reformulated_query = str(payload["reformulated_query"]).strip() or corrected_query
    reformulated_query, preservation_warnings = enforce_meaning_preservation(
        normalized_query,
        corrected_query,
        reformulated_query,
    )

    query_class = _validate_allowed_value(payload["query_class"], ALLOWED_QUERY_CLASSES, "query_class")
    complexity = _validate_allowed_value(payload["complexity"], ALLOWED_COMPLEXITIES, "complexity")
    primary_intent = _validate_allowed_value(payload["primary_intent"], ALLOWED_INTENTS, "primary_intent")

    secondary_intents_raw = payload["secondary_intents"]
    if not isinstance(secondary_intents_raw, list):
        raise ValueError("secondary_intents must be a list.")
    secondary_intents: list[str] = []
    for item in secondary_intents_raw:
        intent = _validate_allowed_value(item, ALLOWED_INTENTS, "secondary_intent")
        if intent != primary_intent and intent not in secondary_intents:
            secondary_intents.append(intent)

    try:
        confidence = float(payload["confidence"])
    except (TypeError, ValueError) as exc:
        raise ValueError("confidence must be numeric.") from exc
    if not 0.0 <= confidence <= 1.0:
        raise ValueError("confidence must be between 0 and 1.")

    deterministic = deterministic_intent_from_text(
        f"{corrected_query} {reformulated_query}",
        query_class,
    )
    if deterministic is not None:
        primary_intent, secondary_intents, deterministic_confidence = deterministic
        confidence = max(confidence, deterministic_confidence)

    warnings_raw = payload["warnings"]
    if not isinstance(warnings_raw, list) or not all(isinstance(item, str) for item in warnings_raw):
        raise ValueError("warnings must be a list of strings.")
    warnings = [item.strip() for item in warnings_raw if item.strip()]
    warnings.extend(preservation_warnings)

    if query_class == "non_medical":
        primary_intent = "non_medical"
        secondary_intents = []
        phrase_payload = {"medical_phrases": [], "warnings": warnings}
    else:
        phrase_payload = {
            "medical_phrases": payload["medical_phrases"],
            "warnings": warnings,
        }

    phrases, phrase_warnings = validate_phrase_payload(
        phrase_payload,
        corrected_query,
        reformulated_query,
    )
    warnings = phrase_warnings

    if query_class == "non_medical" and phrases:
        raise ValueError("non_medical queries must not return medical_phrases.")
    if primary_intent == "non_medical" and query_class != "non_medical":
        warnings.append("primary_intent was non_medical but query_class was medical/unclear.")

    return (
        {
            "original_query": original_query,
            "normalized_query": normalized_query,
            "corrected_query": corrected_query,
            "reformulated_query": reformulated_query,
            "query_class": query_class,
            "complexity": complexity,
            "primary_intent": primary_intent,
            "secondary_intents": secondary_intents,
            "medical_phrases": phrases,
            "confidence": confidence,
            "preferred_relation_types": relation_types_for_intents(primary_intent, secondary_intents),
        },
        warnings,
    )


def fallback_result(
    original_query: str,
    normalized_query: str,
    config: AppConfig,
    warning: str,
) -> UnifiedQueryAnalysisResult:
    # The LLM is the normal analyzer, but a provider failure must not erase an
    # obvious request such as "what tests" or "what treatment".  This fallback
    # recovers intent only from explicit lexical cues; it deliberately leaves
    # phrase extraction empty instead of guessing medical concepts.
    deterministic = deterministic_intent_from_text(normalized_query, "unclear")
    if deterministic is None:
        primary_intent = "unclear_intent"
        secondary_intents: list[str] = []
        confidence = 0.0
        query_class = "unclear"
        complexity = "medium"
        fallback_warnings = [warning]
    else:
        primary_intent, secondary_intents, confidence = deterministic
        query_class = "non_medical" if primary_intent == "non_medical" else "complex_medical"
        complexity = "low" if primary_intent == "non_medical" else "medium"
        fallback_warnings = [
            warning,
            "Recovered explicit query intent with deterministic lexical rules; medical phrases remain unextracted.",
            *graph_support_warnings(primary_intent, secondary_intents),
        ]
    return UnifiedQueryAnalysisResult(
        original_query=original_query,
        normalized_query=normalized_query,
        corrected_query=normalized_query,
        reformulated_query=normalized_query,
        query_class=query_class,
        complexity=complexity,
        primary_intent=primary_intent,
        secondary_intents=secondary_intents,
        medical_phrases=[],
        confidence=confidence,
        preferred_relation_types=relation_types_for_intents(primary_intent, secondary_intents),
        warnings=list(dict.fromkeys(fallback_warnings)),
        model=config.query_analysis.model,
        prompt_version=PROMPT_VERSION,
    )


def analyze_query(query: str, config: AppConfig | None = None) -> UnifiedQueryAnalysisResult:
    config = config or load_config()
    normalization = normalize_query(query)

    if config.query_analysis.provider != "groq":
        return fallback_result(
            normalization.original_query,
            normalization.normalized_query,
            config,
            f"Unsupported query analysis provider: {config.query_analysis.provider}",
        )

    try:
        payload = call_groq_json(
            make_messages(normalization.original_query, normalization.normalized_query),
            config,
        )
        cleaned, validation_warnings = validate_analysis_payload(
            payload,
            normalization.original_query,
            normalization.normalized_query,
        )
    except (RuntimeError, ValueError, KeyError, json.JSONDecodeError, urllib.error.URLError, urllib.error.HTTPError) as exc:
        error_name = type(exc).__name__
        if isinstance(exc, urllib.error.HTTPError):
            error_name = f"HTTPError {exc.code}"
        return fallback_result(
            normalization.original_query,
            normalization.normalized_query,
            config,
            f"Unified LLM query analysis failed: {error_name}",
        )

    warnings = [
        *normalization.warnings,
        *validation_warnings,
        *graph_support_warnings(cleaned["primary_intent"], cleaned["secondary_intents"]),
    ]

    return UnifiedQueryAnalysisResult(
        original_query=cleaned["original_query"],
        normalized_query=cleaned["normalized_query"],
        corrected_query=cleaned["corrected_query"],
        reformulated_query=cleaned["reformulated_query"],
        query_class=cleaned["query_class"],
        complexity=cleaned["complexity"],
        primary_intent=cleaned["primary_intent"],
        secondary_intents=cleaned["secondary_intents"],
        medical_phrases=cleaned["medical_phrases"],
        confidence=cleaned["confidence"],
        preferred_relation_types=cleaned["preferred_relation_types"],
        warnings=warnings,
        model=config.query_analysis.model,
        prompt_version=PROMPT_VERSION,
    )


def analyze_and_link_query(
    query: str,
    repository: Neo4jRepository | None = None,
    config: AppConfig | None = None,
) -> tuple[UnifiedQueryAnalysisResult, QueryEntityLinkingResult]:
    analysis = analyze_query(query, config=config)

    if repository is None:
        with Neo4jRepository(config=config) as repo:
            linking = link_extracted_phrases(
                analysis.original_query,
                analysis.corrected_query,
                analysis.reformulated_query,
                analysis.query_class,
                analysis.complexity,
                analysis.medical_phrases,
                repo,
                analysis.warnings,
            )
    else:
        linking = link_extracted_phrases(
            analysis.original_query,
            analysis.corrected_query,
            analysis.reformulated_query,
            analysis.query_class,
            analysis.complexity,
            analysis.medical_phrases,
            repository,
            analysis.warnings,
        )

    linking.warnings.extend(generic_link_warnings(linking))
    return analysis, linking


def print_result(analysis: UnifiedQueryAnalysisResult, linking: QueryEntityLinkingResult | None = None) -> None:
    payload = asdict(analysis)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if linking is None:
        return
    print("linked_entities:")
    for entity in linking.linked_entities:
        print(
            f"- surface: {entity.surface_form} | normalized: {entity.normalized_form} | "
            f"type: {entity.extracted_entity_type} | status: {entity.status} | "
            f"entity_id: {entity.linked_entity_id} | canonical: {entity.linked_canonical_name} | "
            f"match_type: {entity.match_type} | score: {entity.match_score:.2f}"
        )
    if linking.warnings:
        print("linking_warnings:")
        for warning in linking.warnings:
            print(f"- {warning}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run unified Step 8 query analysis with one LLM call.")
    parser.add_argument("--query", required=True, help="Arabic query.")
    parser.add_argument("--link", action="store_true", help="Also link extracted phrases to Neo4j entities.")
    args = parser.parse_args()

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    if args.link:
        analysis, linking = analyze_and_link_query(args.query)
        print_result(analysis, linking)
    else:
        print_result(analyze_query(args.query))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
