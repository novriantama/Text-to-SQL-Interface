"""Abstract database port for schema extraction and query execution in read-only sandbox."""

from abc import ABC, abstractmethod
from src.domain.entities.schema import DatabaseSchema
from src.domain.entities.query import QueryResult


class DatabasePort(ABC):
    """Port interface defining database operations."""

    @abstractmethod
    def extract_schema(self) -> DatabaseSchema:
        """Introspect database schema and return structured metadata."""
        pass

    @abstractmethod
    def execute_read_only(self, sql_query: str) -> QueryResult:
        """Execute SELECT query in a read-only transaction sandbox."""
        pass

    @abstractmethod
    def get_explain_plan(self, sql_query: str) -> str:
        """Get database EXPLAIN execution plan."""
        pass
