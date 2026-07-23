"""Multi-query consensus engine for comparing dual query strategy results."""

from typing import Any
from src.core.logger import get_logger
from src.domain.entities.query import QueryResult

logger = get_logger(__name__)


class MultiQueryConsensusEngine:
    """Generates and compares alternative SQL approaches to verify correctness.
    
    If results of independent primary and alternative queries match (identical row count,
    equivalent values / sets), consensus is established (high confidence signal).
    If results diverge, consensus fails and specific discrepancy warnings are generated.
    """

    def compare_result_sets(
        self,
        primary_result: QueryResult | None,
        alternative_result: QueryResult | None
    ) -> tuple[bool, str | None]:
        """Compares execution output datasets of primary and alternative queries."""
        if primary_result is None or alternative_result is None:
            return True, None

        data_a = primary_result.data or []
        data_b = alternative_result.data or []

        # 1. Compare row counts
        if len(data_a) != len(data_b):
            discrepancy = (
                f"Multi-query consensus discrepancy: Primary query returned {len(data_a)} rows, "
                f"whereas Alternative query returned {len(data_b)} rows."
            )
            logger.warning(discrepancy)
            return False, discrepancy

        if not data_a and not data_b:
            return True, None

        # 2. Compare dataset values normalized across column alias differences
        normalized_a = self._normalize_dataset(data_a)
        normalized_b = self._normalize_dataset(data_b)

        if normalized_a == normalized_b:
            logger.info("Multi-query consensus verified: Independent query approaches produced identical result sets.")
            return True, None

        discrepancy = (
            f"Multi-query consensus discrepancy: Primary query and alternative query results "
            f"returned divergent values across rows."
        )
        logger.warning(discrepancy)
        return False, discrepancy

    def _normalize_dataset(self, data: list[dict[str, Any]]) -> list[tuple]:
        """Normalizes list of row dictionaries to comparable sorted tuples of values."""
        normalized_rows = []
        for row in data:
            # Sort row values converted to string representations for scalar comparison
            sorted_vals = tuple(sorted(str(v) if v is not None else "" for v in row.values()))
            normalized_rows.append(sorted_vals)
        return sorted(normalized_rows)
