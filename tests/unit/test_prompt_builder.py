"""Unit tests for Dynamic Prompt Builder, FewShotRepository, and BusinessGlossaryRepository."""

import unittest
from src.domain.entities.schema import DatabaseSchema, TableSchema, ColumnSchema
from src.domain.entities.prompt import FewShotExample, BusinessTerm
from src.infrastructure.llm.prompt_builder import DynamicPromptBuilder
from src.infrastructure.llm.few_shot_repository import FewShotRepository
from src.infrastructure.llm.glossary_repository import BusinessGlossaryRepository


class TestDynamicPromptBuilder(unittest.TestCase):

    def setUp(self):
        self.few_shot_repo = FewShotRepository()
        self.glossary_repo = BusinessGlossaryRepository()
        self.prompt_builder = DynamicPromptBuilder(
            few_shot_repo=self.few_shot_repo,
            glossary_repo=self.glossary_repo,
            dialect="PostgreSQL"
        )
        self.sample_schema = DatabaseSchema(
            tables={
                "users": TableSchema(
                    name="users",
                    columns=[
                        ColumnSchema(name="id", data_type="INTEGER", is_primary_key=True),
                        ColumnSchema(name="username", data_type="VARCHAR(50)"),
                        ColumnSchema(name="status", data_type="VARCHAR(20)", sample_values=["active", "inactive"])
                    ],
                    description="User account records"
                ),
                "orders": TableSchema(
                    name="orders",
                    columns=[
                        ColumnSchema(name="id", data_type="INTEGER", is_primary_key=True),
                        ColumnSchema(name="user_id", data_type="INTEGER", is_foreign_key=True, foreign_table="users", foreign_column="id"),
                        ColumnSchema(name="amount", data_type="NUMERIC(10,2)"),
                        ColumnSchema(name="status", data_type="VARCHAR(20)", sample_values=["completed", "pending"])
                    ]
                )
            }
        )

    def test_few_shot_retrieval(self):
        examples = self.few_shot_repo.get_relevant_examples("What is the total revenue for this month?", limit=4)
        self.assertGreaterEqual(len(examples), 3)
        self.assertLessEqual(len(examples), 4)
        questions = [ex.question for ex in examples]
        self.assertTrue(any("revenue" in q.lower() for q in questions))

    def test_glossary_term_matching(self):
        terms = self.glossary_repo.find_matching_terms("Show total revenue for active customer accounts")
        term_names = [t.term for t in terms]
        self.assertIn("revenue", term_names)
        self.assertIn("active customer", term_names)

    def test_prompt_builder_assembly(self):
        question = "Calculate total revenue for active customer accounts"
        prompt = self.prompt_builder.build_prompt(question, self.sample_schema)

        # Check Schema injection
        self.assertIn("DATABASE SCHEMA:", prompt)
        self.assertIn("Table: users (User account records)", prompt)
        self.assertIn("[PRIMARY KEY]", prompt)
        self.assertIn("[FK -> users.id]", prompt)
        self.assertIn("Sample values: 'active', 'inactive'", prompt)

        # Check Glossary injection
        self.assertIn("BUSINESS GLOSSARY & METRIC DEFINITIONS:", prompt)
        self.assertIn("**revenue**", prompt)

        # Check Few-Shot Examples injection (3-5 pairs)
        self.assertIn("FEW-SHOT EXAMPLES (QUESTION-TO-SQL PAIRS):", prompt)
        self.assertIn("Q:", prompt)
        self.assertIn("SQL:", prompt)

        # Check PostgreSQL execution & safety rules
        self.assertIn("EXECUTION & SAFETY RULES:", prompt)
        self.assertIn("PostgreSQL", prompt)
        self.assertIn("USER QUESTION: Calculate total revenue for active customer accounts", prompt)


if __name__ == "__main__":
    unittest.main()
