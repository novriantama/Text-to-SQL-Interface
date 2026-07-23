"""FastAPI Dependency Injection Providers."""

from functools import lru_cache
from src.infrastructure.db.connection import get_db_engine
from src.infrastructure.db.sandbox_executor import SandboxDatabaseAdapter
from src.infrastructure.guardrails.ast_parser import ASTGuardrailAdapter
from src.infrastructure.llm.instructor_client import InstructorLLMAdapter
from src.infrastructure.validation.back_translator import DefaultHallucinationValidatorAdapter
from src.infrastructure.vector_store.schema_retriever import EmbeddingSchemaRetriever
from src.application.use_cases.process_text_to_sql import ProcessTextToSQLUseCase
from src.application.use_cases.extract_schema import ExtractSchemaUseCase
from src.application.use_cases.submit_feedback import SubmitFeedbackUseCase


@lru_cache()
def get_pipeline_use_case() -> ProcessTextToSQLUseCase:
    """Instantiates and wires dependencies for the Text-to-SQL pipeline use case."""
    engine = get_db_engine()
    db_port = SandboxDatabaseAdapter(engine)
    llm_port = InstructorLLMAdapter()
    guardrail_port = ASTGuardrailAdapter()
    validation_port = DefaultHallucinationValidatorAdapter(llm_port=llm_port)
    vector_store_port = EmbeddingSchemaRetriever()

    return ProcessTextToSQLUseCase(
        db_port=db_port,
        llm_port=llm_port,
        guardrail_port=guardrail_port,
        validation_port=validation_port,
        vector_store_port=vector_store_port,
    )


@lru_cache()
def get_extract_schema_use_case() -> ExtractSchemaUseCase:
    """Instantiates schema extraction use case."""
    engine = get_db_engine()
    db_port = SandboxDatabaseAdapter(engine)
    vector_store_port = EmbeddingSchemaRetriever()
    return ExtractSchemaUseCase(db_port, vector_store_port)


@lru_cache()
def get_submit_feedback_use_case() -> SubmitFeedbackUseCase:
    """Instantiates submit feedback use case."""
    return SubmitFeedbackUseCase()
