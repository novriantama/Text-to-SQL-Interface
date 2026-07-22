"""Abstract validation port for hallucination detection, sanity checks, and multi-query consensus."""

from abc import ABC, abstractmethod
from src.domain.entities.query import QueryResult, GeneratedSQL
from src.domain.entities.validation import HallucinationCheckResult


class ValidationPort(ABC):
    """Port interface defining hallucination validation operations."""

    @abstractmethod
    def check_hallucination(
        self,
        original_question: str,
        generated_sql: GeneratedSQL,
        query_result: QueryResult | None
    ) -> HallucinationCheckResult:
        """Perform back-translation alignment, result sanity, and consensus checks."""
        pass
