"""Unit tests for EmbeddingSchemaRetriever and relevance schema filtering."""

import unittest
from src.domain.entities.schema import DatabaseSchema, TableSchema, ColumnSchema
from src.infrastructure.vector_store.schema_retriever import EmbeddingSchemaRetriever


class TestEmbeddingSchemaRetriever(unittest.TestCase):

    def setUp(self):
        self.retriever = EmbeddingSchemaRetriever()
        self.schema = DatabaseSchema(
            tables={
                "users": TableSchema(
                    name="users",
                    columns=[
                        ColumnSchema(name="id", data_type="INTEGER", is_primary_key=True),
                        ColumnSchema(name="username", data_type="VARCHAR"),
                        ColumnSchema(name="email", data_type="VARCHAR")
                    ],
                    description="User account profiles and credentials"
                ),
                "orders": TableSchema(
                    name="orders",
                    columns=[
                        ColumnSchema(name="id", data_type="INTEGER", is_primary_key=True),
                        ColumnSchema(name="user_id", data_type="INTEGER", is_foreign_key=True, foreign_table="users", foreign_column="id"),
                        ColumnSchema(name="amount", data_type="NUMERIC"),
                        ColumnSchema(name="status", data_type="VARCHAR", sample_values=["completed"])
                    ],
                    description="Customer transaction purchase orders"
                ),
                "audit_logs": TableSchema(
                    name="audit_logs",
                    columns=[
                        ColumnSchema(name="id", data_type="INTEGER", is_primary_key=True),
                        ColumnSchema(name="action", data_type="VARCHAR"),
                        ColumnSchema(name="timestamp", data_type="TIMESTAMP")
                    ],
                    description="System security event audit log entries"
                )
            }
        )

    def test_indexing(self):
        self.retriever.index_schema(self.schema)
        self.assertEqual(len(self.retriever._table_vectors), 3)
        self.assertIn("users", self.retriever._table_vectors)

    def test_schema_filtering_relevance(self):
        # Query specifically about transaction orders
        filtered = self.retriever.filter_schema("Show purchase orders for customer", self.schema, threshold=0.1)
        self.assertIn("orders", filtered.tables)
        # Verify foreign key graph expansion included connected users table
        self.assertIn("users", filtered.tables)

    def test_fallback_top_table(self):
        # High threshold should still return top relevant table fallback
        filtered = self.retriever.filter_schema("Show audit log events", self.schema, threshold=0.99)
        self.assertGreaterEqual(len(filtered.tables), 1)


if __name__ == "__main__":
    unittest.main()
