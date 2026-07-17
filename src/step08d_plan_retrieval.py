from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.config import AppConfig, load_config
from src.models import QueryEntityLinkingResult, RetrievalPlanResult, UnifiedQueryAnalysisResult
from src.step08a_normalize_query import normalize_query
from src.step08b_analyze_query import UNSUPPORTED_GRAPH_INTENTS, analyze_and_link_query
from src.step08c_link_entities import GENERIC_PHRASES


def _strip_article(value: str) -> str:
    normalized = normalize_query(value).normalized_query
    if normalized.startswith("ال") and len(normalized) > 2:
        return normalized[2:]
    return normalized


def is_low_specificity_entity(surface_form: str, canonical_name: str) -> bool:
    surface = normalize_query(surface_form).normalized_query
    canonical = normalize_query(canonical_name).normalized_query
    candidates = {surface, canonical, _strip_article(surface), _strip_article(canonical)}
    return bool(candidates.intersection(GENERIC_PHRASES))


def unique_warnings(warnings: list[str]) -> list[str]:
    unique: list[str] = []
    seen: set[str] = set()
    for warning in warnings:
        if warning and warning not in seen:
            unique.append(warning)
            seen.add(warning)
    return unique


def linked_entity_ids_by_specificity(
    linking: QueryEntityLinkingResult,
) -> tuple[list[str], list[str], list[str]]:
    primary_entity_ids: list[str] = []
    low_specificity_entity_ids: list[str] = []
    unresolved_phrases: list[str] = []

    for entity in linking.linked_entities:
        if entity.status != "linked" or not entity.linked_entity_id:
            unresolved_phrases.append(entity.surface_form)
            continue

        if is_low_specificity_entity(entity.surface_form, entity.linked_canonical_name):
            if entity.linked_entity_id not in low_specificity_entity_ids:
                low_specificity_entity_ids.append(entity.linked_entity_id)
            continue

        if entity.linked_entity_id not in primary_entity_ids:
            primary_entity_ids.append(entity.linked_entity_id)

    return primary_entity_ids, low_specificity_entity_ids, unresolved_phrases


def has_complex_retrieval_signals(analysis: UnifiedQueryAnalysisResult) -> bool:
    text = normalize_query(f"{analysis.corrected_query} {analysis.reformulated_query}").normalized_query
    age_or_child_terms = {"طفل", "طفلي", "ابني", "بنتي", "عمره", "عمرها", "سنه", "سنوات", "اشهر"}
    duration_terms = {"منذ", "يوم", "يومين", "ايام", "اسبوع", "اسابيع", "شهر", "اشهر"}
    comparison_terms = {" ام ", "او ", "هل ", "بسبب"}
    has_age_or_child = any(term in text for term in age_or_child_terms)
    has_duration = any(term in text for term in duration_terms)
    has_comparison = any(term in f" {text} " for term in comparison_terms)
    has_multiple_phrases = len(analysis.medical_phrases) >= 2
    return has_comparison or (has_multiple_phrases and (has_age_or_child or has_duration))


def choose_hop_depth(analysis: UnifiedQueryAnalysisResult, config: AppConfig) -> int:
    if analysis.query_class == "non_medical" or analysis.primary_intent == "non_medical":
        return 0
    if (
        analysis.query_class == "complex_medical"
        or analysis.complexity == "high"
        or has_complex_retrieval_signals(analysis)
    ):
        return min(max(config.retrieval.max_hops, 2), 2)
    if analysis.complexity == "medium":
        return min(max(config.retrieval.max_hops, 1), 2)
    return 1


def build_retrieval_plan(
    analysis: UnifiedQueryAnalysisResult,
    linking: QueryEntityLinkingResult,
    config: AppConfig | None = None,
) -> RetrievalPlanResult:
    config = config or load_config()
    primary_entity_ids, low_specificity_entity_ids, unresolved_phrases = linked_entity_ids_by_specificity(linking)

    warnings = unique_warnings([*analysis.warnings, *linking.warnings])
    is_non_medical = analysis.query_class == "non_medical" or analysis.primary_intent == "non_medical"
    if is_non_medical:
        return RetrievalPlanResult(
            original_query=analysis.original_query,
            corrected_query=analysis.corrected_query,
            reformulated_query=analysis.reformulated_query,
            query_class=analysis.query_class,
            complexity=analysis.complexity,
            primary_intent=analysis.primary_intent,
            use_vector_search=False,
            use_graph_search=False,
            hop_depth=0,
            entity_top_k=0,
            evidence_top_k=0,
            qa_top_k=0,
            preferred_relation_types=[],
            primary_entity_ids=[],
            low_specificity_entity_ids=low_specificity_entity_ids,
            unresolved_phrases=unresolved_phrases,
            warnings=warnings,
        )

    preferred_relation_types = list(analysis.preferred_relation_types)
    unsupported_intent = analysis.primary_intent in UNSUPPORTED_GRAPH_INTENTS
    use_vector_search = True
    use_graph_search = bool(primary_entity_ids)

    if low_specificity_entity_ids:
        warnings.append("Low-specificity linked entities are excluded from primary graph seeds.")
    if unsupported_intent:
        warnings.append("Graph relation filter disabled for unsupported intent; vector/evidence retrieval should carry the answer.")
    if unresolved_phrases:
        warnings.append("Some extracted phrases were not linked and should rely on vector retrieval.")
    if has_complex_retrieval_signals(analysis) and analysis.complexity != "high":
        warnings.append("Planner increased graph depth because the query has age, duration, comparison, or multiple-phrase signals.")

    return RetrievalPlanResult(
        original_query=analysis.original_query,
        corrected_query=analysis.corrected_query,
        reformulated_query=analysis.reformulated_query,
        query_class=analysis.query_class,
        complexity=analysis.complexity,
        primary_intent=analysis.primary_intent,
        use_vector_search=use_vector_search,
        use_graph_search=use_graph_search,
        hop_depth=choose_hop_depth(analysis, config) if use_graph_search else 0,
        entity_top_k=config.retrieval.entity_top_k,
        evidence_top_k=config.retrieval.evidence_top_k,
        qa_top_k=config.retrieval.qa_top_k,
        preferred_relation_types=[] if unsupported_intent else preferred_relation_types,
        primary_entity_ids=primary_entity_ids,
        low_specificity_entity_ids=low_specificity_entity_ids,
        unresolved_phrases=unresolved_phrases,
        warnings=unique_warnings(warnings),
    )


def plan_query_retrieval(query: str, config: AppConfig | None = None) -> RetrievalPlanResult:
    config = config or load_config()
    analysis, linking = analyze_and_link_query(query, config=config)
    return build_retrieval_plan(analysis, linking, config=config)


def print_plan(plan: RetrievalPlanResult) -> None:
    print(json.dumps(asdict(plan), ensure_ascii=False, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser(description="Build deterministic Step 8H retrieval plan.")
    parser.add_argument("--query", required=True, help="Arabic query.")
    args = parser.parse_args()

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    print_plan(plan_query_retrieval(args.query))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
