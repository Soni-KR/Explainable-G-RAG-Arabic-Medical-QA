import argparse
import csv
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path


# %% [markdown]
# Step 3 - LLM entity extraction
# This script sends chunked Arabic medical Q&A records to Groq, validates the
# JSON entity output, canonicalizes noisy forms, and exports entity/mention/alias
# tables for the trial graph. It intentionally stays entity-only: no relations
# and no Neo4j import happen here.

SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent if SCRIPT_DIR.name == "scripts" else SCRIPT_DIR
CHUNKING_DIR = BASE_DIR / "outputs" / "02_chunking"
ENTITY_DIR = BASE_DIR / "outputs" / "03_entity_extraction"
REPORTS_DIR = BASE_DIR / "reports"

CHUNKS_JSONL = CHUNKING_DIR / "ahd_chunks_5000.jsonl"
REQUESTS_JSONL = ENTITY_DIR / "ahd_llm_entity_extraction_requests.jsonl"
RAW_RESPONSES_JSONL = ENTITY_DIR / "ahd_llm_entity_extraction_raw_responses.jsonl"
VALIDATED_JSONL = ENTITY_DIR / "ahd_llm_entity_extraction_validated.jsonl"
ENTITIES_CSV = ENTITY_DIR / "ahd_entities_llm.csv"
MENTIONS_CSV = ENTITY_DIR / "ahd_entity_mentions_llm.csv"
ALIASES_CSV = ENTITY_DIR / "ahd_entity_aliases_llm.csv"
ERRORS_CSV = ENTITY_DIR / "ahd_entity_extraction_errors.csv"
REPORT_MD = REPORTS_DIR / "ahd_entity_extraction_report.md"

DEFAULT_PROVIDER = "groq"
DEFAULT_GROQ_MODEL = "llama-3.3-70b-versatile"
LOW_CONFIDENCE_THRESHOLD = 0.5
ENV_FILE = BASE_DIR / ".env"
MAX_MODEL_CALL_RETRIES = 2
RETRY_BACKOFF_SECONDS = 20
MAX_RETRY_WAIT_SECONDS = 60

ENTITY_TYPES = {
    "DiseaseCondition",
    "Symptom",
    "Treatment",
    "Test",
}

ARABIC_DIACRITICS_RE = re.compile(r"[\u064b-\u065f\u0670\u06d6-\u06ed]")
TATWEEL_RE = re.compile(r"\u0640+")
WHITESPACE_RE = re.compile(r"\s+")
ARABIC_LETTER_NORMALIZATION = str.maketrans(
    {
        "\u0623": "\u0627",
        "\u0625": "\u0627",
        "\u0622": "\u0627",
        "\u0671": "\u0627",
        "\u0649": "\u064a",
        "\u0626": "\u064a",
        "\u0624": "\u0648",
        "\u0629": "\u0647",
    }
)

GENERIC_STANDALONE_TERMS = {
    "\u0645\u0631\u064a\u0636",
    "\u0637\u0628\u064a\u0628",
    "\u0639\u0644\u0627\u062c",
    "\u0627\u0644\u062d\u0627\u0644\u0629",
    "\u062d\u0627\u0644\u0629",
    "\u0645\u0631\u0636",
    "\u0645\u0634\u0643\u0644\u0629",
    "\u0637\u0628\u064a\u0639\u064a",
    "\u062f\u0648\u0627\u0621",
    "\u0627\u0644\u0645",
    "\u062d\u0628\u0648\u0628",
}

NOISY_STANDALONE_TERMS = {
    "\u0647\u0644\u0627\u062c",
}

ANTIHISTAMINE_ALIASES = {
    "\u0645\u0636\u0627\u062f \u0627\u0644\u0647\u0633\u062a\u0627\u0645\u064a\u0646",
    "\u0645\u0636\u0627\u062f \u0627\u0644\u0647\u064a\u0633\u062a\u0627\u0645\u064a\u0646",
    "\u0645\u0636\u0627\u062f \u0647\u064a\u0633\u0627\u0645\u064a\u0646",
    "\u0645\u0636\u0627\u062f \u0647\u064a\u0633\u062a\u0627\u0645\u064a\u0646",
}
ANTIHISTAMINE_CANONICAL = "\u0645\u0636\u0627\u062f \u0627\u0644\u0647\u064a\u0633\u062a\u0627\u0645\u064a\u0646"

CANONICAL_NAME_OVERRIDES = {
    "\u062a\u0647\u0627\u0628 \u0644\u0648\u0632": "\u0627\u0644\u062a\u0647\u0627\u0628 \u0627\u0644\u0644\u0648\u0632\u062a\u064a\u0646",
    "\u0627\u0644\u062a\u0647\u0627\u0628 \u0644\u0648\u0632": "\u0627\u0644\u062a\u0647\u0627\u0628 \u0627\u0644\u0644\u0648\u0632\u062a\u064a\u0646",
    "\u062d\u0645\u0644": "\u0627\u0644\u062d\u0645\u0644",
    "\u0627\u0633\u0628\u0631\u064a\u0646": "\u0627\u0644\u0623\u0633\u0628\u0631\u064a\u0646",
    "\u0627\u0644\u0627\u0633\u0628\u0631\u064a\u0646": "\u0627\u0644\u0623\u0633\u0628\u0631\u064a\u0646",
    "\u062a\u062d\u0644\u064a\u0644 \u062d\u0633\u0627\u0633\u064a\u0647": "\u062a\u062d\u0644\u064a\u0644 \u0627\u0644\u062d\u0633\u0627\u0633\u064a\u0629",
    "\u062a\u062d\u0644\u064a\u0644 \u0645\u062e\u0628\u0631\u064a": "\u062a\u062d\u0627\u0644\u064a\u0644 \u0645\u062e\u0628\u0631\u064a\u0629",
    "\u062a\u062d\u0627\u0644\u064a\u0644 \u0645\u062e\u0628\u0631\u064a\u0647": "\u062a\u062d\u0627\u0644\u064a\u0644 \u0645\u062e\u0628\u0631\u064a\u0629",
    "\u0636\u064a\u0642 \u0627\u0644\u0646\u0641\u0633": "\u0636\u064a\u0642 \u062a\u0646\u0641\u0633",
    "\u0636\u064a\u0642 \u0646\u0641\u0633": "\u0636\u064a\u0642 \u062a\u0646\u0641\u0633",
    "\u0646\u0632\u0644\u0647 \u0645\u0639\u0648\u064a\u0647": "\u0646\u0632\u0644\u0629 \u0645\u0639\u0648\u064a\u0629",
}

FORCED_TYPE_OVERRIDES = {
    "\u0627\u0644\u062c\u0644\u0637\u0629 \u0627\u0644\u062f\u0645\u0627\u063a\u064a\u0629": "DiseaseCondition",
    "\u0627\u0644\u062c\u0644\u0637\u0647 \u0627\u0644\u062f\u0645\u0627\u063a\u064a\u0647": "DiseaseCondition",
    "\u062d\u0645\u0649": "Symptom",
    "\u062d\u0645\u064a": "Symptom",
    "\u0627\u0644\u062c\u0644\u0648\u0643\u0648\u0632": "Test",
    "\u062c\u0644\u0648\u0643\u0648\u0632": "Test",
}

CATEGORY_LIKE_TERMS = {
    "\u0623\u0645\u0631\u0627\u0636 \u0627\u0644\u0642\u0644\u0628 \u0648 \u0627\u0644\u0634\u0631\u0627\u064a\u064a\u0646",
    "\u0627\u0645\u0631\u0627\u0636 \u0627\u0644\u0642\u0644\u0628 \u0648 \u0627\u0644\u0634\u0631\u0627\u064a\u064a\u0646",
    "\u0623\u0645\u0631\u0627\u0636 \u0627\u0644\u0642\u0644\u0628 \u0648\u0627\u0644\u0634\u0631\u0627\u064a\u064a\u0646",
    "\u0627\u0645\u0631\u0627\u0636 \u0627\u0644\u0642\u0644\u0628 \u0648\u0627\u0644\u0634\u0631\u0627\u064a\u064a\u0646",
}

