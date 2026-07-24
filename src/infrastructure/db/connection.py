"""Database connection factory using SQLAlchemy."""

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from src.core.config import settings
from src.core.logger import get_logger

logger = get_logger(__name__)


def get_db_engine(uri: str | None = None) -> Engine:
    """Returns SQLAlchemy engine instance with read-only connection pool settings.
    
    Falls back gracefully to local SQLite database if PostgreSQL driver is unavailable locally.
    """
    db_uri = uri or settings.READONLY_DB_URI

    try:
        engine = create_engine(
            db_uri,
            pool_pre_ping=True,
            execution_options={"isolation_level": "AUTOCOMMIT"}
        )
        # Test connection ping
        with engine.connect() as conn:
            pass
        return engine
    except Exception as err:
        if "postgresql" in db_uri:
            fallback_uri = "sqlite:///./data/sample_db.sqlite"
            logger.warning(
                f"PostgreSQL connection failed ({err}). Falling back to local SQLite database at '{fallback_uri}' for local execution."
            )
            return create_engine(
                fallback_uri,
                pool_pre_ping=True,
                execution_options={"isolation_level": "AUTOCOMMIT"}
            )
        raise err
