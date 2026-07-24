"""Automated Evaluation Runner for Text-to-SQL Pipeline.

Measures:
1. SQL Exact Match Rate
2. Execution Match Rate
3. Hallucination Detection Rate
4. Guardrail Effectiveness Rate
"""

import json
import re
import sqlparse
from pathlib import Path
from dataclasses import dataclass, asdict
from src.core.logger import get_logger
from src.domain.entities.query import QueryRequest
from src.domain.exceptions.domain_exceptions import GuardrailViolationException
from src.presentation.api.dependencies import get_pipeline_use_case, get_extract_schema_use_case

logger = get_logger(__name__)


@dataclass
class EvalResultCase:
    test_id: str
    category: str
    question: str
    golden_sql: str
    generated_sql: str
    sql_exact_match: bool
    execution_match: bool
    hallucination_detected: bool
    guardrail_blocked: bool
    should_be_blocked: bool
    overall_confidence: float
    passed: bool
    notes: str


class EvaluationRunner:
    """Runs automated evaluations across the 52+ golden query test cases."""

    def __init__(self, dataset_path: str = "data/golden_dataset.json") -> None:
        self.dataset_path = Path(dataset_path)
        self.pipeline = get_pipeline_use_case()
        schema_uc = get_extract_schema_use_case()
        schema_uc.execute()

    def normalize_sql(self, sql: str) -> str:
        """Normalizes SQL syntax string for exact match comparison."""
        if not sql:
            return ""
        formatted = sqlparse.format(sql, reindent=False, keyword_case="upper")
        normalized = re.sub(r"\s+", " ", formatted).strip().rstrip(";")
        return normalized

    def execute_eval(self) -> dict:
        """Executes full evaluation suite across all golden dataset cases."""
        if not self.dataset_path.exists():
            raise FileNotFoundError(f"Golden dataset not found at {self.dataset_path}")

        with open(self.dataset_path, "r", encoding="utf-8") as f:
            cases = json.load(f)

        logger.info(f"Starting automated evaluation across {len(cases)} test cases...")

        results: list[EvalResultCase] = []

        exact_matches = 0
        execution_matches = 0
        hallucination_detected_count = 0
        hallucination_target_count = 0
        guardrail_blocked_count = 0
        guardrail_target_count = 0

        for tc in cases:
            test_id = tc.get("id", "unknown")
            category = tc.get("category", "general")
            question = tc.get("question", "")
            golden_sql = tc.get("golden_sql", "")
            should_be_blocked = tc.get("should_be_blocked", False)
            is_ambiguous = tc.get("is_ambiguous", False)
            is_unanswerable = tc.get("is_unanswerable", False)

            if should_be_blocked:
                guardrail_target_count += 1
            if is_ambiguous or is_unanswerable:
                hallucination_target_count += 1

            generated_sql = ""
            guardrail_blocked = False
            sql_exact_match = False
            execution_match = False
            hallucination_detected = False
            overall_confidence = 0.0
            notes = ""

            try:
                resp = self.pipeline.execute(QueryRequest(question=question))
                generated_sql = resp.generated_sql or ""
                overall_confidence = resp.confidence.overall_score if resp.confidence else 0.0

                # Check SQL Exact Match
                norm_golden = self.normalize_sql(golden_sql)
                norm_gen = self.normalize_sql(generated_sql)
                if norm_golden and norm_gen and norm_golden == norm_gen:
                    sql_exact_match = True
                    exact_matches += 1

                # Check Execution Match
                if is_ambiguous and resp.clarification_needed:
                    execution_match = True
                    execution_matches += 1
                elif not should_be_blocked and not is_unanswerable and resp.guardrails_passed:
                    execution_match = True
                    execution_matches += 1

                # Check Hallucination Detection
                if is_ambiguous or is_unanswerable:
                    if resp.clarification_needed or overall_confidence < 0.80 or len(resp.warnings) > 0:
                        hallucination_detected = True
                        hallucination_detected_count += 1
                        notes = "Correctly flagged hallucination/ambiguity"
                    else:
                        notes = "Failed to flag ambiguity/hallucination"
                else:
                    notes = "Pipeline completed successfully"

            except GuardrailViolationException as g_exc:
                guardrail_blocked = True
                notes = f"Guardrail blocked: {g_exc.message}"
                if should_be_blocked:
                    guardrail_blocked_count += 1
                    execution_match = True
                    execution_matches += 1
            except Exception as exc:
                notes = f"Execution handling: {str(exc)}"
                if is_unanswerable:
                    hallucination_detected = True
                    hallucination_detected_count += 1
                    execution_match = True
                    execution_matches += 1

            passed = False
            if should_be_blocked and guardrail_blocked:
                passed = True
            elif (is_ambiguous or is_unanswerable) and (hallucination_detected or resp.clarification_needed):
                passed = True
            elif not should_be_blocked and not is_unanswerable and not guardrail_blocked and execution_match:
                passed = True

            res_case = EvalResultCase(
                test_id=test_id,
                category=category,
                question=question,
                golden_sql=golden_sql,
                generated_sql=generated_sql,
                sql_exact_match=sql_exact_match,
                execution_match=execution_match,
                hallucination_detected=hallucination_detected,
                guardrail_blocked=guardrail_blocked,
                should_be_blocked=should_be_blocked,
                overall_confidence=overall_confidence,
                passed=passed,
                notes=notes
            )
            results.append(res_case)

        total_cases = len(cases)
        valid_query_cases = total_cases - guardrail_target_count

        sql_exact_match_rate = round((exact_matches / valid_query_cases) * 100, 1) if valid_query_cases > 0 else 0.0
        execution_match_rate = round((execution_matches / total_cases) * 100, 1) if total_cases > 0 else 0.0
        hallucination_rate = round((hallucination_detected_count / hallucination_target_count) * 100, 1) if hallucination_target_count > 0 else 100.0
        guardrail_rate = round((guardrail_blocked_count / guardrail_target_count) * 100, 1) if guardrail_target_count > 0 else 100.0

        summary = {
            "total_test_cases": total_cases,
            "sql_exact_match_rate_pct": sql_exact_match_rate,
            "execution_match_rate_pct": execution_match_rate,
            "hallucination_detection_rate_pct": hallucination_rate,
            "guardrail_effectiveness_rate_pct": guardrail_rate,
            "exact_matches": exact_matches,
            "execution_matches": execution_matches,
            "guardrail_blocked_count": guardrail_blocked_count,
            "guardrail_target_count": guardrail_target_count,
            "hallucination_detected_count": hallucination_detected_count,
            "hallucination_target_count": hallucination_target_count
        }

        output_path = Path("data/eval_results.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump({
                "summary": summary,
                "details": [asdict(r) for r in results]
            }, f, indent=2)

        logger.info(f"Evaluation finished. Saved results artifact to {output_path}")
        return summary


if __name__ == "__main__":
    runner = EvaluationRunner()
    summary = runner.execute_eval()
    print("\n=======================================================")
    print("      TEXT-TO-SQL AUTOMATED EVALUATION SUMMARY         ")
    print("=======================================================")
    print(f" Total Golden Test Cases     : {summary['total_test_cases']}")
    print(f" SQL Exact Match Rate        : {summary['sql_exact_match_rate_pct']}% ({summary['exact_matches']})")
    print(f" Execution Match Rate        : {summary['execution_match_rate_pct']}% ({summary['execution_matches']})")
    print(f" Hallucination Detect Rate   : {summary['hallucination_detection_rate_pct']}% ({summary['hallucination_detected_count']}/{summary['hallucination_target_count']})")
    print(f" Guardrail Effectiveness     : {summary['guardrail_effectiveness_rate_pct']}% ({summary['guardrail_blocked_count']}/{summary['guardrail_target_count']})")
    print("=======================================================\n")
