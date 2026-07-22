"""Multi-query consensus engine for comparing dual query strategy results."""


class MultiQueryConsensusEngine:
    """Generates and compares alternative SQL approaches to verify correctness."""

    def compare_result_sets(self, results_a: list[dict], results_b: list[dict]) -> bool:
        """Returns True if independent execution results match."""
        if len(results_a) != len(results_b):
            return False
        return results_a == results_b
