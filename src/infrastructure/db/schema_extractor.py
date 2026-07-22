"""SQLAlchemy schema extractor implementing automatic table and column introspection."""

from sqlalchemy import inspect
from sqlalchemy.engine import Engine
from src.domain.entities.schema import DatabaseSchema, TableSchema, ColumnSchema


class SQLAlchemySchemaExtractor:
    """Introspects database schema metadata using SQLAlchemy Inspector API."""

    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    def extract(self) -> DatabaseSchema:
        """Introspects all tables, columns, data types, primary and foreign keys."""
        inspector = inspect(self.engine)
        schema = DatabaseSchema()

        for table_name in inspector.get_table_names():
            columns = []
            pk_constraint = inspector.get_pk_constraint(table_name)
            pk_cols = set(pk_constraint.get("constrained_columns", []))
            
            fkey_map = {}
            for fk in inspector.get_foreign_keys(table_name):
                for local_col, ref_col in zip(fk["constrained_columns"], fk["referred_columns"]):
                    fkey_map[local_col] = (fk["referred_table"], ref_col)

            for col in inspector.get_columns(table_name):
                col_name = col["name"]
                is_fk = col_name in fkey_map
                ref_table, ref_col = fkey_map.get(col_name, (None, None))

                columns.append(
                    ColumnSchema(
                        name=col_name,
                        data_type=str(col["type"]),
                        is_primary_key=col_name in pk_cols,
                        is_foreign_key=is_fk,
                        foreign_table=ref_table,
                        foreign_column=ref_col
                    )
                )

            schema.tables[table_name] = TableSchema(
                name=table_name,
                columns=columns
            )

        return schema
