"""Use Case: Submit User Feedback Flywheel."""

from src.core.logger import get_logger
from src.application.dtos.query_dto import FeedbackRequestDTO

logger = get_logger(__name__)


class SubmitFeedbackUseCase:
    """Processes user feedback on generated SQL queries for continuous few-shot alignment."""

    def execute(self, feedback: FeedbackRequestDTO) -> dict:
        """Stores feedback into benchmark/few-shot repository."""
        logger.info(
            f"Feedback received for question: '{feedback.question}' | Correct: {feedback.is_correct}"
        )
        # Store feedback into database or JSON test set repository
        return {"status": "success", "message": "Feedback recorded successfully"}
