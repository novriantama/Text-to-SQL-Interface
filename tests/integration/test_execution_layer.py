"""Integration tests for the Query Execution Layer."""

import unittest
import sqlite3
import tempfile
from pathlib import Path
from sqlalchemy import create_engine
from src.infrastructure.db.sandbox_executor import SandboxDatabaseAdapter
from src.domain.entities.query import QueryRequest
from src.application.use_cases.process_text_to_sql import ProcessTextToSQLUseCase
from src.infrastructure.llm.instructor_client import InstructorLLMAdapter
from src.infrastructure.guardrails.ast_parser import ASTGuardrailAdapter
from src.infrastructure.validation.back_translator import DefaultHallucinationValidatorAdapter
from src.infrastructure.vector_store.schema_retriever import EmbeddingSchemaRetriever


class TestExecutionLayer(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_file = Path(self.temp_dir.name) / "test_exec.db"
        conn = sqlite3.connect(self.db_file)
        conn.execute("CREATE TABLE orders (id INT, amount DECIMAL);")
        for i in range(1, 15):
            conn.execute(f"INSERT INTO orders VALUES ({i}, {i * 10.0});")
        conn.commit()
        conn.close()

        self.engine = create_engine(f"sqlite:///{self.db_file}")
        self.db_adapter = SandboxDatabaseAdapter(self.engine)
        self.llm_adapter = InstructorLLMAdapter()
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

    def test_execution_layer_payload_packaging(self):
        req = QueryRequest(question="List orders")
        res = self.use_case.execute(req)

        self.assertTrue(res.guardrails_passed)
        self.assertIsNotNone(res.results)
        self.assertGreater(res.results.rows_returned, 0)
        self.assertGreaterEqual(res.results.execution_time_ms, 0.0)
        self.assertIsNotNone(res.results.explain_plan)
        self.assertIn("LIMIT", res.generated_sql)


if __name__ == "__main__":
    unittest.main()
