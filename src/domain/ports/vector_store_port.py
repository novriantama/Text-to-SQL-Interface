"""Abstract vector store port for semantic schema table selection."""

from abc import ABC, abstractmethod
from src.domain.entities.schema import DatabaseSchema


class VectorStorePort(ABC):
    """Port interface defining vector similarity search for schemas."""

    @abstractmethod
    def index_schema(self, schema: DatabaseSchema) -> None:
        """Store table schema representations into vector index."""
        pass

    @abstractmethod
    def filter_schema(self, question: str, full_schema: DatabaseSchema, threshold: float = 0.35) -> DatabaseSchema:
        """Filter schema to relevant tables above similarity threshold."""
        pass
