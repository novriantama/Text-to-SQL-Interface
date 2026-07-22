"""Use Case: Schema Extraction and Indexing."""

from src.core.logger import get_logger
from src.domain.entities.schema import DatabaseSchema
from src.domain.ports.database_port import DatabasePort
from src.domain.ports.vector_store_port import VectorStorePort

logger = get_logger(__name__)


class ExtractSchemaUseCase:
    """Extracts metadata from database and updates vector store index."""

    def __init__(self, db_port: DatabasePort, vector_store_port: VectorStorePort) -> None:
        self.db = db_port
        self.vector_store = vector_store_port

    def execute(self) -> DatabaseSchema:
        """Extracts schema and updates semantic index."""
        logger.info("Extracting database schema and refreshing vector index...")
        schema = self.db.extract_schema()
        self.vector_store.index_schema(schema)
        return schema
