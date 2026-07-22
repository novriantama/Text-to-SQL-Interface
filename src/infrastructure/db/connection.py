"""Database connection factory using SQLAlchemy."""

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from src.core.config import settings


def get_db_engine(uri: str | None = None) -> Engine:
    """Returns SQLAlchemy engine instance with read-only connection pool settings."""
    db_uri = uri or settings.READONLY_DB_URI
    return create_engine(
        db_uri,
        pool_pre_ping=True,
        execution_options={"isolation_level": "AUTOCOMMIT"}
    )
