"""EXPLAIN cost evaluator adapter."""

import re
from src.core.config import settings


class ExplainCostEvaluator:
    """Parses database EXPLAIN plan outputs and calculates query scanning cost."""

    def estimate_cost(self, explain_plan: str) -> float:
        """Parses cost metrics from EXPLAIN plan string."""
        if not explain_plan:
            return 0.0
        match = re.search(r"cost=\d+\.\d+\.\.(\d+\.\d+)", explain_plan)
        if match:
            return float(match.group(1))
        return 0.0

    def is_cost_acceptable(self, explain_plan: str) -> bool:
        """Checks if estimated cost is below safety threshold."""
        cost = self.estimate_cost(explain_plan)
        return cost <= settings.MAX_EXPLAIN_COST
