import argparse
import csv
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TRIAL_DIR = ROOT / "outputs" / "05_trial_graph_v1"
IMPORT_DIR = TRIAL_DIR / "import"
STEP8_DIR = TRIAL_DIR / "query_understanding"
REPORT_MD = ROOT / "reports" / "trial_graph_v1_step8_query_understanding_report.md"

ENTITIES_CSV = IMPORT_DIR / "trial_graph_v1_entities.csv"
QA_SOURCES_CSV = IMPORT_DIR / "trial_graph_v1_qa_sources.csv"

QUERY_UNDERSTANDING_JSON = STEP8_DIR / "trial_graph_v1_query_understanding.json"
QUERY_UNDERSTANDING_CSV = STEP8_DIR / "trial_graph_v1_query_understanding.csv"
QUERY_SET_CSV = STEP8_DIR / "trial_graph_v1_query_set.csv"

ARABIC_DIACRITICS_RE = re.compile(r"[\u064b-\u065f\u0670\u06d6-\u06ed]")
TATWEEL_RE = re.compile(r"\u0640+")
WHITESPACE_RE = re.compile(r"\s+")
TOKEN_RE = re.compile(r"[\w\u0600-\u06ff]+", re.UNICODE)
ARABIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")
ARABIC_LETTER_NORMALIZATION = str.maketrans(
    {
        "أ": "ا",
        "إ": "ا",
        "آ": "ا",
        "ٱ": "ا",
        "ى": "ي",
        "ئ": "ي",
        "ؤ": "و",
        "ة": "ه",
    }
)
PUNCTUATION_NORMALIZATION = str.maketrans({"؟": "?", "،": ",", "؛": ";", "“": '"', "”": '"'})

DEFAULT_QUERIES = [
    "ما علاج حساسية الصدر مع السعال والبلغم؟",
    "عندي كحة وبلغم هل هذا ربو؟",
    "ما التحاليل المناسبة لفقر الدم؟",
    "ما أسباب صداع مع دوخة؟",
    "ما علاج الجلطة الدماغية؟",
    "هل ضيق التنفس من أعراض الحساسية؟",
    "ما الفحوصات المطلوبة للسكري؟",
    "ما علاج التهاب المفاصل وألم المفاصل؟",
]

QUERY_EXPANSIONS = {
    "كحه": ["سعال"],
    "كحة": ["سعال"],
    "حساسيه الصدر": ["حساسية", "ربو"],
    "حساسية الصدر": ["حساسية", "ربو"],
    "انيميا": ["فقر الدم"],
    "أنيميا": ["فقر الدم"],
    "ضيق النفس": ["ضيق تنفس"],
    "نهجان": ["ضيق تنفس"],
    "سكر": ["مرض السكري"],
}

CANONICAL_FAMILY_OVERRIDES = {
    "بلغم": "بلغم",
    "البلغم": "بلغم",
    "مرض السكري": "مرض السكري",
    "السكري": "مرض السكري",
    "سكري": "مرض السكري",
    "داء السكري": "مرض السكري",
    "فقر الدم": "فقر الدم",
    "فقر دم": "فقر الدم",
    "انيميا": "فقر الدم",
    "ضيق تنفس": "ضيق تنفس",
    "ضيق النفس": "ضيق تنفس",
}

GENERIC_ENTITY_SEED_BLOCKLIST = {
    "الدم",
    "دم",
    "التهاب",
    "تهاب",
    "جرعه",
    "جرعة",
    "علاج",
    "مرض",
    "تحليل",
    "تحاليل",
    "الم",
    "ألم",
}

INTENT_RULES = [
    {
        "intent": "treatment_request",
        "answer_focus": "treatments and medical recommendations",
        "target_relation_types": ["TREATED_BY", "TREATS"],
        "keywords": ["علاج", "دواء", "ادويه", "ادوية", "اعالج", "مضاد", "جرعه", "عملية", "استخدام"],
    },
    {
        "intent": "diagnostic_test_request",
        "answer_focus": "diagnostic tests and investigations",
        "target_relation_types": ["DIAGNOSED_BY", "DIAGNOSES", "INVESTIGATED_BY", "INVESTIGATES"],
        "keywords": ["تحليل", "تحاليل", "فحص", "فحوصات", "اختبار", "اشعه", "تصوير", "تشخيص"],
    },
    {
        "intent": "symptom_check",
        "answer_focus": "symptoms and possible associated conditions",
        "target_relation_types": ["HAS_SYMPTOM", "SYMPTOM_OF"],
        "keywords": ["اعراض", "عرض", "اشعر", "عندي", "اعاني", "الم", "كحه", "سعال", "بلغم", "دوخه", "صداع", "ضيق"],
    },
    {
        "intent": "cause_or_condition_question",
        "answer_focus": "possible conditions and relation evidence",
        "target_relation_types": ["HAS_SYMPTOM", "SYMPTOM_OF"],
        "keywords": ["سبب", "اسباب", "يسبب", "هل هذا", "هل يمكن", "ما هو", "ماهي"],
    },
]


