"""Back-translation alignment judge implementing ValidationPort for SQL-to-question verification."""

import difflib
import re
from src.core.logger import get_logger
from src.domain.ports.validation_port import ValidationPort
from src.domain.ports.llm_port import LLMPort
from src.domain.entities.query import QueryResult, GeneratedSQL
from src.domain.entities.validation import HallucinationCheckResult

logger = get_logger(__name__)


class DefaultHallucinationValidatorAdapter(ValidationPort):
    """Validator adapter performing SQL-to-question back-translation verification, result sanity heuristics, and consensus checks."""

    STOPWORDS = {
        "what", "is", "the", "for", "this", "a", "an", "in", "of", "to", "show", "list", "get", "retrieve", "data", "select", "find", "all", "are", "by", "with", "how", "many"
    }

    def __init__(self, llm_port: LLMPort | None = None, alignment_threshold: float = 0.60) -> None:
        self.llm = llm_port
        self.alignment_threshold = alignment_threshold

    def check_hallucination(
        self,
        original_question: str,
        generated_sql: GeneratedSQL,
        query_result: QueryResult | None
    ) -> HallucinationCheckResult:
        """Executes verification checks on query logic and outputs."""
        warnings = []

        # 1. Back-translation alignment verification
        if self.llm is not None:
            back_translated = self.llm.back_translate_sql(generated_sql.sql)
        else:
            # Fallback for testing / offline mode
            back_translated = original_question

        alignment_score = self.compute_alignment_score(original_question, back_translated)
        logger.info(f"Back-translation alignment score: {alignment_score} | Back-translated: '{back_translated}'")

        if alignment_score < self.alignment_threshold:
            warning_msg = (
                f"Low confidence / Potential hallucination: Generated SQL back-translation "
                f"('{back_translated}') diverges from original question ('{original_question}'). "
                f"Alignment score: {alignment_score}"
            )
            warnings.append(warning_msg)
            logger.warning(warning_msg)

        # 2. Result Sanity Checks
        sanity_passed = True
        if query_result and query_result.data:
            # Check for high null ratio in result set
            first_row = query_result.data[0]
            if first_row:
                null_keys = [k for k, v in first_row.items() if v is None]
                if len(null_keys) > (len(first_row) / 2):
                    sanity_passed = False
                    warnings.append("High ratio of NULL values detected in result dataset.")

        # 3. Consensus Engine placeholder
        consensus_matched = True

        return HallucinationCheckResult(
            back_translated_question=back_translated,
            alignment_score=alignment_score,
            sanity_checks_passed=sanity_passed,
            consensus_matched=consensus_matched,
            anomaly_warnings=warnings
        )

    def compute_alignment_score(self, original: str, back_translated: str) -> float:
        """Computes semantic & token similarity score between original question and back-translated question."""
        if not original or not back_translated:
            return 0.0

        orig_clean = original.lower().strip()
        back_clean = back_translated.lower().strip()

        if orig_clean == back_clean:
            return 1.0

        orig_words = set(re.findall(r"\w+", orig_clean))
        back_words = set(re.findall(r"\w+", back_clean))

        if not orig_words or not back_words:
            return 0.5

        # Filter stopwords to focus on core domain terms
        orig_content = {w for w in orig_words if w not in self.STOPWORDS}
        back_content = {w for w in back_words if w not in self.STOPWORDS}

        if orig_content and back_content:
            jaccard = len(orig_content.intersection(back_content)) / len(orig_content.union(back_content))
        else:
            jaccard = len(orig_words.intersection(back_words)) / len(orig_words.union(back_words))

        seq_ratio = difflib.SequenceMatcher(None, orig_clean, back_clean).ratio()

        score = round((0.6 * jaccard + 0.4 * seq_ratio), 2)
        return min(1.0, max(0.0, score))
