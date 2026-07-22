"""Validation entities for guardrails and hallucination detection checks."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class GuardrailResult:
    """Result from AST parsing and security guardrail evaluation."""
    is_safe: bool
    blocked_reason: str | None = None
    row_limit_applied: bool = False
    ast_parsed: bool = True
    estimated_cost: float = 0.0


@dataclass(frozen=True)
class HallucinationCheckResult:
    """Result from hallucination validation engines."""
    back_translated_question: str
    alignment_score: float
    sanity_checks_passed: bool
    consensus_matched: bool
    anomaly_warnings: list[str] = field(default_factory=list)