def relpath(path):
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def write_csv(path, rows, fieldnames):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def parse_json_list(value):
    if not value:
        return []
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return []
    return parsed if isinstance(parsed, list) else []


def normalize_arabic(value):
    text = "" if value is None else str(value)
    text = text.translate(ARABIC_DIGITS)
    text = TATWEEL_RE.sub("", text)
    text = ARABIC_DIACRITICS_RE.sub("", text)
    text = text.translate(ARABIC_LETTER_NORMALIZATION)
    text = text.translate(PUNCTUATION_NORMALIZATION)
    text = WHITESPACE_RE.sub(" ", text)
    return text.strip().lower()


def contains_phrase(normalized_text, normalized_phrase):
    if not normalized_phrase:
        return False
    escaped = re.escape(normalized_phrase)
    direct_pattern = rf"(?<!\w){escaped}(?!\w)"
    article_pattern = rf"(?<!\w)ال{escaped}(?!\w)"
    proclitic_pattern = rf"(?<!\w)[وبفكل]{escaped}(?!\w)"
    return (
        re.search(direct_pattern, normalized_text, flags=re.UNICODE) is not None
        or re.search(article_pattern, normalized_text, flags=re.UNICODE) is not None
        or re.search(proclitic_pattern, normalized_text, flags=re.UNICODE) is not None
    )


def tokenize(value):
    return TOKEN_RE.findall(normalize_arabic(value))


def enrich_query_text_for_matching(normalized_query):
    tokens = TOKEN_RE.findall(normalized_query)
    variants = []
    for token in tokens:
        if len(token) <= 3:
            continue
        if token.startswith("لل") and len(token) > 4:
            stem = token[2:]
            variants.append(stem)
            variants.append(f"ال{stem}")
        elif token[0] in {"ل", "ب", "ف", "و", "ك"}:
            variants.append(token[1:])
    if not variants:
        return normalized_query
    return normalize_arabic(" ".join([normalized_query] + variants))


def alias_is_compatible(canonical_name, alias):
    canonical_tokens = set(tokenize(canonical_name))
    alias_tokens = set(tokenize(alias))
    if not canonical_tokens or not alias_tokens:
        return False
    if len(canonical_tokens) == 1:
        return next(iter(canonical_tokens)) in alias_tokens
    return len(canonical_tokens & alias_tokens) / len(canonical_tokens) >= 0.5


def clean_aliases(canonical_name, aliases):
    cleaned = []
    seen = set()
    for alias in aliases:
        alias = str(alias).strip()
        alias_norm = normalize_arabic(alias)
        if not alias or alias_norm in seen:
            continue
        if alias_is_compatible(canonical_name, alias):
            cleaned.append(alias)
            seen.add(alias_norm)
    return cleaned


def load_entity_lexicon():
    rows = read_csv(ENTITIES_CSV)
    lexicon = []
    for row in rows:
        canonical_norm = normalize_arabic(row.get("canonical_name", ""))
        if canonical_norm in GENERIC_ENTITY_SEED_BLOCKLIST:
            continue
        names = [("exact", row.get("canonical_name", ""))]
        names.extend(("alias", alias) for alias in clean_aliases(row.get("canonical_name", ""), parse_json_list(row.get("aliases", ""))))
        seen = set()
        for match_type, name in names:
            norm = normalize_arabic(name)
            if not norm or norm in seen:
                continue
            if norm in GENERIC_ENTITY_SEED_BLOCKLIST:
                continue
            seen.add(norm)
            lexicon.append(
                {
                    "surface": name,
                    "surface_norm": norm,
                    "match_type": match_type,
                    "entity_id": row.get("entity_id", ""),
                    "canonical_name": row.get("canonical_name", ""),
                    "canonical_name_norm": row.get("canonical_name_norm", normalize_arabic(row.get("canonical_name", ""))),
                    "entity_type": row.get("entity_type", ""),
                    "entity_quality": row.get("entity_quality", ""),
                    "mention_count": int(row.get("mention_count") or 0),
                }
            )
    lexicon.sort(key=lambda item: (len(item["surface_norm"]), item["mention_count"]), reverse=True)
    return lexicon


