"""Abstract guardrail port for SQL safety parsing and execution cost estimation."""

from abc import ABC, abstractmethod
from src.domain.entities.validation import GuardrailResult


class GuardrailPort(ABC):
    """Port interface defining safety guardrail validation."""

    @abstractmethod
    def validate_sql_safety(self, sql_query: str, explain_plan: str | None = None) -> GuardrailResult:
        """Analyze SQL query for destructive operations, row limits, subquery depth, and execution cost."""
        pass
