"""Unit tests for ConfidenceEvaluator multi-signal scoring system."""

import unittest
from src.infrastructure.validation.confidence_evaluator import ConfidenceEvaluator


class TestConfidenceEvaluator(unittest.TestCase):

    def setUp(self):
        self.evaluator = ConfidenceEvaluator()

    def test_high_confidence_perfect_signals(self):
        score = self.evaluator.calculate_confidence(
            guardrails_passed=True,
            ast_parsed=True,
            back_translation_alignment=1.0,
            sanity_checks_passed=True,
            sanity_warning_count=0,
            consensus_matched=True,
            accessed_tables=["orders"],
            schema_tables=["orders"]
        )

        self.assertEqual(score.syntax_validity, 1.0)
        self.assertEqual(score.back_translation_match, 1.0)
        self.assertEqual(score.result_sanity_score, 1.0)
        self.assertEqual(score.multi_query_consensus, 1.0)
        self.assertEqual(score.schema_coverage, 1.0)
        self.assertEqual(score.overall_score, 1.0)
        self.assertTrue(score.is_high_confidence())

    def test_low_confidence_divergent_signals(self):
        score = self.evaluator.calculate_confidence(
            guardrails_passed=True,
            ast_parsed=True,
            back_translation_alignment=0.20,
            sanity_checks_passed=False,
            sanity_warning_count=2,
            consensus_matched=False,
            accessed_tables=["orders"],
            schema_tables=["orders", "users", "products"]
        )

        self.assertEqual(score.syntax_validity, 1.0)
        self.assertEqual(score.back_translation_match, 0.20)
        self.assertEqual(score.multi_query_consensus, 0.0)
        self.assertLess(score.overall_score, 0.80)
        self.assertFalse(score.is_high_confidence())

    def test_schema_coverage_calculation(self):
        cov_full = self.evaluator._calculate_schema_coverage(["orders", "users"], ["orders", "users"])
        self.assertEqual(cov_full, 1.0)

        cov_partial = self.evaluator._calculate_schema_coverage(["orders"], ["orders", "users"])
        self.assertEqual(cov_partial, 0.5)


if __name__ == "__main__":
    unittest.main()