CONTEXT_ONLY_TERMS = {
    "\u0627\u0644\u0646\u0648\u0645",
    "\u0646\u0648\u0645",
}

INFLAMMATION_MARKERS = {
    "\u0627\u0644\u062a\u0647\u0627\u0628",
    "\u062a\u0647\u0627\u0628",
}

INFLAMMATION_TREATMENT_MARKERS = {
    "\u0639\u0644\u0627\u062c",
    "\u062f\u0648\u0627\u0621",
    "\u0645\u0636\u0627\u062f",
    "\u0645\u0631\u0647\u0645",
    "\u0643\u0631\u064a\u0645",
    "\u0642\u0637\u0631\u0629",
    "\u0634\u0631\u0627\u0628",
    "\u0627\u0642\u0631\u0627\u0635",
    "\u062d\u0628\u0648\u0628",
}

BROAD_LOW_QUALITY_TREATMENTS = {
    "\u0627\u0644\u0631\u064a\u0627\u0636\u0629",
    "\u0631\u064a\u0627\u0636\u0629",
    "\u062c\u0631\u0639\u0629",
    "\u0628\u0644\u0633\u0645",
    "\u0628\u0631\u0627\u0645\u062c \u0631\u0642\u064a\u0629",
    "\u0634\u0648\u0641\u0627\u0646",
    "\u0639\u064a\u0634 \u0627\u0644\u063a\u0631\u0627\u0628",
}

TRIGGER_OR_ALLERGEN_STANDALONE_TERMS = {
    "\u062c\u0644\u0648\u062a\u064a\u0646",
    "\u0627\u0644\u062c\u0644\u0648\u062a\u064a\u0646",
    "\u062d\u0644\u064a\u0628 \u0627\u0644\u0628\u0642\u0631",
}

BACKGROUND_MEDICATION_TERMS = {
    "\u0639\u0644\u0627\u062c \u0627\u0644\u0636\u063a\u0637",
    "\u0639\u0644\u0627\u062c \u0644\u0644\u0636\u063a\u0637",
    "\u0639\u0644\u0627\u062c \u0627\u0644\u0643\u0648\u0644\u064a\u0633\u062a\u0631\u0648\u0644",
    "\u0639\u0644\u0627\u062c \u0644\u0644\u0643\u0648\u0644\u064a\u0633\u062a\u0631\u0648\u0644",
}

DISEASE_CONDITION_OVERRIDES = {
    "\u062d\u0633\u0627\u0633\u064a\u0629 \u0627\u0644\u0635\u062f\u0631",
    "\u062d\u0633\u0627\u0633\u064a\u0647 \u0627\u0644\u0635\u062f\u0631",
    "\u0646\u0632\u0644\u0629 \u0645\u0639\u0648\u064a\u0629",
    "\u0646\u0632\u0644\u0647 \u0645\u0639\u0648\u064a\u0647",
    "\u0627\u0644\u0627\u0631\u062a\u0643\u0627\u0631\u064a\u0627",
    "\u0627\u0631\u062a\u0643\u0627\u0631\u064a\u0627",
}

SYMPTOM_TYPE_OVERRIDES = {
    "\u0636\u064a\u0642 \u062a\u0646\u0641\u0633",
    "\u0636\u064a\u0642 \u0627\u0644\u0646\u0641\u0633",
    "\u0633\u0639\u0627\u0644",
    "\u0628\u0644\u063a\u0645",
    "\u062d\u0643\u0629",
    "\u062d\u0643\u0647",
    "\u062a\u0639\u0628",
    "\u0635\u062f\u0627\u0639",
}

BODY_PART_ONLY_TERMS = {
    "\u0627\u0644\u0639\u064a\u0646",
    "\u0639\u064a\u0646",
    "\u0627\u0644\u062d\u0644\u0642",
    "\u062d\u0644\u0642",
    "\u0627\u0644\u0642\u0644\u0628",
    "\u0642\u0644\u0628",
    "\u0627\u0644\u0643\u0644\u0649",
    "\u0643\u0644\u0649",
    "\u0627\u0644\u0643\u0628\u062f",
    "\u0643\u0628\u062f",
    "\u0627\u0644\u0645\u0639\u062f\u0629",
    "\u0645\u0639\u062f\u0629",
    "\u0627\u0644\u062c\u0644\u062f",
    "\u062c\u0644\u062f",
    "\u0627\u0644\u0631\u0623\u0633",
    "\u0631\u0623\u0633",
    "\u0627\u0644\u0635\u062f\u0631",
    "\u0635\u062f\u0631",
    "\u0627\u0644\u0638\u0647\u0631",
    "\u0638\u0647\u0631",
    "\u0627\u0644\u0628\u0637\u0646",
    "\u0628\u0637\u0646",
    "\u0627\u0644\u0631\u062d\u0645",
    "\u0631\u062d\u0645",
    "\u0627\u0644\u0645\u0628\u064a\u0636",
    "\u0645\u0628\u064a\u0636",
}

ACCIDENTAL_TYPE_TERMS = {"Category", "BodyPart", "Other"}


# %% [markdown]
# Shared utilities
# Path helpers, `.env` loading, JSON parsing, Arabic normalization, and stable IDs.


def relpath(path):
    return path.relative_to(BASE_DIR).as_posix()


def load_env_file(path=ENV_FILE):
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


def parse_json(value, default):
    if value is None or value == "":
        return default
    if isinstance(value, (list, dict)):
        return value
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return default


def normalize_arabic(value):
    value = str(value or "")
    value = TATWEEL_RE.sub("", value)
    value = ARABIC_DIACRITICS_RE.sub("", value)
    value = value.translate(ARABIC_LETTER_NORMALIZATION)
    value = WHITESPACE_RE.sub(" ", value)
    return value.strip().lower()


def stable_entity_id(entity_type, canonical_name):
    normalized = normalize_arabic(canonical_name)
    digest = hashlib.sha1(f"{entity_type}::{normalized}".encode("utf-8")).hexdigest()[:12]
    return f"ent_{entity_type.lower()}_{digest}"


def stable_mention_key(entity_id, chunk_id, qa_id, field, surface_form, evidence):
    normalized = normalize_arabic(f"{entity_id}|{chunk_id}|{qa_id}|{field}|{surface_form}|{evidence}")
    return hashlib.sha1(normalized.encode("utf-8")).hexdigest()


def is_missing_or_placeholder_key(api_key):
    if not api_key:
        return True
    normalized = api_key.strip().lower()
    return normalized in {"replace_with_your_groq_api_key", "your_key_here", "your_groq_api_key_here"}


def is_generic_standalone(canonical_name):
    normalized = normalize_arabic(canonical_name)
    generic_terms = GENERIC_STANDALONE_TERMS | NOISY_STANDALONE_TERMS
    return normalized in {normalize_arabic(term) for term in generic_terms}


def is_body_part_only(canonical_name):
    normalized = normalize_arabic(canonical_name)
    return normalized in {normalize_arabic(term) for term in BODY_PART_ONLY_TERMS}


def is_trigger_or_allergen_standalone(canonical_name):
    normalized = normalize_arabic(canonical_name)
    return normalized in {normalize_arabic(term) for term in TRIGGER_OR_ALLERGEN_STANDALONE_TERMS}


def is_background_medication(canonical_name):
    normalized = normalize_arabic(canonical_name)
    return normalized in {normalize_arabic(term) for term in BACKGROUND_MEDICATION_TERMS}


