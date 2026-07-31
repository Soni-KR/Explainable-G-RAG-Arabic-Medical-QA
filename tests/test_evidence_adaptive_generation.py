from __future__ import annotations

import json
import unittest

from src.config import AnswerGenerationConfig, AppConfig
from src.models import AnswerClaim, EvidenceContextBundle, GeneratedAnswer
from src.step12_generate_grounded_answer import (
    PARTIAL_EVIDENCE_MODE,
    STRONG_DIRECT_MODE,
    V31_PROMPT_VERSION,
    V31_STRUCTURED_MODE,
    build_messages,
    is_strong_direct_evidence,
    prepare_generation_context,
    select_generation_mode,
    validate_answer_payload,
)
from src.step13_extract_claims import extract_claims


def direct_evidence(**overrides: object) -> dict[str, object]:
    item: dict[str, object] = {
        "evidence_id": "E1",
        "qa_id": "qa-1",
        "evidence": "يستخدم بخاخ موسع للشعب في علاج الربو وفق تقييم الطبيب.",
        "source_question": "ما علاج الربو؟",
        "source_answer": "يستخدم بخاخ موسع للشعب في علاج الربو وفق تقييم الطبيب.",
        "source_quality": "ahd_heldout_safe_corpus",
        "evidence_origin": "answer",
        "question_text_excluded": False,
        "answer_relevance": 0.95,
        "entity_identity": 0.90,
        "intent_support": 1.0,
        "query_concept_coverage": 1.0,
        "query_constraint_coverage": 1.0,
        "source_reliability": 0.95,
        "anatomy_mismatch": False,
        "unrelated_condition_mismatch": False,
        "direct_question_anchor": False,
        "retrieval_score": 0.90,
        "relation_ids": ["R1"],
    }
    item.update(overrides)
    return item


def evidence_context(*items: dict[str, object]) -> EvidenceContextBundle:
    evidence_items = list(items or (direct_evidence(),))
    return EvidenceContextBundle(
        query="ما علاج الربو؟",
        reformulated_query="ما علاج الربو؟",
        primary_intent="treatment_request",
        query_medical_phrases=["الربو"],
        graph_facts=[
            {
                "relation_id": "R1",
                "fact": "الربو --TREATED_BY--> بخاخ موسع للشعب",
            }
        ],
        evidence_items=evidence_items,
        allowed_evidence_ids=[
            str(item["evidence_id"]) for item in evidence_items
        ],
        allowed_qa_ids=[
            str(item["qa_id"]) for item in evidence_items if item.get("qa_id")
        ],
    )


class EvidenceAdaptiveGenerationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = AppConfig(
            answer_generation=AnswerGenerationConfig(
                prompt_version="grounded_evidence_adaptive_v4_2"
            )
        )

    def test_strong_direct_gate_requires_answer_origin_and_all_quality_gates(self) -> None:
        self.assertTrue(is_strong_direct_evidence(direct_evidence()))
        self.assertFalse(
            is_strong_direct_evidence(
                direct_evidence(evidence_origin="question")
            )
        )
        self.assertFalse(
            is_strong_direct_evidence(
                direct_evidence(query_constraint_coverage=0.5)
            )
        )
        self.assertFalse(
            is_strong_direct_evidence(
                direct_evidence(anatomy_mismatch=True)
            )
        )

    def test_strong_mode_narrows_generation_to_one_passage(self) -> None:
        weaker = direct_evidence(
            evidence_id="E2",
            qa_id="qa-2",
            answer_relevance=0.80,
            entity_identity=0.70,
            retrieval_score=0.70,
        )
        context = evidence_context(direct_evidence(), weaker)
        decision = select_generation_mode(context)
        narrowed = prepare_generation_context(context, decision)

        self.assertEqual(decision.mode, STRONG_DIRECT_MODE)
        self.assertEqual(decision.evidence_ids, ["E1"])
        self.assertEqual(narrowed.allowed_evidence_ids, ["E1"])
        self.assertEqual(len(narrowed.evidence_items), 1)
        self.assertEqual(narrowed.graph_facts, [])

    def test_partial_mode_keeps_step11_context(self) -> None:
        context = evidence_context(
            direct_evidence(
                evidence_origin="answer",
                entity_identity=0.20,
                direct_question_anchor=False,
            )
        )
        decision = select_generation_mode(context)
        prepared = prepare_generation_context(context, decision)

        self.assertEqual(decision.mode, PARTIAL_EVIDENCE_MODE)
        self.assertIs(prepared, context)

    def test_prompt_exposes_mode_and_never_requests_free_form_answer(self) -> None:
        context = evidence_context()
        decision = select_generation_mode(context)
        payload = json.loads(build_messages(context, decision)[1]["content"])

        self.assertEqual(payload["generation_mode"], STRONG_DIRECT_MODE)
        self.assertEqual(len(payload["evidence_items"]), 1)
        self.assertEqual(
            set(payload["evidence_items"][0]),
            {"evidence_id", "evidence"},
        )
        self.assertNotIn("answer_ar", payload["required_json"])
        self.assertNotIn("source_qa_ids", payload["required_json"]["claims"][0])

    def test_validation_derives_answer_and_provenance_from_one_citation(self) -> None:
        context = evidence_context()
        decision = select_generation_mode(context)
        context = prepare_generation_context(context, decision)
        claim = "يستخدم بخاخ موسع للشعب في علاج الربو وفق تقييم الطبيب."
        result = validate_answer_payload(
            {
                "claims": [{"claim_ar": claim, "citations": ["E1"]}],
                "limitations_ar": [],
            },
            context,
            self.config,
            decision=decision,
        )

        self.assertEqual(result.answer, claim)
        self.assertEqual(result.claims[0].source_qa_ids, ["qa-1"])
        self.assertEqual(result.used_relations, ["R1"])
        self.assertEqual(result.generation_evidence_ids, ["E1"])
        self.assertEqual(result.generation_mode, STRONG_DIRECT_MODE)

    def test_validation_rejects_multiple_or_unknown_citations(self) -> None:
        context = evidence_context()
        decision = select_generation_mode(context)
        with self.assertRaisesRegex(ValueError, "exactly one"):
            validate_answer_payload(
                {
                    "claims": [
                        {
                            "claim_ar": "يستخدم علاج للربو.",
                            "citations": ["E1", "E2"],
                        }
                    ],
                    "limitations_ar": [],
                },
                context,
                self.config,
                decision=decision,
            )
        with self.assertRaisesRegex(ValueError, "unavailable evidence"):
            validate_answer_payload(
                {
                    "claims": [
                        {
                            "claim_ar": "يستخدم علاج للربو.",
                            "citations": ["E9"],
                        }
                    ],
                    "limitations_ar": [],
                },
                context,
                self.config,
                decision=decision,
            )

    def test_validation_defers_contextless_claim_to_step14_and_caps_claims(self) -> None:
        context = evidence_context()
        decision = select_generation_mode(context)
        result = validate_answer_payload(
            {
                "claims": [
                    {
                        "claim_ar": "ينصح بإجراء فحص طبي.",
                        "citations": ["E1"],
                    }
                ],
                "limitations_ar": [],
            },
            context,
            self.config,
            decision=decision,
        )
        self.assertTrue(
            any("Step 14 must decide" in warning for warning in result.warnings)
        )
        with self.assertRaisesRegex(ValueError, "at most two"):
            validate_answer_payload(
                {
                    "claims": [
                        {"claim_ar": "علاج الربو الأول.", "citations": ["E1"]},
                        {"claim_ar": "علاج الربو الثاني.", "citations": ["E1"]},
                        {"claim_ar": "علاج الربو الثالث.", "citations": ["E1"]},
                    ],
                    "limitations_ar": [],
                },
                context,
                self.config,
                decision=decision,
            )

    def test_step13_preserves_v4_claim_context_and_provenance(self) -> None:
        compound = AnswerClaim(
            claim=(
                "لعلاج الربو يستخدم بخاخ موسع للشعب، كما يجب تقييم الربو طبيا."
            ),
            citations=["E1"],
            source_qa_ids=["qa-1"],
        )
        generated = GeneratedAnswer(
            query="ما علاج الربو؟",
            answer=compound.claim,
            claims=[compound],
            prompt_version="grounded_evidence_adaptive_v4_2",
            generation_mode=PARTIAL_EVIDENCE_MODE,
        )

        claims = extract_claims(generated)

        self.assertEqual(claims, [compound])


