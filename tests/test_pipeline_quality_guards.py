from __future__ import annotations

import unittest
from dataclasses import replace

from src.config import AppConfig, RetrievalConfig
from src.models import (
    AnswerClaim,
    EvidenceContextBundle,
    ExtractedMedicalPhrase,
    GeneratedAnswer,
    HybridRetrievalBundle,
    QueryEntityLinkingResult,
    RerankedSubgraph,
    RetrievalPlanResult,
    RetrievedEvidence,
    RetrievedMedicalRelation,
    UnifiedQueryAnalysisResult,
    VectorSearchResult,
)
from src.step09_hybrid_retrieval import anatomy_terms, medical_identity_similarity, score_relations, seed_scores
from src.step08b_analyze_query import fallback_result
from src.step10_rerank_subgraph import rerank_subgraph
from src.step11_build_evidence_context import build_evidence_context
from src.step13_extract_claims import extract_claims
from src.step14_verify_claims import verify_claims
from src.step12_generate_grounded_answer import fallback_answer
from src.step15_mitigate_hallucinations import mitigate_hallucinations


def plan(primary_ids: list[str] | None = None) -> RetrievalPlanResult:
    return RetrievalPlanResult(
        original_query="ما علاج الربو؟",
        corrected_query="ما علاج الربو؟",
        reformulated_query="ما علاج الربو؟",
        query_class="simple_medical",
        complexity="low",
        primary_intent="treatment_request",
        use_vector_search=True,
        use_graph_search=True,
        hop_depth=1,
        entity_top_k=10,
        evidence_top_k=10,
        qa_top_k=5,
        preferred_relation_types=["TREATED_BY", "TREATS"],
        primary_entity_ids=primary_ids or [],
    )


def analysis(query: str, entity_type: str = "DiseaseCondition") -> UnifiedQueryAnalysisResult:
    return UnifiedQueryAnalysisResult(
        original_query=query,
        normalized_query=query,
        corrected_query=query,
        reformulated_query=query,
        query_class="simple_medical",
        complexity="low",
        primary_intent="treatment_request",
        medical_phrases=[
            ExtractedMedicalPhrase("الربو", "الربو", entity_type, "corrected_query", 1.0)
        ],
    )