def is_category_like_entity(canonical_name):
    normalized = normalize_arabic(canonical_name)
    return normalized in {normalize_arabic(term) for term in CATEGORY_LIKE_TERMS}


def is_context_only_entity(canonical_name):
    normalized = normalize_arabic(canonical_name)
    return normalized in {normalize_arabic(term) for term in CONTEXT_ONLY_TERMS}


def extract_json_object(text):
    text = str(text or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text).strip()
        text = re.sub(r"```$", "", text).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        return json.loads(text[start : end + 1])
    raise ValueError("Could not parse JSON object from model response")


def repair_mojibake(value):
    value = str(value or "")
    if not any(marker in value for marker in ("\u00d8", "\u00d9")):
        return value
    try:
        repaired = value.encode("latin-1").decode("utf-8")
    except UnicodeError:
        return value
    return repaired if repaired else value


def canonicalize_entity_name(entity_type, canonical_name, aliases):
    canonical_name = repair_mojibake(canonical_name)
    aliases = [repair_mojibake(alias) for alias in aliases]
    alias_values = sorted(set(str(alias).strip() for alias in aliases if str(alias).strip()))
    override = CANONICAL_NAME_OVERRIDES.get(normalize_arabic(canonical_name))
    if override:
        alias_values = sorted(set(alias_values + [canonical_name]))
        canonical_name = override
    all_names_norm = {normalize_arabic(canonical_name)}
    all_names_norm.update(normalize_arabic(alias) for alias in alias_values)
    antihistamine_norms = {normalize_arabic(alias) for alias in ANTIHISTAMINE_ALIASES}
    if entity_type == "Treatment" and all_names_norm.intersection(antihistamine_norms):
        alias_values = sorted(set(alias_values + list(ANTIHISTAMINE_ALIASES) + [canonical_name]))
        canonical_name = ANTIHISTAMINE_CANONICAL
    return canonical_name, alias_values


def correct_entity_type(entity_type, canonical_name, aliases):
    all_names_norm = {normalize_arabic(canonical_name)}
    all_names_norm.update(normalize_arabic(alias) for alias in aliases)
    forced_type_by_norm = {
        normalize_arabic(name): forced_type
        for name, forced_type in FORCED_TYPE_OVERRIDES.items()
    }
    for name in all_names_norm:
        if name in forced_type_by_norm:
            return forced_type_by_norm[name]
    symptom_override_norms = {normalize_arabic(term) for term in SYMPTOM_TYPE_OVERRIDES}
    if all_names_norm.intersection(symptom_override_norms):
        return "Symptom"
    condition_override_norms = {normalize_arabic(term) for term in DISEASE_CONDITION_OVERRIDES}
    if all_names_norm.intersection(condition_override_norms):
        return "DiseaseCondition"
    inflammation_marker_norms = {normalize_arabic(term) for term in INFLAMMATION_MARKERS}
    treatment_marker_norms = {normalize_arabic(term) for term in INFLAMMATION_TREATMENT_MARKERS}
    has_inflammation_marker = any(
        any(marker in name for marker in inflammation_marker_norms)
        for name in all_names_norm
    )
    has_treatment_marker = any(
        any(marker in name for marker in treatment_marker_norms)
        for name in all_names_norm
    )
    if has_inflammation_marker and not has_treatment_marker:
        return "DiseaseCondition"
    return entity_type


def assess_entity_quality(entity_type, canonical_name, aliases):
    normalized = normalize_arabic(canonical_name)
    alias_norms = {normalize_arabic(alias) for alias in aliases}
    low_quality_terms = {normalize_arabic(term) for term in BROAD_LOW_QUALITY_TREATMENTS}
    if entity_type == "Treatment" and (normalized in low_quality_terms or alias_norms.intersection(low_quality_terms)):
        return "low", "false"
    if entity_type == "Treatment" and len(canonical_name) > 80:
        return "low", "false"
    if entity_type == "Treatment" and len(canonical_name.split()) == 1:
        return "medium", "true"
    return "high", "true"


# %% [markdown]
# Prompt construction
# Build a compact entity-only prompt. The current chunks include structured
# `qa_records`, so live extraction sends those instead of duplicating chunk text.


def compact_qa_records_for_prompt(qa_records):
    compact_records = []
    for record in qa_records:
        if not isinstance(record, dict):
            continue
        compact_records.append(
            {
                "subset_id": record.get("subset_id", ""),
                "source_row_number": record.get("source_row_number", ""),
                "split": record.get("split", ""),
                "category": record.get("category", ""),
                "question": truncate_text(record.get("question", ""), 900),
                "answer": truncate_text(record.get("answer", ""), 2600),
            }
        )
    return compact_records


def make_messages(chunk):
    qa_records = parse_json(chunk.get("qa_records"), [])
    has_qa_records = isinstance(qa_records, list) and bool(qa_records)

    system = (
        "You are a careful Arabic medical entity extraction system for a Graph-RAG pipeline.\n"
        "Extract only explicit medical entities from Arabic healthcare Q&A chunks.\n"
        "Do not infer hidden diagnoses.\n"
        "Do not invent treatments, symptoms, tests, or conditions.\n"
        "This is Step 3 only: extract entities only. Do not extract relations.\n"
        "Return valid JSON only."
    )

    required_schema = {
        "chunk_id": chunk["chunk_id"],
        "entities": [
            {
                "local_entity_id": "E1",
                "canonical_name": "Arabic canonical name",
                "entity_type": "DiseaseCondition|Symptom|Treatment|Test",
                "aliases": ["surface form 1", "surface form 2"],
                "mentions": [
                    {
                        "qa_id": "ahd5k_00001",
                        "source_row_number": "123",
                        "surface_form": "exact phrase from text",
                        "field": "question|answer",
                        "evidence": "short exact or near-exact evidence phrase",
                    }
                ],
                "confidence": 0.85,
            }
        ],
    }

    user = {
        "task": "Arabic medical entity extraction for Step 3 of Graph-RAG. Extract entities only.",
        "rules": [
            "Use the exact chunk_id provided.",
            "Use only the four allowed entity types.",
            "Extract only entities explicitly present in the chunk.",
            "Do not infer hidden diagnoses.",
            "Do not invent treatments, tests, symptoms, or conditions.",
            "Keep canonical names in Arabic.",
            "Normalize spelling lightly.",
            "DiseaseCondition: diseases, syndromes, allergies, infections, inflammation, chronic conditions, and named medical conditions. Examples: حساسية، حساسية الصدر، ربو، التهاب، نزلة معوية، ارتكاريا.",
            "Symptom: only patient complaints or signs. Examples: حكة، سعال، بلغم، ضيق تنفس، تعب، صداع.",
            "Treatment: only medications, procedures, therapies, diet substitutions, or explicit medical recommendations.",
            "Do not classify allergens, triggers, or background foods as Treatment unless they are explicitly recommended as treatment or substitution.",
            "Test: only diagnostic tests, lab tests, and imaging. Examples: تحليل الحساسية، RAST Test، تحاليل مخبرية.",
            "Do not extract allergens or triggers as entities unless they are recommended as a treatment/substitution.",
            "Do not extract generic typo/noisy standalone words.",
            "Do not extract background medications unless they are relevant to the medical answer.",
            "Each entity must have at least one mention.",
            "Each mention must include qa_id, source_row_number, surface_form, field, and evidence.",
            "For qa_id, use only subset_id values from qa_records. Never use schema/example qa_ids such as ahd5k_00001 unless that exact value appears in qa_records.",
            "Set confidence between 0 and 1. Use realistic values such as 0.7, 0.85, or 0.95. Do not copy the schema example mechanically.",
            "field must be question or answer.",
            "Evidence must come from the same QA record.",
            "Do not mix evidence across different QA IDs.",
            "Do not extract body parts alone.",
            "Do not extract generic standalone words.",
            "Do not extract categories, body parts, other entities, or relations.",
            "Return valid JSON only matching required_schema.",
        ],
        "allowed_entity_types": sorted(ENTITY_TYPES),
        "required_schema": required_schema,
        "chunk_metadata": {
            "chunk_id": chunk["chunk_id"],
            "category": chunk["category"],
            "category_en": chunk["category_en"],
            "semantic_group": chunk["semantic_group"],
            "qa_ids": parse_json(chunk.get("qa_ids"), []),
            "source_row_numbers": parse_json(chunk.get("source_row_numbers"), []),
            "has_qa_records": has_qa_records,
            "weak_medical_hints": parse_json(chunk.get("top_weak_medical_hints"), []),
        },
    }
    if has_qa_records:
        user["qa_records"] = compact_qa_records_for_prompt(qa_records)
    else:
        user["qa_records"] = []
        user["chunk_text"] = chunk["chunk_text"]
        user["normalized_chunk_text"] = chunk["normalized_chunk_text"]

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": json.dumps(user, ensure_ascii=False)},
    ]


