from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from scripts.evaluation_common import ROOT


DEFAULT_RETRIEVAL_RUN = (
    ROOT / "outputs" / "evaluation" / "retrieval" / "evaluation_v1_retrieval_all_20260716"
)
DEFAULT_GENERATION_RUN = (
    ROOT / "outputs" / "evaluation" / "generation" / "evaluation_v1_generation_all_20260716"
)
DEFAULT_OUTPUT = (
    ROOT
    / "outputs"
    / "evaluation"
    / "qualitative"
    / "evaluation_v1_steps08_12_examples.md"
)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records = []
    with path.open("r", encoding="utf-8-sig") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON at {path}:{line_number}") from exc
    return records


def by_query(path: Path) -> dict[str, dict[str, Any]]:
    return {str(row["query_id"]): row for row in read_jsonl(path)}


def compact(value: Any, limit: int = 320) -> str:
    text = " ".join(str(value or "").split())
    return text if len(text) <= limit else text[: limit - 3].rstrip() + "..."


def md(value: Any, limit: int = 320) -> str:
    return compact(value, limit).replace("|", "\\|") or "-"


def load_entity_names() -> dict[str, str]:
    path = ROOT / "outputs" / "final_graph" / "entities.csv"
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return {
            str(row.get("entity_id") or ""): str(row.get("canonical_name") or "")
            for row in csv.DictReader(handle)
        }


def generation_failed(record: dict[str, Any]) -> bool:
    explicit_status = str(
        record.get("generation_status")
        or record.get("raw", {}).get("generated", {}).get("generation_status")
        or ""
    )
    if explicit_status:
        return explicit_status != "generated"
    return any(
        "HTTPError" in str(warning) or "failed" in str(warning).lower()
        for warning in record.get("warnings", [])
    )


def example_category(record: dict[str, Any]) -> str:
    gold = record.get("gold", {})
    relation_count = len(record.get("relations") or [])
    evidence_count = len(record.get("evidence") or [])
    analysis = record.get("query_analysis", {})
    linking = record.get("entity_linking", {})
    if gold.get("answerable_from_final_graph") is False:
        return "little_available_evidence"
    if relation_count >= 5:
        return "strong_graph_coverage"
    if relation_count <= 1 and evidence_count >= 5:
        return "qa_evidence_dominant"
    if linking.get("unresolved_phrases") or analysis.get("corrected_query") != analysis.get("original_query"):
        return "spelling_dialect_or_unresolved"
    return "mixed_or_incomplete_graph"


def select_examples(
    full_records: dict[str, dict[str, Any]],
    generation_records: dict[str, dict[str, Any]],
    count: int,
) -> list[str]:
    selected: list[str] = []

    # Preserve every successful grounded generation so answer quality can be inspected.
    for query_id in sorted(generation_records):
        if query_id in full_records and not generation_failed(generation_records[query_id]):
            selected.append(query_id)

    buckets: dict[str, list[str]] = {}
    for query_id, record in full_records.items():
        buckets.setdefault(example_category(record), []).append(query_id)
    for values in buckets.values():
        values.sort()

    category_order = (
        "strong_graph_coverage",
        "qa_evidence_dominant",
        "mixed_or_incomplete_graph",
        "spelling_dialect_or_unresolved",
        "little_available_evidence",
    )
    while len(selected) < count:
        progressed = False
        for category in category_order:
            candidates = buckets.get(category, [])
            while candidates and candidates[0] in selected:
                candidates.pop(0)
            if candidates and len(selected) < count:
                selected.append(candidates.pop(0))
                progressed = True
        if not progressed:
            break
    return selected[:count]


