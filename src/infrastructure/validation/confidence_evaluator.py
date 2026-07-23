"""Confidence Evaluator calculating multi-signal composite confidence scores."""

from src.core.logger import get_logger
from src.domain.entities.query import ConfidenceScore

logger = get_logger(__name__)


class ConfidenceEvaluator:
    """Combines 5 core verification signals into a composite confidence score:
    1. SQL Syntax Validity & Guardrail Pass Rate (20% weight)
    2. Back-Translation Alignment Score (25% weight)
    3. Result Sanity Check Pass Rate (20% weight)
    4. Multi-Query Consensus Agreement (20% weight)
    5. Schema Coverage Score (15% weight)
    """

    WEIGHT_SYNTAX: float = 0.20
    WEIGHT_BACK_TRANSLATION: float = 0.25
    WEIGHT_SANITY: float = 0.20
    WEIGHT_CONSENSUS: float = 0.20
    WEIGHT_SCHEMA: float = 0.15

    def calculate_confidence(
        self,
        guardrails_passed: bool,
        ast_parsed: bool,
        back_translation_alignment: float,
        sanity_checks_passed: bool,
        sanity_warning_count: int,
        consensus_matched: bool,
        accessed_tables: list[str],
        schema_tables: list[str]
    ) -> ConfidenceScore:
        """Calculates normalized confidence score across all 5 verification signals."""
        # 1. Syntax Validity & Guardrail Signal (0.0 or 1.0)
        syntax_validity = 1.0 if (ast_parsed and guardrails_passed) else 0.0

        # 2. Back-Translation Alignment Signal (0.0 to 1.0)
        back_translation_match = round(min(1.0, max(0.0, back_translation_alignment)), 2)

        # 3. Result Sanity Check Signal (0.0 to 1.0)
        if sanity_checks_passed and sanity_warning_count == 0:
            result_sanity_score = 1.0
        elif sanity_warning_count == 1:
            result_sanity_score = 0.60
        else:
            result_sanity_score = max(0.0, round(1.0 - (0.35 * sanity_warning_count), 2))

        # 4. Multi-Query Consensus Signal (0.0 or 1.0)
        multi_query_consensus = 1.0 if consensus_matched else 0.0

        # 5. Schema Coverage Signal (0.0 to 1.0)
        schema_coverage = self._calculate_schema_coverage(accessed_tables, schema_tables)

        # Weighted Composite Overall Score
        overall = (
            (self.WEIGHT_SYNTAX * syntax_validity)
            + (self.WEIGHT_BACK_TRANSLATION * back_translation_match)
            + (self.WEIGHT_SANITY * result_sanity_score)
            + (self.WEIGHT_CONSENSUS * multi_query_consensus)
            + (self.WEIGHT_SCHEMA * schema_coverage)
        )
        overall_score = round(min(1.0, max(0.0, overall)), 2)

        logger.info(
            f"Computed Confidence Score: Overall={overall_score} | Syntax={syntax_validity} | "
            f"BackTranslation={back_translation_match} | Sanity={result_sanity_score} | "
            f"Consensus={multi_query_consensus} | SchemaCoverage={schema_coverage}"
        )

        return ConfidenceScore(
            overall_score=overall_score,
            syntax_validity=syntax_validity,
            back_translation_match=back_translation_match,
            result_sanity_score=result_sanity_score,
            multi_query_consensus=multi_query_consensus,
            schema_coverage=schema_coverage
        )

    def _calculate_schema_coverage(self, accessed_tables: list[str], schema_tables: list[str]) -> float:
        """Calculates ratio of relevant schema tables covered by generated query."""
        if not schema_tables:
            return 1.0

        accessed_set = {t.lower() for t in accessed_tables if t}
        schema_set = {t.lower() for t in schema_tables if t}

        if not accessed_set:
            return 0.50

        intersection = accessed_set.intersection(schema_set)
        if not intersection:
            return 0.50

        coverage = len(intersection) / len(schema_set)
        return round(min(1.0, max(0.5, coverage)), 2)
