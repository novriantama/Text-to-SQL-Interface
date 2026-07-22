"""Application Configuration powered by Pydantic Settings."""

from typing import Literal
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Production settings container enforcing type validation."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Application settings
    APP_ENV: str = Field(default="development", description="Application environment")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    SECRET_KEY: str = Field(default="dev-secret-key-32-chars-minimum-len", description="Application secret key")

    # Database Configuration
    DB_DRIVER: str = Field(default="sqlite", description="Database driver (postgresql/duckdb/sqlite)")
    READONLY_DB_URI: str = Field(
        default="sqlite:///./data/sample_db.sqlite",
        description="Database connection URI with read-only permissions"
    )

    # LLM Settings
    LLM_PROVIDER: Literal["openai", "anthropic"] = Field(default="anthropic", description="Active LLM provider")
    OPENAI_API_KEY: str = Field(default="", description="OpenAI API Key")
    OPENAI_MODEL: str = Field(default="gpt-4o", description="OpenAI LLM Model Name")
    ANTHROPIC_API_KEY: str = Field(default="", description="Anthropic API Key")
    ANTHROPIC_MODEL: str = Field(default="claude-3-5-sonnet-20241022", description="Anthropic Model Name")

    # Safety Guardrails Thresholds & Flags
    BLOCK_DDL: bool = Field(default=True, description="Enable blocking DDL (CREATE, ALTER, DROP, TRUNCATE, etc.)")
    BLOCK_DML_WRITES: bool = Field(default=True, description="Enable blocking DML writes (INSERT, UPDATE, DELETE, MERGE)")
    MAX_ROW_LIMIT: int = Field(default=1000, description="Max rows returned by any query")
    MAX_SUBQUERY_DEPTH: int = Field(default=3, description="Max subquery nesting levels allowed")
    MAX_EXPLAIN_COST: float = Field(default=50000.0, description="Max estimated query scan cost")
    ENABLE_GUARDRAIL_LOGGING: bool = Field(default=True, description="Log all blocked queries to audit log")

    # Vector Store Settings
    VECTOR_SIMILARITY_THRESHOLD: float = Field(
        default=0.35,
        description="Minimum similarity score for table schema selection"
    )


settings = Settings()
