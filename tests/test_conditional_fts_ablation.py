from __future__ import annotations

from types import SimpleNamespace

from scripts.build_conditional_fts_ablation import (
    CATEGORY_BONUS,
    append_expansion,
    expansion_evidence,
    has_strong_direct_evidence,
    infer_preferred_category,
    query_variants,
)


def test_query_variants_are_label_free_and_deduplicated() -> None:
    record = {
        "query": "ما علاج الربو؟",
        "query_analysis": {
            "reformulated_query": "ما العلاجات المستخدمة للربو؟",
            "medical_phrases": [
                {
                    "surface_form": "الربو",
                    "normalized_form": "الربو",
                }
            ],
        },
    }

    variants = query_variants(record)

    assert [name for name, _ in variants] == [
        "original_query",
        "reformulated_query",
        "medical_phrases",
    ]
    assert all("reference" not in name for name, _ in variants)


def test_strong_direct_evidence_uses_absolute_gates() -> None:
    context = SimpleNamespace(
        evidence_items=[
            {
                "direct_question_anchor": False,
                "answer_relevance": 0.80,
                "query_concept_coverage": 0.80,
                "intent_support": 0.75,
                "source_reliability": 0.90,
                "anatomy_mismatch": False,
                "unrelated_condition_mismatch": False,
            }
        ]
    )

    assert has_strong_direct_evidence(context) is True
    context.evidence_items[0]["anatomy_mismatch"] = True
    assert has_strong_direct_evidence(context) is False


def test_category_inference_ignores_mismatched_context() -> None:
    context = SimpleNamespace(
        evidence_items=[
            {
                "category": "أمراض الصدر",
                "retrieval_score": 0.8,
                "source_reliability": 0.9,
                "anatomy_mismatch": False,
                "unrelated_condition_mismatch": False,
            },
            {
                "category": "أمراض القلب",
                "retrieval_score": 1.0,
                "source_reliability": 1.0,
                "anatomy_mismatch": True,
                "unrelated_condition_mismatch": False,
            },
        ]
    )

    assert infer_preferred_category(context) == "أمراض الصدر"


def test_category_bonus_is_small_and_explicit() -> None:
    row = {
        "qa_id": "qa_1",
        "source_row_number": 4,
        "question": "ما علاج الربو؟",
        "answer": "إجابة",
        "category": "أمراض الصدر",
        "best_score": 0.70,
        "best_rank": 1,
        "matched_variants": ["original_query"],
        "variant_ranks": {"original_query": 1},
    }

    evidence = expansion_evidence(
        row,
        preferred_category="أمراض الصدر",
        use_category_bonus=True,
    )

    assert evidence["score"] == 0.70 + CATEGORY_BONUS
    assert evidence["metadata"]["category_bonus"] == CATEGORY_BONUS
    assert evidence["metadata"]["evidence_origin"] == "answer"


def test_append_expansion_deduplicates_existing_qa_ids() -> None:
    record = {
        "evidence": [
            {
                "evidence_id": "qa::qa_1",
                "source_id": "qa_1",
                "qa_id": "qa_1",
            }
        ]
    }
    candidates = [
        {
            "qa_id": "qa_1",
            "source_row_number": 1,
            "question": "سؤال 1",
            "answer": "إجابة 1",
            "category": "عام",
            "best_score": 0.8,
            "best_rank": 1,
            "matched_variants": ["original_query"],
            "variant_ranks": {"original_query": 1},
        },
        {
            "qa_id": "qa_2",
            "source_row_number": 2,
            "question": "سؤال 2",
            "answer": "إجابة 2",
            "category": "عام",
            "best_score": 0.7,
            "best_rank": 2,
            "matched_variants": ["original_query"],
            "variant_ranks": {"original_query": 2},
        },
    ]

    updated, added = append_expansion(
        record,
        candidates,
        preferred_category="",
        use_category_bonus=False,
    )

    assert added == 1
    assert [item["qa_id"] for item in updated["evidence"]] == ["qa_1", "qa_2"]
