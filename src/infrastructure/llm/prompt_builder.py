"""Dynamic prompt constructor for assembling schema context, few-shot examples, and disambiguation rules."""

from src.domain.entities.schema import DatabaseSchema


class DynamicPromptBuilder:
    """Assembles rich context prompts for LLM Text-to-SQL generation."""

    def build_prompt(
        self,
        question: str,
        schema: DatabaseSchema,
        few_shots: list[dict] | None = None
    ) -> str:
        """Constructs system prompt containing schema definition, guidelines, and few-shots."""
        schema_context = schema.to_prompt_str()
        
        few_shot_context = ""
        if few_shots:
            few_shot_context = "### FEW-SHOT EXAMPLES:\n"
            for shot in few_shots:
                few_shot_context += f"Q: {shot['question']}\nSQL: {shot['sql']}\n\n"

        prompt = f"""You are an expert SQL Data Engineer. Translate the user's question into a valid SQL query based on the database schema provided below.

### DATABASE SCHEMA:
{schema_context}

{few_shot_context}
### RULES:
1. Return ONLY SELECT queries. Never generate DDL or DML statements (CREATE, DROP, INSERT, UPDATE, DELETE).
2. If the user question is ambiguous, specify assumptions clearly in the explanation field.
3. Always include explicit column aliases for aggregation functions.

USER QUESTION: {question}
"""
        return prompt
