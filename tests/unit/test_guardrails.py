"""Unit tests for Configurable AST Guardrail Middleware."""

import unittest
from src.core.config import settings
from src.infrastructure.guardrails.ast_parser import ASTGuardrailAdapter
from src.infrastructure.guardrails.explain_evaluator import ExplainCostEvaluator


class TestASTGuardrailMiddleware(unittest.TestCase):

    def setUp(self):
        self.explain_evaluator = ExplainCostEvaluator()
        self.guardrail = ASTGuardrailAdapter(self.explain_evaluator)

    def test_blocks_ddl_operations(self):
        ddl_queries = [
            "CREATE TABLE test (id INT);",
            "ALTER TABLE users ADD COLUMN age INT;",
            "DROP TABLE orders;",
            "TRUNCATE TABLE logs;",
            "GRANT ALL PRIVILEGES ON DATABASE db TO public;"
        ]
        for query in ddl_queries:
            with self.subTest(query=query):
                res = self.guardrail.validate_sql_safety(query)
                self.assertFalse(res.is_safe)
                self.assertIn("DDL operation", res.blocked_reason)

    def test_blocks_dml_write_operations(self):
        dml_queries = [
            "INSERT INTO users VALUES (1, 'john');",
            "UPDATE accounts SET balance = 0 WHERE id = 1;",
            "DELETE FROM orders WHERE id = 5;",
            "MERGE INTO target USING source ON target.id = source.id;"
        ]
        for query in dml_queries:
            with self.subTest(query=query):
                res = self.guardrail.validate_sql_safety(query)
                self.assertFalse(res.is_safe)
                self.assertIn("DML write operation", res.blocked_reason)

    def test_enforces_row_limit(self):
        sql = "SELECT id, username FROM users"
        limited_sql, applied = self.guardrail.enforce_row_limit(sql)
        self.assertTrue(applied)
        self.assertIn(f"LIMIT {settings.MAX_ROW_LIMIT}", limited_sql)

        already_limited = "SELECT id, username FROM users LIMIT 50;"
        _, applied_2 = self.guardrail.enforce_row_limit(already_limited)
        self.assertFalse(applied_2)

    def test_blocks_deep_subqueries(self):
        # 5 SELECT statements = depth 4 subquery (> max allowed depth 3)
        deep_sql = "SELECT * FROM (SELECT * FROM (SELECT * FROM (SELECT * FROM (SELECT * FROM orders t1) t2) t3) t4);"
        res = self.guardrail.validate_sql_safety(deep_sql)
        self.assertFalse(res.is_safe)
        self.assertIn("Subquery depth", res.blocked_reason)

    def test_blocks_high_explain_cost(self):
        high_cost_plan = "Seq Scan on large_table (cost=0.00..999999.00 rows=1000000)"
        sql = "SELECT * FROM large_table;"
        res = self.guardrail.validate_sql_safety(sql, explain_plan=high_cost_plan)
        self.assertFalse(res.is_safe)
        self.assertIn("EXPLAIN plan estimated scan cost", res.blocked_reason)


if __name__ == "__main__":
    unittest.main()