class V31StructuredGenerationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = AppConfig(
            answer_generation=AnswerGenerationConfig(
                prompt_version=V31_PROMPT_VERSION
            )
        )

    def test_v31_keeps_all_selected_context_instead_of_strong_narrowing(self) -> None:
        second = direct_evidence(
            evidence_id="E2",
            qa_id="qa-2",
            evidence="يُنصح بتقييم السيطرة على الربو مع الطبيب.",
            relation_ids=["R2"],
        )
        context = evidence_context(direct_evidence(), second)
        decision = select_generation_mode(context, V31_PROMPT_VERSION)
        prepared = prepare_generation_context(context, decision)

        self.assertEqual(decision.mode, V31_STRUCTURED_MODE)
        self.assertEqual(decision.evidence_ids, ["E1", "E2"])
        self.assertIs(prepared, context)
        self.assertEqual(len(prepared.evidence_items), 2)
        self.assertEqual(len(prepared.graph_facts), 1)

    def test_v31_prompt_uses_claim_only_schema_and_python_owned_provenance(self) -> None:
        context = evidence_context()
        decision = select_generation_mode(context, V31_PROMPT_VERSION)
        payload = json.loads(
            build_messages(
                context,
                decision,
                V31_PROMPT_VERSION,
            )[1]["content"]
        )

        self.assertEqual(payload["generation_mode"], V31_STRUCTURED_MODE)
        self.assertNotIn("answer_ar", payload["required_json"])
        self.assertNotIn("source_qa_ids", payload["required_json"]["claims"][0])
        self.assertNotIn("used_relation_ids", payload["required_json"])
        self.assertTrue(
            any("at most three" in rule for rule in payload["rules"])
        )
        self.assertTrue(
            any(
                "Do not silently correct or reinterpret" in rule
                for rule in payload["rules"]
            )
        )

    def test_v31_accepts_three_claims_and_derives_each_source(self) -> None:
        context = evidence_context(
            direct_evidence(relation_ids=["R1"]),
            direct_evidence(
                evidence_id="E2",
                qa_id="qa-2",
                evidence="تُراجع أعراض الربو بعد بدء العلاج.",
                relation_ids=["R2"],
            ),
            direct_evidence(
                evidence_id="E3",
                qa_id="qa-3",
                evidence="يُقيّم الطبيب شدة الربو قبل تعديل العلاج.",
                relation_ids=["R3"],
            ),
        )
        result = validate_answer_payload(
            {
                "claims": [
                    {
                        "claim_ar": "يستخدم بخاخ موسع للشعب في علاج الربو.",
                        "citations": ["E1"],
                    },
                    {
                        "claim_ar": "تُراجع أعراض الربو بعد بدء العلاج.",
                        "citations": ["E2"],
                    },
                    {
                        "claim_ar": "يُقيّم الطبيب شدة الربو قبل تعديل العلاج.",
                        "citations": ["E3"],
                    },
                ],
                "limitations_ar": [],
            },
            context,
            self.config,
        )

        self.assertEqual(result.generation_mode, V31_STRUCTURED_MODE)
        self.assertEqual(len(result.claims), 3)
        self.assertEqual(
            [claim.source_qa_ids for claim in result.claims],
            [["qa-1"], ["qa-2"], ["qa-3"]],
        )
        self.assertEqual(result.used_relations, ["R1", "R2", "R3"])
        self.assertEqual(result.generation_evidence_ids, ["E1", "E2", "E3"])

    def test_v31_rejects_more_than_three_claims(self) -> None:
        context = evidence_context()
        with self.assertRaisesRegex(ValueError, "at most 3"):
            validate_answer_payload(
                {
                    "claims": [
                        {
                            "claim_ar": f"علاج الربو المدعوم رقم {index}.",
                            "citations": ["E1"],
                        }
                        for index in range(1, 5)
                    ],
                    "limitations_ar": [],
                },
                context,
                self.config,
            )

    def test_step13_preserves_v31_self_contained_claim(self) -> None:
        compound = AnswerClaim(
            claim=(
                "لعلاج الربو يستخدم بخاخ موسع للشعب، كما يراجع الطبيب شدة الربو."
            ),
            citations=["E1"],
            source_qa_ids=["qa-1"],
        )
        generated = GeneratedAnswer(
            query="ما علاج الربو؟",
            answer=compound.claim,
            claims=[compound],
            prompt_version=V31_PROMPT_VERSION,
            generation_mode=V31_STRUCTURED_MODE,
        )

        self.assertEqual(extract_claims(generated), [compound])


if __name__ == "__main__":
    unittest.main()
