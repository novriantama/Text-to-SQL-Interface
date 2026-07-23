"""Result sanity checking heuristics for Text-to-SQL execution outputs."""

import math
import re
from datetime import datetime, timezone
from typing import Any
from src.core.logger import get_logger
from src.domain.entities.query import QueryResult

logger = get_logger(__name__)


class ResultSanityChecker:
    """Verifies that execution result outputs fall within expected domain parameters and heuristics.
    
    Checks performed:
    1. Null-heavy column detection (identifies bad JOINs or missing relationships).
    2. Aggregated/numeric value plausibility (detects negative counts/sums, NaN/Infinity, extreme Cartesian values).
    3. Count & magnitude validation (detects negative counts or unrealistic value explosions).
    4. Date range & timespan validation (detects future dates or sentinel epoch past dates).
    """

    def __init__(
        self,
        column_null_threshold: float = 0.50,
        extreme_value_threshold: float = 1e12,
        future_date_buffer_seconds: int = 86400
    ) -> None:
        self.column_null_threshold = column_null_threshold
        self.extreme_value_threshold = extreme_value_threshold
        self.future_date_buffer_seconds = future_date_buffer_seconds

    def check_sanity(
        self,
        query_result: QueryResult | None,
        question: str = ""
    ) -> tuple[bool, list[str]]:
        """Scans records for anomalies like extreme values, null spikes, or invalid dates."""
        warnings: list[str] = []

        if query_result is None or not query_result.data:
            return True, warnings

        data = query_result.data
        total_rows = len(data)
        columns = query_result.columns or list(data[0].keys())

        # 1. Check for NULL-heavy columns (Potential bad JOIN indicator)
        for col in columns:
            null_count = sum(1 for row in data if row.get(col) is None)
            null_ratio = null_count / total_rows
            if null_ratio >= self.column_null_threshold and total_rows >= 2:
                pct = round(null_ratio * 100, 1)
                warning = (
                    f"Column '{col}' is NULL-heavy ({pct}% NULLs across {total_rows} rows), "
                    f"which may indicate an incorrect JOIN condition or missing relationship."
                )
                warnings.append(warning)
                logger.warning(warning)

        # 2. Check Numeric & Aggregate Plausibility
        for col in columns:
            col_lower = col.lower()
            numeric_vals = []
            for row in data:
                val = row.get(col)
                if val is None:
                    continue

                # Check for NaN / Infinity
                if isinstance(val, float):
                    if math.isnan(val) or math.isinf(val):
                        warning = f"Column '{col}' contains non-finite numerical value ({val})."
                        warnings.append(warning)
                        logger.warning(warning)
                        continue

                if isinstance(val, (int, float)):
                    numeric_vals.append(val)

            if numeric_vals:
                # Check for negative values in columns where negative is improbable
                is_count_col = any(k in col_lower for k in ("count", "cnt", "quantity", "qty", "num_"))
                is_positive_col = is_count_col or any(
                    k in col_lower for k in ("revenue", "price", "amount", "total_sales", "subtotal")
                )

                if is_count_col:
                    negative_counts = [v for v in numeric_vals if v < 0]
                    if negative_counts:
                        warning = (
                            f"Count column '{col}' contains negative value ({negative_counts[0]}), "
                            f"which is logically invalid."
                        )
                        warnings.append(warning)
                        logger.warning(warning)

                elif is_positive_col:
                    negative_vals = [v for v in numeric_vals if v < 0]
                    if negative_vals and len(negative_vals) == len(numeric_vals):
                        warning = (
                            f"Metric column '{col}' contains exclusively negative values (e.g. {negative_vals[0]}), "
                            f"which may indicate a calculation or sign error."
                        )
                        warnings.append(warning)
                        logger.warning(warning)

                # Check for extreme magnitude values (Cartesian explosion indicator)
                max_val = max(abs(v) for v in numeric_vals)
                if max_val >= self.extreme_value_threshold:
                    warning = (
                        f"Column '{col}' contains an unusually large magnitude value ({max_val}), "
                        f"which may indicate an unintended Cartesian product or duplicate JOIN."
                    )
                    warnings.append(warning)
                    logger.warning(warning)

        # 3. Check Date Ranges & Timespan Anomalies
        now_ts = datetime.now(timezone.utc).timestamp() + self.future_date_buffer_seconds

        for col in columns:
            col_lower = col.lower()
            if any(k in col_lower for k in ("date", "time", "created", "updated", "timestamp", "dt", "at")):
                for row in data:
                    val = row.get(col)
                    if val is None:
                        continue

                    dt_obj = self._parse_datetime(val)
                    if dt_obj:
                        ts = dt_obj.timestamp()
                        if ts > now_ts:
                            warning = (
                                f"Column '{col}' contains a future date/timestamp '{val}', "
                                f"which exceeds the current system timespan."
                            )
                            warnings.append(warning)
                            logger.warning(warning)
                            break
                        if dt_obj.year in (1900, 1970) and "epoch" not in col_lower:
                            warning = (
                                f"Column '{col}' contains sentinel default date '{val}' (year {dt_obj.year})."
                            )
                            warnings.append(warning)
                            logger.warning(warning)
                            break

        sanity_passed = len(warnings) == 0
        return sanity_passed, warnings

    def _parse_datetime(self, val: Any) -> datetime | None:
        """Helper to parse string or datetime object."""
        if isinstance(val, datetime):
            if val.tzinfo is None:
                return val.replace(tzinfo=timezone.utc)
            return val
        if isinstance(val, str):
            val_str = val.strip()
            match = re.match(r"^(\d{4})-(\d{2})-(\d{2})", val_str)
            if match:
                try:
                    dt = datetime.fromisoformat(val_str.replace("Z", "+00:00"))
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    return dt
                except Exception:
                    pass
        return None
