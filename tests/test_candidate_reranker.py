from __future__ import annotations

import unittest

from scripts.train_candidate_reranker import (
    confirmed_rows,
    phrase_features,
    ranking_metrics,
    validate_candidate_rows,
)


def candidate(
    query_id: str,
    candidate_id: str,
    label: str,
    rank: int,
) -> dict[str, str]:
    return {
        "query_id": query_id,
        "query": "low blood pressure",
        "candidate_type": "evidence",
        "candidate_rank": str(rank),
        "candidate_id": candidate_id,
        "candidate_question": "low blood pressure",
        "candidate_answer_or_evidence": "clinical answer",
        "retrieval_channel": "vector",
        "retrieval_score": "0.5",
        "answer_relevance": "0.5",
        "query_concept_coverage": "1.0",
        "query_constraint_coverage": "1.0",
        "entity_identity": "1.0",
        "intent_support": "1.0",
        "source_reliability": "0.9",
        "vector_similarity": "0.8",
        "graph_support": "0.0",
        "anatomy_mismatch": "false",
        "unrelated_condition_mismatch": "false",
        "matched_query_concepts": "pressure",
        "missing_query_concepts": "",
        "relevance_label": label,
        "error_reason": "" if label == "2" else "different clinical scenario",
    }


class CandidateRerankerTests(unittest.TestCase):
    def test_final_file_requires_explicit_provenance(self) -> None:
        rows = [candidate("q1", "c1", "2", 1)]
        fields = list(rows[0])

        unconfirmed, statuses, mode = confirmed_rows(rows, fields, "")
        confirmed, _, confirmed_mode = confirmed_rows(
            rows,
            fields,
            "human_review_v1",
        )

        self.assertEqual(unconfirmed, [])
        self.assertEqual(statuses, {"missing_provenance": 1})
        self.assertEqual(mode, "missing_provenance")
        self.assertEqual(confirmed[0]["annotator_id"], "human_review_v1")
        self.assertEqual(confirmed_mode, "explicit_cli_confirmation")

    def test_validation_rejects_duplicate_candidate_keys(self) -> None:
        rows = [
            candidate("q1", "c1", "2", 1),
            candidate("q1", "c1", "1", 2),
        ]
        with self.assertRaises(ValueError):
            validate_candidate_rows(rows, list(rows[0]))

    def test_phrase_features_reward_complete_phrase_coverage(self) -> None:
        complete = candidate("q1", "c1", "2", 1)
        incomplete = {
            **complete,
            "candidate_question": "blood test",
            "candidate_answer_or_evidence": "pressure was not discussed",
        }

        complete_features = phrase_features(
            complete,
            ["low blood pressure"],
        )
        incomplete_features = phrase_features(
            incomplete,
            ["low blood pressure"],
        )

        self.assertEqual(complete_features[-1], 1.0)
        self.assertEqual(incomplete_features[-1], 0.0)
        self.assertGreater(complete_features[2], incomplete_features[2])

    def test_ranking_metrics_reward_direct_candidate_at_rank_one(self) -> None:
        rows = [
            candidate("q1", "c1", "0", 1),
            candidate("q1", "c2", "2", 2),
        ]

        weak = ranking_metrics(rows, [1.0, 0.0])
        strong = ranking_metrics(rows, [0.0, 1.0])

        self.assertEqual(weak["direct_at_rank_1_count"], 0)
        self.assertEqual(strong["direct_at_rank_1_count"], 1)
        self.assertGreater(strong["ndcg_at_5_all_queries"], weak["ndcg_at_5_all_queries"])


if __name__ == "__main__":
    unittest.main()
