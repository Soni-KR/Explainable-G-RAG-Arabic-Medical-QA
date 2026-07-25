from __future__ import annotations

import unittest

from scripts.run_partial_only_fts_expansion import (
    merge_new_candidates,
    reformulation_drift,
    validate_raw_fts_expression,
)


class PartialOnlyFtsExpansionTests(unittest.TestCase):
    def test_raw_fts_expression_allows_only_quoted_boolean_groups(self) -> None:
        expression = '("asthma" OR "chest allergy") AND ("safe" OR "interaction")'
        self.assertEqual(validate_raw_fts_expression(expression), expression)
        with self.assertRaises(ValueError):
            validate_raw_fts_expression("asthma* OR answer_norm:unsafe")

    def test_reformulation_drift_rejects_ungrounded_medical_substitution(self) -> None:
        row = {
            "original_query": "treatment for glioma",
            "normalized_query": "treatment for glioma",
            "medical_phrase_normalized": "blood tumor",
            "linked_graph_canonical_names": "",
        }
        linked_row = {
            **row,
            "linked_graph_canonical_names": "blood tumor",
        }

        drifted, added = reformulation_drift(row)
        linked_drifted, _ = reformulation_drift(linked_row)

        self.assertTrue(drifted)
        self.assertTrue(added)
        self.assertFalse(linked_drifted)

    def test_merge_excludes_existing_and_deduplicates_across_variants(self) -> None:
        query_row = {
            "original_query": "query",
            "query_group": "group",
            "primary_intent": "test_request",
        }
        shared = {
            "qa_id": "qa_new",
            "source_row_number": 2,
            "question": "new question",
            "answer": "new answer",
            "category": "category",
            "lexical_rank": -2.0,
        }
        existing = {
            **shared,
            "qa_id": "qa_existing",
        }
        candidates, excluded = merge_new_candidates(
            "q1",
            query_row,
            {
                "A": [shared, existing],
                "B": [shared],
                "C": [],
            },
            {"qa_existing"},
            "all_three_variants",
            "",
            "fts_variant_C_full_query",
            [],
            max_new_per_query=10,
        )

        self.assertEqual(excluded, 1)
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0]["matched_variants"], "A|B")
        self.assertEqual(candidates[0]["variant_support_count"], 2)
        self.assertEqual(candidates[0]["expansion_rank"], 1)


if __name__ == "__main__":
    unittest.main()
