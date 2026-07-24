"""Use Case: Submit User Feedback Flywheel."""

import json
import re
import time
from pathlib import Path
from src.core.logger import get_logger
from src.application.dtos.query_dto import FeedbackRequestDTO
from src.domain.entities.prompt import FewShotExample
from src.infrastructure.llm.few_shot_repository import FewShotRepository

logger = get_logger(__name__)


class SubmitFeedbackUseCase:
    """Processes user feedback on generated SQL queries to drive the continuous improvement flywheel:
    1. Correct results -> Promoted into dynamic few-shot examples for future prompt generation.
    2. Incorrect results -> Recorded as new regression test cases in the golden evaluation dataset.
    """

    def __init__(self, few_shot_repo: FewShotRepository | None = None, dataset_path: str = "data/golden_dataset.json") -> None:
        self.few_shot_repo = few_shot_repo or FewShotRepository()
        self.dataset_path = Path(dataset_path)

    def execute(self, feedback: FeedbackRequestDTO) -> dict:
        """Stores user feedback, updates dynamic few-shots, or records new eval suite test cases."""
        logger.info(
            f"[FEEDBACK FLYWHEEL] Received feedback for question: '{feedback.question}' | Correct: {feedback.is_correct}"
        )

        target_sql = feedback.suggested_sql if (feedback.suggested_sql and feedback.suggested_sql.strip()) else feedback.generated_sql

        if feedback.is_correct:
            # 1. Flywheel Path A: Convert approved pair to new Few-Shot Example
            tags = [w for w in re.findall(r"\w+", feedback.question.lower()) if len(w) > 3]
            example = FewShotExample(
                question=feedback.question,
                sql=target_sql,
                explanation=feedback.comments or "User verified correct query pair.",
                tags=tags
            )
            self.few_shot_repo.add_example(example)

            return {
                "status": "success",
                "flywheel_action": "few_shot_added",
                "message": "Thank you! Correct query pair added to dynamic few-shot prompt repository to improve future generations."
            }
        else:
            # 2. Flywheel Path B: Convert failing query to new regression test case in eval suite
            new_test_case = {
                "id": f"eval_fb_{int(time.time())}",
                "question": feedback.question,
                "golden_sql": target_sql if (feedback.suggested_sql and feedback.suggested_sql.strip()) else "",
                "failing_generated_sql": feedback.generated_sql,
                "comments": feedback.comments or "User flagged incorrect generation",
                "expected_tables": [],
                "is_ambiguous": False
            }

            self._append_to_eval_dataset(new_test_case)

            return {
                "status": "success",
                "flywheel_action": "eval_test_case_added",
                "message": "Thank you! Incorrect result recorded as a new regression test case in the evaluation suite."
            }

    def _append_to_eval_dataset(self, test_case: dict) -> None:
        """Appends new test case to golden_dataset.json file safely."""
        try:
            entries = []
            if self.dataset_path.exists():
                try:
                    with open(self.dataset_path, "r", encoding="utf-8") as f:
                        entries = json.load(f)
                except Exception:
                    entries = []
            
            entries.append(test_case)
            
            self.dataset_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.dataset_path, "w", encoding="utf-8") as f:
                json.dump(entries, f, indent=2)

            logger.info(f"[FLYWHEEL EVAL ADDED] Saved new test case '{test_case['id']}' to {self.dataset_path}")
        except Exception as err:
            logger.error(f"Error appending test case to eval dataset: {err}")
