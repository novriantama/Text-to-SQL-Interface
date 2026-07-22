"""Use Case: Main Text-to-SQL Pipeline Orchestration."""

from src.core.logger import get_logger
from src.domain.entities.query import QueryRequest, QueryResponse, ConfidenceScore
from src.domain.exceptions.domain_exceptions import GuardrailViolationException
from src.domain.ports.database_port import DatabasePort
from src.domain.ports.llm_port import LLMPort
from src.domain.ports.guardrail_port import GuardrailPort
from src.domain.ports.validation_port import ValidationPort
from src.domain.ports.vector_store_port import VectorStorePort

logger = get_logger(__name__)


class ProcessTextToSQLUseCase:
    """Orchestrates end-to-end question translation, safety checks, execution, and validation."""

    def __init__(
        self,
        db_port: DatabasePort,
        llm_port: LLMPort,
        guardrail_port: GuardrailPort,
        validation_port: ValidationPort,
        vector_store_port: VectorStorePort,
    ) -> None:
        self.db = db_port
        self.llm = llm_port
        self.guardrails = guardrail_port
        self.validator = validation_port
        self.vector_store = vector_store_port

    def execute(self, request: QueryRequest) -> QueryResponse:
        """Executes the full pipeline for a natural language question."""
        logger.info(f"Processing question: '{request.question}'")

        # Step 1: Introspect & Filter Schema
        full_schema = self.db.extract_schema()
        filtered_schema = self.vector_store.filter_schema(request.question, full_schema)

        # Step 2: Generate Structured SQL via LLM
        generated = self.llm.generate_sql(request.question, filtered_schema)

        # Step 3: Validate SQL Safety through Guardrails
        explain_plan = self.db.get_explain_plan(generated.sql)
        guardrail_check = self.guardrails.validate_sql_safety(generated.sql, explain_plan)

        if not guardrail_check.is_safe:
            logger.warning(f"Query blocked by guardrails: {guardrail_check.blocked_reason}")
            raise GuardrailViolationException(
                f"Security guardrail blocked query: {guardrail_check.blocked_reason}"
            )

        # Step 4: Execute SQL in Read-Only Sandbox
        query_result = self.db.execute_read_only(generated.sql)

        # Step 5: Run Hallucination & Consensus Validation
        hallucination_check = self.validator.check_hallucination(
            request.question, generated, query_result
        )

        # Step 6: Compute Composite Confidence Score
        confidence = ConfidenceScore(
            overall_score=(
                1.0 * (1 if guardrail_check.is_safe else 0)
                + hallucination_check.alignment_score
                + (1.0 if hallucination_check.sanity_checks_passed else 0.5)
                + (1.0 if hallucination_check.consensus_matched else 0.5)
            ) / 4.0,
            syntax_validity=1.0 if guardrail_check.ast_parsed else 0.0,
            back_translation_match=hallucination_check.alignment_score,
            result_sanity_score=1.0 if hallucination_check.sanity_checks_passed else 0.0,
            multi_query_consensus=1.0 if hallucination_check.consensus_matched else 0.0,
        )

        return QueryResponse(
            question=request.question,
            generated_sql=generated.sql,
            explanation=generated.explanation,
            results=query_result,
            confidence=confidence,
            guardrails_passed=guardrail_check.is_safe,
            warnings=hallucination_check.anomaly_warnings,
        )
