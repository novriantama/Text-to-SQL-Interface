"""Evaluation test runner for Golden Benchmark Dataset."""

import unittest
import json
from pathlib import Path


class TestGoldenDataset(unittest.TestCase):

    def test_golden_dataset_structure(self):
        dataset_path = Path("data/golden_dataset.json")
        self.assertTrue(dataset_path.exists(), "Golden dataset file does not exist")

        with open(dataset_path, "r") as f:
            cases = json.load(f)

        self.assertGreater(len(cases), 0)
        for case in cases:
            self.assertIn("id", case)
            self.assertIn("question", case)
            self.assertIn("expected_tables", case)


if __name__ == "__main__":
    unittest.main()
