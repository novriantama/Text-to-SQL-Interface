"""Unit tests for SQLAlchemySchemaExtractor."""

import unittest
import sqlite3
import tempfile
from pathlib import Path
from sqlalchemy import create_engine
from src.infrastructure.db.schema_extractor import SQLAlchemySchemaExtractor
from src.domain.entities.schema import DatabaseSchema, TableSchema, ColumnSchema


class TestSQLAlchemySchemaExtractor(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_file = Path(self.temp_dir.name) / "test_schema.db"
        
        conn = sqlite3.connect(self.db_file)
        # Create users table with PK, VARCHAR categorical status
        conn.execute("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                username VARCHAR(50) NOT NULL,
                status VARCHAR(20) NOT NULL,
                role VARCHAR(20) NOT NULL
            );
        """)
        # Insert sample rows for categorical value extraction
        conn.execute("INSERT INTO users VALUES (1, 'alice', 'active', 'admin');")
        conn.execute("INSERT INTO users VALUES (2, 'bob', 'inactive', 'user');")
        conn.execute("INSERT INTO users VALUES (3, 'charlie', 'pending', 'user');")

        # Create orders table with Foreign Key
        conn.execute("""
            CREATE TABLE orders (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                amount DECIMAL(10, 2),
                order_status VARCHAR(20),
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
        """)
        conn.execute("INSERT INTO orders VALUES (101, 1, 150.00, 'completed');")
        conn.execute("INSERT INTO orders VALUES (102, 2, 89.50, 'shipped');")
        conn.commit()
        conn.close()

        self.engine = create_engine(f"sqlite:///{self.db_file}")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_extract_schema_structure(self):
        extractor = SQLAlchemySchemaExtractor(self.engine, sample_limit=5, extract_samples=True)
        schema = extractor.extract()

        self.assertIn("users", schema.tables)
        self.assertIn("orders", schema.tables)

        users_table = schema.tables["users"]
        self.assertEqual(len(users_table.columns), 4)

        # Check Primary Key
        id_col = next(c for c in users_table.columns if c.name == "id")
        self.assertTrue(id_col.is_primary_key)

        # Check Categorical Sample Values
        status_col = next(c for c in users_table.columns if c.name == "status")
        self.assertGreaterEqual(len(status_col.sample_values), 3)
        self.assertIn("active", status_col.sample_values)
        self.assertIn("inactive", status_col.sample_values)
        self.assertIn("pending", status_col.sample_values)

        # Check Foreign Key relationship in orders table
        orders_table = schema.tables["orders"]
        user_id_col = next(c for c in orders_table.columns if c.name == "user_id")
        self.assertTrue(user_id_col.is_foreign_key)
        self.assertEqual(user_id_col.foreign_table, "users")
        self.assertEqual(user_id_col.foreign_column, "id")

    def test_prompt_string_formatting(self):
        extractor = SQLAlchemySchemaExtractor(self.engine, sample_limit=5, extract_samples=True)
        schema = extractor.extract()
        prompt_str = schema.to_prompt_str()

        self.assertIn("Table: users", prompt_str)
        self.assertIn("[PRIMARY KEY]", prompt_str)
        self.assertIn("[FK -> users.id]", prompt_str)
        self.assertIn("Sample values:", prompt_str)


if __name__ == "__main__":
    unittest.main()
