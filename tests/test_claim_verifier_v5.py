from __future__ import annotations

import unittest

from src.models import (
    AnswerClaim,
    ClaimVerification,
    EvidenceContextBundle,
)
from src.step14_semantic_adjudication import (
    eligible_for_semantic_adjudication,
)
from src.step14_verify_claims_v5 import (
    apply_v5_hard_gates,
    introduces_unsupported_relation,
    relation_families,
)


class ClaimVerifierV5Tests(unittest.TestCase):
    def make_context(
        self,
        evidence: str,
        **metadata: object,
    ) -> EvidenceContextBundle:
        return EvidenceContextBundle(
            query="ما سبب الدوخة؟",
            reformulated_query="ما سبب الدوخة؟",
            primary_intent="cause_request",
            evidence_items=[
                {
                    "evidence_id": "E1",
                    "qa_id": "qa1",
                    "evidence": evidence,
                    "source_answer": evidence,
                    "source_question": "ما سبب الدوخة؟",
                    "relation_ids": [],
                    **metadata,
                }
            ],
            allowed_evidence_ids=["E1"],
            allowed_qa_ids=["qa1"],
        )

    def make_verification(
        self,
        claim: str,
        *,
        support_score: float = 0.75,
        status: str = "unsupported",
        failures: list[str] | None = None,
    ) -> ClaimVerification:
        return ClaimVerification(
            claim=AnswerClaim(claim, ["E1"], ["qa1"]),
            status=status,
            support_score=support_score,
            question_relevance=0.90,
            query_concept_coverage=0.50,
            valid_citations=["E1"] if status == "supported" else [],
            valid_qa_ids=["qa1"] if status == "supported" else [],
            best_evidence_id="E1",
            failed_checks=failures or ["intent_mismatch"],
        )

    def test_anatomy_failure_is_never_semantically_eligible(self) -> None:
        verification = self.make_verification(
            "يوجد ألم في المعدة",
            failures=["anatomy_mismatch"],
        )
        self.assertFalse(eligible_for_semantic_adjudication(verification))

    def test_intent_or_concept_only_failure_remains_eligible(self) -> None:
        verification = self.make_verification(
            "ينصح بقياس ضغط الدم",
            failures=["intent_mismatch", "claim_query_concept_mismatch"],
        )
        self.assertTrue(eligible_for_semantic_adjudication(verification))

    def test_query_anatomy_can_resolve_answer_pronoun(self) -> None:
        context = EvidenceContextBundle(
            query="هل يوجد التهاب في العين؟",
            reformulated_query="هل يوجد التهاب في العين؟",
            evidence_items=[
                {
                    "evidence_id": "E1",
                    "qa_id": "qa1",
                    "source_answer": "ممكن أن يكون التهاباً ويلزم فحص الطبيب.",
                    "relation_ids": [],
                }
            ],
            allowed_evidence_ids=["E1"],
        )
        verification = self.make_verification(
            "ممكن أن يكون التهاباً في العين.",
            failures=["anatomy_mismatch", "intent_mismatch"],
        )
        hardened, audit = apply_v5_hard_gates(
            [verification],
            context,
        )
        self.assertNotIn("anatomy_mismatch", hardened[0].failed_checks)
        self.assertTrue(audit[0]["semantic_eligible"])

    def test_new_anatomy_absent_from_query_and_evidence_is_blocked(self) -> None:
        verification = self.make_verification(
            "قد يكون الالتهاب في الكبد.",
        )
        hardened, audit = apply_v5_hard_gates(
            [verification],
            self.make_context("قد يكون هناك التهاب."),
        )
        self.assertIn("anatomy_mismatch", hardened[0].failed_checks)
        self.assertFalse(audit[0]["semantic_eligible"])

    def test_relation_family_detects_invented_medication_cause(self) -> None:
        evidence = "هناك أسباب التهابية وعدوائية وتنفسية وقلبية ودموية."
        claim = "قد تكون الأسباب التهابية أو دوائية أو تنفسية."
        self.assertIn("medication_or_treatment", relation_families(claim))
        self.assertTrue(introduces_unsupported_relation(claim, evidence))

        hardened, audit = apply_v5_hard_gates(
            [self.make_verification(claim, status="supported", failures=[])],
            self.make_context(evidence),
        )
        self.assertEqual(hardened[0].status, "unsupported")
        self.assertIn(
            "clinical_relation_mismatch",
            hardened[0].failed_checks,
        )
        self.assertFalse(audit[0]["semantic_eligible"])

    def test_matching_clinical_relation_is_not_blocked(self) -> None:
        evidence = "قد تسبب بعض الأدوية الدوخة."
        claim = "قد تكون الدوخة ناتجة عن بعض الأدوية."
        self.assertFalse(introduces_unsupported_relation(claim, evidence))

        hardened, audit = apply_v5_hard_gates(
            [self.make_verification(claim)],
            self.make_context(evidence),
        )
        self.assertEqual(hardened[0].failed_checks, ["intent_mismatch"])
        self.assertTrue(audit[0]["semantic_eligible"])

    def test_low_identity_low_coverage_context_is_hard_blocked(self) -> None:
        context = self.make_context(
            "ينصح بمراجعة الطبيب عند استمرار ألم القولون.",
            entity_identity=0.05,
            query_concept_coverage=0.10,
        )
        verification = self.make_verification(
            "ينصح بمراجعة الطبيب عند استمرار الألم.",
        )
        hardened, audit = apply_v5_hard_gates(
            [verification],
            context,
        )
        self.assertEqual(hardened[0].status, "unsupported")
        self.assertIn(
            "patient_context_mismatch",
            hardened[0].failed_checks,
        )
        self.assertFalse(audit[0]["semantic_eligible"])

    def test_list_claim_requires_complete_support(self) -> None:
        evidence = "لكل مرض قلبي سببه الخاص."
        verification = self.make_verification(
            "أسباب مرض القلب تشمل مشاكل الصمامات والشرايين.",
            support_score=0.416667,
        )
        hardened, audit = apply_v5_hard_gates(
            [verification],
            self.make_context(evidence),
        )
        self.assertIn(
            "incomplete_list_support",
            hardened[0].failed_checks,
        )
        self.assertFalse(audit[0]["semantic_eligible"])

    def test_well_supported_list_can_reach_soft_review(self) -> None:
        evidence = "أسباب الرعشة تشمل القلق واضطرابات الغدة الدرقية."
        verification = self.make_verification(
            "أسباب الرعشة تشمل القلق واضطرابات الغدة الدرقية.",
            support_score=0.90,
        )
        hardened, audit = apply_v5_hard_gates(
            [verification],
            self.make_context(evidence),
        )
        self.assertNotIn(
            "incomplete_list_support",
            hardened[0].failed_checks,
        )
        self.assertTrue(audit[0]["semantic_eligible"])


if __name__ == "__main__":
    unittest.main()
