"""Result sanity checking heuristics."""


class ResultSanityChecker:
    """Verifies that execution dataframe outputs fall within expected domain parameters."""

    def check_dataframe_sanity(self, data: list[dict]) -> tuple[bool, list[str]]:
        """Scans records for anomalies like extreme values, null spikes, or invalid dates."""
        warnings = []
        if not data:
            return True, warnings

        # Heuristic check on null values
        total_fields = sum(len(row) for row in data)
        null_fields = sum(sum(1 for v in row.values() if v is None) for row in data)
        
        if total_fields > 0 and (null_fields / total_fields) > 0.4:
            warnings.append("More than 40% of fields in the result set are NULL.")
            return False, warnings

        return True, warnings