class RetrievalQualityGuardTests(unittest.TestCase):
    def test_hard_link_prevents_unrelated_semantic_graph_seed(self) -> None:
        vectors = [
            VectorSearchResult(
                result_id="wrong",
                document_type="MedicalEntity",
                score=0.99,
                entity_id="wrong",
                title="التهاب الركبة",
                metadata={"entity_type": "DiseaseCondition"},
            )
        ]
        scores = seed_scores(
            QueryEntityLinkingResult("q", "q", "q", "simple_medical", "low"),
            plan(["asthma"]),
            vectors,
            AppConfig(),
            analysis=analysis("ما علاج الربو؟"),
        )
        self.assertEqual(scores, {"asthma": 1.0})

    def test_semantic_anatomical_conflict_is_removed(self) -> None:
        rows = [
            {
                "relation_id": "r1",
                "source_relation_id": "r1",
                "seed_entity_id": "knee",
                "seed_entity_type": "DiseaseCondition",
                "source_entity_id": "knee",
                "source_name": "التهاب الركبة",
                "source_entity_type": "DiseaseCondition",
                "target_entity_id": "drug",
                "target_name": "مسكن",
                "target_entity_type": "Treatment",
                "relation_type": "TREATED_BY",
                "confidence": 1.0,
            }
        ]
        results = score_relations(
            rows,
            "ما علاج ألم العين؟",
            {"knee": 0.7},
            ["TREATED_BY"],
            [],
            analysis=analysis("ما علاج ألم العين؟"),
        )
        self.assertEqual(results, [])

    def test_context_is_dynamic_and_not_padded_to_twelve(self) -> None:
        evidence = [
            RetrievedEvidence(
                evidence_id=f"qa::{index}",
                source_id=str(index),
                qa_id=str(index),
                text="علاج الربو بالبخاخ حسب وصف الطبيب",
                question="ما علاج الربو؟",
                score=score,
            )
            for index, score in enumerate([0.90, 0.84, 0.60, 0.40, 0.20], start=1)
        ]
        bundle = HybridRetrievalBundle(
            query="ما علاج الربو؟",
            normalized_query="ما علاج الربو؟",
            reformulated_query="ما علاج الربو؟",
            plan=plan(),
            evidence=evidence,
        )
        context = build_evidence_context(
            rerank_subgraph(bundle, config=AppConfig()),
            "ما علاج الربو؟",
            config=replace(
                AppConfig(),
                retrieval=replace(RetrievalConfig(), context_max_items=6),
            ),
        )
        self.assertLess(len(context.evidence_items), 5)
        self.assertLessEqual(len(context.evidence_items), 6)

    def test_context_preserves_one_relation_backed_evidence_item(self) -> None:
        vector_item = RetrievedEvidence(
            evidence_id="mention::vector",
            source_id="vector",
            qa_id="qa1",
            text="معلومة عن الربو",
            question="ما علاج الربو؟",
            score=0.90,
        )
        relation_item = RetrievedEvidence(
            evidence_id="mention::relation",
            source_id="relation",
            qa_id="qa2",
            text="يستخدم البخاخ للربو",
            answer="يستخدم البخاخ لعلاج الربو",
            score=0.45,
            relation_ids=["r1"],
        )
        relation = RetrievedMedicalRelation(
            relation_id="r1",
            source_relation_id="r1",
            source_entity_id="asthma",
            source_name="الربو",
            target_entity_id="inhaler",
            target_name="البخاخ",
            relation_type="TREATED_BY",
            confidence=0.9,
            hybrid_score=0.7,
        )
        subgraph = rerank_subgraph(
            HybridRetrievalBundle(
                query="ما علاج الربو؟",
                normalized_query="ما علاج الربو؟",
                reformulated_query="ما علاج الربو؟",
                plan=plan(),
                relations=[relation],
                evidence=[vector_item, relation_item],
            ),
            config=AppConfig(),
        )
        context = build_evidence_context(subgraph, "ما علاج الربو؟", config=AppConfig())
        self.assertTrue(any(item["relation_ids"] for item in context.evidence_items))
        self.assertEqual(len(context.graph_facts), 1)

    def test_claims_are_recovered_from_successful_unstructured_answer(self) -> None:
        generated = GeneratedAnswer(
            query="q",
            answer="يستخدم البخاخ لعلاج الربو [E1]. ويجب اتباع وصف الطبيب [E2].",
            generation_status="generated",
        )
        claims = extract_claims(generated)
        self.assertEqual(len(claims), 2)
        self.assertEqual(claims[0].citations, ["E1"])

    def test_fallback_is_not_treated_as_generated_factual_claims(self) -> None:
        generated = GeneratedAnswer(
            query="q",
            answer="لا توجد أدلة كافية في الرسم الطبي للإجابة بثقة.",
            generation_status="fallback",
        )
        self.assertEqual(extract_claims(generated), [])

    def test_relation_fact_can_support_a_cited_claim(self) -> None:
        context = EvidenceContextBundle(
            query="ما علاج الربو؟",
            reformulated_query="ما علاج الربو؟",
            graph_facts=[{"relation_id": "R1", "fact": "الربو TREATED_BY البخاخ"}],
            evidence_items=[
                {
                    "evidence_id": "E1",
                    "evidence": "",
                    "source_question": "",
                    "source_answer": "",
                    "relation_ids": ["R1"],
                }
            ],
            allowed_evidence_ids=["E1"],
        )
        rows = verify_claims([AnswerClaim("يعالج الربو بالبخاخ", ["E1"])], context)
        self.assertIn(rows[0].status, {"supported", "weakly_supported"})

    def test_unrelated_negation_in_another_sentence_does_not_reject_claim(self) -> None:
        context = EvidenceContextBundle(
            query="ما مضاعفات فرط فيتامين أ؟",
            reformulated_query="ما مضاعفات فرط فيتامين أ؟",
            evidence_items=[
                {
                    "evidence_id": "E1",
                    "evidence": "التسمم بفرط فيتامين أ يسبب تضخم الكبد. لا تستخدم جرعات عالية دون طبيب.",
                    "source_question": "",
                    "source_answer": "",
                    "relation_ids": [],
                }
            ],
            allowed_evidence_ids=["E1"],
        )
        rows = verify_claims(
            [AnswerClaim("التسمم بفرط فيتامين أ يسبب تضخم الكبد", ["E1"])],
            context,
        )
        self.assertEqual(rows[0].status, "supported")

    def test_named_hormone_identity_distinguishes_progesterone_from_testosterone(self) -> None:
        query = "رفع مستوى هرمون البروجستيرون"
        progesterone = medical_identity_similarity(query, "هرمون البروجسترون")
        testosterone = medical_identity_similarity(query, "هرمون التستوستيرون")
        self.assertGreaterEqual(progesterone, 0.90)
        self.assertLess(testosterone, 0.86)

    def test_conversational_overlap_is_not_medical_entity_identity(self) -> None:
        eye_query = "أنا أعاني من ضعف النظر والحول في العين اليسرى"
        unrelated = "أنا أعاني من ألم الرأس وكثرة النسيان"
        self.assertLess(medical_identity_similarity(eye_query, unrelated), 0.50)

    def test_arabic_clitics_do_not_hide_anatomical_locations(self) -> None:
        self.assertEqual(anatomy_terms("بطني متورم وأخشى تضخماً بالكبد"), {"بطن", "كبد"})
        self.assertEqual(anatomy_terms("انتفاخ تحت الإبط وبالوجه"), {"ابط", "وجه"})
        self.assertEqual(anatomy_terms("انتفاخ برجلي"), {"رجل"})

    def test_step11_rejects_supported_but_query_irrelevant_evidence(self) -> None:
        irrelevant = RetrievedEvidence(
            evidence_id="mention::vitamin-a",
            source_id="vitamin-a",
            qa_id="qa-vitamin-a",
            text="فرط فيتامين أ قد يسبب تضخم الكبد",
            question="ما علاج فرط فيتامين أ؟",
            score=0.90,
            metadata={"answer_relevance": 0.10},
        )
        context = build_evidence_context(
            RerankedSubgraph(
                query="ما التحاليل اللازمة لانتفاخ البطن؟",
                primary_intent="test_request",
                evidence=[irrelevant],
            ),
            "ما التحاليل اللازمة لانتفاخ البطن؟",
            config=AppConfig(),
        )
        self.assertEqual(context.evidence_items, [])

    def test_reranker_hard_rejects_explicit_anatomical_mismatch(self) -> None:
        chest = RetrievedEvidence(
            evidence_id="qa::chest",
            source_id="chest",
            qa_id="chest",
            text="تم إجراء أشعة للصدر",
            question="لدي سعال وألم في الصدر، ما الفحص المطلوب؟",
            score=0.95,
        )
        test_plan = replace(
            plan(),
            primary_intent="test_request",
            preferred_relation_types=["INVESTIGATED_BY", "INVESTIGATES"],
        )
        reranked = rerank_subgraph(
            HybridRetrievalBundle(
                query="ما التحاليل اللازمة لانتفاخ البطن وتضخم الكبد؟",
                normalized_query="ما التحاليل اللازمة لانتفاخ البطن وتضخم الكبد؟",
                reformulated_query="ما التحاليل اللازمة لانتفاخ البطن وتضخم الكبد؟",
                plan=test_plan,
                evidence=[chest],
            ),
            config=AppConfig(),
        )
        self.assertEqual(reranked.evidence[0].metadata["answer_relevance"], 0.0)

    def test_verifier_rejects_an_organ_added_beyond_the_citation(self) -> None:
        context = EvidenceContextBundle(
            query="ما الفحص المناسب لانتفاخ البطن وتضخم الكبد؟",
            reformulated_query="ما الفحص المناسب لانتفاخ البطن وتضخم الكبد؟",
            evidence_items=[
                {
                    "evidence_id": "E1",
                    "evidence": "يجب فحص البطن بالسونار للتأكد من سلامة المرارة",
                    "source_question": "",
                    "source_answer": "",
                    "relation_ids": [],
                }
            ],
            allowed_evidence_ids=["E1"],
        )
        rows = verify_claims(
            [AnswerClaim("ينصح بفحص البطن بالسونار للتأكد من سلامة المرارة والكبد", ["E1"])],
            context,
        )
        self.assertEqual(rows[0].status, "unsupported")

    def test_technical_fallback_is_not_reported_as_insufficient_evidence(self) -> None:
        context = EvidenceContextBundle(
            query="ما علاج الربو؟",
            reformulated_query="ما علاج الربو؟",
            evidence_items=[{"evidence_id": "E1", "evidence": "دليل"}],
        )
        generated = fallback_answer(
            context,
            "HTTPError 503",
            AppConfig(),
            attempt_count=3,
            fallback_type="technical_failure",
        )
        mitigated = mitigate_hallucinations(generated, [])
        self.assertEqual(generated.fallback_type, "technical_failure")
        self.assertEqual(mitigated.answerability, "generation_unavailable")
        self.assertIn("مشكلة تقنية", mitigated.answer)

    def test_query_analysis_failure_recovers_explicit_test_intent(self) -> None:
        result = fallback_result(
            "ما هي التحاليل اللازمة لانتفاخ البطن؟",
            "ما هي التحاليل اللازمه لانتفاخ البطن؟",
            AppConfig(),
            "Unified LLM query analysis failed: HTTPError",
        )
        self.assertEqual(result.primary_intent, "test_request")
        self.assertEqual(result.preferred_relation_types, ["INVESTIGATED_BY", "INVESTIGATES"])
        self.assertEqual(result.medical_phrases, [])

    def test_step11_rejects_symptom_restatement_for_test_request(self) -> None:
        symptom_only = RetrievedEvidence(
            evidence_id="qa::symptom-only",
            source_id="symptom-only",
            qa_id="symptom-only",
            text="انتفاخ في البطن",
            question="المريض لديه انتفاخ في البطن",
            score=0.90,
            metadata={
                "answer_relevance": 0.80,
                "entity_identity": 1.0,
                "intent_support": 0.0,
            },
        )
        context = build_evidence_context(
            RerankedSubgraph(
                query="ما هي التحاليل اللازمة لانتفاخ البطن؟",
                primary_intent="test_request",
                evidence=[symptom_only],
            ),
            "ما هي التحاليل اللازمة لانتفاخ البطن؟",
            config=AppConfig(),
        )
        self.assertEqual(context.evidence_items, [])

    def test_verifier_rejects_symptom_restatement_for_test_request(self) -> None:
        context = EvidenceContextBundle(
            query="ما هي التحاليل اللازمة لانتفاخ البطن؟",
            reformulated_query="ما هي التحاليل اللازمة لانتفاخ البطن؟",
            primary_intent="test_request",
            evidence_items=[
                {
                    "evidence_id": "E1",
                    "evidence": "انتفاخ في البطن",
                    "source_question": "المريض لديه انتفاخ في البطن",
                    "source_answer": "انتفاخ في البطن",
                    "relation_ids": [],
                }
            ],
            allowed_evidence_ids=["E1"],
        )
        rows = verify_claims([AnswerClaim("انتفاخ في البطن", ["E1"])], context)
        self.assertEqual(rows[0].status, "unsupported")

    def test_verifier_uses_vetted_context_relevance_for_a_paraphrase(self) -> None:
        context = EvidenceContextBundle(
            query="لدي ضعف في النظر وحول، ماذا أفعل؟",
            reformulated_query="لدي ضعف في النظر وحول، ماذا أفعل؟",
            primary_intent="test_request",
            evidence_items=[
                {
                    "evidence_id": "E1",
                    "evidence": "يجب إجراء فحص كامل للعين يشمل قياس البصر وضغط العين وفحص قاع العين",
                    "source_question": "ما الفحوصات المطلوبة لمشكلة في الرؤية؟",
                    "source_answer": "فحص كامل للعين وقياس البصر وضغط العين وفحص قاع العين",
                    "answer_relevance": 0.82,
                    "relation_ids": [],
                }
            ],
            allowed_evidence_ids=["E1"],
        )
        rows = verify_claims(
            [AnswerClaim("يجب إجراء فحص كامل للعين يشمل قياس البصر وضغط العين وفحص قاع العين", ["E1"])],
            context,
        )
        self.assertEqual(rows[0].status, "supported")
        self.assertGreaterEqual(rows[0].question_relevance, 0.82)

    def test_h_pylori_compound_claim_is_split_and_supported_core_survives(self) -> None:
        generated = GeneratedAnswer(
            query="ما العلاج المناسب لالتهاب المريء والمعدة؟",
            answer="من الأفضل إجراء اختبار H. pylori لتحديد ما إذا كان السبب عدوى بكتيرية.",
            generation_status="generated",
            claims=[
                AnswerClaim(
                    "من الأفضل إجراء اختبار H. pylori لتحديد ما إذا كان السبب هو عدوى بكتيرية",
                    ["E1"],
                    ["qa1"],
                )
            ],
        )
        claims = extract_claims(generated)
        self.assertEqual(len(claims), 2)
        self.assertIn("H. pylori", claims[0].claim)
        context = EvidenceContextBundle(
            query=generated.query,
            reformulated_query=generated.query,
            primary_intent="treatment_request",
            evidence_items=[
                {
                    "evidence_id": "E1",
                    "evidence": "من الجيد عمل فحص H. pylori واعلامي بالنتيجة",
                    "source_question": "منظار المعدة أظهر التهاب المريء والمعدة، فما العلاج؟",
                    "source_answer": "من الجيد عمل فحص H. pylori واعلامي بالنتيجة",
                    "answer_relevance": 1.0,
                    "relation_ids": [],
                }
            ],
            allowed_evidence_ids=["E1"],
            allowed_qa_ids=["qa1"],
        )
        rows = verify_claims(claims, context)
        self.assertEqual(rows[0].status, "supported")
        self.assertEqual(rows[1].status, "unsupported")

    def test_imaging_paraphrase_matches_conservative_equivalences(self) -> None:
        context = EvidenceContextBundle(
            query="الدوخة والإغماء مستمران، ماذا أفعل؟",
            reformulated_query="الدوخة والإغماء مستمران، ماذا أفعل؟",
            primary_intent="general_medical_advice",
            evidence_items=[
                {
                    "evidence_id": "E1",
                    "evidence": "ننصحك بقياس ضغط الدم وعمل رسم مخ بالكمبيوتر مع اشعة رنين مغناطيسي على المخ",
                    "source_question": "دوخة وإغماء مستمران",
                    "source_answer": "قياس ضغط الدم وعمل رسم مخ بالكمبيوتر مع اشعة رنين مغناطيسي على المخ",
                    "answer_relevance": 0.9,
                    "relation_ids": [],
                }
            ],
            allowed_evidence_ids=["E1"],
        )
        rows = verify_claims(
            [AnswerClaim("ينصح بقياس ضغط الدم وإجراء تصوير بالرنين المغناطيسي أو التصوير المقطعي المحوسب للمخ", ["E1"])],
            context,
        )
        self.assertEqual(rows[0].status, "supported")

    def test_recommendation_cannot_compose_anatomy_across_question_and_answer(self) -> None:
        context = EvidenceContextBundle(
            query="ما علاج التهاب المريء؟",
            reformulated_query="ما علاج التهاب المريء؟",
            primary_intent="treatment_request",
            evidence_items=[
                {
                    "evidence_id": "E1",
                    "evidence": "من الجيد عمل فحص H. pylori",
                    "source_question": "المنظار أظهر التهاب المريء",
                    "source_answer": "يجب معرفة سبب الالتهاب وعمل فحص H. pylori",
                    "answer_relevance": 1.0,
                    "relation_ids": [],
                }
            ],
            allowed_evidence_ids=["E1"],
        )
        rows = verify_claims(
            [AnswerClaim("يجب فحص المريء لاكتشاف سبب الالتهاب", ["E1"])],
            context,
        )
        self.assertEqual(rows[0].status, "unsupported")


if __name__ == "__main__":
    unittest.main()
