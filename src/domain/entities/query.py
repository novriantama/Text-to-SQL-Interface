"""Query domain entities representing user inputs, generated SQL, confidence scores, and responses."""

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class QueryInterpretation:
    """Represents a specific candidate interpretation of an ambiguous question."""
    label: str
    description: str
    example_sql: str


@dataclass(frozen=True)
class QueryRequest:
    """Natural language question input from user."""
    question: str
    session_id: str = "default_session"
    user_id: str | None = None


@dataclass(frozen=True)
class GeneratedSQL:
    """Structured response from LLM generation engine."""
    sql: str
    explanation: str
    confidence_estimate: float
    accessed_tables: list[str] = field(default_factory=list)
    accessed_columns: list[str] = field(default_factory=list)
    is_ambiguous: bool = False
    clarification_options: list[QueryInterpretation] = field(default_factory=list)


@dataclass(frozen=True)
class QueryResult:
    """Execution output from database sandbox."""
    data: list[dict[str, Any]]
    columns: list[str]
    rows_returned: int
    execution_time_ms: float
    explain_plan: str | None = None


@dataclass(frozen=True)
class ConfidenceScore:
    """Combined confidence score breakdown based on multi-check signals."""
    overall_score: float
    syntax_validity: float
    back_translation_match: float
    result_sanity_score: float
    multi_query_consensus: float

    def is_high_confidence(self, threshold: float = 0.8) -> bool:
        """Determines if the generated SQL is safe and accurate."""
        return self.overall_score >= threshold


@dataclass
class QueryResponse:
    """Complete output payload delivered back to presentation layer."""
    question: str
    generated_sql: str
    explanation: str
    results: QueryResult | None
    confidence: ConfidenceScore
    guardrails_passed: bool
    warnings: list[str] = field(default_factory=list)
    clarification_needed: bool = False
    clarification_options: list[QueryInterpretation] = field(default_factory=list)