def step8_section(record: dict[str, Any]) -> list[str]:
    analysis = record.get("query_analysis", {})
    linking = record.get("entity_linking", {})
    plan = record.get("retrieval_plan", {})
    phrases = analysis.get("medical_phrases") or []
    linked = linking.get("linked_entities") or []
    lines = [
        "### Step 8: Query understanding",
        "",
        f"- Model/configuration: `{analysis.get('model', 'unknown')}` / `{analysis.get('prompt_version', 'unknown')}`",
        f"- Original: {md(analysis.get('original_query'), 600)}",
        f"- Normalized: {md(analysis.get('normalized_query'), 600)}",
        f"- Corrected: {md(analysis.get('corrected_query'), 600)}",
        f"- Reformulated: {md(analysis.get('reformulated_query'), 600)}",
        f"- Class / complexity: `{analysis.get('query_class', '-')}` / `{analysis.get('complexity', '-')}`",
        f"- Primary intent: `{analysis.get('primary_intent', '-')}`",
        f"- Preferred relations: `{', '.join(analysis.get('preferred_relation_types') or []) or 'none'}`",
        f"- Analysis confidence: `{analysis.get('confidence', 0)}`",
        "",
        "| Medical phrase | Type | Source | Confidence |",
        "|---|---|---|---:|",
    ]
    if phrases:
        for item in phrases:
            lines.append(
                f"| {md(item.get('surface_form'))} | {md(item.get('entity_type'))} | "
                f"{md(item.get('source'))} | {item.get('confidence', 0)} |"
            )
    else:
        lines.append("| _none_ | - | - | - |")
    lines.extend(
        [
            "",
            "| Phrase | Linked entity | Entity ID | Match | Score | Status |",
            "|---|---|---|---|---:|---|",
        ]
    )
    if linked:
        for item in linked:
            lines.append(
                f"| {md(item.get('surface_form'))} | {md(item.get('linked_canonical_name'))} | "
                f"`{item.get('linked_entity_id') or '-'}` | `{item.get('match_type', '-')}` | "
                f"{item.get('match_score', 0)} | `{item.get('status', '-')}` |"
            )
    else:
        lines.append("| _none_ | - | - | - | - | - |")
    lines.extend(
        [
            "",
            f"Retrieval plan: vector=`{plan.get('use_vector_search')}`, graph=`{plan.get('use_graph_search')}`, "
            f"hop depth=`{plan.get('hop_depth')}`, entity/evidence/QA top-k="
            f"`{plan.get('entity_top_k')}/{plan.get('evidence_top_k')}/{plan.get('qa_top_k')}`.",
            "",
        ]
    )
    return lines


def step9_section(
    graph_record: dict[str, Any],
    vector_record: dict[str, Any],
    entity_names: dict[str, str],
) -> list[str]:
    relations = graph_record.get("relations") or []
    evidence = vector_record.get("evidence") or []
    entity_ids = vector_record.get("rankings", {}).get("entity_ids") or []
    lines = [
        "### Step 9: Retrieval channels",
        "",
        "**Semantic entity retrieval**",
        "",
    ]
    lines.extend(
        f"- `{entity_id}`: {md(entity_names.get(entity_id, 'unknown'))}"
        for entity_id in entity_ids[:5]
    )
    if not entity_ids:
        lines.append("- No entity candidates.")
    lines.extend(
        [
            "",
            "**Graph retrieval**",
            "",
            "| Relation | Confidence | Hybrid score | QA |",
            "|---|---:|---:|---|",
        ]
    )
    for item in relations[:5]:
        fact = f"{item.get('source_name', '')} --{item.get('relation_type', '')}--> {item.get('target_name', '')}"
        lines.append(
            f"| {md(fact)} | {item.get('confidence', 0)} | {item.get('hybrid_score', 0)} | "
            f"`{item.get('qa_id') or '-'}` |"
        )
    if not relations:
        lines.append("| _No graph relation returned_ | - | - | - |")
    lines.extend(
        [
            "",
            "**Evidence retrieval**",
            "",
            "| Evidence ID | Evidence | Score | QA | Source quality |",
            "|---|---|---:|---|---|",
        ]
    )
    for item in evidence[:5]:
        lines.append(
            f"| `{item.get('source_id') or item.get('evidence_id') or '-'}` | {md(item.get('text'), 260)} | "
            f"{item.get('score', 0)} | `{item.get('qa_id') or '-'}` | `{item.get('source_quality') or '-'}` |"
        )
    if not evidence:
        lines.append("| _No evidence returned_ | - | - | - | - |")
    lines.extend(
        [
            "",
            "**Direct QA retrieval**",
            "",
            "| QA ID | Similar question | Answer excerpt | Best score |",
            "|---|---|---|---:|",
        ]
    )
    qa_best: dict[str, dict[str, Any]] = {}
    for item in evidence:
        qa_id = str(item.get("qa_id") or "")
        if qa_id and (qa_id not in qa_best or item.get("score", 0) > qa_best[qa_id].get("score", 0)):
            qa_best[qa_id] = item
    for item in sorted(qa_best.values(), key=lambda value: value.get("score", 0), reverse=True)[:3]:
        lines.append(
            f"| `{item.get('qa_id')}` | {md(item.get('question'), 220)} | "
            f"{md(item.get('answer'), 260)} | {item.get('score', 0)} |"
        )
    if not qa_best:
        lines.append("| _No QA record returned_ | - | - | - |")
    lines.append("")
    return lines


