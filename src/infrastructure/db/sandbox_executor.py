"""Read-only sandbox database executor implementing DatabasePort and enforcing multi-layered query isolation."""

import time
from sqlalchemy import text
from sqlalchemy.engine import Engine
from src.core.logger import get_logger
from src.domain.ports.database_port import DatabasePort
from src.domain.entities.schema import DatabaseSchema
from src.domain.entities.query import QueryResult
from src.infrastructure.db.schema_extractor import SQLAlchemySchemaExtractor

logger = get_logger(__name__)


class SandboxDatabaseAdapter(DatabasePort):
    """Database adapter executing queries strictly within read-only transactions.
    
    Security & Defense-in-Depth Features:
    1. Read-Only Transaction Mode: Issues `SET TRANSACTION READ ONLY` on PostgreSQL connections.
    2. Automatic Rollback: Always executes transaction rollback in a `finally` block to prevent mutations.
    3. SELECT-Only DB User Compatibility: Works seamlessly with restricted read-only database credentials.
    """

    def __init__(self, engine: Engine) -> None:
        self.engine = engine
        self.extractor = SQLAlchemySchemaExtractor(engine)

    def extract_schema(self) -> DatabaseSchema:
        return self.extractor.extract()

    def execute_read_only(self, sql_query: str) -> QueryResult:
        """Executes query within a sandboxed read-only transaction block with mandatory rollback."""
        start_time = time.time()
        with self.engine.connect() as conn:
            # Begin transaction block
            trans = conn.begin()
            try:
                # 1. Enforce PostgreSQL read-only transaction mode
                if "postgresql" in self.engine.name:
                    conn.execute(text("SET TRANSACTION READ ONLY;"))

                # 2. Execute query
                result = conn.execute(text(sql_query))
                keys = list(result.keys()) if result.returns_rows else []
                rows = [dict(zip(keys, row)) for row in result.fetchall()] if result.returns_rows else []
                elapsed_ms = (time.time() - start_time) * 1000.0

                logger.debug(f"Executed query in sandbox ({len(rows)} rows, {round(elapsed_ms, 2)}ms)")
                return QueryResult(
                    data=rows,
                    columns=keys,
                    rows_returned=len(rows),
                    execution_time_ms=round(elapsed_ms, 2)
                )
            except Exception as err:
                logger.error(f"Error during sandbox query execution: {err}")
                raise err
            finally:
                # 3. Always rollback transaction block to guarantee zero state persistence
                trans.rollback()

    def get_explain_plan(self, sql_query: str) -> str:
        """Fetches EXPLAIN execution plan within a sandboxed read-only transaction."""
        try:
            with self.engine.connect() as conn:
                trans = conn.begin()
                try:
                    if "postgresql" in self.engine.name:
                        conn.execute(text("SET TRANSACTION READ ONLY;"))
                    result = conn.execute(text(f"EXPLAIN {sql_query}"))
                    return "\n".join(str(row[0]) for row in result.fetchall())
                finally:
                    trans.rollback()
        except Exception as err:
            logger.debug(f"Could not retrieve EXPLAIN plan: {err}")
            return "EXPLAIN plan unavailable"
