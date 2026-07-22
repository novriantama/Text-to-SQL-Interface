"""SQLAlchemy schema extractor implementing automatic database table, column, PK/FK, comment, and categorical sample value introspection."""

from typing import Any
from sqlalchemy import inspect, text, String, Enum
from sqlalchemy.engine import Engine
from src.core.logger import get_logger
from src.domain.entities.schema import DatabaseSchema, TableSchema, ColumnSchema

logger = get_logger(__name__)


class SQLAlchemySchemaExtractor:
    """Introspects database schema metadata using SQLAlchemy Inspector API.
    
    Supports PostgreSQL and other relational engines by programmatically extracting:
    - Table definitions & table comments
    - Column data types, primary keys, and foreign key relationships
    - Column comments/descriptions
    - Sample values for categorical columns (e.g., status, category, type)
    - Estimated row counts
    """

    CATEGORICAL_TYPE_KEYWORDS = ("varchar", "char", "text", "enum", "string", "citext")

    def __init__(
        self,
        engine: Engine,
        sample_limit: int = 5,
        extract_samples: bool = True,
        schema_name: str | None = None
    ) -> None:
        self.engine = engine
        self.sample_limit = sample_limit
        self.extract_samples = extract_samples
        self.schema_name = schema_name

    def extract(self) -> DatabaseSchema:
        """Introspects full database schema structure with categorical samples and metadata."""
        inspector = inspect(self.engine)
        schema = DatabaseSchema()

        table_names = inspector.get_table_names(schema=self.schema_name)
        logger.info(f"Extracting schema for {len(table_names)} tables (schema: '{self.schema_name or 'default'}')...")

        with self.engine.connect() as conn:
            for table_name in table_names:
                table_schema = self._introspect_table(inspector, conn, table_name)
                schema.tables[table_name] = table_schema

        return schema

    def _introspect_table(self, inspector: Any, conn: Any, table_name: str) -> TableSchema:
        """Introspects a single table's metadata."""
        # 1. Primary keys & Foreign keys map
        pk_constraint = inspector.get_pk_constraint(table_name, schema=self.schema_name)
        pk_cols = set(pk_constraint.get("constrained_columns", []))

        fkey_map = {}
        for fk in inspector.get_foreign_keys(table_name, schema=self.schema_name):
            for local_col, ref_col in zip(fk["constrained_columns"], fk["referred_columns"]):
                fkey_map[local_col] = (fk["referred_table"], ref_col)

        # 2. Table Comment
        table_comment = None
        try:
            comment_dict = inspector.get_table_comment(table_name, schema=self.schema_name)
            table_comment = comment_dict.get("text")
        except Exception:
            table_comment = None

        # 3. Row Count Estimate
        row_count_estimate = self._get_row_count_estimate(conn, table_name)

        # 4. Columns Introspection
        columns = []
        raw_columns = inspector.get_columns(table_name, schema=self.schema_name)
        for col in raw_columns:
            col_name = col["name"]
            type_str = str(col["type"])
            is_pk = col_name in pk_cols
            is_fk = col_name in fkey_map
            ref_table, ref_col = fkey_map.get(col_name, (None, None))
            col_comment = col.get("comment")

            # Check if column is categorical and fetch sample values
            sample_vals = []
            if self.extract_samples and not is_pk and self._is_categorical_type(type_str, col["type"]):
                sample_vals = self._fetch_sample_values(conn, table_name, col_name)

            columns.append(
                ColumnSchema(
                    name=col_name,
                    data_type=type_str,
                    is_primary_key=is_pk,
                    is_foreign_key=is_fk,
                    foreign_table=ref_table,
                    foreign_column=ref_col,
                    sample_values=sample_vals,
                    description=col_comment
                )
            )

        return TableSchema(
            name=table_name,
            columns=columns,
            description=table_comment,
            row_count_estimate=row_count_estimate
        )

    def _is_categorical_type(self, type_str: str, type_obj: Any) -> bool:
        """Determines if a column data type is likely categorical (text, varchar, enum)."""
        if isinstance(type_obj, (String, Enum)):
            return True
        type_lower = type_str.lower()
        return any(keyword in type_lower for keyword in self.CATEGORICAL_TYPE_KEYWORDS)

    def _fetch_sample_values(self, conn: Any, table_name: str, column_name: str) -> list[Any]:
        """Fetches up to sample_limit distinct non-null values for categorical columns."""
        quoted_table = f'"{self.schema_name}"."{table_name}"' if self.schema_name else f'"{table_name}"'
        quoted_col = f'"{column_name}"'
        query_str = f"SELECT DISTINCT {quoted_col} FROM {quoted_table} WHERE {quoted_col} IS NOT NULL LIMIT {self.sample_limit}"
        
        try:
            res = conn.execute(text(query_str))
            samples = [row[0] for row in res.fetchall() if row[0] is not None]
            return samples
        except Exception as exc:
            logger.debug(f"Could not fetch sample values for {table_name}.{column_name}: {exc}")
            return []

    def _get_row_count_estimate(self, conn: Any, table_name: str) -> int | None:
        """Fetches estimated row count using PostgreSQL system catalogs or fast count query."""
        try:
            if "postgresql" in self.engine.name:
                schema = self.schema_name or "public"
                pg_query = text(
                    "SELECT reltuples::bigint FROM pg_class "
                    "JOIN pg_namespace ON pg_namespace.oid = pg_class.relnamespace "
                    "WHERE relname = :table_name AND nspname = :schema_name"
                )
                res = conn.execute(pg_query, {"table_name": table_name, "schema_name": schema}).fetchone()
                if res and res[0] is not None and res[0] >= 0:
                    return int(res[0])
            
            # Fallback for small tables or non-Postgres engines
            quoted_table = f'"{self.schema_name}"."{table_name}"' if self.schema_name else f'"{table_name}"'
            res = conn.execute(text(f"SELECT COUNT(*) FROM {quoted_table}")).fetchone()
            if res:
                return int(res[0])
        except Exception:
            pass
        return None
