"""FastAPI Web Application Entry Point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.core.config import settings
from src.presentation.api.v1.router import api_v1_router

app = FastAPI(
    title="Production Text-to-SQL API Interface",
    description="Natural language to SQL interface with guardrails and hallucination detection.",
    version="0.1.0",
)

# Enable CORS for Streamlit / React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_v1_router)


@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "environment": settings.APP_ENV}
