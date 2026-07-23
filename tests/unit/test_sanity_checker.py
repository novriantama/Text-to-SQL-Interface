"""Unit tests for ResultSanityChecker result sanity heuristics."""

import unittest
from datetime import datetime, timedelta, timezone
from src.domain.entities.query import QueryResult
from src.infrastructure.validation.sanity_checker import ResultSanityChecker


class TestResultSanityChecker(unittest.TestCase):

    def setUp(self):
        self.checker = ResultSanityChecker(
            column_null_threshold=0.50,
            extreme_value_threshold=1e12
        )

    def test_clean_dataset_passes_sanity(self):
        result = QueryResult(
            data=[
                {"user_id": 1, "username": "alice", "total_revenue": 150.00, "created_at": "2024-05-10"},
                {"user_id": 2, "username": "bob", "total_revenue": 200.50, "created_at": "2024-05-11"}
            ],
            columns=["user_id", "username", "total_revenue", "created_at"],
            rows_returned=2,
            execution_time_ms=1.5
        )
        passed, warnings = self.checker.check_sanity(result, "Show user revenue")
        self.assertTrue(passed)
        self.assertEqual(len(warnings), 0)

    def test_detects_null_heavy_column_bad_join(self):
        # 3 out of 4 rows NULL in order_status column (75% NULLs)
        result = QueryResult(
            data=[
                {"user_id": 1, "order_status": None},
                {"user_id": 2, "order_status": None},
                {"user_id": 3, "order_status": None},
                {"user_id": 4, "order_status": "completed"}
            ],
            columns=["user_id", "order_status"],
            rows_returned=4,
            execution_time_ms=2.0
        )
        passed, warnings = self.checker.check_sanity(result, "Show order status")
        self.assertFalse(passed)
        self.assertEqual(len(warnings), 1)
        self.assertIn("Column 'order_status' is NULL-heavy", warnings[0])
        self.assertIn("incorrect JOIN condition", warnings[0])

    def test_detects_negative_count_and_aggregates(self):
        result = QueryResult(
            data=[
                {"category": "Electronics", "order_count": -5, "total_amount": -100.0}
            ],
            columns=["category", "order_count", "total_amount"],
            rows_returned=1,
            execution_time_ms=1.0
        )
        passed, warnings = self.checker.check_sanity(result, "Show category counts")
        self.assertFalse(passed)
        self.assertGreaterEqual(len(warnings), 1)
        self.assertTrue(any("Count column 'order_count' contains negative value" in w for w in warnings))

    def test_detects_extreme_magnitude_cartesian_explosion(self):
        result = QueryResult(
            data=[
                {"item": "Widget", "calculated_total": 9e15}
            ],
            columns=["item", "calculated_total"],
            rows_returned=1,
            execution_time_ms=1.0
        )
        passed, warnings = self.checker.check_sanity(result, "Calculate totals")
        self.assertFalse(passed)
        self.assertEqual(len(warnings), 1)
        self.assertIn("unusually large magnitude value", warnings[0])
        self.assertIn("Cartesian product", warnings[0])

    def test_detects_future_dates_and_sentinel_past_dates(self):
        future_dt = (datetime.now(timezone.utc) + timedelta(days=10)).strftime("%Y-%m-%d %H:%M:%S")
        result = QueryResult(
            data=[
                {"id": 1, "created_at": future_dt},
                {"id": 2, "updated_at": "1970-01-01 00:00:00"}
            ],
            columns=["id", "created_at", "updated_at"],
            rows_returned=2,
            execution_time_ms=1.0
        )
        passed, warnings = self.checker.check_sanity(result, "Show timestamps")
        self.assertFalse(passed)
        self.assertGreaterEqual(len(warnings), 2)
        self.assertTrue(any("future date/timestamp" in w for w in warnings))
        self.assertTrue(any("sentinel default date" in w for w in warnings))


if __name__ == "__main__":
    unittest.main()
