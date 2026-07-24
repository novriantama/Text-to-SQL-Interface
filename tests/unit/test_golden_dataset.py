"""Unit test verifying integrity of the golden evaluation dataset."""

import json
import unittest
from pathlib import Path


class TestGoldenDatasetIntegrity(unittest.TestCase):

    def test_golden_dataset_structure_and_count(self):
        dataset_path = Path("data/golden_dataset.json")
        self.assertTrue(dataset_path.exists(), "data/golden_dataset.json must exist")

        with open(dataset_path, "r", encoding="utf-8") as f:
            dataset = json.load(f)

        self.assertGreaterEqual(len(dataset), 50, "Golden dataset must contain at least 50 test cases")

        categories = set()
        for idx, entry in enumerate(dataset):
            self.assertIn("id", entry, f"Entry at index {idx} missing 'id'")
            self.assertIn("category", entry, f"Entry at index {idx} missing 'category'")
            self.assertIn("question", entry, f"Entry at index {idx} missing 'question'")
            self.assertIn("golden_sql", entry, f"Entry at index {idx} missing 'golden_sql'")
            self.assertIn("expected_tables", entry, f"Entry at index {idx} missing 'expected_tables'")
            self.assertIn("is_ambiguous", entry, f"Entry at index {idx} missing 'is_ambiguous'")
            self.assertIn("should_be_blocked", entry, f"Entry at index {idx} missing 'should_be_blocked'")

            categories.add(entry["category"])

        required_categories = {
            "simple_lookup",
            "multi_table_join",
            "aggregation_group_by",
            "date_range_filter",
            "ambiguous_phrasing",
            "unanswerable_or_blocked"
        }
        self.assertTrue(required_categories.issubset(categories), f"Missing categories: {required_categories - categories}")


if __name__ == "__main__":
    unittest.main()
