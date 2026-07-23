"""Abstract LLM port for structured SQL generation, alternative approach generation, and back-translation."""

from abc import ABC, abstractmethod
from src.domain.entities.schema import DatabaseSchema
from src.domain.entities.query import GeneratedSQL


class LLMPort(ABC):
    """Port interface defining LLM interaction capabilities."""

    @abstractmethod
    def generate_sql(self, question: str, schema_context: DatabaseSchema, few_shots: list[dict] | None = None) -> GeneratedSQL:
        """Generate structured SQL query given question and schema context."""
        pass

    @abstractmethod
    def generate_alternative_sql(self, question: str, schema_context: DatabaseSchema, primary_sql: str) -> GeneratedSQL:
        """Generate an independent alternative SQL approach (e.g. subqueries, CTEs, alternative JOINs) for consensus validation."""
        pass

    @abstractmethod
    def back_translate_sql(self, sql_query: str) -> str:
        """Translate SQL query back to natural language question for validation."""
        pass