def make_request_record(chunk, provider, model):
    return {
        "request_id": f"entity_request_{chunk['chunk_id']}",
        "chunk_id": chunk["chunk_id"],
        "provider": provider,
        "model": model,
        "messages": make_messages(chunk),
    }


def call_groq(request_record, api_key):
    body = {
        "model": request_record["model"],
        "messages": request_record["messages"],
        "temperature": 0,
        "response_format": {"type": "json_object"},
    }
    req = urllib.request.Request(
        "https://api.groq.com/openai/v1/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "AHD-GraphRAG/0.1",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=90) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return payload["choices"][0]["message"]["content"]


def warning(error_rows, chunk_id, stage, message):
    error_rows.append({"chunk_id": chunk_id, "stage": stage, "severity": "warning", "error": message})


def error(error_rows, chunk_id, stage, message):
    error_rows.append({"chunk_id": chunk_id, "stage": stage, "severity": "error", "error": message})


def truncate_text(value, limit=2000):
    value = str(value or "")
    if len(value) <= limit:
        return value
    return value[:limit] + "...[truncated]"


def collect_http_error_details(exc):
    try:
        body = exc.read().decode("utf-8", errors="replace")
    except Exception:
        body = ""
    headers = dict(exc.headers.items()) if exc.headers else {}
    rate_limit_headers = {
        key: value
        for key, value in headers.items()
        if key.lower().startswith("x-ratelimit")
    }
    return {
        "http_status": exc.code,
        "http_reason": exc.reason,
        "error_body": truncate_text(body),
        "retry_after": headers.get("Retry-After", ""),
        "rate_limit_headers": rate_limit_headers,
    }


def format_raw_error(raw):
    parts = [str(raw.get("error", "unknown error"))]
    if raw.get("http_status"):
        parts.append(f"HTTP status: {raw.get('http_status')}")
    if raw.get("retry_after"):
        parts.append(f"Retry-After: {raw.get('retry_after')}")
    if raw.get("rate_limit_headers"):
        parts.append(f"x-ratelimit headers: {json.dumps(raw.get('rate_limit_headers'), ensure_ascii=False)}")
    if raw.get("error_body"):
        parts.append(f"body: {truncate_text(raw.get('error_body'), 1000)}")
    return " | ".join(part for part in parts if part)


def resolve_qa_id_from_evidence(qa_id, allowed_qa_ids, qa_records, surface_form, evidence, field):
    if qa_id in allowed_qa_ids:
        return qa_id
    candidates = []
    needles = [value for value in (evidence, surface_form) if value]
    for record in qa_records:
        if not isinstance(record, dict):
            continue
        record_id = record.get("subset_id", "")
        if record_id not in allowed_qa_ids:
            continue
        fields_to_check = [field] if field in {"question", "answer"} else ["question", "answer"]
        haystacks = [str(record.get(name, "")) for name in fields_to_check]
        haystacks.extend(str(record.get(f"{name}_norm", "")) for name in fields_to_check)
        if any(needle and any(needle in haystack for haystack in haystacks) for needle in needles):
            candidates.append(record_id)
    return candidates[0] if len(set(candidates)) == 1 else qa_id


# %% [markdown]
# Model output validation
# Parse model JSON, enforce the four allowed entity types, repair noisy Arabic
# forms, and attach each mention back to a real Q&A source.


def validate_extraction(parsed, chunk_lookup, error_rows):
    chunk_id = parsed.get("chunk_id")
    if chunk_id not in chunk_lookup:
        error(error_rows, chunk_id or "", "validation", f"Unknown chunk_id: {chunk_id}")
        return None

    chunk = chunk_lookup[chunk_id]
    allowed_qa_ids = set(parse_json(chunk.get("qa_ids"), []))
    qa_records = parse_json(chunk.get("qa_records"), [])
    source_rows_by_qa = {
        record.get("subset_id"): record.get("source_row_number", "")
        for record in qa_records
        if isinstance(record, dict)
    }

    entities = parsed.get("entities", [])
    if not isinstance(entities, list):
        error(error_rows, chunk_id, "validation", "entities must be a list")
        entities = []

    valid_entities = []
    for entity_index, entity in enumerate(entities):
        if not isinstance(entity, dict):
            error(error_rows, chunk_id, "validation", f"entity[{entity_index}] is not an object")
            continue

        canonical_name = str(entity.get("canonical_name", "")).strip()
        entity_type = str(entity.get("entity_type", "")).strip()
        aliases = entity.get("aliases", [])
        mentions = entity.get("mentions", [])

        if entity_type in ACCIDENTAL_TYPE_TERMS:
            warning(error_rows, chunk_id, "validation", f"Rejected accidental entity type: {entity_type}")
            continue
        if entity_type not in ENTITY_TYPES:
            error(error_rows, chunk_id, "validation", f"Invalid entity type: {entity_type}")
            continue
        if not canonical_name:
            error(error_rows, chunk_id, "validation", f"entity[{entity_index}] missing canonical_name")
            continue
        if not isinstance(aliases, list):
            warning(error_rows, chunk_id, "validation", f"aliases for {canonical_name} was not a list")
            aliases = []
        canonical_name, alias_values = canonicalize_entity_name(entity_type, canonical_name, aliases)
        entity_type = correct_entity_type(entity_type, canonical_name, alias_values)
        if is_generic_standalone(canonical_name):
            warning(error_rows, chunk_id, "validation", f"Rejected generic/noisy standalone entity: {canonical_name}")
            continue
        if is_body_part_only(canonical_name):
            warning(error_rows, chunk_id, "validation", f"Rejected body-part-only entity: {canonical_name}")
            continue
        if is_trigger_or_allergen_standalone(canonical_name):
            warning(error_rows, chunk_id, "validation", f"Rejected standalone allergen/trigger entity: {canonical_name}")
            continue
        if is_background_medication(canonical_name):
            warning(error_rows, chunk_id, "validation", f"Rejected background medication entity: {canonical_name}")
            continue
        if is_category_like_entity(canonical_name):
            warning(error_rows, chunk_id, "validation", f"Rejected category-like entity: {canonical_name}")
            continue
        if is_context_only_entity(canonical_name):
            warning(error_rows, chunk_id, "validation", f"Rejected context-only entity: {canonical_name}")
            continue
        if not isinstance(mentions, list) or not mentions:
            error(error_rows, chunk_id, "validation", f"{canonical_name} has no mentions")
            continue

        try:
            confidence = float(entity.get("confidence", 0.7))
        except (TypeError, ValueError):
            confidence = 0.7
            warning(error_rows, chunk_id, "validation", f"{canonical_name} confidence was invalid")
        confidence = min(1.0, max(0.0, confidence))

        valid_mentions = []
        for mention_index, mention in enumerate(mentions):
            if not isinstance(mention, dict):
                error(error_rows, chunk_id, "validation", f"mention[{mention_index}] is not an object")
                continue

            qa_id = str(mention.get("qa_id", "")).strip()
            surface_form = repair_mojibake(mention.get("surface_form", "")).strip()
            field = str(mention.get("field", "")).strip()
            evidence = repair_mojibake(mention.get("evidence", "")).strip()
            source_row_number = str(mention.get("source_row_number", "")).strip()

            qa_id = resolve_qa_id_from_evidence(qa_id, allowed_qa_ids, qa_records, surface_form, evidence, field)
            if qa_id not in allowed_qa_ids:
                error(error_rows, chunk_id, "validation", f"Dropped mention with invalid qa_id: {qa_id}")
                continue
            if not surface_form:
                error(error_rows, chunk_id, "validation", f"Dropped mention for {canonical_name}: empty surface_form")
                continue
            if not evidence:
                error(error_rows, chunk_id, "validation", f"Dropped mention for {canonical_name}: empty evidence")
                continue
            if field not in {"question", "answer"}:
                warning(error_rows, chunk_id, "validation", f"Invalid field for {canonical_name}: {field}")
                field = "unknown"
            if not source_row_number:
                source_row_number = source_rows_by_qa.get(qa_id, "")

            valid_mentions.append(
                {
                    "qa_id": qa_id,
                    "source_row_number": source_row_number,
                    "surface_form": surface_form[:300],
                    "field": field,
                    "evidence": evidence[:700],
                }
            )

        if not valid_mentions:
            error(error_rows, chunk_id, "validation", f"{canonical_name} has no valid mentions")
            continue

        entity_quality, is_actionable_medical_entity = assess_entity_quality(entity_type, canonical_name, alias_values)
        valid_entities.append(
            {
                "local_entity_id": str(entity.get("local_entity_id", "")).strip(),
                "canonical_name": canonical_name,
                "entity_type": entity_type,
                "aliases": alias_values,
                "mentions": valid_mentions,
                "confidence": round(confidence, 3),
                "entity_quality": entity_quality,
                "is_actionable_medical_entity": is_actionable_medical_entity,
            }
        )

    return {"chunk_id": chunk_id, "entities": valid_entities}


# %% [markdown]
# Entity merging
# Merge validated mentions into stable graph nodes, alias rows, and evidence rows.


def merge_validated_entities(validated_records):
    entities = {}
    mentions = []
    seen_mention_keys = set()

    for record in validated_records:
        chunk_id = record["chunk_id"]
        provider = record.get("provider", "")
        model = record.get("model", "")
        for item in record["entities"]:
            entity_id = stable_entity_id(item["entity_type"], item["canonical_name"])
            entity = entities.setdefault(
                entity_id,
                {
                    "entity_id": entity_id,
                    "canonical_name": item["canonical_name"],
                    "canonical_name_norm": normalize_arabic(item["canonical_name"]),
                    "entity_type": item["entity_type"],
                    "aliases": set(),
                    "source_chunks": set(),
                    "qa_ids": set(),
                    "source_models": set(),
                    "mention_count": 0,
                    "confidence_values": [],
                    "quality_values": [],
                    "actionable_values": [],
                    "alias_support": defaultdict(lambda: {"source_chunks": set(), "qa_ids": set(), "count": 0}),
                },
            )

            entity["aliases"].add(item["canonical_name"])
            entity["aliases"].update(item["aliases"])
            entity["source_chunks"].add(chunk_id)
            if model:
                entity["source_models"].add(model)
            entity["confidence_values"].append(item["confidence"])
            entity["quality_values"].append(item.get("entity_quality", "high"))
            entity["actionable_values"].append(item.get("is_actionable_medical_entity", "true"))

            for mention in item["mentions"]:
                mention_key = stable_mention_key(
                    entity_id,
                    chunk_id,
                    mention["qa_id"],
                    mention["field"],
                    mention["surface_form"],
                    mention["evidence"],
                )
                if mention_key in seen_mention_keys:
                    continue
                seen_mention_keys.add(mention_key)

                entity["mention_count"] += 1
                entity["qa_ids"].add(mention["qa_id"])
                entity["alias_support"][mention["surface_form"]]["count"] += 1
                entity["alias_support"][mention["surface_form"]]["source_chunks"].add(chunk_id)
                entity["alias_support"][mention["surface_form"]]["qa_ids"].add(mention["qa_id"])

                mentions.append(
                    {
                        "mention_id": f"men_llm_{len(mentions) + 1:07d}",
                        "entity_id": entity_id,
                        "canonical_name": entity["canonical_name"],
                        "entity_type": entity["entity_type"],
                        "chunk_id": chunk_id,
                        "qa_id": mention["qa_id"],
                        "source_row_number": mention["source_row_number"],
                        "surface_form": mention["surface_form"],
                        "field": mention["field"],
                        "evidence": mention["evidence"],
                        "extraction_method": "llm_structured_entity_extraction",
                        "provider": provider,
                        "model": model,
                        "confidence": f"{item['confidence']:.3f}",
                    }
                )

    entity_rows = []
    alias_rows = []
    for entity in entities.values():
        avg_confidence = (
            sum(entity["confidence_values"]) / len(entity["confidence_values"])
            if entity["confidence_values"]
            else 0
        )
        sorted_aliases = sorted(entity["aliases"])
        quality_rank = {"low": 0, "medium": 1, "high": 2}
        entity_quality = min(entity["quality_values"], key=lambda value: quality_rank.get(value, 2)) if entity["quality_values"] else "high"
        is_actionable_medical_entity = "false" if "false" in entity["actionable_values"] else "true"
        entity_rows.append(
            {
                "entity_id": entity["entity_id"],
                "canonical_name": entity["canonical_name"],
                "canonical_name_norm": entity["canonical_name_norm"],
                "entity_type": entity["entity_type"],
                "entity_quality": entity_quality,
                "is_actionable_medical_entity": is_actionable_medical_entity,
                "aliases": json.dumps(sorted_aliases, ensure_ascii=False),
                "mention_count": entity["mention_count"],
                "source_chunk_count": len(entity["source_chunks"]),
                "qa_count": len(entity["qa_ids"]),
                "avg_confidence": f"{avg_confidence:.3f}",
                "source_chunks": json.dumps(sorted(entity["source_chunks"]), ensure_ascii=False),
                "source_models": json.dumps(sorted(entity["source_models"]), ensure_ascii=False),
                "qa_ids": json.dumps(sorted(entity["qa_ids"]), ensure_ascii=False),
            }
        )

        for alias in sorted_aliases:
            support = entity["alias_support"].get(alias)
            source_chunks = support["source_chunks"] if support else entity["source_chunks"]
            qa_ids = support["qa_ids"] if support else entity["qa_ids"]
            support_count = support["count"] if support else 0
            alias_rows.append(
                {
                    "alias": alias,
                    "alias_norm": normalize_arabic(alias),
                    "entity_id": entity["entity_id"],
                    "canonical_name": entity["canonical_name"],
                    "entity_type": entity["entity_type"],
                    "support_count": support_count,
                    "source_chunks": json.dumps(sorted(source_chunks), ensure_ascii=False),
                    "qa_ids": json.dumps(sorted(qa_ids), ensure_ascii=False),
                }
            )

    entity_rows.sort(key=lambda row: (row["entity_type"], row["canonical_name_norm"]))
    alias_rows.sort(key=lambda row: (row["entity_type"], row["alias_norm"], row["entity_id"]))
    return entity_rows, mentions, alias_rows


# %% [markdown]
# Batch selection
# Select a limit/batch, skip completed chunks in resume mode, and keep errored
# chunks eligible for retry.


def load_existing_raw_responses():
    existing_records = []
    latest_by_chunk_id = {}

    if not RAW_RESPONSES_JSONL.exists():
        return existing_records, set(), set()

    with RAW_RESPONSES_JSONL.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            existing_records.append(record)
            chunk_id = str(record.get("chunk_id", "")).strip()
            if not chunk_id:
                continue
            latest_by_chunk_id[chunk_id] = record

    completed_chunk_ids = {
        chunk_id
        for chunk_id, record in latest_by_chunk_id.items()
        if record.get("status") == "ok" and str(record.get("response_text", "")).strip()
    }
    errored_chunk_ids = {
        chunk_id
        for chunk_id, record in latest_by_chunk_id.items()
        if chunk_id not in completed_chunk_ids and record.get("status") != "ok"
    }
    return existing_records, completed_chunk_ids, errored_chunk_ids


def select_chunks_for_request(chunks, args, completed_chunk_ids):
    if args.batch_size > 0:
        start = max(0, args.batch_start)
        stop = start + args.batch_size
        candidate_chunks = chunks[start:stop]
    elif args.limit > 0:
        candidate_chunks = chunks[: args.limit]
    else:
        candidate_chunks = chunks

    if args.resume:
        selected_chunks = [chunk for chunk in candidate_chunks if chunk["chunk_id"] not in completed_chunk_ids]
    else:
        selected_chunks = candidate_chunks

    return candidate_chunks, selected_chunks


def write_requests(selected_chunks, provider, model):
    with REQUESTS_JSONL.open("w", encoding="utf-8") as handle:
        for chunk in selected_chunks:
            handle.write(json.dumps(make_request_record(chunk, provider, model), ensure_ascii=False) + "\n")
    return selected_chunks


# %% [markdown]
# LLM calls and resume cache
# Requests are kept as JSONL so long Groq batches can resume without repeating
# successful chunks. Raw responses are temporary audit/cache files; final graph
# data comes from the validated CSV exports.


def run_live_requests(requests, sleep_seconds, append=False, stop_on_rate_limit=False):
    if not requests:
        return 0, False

    api_key = os.getenv("GROQ_API_KEY")
    if is_missing_or_placeholder_key(api_key):
        raise RuntimeError("GROQ_API_KEY is not set. Put your real key in .env first.")

    mode = "a" if append else "w"
    stopped_on_rate_limit = False
    calls_made = 0
    with RAW_RESPONSES_JSONL.open(mode, encoding="utf-8") as handle:
        for index, request_record in enumerate(requests, start=1):
            response_text = ""
            status = "error"
            call_error = ""
            http_details = {}
            for attempt in range(MAX_MODEL_CALL_RETRIES + 1):
                try:
                    response_text = call_groq(request_record, api_key)
                    status = "ok"
                    call_error = ""
                    http_details = {}
                    break
                except urllib.error.HTTPError as exc:
                    http_details = collect_http_error_details(exc)
                    call_error = f"HTTP Error {exc.code}: {exc.reason}"
                    if exc.code == 429 and stop_on_rate_limit:
                        stopped_on_rate_limit = True
                        break
                    if exc.code == 429 and attempt < MAX_MODEL_CALL_RETRIES:
                        retry_after = http_details.get("retry_after", "")
                        try:
                            wait_seconds = float(retry_after) if retry_after else 0
                        except ValueError:
                            wait_seconds = 0
                        wait_seconds = max(wait_seconds, sleep_seconds, RETRY_BACKOFF_SECONDS * (attempt + 1))
                        wait_seconds = min(wait_seconds, MAX_RETRY_WAIT_SECONDS)
                        time.sleep(wait_seconds)
                        continue
                    break
                except Exception as exc:
                    call_error = str(exc)
                    break

            handle.write(
                json.dumps(
                    {
                        "request_id": request_record["request_id"],
                        "chunk_id": request_record["chunk_id"],
                        "provider": DEFAULT_PROVIDER,
                        "model": request_record["model"],
                        "status": status,
                        "error": call_error,
                        **http_details,
                        "response_text": response_text,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
            calls_made += 1
            if stopped_on_rate_limit:
                break
            if index < len(requests) and sleep_seconds:
                time.sleep(sleep_seconds)
    return calls_made, stopped_on_rate_limit


def validate_raw_responses(chunk_lookup):
    validated_records = []
    error_rows = []

    if not RAW_RESPONSES_JSONL.exists():
        return validated_records, error_rows

    latest_by_chunk_id = {}
    with RAW_RESPONSES_JSONL.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            raw = json.loads(line)
            chunk_id = str(raw.get("chunk_id", "")).strip()
            if chunk_id:
                latest_by_chunk_id[chunk_id] = raw

    for raw in latest_by_chunk_id.values():
        chunk_id = raw.get("chunk_id", "")
        if raw.get("status") != "ok":
            error(error_rows, chunk_id, "model_call", format_raw_error(raw))
            continue
        try:
            parsed = extract_json_object(raw.get("response_text", ""))
            validated = validate_extraction(parsed, chunk_lookup, error_rows)
        except Exception as exc:
            validated = None
            error(error_rows, chunk_id, "validation", str(exc))
        if validated:
            validated["provider"] = raw.get("provider", "")
            validated["model"] = raw.get("model", "")
            validated_records.append(validated)

    with VALIDATED_JSONL.open("w", encoding="utf-8") as handle:
        for record in validated_records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    return validated_records, error_rows


# %% [markdown]
# Final exports and report
# Write graph-ready CSV tables plus a compact markdown report.


def write_final_outputs(entity_rows, mention_rows, alias_rows, error_rows):
    with ENTITIES_CSV.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "entity_id",
                "canonical_name",
                "canonical_name_norm",
                "entity_type",
                "entity_quality",
                "is_actionable_medical_entity",
                "aliases",
                "mention_count",
                "source_chunk_count",
                "qa_count",
                "avg_confidence",
                "source_chunks",
                "source_models",
                "qa_ids",
            ],
        )
        writer.writeheader()
        writer.writerows(entity_rows)

    with MENTIONS_CSV.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "mention_id",
                "entity_id",
                "canonical_name",
                "entity_type",
                "chunk_id",
                "qa_id",
                "source_row_number",
                "surface_form",
                "field",
                "evidence",
                "extraction_method",
                "provider",
                "model",
                "confidence",
            ],
        )
        writer.writeheader()
        writer.writerows(mention_rows)

    with ALIASES_CSV.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "alias",
                "alias_norm",
                "entity_id",
                "canonical_name",
                "entity_type",
                "support_count",
                "source_chunks",
                "qa_ids",
            ],
        )
        writer.writeheader()
        writer.writerows(alias_rows)

    with ERRORS_CSV.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["chunk_id", "stage", "severity", "error"])
        writer.writeheader()
        writer.writerows(error_rows)


