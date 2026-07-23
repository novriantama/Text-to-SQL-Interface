"""Integration tests for Database Sandbox Adapter and Query Sandboxing."""

import unittest
import sqlite3
import tempfile
from pathlib import Path
from sqlalchemy import create_engine, text
from src.infrastructure.db.sandbox_executor import SandboxDatabaseAdapter


class TestDBSandbox(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_file = Path(self.temp_dir.name) / "test.db"
        conn = sqlite3.connect(self.db_file)
        conn.execute("CREATE TABLE test_table (id INT, val TEXT);")
        conn.execute("INSERT INTO test_table VALUES (1, 'hello');")
        conn.commit()
        conn.close()

        self.engine = create_engine(f"sqlite:///{self.db_file}")
        self.adapter = SandboxDatabaseAdapter(self.engine)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_sandbox_read_only_execution(self):
        res = self.adapter.execute_read_only("SELECT * FROM test_table")
        self.assertEqual(res.rows_returned, 1)
        self.assertEqual(res.data[0]["val"], "hello")

    def test_sandbox_automatic_rollback_guarantee(self):
        # Test that any execution in sandbox is rolled back
        try:
            self.adapter.execute_read_only("INSERT INTO test_table VALUES (2, 'unauthorized');")
        except Exception:
            pass

        # Verify database still contains only 1 original record
        with self.engine.connect() as conn:
            res = conn.execute(text("SELECT COUNT(*) FROM test_table")).fetchone()
            self.assertEqual(res[0], 1)


if __name__ == "__main__":
    unittest.main()
