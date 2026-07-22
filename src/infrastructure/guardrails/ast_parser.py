"""AST parser using sqlparse to validate SQL syntax, block DDL/DML, enforce subquery depth, and verify query structure."""

import sqlparse
from src.core.config import settings
from src.domain.ports.guardrail_port import GuardrailPort
from src.domain.entities.validation import GuardrailResult


class ASTGuardrailAdapter(GuardrailPort):
    """Guardrail middleware parsing AST syntax with sqlparse, blocking dangerous operations, and enforcing query rules."""

    FORBIDDEN_KEYWORDS = {
        "DROP", "ALTER", "CREATE", "DELETE", "UPDATE", "INSERT",
        "GRANT", "REVOKE", "TRUNCATE", "REPLACE", "EXEC", "EXECUTE"
    }

    VALID_SQL_KEYWORDS = {
        "SELECT", "WITH", "DROP", "DELETE", "UPDATE", "INSERT", "CREATE", "ALTER", "GRANT", "TRUNCATE"
    }

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

    def validate_sql_safety(self, sql_query: str, explain_plan: str | None = None) -> GuardrailResult:
        """Parse query AST, validate syntax integrity, and enforce security policies."""
        # 1. Validate AST Syntax Integrity
        if not self.validate_sql_syntax(sql_query):
            return GuardrailResult(
                is_safe=False,
                blocked_reason="Invalid SQL syntax: Query failed AST parsing.",
                ast_parsed=False
            )

        parsed = sqlparse.parse(sql_query)
        statement = parsed[0]

        # 2. Block DDL and DML operations
        for token in statement.flatten():
            token_val = token.value.upper()
            if token_val in self.FORBIDDEN_KEYWORDS:
                return GuardrailResult(
                    is_safe=False,
                    blocked_reason=f"Forbidden DDL/DML operation detected: '{token_val}'",
                    ast_parsed=True
                )

        # 3. Check Subquery Depth
        subquery_count = max(0, sql_query.upper().count("SELECT") - 1)
        if subquery_count > settings.MAX_SUBQUERY_DEPTH:
            return GuardrailResult(
                is_safe=False,
                blocked_reason=f"Subquery depth ({subquery_count}) exceeds max allowed depth ({settings.MAX_SUBQUERY_DEPTH})",
                ast_parsed=True
            )

        # 4. Check Row Limit
        has_limit = "LIMIT" in sql_query.upper()

        return GuardrailResult(
            is_safe=True,
            row_limit_applied=has_limit,
            ast_parsed=True
        )
