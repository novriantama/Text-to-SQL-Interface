"""Unit tests for Feedback Flywheel learning & dataset recording."""

import json
import unittest
from pathlib import Path
from src.application.dtos.query_dto import FeedbackRequestDTO
from src.application.use_cases.submit_feedback import SubmitFeedbackUseCase
from src.infrastructure.llm.few_shot_repository import FewShotRepository


class TestFeedbackFlywheel(unittest.TestCase):

    def setUp(self):
        self.few_shot_repo = FewShotRepository()
        self.test_dataset_path = Path("data/test_golden_dataset.json")
        if self.test_dataset_path.exists():
            self.test_dataset_path.unlink()
        
        self.use_case = SubmitFeedbackUseCase(
            few_shot_repo=self.few_shot_repo,
            dataset_path=str(self.test_dataset_path)
        )

    def tearDown(self):
        if self.test_dataset_path.exists():
            self.test_dataset_path.unlink()

    def test_correct_feedback_promotes_to_few_shot(self):
        dto = FeedbackRequestDTO(
            question="What is the total revenue for completed orders in Q1?",
            generated_sql="SELECT SUM(amount) FROM orders WHERE status = 'completed';",
            is_correct=True,
            comments="Verified correct by user"
        )

        res = self.use_case.execute(dto)
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["flywheel_action"], "few_shot_added")

        # Verify added to few-shot repository
        examples = self.few_shot_repo.get_relevant_examples("completed orders revenue Q1")
        self.assertTrue(any(ex.question == dto.question for ex in examples))

    def test_incorrect_feedback_records_to_eval_dataset(self):
        dto = FeedbackRequestDTO(
            question="Find users who never logged in",
            generated_sql="SELECT * FROM users WHERE active = false;",
            is_correct=False,
            comments="Incorrect filter, should check last_login IS NULL",
            suggested_sql="SELECT * FROM users WHERE last_login IS NULL;"
        )

        res = self.use_case.execute(dto)
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["flywheel_action"], "eval_test_case_added")

        # Verify appended to golden dataset json file
        self.assertTrue(self.test_dataset_path.exists())
        with open(self.test_dataset_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["question"], dto.question)
        self.assertEqual(data[0]["golden_sql"], dto.suggested_sql)


if __name__ == "__main__":
    unittest.main()
