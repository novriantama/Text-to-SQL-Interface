"""EXPLAIN cost and estimated row scan evaluator adapter."""

import re
from src.core.config import settings
from src.core.logger import get_logger

logger = get_logger(__name__)


class ExplainCostEvaluator:
    """Parses database EXPLAIN plan outputs and calculates estimated query scanning cost and row counts."""

    def estimate_cost(self, explain_plan: str) -> float:
        """Parses max cost metrics from PostgreSQL/SQLite EXPLAIN plan string."""
        if not explain_plan or explain_plan == "EXPLAIN plan unavailable":
            return 0.0

        # PostgreSQL cost regex pattern: cost=0.00..50000.00 rows=1000
        cost_match = re.search(r"cost=\d+\.\d+\.\.(\d+\.\d+)", explain_plan)
        if cost_match:
            return float(cost_match.group(1))

        # Rows scan regex pattern: rows=50000
        rows_match = re.search(r"rows=(\d+)", explain_plan)
        if rows_match:
            return float(rows_match.group(1))

        return 0.0

    def is_cost_acceptable(self, explain_plan: str) -> tuple[bool, float]:
        """Checks if estimated cost/row count is below safety threshold."""
        cost = self.estimate_cost(explain_plan)
        if cost > settings.MAX_EXPLAIN_COST:
            return False, cost
        return True, cost