def step10_section(before: dict[str, Any], after: dict[str, Any]) -> list[str]:
    preferred = set(after.get("retrieval_plan", {}).get("preferred_relation_types") or [])
    before_relations = {item.get("relation_id"): (rank, item) for rank, item in enumerate(before.get("relations") or [], 1)}
    before_evidence = {item.get("evidence_id"): (rank, item) for rank, item in enumerate(before.get("evidence") or [], 1)}
    candidates = []
    for rank, item in enumerate(after.get("relations") or [], 1):
        old_rank, old = before_relations.get(item.get("relation_id"), (None, {}))
        candidates.append(
            {
                "after": rank,
                "before": old_rank,
                "result": f"{item.get('source_name', '')} --{item.get('relation_type', '')}--> {item.get('target_name', '')}",
                "source": "Relation",
                "semantic": item.get("semantic_support"),
                "entity": item.get("seed_score"),
                "intent": 1.0 if item.get("relation_type") in preferred else 0.4,
                "answer_relevance": item.get("metadata", {}).get("query_support"),
                "before_score": old.get("hybrid_score"),
                "final": item.get("hybrid_score"),
                "reason": item.get("metadata", {}).get("rank_reason", "relation reranker"),
            }
        )
    for rank, item in enumerate(after.get("evidence") or [], 1):
        old_rank, old = before_evidence.get(item.get("evidence_id"), (None, {}))
        source = "QA" if item.get("source_id") == item.get("qa_id") else "Evidence"
        candidates.append(
            {
                "after": rank,
                "before": old_rank,
                "result": item.get("question") if source == "QA" else item.get("text"),
                "source": source,
                "semantic": old.get("score"),
                "entity": None,
                "intent": None,
                "answer_relevance": item.get("metadata", {}).get("answer_relevance"),
                "before_score": old.get("score"),
                "final": item.get("score"),
                "reason": "query relevance+source quality+direct-QA+relation support",
            }
        )
    candidates.sort(key=lambda item: float(item.get("final") or 0), reverse=True)
    lines = [
        "### Step 10: Reranking",
        "",
        "| Final rank | Previous rank | Result | Source | Semantic | Entity seed | Intent | Answer relevance | Before | Final | Reason |",
        "|---:|---:|---|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for final_rank, item in enumerate(candidates[:10], start=1):
        value = lambda key: "-" if item.get(key) is None else str(round(float(item[key]), 4))
        lines.append(
            f"| {final_rank} | {item.get('before') or '-'} | {md(item.get('result'), 220)} | "
            f"{item.get('source')} | {value('semantic')} | {value('entity')} | {value('intent')} | "
            f"{value('answer_relevance')} | {value('before_score')} | {value('final')} | {md(item.get('reason'), 120)} |"
        )
    lines.append("")
    return lines


def step11_section(generation_record: dict[str, Any]) -> list[str]:
    context = generation_record.get("raw", {}).get("context", {})
    facts = context.get("graph_facts") or []
    evidence = context.get("evidence_items") or []
    lines = [
        "### Step 11: Final evidence context",
        "",
        f"Context contains `{len(facts)}` graph facts and `{len(evidence)}` evidence/QA items.",
        "",
        "**Graph facts supplied to the generator**",
        "",
    ]
    lines.extend(
        f"- `{item.get('relation_id')}` {md(item.get('fact'), 360)} "
        f"(score={item.get('retrieval_score', 0)}, QA=`{item.get('qa_id') or '-'}`)"
        for item in facts[:5]
    )
    if not facts:
        lines.append("- No graph facts supplied.")
    lines.extend(["", "**Evidence supplied to the generator**", ""])
    for item in evidence[:6]:
        lines.append(
            f"- `{item.get('evidence_id')}` / source `{item.get('source_id')}` / QA `{item.get('qa_id')}`: "
            f"{md(item.get('evidence'), 360)}"
        )
    if not evidence:
        lines.append("- No evidence supplied.")
    if len(facts) > 5 or len(evidence) > 6:
        lines.append(f"- Remaining context omitted from this display: {max(0, len(facts)-5)} facts, {max(0, len(evidence)-6)} evidence items.")
    lines.append("")
    return lines


def step12_section(generation_record: dict[str, Any]) -> list[str]:
    raw = generation_record.get("raw", {})
    generated = raw.get("generated", {})
    verifications = raw.get("verifications") or []
    bert = generation_record.get("metrics", {}).get("bertscore", {})
    failed = generation_failed(generation_record)
    fallback_type = generated.get("fallback_type") or generation_record.get("generation_status") or ""
    bert_display = (
        bert.get("bertscore_f1")
        if bert.get("status") == "computed"
        else f"unavailable: {bert.get('reason', 'generation was not scored')}"
    )
    lines = [
        "### Step 12: Answer generation and claim inspection",
        "",
        f"- Model: `{generated.get('model') or 'unknown'}`",
        f"- Provider result: `{'failed/fallback' if failed else 'successful'}`",
        f"- Fallback type: `{fallback_type or 'none'}`",
        f"- BERTScore F1 against AHD reference: `{bert_display}`",
        f"- End-to-end latency: `{generation_record.get('timings_ms', {}).get('end_to_end', 0)} ms`",
        "",
        "**Reference AHD answer**",
        "",
        md(generation_record.get("gold", {}).get("reference_answer"), 1600),
        "",
        "**Generated answer before mitigation**",
        "",
        md(generated.get("answer") or generation_record.get("answer"), 1600),
        "",
        "**Final answer after mitigation**",
        "",
        md(generation_record.get("answer"), 1600),
        "",
        "| Claim | Status | Support score | Question relevance | Valid citations | Valid QA IDs | Reason |",
        "|---|---|---:|---:|---|---|---|",
    ]
    for item in verifications:
        claim = item.get("claim", {}) if isinstance(item.get("claim"), dict) else {"claim": item.get("claim")}
        lines.append(
            f"| {md(claim.get('claim'), 360)} | `{item.get('status', '-')}` | {item.get('support_score', 0)} | {item.get('question_relevance', 0)} | "
            f"`{', '.join(item.get('valid_citations') or []) or '-'}` | "
            f"`{', '.join(item.get('valid_qa_ids') or []) or '-'}` | {md(item.get('reason'), 220)} |"
        )
    if not verifications and failed:
        lines.append("| _Claim audit unavailable because this was an API fallback, not a generated medical answer_ | - | - | - | - | - | - |")
    elif not verifications:
        recorded_claims = raw.get("claims") or generation_record.get("output_claims") or []
        if recorded_claims:
            for item in recorded_claims:
                lines.append(
                    f"| {md(item.get('claim'), 360)} | `audit_not_recorded` | - | - | "
                    f"`{', '.join(item.get('citations') or []) or '-'}` | "
                    f"`{', '.join(item.get('source_qa_ids') or []) or '-'}` | Claim exists, but its verification row is absent. |"
                )
        else:
            lines.append("| _No factual claims were extracted from the successful response_ | - | - | - | - | - | - |")
    warnings = generation_record.get("warnings") or []
    if warnings:
        lines.extend(["", "Warnings:"])
        lines.extend(f"- {md(warning, 300)}" for warning in warnings)
    lines.append("")
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a readable Step 8-12 qualitative inspection report.")
    parser.add_argument("--retrieval-run", type=Path, default=DEFAULT_RETRIEVAL_RUN)
    parser.add_argument("--generation-run", type=Path, default=DEFAULT_GENERATION_RUN)
    parser.add_argument("--example-count", type=int, default=15)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    if not 10 <= args.example_count <= 20:
        raise ValueError("example-count must be between 10 and 20.")
    retrieval_run = args.retrieval_run.resolve()
    generation_run = args.generation_run.resolve()
    output = args.output.resolve()
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite qualitative report: {output}")

    full = by_query(retrieval_run / "full_hybrid.jsonl")
    before = by_query(retrieval_run / "hybrid_without_reranking.jsonl")
    vector = by_query(retrieval_run / "vector_only.jsonl")
    generation = by_query(generation_run / "full_pipeline.jsonl")
    selected = select_examples(full, generation, args.example_count)
    entity_names = load_entity_names()
    category_counts: dict[str, int] = {}
    for query_id in selected:
        category = example_category(full[query_id])
        category_counts[category] = category_counts.get(category, 0) + 1

    lines = [
        "# Evaluation-v1 Qualitative Inspection: Steps 8-12",
        "",
        "This report inspects saved outputs for held-out questions verified against the original AHD dataset.",
        "It is qualitative debugging evidence, not a replacement for human-confirmed retrieval gold labels.",
        "The supplemental graph is not used.",
        "",
        "## Configuration note",
        "",
        "The current final pipeline has one valid Step 8 configuration: `openai/gpt-oss-20b` with `query_analysis_v1`.",
        "Four-model comparison is deferred; old colleague Step 8 outputs target the incompatible trial/supplemental graph and are excluded.",
        "The historical generation records inspected here used the model recorded in each example. The project default is now `openai/gpt-oss-20b`.",
        "",
        "## Selected examples",
        "",
        f"Total: `{len(selected)}`. Categories: `{json.dumps(category_counts, ensure_ascii=False, sort_keys=True)}`.",
        "",
    ]

    for number, query_id in enumerate(selected, start=1):
        record = full[query_id]
        lines.extend(
            [
                f"## Example {number}: `{query_id}`",
                "",
                f"Coverage category: `{example_category(record)}`",
                "",
                "### Original AHD record",
                "",
                f"**Question:** {md(record.get('query'), 1000)}",
                "",
                f"**Reference answer:** {md(record.get('gold', {}).get('reference_answer'), 1600)}",
                "",
            ]
        )
        lines.extend(step8_section(record))
        lines.extend(step9_section(before[query_id], vector[query_id], entity_names))
        lines.extend(step10_section(before[query_id], record))
        lines.extend(step11_section(generation[query_id]))
        lines.extend(step12_section(generation[query_id]))
        lines.extend(["---", ""])

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "status": "ok",
                "examples": len(selected),
                "categories": category_counts,
                "output": str(output),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
