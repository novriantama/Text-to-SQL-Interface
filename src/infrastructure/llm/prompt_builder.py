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

        # 3. Resolve Few-Shot Examples (up to 2 pairs)
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
            resolved_shots = self.few_shot_repo.get_relevant_examples(question, limit=2)

        few_shot_lines = ["### FEW-SHOT EXAMPLES:"]
        for shot in resolved_shots:
            few_shot_lines.append(f"Q: {shot.question}\nSQL: {shot.sql}")
        few_shot_context = "\n\n".join(few_shot_lines).strip()

        # 4. Construct Concise System Prompt
        prompt = f"""You are a {self.dialect} Data Engineer. Translate the user's question into a valid, efficient {self.dialect} SELECT query strictly using the schema below.

### DATABASE SCHEMA:
{schema_context}

{glossary_context}{few_shot_context}

### RULES:
1. Generate ONLY SELECT queries (read-only). Never DDL/DML.
2. Use explicit column aliases for aggregate expressions (e.g. `SUM(amount) AS total_revenue`).
3. Match categorical string values from schema samples.
4. Append `LIMIT 1000` unless explicit limit is provided.
5. If the question has multiple distinct business interpretations, set `is_ambiguous = true` and provide `clarification_options`.

USER QUESTION: {question}
"""
        return prompt.strip()
