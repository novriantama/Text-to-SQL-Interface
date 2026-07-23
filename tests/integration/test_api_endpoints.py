"""Integration tests for FastAPI REST API endpoints (/v1/query, /v1/schema, /v1/history)."""

import unittest
from sqlalchemy import text
from fastapi.testclient import TestClient
from src.presentation.api.main import app
from src.infrastructure.db.connection import get_db_engine


class TestAPIEndpoints(unittest.TestCase):

    def setUp(self):
        # Ensure database tables exist for API testing
        engine = get_db_engine()
        with engine.connect() as conn:
            conn.execute(text("CREATE TABLE IF NOT EXISTS orders (id INT, amount DECIMAL);"))
            res = conn.execute(text("SELECT COUNT(*) FROM orders;")).fetchone()
            if res[0] == 0:
                conn.execute(text("INSERT INTO orders VALUES (1, 100.0), (2, 250.0);"))
        
        self.client = TestClient(app)

    def test_health_check_endpoint(self):
        res = self.client.get("/health")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["status"], "ok")

    def test_get_schema_endpoint(self):
        res = self.client.get("/v1/schema")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("tables", data)

    def test_post_query_endpoint(self):
        payload = {
            "question": "Show all orders",
            "session_id": "test_session_123"
        }
        res = self.client.post("/v1/query", json=payload)
        self.assertEqual(res.status_code, 200)

        data = res.json()
        self.assertIn("generated_sql", data)
        self.assertIn("results", data)
        self.assertIn("confidence", data)
        self.assertIn("guardrails_passed", data)
        self.assertTrue(data["guardrails_passed"])

    def test_get_history_endpoint(self):
        session_id = "history_test_session"
        # 1. Post a query first
        res_post = self.client.post("/v1/query", json={"question": "List orders for history test", "session_id": session_id})
        self.assertEqual(res_post.status_code, 200)

        # 2. Fetch history
        res = self.client.get(f"/v1/history?session_id={session_id}")
        self.assertEqual(res.status_code, 200)
        history = res.json()
        self.assertIsInstance(history, list)
        self.assertGreaterEqual(len(history), 1)
        self.assertEqual(history[0]["session_id"], session_id)
        self.assertEqual(history[0]["question"], "List orders for history test")


if __name__ == "__main__":
    unittest.main()
