"""Use Case: Main Text-to-SQL Pipeline Orchestration."""

import inspect
from src.core.logger import get_logger
from src.domain.entities.query import QueryRequest, QueryResponse, ConfidenceScore
from src.domain.exceptions.domain_exceptions import GuardrailViolationException
from src.domain.ports.database_port import DatabasePort
from src.domain.ports.llm_port import LLMPort
from src.domain.ports.guardrail_port import GuardrailPort
from src.domain.ports.validation_port import ValidationPort
from src.domain.ports.vector_store_port import VectorStorePort
from src.infrastructure.validation.confidence_evaluator import ConfidenceEvaluator

logger = get_logger(__name__)


class ProcessTextToSQLUseCase:
    """Orchestrates end-to-end question translation, safety checks, execution, and multi-signal confidence scoring."""

    def __init__(
        self,
        db_port: DatabasePort,
        llm_port: LLMPort,
        guardrail_port: GuardrailPort,
        validation_port: ValidationPort,
        vector_store_port: VectorStorePort,
        confidence_evaluator: ConfidenceEvaluator | None = None,
    ) -> None:
        self.db = db_port
        self.llm = llm_port
        self.guardrails = guardrail_port
        self.validator = validation_port
        self.vector_store = vector_store_port
        self.confidence_evaluator = confidence_evaluator or ConfidenceEvaluator()

    def execute(self, request: QueryRequest) -> QueryResponse:
        """Executes the full pipeline for a natural language question."""
        logger.info(f"[AUDIT QUESTION START] Processing question: '{request.question}'")

        # Step 1: Introspect & Filter Schema
        full_schema = self.db.extract_schema()
        filtered_schema = self.vector_store.filter_schema(request.question, full_schema)
        filtered_table_names = list(filtered_schema.tables.keys()) if filtered_schema and filtered_schema.tables else []

        # Step 2: Generate Primary Structured SQL via LLM
        generated = self.llm.generate_sql(request.question, filtered_schema)

        # Step 2b: Explicit Ambiguity Check
        if generated.is_ambiguous and generated.clarification_options:
            logger.info(f"[AUDIT AMBIGUITY DETECTED] Question: '{request.question}'. Returning clarification request.")
            return QueryResponse(
                question=request.question,
                generated_sql=generated.sql,
                explanation=generated.explanation or "Multiple distinct business interpretations detected. Please select an option below.",
                results=None,
                confidence=ConfidenceScore(
                    overall_score=0.50,
                    syntax_validity=1.0,
                    back_translation_match=0.50,
                    result_sanity_score=0.50,
                    multi_query_consensus=0.50,
                    schema_coverage=0.50
                ),
                guardrails_passed=True,
                warnings=["Ambiguous question detected. Please choose a specific interpretation."],
                clarification_needed=True,
                clarification_options=generated.clarification_options
            )

        # Step 3: Validate Primary SQL Safety through Configurable Guardrails
        explain_plan = self.db.get_explain_plan(generated.sql)
        guardrail_check = self.guardrails.validate_sql_safety(generated.sql, explain_plan)

        if not guardrail_check.is_safe:
            logger.warning(f"[AUDIT GUARDRAIL BLOCKED] Reason: {guardrail_check.blocked_reason} | Query: '{generated.sql}'")
            raise GuardrailViolationException(
                f"Security guardrail blocked query: {guardrail_check.blocked_reason}"
            )

        # Enforce Row Limit on Primary Query
        target_sql = generated.sql
        if hasattr(self.guardrails, "enforce_row_limit"):
            target_sql, _ = self.guardrails.enforce_row_limit(generated.sql)

        # Step 4: Execute Primary SQL in Read-Only Sandbox
        query_result = self.db.execute_read_only(target_sql)

        # Step 5: Multi-Query Validation - Generate & Execute Independent Alternative SQL Approach
        alt_generated = self.llm.generate_alternative_sql(
            request.question, filtered_schema, primary_sql=generated.sql
        )
        alt_sql = alt_generated.sql
        if hasattr(self.guardrails, "enforce_row_limit"):
            alt_sql, _ = self.guardrails.enforce_row_limit(alt_generated.sql)

        alt_result = None
        try:
            alt_guardrail = self.guardrails.validate_sql_safety(alt_sql)
            if alt_guardrail.is_safe:
                alt_result = self.db.execute_read_only(alt_sql)
        except Exception as err:
            logger.debug(f"Alternative query execution skipped or failed: {err}")

        # Step 6: Run Hallucination & Consensus Validation
        if hasattr(self.validator, "check_hallucination"):
            sig = inspect.signature(self.validator.check_hallucination)
            if "alternative_result" in sig.parameters:
                hallucination_check = self.validator.check_hallucination(
                    request.question, generated, query_result, alternative_result=alt_result
                )
            else:
                hallucination_check = self.validator.check_hallucination(
                    request.question, generated, query_result
                )

        # Step 7: Compute Multi-Signal Composite Confidence Score via ConfidenceEvaluator
        sanity_warning_count = len(hallucination_check.anomaly_warnings)
        confidence = self.confidence_evaluator.calculate_confidence(
            guardrails_passed=guardrail_check.is_safe,
            ast_parsed=guardrail_check.ast_parsed,
            back_translation_alignment=hallucination_check.alignment_score,
            sanity_checks_passed=hallucination_check.sanity_checks_passed,
            sanity_warning_count=sanity_warning_count,
            consensus_matched=hallucination_check.consensus_matched,
            accessed_tables=generated.accessed_tables,
            schema_tables=filtered_table_names
        )

        logger.info(
            f"[AUDIT PIPELINE COMPLETE] Question: '{request.question}' | Primary Rows: {query_result.rows_returned} | "
            f"Alt Rows: {alt_result.rows_returned if alt_result else 0} | Consensus: {hallucination_check.consensus_matched} | "
            f"Overall Confidence: {round(confidence.overall_score * 100, 1)}%"
        )

        return QueryResponse(
            question=request.question,
            generated_sql=target_sql,
            explanation=generated.explanation,
            results=query_result,
            confidence=confidence,
            guardrails_passed=guardrail_check.is_safe,
            warnings=hallucination_check.anomaly_warnings,
            alternative_sql=alt_sql,
            alternative_explanation=alt_generated.explanation,
            alternative_results=alt_result
        )
