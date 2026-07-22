"""Read-only sandbox database executor implementing DatabasePort."""

import time
from sqlalchemy import text
from sqlalchemy.engine import Engine
from src.domain.ports.database_port import DatabasePort
from src.domain.entities.schema import DatabaseSchema
from src.domain.entities.query import QueryResult
from src.infrastructure.db.schema_extractor import SQLAlchemySchemaExtractor


class SandboxDatabaseAdapter(DatabasePort):
    """Database adapter executing queries strictly within read-only transactions."""

    def __init__(self, engine: Engine) -> None:
        self.engine = engine
        self.extractor = SQLAlchemySchemaExtractor(engine)

    def extract_schema(self) -> DatabaseSchema:
        return self.extractor.extract()

    def execute_read_only(self, sql_query: str) -> QueryResult:
        start_time = time.time()
        with self.engine.connect() as conn:
            # Begin read-only transaction block
            trans = conn.begin()
            try:
                result = conn.execute(text(sql_query))
                keys = list(result.keys())
                rows = [dict(zip(keys, row)) for row in result.fetchall()]
                elapsed_ms = (time.time() - start_time) * 1000.0
                return QueryResult(
                    data=rows,
                    columns=keys,
                    rows_returned=len(rows),
                    execution_time_ms=round(elapsed_ms, 2)
                )
            finally:
                # Always rollback read-only transaction block
                trans.rollback()

    def get_explain_plan(self, sql_query: str) -> str:
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(f"EXPLAIN {sql_query}"))
                return "\n".join(str(row[0]) for row in result.fetchall())
        except Exception:
            return "EXPLAIN plan unavailable"
