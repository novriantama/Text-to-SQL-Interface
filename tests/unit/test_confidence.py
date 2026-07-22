"""Unit tests for Confidence Score calculation."""

import unittest
from src.domain.entities.query import ConfidenceScore


class TestConfidenceScore(unittest.TestCase):

    def test_confidence_score_calculation(self):
        score = ConfidenceScore(
            overall_score=0.95,
            syntax_validity=1.0,
            back_translation_match=0.9,
            result_sanity_score=1.0,
            multi_query_consensus=0.9
        )
        self.assertTrue(score.is_high_confidence(threshold=0.8))
        self.assertFalse(score.is_high_confidence(threshold=0.98))


if __name__ == "__main__":
    unittest.main()
