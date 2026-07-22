"""Use Case: Evaluation Suite Runner."""

from src.core.logger import get_logger
from src.domain.entities.query import QueryRequest
from src.application.use_cases.process_text_to_sql import ProcessTextToSQLUseCase

logger = get_logger(__name__)


class EvaluateQueriesUseCase:
    """Executes benchmark test suite and calculates execution accuracy and safety block rates."""

    def __init__(self, pipeline: ProcessTextToSQLUseCase) -> None:
        self.pipeline = pipeline

    def run_suite(self, benchmark_cases: list[dict]) -> dict:
        """Runs automated evaluation suite against benchmark cases."""
        total = len(benchmark_cases)
        passed = 0
        blocked_count = 0

        for case in benchmark_cases:
            try:
                res = self.pipeline.execute(QueryRequest(question=case["question"]))
                if res.guardrails_passed and not case.get("should_be_blocked", False):
                    passed += 1
            except Exception as err:
                if case.get("should_be_blocked", False):
                    blocked_count += 1
                logger.warning(f"Benchmark case '{case.get('id')}' failed/blocked: {err}")

        return {
            "total_cases": total,
            "passed_cases": passed,
            "blocked_dangerous_queries": blocked_count,
            "accuracy": (passed / total) if total > 0 else 0.0,
        }
