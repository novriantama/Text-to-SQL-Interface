"""Unit tests for AST Guardrails."""

import unittest
from src.infrastructure.guardrails.ast_parser import ASTGuardrailAdapter


class TestASTGuardrail(unittest.TestCase):

    def setUp(self):
        self.guardrail_adapter = ASTGuardrailAdapter()

    def test_guardrails_blocks_ddl(self):
        sql = "DROP TABLE users;"
        result = self.guardrail_adapter.validate_sql_safety(sql)
        self.assertFalse(result.is_safe)
        self.assertIn("Forbidden DDL/DML", result.blocked_reason)

    def test_guardrails_blocks_dml(self):
        sql = "DELETE FROM orders WHERE id = 1;"
        result = self.guardrail_adapter.validate_sql_safety(sql)
        self.assertFalse(result.is_safe)
        self.assertIn("Forbidden DDL/DML", result.blocked_reason)

    def test_guardrails_allows_valid_select(self):
        sql = "SELECT id, name FROM users WHERE active = true LIMIT 10;"
        result = self.guardrail_adapter.validate_sql_safety(sql)
        self.assertTrue(result.is_safe)
        self.assertIsNone(result.blocked_reason)


if __name__ == "__main__":
    unittest.main()
