from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from src.config import AppConfig, ClaimAdjudicationConfig
from src.models import AnswerClaim, ClaimVerification, EvidenceContextBundle
from src.step14_semantic_adjudication import (
    SemanticClaimAdjudicator,
    adjudication_fingerprint,
    build_adjudication_cases,
    build_messages,
    eligible_for_semantic_adjudication,
    validate_response,
)


class SemanticClaimAdjudicationTests(unittest.TestCase):
    def make_context(self) -> EvidenceContextBundle:
        return EvidenceContextBundle(
            query="ما أضرار الإفراط في عرق السوس؟",
            reformulated_query="ما أضرار تناول عرق السوس بكميات كبيرة؟",
            primary_intent="symptom_request",
            evidence_items=[
                {
                    "evidence_id": "E1",
                    "qa_id": "qa1",
                    "evidence": (
                        "يمكن أن يؤدي تناول عرق السوس بكميات كبيرة إلى "
                        "ارتفاع ضغط الدم."
                    ),
                    "source_answer": (
                        "الإفراط في عرق السوس قد يرفع ضغط الدم ويسبب "
                        "احتباس السوائل."
                    ),
                    "source_question": "ما فوائد عرق السوس وأضراره؟",
                    "relation_ids": ["R1"],
                }
            ],
            graph_facts=[
                {
                    "relation_id": "R1",
                    "fact": "الإفراط في عرق السوس قد يرفع ضغط الدم.",
                }
            ],
            allowed_evidence_ids=["E1"],
            allowed_qa_ids=["qa1"],
        )

    def make_verification(
        self,
        *,
        failures: list[str] | None = None,
    ) -> ClaimVerification:
        return ClaimVerification(
            claim=AnswerClaim(
                "تناول عرق السوس بكميات كبيرة قد يرفع ضغط الدم.",
                ["E1"],
                ["qa1"],
            ),
            status="unsupported",
            support_score=0.875,
            question_relevance=0.98,
            best_evidence_id="E1",
            failed_checks=failures or ["intent_mismatch"],
        )

    def test_only_soft_gate_failures_are_eligible(self) -> None:
        self.assertTrue(
            eligible_for_semantic_adjudication(self.make_verification())
        )
        self.assertFalse(
            eligible_for_semantic_adjudication(
                self.make_verification(
                    failures=["intent_mismatch", "number_mismatch"]
                )
            )
        )

    def test_response_fails_closed_on_inconsistent_retain_flag(self) -> None:
        config = ClaimAdjudicationConfig()
        decisions = validate_response(
            {
                "decisions": [
                    {
                        "claim_id": "C1",
                        "evidence_support": "partial",
                        "query_relevance": "relevant",
                        "intent_match": True,
                        "concept_match": True,
                        "anatomy_match": "not_applicable",
                        "answer_contribution": "direct_answer",
                        "clinical_relation_preserved": True,
                        "named_entity_identity_preserved": True,
                        "patient_context_compatible": True,
                        "should_retain": True,
                        "reason": "Only part of the claim is supported.",
                    }
                ]
            },
            {"C1"},
            config,
        )
        self.assertFalse(decisions[0].should_retain)
        self.assertIn("Python fail-closed", decisions[0].reason)

    def test_generic_advice_cannot_be_marked_for_retention(self) -> None:
        config = ClaimAdjudicationConfig()
        decisions = validate_response(
            {
                "decisions": [
                    {
                        "claim_id": "C1",
                        "evidence_support": "supported",
                        "query_relevance": "relevant",
                        "intent_match": True,
                        "concept_match": True,
                        "anatomy_match": "not_applicable",
                        "answer_contribution": "generic_advice",
                        "clinical_relation_preserved": True,
                        "named_entity_identity_preserved": True,
                        "patient_context_compatible": True,
                        "should_retain": True,
                        "reason": "The advice is supported but generic.",
                    }
                ]
            },
            {"C1"},
            config,
        )
        self.assertFalse(decisions[0].should_retain)

    def test_named_entity_mismatch_cannot_be_marked_for_retention(self) -> None:
        config = ClaimAdjudicationConfig()
        decisions = validate_response(
            {
                "decisions": [
                    {
                        "claim_id": "C1",
                        "evidence_support": "supported",
                        "query_relevance": "relevant",
                        "intent_match": True,
                        "concept_match": True,
                        "anatomy_match": "not_applicable",
                        "answer_contribution": "direct_answer",
                        "clinical_relation_preserved": True,
                        "named_entity_identity_preserved": False,
                        "patient_context_compatible": True,
                        "should_retain": True,
                        "reason": "The query and evidence name different drugs.",
                    }
                ]
            },
            {"C1"},
            config,
        )
        self.assertFalse(decisions[0].should_retain)

    def test_question_only_evidence_is_not_sent_for_adjudication(self) -> None:
        context = EvidenceContextBundle(
            query="why is my period delayed?",
            reformulated_query="why is my period delayed?",
            evidence_items=[
                {
                    "evidence_id": "E1",
                    "evidence": "period delayed for three weeks",
                    "source_question": (
                        "period delayed for three weeks with pregnancy symptoms"
                    ),
                    "source_answer": "",
                    "source_quality": "mention_evidence",
                    "relation_ids": [],
                }
            ],
            allowed_evidence_ids=["E1"],
        )
        verification = ClaimVerification(
            claim=AnswerClaim("period delayed for three weeks", ["E1"]),
            status="unsupported",
            support_score=1.0,
            question_relevance=1.0,
            best_evidence_id="E1",
            failed_checks=["intent_mismatch"],
        )

        cases, verification_by_claim_id = build_adjudication_cases(
            [verification],
            context,
        )

        self.assertEqual(cases, [])
        self.assertEqual(verification_by_claim_id, {})

    def test_unrelated_answer_does_not_inherit_question_support_score(self) -> None:
        context = EvidenceContextBundle(
            query="why is my period delayed?",
            reformulated_query="why is my period delayed?",
            evidence_items=[
                {
                    "evidence_id": "E1",
                    "evidence": "period delayed for three weeks",
                    "source_question": (
                        "period delayed for three weeks with pregnancy symptoms"
                    ),
                    "source_answer": "perform a pregnancy blood test",
                    "source_quality": "mention_evidence",
                    "relation_ids": [],
                }
            ],
            allowed_evidence_ids=["E1"],
        )
        verification = ClaimVerification(
            claim=AnswerClaim("period delayed for three weeks", ["E1"]),
            status="unsupported",
            support_score=1.0,
            question_relevance=1.0,
            best_evidence_id="E1",
            failed_checks=["intent_mismatch"],
        )

        cases, verification_by_claim_id = build_adjudication_cases(
            [verification],
            context,
        )

        self.assertEqual(cases, [])
        self.assertEqual(verification_by_claim_id, {})

    def test_outbound_payload_contains_only_approved_fields_and_redacts_ids(self) -> None:
        context = EvidenceContextBundle(
            query="اتصل بي على 123456789 أو test@example.com بخصوص السعال",
            reformulated_query="السؤال عن السعال",
        )
        messages = build_messages(
            context,
            [
                {
                    "claim_id": "C1",
                    "claim": "السعال يحتاج إلى تقييم",
                    "evidence_segments": ["راجع https://example.com والدليل الطبي."],
                    "cited_evidence_id": "must-not-leave-workspace",
                    "source_question_context_only": "must-not-leave-workspace",
                }
            ],
        )
        payload = json.loads(messages[1]["content"])

        self.assertEqual(set(payload), {"query", "claims"})
        self.assertEqual(
            set(payload["claims"][0]),
            {"claim_id", "claim", "evidence_segments"},
        )
        serialized = json.dumps(payload, ensure_ascii=False)
        self.assertNotIn("123456789", serialized)
        self.assertNotIn("test@example.com", serialized)
        self.assertNotIn("https://example.com", serialized)
        self.assertNotIn("must-not-leave-workspace", serialized)

    def test_cached_supported_decision_promotes_soft_rejection(self) -> None:
        context = self.make_context()
        verification = self.make_verification()
        config = AppConfig(
            claim_adjudication=ClaimAdjudicationConfig(enabled=True)
        )
        cases, _ = build_adjudication_cases([verification], context)
        fingerprint = adjudication_fingerprint(
            context,
            cases,
            config.claim_adjudication,
        )
        response = {
            "decisions": [
                {
                    "claim_id": "C1",
                    "evidence_support": "supported",
                    "query_relevance": "relevant",
                    "intent_match": True,
                    "concept_match": True,
                    "anatomy_match": "not_applicable",
                    "answer_contribution": "direct_answer",
                    "clinical_relation_preserved": True,
                    "named_entity_identity_preserved": True,
                    "patient_context_compatible": True,
                    "should_retain": True,
                    "reason": "The cited answer directly supports the harm.",
                }
            ]
        }
        with tempfile.TemporaryDirectory() as directory:
            cache_path = Path(directory) / "cache.jsonl"
            cache_path.write_text(
                json.dumps(
                    {
                        "fingerprint": fingerprint,
                        "status": "ok",
                        "response": response,
                    },
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )
            adjudicator = SemanticClaimAdjudicator(
                config,
                cache_path=cache_path,
                raise_on_error=True,
            )
            updated, audit = adjudicator.adjudicate([verification], context)

        self.assertTrue(audit["cache_hit"])
        self.assertEqual(updated[0].status, "supported")
        self.assertEqual(updated[0].valid_citations, ["E1"])
        self.assertEqual(updated[0].valid_qa_ids, ["qa1"])
        self.assertEqual(updated[0].supporting_relation_ids, ["R1"])
        self.assertEqual(updated[0].failed_checks, [])

    def test_cached_rejection_preserves_deterministic_result(self) -> None:
        context = self.make_context()
        verification = self.make_verification()
        config = AppConfig(
            claim_adjudication=ClaimAdjudicationConfig(enabled=True)
        )
        cases, _ = build_adjudication_cases([verification], context)
        fingerprint = adjudication_fingerprint(
            context,
            cases,
            config.claim_adjudication,
        )
        response = {
            "decisions": [
                {
                    "claim_id": "C1",
                    "evidence_support": "partial",
                    "query_relevance": "relevant",
                    "intent_match": True,
                    "concept_match": True,
                    "anatomy_match": "not_applicable",
                    "answer_contribution": "partial_answer",
                    "clinical_relation_preserved": True,
                    "named_entity_identity_preserved": True,
                    "patient_context_compatible": True,
                    "should_retain": False,
                    "reason": "The evidence supports only part of the claim.",
                }
            ]
        }
        with tempfile.TemporaryDirectory() as directory:
            cache_path = Path(directory) / "cache.jsonl"
            cache_path.write_text(
                json.dumps(
                    {
                        "fingerprint": fingerprint,
                        "status": "ok",
                        "response": response,
                    },
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )
            adjudicator = SemanticClaimAdjudicator(
                config,
                cache_path=cache_path,
                raise_on_error=True,
            )
            updated, audit = adjudicator.adjudicate([verification], context)

        self.assertTrue(audit["cache_hit"])
        self.assertEqual(updated, [verification])


if __name__ == "__main__":
    unittest.main()
