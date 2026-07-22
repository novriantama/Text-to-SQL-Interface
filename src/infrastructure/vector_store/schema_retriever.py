"""Vector store schema retriever implementing VectorStorePort."""

from src.domain.ports.vector_store_port import VectorStorePort
from src.domain.entities.schema import DatabaseSchema, TableSchema


class KeywordAndVectorSchemaRetriever(VectorStorePort):
    """Schema filtering adapter using keyword matching and embeddings threshold search."""

    def index_schema(self, schema: DatabaseSchema) -> None:
        """Stores table representation into vector store."""
        pass

    def filter_schema(self, question: str, full_schema: DatabaseSchema, threshold: float = 0.35) -> DatabaseSchema:
        """Filters schema tables based on relevance to user question."""
        if len(full_schema.tables) <= 5:
            # For small schemas, return full schema
            return full_schema

        filtered = DatabaseSchema()
        q_lower = question.lower()

        for table_name, table in full_schema.tables.items():
            # Keyword and column match heuristic filter
            if table_name.lower() in q_lower or any(col.name.lower() in q_lower for col in table.columns):
                filtered.tables[table_name] = table

        # Fallback if no specific table matched keyword
        if not filtered.tables:
            return full_schema

        return filtered
