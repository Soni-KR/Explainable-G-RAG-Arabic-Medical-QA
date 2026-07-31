from __future__ import annotations

import unittest

from src.models import EvidenceContextBundle
from src.step12b_extractive_fallback import (
    compact_whitespace,
    fallback_eligible,
    select_extractive_fallback,
    split_answer_sentences,
)


def evidence_item(**overrides: object) -> dict[str, object]:
    answer = "يستخدم بخاخ موسع للشعب في علاج الربو وفق تقييم الطبيب."
    row: dict[str, object] = {
        "evidence_id": "E1",
        "qa_id": "qa-1",
        "evidence": answer,
        "source_question": "ما علاج الربو؟",
        "source_answer": answer,
        "field": "answer",
        "evidence_origin": "answer",
        "source_quality": "ahd_heldout_safe_corpus",
        "source_reliability": 0.95,
        "answer_relevance": 0.95,
        "original_question_relevance": 1.0,
        "entity_identity": 1.0,
        "intent_support": 1.0,
        "query_concept_coverage": 1.0,
        "query_constraint_coverage": 1.0,
        "retrieval_score": 0.90,
        "anatomy_mismatch": False,
        "unrelated_condition_mismatch": False,
        "direct_question_anchor": True,
        "exact_question_match": True,
        "relation_ids": [],
    }
    row.update(overrides)
    return row


def context(*items: dict[str, object]) -> EvidenceContextBundle:
    rows = list(items or (evidence_item(),))
    return EvidenceContextBundle(
        query="ما علاج الربو؟",
        reformulated_query="ما علاج الربو؟",
        primary_intent="treatment_request",
        query_medical_phrases=["الربو"],
        evidence_items=rows,
        allowed_evidence_ids=[
            str(item["evidence_id"]) for item in rows
        ],
        allowed_qa_ids=[str(item["qa_id"]) for item in rows],
    )


class ExtractiveFallbackTests(unittest.TestCase):
    def test_fallback_requires_context_and_no_surviving_claims(self) -> None:
        self.assertTrue(
            fallback_eligible(output_claims=[], context=context())
        )
        self.assertFalse(
            fallback_eligible(
                output_claims=[{"claim": "existing"}],
                context=context(),
            )
        )
        self.assertFalse(
            fallback_eligible(
                output_claims=[],
                context=EvidenceContextBundle(
                    query="ما علاج الربو؟",
                    reformulated_query="ما علاج الربو؟",
                ),
            )
        )

    def test_selected_claim_is_exact_and_has_one_allowed_citation(self) -> None:
        result = select_extractive_fallback(context())

        self.assertEqual(result.status, "selected")
        self.assertIsNotNone(result.selected)
        assert result.selected is not None
        self.assertEqual(
            result.selected.claim.claim,
            compact_whitespace(result.selected.source_answer),
        )
        self.assertEqual(result.selected.claim.citations, ["E1"])
        self.assertEqual(result.selected.claim.source_qa_ids, ["qa-1"])
        self.assertEqual(
            result.selected.verification.status,
            "supported",
        )
        self.assertTrue(result.selected.exact_source_match)

    def test_hard_context_mismatch_is_rejected_before_verification(self) -> None:
        result = select_extractive_fallback(
            context(evidence_item(anatomy_mismatch=True))
        )

        self.assertEqual(result.status, "no_supported_sentence")
        self.assertEqual(
            result.rejected_evidence,
            [{"evidence_id": "E1", "reason": "anatomy_mismatch"}],
        )

    def test_weak_source_question_match_is_not_rescued(self) -> None:
        result = select_extractive_fallback(
            context(
                evidence_item(
                    direct_question_anchor=False,
                    exact_question_match=False,
                    original_question_relevance=0.49,
                )
            )
        )

        self.assertEqual(result.status, "no_supported_sentence")
        self.assertEqual(
            result.rejected_evidence[0]["reason"],
            "source_question_relevance_below_gate",
        )

    def test_sentence_split_preserves_negation_numbers_and_relations(self) -> None:
        answer = (
            "لا تستخدم جرعة 20 ملغ دون وصفة الطبيب. "
            "يستخدم الدواء لعلاج الربو، وليس لعلاج العدوى."
        )

        sentences = split_answer_sentences(answer)

        self.assertEqual(
            sentences,
            [
                "لا تستخدم جرعة 20 ملغ دون وصفة الطبيب.",
                "يستخدم الدواء لعلاج الربو، وليس لعلاج العدوى.",
            ],
        )
        for sentence in sentences:
            self.assertIn(sentence, compact_whitespace(answer))


if __name__ == "__main__":
    unittest.main()