def report_error_count(error_rows, text):
    return sum(1 for row in error_rows if text in row["error"])


def write_report(
    args,
    mode,
    chunks,
    candidate_chunks,
    selected_chunks,
    validated_records,
    entity_rows,
    mention_rows,
    alias_rows,
    error_rows,
    live_ran,
    existing_successful_count,
    existing_errored_count,
    new_llm_calls,
    append_raw,
    stopped_on_rate_limit,
):
    chunks_with_qa_records = sum(1 for chunk in selected_chunks if parse_json(chunk.get("qa_records"), []))
    chunks_missing_qa_records = len(selected_chunks) - chunks_with_qa_records
    failed_chunks = len({row["chunk_id"] for row in error_rows if row["severity"] == "error"})
    type_counts = Counter(row["entity_type"] for row in entity_rows)
    quality_counts = Counter(row.get("entity_quality", "unknown") for row in entity_rows)
    non_actionable_entities = sum(1 for row in entity_rows if row.get("is_actionable_medical_entity") == "false")
    chunks_by_model = Counter(record.get("model", "unknown") or "unknown" for record in validated_records)
    entities_by_model = Counter(
        record.get("model", "unknown") or "unknown"
        for record in validated_records
        for _ in record.get("entities", [])
    )
    model_used_per_chunk = {
        record["chunk_id"]: record.get("model", "unknown") or "unknown"
        for record in validated_records
    }
    low_conf_entities = sum(1 for row in entity_rows if float(row["avg_confidence"] or 0) < LOW_CONFIDENCE_THRESHOLD)
    low_conf_mentions = sum(1 for row in mention_rows if float(row["confidence"] or 0) < LOW_CONFIDENCE_THRESHOLD)
    chunks_with_entities = {
        chunk_id
        for record in validated_records
        for chunk_id in [record["chunk_id"]]
        if record.get("entities")
    }
    chunks_with_zero_entities = max(0, len(validated_records) - len(chunks_with_entities))
    avg_entities_per_validated_chunk = (
        round(sum(len(record.get("entities", [])) for record in validated_records) / len(validated_records), 2)
        if validated_records
        else 0
    )

    lines = [
        "# AHD Step 3 Entity Extraction Report",
        "",
        "## Purpose",
        "",
        "Step 3 converts graph-train chunks into validated, normalized, evidence-linked Arabic medical entities for graph construction.",
        "",
        "This step is entity-only: no relations, no Neo4j import, no category/body-part/other nodes.",
        "",
        "## Allowed Entity Types",
        "",
        "- DiseaseCondition",
        "- Symptom",
        "- Treatment",
        "- Test",
        "",
        "## Current Run",
        "",
        f"- Provider: `{args.provider}`",
        f"- Model: `{args.model}`",
        f"- Mode used: `{mode}`",
        f"- Live LLM call executed: `{live_ran}`",
        f"- Resume mode: `{args.resume}`",
        f"- Append raw mode: `{append_raw}`",
        f"- Total available chunks: {len(chunks)}",
        f"- Candidate chunks before resume filtering: {len(candidate_chunks)}",
        f"- Existing successful raw responses: {existing_successful_count}",
        f"- Existing errored raw responses: {existing_errored_count}",
        f"- New LLM calls made in this run: {new_llm_calls}",
        f"- Stopped on rate limit: `{stopped_on_rate_limit}`",
        f"- Chunks requested after resume filtering: {len(selected_chunks)}",
        f"- Chunks with qa_records: {chunks_with_qa_records}",
        f"- Chunks missing qa_records: {chunks_missing_qa_records}",
        f"- Total validated chunks after merging old + new responses: {len(validated_records)}",
        f"- Failed chunks: {failed_chunks}",
        f"- Extracted unique entities: {len(entity_rows)}",
        f"- Entity mentions: {len(mention_rows)}",
        f"- Alias count: {len(alias_rows)}",
        f"- Non-actionable / low-signal entities: {non_actionable_entities}",
        f"- Validation/model errors: {len(error_rows)}",
        f"- Average entities per validated chunk: {avg_entities_per_validated_chunk}",
        f"- Chunks with zero entities: {chunks_with_zero_entities}",
        f"- Low-confidence entities (< {LOW_CONFIDENCE_THRESHOLD}): {low_conf_entities}",
        f"- Low-confidence mentions (< {LOW_CONFIDENCE_THRESHOLD}): {low_conf_mentions}",
        f"- Generic/noisy entities rejected: {report_error_count(error_rows, 'Rejected generic')}",
        f"- Standalone allergen/trigger entities rejected: {report_error_count(error_rows, 'Rejected standalone allergen/trigger entity')}",
        f"- Background medication entities rejected: {report_error_count(error_rows, 'Rejected background medication entity')}",
        f"- Category-like entities rejected: {report_error_count(error_rows, 'Rejected category-like entity')}",
        f"- Context-only entities rejected: {report_error_count(error_rows, 'Rejected context-only entity')}",
        f"- BodyPart/category/other accidental outputs rejected: {report_error_count(error_rows, 'Rejected body-part-only entity') + report_error_count(error_rows, 'Rejected accidental entity type')}",
        "",
        "## Entity Type Distribution",
        "",
    ]

    if type_counts:
        for entity_type, count in sorted(type_counts.items()):
            lines.append(f"- {entity_type}: {count}")
    else:
        lines.append("- No entities yet.")

    lines.extend(["", "## Entity Quality", ""])
    if quality_counts:
        for quality, count in sorted(quality_counts.items()):
            lines.append(f"- {quality}: {count}")
        lines.append(f"- is_actionable_medical_entity=false: {non_actionable_entities}")
    else:
        lines.append("- No quality counts yet.")

    lines.extend(
        [
            "",
            "## Model Usage",
            "",
        ]
    )
    if chunks_by_model:
        lines.append("Chunks by model:")
        for model, count in sorted(chunks_by_model.items()):
            lines.append(f"- `{model}`: {count}")
        lines.append("")
        lines.append("Extracted entity records by model before merging:")
        for model, count in sorted(entities_by_model.items()):
            lines.append(f"- `{model}`: {count}")
        lines.append("")
        lines.append("Model used per validated chunk:")
        for chunk_id, model in sorted(model_used_per_chunk.items())[:50]:
            lines.append(f"- `{chunk_id}`: `{model}`")
        if len(model_used_per_chunk) > 50:
            lines.append(f"- ... {len(model_used_per_chunk) - 50} more chunks omitted")
    else:
        lines.append("- No validated model usage yet.")

    lines.extend(
        [
            "",
            "## Output Files",
            "",
            f"- LLM request batch: `{relpath(REQUESTS_JSONL)}`",
            f"- Raw LLM responses: `{relpath(RAW_RESPONSES_JSONL)}`",
            f"- Validated LLM JSON: `{relpath(VALIDATED_JSONL)}`",
            f"- Final entities: `{relpath(ENTITIES_CSV)}`",
            f"- Final mentions/evidence: `{relpath(MENTIONS_CSV)}`",
            f"- Alias dictionary: `{relpath(ALIASES_CSV)}`",
            f"- Errors: `{relpath(ERRORS_CSV)}`",
            "",
            "## Sample Extracted Entities",
            "",
        ]
    )

    mention_by_entity = defaultdict(list)
    for mention in mention_rows:
        mention_by_entity[mention["entity_id"]].append(mention)
    for entity in entity_rows[:3]:
        sample_mention = mention_by_entity.get(entity["entity_id"], [{}])[0]
        lines.extend(
            [
                f"### {entity['entity_id']}",
                "",
                f"- canonical_name: {entity['canonical_name']}",
                f"- entity_type: {entity['entity_type']}",
                f"- aliases: `{entity['aliases']}`",
                f"- mention evidence: {sample_mention.get('evidence', '')}",
                f"- qa_id: {sample_mention.get('qa_id', '')}",
                f"- chunk_id: {sample_mention.get('chunk_id', '')}",
                "",
            ]
        )
    if not entity_rows:
        lines.append("No sample entities available yet.")

    lines.extend(
        [
            "",
            "## Safe Run Commands",
            "",
            "Put your API key in `.env` first:",
            "",
            "```text",
            "GROQ_API_KEY=your_key_here",
            "```",
            "",
            "Prepare 5 Groq requests only:",
            "",
            "```powershell",
            "python scripts\\step03_extract_entities.py --provider groq --model llama-3.3-70b-versatile --limit 5 --prepare-only",
            "```",
            "",
            "Run live on 5 Groq chunks:",
            "",
            "```powershell",
            "python scripts\\step03_extract_entities.py --provider groq --model llama-3.3-70b-versatile --limit 5 --run-live --force-overwrite --sleep-seconds 8",
            "```",
            "",
            "Resume safely to 20 total chunks. If 5 chunks already succeeded, this calls only the missing 15:",
            "",
            "```powershell",
            "python scripts\\step03_extract_entities.py --provider groq --model llama-3.3-70b-versatile --limit 20 --run-live --resume --sleep-seconds 30 --stop-on-rate-limit",
            "```",
            "",
            "Run the next explicit batch:",
            "",
            "```powershell",
            "python scripts\\step03_extract_entities.py --provider groq --model llama-3.3-70b-versatile --batch-start 20 --batch-size 20 --run-live --resume --sleep-seconds 30 --stop-on-rate-limit",
            "```",
            "",
            "Use a smaller Groq model for bulk extraction after checking your Groq console model/rate-limit page:",
            "",
            "```powershell",
            "python scripts\\step03_extract_entities.py --provider groq --model <smaller_model_id> --batch-start 15 --batch-size 20 --run-live --resume --sleep-seconds 10 --stop-on-rate-limit",
            "```",
            "",
            "Validate existing responses:",
            "",
            "```powershell",
            "python scripts\\step03_extract_entities.py --validate-existing",
            "```",
        ]
    )

    REPORT_MD.write_text("\n".join(lines), encoding="utf-8-sig")