def canonical_family(canonical_name):
    normalized = normalize_arabic(canonical_name)
    return CANONICAL_FAMILY_OVERRIDES.get(normalized, normalized)


def entity_specificity(entity):
    return len(tokenize(entity.get("canonical_name", "")))


def match_priority(match_type):
    return {"exact": 3, "alias": 2, "expansion": 1, "vector": 0}.get(match_type, 0)


def should_keep_both(existing, candidate):
    existing_tokens = set(tokenize(existing.get("canonical_name", "")))
    candidate_tokens = set(tokenize(candidate.get("canonical_name", "")))
    if not existing_tokens or not candidate_tokens:
        return False
    if existing_tokens == candidate_tokens:
        return False
    if existing_tokens < candidate_tokens or candidate_tokens < existing_tokens:
        return existing.get("match_type") == "exact" or candidate.get("match_type") == "exact"
    return False


def dedupe_entities(entities):
    kept = []
    for entity in sorted(
        entities,
        key=lambda item: (
            match_priority(item.get("match_type", "")),
            entity_specificity(item),
            int(item.get("mention_count") or 0),
        ),
        reverse=True,
    ):
        family = canonical_family(entity.get("canonical_name", ""))
        duplicate_index = None
        keep_as_specific_pair = False
        for index, existing in enumerate(kept):
            if existing.get("entity_id") == entity.get("entity_id"):
                duplicate_index = index
                break
            if canonical_family(existing.get("canonical_name", "")) == family:
                if should_keep_both(existing, entity):
                    keep_as_specific_pair = True
                    continue
                duplicate_index = index
                break
        if duplicate_index is None or keep_as_specific_pair:
            kept.append(entity)
            continue
        existing = kept[duplicate_index]
        existing_score = (
            match_priority(existing.get("match_type", "")),
            entity_specificity(existing),
            int(existing.get("mention_count") or 0),
        )
        candidate_score = (
            match_priority(entity.get("match_type", "")),
            entity_specificity(entity),
            int(entity.get("mention_count") or 0),
        )
        if candidate_score > existing_score:
            kept[duplicate_index] = entity
    return kept


def expand_query(normalized_query):
    expansions = []
    for source, targets in QUERY_EXPANSIONS.items():
        source_norm = normalize_arabic(source)
        if contains_phrase(normalized_query, source_norm):
            expansions.extend(targets)
    return sorted(set(expansions))


def keyword_position(normalized_query, keyword):
    keyword_norm = normalize_arabic(keyword)
    match = re.search(rf"(?<!\w)(?:ال)?{re.escape(keyword_norm)}(?!\w)", normalized_query, flags=re.UNICODE)
    return match.start() if match else 10_000


def classify_intents(normalized_query):
    matches = []
    for rule in INTENT_RULES:
        hit_keywords = []
        positions = []
        for keyword in rule["keywords"]:
            if contains_phrase(normalized_query, normalize_arabic(keyword)):
                hit_keywords.append(keyword)
                positions.append(keyword_position(normalized_query, keyword))
        if hit_keywords:
            matches.append(
                {
                    "intent": rule["intent"],
                    "answer_focus": rule["answer_focus"],
                    "target_relation_types": rule["target_relation_types"],
                    "matched_keywords": hit_keywords,
                    "first_keyword_position": min(positions) if positions else 10_000,
                }
            )
    if not matches:
        matches.append(
            {
                "intent": "general_medical_question",
                "answer_focus": "retrieve semantically similar entities, relations, and evidence",
                "target_relation_types": ["HAS_SYMPTOM", "TREATED_BY", "DIAGNOSED_BY", "INVESTIGATED_BY"],
                "matched_keywords": [],
                "first_keyword_position": 10_000,
            }
        )
    matches.sort(key=lambda item: item["first_keyword_position"])
    for index, item in enumerate(matches):
        item["intent_role"] = "primary" if index == 0 else "secondary"
        item["intent_weight"] = 1.0 if index == 0 else 0.4
    return matches


