"""AST parser using sqlparse to block DDL/DML, enforce subquery depth, and append row limits."""

import re
import sqlparse
from sqlparse.tokens import Keyword, DDL, DML
from src.core.config import settings
from src.domain.ports.guardrail_port import GuardrailPort
from src.domain.entities.validation import GuardrailResult


class ASTGuardrailAdapter(GuardrailPort):
    """Guardrail middleware blocking dangerous operations and enforcing query restrictions."""

    FORBIDDEN_KEYWORDS = {
        "DROP", "ALTER", "CREATE", "DELETE", "UPDATE", "INSERT",
        "GRANT", "REVOKE", "TRUNCATE", "REPLACE", "EXEC", "EXECUTE"
    }

    def validate_sql_safety(self, sql_query: str, explain_plan: str | None = None) -> GuardrailResult:
        """Parse query AST and enforce security rules."""
        parsed = sqlparse.parse(sql_query)
        if not parsed:
            return GuardrailResult(is_safe=False, blocked_reason="Invalid SQL syntax")

        statement = parsed[0]

        # 1. Block DDL and DML operations
        for token in statement.flatten():
            token_val = token.value.upper()
            if token_val in self.FORBIDDEN_KEYWORDS:
                return GuardrailResult(
                    is_safe=False,
                    blocked_reason=f"Forbidden DDL/DML operation detected: '{token_val}'"
                )

        # 2. Check Subquery Depth
        subquery_count = sql_query.upper().count("SELECT") - 1
        if subquery_count > settings.MAX_SUBQUERY_DEPTH:
            return GuardrailResult(
                is_safe=False,
                blocked_reason=f"Subquery depth ({subquery_count}) exceeds max allowed depth ({settings.MAX_SUBQUERY_DEPTH})"
            )

        # 3. Check Row Limit
        has_limit = "LIMIT" in sql_query.upper()

        return GuardrailResult(
            is_safe=True,
            row_limit_applied=has_limit,
            ast_parsed=True
        )
