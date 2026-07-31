from __future__ import annotations

import unittest

from src.step14_semantic_safety_gate import semantic_rescue_safety_failures


class SemanticRescueSafetyGateTests(unittest.TestCase):
    def test_bare_reassurance_is_blocked(self) -> None:
        failures = semantic_rescue_safety_failures(
            "لا داعي للقلق",
            ["لا داعي للقلق لكن لا بد من فحص طبي سريري."],
        )
        self.assertIn("bare_reassurance_without_medical_answer", failures)

    def test_medically_scoped_reassurance_is_not_bare(self) -> None:
        failures = semantic_rescue_safety_failures(
            "نزول كتل من الدم أثناء الدورة الشهرية عادي ولا خطورة منه.",
            ["هذا عادي ولا خطر منه، ولكن اعملي فحص قوة الدم."],
        )
        self.assertNotIn(
            "bare_reassurance_without_medical_answer",
            failures,
        )

    def test_missing_parenthetical_identifier_is_blocked(self) -> None:
        failures = semantic_rescue_safety_failures(
            "الدواء لا يؤثر على نتيجة التحليل (hCG).",
            ["الدواء لا يؤثر على الحمل عند استخدامه مرة واحدة."],
        )
        self.assertIn("unsupported_parenthetical_identifier", failures)

    def test_present_parenthetical_identifier_is_allowed(self) -> None:
        failures = semantic_rescue_safety_failures(
            "لا تتغير نتيجة (hCG).",
            ["لا تتغير نتيجة hCG عند استخدام العلاج."],
        )
        self.assertNotIn("unsupported_parenthetical_identifier", failures)

    def test_changed_condition_scope_is_blocked(self) -> None:
        failures = semantic_rescue_safety_failures(
            "احتمال الحمل ضعيف إذا وجدت إفرازات قبل القذف.",
            ["الاحتمال ضعيف عند وجود منويات من قذف سابق."],
        )
        self.assertIn("unsupported_condition_scope", failures)

    def test_supported_condition_scope_is_allowed(self) -> None:
        failures = semantic_rescue_safety_failures(
            "إذا كانت صعوبة التنفس شديدة ومستمرة يجب مراجعة الطبيب.",
            ["إذا كانت صعوبة التنفس شديدة ومستمرة فعليك مراجعة الطبيب."],
        )
        self.assertNotIn("unsupported_condition_scope", failures)

    def test_generic_other_symptoms_can_be_supported_by_examples(self) -> None:
        failures = semantic_rescue_safety_failures(
            "اطلب العناية الطبية خاصة إذا كانت مصحوبة بأعراض أخرى.",
            ["اطلب العناية الطبية عند ألم الصدر أو تورم الوجه."],
        )
        self.assertNotIn("unsupported_condition_scope", failures)

    def test_unsupported_directional_outcome_is_blocked(self) -> None:
        failures = semantic_rescue_safety_failures(
            "قد يساعد شرب الماء في زيادة حركة الحيوانات المنوية.",
            ["ينصح بشرب الماء وممارسة الرياضة."],
        )
        self.assertIn("unsupported_directional_outcome", failures)

    def test_supported_directional_outcome_is_allowed(self) -> None:
        failures = semantic_rescue_safety_failures(
            "قد يرفع عرق السوس ضغط الدم.",
            ["قد يؤدي عرق السوس إلى ارتفاع ضغط الدم."],
        )
        self.assertNotIn("unsupported_directional_outcome", failures)


if __name__ == "__main__":
    unittest.main()
