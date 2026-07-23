"""Unit tests for MultiQueryConsensusEngine and multi-query validation pipeline."""

import unittest
import sqlite3
import tempfile
from pathlib import Path
from sqlalchemy import create_engine
from src.domain.entities.query import QueryResult, QueryRequest
from src.infrastructure.validation.consensus_engine import MultiQueryConsensusEngine
from src.infrastructure.db.sandbox_executor import SandboxDatabaseAdapter
from src.infrastructure.llm.instructor_client import InstructorLLMAdapter
from src.infrastructure.guardrails.ast_parser import ASTGuardrailAdapter
from src.infrastructure.validation.back_translator import DefaultHallucinationValidatorAdapter
from src.infrastructure.vector_store.schema_retriever import EmbeddingSchemaRetriever
from src.application.use_cases.process_text_to_sql import ProcessTextToSQLUseCase


class TestMultiQueryConsensusEngine(unittest.TestCase):

    def setUp(self):
        self.engine = MultiQueryConsensusEngine()

    def test_matching_results_returns_consensus(self):
        res_a = QueryResult(
            data=[{"id": 1, "val": 100}, {"id": 2, "val": 200}],
            columns=["id", "val"],
            rows_returned=2,
            execution_time_ms=1.0
        )
        res_b = QueryResult(
            data=[{"val": 100, "id": 1}, {"val": 200, "id": 2}],
            columns=["val", "id"],
            rows_returned=2,
            execution_time_ms=1.2
        )
        matched, discrepancy = self.engine.compare_result_sets(res_a, res_b)
        self.assertTrue(matched)
        self.assertIsNone(discrepancy)

    def test_divergent_row_count_returns_discrepancy(self):
        res_a = QueryResult(
            data=[{"id": 1, "val": 100}, {"id": 2, "val": 200}],
            columns=["id", "val"],
            rows_returned=2,
            execution_time_ms=1.0
        )
        res_b = QueryResult(
            data=[{"id": 1, "val": 100}],
            columns=["id", "val"],
            rows_returned=1,
            execution_time_ms=0.8
        )
        matched, discrepancy = self.engine.compare_result_sets(res_a, res_b)
        self.assertFalse(matched)
        self.assertIsNotNone(discrepancy)
        self.assertIn("returned 2 rows, whereas Alternative query returned 1 rows", discrepancy)

    def test_divergent_values_returns_discrepancy(self):
        res_a = QueryResult(
            data=[{"id": 1, "val": 100}],
            columns=["id", "val"],
            rows_returned=1,
            execution_time_ms=1.0
        )
        res_b = QueryResult(
            data=[{"id": 1, "val": 999}],
            columns=["id", "val"],
            rows_returned=1,
            execution_time_ms=1.0
        )
        matched, discrepancy = self.engine.compare_result_sets(res_a, res_b)
        self.assertFalse(matched)
        self.assertIsNotNone(discrepancy)
        self.assertIn("returned divergent values", discrepancy)


class TestMultiQueryPipelineIntegration(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_file = Path(self.temp_dir.name) / "test_consensus.db"
        conn = sqlite3.connect(self.db_file)
        conn.execute("CREATE TABLE orders (id INT, amount DECIMAL);")
        conn.execute("INSERT INTO orders VALUES (1, 100.0);")
        conn.execute("INSERT INTO orders VALUES (2, 200.0);")
        conn.commit()
        conn.close()

        self.db_engine = create_engine(f"sqlite:///{self.db_file}")
        self.db_adapter = SandboxDatabaseAdapter(self.db_engine)
        self.llm_adapter = InstructorLLMAdapter()
        self.guardrails = ASTGuardrailAdapter()
        self.validator = DefaultHallucinationValidatorAdapter(llm_port=self.llm_adapter)
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

    def test_pipeline_executes_dual_queries_and_matches_consensus(self):
        req = QueryRequest(question="List all orders")
        res = self.use_case.execute(req)

        self.assertIsNotNone(res.generated_sql)
        self.assertIsNotNone(res.alternative_sql)
        self.assertIsNotNone(res.results)
        self.assertIsNotNone(res.alternative_results)
        self.assertEqual(res.confidence.multi_query_consensus, 1.0)
        self.assertEqual(res.results.rows_returned, res.alternative_results.rows_returned)

    def test_pipeline_flags_discrepancy_when_queries_diverge(self):
        # Trigger mock divergent alternative query
        req = QueryRequest(question="List all orders diverge_consensus")
        res = self.use_case.execute(req)

        self.assertEqual(res.confidence.multi_query_consensus, 0.0)
        self.assertTrue(any("Multi-query consensus discrepancy" in w for w in res.warnings))


if __name__ == "__main__":
    unittest.main()