def detect_entities(normalized_query, lexicon, limit=12, forced_match_type=None):
    matches = []
    seen_entities = set()
    for item in lexicon:
        if item["entity_id"] in seen_entities:
            continue
        if len(item["surface_norm"]) < 3:
            continue
        if contains_phrase(normalized_query, item["surface_norm"]):
            matched = dict(item)
            if forced_match_type:
                matched["match_type"] = forced_match_type
            matches.append(matched)
            seen_entities.add(item["entity_id"])
        if len(matches) >= limit:
            break
    return dedupe_entities(matches)


def detect_expansion_candidate_entities(expansions, lexicon, hard_entity_ids, limit=12):
    if not expansions:
        return []
    expansion_query = normalize_arabic(" ".join(expansions))
    candidates = []
    for item in detect_entities(expansion_query, lexicon, limit=limit, forced_match_type="expansion"):
        if item["entity_id"] not in hard_entity_ids:
            candidates.append(item)
    return dedupe_entities(candidates)


def build_retrieval_plan(intents, detected_entities):
    relation_types = []
    relation_type_weights = {}
    for intent in intents:
        for relation_type in intent["target_relation_types"]:
            if relation_type not in relation_types:
                relation_types.append(relation_type)
            relation_type_weights[relation_type] = max(
                relation_type_weights.get(relation_type, -0.2),
                intent.get("intent_weight", 0.4),
            )
    seed_types = sorted({entity["entity_type"] for entity in detected_entities})
    if detected_entities:
        mode = "entity_seeded_vector_then_graph"
    else:
        mode = "semantic_vector_first"
    return {
        "retrieval_mode": mode,
        "semantic_search_targets": ["entity", "evidence", "qa"],
        "graph_expansion": {
            "start_from_detected_entities": bool(detected_entities),
            "seed_entity_types": seed_types,
            "target_relation_types": relation_types,
            "relation_type_weights": relation_type_weights,
            "default_relation_weight": -0.2,
            "max_hops": 1,
        },
        "reranking_signals": ["embedding_similarity", "entity_exact_match", "relation_type_match", "evidence_confidence"],
    }


def build_warnings(intents):
    warnings = []
    if any(intent["intent"] == "cause_or_condition_question" for intent in intents):
        warnings.append(
            "Current trial graph has no direct CAUSES/CAUSED_BY/RISK_FACTOR_FOR relation. Step 9 should approximate cause questions with SYMPTOM_OF/HAS_SYMPTOM and mark this limitation."
        )
    return warnings


def make_query_set(args):
    queries = []
    if args.query:
        queries.extend(args.query)
    elif args.from_qa:
        qa_rows = read_csv(QA_SOURCES_CSV)
        for row in qa_rows[: args.limit]:
            queries.append(row.get("question", ""))
    else:
        queries.extend(DEFAULT_QUERIES[: args.limit] if args.limit else DEFAULT_QUERIES)
    rows = [{"query_id": f"trial_query_{index:03d}", "query": query} for index, query in enumerate(queries, start=1)]
    write_csv(QUERY_SET_CSV, rows, ["query_id", "query"])
    return rows


def understand_query(row, lexicon):
    normalized = normalize_arabic(row["query"])
    matchable_normalized = enrich_query_text_for_matching(normalized)
    expansions = expand_query(matchable_normalized)
    expanded_normalized = normalize_arabic(" ".join([matchable_normalized] + expansions))
    intents = classify_intents(expanded_normalized)
    entities = detect_entities(matchable_normalized, lexicon)
    semantic_candidates = detect_expansion_candidate_entities(expansions, lexicon, {item["entity_id"] for item in entities})
    return {
        "query_id": row["query_id"],
        "query": row["query"],
        "normalized_query": normalized,
        "expanded_terms": expansions,
        "expanded_normalized_query": expanded_normalized,
        "intents": intents,
        "detected_entities": entities,
        "semantic_candidate_entities": semantic_candidates,
        "warnings": build_warnings(intents),
        "retrieval_plan": build_retrieval_plan(intents, entities),
    }


def flatten_result(result):
    return {
        "query_id": result["query_id"],
        "query": result["query"],
        "normalized_query": result["normalized_query"],
        "expanded_terms": json.dumps(result["expanded_terms"], ensure_ascii=False),
        "primary_intent": result["intents"][0]["intent"],
        "all_intents": json.dumps([item["intent"] for item in result["intents"]], ensure_ascii=False),
        "target_relation_types": json.dumps(result["retrieval_plan"]["graph_expansion"]["target_relation_types"], ensure_ascii=False),
        "detected_entity_names": json.dumps([item["canonical_name"] for item in result["detected_entities"]], ensure_ascii=False),
        "detected_entity_types": json.dumps([item["entity_type"] for item in result["detected_entities"]], ensure_ascii=False),
        "detected_entity_match_types": json.dumps([item["match_type"] for item in result["detected_entities"]], ensure_ascii=False),
        "semantic_candidate_entity_names": json.dumps([item["canonical_name"] for item in result["semantic_candidate_entities"]], ensure_ascii=False),
        "relation_type_weights": json.dumps(result["retrieval_plan"]["graph_expansion"]["relation_type_weights"], ensure_ascii=False),
        "warnings": json.dumps(result["warnings"], ensure_ascii=False),
        "retrieval_mode": result["retrieval_plan"]["retrieval_mode"],
    }


