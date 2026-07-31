from __future__ import annotations

import unittest
from dataclasses import replace

from src.config import AppConfig
from src.models import (
    EvidenceContextBundle,
    HybridRetrievalBundle,
    RetrievalPlanResult,
    RetrievedEvidence,
)
from src.step09e_conditional_cross_encoder_rescue import (
    apply_conditional_cross_encoder_rescue,
    rerank_candidates,
    rescue_eligible,
    resolve_local_checkpoint,
)
from src.step10_rerank_subgraph import rerank_subgraph


class FakeCrossEncoder:
    def __init__(self, scores: list[float]) -> None:
        self.scores = scores
        self.calls = 0

    def predict(
        self,
        sentences: list[list[str]],
        *,
        batch_size: int,
        show_progress_bar: bool,
    ) -> list[float]:
        self.calls += 1
        self.last_sentences = sentences
        self.last_batch_size = batch_size
        self.last_show_progress_bar = show_progress_bar
        return self.scores


class ConditionalCrossEncoderRescueTests(unittest.TestCase):
    def make_config(self, enabled: bool = True) -> AppConfig:
        base = AppConfig()
        return replace(
            base,
            qa_corpus=replace(
                base.qa_corpus,
                cross_encoder_rescue_enabled=enabled,
                cross_encoder_candidate_k=10,
                cross_encoder_batch_size=4,
                cross_encoder_weight=0.35,
                cross_encoder_min_score=0.55,
            ),
        )

    def make_bundle(
        self,
        evidence: list[RetrievedEvidence] | None = None,
    ) -> HybridRetrievalBundle:
        plan = RetrievalPlanResult(
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
            primary_entity_ids=["entity-asthma"],
        )
        return HybridRetrievalBundle(
            query="ما علاج الربو؟",
            normalized_query="ما علاج الربو?",
            reformulated_query="ما علاج الربو؟",
            plan=plan,
            query_medical_phrases=["الربو"],
            evidence=evidence or [],
        )

    def test_disabled_rescue_never_runs(self) -> None:
        eligible, reason = rescue_eligible(
            self.make_bundle(),
            EvidenceContextBundle(
                query="ما علاج الربو؟",
                reformulated_query="ما علاج الربو؟",
            ),
            self.make_config(enabled=False),
        )
        self.assertFalse(eligible)
        self.assertEqual(reason, "disabled")

    def test_strong_direct_context_is_not_rescored(self) -> None:
        context = EvidenceContextBundle(
            query="ما علاج الربو؟",
            reformulated_query="ما علاج الربو؟",
            evidence_items=[
                {
                    "evidence_id": "E1",
                    "answer_relevance": 0.90,
                    "intent_support": 1.0,
                    "entity_identity": 1.0,
                }
            ],
        )
        eligible, reason = rescue_eligible(
            self.make_bundle(),
            context,
            self.make_config(),
        )
        self.assertFalse(eligible)
        self.assertEqual(reason, "strong_context_already_available")

    def test_empty_identifiable_context_is_eligible(self) -> None:
        eligible, reason = rescue_eligible(
            self.make_bundle(),
            EvidenceContextBundle(
                query="ما علاج الربو؟",
                reformulated_query="ما علاج الربو؟",
            ),
            self.make_config(),
        )
        self.assertTrue(eligible)
        self.assertEqual(reason, "empty_context")

    def test_reranking_preserves_ids_and_records_scores(self) -> None:
        candidates = [
            RetrievedEvidence(
                evidence_id="qa::1",
                source_id="qa1",
                qa_id="qa1",
                text="تستخدم موسعات الشعب لعلاج الربو.",
                question="ما علاج الربو؟",
                answer="تستخدم موسعات الشعب لعلاج الربو.",
                source_quality="ahd_heldout_safe_corpus",
                score=0.40,
            ),
            RetrievedEvidence(
                evidence_id="qa::2",
                source_id="qa2",
                qa_id="qa2",
                text="علاج فقر الدم يعتمد على السبب.",
                question="ما علاج فقر الدم؟",
                answer="علاج فقر الدم يعتمد على السبب.",
                source_quality="ahd_heldout_safe_corpus",
                score=0.70,
            ),
        ]
        model = FakeCrossEncoder([0.95, 0.10])
        rows = rerank_candidates(
            self.make_bundle(candidates),
            candidates,
            model,
            self.make_config(),
        )
        self.assertEqual([row.evidence_id for row in rows], ["qa::1", "qa::2"])
        self.assertEqual(rows[0].qa_id, "qa1")
        self.assertEqual(rows[0].metadata["cross_encoder_score"], 0.95)
        self.assertEqual(rows[0].metadata["pre_cross_encoder_score"], 0.40)
        self.assertEqual(model.calls, 1)

    def test_step10_uses_cross_score_only_after_hard_constraints(self) -> None:
        good = RetrievedEvidence(
            evidence_id="qa::1",
            source_id="qa1",
            qa_id="qa1",
            text="تستخدم بخاخات موسعة للشعب في علاج الربو.",
            question="ما علاج الربو؟",
            answer="تستخدم بخاخات موسعة للشعب في علاج الربو.",
            source_quality="ahd_heldout_safe_corpus",
            score=0.30,
            metadata={
                "retrieval_channel": "fts_qa",
                "cross_encoder_rescue": True,
                "cross_encoder_score": 0.95,
            },
        )
        wrong_anatomy = RetrievedEvidence(
            evidence_id="qa::2",
            source_id="qa2",
            qa_id="qa2",
            text="ينصح بمنظار المعدة لعلاج ألم البطن.",
            question="ما علاج ألم المعدة؟",
            answer="ينصح بمنظار المعدة لعلاج ألم البطن.",
            source_quality="ahd_heldout_safe_corpus",
            score=0.60,
            metadata={
                "retrieval_channel": "fts_qa",
                "cross_encoder_rescue": True,
                "cross_encoder_score": 0.99,
            },
        )
        bundle = self.make_bundle([good, wrong_anatomy])
        reranked = rerank_subgraph(bundle, config=self.make_config())
        by_id = {row.evidence_id: row for row in reranked.evidence}
        self.assertTrue(by_id["qa::1"].metadata["cross_encoder_support"])
        self.assertFalse(
            by_id["qa::2"].metadata["cross_encoder_support"]
        )

    def test_missing_checkpoint_fails_closed_without_model_call(self) -> None:
        config = self.make_config()
        config = replace(
            config,
            qa_corpus=replace(
                config.qa_corpus,
                cross_encoder_model="missing/local-cross-encoder",
            ),
        )
        original = self.make_bundle(
            [
                RetrievedEvidence(
                    evidence_id="qa::1",
                    source_id="qa1",
                    qa_id="qa1",
                    text="دليل",
                )
            ]
        )
        # The top-level function may discover no lexical rows in a test
        # environment, so checkpoint resolution is tested directly as well.
        with self.assertRaises(FileNotFoundError):
            resolve_local_checkpoint(
                config.qa_corpus.cross_encoder_model
            )
        rescued, audit, model = apply_conditional_cross_encoder_rescue(
            original,
            EvidenceContextBundle(
                query="ما علاج الربو؟",
                reformulated_query="ما علاج الربو؟",
            ),
            config,
        )
        self.assertEqual(rescued.evidence, original.evidence)
        self.assertEqual(audit["status"], "unavailable")
        self.assertIsNone(model)


if __name__ == "__main__":
    unittest.main()