# %% [markdown]
# CLI entry point
# Default mode prepares request JSONL. `--run-live` calls Groq. `--resume`
# appends missing chunks only. `--validate-existing` rebuilds CSV exports from
# saved raw responses.


def load_chunks():
    chunks = []
    with CHUNKS_JSONL.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                chunks.append(json.loads(line))
    return chunks


def load_requests():
    if not REQUESTS_JSONL.exists():
        return []
    return [json.loads(line) for line in REQUESTS_JSONL.read_text(encoding="utf-8").splitlines() if line.strip()]


def mode_from_args(args):
    modes = [args.prepare_only, args.run_live, args.validate_existing]
    if sum(1 for mode in modes if mode) > 1:
        raise RuntimeError("Choose only one mode: --prepare-only, --run-live, or --validate-existing")
    if args.run_live:
        return "run-live"
    if args.validate_existing:
        return "validate-existing"
    return "prepare-only"


def main():
    load_env_file()

    parser = argparse.ArgumentParser(description="Step 3 entity-only Groq LLM extraction for AHD Graph-RAG.")
    parser.add_argument("--provider", choices=["groq"], default=DEFAULT_PROVIDER)
    parser.add_argument("--model", default=DEFAULT_GROQ_MODEL)
    parser.add_argument("--limit", type=int, default=0, help="Number of chunks to request. 0 means all.")
    parser.add_argument("--sleep-seconds", type=float, default=0.0)
    parser.add_argument("--prepare-only", action="store_true")
    parser.add_argument("--run-live", action="store_true")
    parser.add_argument("--validate-existing", action="store_true")
    parser.add_argument("--force-overwrite", action="store_true")
    parser.add_argument("--resume", action="store_true", help="Skip chunk_ids that already have successful raw responses.")
    parser.add_argument("--append-raw", action="store_true", help="Append new raw responses instead of overwriting.")
    parser.add_argument("--batch-start", type=int, default=0, help="Start index for an explicit chunk batch.")
    parser.add_argument("--batch-size", type=int, default=0, help="Batch size. 0 uses --limit behavior.")
    parser.add_argument("--retry-errors", action="store_true", help="Keep errored chunk_ids eligible for retry in resume runs.")
    parser.add_argument("--stop-on-rate-limit", action="store_true", help="Write the first 429 response, stop the batch, and validate existing outputs.")
    args = parser.parse_args()

    mode = mode_from_args(args)
    if args.resume and args.force_overwrite:
        raise RuntimeError("Use either --resume or --force-overwrite, not both.")
    if args.batch_start < 0:
        raise RuntimeError("--batch-start must be >= 0")
    if args.batch_size < 0:
        raise RuntimeError("--batch-size must be >= 0")
    if args.limit < 0:
        raise RuntimeError("--limit must be >= 0")
    ENTITY_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    chunks = load_chunks()
    chunk_lookup = {chunk["chunk_id"]: chunk for chunk in chunks}
    existing_records, completed_chunk_ids, errored_chunk_ids = load_existing_raw_responses()
    candidate_chunks, selected_chunks = select_chunks_for_request(chunks, args, completed_chunk_ids)
    append_raw = args.append_raw or args.resume
    existing_successful_count = len(completed_chunk_ids)
    existing_errored_count = len(errored_chunk_ids)
    new_llm_calls = 0
    stopped_on_rate_limit = False
    live_ran = False
    validated_records = []
    error_rows = []
    entity_rows = []
    mention_rows = []
    alias_rows = []

    if mode in {"prepare-only", "run-live"}:
        selected_chunks = write_requests(selected_chunks, args.provider, args.model)

    if mode == "run-live":
        raw_exists = RAW_RESPONSES_JSONL.exists() and RAW_RESPONSES_JSONL.stat().st_size > 0
        if raw_exists and not args.resume and not args.force_overwrite:
            raise RuntimeError(
                f"{relpath(RAW_RESPONSES_JSONL)} already exists. Use --resume to append missing chunks or --force-overwrite to replace it."
            )
        if raw_exists and args.force_overwrite:
            append_raw = False
        requests = load_requests()
        new_llm_calls, stopped_on_rate_limit = run_live_requests(
            requests,
            args.sleep_seconds,
            append=append_raw,
            stop_on_rate_limit=args.stop_on_rate_limit,
        )
        live_ran = True
        validated_records, error_rows = validate_raw_responses(chunk_lookup)
        entity_rows, mention_rows, alias_rows = merge_validated_entities(validated_records)
        write_final_outputs(entity_rows, mention_rows, alias_rows, error_rows)
    elif mode == "validate-existing":
        candidate_chunks = chunks
        selected_chunks = chunks
        validated_records, error_rows = validate_raw_responses(chunk_lookup)
        entity_rows, mention_rows, alias_rows = merge_validated_entities(validated_records)
        write_final_outputs(entity_rows, mention_rows, alias_rows, error_rows)

    write_report(
        args,
        mode,
        chunks,
        candidate_chunks,
        selected_chunks,
        validated_records,
        entity_rows,
        mention_rows,
        alias_rows,
        error_rows,
        live_ran,
        existing_successful_count,
        existing_errored_count,
        new_llm_calls,
        append_raw,
        stopped_on_rate_limit,
    )
    print(
        json.dumps(
            {
                "mode": mode,
                "provider": args.provider,
                "model": args.model,
                "live_llm_call_executed": live_ran,
                "resume": args.resume,
                "append_raw": append_raw,
                "available_chunks": len(chunks),
                "candidate_chunks": len(candidate_chunks),
                "existing_successful_raw_responses": existing_successful_count,
                "existing_errored_raw_responses": existing_errored_count,
                "new_llm_calls": new_llm_calls,
                "stopped_on_rate_limit": stopped_on_rate_limit,
                "requested_chunks_after_resume_filtering": len(selected_chunks),
                "validated_chunks": len(validated_records),
                "entities": len(entity_rows),
                "mentions": len(mention_rows),
                "aliases": len(alias_rows),
                "errors": len(error_rows),
                "requests_jsonl": relpath(REQUESTS_JSONL),
                "entities_csv": relpath(ENTITIES_CSV),
                "mentions_csv": relpath(MENTIONS_CSV),
                "aliases_csv": relpath(ALIASES_CSV),
                "report_md": relpath(REPORT_MD),
            },
            ensure_ascii=True,
            indent=2,
        )
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

