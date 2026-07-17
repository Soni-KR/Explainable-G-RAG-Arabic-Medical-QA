from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from dataclasses import asdict
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.models import ExtractedMedicalPhrase, LinkedMedicalEntity, QueryEntityLinkingResult
from src.neo4j_repository import Neo4jRepository
from src.step08a_normalize_query import normalize_query


MATCH_SCORES = {
    "exact_canonical": 1.0,
    "exact_alias": 0.95,
    "article_normalized": 0.90,
    "medical_variant": 0.92,
    "none": 0.0,
}
MEDICAL_SPELLING_VARIANTS = {
    "بروجسترو": "بروجسترون",
    "البروجسترو": "البروجسترون",
    "بروجستيرون": "بروجسترون",
    "البروجستيرون": "البروجسترون",
    "بروجيستيرون": "بروجسترون",
    "البروجيستيرون": "البروجسترون",
}
GENERIC_PHRASES = {
    "دواء",
    "علاج",
    "تحاليل",
    "تحليل",
    "مرض",
    "دم",
    "التهاب",
    "جرعه",
    "الم",
    "نسبه",
}


def strip_arabic_definite_article(value: str) -> str:
    normalized = normalize_query(value).normalized_query
    if normalized.startswith("ال") and len(normalized) > 2:
        return normalized[2:]
    return normalized


def medical_spelling_variants(value: str) -> list[str]:
    tokens = normalize_query(value).normalized_query.split()
    variant = " ".join(MEDICAL_SPELLING_VARIANTS.get(token, token) for token in tokens)
    return [variant] if variant and variant != " ".join(tokens) else []


