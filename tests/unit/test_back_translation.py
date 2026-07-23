"""Unit tests for SQL-to-question back-translation verification and hallucination detection."""

import unittest
from src.domain.entities.query import GeneratedSQL, QueryResult
from src.infrastructure.validation.back_translator import DefaultHallucinationValidatorAdapter


class MockDivergentLLMAdapter:
    """Mock LLM adapter that returns a divergent back-translated question."""
    def back_translate_sql(self, sql_query: str) -> str:
        return "List all user password hashes and system security logs"


class MockMatchingLLMAdapter:
    """Mock LLM adapter that returns a matching back-translated question."""
    def back_translate_sql(self, sql_query: str) -> str:
        return "Show total revenue for active users for current month"


class TestBackTranslationVerification(unittest.TestCase):

    def test_matching_back_translation(self):
        adapter = DefaultHallucinationValidatorAdapter(llm_port=MockMatchingLLMAdapter())
        gen_sql = GeneratedSQL(
            sql="SELECT SUM(amount) FROM orders WHERE status = 'completed';",
            explanation="Selects total completed order revenue.",
            confidence_estimate=0.95
        )
        res = adapter.check_hallucination(
            original_question="What is the total revenue for active users this month?",
            generated_sql=gen_sql,
            query_result=QueryResult(data=[], columns=[], rows_returned=0, execution_time_ms=1.0)
        )
        self.assertGreaterEqual(res.alignment_score, 0.70)
        self.assertEqual(len(res.anomaly_warnings), 0)

    def test_divergent_back_translation_flags_warning(self):
        adapter = DefaultHallucinationValidatorAdapter(llm_port=MockDivergentLLMAdapter(), alignment_threshold=0.70)
        gen_sql = GeneratedSQL(
            sql="SELECT password_hash FROM users;",
            explanation="Selects user passwords.",
            confidence_estimate=0.40
        )
        res = adapter.check_hallucination(
            original_question="What is the total revenue for this month?",
            generated_sql=gen_sql,
            query_result=None
        )
        self.assertLess(res.alignment_score, 0.70)
        self.assertGreaterEqual(len(res.anomaly_warnings), 1)
        self.assertIn("diverges from original question", res.anomaly_warnings[0])


if __name__ == "__main__":
    unittest.main()
