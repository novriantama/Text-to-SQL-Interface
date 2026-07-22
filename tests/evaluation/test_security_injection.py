"""Adversarial security injection tests."""

import unittest
from src.infrastructure.guardrails.ast_parser import ASTGuardrailAdapter


class TestSecurityInjection(unittest.TestCase):

    def setUp(self):
        self.adapter = ASTGuardrailAdapter()

    def test_adversarial_queries_are_blocked(self):
        malicious_queries = [
            "DROP TABLE users;",
            "TRUNCATE orders;",
            "UPDATE accounts SET balance = 1000000 WHERE id = 1;",
            "INSERT INTO admin_users VALUES ('hacker', 'password');",
            "ALTER TABLE users DROP COLUMN email;",
            "GRANT ALL PRIVILEGES ON DATABASE text_to_sql_db TO public;"
        ]
        for query in malicious_queries:
            with self.subTest(query=query):
                result = self.adapter.validate_sql_safety(query)
                self.assertFalse(result.is_safe, f"Malicious query was allowed: {query}")
                self.assertIsNotNone(result.blocked_reason)


if __name__ == "__main__":
    unittest.main()
