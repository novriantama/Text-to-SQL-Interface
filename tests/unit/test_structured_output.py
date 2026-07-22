"""Unit tests for Structured LLM Output generation and sqlparse syntax pre-validation."""

import unittest
from src.domain.entities.schema import DatabaseSchema, TableSchema, ColumnSchema
from src.infrastructure.llm.instructor_client import InstructorLLMAdapter, LLMSQLOutputSchema
from src.infrastructure.guardrails.ast_parser import ASTGuardrailAdapter


class TestStructuredOutputAndSyntaxValidation(unittest.TestCase):

    def setUp(self):
        self.llm_adapter = InstructorLLMAdapter()
        self.guardrail = ASTGuardrailAdapter()
        self.sample_schema = DatabaseSchema(
            tables={
                "orders": TableSchema(
                    name="orders",
                    columns=[
                        ColumnSchema(name="id", data_type="INTEGER"),
                        ColumnSchema(name="amount", data_type="NUMERIC"),
                        ColumnSchema(name="status", data_type="VARCHAR")
                    ]
                )
            }
        )

    def test_structured_output_schema_fields(self):
        output = LLMSQLOutputSchema(
            sql="SELECT id, amount FROM orders WHERE status = 'completed';",
            explanation="Selects order id and amount for completed orders.",
            confidence_estimate=0.92,
            accessed_tables=["orders"],
            accessed_columns=["id", "amount", "status"],
            is_ambiguous=False
        )
        self.assertEqual(output.accessed_tables, ["orders"])
        self.assertEqual(output.accessed_columns, ["id", "amount", "status"])
        self.assertEqual(output.confidence_estimate, 0.92)

    def test_sqlparse_syntax_validation_valid(self):
        sql = "SELECT id, amount FROM orders WHERE status = 'completed' LIMIT 10;"
        self.assertTrue(self.guardrail.validate_sql_syntax(sql))
        result = self.guardrail.validate_sql_safety(sql)
        self.assertTrue(result.is_safe)
        self.assertTrue(result.ast_parsed)

    def test_sqlparse_syntax_validation_invalid(self):
        invalid_sql = "INVALID QUERY EXPRESSION WITHOUT SELECT"
        self.assertFalse(self.guardrail.validate_sql_syntax(invalid_sql))
        result = self.guardrail.validate_sql_safety(invalid_sql)
        self.assertFalse(result.is_safe)
        self.assertIn("Invalid SQL syntax", result.blocked_reason)


if __name__ == "__main__":
    unittest.main()
