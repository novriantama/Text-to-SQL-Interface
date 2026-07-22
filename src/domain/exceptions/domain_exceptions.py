"""Domain exceptions representing business logic violations."""

from src.core.exceptions import BaseAppException


class DomainException(BaseAppException):
    """Base domain exception."""
    pass


class GuardrailViolationException(DomainException):
    """Raised when generated SQL violates safety policies (DDL/DML, depth, cost)."""
    pass


class AmbiguousQueryException(DomainException):
    """Raised when user question maps to multiple valid interpretations."""
    def __init__(self, question: str, interpretations: list[str]) -> None:
        super().__init__(f"Ambiguous query detected for: {question}", details={"interpretations": interpretations})
        self.interpretations = interpretations


class SQLSyntaxException(DomainException):
    """Raised when generated SQL syntax is invalid."""
    pass
