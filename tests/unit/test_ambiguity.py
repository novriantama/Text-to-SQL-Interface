"""Unit tests for explicit ambiguity handling and clarification requests."""

import unittest
from src.domain.entities.query import QueryRequest, QueryInterpretation
from src.infrastructure.llm.instructor_client import InstructorLLMAdapter
from src.application.use_cases.process_text_to_sql import ProcessTextToSQLUseCase
from src.infrastructure.db.sandbox_executor import SandboxDatabaseAdapter
from src.infrastructure.guardrails.ast_parser import ASTGuardrailAdapter
from src.infrastructure.validation.back_translator import DefaultHallucinationValidatorAdapter
from src.infrastructure.vector_store.schema_retriever import EmbeddingSchemaRetriever
from sqlalchemy import create_engine
import tempfile
import sqlite3
from pathlib import Path


class TestAmbiguityHandling(unittest.TestCase):

    def setUp(self):
        self.llm_adapter = InstructorLLMAdapter()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_file = Path(self.temp_dir.name) / "test_amb.db"
        
        conn = sqlite3.connect(self.db_file)
        conn.execute("CREATE TABLE orders (id INT, amount DECIMAL, status TEXT);")
        conn.execute("INSERT INTO orders VALUES (1, 100.0, 'completed');")
        conn.commit()
        conn.close()

        self.engine = create_engine(f"sqlite:///{self.db_file}")
        self.db_adapter = SandboxDatabaseAdapter(self.engine)
        self.guardrails = ASTGuardrailAdapter()
        self.validator = DefaultHallucinationValidatorAdapter()
        self.vector_store = EmbeddingSchemaRetriever()

        self.use_case = ProcessTextToSQLUseCase(
            db_port=self.db_adapter,
            llm_port=self.llm_adapter,
            guardrail_port=self.guardrails,
            validation_port=self.validator,
            vector_store_port=self.vector_store
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_ambiguity_detection_and_clarification_response(self):
        # Trigger mock ambiguous query
        request = QueryRequest(question="Show revenue (ambiguous)")
        response = self.use_case.execute(request)

        self.assertTrue(response.clarification_needed)
        self.assertGreaterEqual(len(response.clarification_options), 2)
        
        labels = [opt.label for opt in response.clarification_options]
        self.assertIn("Gross Revenue", labels)
        self.assertIn("Net Revenue", labels)
        self.assertIsNone(response.results)  # Ensures no arbitrary query was executed


if __name__ == "__main__":
    unittest.main()
