"""Dynamic prompt constructor for assembling filtered schema context, foreign keys, sample values, business glossary terms, and few-shot examples."""

from src.domain.entities.schema import DatabaseSchema
from src.domain.entities.prompt import FewShotExample, BusinessTerm
from src.infrastructure.llm.few_shot_repository import FewShotRepository
from src.infrastructure.llm.glossary_repository import BusinessGlossaryRepository


class DynamicPromptBuilder:
    """Assembles rich, production-grade context prompts for LLM Text-to-SQL generation.
    
    Includes:
    - Relevant database schema (tables, data types, PKs, FKs, column comments)
    - Categorical sample values for string/enum disambiguation
    - Relevant business glossary terms & metric expressions
    - 3-5 few-shot question-to-SQL example pairs tailored to the query domain
    - Explicit PostgreSQL dialect rules and security constraints
    """

    def __init__(
        self,
        few_shot_repo: FewShotRepository | None = None,
        glossary_repo: BusinessGlossaryRepository | None = None,
        dialect: str = "PostgreSQL"
    ) -> None:
        self.few_shot_repo = few_shot_repo or FewShotRepository()
        self.glossary_repo = glossary_repo or BusinessGlossaryRepository()
        self.dialect = dialect

    def build_prompt(
        self,
        question: str,
        schema: DatabaseSchema,
        few_shots: list[FewShotExample] | list[dict] | None = None,
        glossary_terms: list[BusinessTerm] | None = None
    ) -> str:
        """Constructs system prompt containing schema definition, glossary rules, guidelines, and 3-5 few-shots."""
        # 1. Format Schema Context (Tables, Columns, PKs, FKs, Categorical Samples, Descriptions)
        schema_context = schema.to_prompt_str()

        # 2. Extract or Resolve Business Glossary Terms
        if glossary_terms is None:
            glossary_terms = self.glossary_repo.find_matching_terms(question)

        glossary_context = ""
        if glossary_terms:
            glossary_lines = ["### BUSINESS GLOSSARY & METRIC DEFINITIONS:"]
            for g_term in glossary_terms:
                line = f"- **{g_term.term}**: {g_term.definition}"
                if g_term.sql_expression:
                    line += f" (Suggested SQL: `{g_term.sql_expression}`)"
                glossary_lines.append(line)
            glossary_context = "\n".join(glossary_lines) + "\n\n"

        # 3. Resolve Few-Shot Examples (3 to 5 pairs)
        resolved_shots: list[FewShotExample] = []
        if few_shots:
            for s in few_shots:
                if isinstance(s, FewShotExample):
                    resolved_shots.append(s)
                elif isinstance(s, dict):
                    resolved_shots.append(
                        FewShotExample(question=s["question"], sql=s["sql"], explanation=s.get("explanation"))
                    )
        else:
            resolved_shots = self.few_shot_repo.get_relevant_examples(question, limit=4)

        few_shot_lines = ["### FEW-SHOT EXAMPLES (QUESTION-TO-SQL PAIRS):"]
        for shot in resolved_shots:
            few_shot_lines.append(f"Q: {shot.question}")
            few_shot_lines.append(f"SQL: {shot.sql}")
            if shot.explanation:
                few_shot_lines.append(f"Explanation: {shot.explanation}")
            few_shot_lines.append("")
        few_shot_context = "\n".join(few_shot_lines).strip()

        # 4. Construct System Prompt
        prompt = f"""You are an expert {self.dialect} Data Engineer. Your task is to translate the user's natural language question into a valid, highly efficient {self.dialect} SQL query based strictly on the schema provided below.

### DATABASE SCHEMA:
{schema_context}

{glossary_context}{few_shot_context}

### EXECUTION & SAFETY RULES:
1. Dialect: Use standard {self.dialect} syntax. Use DATE_TRUNC, INTERVAL, or ILIKE when appropriate.
2. Read-Only Policy: Generate ONLY SELECT queries. NEVER generate DDL or DML statements (CREATE, DROP, ALTER, INSERT, UPDATE, DELETE, TRUNCATE, GRANT).
3. Explicit Aliases: Always assign explicit column aliases for aggregated functions (e.g., `SUM(amount) AS total_revenue`).
4. Disambiguation: Use exact string values from the categorical sample values provided in the schema whenever filtering categorical text columns (e.g. status = 'completed').
5. Subquery Limits: Prefer clean JOINs or CTEs (WITH clauses) over deeply nested subqueries (max 3 levels).
6. Row Limit: If the user asks for top/limit or list without specifying count, append `LIMIT 1000`.
7. Explicit Ambiguity Handling: If the question maps to multiple distinct interpretations (e.g., 'revenue' could mean Gross Revenue vs Net Revenue, or 'top users' could mean by order count vs total spend), set `is_ambiguous = true` and return a list of `clarification_options` with labels, descriptions, and example queries for each interpretation instead of guessing.

USER QUESTION: {question}
"""
        return prompt.strip()
