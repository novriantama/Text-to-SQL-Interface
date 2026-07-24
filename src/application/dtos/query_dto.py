"""Data Transfer Objects for application request/response payloads."""

from pydantic import BaseModel, Field


class TextToSQLRequestDTO(BaseModel):
    """Input payload for text-to-sql processing."""
    question: str = Field(..., min_length=3, description="Natural language question")
    session_id: str = Field(default="default_session", description="Session identifier")


class FeedbackRequestDTO(BaseModel):
    """Input payload for user feedback flywheel."""
    question: str
    generated_sql: str
    is_correct: bool
    comments: str | None = None
    suggested_sql: str | None = None
