"""Schema domain entities for representing database tables, columns, and relationships."""

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ColumnSchema:
    """Represents metadata for a single database column."""
    name: str
    data_type: str
    is_primary_key: bool = False
    is_foreign_key: bool = False
    foreign_table: str | None = None
    foreign_column: str | None = None
    sample_values: list[Any] = field(default_factory=list)
    description: str | None = None


@dataclass(frozen=True)
class TableSchema:
    """Represents metadata for a database table."""
    name: str
    columns: list[ColumnSchema]
    description: str | None = None
    row_count_estimate: int | None = None

    def get_column_names(self) -> list[str]:
        """Return list of column names."""
        return [col.name for col in self.columns]


@dataclass
class DatabaseSchema:
    """Represents full or filtered database schema definition."""
    tables: dict[str, TableSchema] = field(default_factory=dict)

    def to_prompt_str(self) -> str:
        """Converts schema metadata into readable string prompt context."""
        lines = []
        for table_name, table in self.tables.items():
            lines.append(f"Table: {table_name}")
            for col in table.columns:
                col_str = f"  - {col.name} ({col.data_type})"
                if col.is_primary_key:
                    col_str += " [PRIMARY KEY]"
                if col.is_foreign_key:
                    col_str += f" [FK -> {col.foreign_table}.{col.foreign_column}]"
                lines.append(col_str)
        return "\n".join(lines)
