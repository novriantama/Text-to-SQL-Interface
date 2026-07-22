"""LLM Provider adapter using Anthropic Claude Sonnet & OpenAI with Instructor for structured output."""

from pydantic import BaseModel, Field
from src.core.config import settings
from src.core.logger import get_logger
from src.domain.ports.llm_port import LLMPort
from src.domain.entities.schema import DatabaseSchema
from src.domain.entities.query import GeneratedSQL
from src.infrastructure.llm.prompt_builder import DynamicPromptBuilder

logger = get_logger(__name__)

# Optional Anthropic / OpenAI / Instructor imports
try:
    import instructor
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False


class LLMSQLOutputSchema(BaseModel):
    """Pydantic schema enforcing structured JSON return from LLM."""
    sql: str = Field(description="Generated valid PostgreSQL query string")
    explanation: str = Field(description="Natural language explanation of what the query does")
    confidence_estimate: float = Field(description="Model confidence score between 0.0 and 1.0")
    accessed_tables: list[str] = Field(default_factory=list, description="List of tables accessed")


class InstructorLLMAdapter(LLMPort):
    """LLM client adapter implementing structured output generation and back-translation via Anthropic Claude Sonnet."""

    def __init__(self) -> None:
        self.prompt_builder = DynamicPromptBuilder(dialect="PostgreSQL")
        self._client = None
        self._setup_client()

    def _setup_client(self) -> None:
        """Initializes the Instructor client for Anthropic or OpenAI based on settings."""
        if settings.LLM_PROVIDER == "anthropic":
            if HAS_ANTHROPIC and settings.ANTHROPIC_API_KEY:
                raw_client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
                self._client = instructor.from_anthropic(raw_client)
                logger.info(f"Initialized Anthropic Instructor client using model '{settings.ANTHROPIC_MODEL}'.")
            else:
                logger.info("Anthropic API key or library not loaded. Mock mode active.")
        elif settings.LLM_PROVIDER == "openai":
            if HAS_OPENAI and settings.OPENAI_API_KEY:
                raw_client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
                self._client = instructor.from_openai(raw_client)
                logger.info(f"Initialized OpenAI Instructor client using model '{settings.OPENAI_MODEL}'.")

    def generate_sql(
        self,
        question: str,
        schema_context: DatabaseSchema,
        few_shots: list[dict] | None = None
    ) -> GeneratedSQL:
        """Generates structured SQL query using Anthropic Claude Sonnet structured output."""
        prompt = self.prompt_builder.build_prompt(question, schema_context, few_shots)

        if self._client is None:
            # Fallback mock generator when API keys are omitted in development/test
            table_name = list(schema_context.tables.keys())[0] if schema_context.tables else "orders"
            logger.warning("Executing in mock LLM mode (No active API key set).")
            return GeneratedSQL(
                sql=f"SELECT * FROM {table_name} LIMIT 100;",
                explanation=f"Generated fallback query for question: '{question}' against '{table_name}'.",
                confidence_estimate=0.88,
                accessed_tables=[table_name]
            )

        try:
            if settings.LLM_PROVIDER == "anthropic":
                res: LLMSQLOutputSchema = self._client.messages.create(
                    model=settings.ANTHROPIC_MODEL,
                    max_tokens=1024,
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    response_model=LLMSQLOutputSchema
                )
            else:
                res = self._client.chat.completions.create(
                    model=settings.OPENAI_MODEL,
                    response_model=LLMSQLOutputSchema,
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )

            return GeneratedSQL(
                sql=res.sql,
                explanation=res.explanation,
                confidence_estimate=res.confidence_estimate,
                accessed_tables=res.accessed_tables
            )
        except Exception as err:
            logger.error(f"Error invoking LLM structured output: {err}")
            table_name = list(schema_context.tables.keys())[0] if schema_context.tables else "orders"
            return GeneratedSQL(
                sql=f"SELECT * FROM {table_name} LIMIT 100;",
                explanation=f"Fallback query due to LLM error: {err}",
                confidence_estimate=0.50,
                accessed_tables=[table_name]
            )

    def back_translate_sql(self, sql_query: str) -> str:
        """Translates SQL query back into an English question for hallucination alignment verification."""
        if self._client is None:
            return f"What data is selected by: '{sql_query}'?"

        prompt = f"Explain in a single, simple English question what data this SQL query retrieves: `{sql_query}`"
        try:
            if settings.LLM_PROVIDER == "anthropic":
                resp = self._client.messages.create(
                    model=settings.ANTHROPIC_MODEL,
                    max_tokens=256,
                    messages=[{"role": "user", "content": prompt}]
                )
                return resp.content[0].text.strip()
            else:
                resp = self._client.chat.completions.create(
                    model=settings.OPENAI_MODEL,
                    messages=[{"role": "user", "content": prompt}]
                )
                return resp.choices[0].message.content.strip()
        except Exception:
            return f"What data is selected by: '{sql_query}'?"
