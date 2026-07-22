"""Prompt domain entities for few-shot examples and business glossary definitions."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class FewShotExample:
    """Represents a question-to-SQL example pair for in-context LLM learning."""
    question: str
    sql: str
    explanation: str | None = None
    tags: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class BusinessTerm:
    """Represents a business domain term or metric glossary definition."""
    term: str
    definition: str
    sql_expression: str | None = None
