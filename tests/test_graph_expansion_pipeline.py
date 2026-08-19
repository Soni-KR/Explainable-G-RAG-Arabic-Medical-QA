from __future__ import annotations

import importlib.util
from pathlib import Path
import json
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def load_script(name: str):
    path = SCRIPTS / name
    spec = importlib.util.spec_from_file_location(name.removesuffix(".py"), path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_relation_response_requires_all_ids_and_verbatim_evidence() -> None:
    validator = load_script("step04b_validate_expansion_relations.py")
    request = {
        "request_id": "request_1",
        "chunk_id": "chunk_1",
        "qa_contexts": [
            {
                "qa_id": "qa_1",
                "entities": [
                    {"evidence": "الربو يعالج بموسع الشعب"},
                    {"evidence": "موسع الشعب علاج للربو"},
                ],
                "candidate_pairs": [
                    {"relation_id": "rel_1"},
                    {"relation_id": "rel_2"},
                ],
            }
        ],
    }
    candidates = {
        "rel_1": {"candidate_relation_type": "TREATED_BY"},
        "rel_2": {"candidate_relation_type": "TREATED_BY"},
    }
    valid = {
        "chunk_id": "chunk_1",
        "relations": [
            {
                "relation_id": "rel_1",
                "keep": True,
                "relation_type": "TREATED_BY",
                "evidence": "الربو يعالج بموسع الشعب",
                "confidence": 0.95,
                "reason": "direct",
            },
            {
                "relation_id": "rel_2",
                "keep": False,
                "relation_type": "TREATED_BY",
                "evidence": "",
                "confidence": 0.2,
                "reason": "not supported",
            },
        ],
    }
    parsed = validator.parse_and_validate_response(
        validator.json.dumps(valid, ensure_ascii=False), request, candidates
    )
    assert len(parsed["relations"]) == 2

    missing = dict(valid)
    missing["relations"] = valid["relations"][:1]
    with pytest.raises(ValueError, match="Incomplete decision set"):
        validator.parse_and_validate_response(
            validator.json.dumps(missing, ensure_ascii=False), request, candidates
        )

    fabricated = {**valid, "relations": [dict(item) for item in valid["relations"]]}
    fabricated["relations"][0]["evidence"] = "دواء غير موجود"
    with pytest.raises(ValueError, match="verbatim evidence"):
        validator.parse_and_validate_response(
            validator.json.dumps(fabricated, ensure_ascii=False), request, candidates
        )


def test_compact_relation_response_exports_candidate_specific_evidence() -> None:
    validator = load_script("step04b_validate_expansion_relations.py")
    request = {
        "request_id": "request_compact",
        "chunk_id": "chunk_compact",
        "qa_contexts": [
            {
                "entities": [
                    {"evidence": "السؤال يذكر الربو"},
                    {"evidence": "الإجابة توصي بموسع الشعب"},
                ],
                "candidate_pairs": [{"relation_id": "rel_compact"}],
            }
        ],
    }
    candidates = {
        "rel_compact": {
            "candidate_relation_type": "TREATED_BY",
            "source_evidence": "السؤال يذكر الربو",
            "target_evidence": "الإجابة توصي بموسع الشعب",
        }
    }
    response = {
        "chunk_id": "chunk_compact",
        "decisions": [
            {
                "relation_id": "rel_compact",
                "keep": True,
                "evidence_index": 1,
                "confidence": 0.9,
                "reason_code": "direct_support",
            }
        ],
    }

    parsed = validator.parse_and_validate_response(
        validator.json.dumps(response, ensure_ascii=False), request, candidates
    )

    assert parsed["relations"][0]["evidence"] == (
        "السؤال يذكر الربو | الإجابة توصي بموسع الشعب"
    )
    reparsed = validator.parse_and_validate_response(
        validator.json.dumps(parsed, ensure_ascii=False), request, candidates
    )
    assert reparsed == parsed


def test_final_v2_entity_merge_preserves_parent_id_and_filters_low_quality() -> None:
    merger = load_script("step05_build_final_graph_v2.py")
    old = [
        {
            "entity_id": "ent_parent",
            "canonical_name": "الربو",
            "canonical_name_norm": "الربو",
            "entity_type": "DiseaseCondition",
            "aliases": "[]",
            "confidence": "0.9",
            "mention_count": "2",
            "provider": "groq",
            "model": "old",
        }
    ]
    expansion = [
        {
            "entity_id": "ent_expansion_duplicate",
            "canonical_name": "الربو",
            "canonical_name_norm": "الربو",
            "entity_type": "DiseaseCondition",
            "aliases": '["ربو"]',
            "avg_confidence": "0.8",
            "mention_count": "3",
            "entity_quality": "high",
            "is_actionable_medical_entity": "true",
            "source_models": "new",
        },
        {
            "entity_id": "ent_noise",
            "canonical_name": "جرعة",
            "canonical_name_norm": "جرعه",
            "entity_type": "Treatment",
            "aliases": "[]",
            "avg_confidence": "0.5",
            "mention_count": "1",
            "entity_quality": "low",
            "is_actionable_medical_entity": "false",
            "source_models": "new",
        },
    ]
    entities, id_map, stats = merger.merge_entities(old, expansion)
    assert len(entities) == 1
    assert id_map["ent_expansion_duplicate"] == "ent_parent"
    assert "ent_noise" not in id_map
    assert stats["expansion_entities_merged"] == 1
    assert stats["expansion_entities_filtered"] == 1


def test_final_v2_requires_exact_bounded_entity_snapshot(tmp_path: Path) -> None:
    merger = load_script("step05_build_final_graph_v2.py")
    progress = tmp_path / "progress.json"
    progress.write_text(
        json.dumps({"total_chunks": 1896, "completed_chunks": 474}),
        encoding="utf-8",
    )

    payload = merger.require_entity_snapshot(progress, 474)
    assert payload["completed_chunks"] == 474

    with pytest.raises(RuntimeError, match="snapshot mismatch"):
        merger.require_entity_snapshot(progress, 475)
    with pytest.raises(RuntimeError, match="extraction is partial"):
        merger.require_entity_snapshot(progress, 0)


def test_final_v2_qa_source_is_authoritative_over_legacy_row_noise(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    merger = load_script("step05_build_final_graph_v2.py")
    old_source = tmp_path / "old_qa.csv"
    expansion_source = tmp_path / "expansion_qa.csv"
    old_source.write_text(
        "subset_id,source_row_number,question,answer,category\n"
        "qa_1,779117,question,answer,category\n",
        encoding="utf-8",
    )
    expansion_source.write_text(
        "subset_id,source_row_number,question,answer,category\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(merger, "OLD_QA_SOURCE", old_source)
    monkeypatch.setattr(merger, "EXPANSION_QA_SOURCE", expansion_source)

    mentions = [
        {"qa_id": "qa_1", "source_row_number": "101", "source_graph_version": "final_v1"},
        {"qa_id": "qa_1", "source_row_number": "789", "source_graph_version": "final_v1"},
    ]
    records, stats = merger.build_qa_records(mentions, [])

    assert records[0]["source_row_number"] == 779117
    assert stats["qa_ids_with_multiple_observed_source_rows"] == 1
    assert stats["observed_source_rows_disagreeing_with_authoritative_source"] == 2


def test_candidate_quality_filter() -> None:
    preparer = load_script("step04a_prepare_expansion_relations.py")
    assert preparer.is_usable_entity(
        {"entity_quality": "high", "is_actionable_medical_entity": "true"}
    )
    assert not preparer.is_usable_entity(
        {"entity_quality": "low", "is_actionable_medical_entity": "true"}
    )
    assert not preparer.is_usable_entity(
        {"entity_quality": "medium", "is_actionable_medical_entity": "false"}
    )


def test_entity_cache_keeps_latest_success_authoritative(tmp_path: Path) -> None:
    runner = load_script("step03_expand_graph_entities.py")
    cache = tmp_path / "raw.jsonl"
    records = [
        {
            "chunk_id": "chunk_1",
            "status": "ok",
            "response_text": '{"chunk_id":"chunk_1","entities":[]}',
            "model": "good_model_v1",
        },
        {
            "chunk_id": "chunk_1",
            "status": "error",
            "response_text": "",
            "error": "later retry was rate limited",
        },
        {
            "chunk_id": "chunk_2",
            "status": "error",
            "response_text": "",
            "error": "no successful response",
        },
        {
            "chunk_id": "chunk_1",
            "status": "ok",
            "response_text": '{"chunk_id":"chunk_1","entities":[]}',
            "model": "good_model_v2",
        },
    ]
    cache.write_text(
        "".join(json.dumps(record) + "\n" for record in records),
        encoding="utf-8",
    )

    all_records, authoritative = runner.authoritative_raw_records(cache)

    assert len(all_records) == 4
    assert authoritative["chunk_1"]["status"] == "ok"
    assert authoritative["chunk_1"]["model"] == "good_model_v2"
    assert authoritative["chunk_2"]["status"] == "error"


def test_relation_live_selection_can_replace_one_model_without_repeating_others() -> None:
    validator = load_script("step04b_validate_expansion_relations.py")
    requests = [
        {"request_id": "request_1"},
        {"request_id": "request_2"},
        {"request_id": "request_3"},
    ]
    latest = {
        "request_1": {"status": "ok", "response_text": "{}", "model": "keep_model"},
        "request_2": {"status": "ok", "response_text": "{}", "model": "replace_model"},
    }

    selected, replacements = validator.select_requests_for_live(
        requests,
        latest,
        revalidate_models={"replace_model"},
        limit=0,
    )

    assert [row["request_id"] for row in selected] == ["request_2", "request_3"]
    assert replacements == 1


def test_relation_post_guard_rejects_background_and_ambiguous_cross_pairs() -> None:
    validator = load_script("step04b_validate_expansion_relations.py")
    fields = {
        ("qa_1", "disease_1", "disease one"): {"answer"},
        ("qa_1", "disease_2", "disease two"): {"answer"},
        ("qa_1", "treatment_1", "recommended drug"): {"answer"},
        ("qa_2", "test_1", "historical test"): {"question"},
    }
    groups = {
        ("qa_1", "TREATED_BY"): {"disease_1", "disease_2"},
        ("qa_2", "DIAGNOSED_BY"): {"disease_3"},
    }
    ambiguous = {
        "qa_id": "qa_1",
        "candidate_relation_type": "TREATED_BY",
        "source_entity_id": "disease_1",
        "source_name": "disease one",
        "source_evidence": "disease one",
        "target_entity_id": "treatment_1",
        "target_name": "recommended drug",
        "target_evidence": "recommended drug",
    }
    background_test = {
        "qa_id": "qa_2",
        "candidate_relation_type": "DIAGNOSED_BY",
        "source_entity_id": "disease_3",
        "source_name": "disease three",
        "source_evidence": "possible disease",
        "target_entity_id": "test_1",
        "target_name": "historical test",
        "target_evidence": "historical test",
    }

    assert validator.deterministic_guard_reason(ambiguous, fields, groups) == (
        "deterministic_ambiguous_cross_pair"
    )
    assert validator.deterministic_guard_reason(background_test, fields, groups) == (
        "deterministic_target_not_in_answer"
    )


def test_entity_mention_provenance_is_reconciled_from_source_qa() -> None:
    runner = load_script("step03_expand_graph_entities.py")

    class Module:
        @staticmethod
        def parse_json(value, default):
            return value if isinstance(value, list) else default

        @staticmethod
        def normalize_arabic(value):
            return " ".join(str(value or "").lower().split())

    chunks = [
        {
            "qa_records": [
                {
                    "subset_id": "qa_1",
                    "source_row_number": "779117",
                    "question": "the historical test was done",
                    "answer": "the diagnosis is different",
                }
            ]
        }
    ]
    validated = [
        {
            "entities": [
                {
                    "mentions": [
                        {
                            "qa_id": "qa_1",
                            "source_row_number": "101",
                            "surface_form": "historical test",
                            "evidence": "historical test was done",
                            "field": "answer",
                        }
                    ]
                }
            ]
        }
    ]

    stats = runner.reconcile_validated_mentions(Module(), validated, chunks)
    mention = validated[0]["entities"][0]["mentions"][0]
    assert mention["field"] == "question"
    assert mention["source_row_number"] == "779117"
    assert stats["mention_field_corrections"] == 1
    assert stats["mention_source_row_corrections"] == 1