def build_term_records(phrases: list[ExtractedMedicalPhrase]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for index, phrase in enumerate(phrases):
        normalized = phrase.normalized_form
        stripped = strip_arabic_definite_article(normalized)
        forms = [normalized]
        forms.extend(medical_spelling_variants(normalized))
        if stripped and stripped != normalized:
            forms.append(stripped)

        for form in forms:
            key = (str(index), form)
            if key in seen:
                continue
            seen.add(key)
            records.append(
                {
                    "term_id": str(index),
                    "original_normalized_form": normalized,
                    "normalized_form": form,
                    # Aliases in Neo4j currently follow the imported source form; include both raw and normalized forms.
                    "alias_forms": sorted({phrase.surface_form, normalized, form}),
                }
            )
    return records


def infer_match_type(candidate: dict[str, Any], phrase: ExtractedMedicalPhrase) -> str:
    matched_form = candidate.get("matched_normalized_form", "")
    if candidate.get("canonical_match") and matched_form == phrase.normalized_form:
        return "exact_canonical"
    if candidate.get("alias_matches"):
        return "exact_alias"
    if candidate.get("canonical_match") and matched_form == strip_arabic_definite_article(phrase.normalized_form):
        return "article_normalized"
    if matched_form in medical_spelling_variants(phrase.normalized_form):
        return "medical_variant"
    return "none"


def alias_is_compatible(candidate: dict[str, Any], phrase: ExtractedMedicalPhrase) -> bool:
    if not candidate.get("alias_matches"):
        return True
    canonical_norm = normalize_query(candidate.get("canonical_name", "")).normalized_query
    phrase_norm = phrase.normalized_form
    if canonical_norm == phrase_norm:
        return True
    canonical_tokens = set(canonical_norm.split())
    phrase_tokens = set(phrase_norm.split())
    return bool(canonical_tokens.intersection(phrase_tokens))


def candidate_summary(candidate: dict[str, Any], match_type: str) -> dict[str, Any]:
    return {
        "entity_id": candidate.get("entity_id", ""),
        "canonical_name": candidate.get("canonical_name", ""),
        "entity_type": candidate.get("entity_type", ""),
        "match_type": match_type,
        "match_score": MATCH_SCORES.get(match_type, 0.0),
    }


def choose_link(phrase: ExtractedMedicalPhrase, candidates: list[dict[str, Any]]) -> LinkedMedicalEntity:
    warnings: list[str] = []
    if phrase.normalized_form in GENERIC_PHRASES and not candidates:
        warnings.append("Generic phrase left unresolved because no exact graph entity matched.")

    ranked: list[tuple[str, dict[str, Any]]] = []
    for candidate in candidates:
        if not alias_is_compatible(candidate, phrase):
            warnings.append(
                f"Ignored alias-only match to {candidate.get('canonical_name', '')} because it does not share tokens with the phrase."
            )
            continue
        match_type = infer_match_type(candidate, phrase)
        if match_type != "none":
            ranked.append((match_type, candidate))

    if not ranked:
        return LinkedMedicalEntity(
            surface_form=phrase.surface_form,
            normalized_form=phrase.normalized_form,
            extracted_entity_type=phrase.entity_type,
            status="unresolved",
            warnings=warnings,
        )

    compatible = [(match_type, candidate) for match_type, candidate in ranked if candidate.get("entity_type") == phrase.entity_type]
    incompatible = [(match_type, candidate) for match_type, candidate in ranked if candidate.get("entity_type") != phrase.entity_type]

    if not compatible and incompatible:
        return LinkedMedicalEntity(
            surface_form=phrase.surface_form,
            normalized_form=phrase.normalized_form,
            extracted_entity_type=phrase.entity_type,
            match_type=incompatible[0][0],
            match_score=MATCH_SCORES.get(incompatible[0][0], 0.0),
            status="type_conflict",
            warnings=["Name matched a graph entity, but entity_type conflicts with extracted type."],
            candidates=[candidate_summary(candidate, match_type) for match_type, candidate in incompatible],
        )

    compatible.sort(key=lambda item: MATCH_SCORES.get(item[0], 0.0), reverse=True)
    best_score = MATCH_SCORES.get(compatible[0][0], 0.0)
    best = [(match_type, candidate) for match_type, candidate in compatible if MATCH_SCORES.get(match_type, 0.0) == best_score]

    if len(best) > 1:
        return LinkedMedicalEntity(
            surface_form=phrase.surface_form,
            normalized_form=phrase.normalized_form,
            extracted_entity_type=phrase.entity_type,
            match_type=best[0][0],
            match_score=best_score,
            status="ambiguous",
            warnings=["Multiple same-type graph entities matched this phrase."],
            candidates=[candidate_summary(candidate, match_type) for match_type, candidate in best],
        )

    match_type, candidate = best[0]
    return LinkedMedicalEntity(
        surface_form=phrase.surface_form,
        normalized_form=phrase.normalized_form,
        extracted_entity_type=phrase.entity_type,
        linked_entity_id=candidate.get("entity_id", ""),
        linked_canonical_name=candidate.get("canonical_name", ""),
        linked_entity_type=candidate.get("entity_type", ""),
        match_type=match_type,
        match_score=MATCH_SCORES.get(match_type, 0.0),
        status="linked",
        warnings=warnings,
        candidates=[candidate_summary(candidate, match_type)],
    )


def link_extracted_phrases(
    original_query: str,
    corrected_query: str,
    reformulated_query: str,
    query_class: str,
    complexity: str,
    phrases: list[ExtractedMedicalPhrase],
    repository: Neo4jRepository,
    upstream_warnings: list[str] | None = None,
) -> QueryEntityLinkingResult:
    term_records = build_term_records(phrases)
    candidate_rows = repository.find_entities_by_normalized_terms(term_records)
    candidates_by_term: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in candidate_rows:
        candidates_by_term[str(row.get("term_id", ""))].append(row)

    linked_entities = [
        choose_link(phrase, candidates_by_term.get(str(index), []))
        for index, phrase in enumerate(phrases)
    ]
    unresolved_phrases = [
        entity.surface_form
        for entity in linked_entities
        if entity.status in {"unresolved", "ambiguous", "type_conflict"}
    ]
    warnings = list(upstream_warnings or [])
    warnings.extend(
        warning
        for entity in linked_entities
        for warning in entity.warnings
    )

    return QueryEntityLinkingResult(
        original_query=original_query,
        corrected_query=corrected_query,
        reformulated_query=reformulated_query,
        query_class=query_class,
        complexity=complexity,
        linked_entities=linked_entities,
        unresolved_phrases=unresolved_phrases,
        warnings=warnings,
    )


def link_query_entities(query: str, repository: Neo4jRepository | None = None) -> QueryEntityLinkingResult:
    # Normal pipeline path: one unified LLM analysis call, then deterministic Neo4j linking.
    from src.step08b_analyze_query import analyze_query

    analysis = analyze_query(query)
    if repository is None:
        with Neo4jRepository() as repo:
            return link_extracted_phrases(
                analysis.original_query,
                analysis.corrected_query,
                analysis.reformulated_query,
                analysis.query_class,
                analysis.complexity,
                analysis.medical_phrases,
                repo,
                analysis.warnings,
            )
    return link_extracted_phrases(
        analysis.original_query,
        analysis.corrected_query,
        analysis.reformulated_query,
        analysis.query_class,
        analysis.complexity,
        analysis.medical_phrases,
        repository,
        analysis.warnings,
    )


def print_result(result: QueryEntityLinkingResult) -> None:
    for entity in result.linked_entities:
        print(
            f"surface: {entity.surface_form} | "
            f"normalized: {entity.normalized_form} | "
            f"extracted_type: {entity.extracted_entity_type} | "
            f"linked_entity_id: {entity.linked_entity_id} | "
            f"canonical: {entity.linked_canonical_name} | "
            f"graph_type: {entity.linked_entity_type} | "
            f"match_type: {entity.match_type} | "
            f"score: {entity.match_score:.2f} | "
            f"status: {entity.status}"
        )
        for warning in entity.warnings:
            print(f"  warning: {warning}")
        if entity.status in {"ambiguous", "type_conflict"}:
            print(f"  candidates: {json.dumps(entity.candidates, ensure_ascii=False)}")
    if not result.linked_entities:
        print("linked_entities: 0")
    print("warnings:")
    for warning in result.warnings:
        print(f"- {warning}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Link extracted medical phrases to Neo4j MedicalEntity nodes.")
    parser.add_argument("--query", required=True, help="Arabic query.")
    args = parser.parse_args()

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    print_result(link_query_entities(args.query))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
