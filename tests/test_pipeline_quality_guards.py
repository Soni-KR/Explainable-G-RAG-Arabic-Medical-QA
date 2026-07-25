from __future__ import annotations

import unittest
from dataclasses import replace

from src.config import AppConfig, RetrievalConfig
from src.evidence_policy import source_reliability_prior
from src.models import (
    AnswerClaim,
    ClaimVerification,
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
from src.step09_hybrid_retrieval import (
    anatomy_terms,
    medical_identity_similarity,
    score_relations,
    select_relevance_phrases,
    seed_scores,
    semantic_qa_fallback_eligible,
)
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
    def test_relevance_phrases_prefer_conditions_and_symptoms(self) -> None:
        phrases = [
            ExtractedMedicalPhrase("الدواء", "الدواء", "Treatment", "corrected_query", 0.9),
            ExtractedMedicalPhrase("فحص الدم", "فحص الدم", "Test", "corrected_query", 0.9),
            ExtractedMedicalPhrase("انخفاض الضغط", "انخفاض الضغط", "DiseaseCondition", "corrected_query", 0.9),
            ExtractedMedicalPhrase("الدوخة", "الدوخة", "Symptom", "corrected_query", 0.9),
        ]

        selected = select_relevance_phrases(phrases, "diagnosis_request")

        self.assertEqual(selected, ["انخفاض الضغط", "الدوخة"])

    def test_source_reliability_policy_includes_heldout_safe_qa(self) -> None:
        self.assertEqual(source_reliability_prior("ahd_heldout_safe_corpus"), 0.95)
        self.assertEqual(source_reliability_prior("mention_evidence"), 0.55)

    def test_semantic_fallback_is_only_eligible_after_empty_medical_context(self) -> None:
        bundle = HybridRetrievalBundle(
            query="ما علاج الربو؟",
            normalized_query="ما علاج الربو؟",
            reformulated_query="ما علاج الربو؟",
            plan=plan(primary_ids=["asthma"]),
        )
        self.assertFalse(
            semantic_qa_fallback_eligible(
                bundle,
                context_has_evidence=True,
                config=AppConfig(),
            )
        )
        self.assertTrue(
            semantic_qa_fallback_eligible(
                bundle,
                context_has_evidence=False,
                config=AppConfig(),
            )
        )

    def test_verifier_does_not_mix_features_across_citations(self) -> None:
        claim = AnswerClaim(
            "asthma inhalers reduce airway symptoms",
            ["E1", "E2"],
        )
        context = EvidenceContextBundle(
            query="kidney stone management",
            reformulated_query="kidney stone management",
            evidence_items=[
                {
                    "evidence_id": "E1",
                    "evidence": "asthma inhalers reduce airway symptoms",
                    "source_answer": "asthma inhalers reduce airway symptoms",
                    "answer_relevance": 0.05,
                    "entity_identity": 0.05,
                    "vector_similarity": 0.05,
                    "relation_ids": [],
                },
                {
                    "evidence_id": "E2",
                    "evidence": "kidney stone management requires clinical assessment",
                    "source_answer": "kidney stone management requires clinical assessment",
                    "answer_relevance": 0.95,
                    "entity_identity": 0.95,
                    "vector_similarity": 0.95,
                    "relation_ids": [],
                },
            ],
            allowed_evidence_ids=["E1", "E2"],
        )
        result = verify_claims([claim], context)[0]
        self.assertEqual(result.status, "unsupported")
        self.assertEqual(result.valid_citations, [])

    def test_split_claim_keeps_only_its_supporting_citation(self) -> None:
        context = EvidenceContextBundle(
            query="asthma and anemia guidance",
            reformulated_query="asthma and anemia guidance",
            evidence_items=[
                {
                    "evidence_id": "E1",
                    "evidence": "an inhaler treats asthma",
                    "source_answer": "an inhaler treats asthma",
                    "answer_relevance": 0.9,
                    "relation_ids": [],
                },
                {
                    "evidence_id": "E2",
                    "evidence": "iron treats iron deficiency anemia",
                    "source_answer": "iron treats iron deficiency anemia",
                    "answer_relevance": 0.9,
                    "relation_ids": [],
                },
            ],
            allowed_evidence_ids=["E1", "E2"],
        )
        asthma = verify_claims(
            [AnswerClaim("an inhaler treats asthma", ["E1", "E2"])],
            context,
        )[0]
        anemia = verify_claims(
            [AnswerClaim("iron treats iron deficiency anemia", ["E1", "E2"])],
            context,
        )[0]
        self.assertEqual(asthma.status, "supported")
        self.assertEqual(asthma.valid_citations, ["E1"])
        self.assertEqual(anemia.status, "supported")
        self.assertEqual(anemia.valid_citations, ["E2"])

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

    def test_context_accepts_a_high_confidence_vector_paraphrase(self) -> None:
        semantic_qa = RetrievedEvidence(
            evidence_id="qa::semantic",
            source_id="semantic",
            qa_id="semantic",
            text="persistent cough management",
            question="guidance for a respiratory complaint",
            score=0.92,
            metadata={
                "retrieval_channel": "vector",
                "vector_similarity": 0.92,
            },
        )
        general_plan = replace(
            plan(),
            primary_intent="general_medical_advice",
            preferred_relation_types=[],
        )
        subgraph = rerank_subgraph(
            HybridRetrievalBundle(
                query="help for a cough",
                normalized_query="help for a cough",
                reformulated_query="help for a cough",
                plan=general_plan,
                evidence=[semantic_qa],
            ),
            config=AppConfig(),
        )
        context = build_evidence_context(subgraph, "help for a cough", config=AppConfig())
        self.assertEqual(len(context.evidence_items), 1)
        self.assertEqual(context.evidence_items[0]["vector_similarity"], 0.92)

    def test_exact_original_question_survives_a_different_reformulation(self) -> None:
        original = "هل البخاخ ذو القرص علاجي أم وقائي؟"
        reformulated = "ما تصنيف هذا الجهاز الدوائي؟"
        exact = RetrievedEvidence(
            evidence_id="qa::diskhaler",
            source_id="diskhaler",
            qa_id="diskhaler",
            text="يستخدم حسب نوع البخاخ ووصفة الطبيب",
            question=original,
            score=0.94,
            metadata={"vector_similarity": 0.94, "retrieval_channel": "vector"},
        )
        exact_plan = replace(
            plan(),
            original_query=original,
            corrected_query=original,
            reformulated_query=reformulated,
        )
        subgraph = rerank_subgraph(
            HybridRetrievalBundle(
                query=original,
                normalized_query=original,
                reformulated_query=reformulated,
                plan=exact_plan,
                evidence=[exact],
            ),
            config=AppConfig(),
        )
        self.assertTrue(subgraph.evidence[0].metadata["direct_question_anchor"])
        context = build_evidence_context(subgraph, reformulated, config=AppConfig())
        self.assertEqual(context.evidence_items[0]["qa_id"], "diskhaler")
        self.assertEqual(context.evidence_items[0]["vector_similarity"], 0.94)

    def test_context_does_not_force_a_weaker_graph_item(self) -> None:
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
            text="معلومة عامة عن دواء",
            answer="لا يربط المصدر الدواء بالحالة المطلوبة",
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
        self.assertTrue(context.evidence_items)
        self.assertFalse(any(item["relation_ids"] for item in context.evidence_items))
        self.assertEqual(context.graph_facts, [])

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

    def test_structured_limitation_is_not_treated_as_a_factual_claim(self) -> None:
        generated = GeneratedAnswer(
            query="ما علاج الربو؟",
            answer="لا توجد أدلة كافية في الرسم الطبي للإجابة بثقة.",
            generation_status="generated",
            claims=[AnswerClaim("لا توجد أدلة كافية في الرسم الطبي للإجابة بثقة.", ["E1"])],
        )
        self.assertEqual(extract_claims(generated), [])

    def test_meta_evidence_limitation_is_not_a_factual_claim(self) -> None:
        generated = GeneratedAnswer(
            query="ما علاج الربو؟",
            answer="لا توجد معلومات كافية في الأدلة المرفقة للإجابة.",
            generation_status="generated",
            claims=[AnswerClaim("لا توجد معلومات كافية في الأدلة المرفقة للإجابة.")],
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

    def test_interrogative_ma_in_source_question_is_not_negation(self) -> None:
        context = EvidenceContextBundle(
            query="ما علاج انخفاض البروجستيرون؟",
            reformulated_query="ما علاج انخفاض البروجستيرون؟",
            primary_intent="treatment_request",
            evidence_items=[
                {
                    "evidence_id": "E1",
                    "evidence": "وقف التدخين من الوسائل المتبعة لعلاج انخفاض البروجستيرون",
                    "source_question": "ما علاج انخفاض البروجستيرون؟",
                    "source_answer": "وقف التدخين من الوسائل المتبعة لعلاج انخفاض البروجستيرون",
                    "answer_relevance": 0.95,
                    "intent_support": 1.0,
                    "relation_ids": [],
                }
            ],
            allowed_evidence_ids=["E1"],
        )
        rows = verify_claims(
            [AnswerClaim("الإقلاع عن التدخين يساعد في علاج انخفاض البروجستيرون", ["E1"])],
            context,
        )
        self.assertEqual(rows[0].status, "supported")

    def test_source_question_alone_cannot_support_a_factual_claim(self) -> None:
        context = EvidenceContextBundle(
            query="هل الربو يسبب الحمى؟",
            reformulated_query="هل الربو يسبب الحمى؟",
            primary_intent="cause_request",
            evidence_items=[
                {
                    "evidence_id": "E1",
                    "evidence": "ينبغي مراجعة الطبيب لتقييم الحالة",
                    "source_question": "هل الربو يسبب الحمى؟",
                    "source_answer": "ينبغي مراجعة الطبيب لتقييم الحالة",
                    "answer_relevance": 0.9,
                    "intent_support": 1.0,
                    "relation_ids": [],
                }
            ],
            allowed_evidence_ids=["E1"],
        )
        rows = verify_claims([AnswerClaim("الربو يسبب الحمى", ["E1"])], context)
        self.assertEqual(rows[0].status, "unsupported")

    def test_recommendation_paraphrase_accepts_explicit_action_evidence(self) -> None:
        context = EvidenceContextBundle(
            query="ما علاج حمو الفم؟",
            reformulated_query="ما علاج حمو الفم؟",
            primary_intent="treatment_request",
            evidence_items=[
                {
                    "evidence_id": "E1",
                    "evidence": "استعمال غسولات فموية طبية والمضمضة بالماء الدافئ والملح",
                    "source_question": "",
                    "source_answer": "استعمال غسولات فموية طبية والمضمضة بالماء الدافئ والملح",
                    "answer_relevance": 0.9,
                    "intent_support": 1.0,
                    "relation_ids": [],
                }
            ],
            allowed_evidence_ids=["E1"],
        )
        rows = verify_claims(
            [AnswerClaim("ينصح باستعمال غسولات فموية والمضمضة بالماء الدافئ والملح", ["E1"])],
            context,
        )
        self.assertEqual(rows[0].status, "supported")

    def test_faithfully_cited_wrong_clinical_topic_is_rejected(self) -> None:
        context = EvidenceContextBundle(
            query="ما الفحوصات المطلوبة للدوخة والإغماء؟",
            reformulated_query="ما الفحوصات المطلوبة للدوخة والإغماء؟",
            primary_intent="test_request",
            evidence_items=[
                {
                    "evidence_id": "E1",
                    "evidence": "ينصح بإجراء منظار للمعدة لتقييم آلام البطن",
                    "source_question": "ما فحوصات ألم المعدة؟",
                    "source_answer": "إجراء منظار للمعدة",
                    "answer_relevance": 0.9,
                    "query_concept_coverage": 0.0,
                    "intent_support": 1.0,
                    "relation_ids": [],
                }
            ],
            allowed_evidence_ids=["E1"],
        )
        rows = verify_claims(
            [AnswerClaim("ينصح بإجراء منظار للمعدة لتقييم آلام البطن", ["E1"])],
            context,
        )
        self.assertEqual(rows[0].status, "unsupported")
        self.assertIn("claim_query_concept_mismatch", rows[0].failed_checks)

    def test_answerability_requires_query_coverage_not_only_supported_claims(self) -> None:
        claim = AnswerClaim("ينصح بتقييم الدوخة", ["E1"])
        verification = ClaimVerification(
            claim=claim,
            status="supported",
            support_score=1.0,
            question_relevance=1.0,
            query_concept_coverage=1 / 3,
            valid_citations=["E1"],
        )
        context = EvidenceContextBundle(
            query="دوخة وإغماء وسعال",
            reformulated_query="دوخة وإغماء وسعال",
        )
        mitigated = mitigate_hallucinations(
            GeneratedAnswer(query=context.query, answer=claim.claim, claims=[claim]),
            [verification],
            context=context,
        )
        self.assertEqual(mitigated.answerability, "supported_but_incomplete")
        self.assertLess(mitigated.query_coverage, 0.5)
        self.assertTrue(mitigated.missing_query_concepts)

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

    def test_dizziness_does_not_match_head_pain_by_fuzzy_spelling(self) -> None:
        dizziness = "دوخة وإغماء بعد تحاليل طبيعية"
        head_pain = "ألم مستمر في الرأس من الخلف"
        self.assertLess(medical_identity_similarity(dizziness, head_pain), 0.50)

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

    def test_high_trust_context_promotes_a_weak_lexical_paraphrase(self) -> None:
        context = EvidenceContextBundle(
            query="ما الفحوصات المطلوبة للدوخة والإغماء؟",
            reformulated_query="ما الفحوصات المطلوبة للدوخة والإغماء؟",
            primary_intent="test_request",
            evidence_items=[
                {
                    "evidence_id": "E1",
                    "evidence": "مبدئيا ننصحك بقياس ضغط الدم وعمل رسم مخ بالكمبيوتر",
                    "source_question": "دوخة وإغماء مستمران",
                    "source_answer": "قياس ضغط الدم وعمل رسم مخ بالكمبيوتر",
                    "answer_relevance": 0.91,
                    "entity_identity": 0.83,
                    "intent_support": 1.0,
                    "vector_similarity": 0.92,
                    "relation_ids": [],
                }
            ],
            allowed_evidence_ids=["E1"],
        )
        rows = verify_claims(
            [AnswerClaim("قياس ضغط الدم ضروري لتقييم الدوخة والإغماء", ["E1"])],
            context,
        )
        self.assertEqual(rows[0].status, "supported")

    def test_low_identity_context_does_not_promote_a_weak_paraphrase(self) -> None:
        context = EvidenceContextBundle(
            query="ما الفحوصات المطلوبة للكبد؟",
            reformulated_query="ما الفحوصات المطلوبة للكبد؟",
            primary_intent="test_request",
            evidence_items=[
                {
                    "evidence_id": "E1",
                    "evidence": "صورة الدم من الفحوصات المتاحة",
                    "source_question": "ما فحوصات الدم؟",
                    "source_answer": "صورة الدم",
                    "answer_relevance": 0.90,
                    "entity_identity": 0.05,
                    "intent_support": 1.0,
                    "vector_similarity": 0.92,
                    "relation_ids": [],
                }
            ],
            allowed_evidence_ids=["E1"],
        )
        rows = verify_claims(
            [AnswerClaim("فحص صورة الدم يكشف الاضطرابات المرتبطة بالكبد", ["E1"])],
            context,
        )
        self.assertNotEqual(rows[0].status, "supported")

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
