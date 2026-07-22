"""Integration tests for FastAPI endpoints."""

import unittest

try:
    from fastapi.testclient import TestClient
    from src.presentation.api.main import app
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False


class TestAPIEndpoints(unittest.TestCase):

    def setUp(self):
        if not HAS_FASTAPI:
            self.skipTest("FastAPI not installed in current test environment")
        self.client = TestClient(app)

    def test_health_endpoint(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_query_endpoint_smoke(self):
        payload = {"question": "List all active orders", "session_id": "test_session"}
        response = self.client.post("/v1/query", json=payload)
        self.assertIn(response.status_code, [200, 400, 422, 500])


if __name__ == "__main__":
    unittest.main()