def write_report(results):
    intent_counts = {}
    entity_type_counts = {}
    for result in results:
        for intent in result["intents"]:
            intent_counts[intent["intent"]] = intent_counts.get(intent["intent"], 0) + 1
        for entity in result["detected_entities"]:
            entity_type_counts[entity["entity_type"]] = entity_type_counts.get(entity["entity_type"], 0) + 1

    lines = [
        "# Trial Graph v1 Step 8 Query Understanding Report",
        "",
        "This implements the medical query-understanding layer before semantic retrieval or generation.",
        "",
        "## Scope",
        "",
        "- Arabic query normalization",
        "- Lightweight synonym/variant expansion",
        "- Intent classification",
        "- Entity/alias detection against the frozen trial graph with `match_type`",
        "- Separation between hard detected entities and semantic/expansion candidate entities",
        "- Intent-weighted relation planning",
        "- Retrieval plan construction for Step 9A/9C",
        "",
        "## Counts",
        "",
        f"- Queries processed: {len(results)}",
        f"- Queries with detected graph entities: {sum(1 for item in results if item['detected_entities'])}",
        "",
        "## Intent Distribution",
        "",
    ]
    for intent, count in sorted(intent_counts.items()):
        lines.append(f"- {intent}: {count}")
    lines.extend(["", "## Detected Entity Type Distribution", ""])
    for entity_type, count in sorted(entity_type_counts.items()):
        lines.append(f"- {entity_type}: {count}")
    lines.extend(
        [
            "",
            "## Output Files",
            "",
            f"- Query set: `{relpath(QUERY_SET_CSV)}`",
            f"- Query understanding JSON: `{relpath(QUERY_UNDERSTANDING_JSON)}`",
            f"- Query understanding CSV: `{relpath(QUERY_UNDERSTANDING_CSV)}`",
            "",
            "## Step 9 Planning Notes",
            "",
            "- Treat `detected_entities` with `match_type=exact` or strong `alias` as hard query seeds.",
            "- Treat `semantic_candidate_entities` as soft expansion candidates, not exact links.",
            "- Use `relation_type_weights` to prioritize primary intent relations over secondary intent relations.",
            "- Cause/condition questions include a warning because the current graph has no direct `CAUSES` relation.",
            "",
            "## Next Step From Mix.png",
            "",
            "Use these query-understanding records for Step 9A semantic retrieval over `outputs/05_trial_graph_v1/embeddings/trial_graph_v1_embeddings.jsonl`.",
        ]
    )
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", action="append", help="Arabic medical query. Can be repeated.")
    parser.add_argument("--from-qa", action="store_true", help="Use frozen QA source questions as a query set.")
    parser.add_argument("--limit", type=int, default=8)
    args = parser.parse_args()

    STEP8_DIR.mkdir(parents=True, exist_ok=True)
    lexicon = load_entity_lexicon()
    query_rows = make_query_set(args)
    results = [understand_query(row, lexicon) for row in query_rows]
    QUERY_UNDERSTANDING_JSON.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    write_csv(
        QUERY_UNDERSTANDING_CSV,
        [flatten_result(result) for result in results],
        [
            "query_id",
            "query",
            "normalized_query",
            "expanded_terms",
            "primary_intent",
            "all_intents",
            "target_relation_types",
            "detected_entity_names",
            "detected_entity_types",
            "detected_entity_match_types",
            "semantic_candidate_entity_names",
            "relation_type_weights",
            "warnings",
            "retrieval_mode",
        ],
    )
    write_report(results)
    print(
        json.dumps(
            {
                "queries_processed": len(results),
                "query_understanding_json": relpath(QUERY_UNDERSTANDING_JSON),
                "query_understanding_csv": relpath(QUERY_UNDERSTANDING_CSV),
                "report_md": relpath(REPORT_MD),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
