"""AST parser using sqlparse to validate SQL syntax, block DDL/DML, enforce subquery depth, apply row limits, and log blocked queries."""

import sqlparse
from src.core.config import settings
from src.core.logger import get_logger
from src.domain.ports.guardrail_port import GuardrailPort
from src.domain.entities.validation import GuardrailResult
from src.infrastructure.guardrails.explain_evaluator import ExplainCostEvaluator

logger = get_logger(__name__)


class ASTGuardrailAdapter(GuardrailPort):
    """Configurable guardrail middleware implementing safety checks, row limit enforcement, and audit logging."""

    DDL_KEYWORDS = {
        "DROP", "ALTER", "CREATE", "TRUNCATE", "REPLACE", "GRANT", "REVOKE", "RENAME"
    }

    DML_WRITE_KEYWORDS = {
        "DELETE", "UPDATE", "INSERT", "MERGE"
    }

    VALID_SQL_KEYWORDS = {
        "SELECT", "WITH", "DROP", "DELETE", "UPDATE", "INSERT", "CREATE", "ALTER", "GRANT", "TRUNCATE", "MERGE"
    }

    def __init__(self, explain_evaluator: ExplainCostEvaluator | None = None) -> None:
        self.explain_evaluator = explain_evaluator or ExplainCostEvaluator()

    def validate_sql_syntax(self, sql_query: str) -> bool:
        """Validates if SQL query parses cleanly into a valid SQL statement tree."""
        if not sql_query or not sql_query.strip():
            return False
        try:
            parsed = sqlparse.parse(sql_query)
            if not parsed or len(parsed) == 0:
                return False
            statement = parsed[0]
            stmt_type = statement.get_type()
            first_token = statement.token_first(skip_ws=True, skip_cm=True)
            if not first_token:
                return False
            first_word = first_token.value.upper()
            return stmt_type in ("SELECT", "DELETE", "UPDATE", "INSERT", "CREATE", "DROP", "ALTER") or first_word in self.VALID_SQL_KEYWORDS
        except Exception:
            return False

    def enforce_row_limit(self, sql_query: str) -> tuple[str, bool]:
        """Enforces MAX_ROW_LIMIT if query lacks a LIMIT clause."""
        clean_sql = sql_query.strip().rstrip(";")
        if "LIMIT" not in clean_sql.upper():
            limited_sql = f"{clean_sql} LIMIT {settings.MAX_ROW_LIMIT};"
            return limited_sql, True
        return sql_query, False

    def validate_sql_safety(self, sql_query: str, explain_plan: str | None = None) -> GuardrailResult:
        """Parse query AST, validate syntax integrity, and enforce configurable security policies."""
        # 1. Validate AST Syntax Integrity
        if not self.validate_sql_syntax(sql_query):
            return self._block_and_log(sql_query, "Invalid SQL syntax: Query failed AST parsing.")

        parsed = sqlparse.parse(sql_query)
        statement = parsed[0]

        # 2. Block DDL operations if configured
        if settings.BLOCK_DDL:
            for token in statement.flatten():
                token_val = token.value.upper()
                if token_val in self.DDL_KEYWORDS:
                    return self._block_and_log(sql_query, f"Configured rule blocked DDL operation: '{token_val}'")

        # 3. Block DML write operations if configured
        if settings.BLOCK_DML_WRITES:
            for token in statement.flatten():
                token_val = token.value.upper()
                if token_val in self.DML_WRITE_KEYWORDS:
                    return self._block_and_log(sql_query, f"Configured rule blocked DML write operation: '{token_val}'")

        # 4. Check Subquery Depth
        subquery_count = max(0, sql_query.upper().count("SELECT") - 1)
        if subquery_count > settings.MAX_SUBQUERY_DEPTH:
            return self._block_and_log(
                sql_query,
                f"Subquery depth ({subquery_count}) exceeds max allowed threshold ({settings.MAX_SUBQUERY_DEPTH})"
            )

        # 5. Check EXPLAIN Estimated Scan Cost / Row Limit
        if explain_plan:
            is_acceptable, cost = self.explain_evaluator.is_cost_acceptable(explain_plan)
            if not is_acceptable:
                return self._block_and_log(
                    sql_query,
                    f"EXPLAIN plan estimated scan cost ({cost}) exceeds max allowed limit ({settings.MAX_EXPLAIN_COST})"
                )

        # 6. Enforce Row Limit
        _, limit_applied = self.enforce_row_limit(sql_query)

        return GuardrailResult(
            is_safe=True,
            row_limit_applied=limit_applied,
            ast_parsed=True
        )

    def _block_and_log(self, sql_query: str, reason: str) -> GuardrailResult:
        """Helper to log blocked queries for compliance auditing and return failed GuardrailResult."""
        if settings.ENABLE_GUARDRAIL_LOGGING:
            logger.warning(f"[AUDIT GUARDRAIL BLOCKED] Reason: '{reason}' | Query: '{sql_query}'")
        return GuardrailResult(
            is_safe=False,
            blocked_reason=reason,
            ast_parsed=True
        )
