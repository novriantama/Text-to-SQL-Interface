"""Unit tests for Dynamic Prompt Builder."""

import unittest
from src.domain.entities.schema import DatabaseSchema, TableSchema, ColumnSchema
from src.infrastructure.llm.prompt_builder import DynamicPromptBuilder


class TestPromptBuilder(unittest.TestCase):

    def setUp(self):
        self.prompt_builder = DynamicPromptBuilder()

    def test_prompt_builder_assembly(self):
        schema = DatabaseSchema(
            tables={
                "users": TableSchema(
                    name="users",
                    columns=[
                        ColumnSchema(name="id", data_type="INTEGER", is_primary_key=True),
                        ColumnSchema(name="username", data_type="VARCHAR")
                    ]
                )
            }
        )
        prompt = self.prompt_builder.build_prompt("Show all users", schema)
        self.assertIn("DATABASE SCHEMA:", prompt)
        self.assertIn("Table: users", prompt)
        self.assertIn("USER QUESTION: Show all users", prompt)


if __name__ == "__main__":
    unittest.main()
