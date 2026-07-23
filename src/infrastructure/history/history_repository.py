"""Repository for tracking session query execution history."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import Lock
from src.domain.entities.query import QueryResponse


@dataclass
class QueryHistoryItem:
    """Historical query execution record."""
    session_id: str
    timestamp: str
    question: str
    generated_sql: str
    explanation: str
    confidence_score: float
    guardrails_passed: bool
    rows_returned: int
    execution_time_ms: float
    warnings: list[str] = field(default_factory=list)


class QueryHistoryRepository:
    """Thread-safe session query history repository."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._history: dict[str, list[QueryHistoryItem]] = {}

    def add_entry(self, session_id: str, response: QueryResponse) -> QueryHistoryItem:
        """Stores a QueryResponse object under the specified session_id."""
        with self._lock:
            if session_id not in self._history:
                self._history[session_id] = []

            item = QueryHistoryItem(
                session_id=session_id,
                timestamp=datetime.now(timezone.utc).isoformat(),
                question=response.question,
                generated_sql=response.generated_sql,
                explanation=response.explanation,
                confidence_score=response.confidence.overall_score,
                guardrails_passed=response.guardrails_passed,
                rows_returned=response.results.rows_returned if response.results else 0,
                execution_time_ms=response.results.execution_time_ms if response.results else 0.0,
                warnings=response.warnings or []
            )
            self._history[session_id].append(item)
            return item

    def get_session_history(self, session_id: str = "default_session", limit: int = 50) -> list[QueryHistoryItem]:
        """Retrieves query execution history for a given session."""
        with self._lock:
            items = self._history.get(session_id, [])
            return list(reversed(items))[:limit]

    def clear_session_history(self, session_id: str = "default_session") -> None:
        """Clears stored history for a session."""
        with self._lock:
            if session_id in self._history:
                self._history[session_id] = []
