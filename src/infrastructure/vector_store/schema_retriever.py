"""Embedding-based schema relevance retriever using vector cosine similarity and FK graph expansion."""

import math
import re
from collections import Counter
from src.core.logger import get_logger
from src.domain.ports.vector_store_port import VectorStorePort
from src.domain.entities.schema import DatabaseSchema, TableSchema

logger = get_logger(__name__)

# Optional sentence-transformers support
try:
    from sentence_transformers import SentenceTransformer
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False


class EmbeddingSchemaRetriever(VectorStorePort):
    """Semantic schema relevance filter implementing VectorStorePort.
    
    Features:
    - Embeds table definitions (name, description, columns, categorical samples)
    - Embeds user question into dense vector space
    - Computes Cosine Similarity scores
    - Filters tables above similarity threshold (default 0.35)
    - Applies Foreign Key graph expansion to preserve JOIN integrity
    - Uses sentence-transformers (all-MiniLM-L6-v2) or built-in TF-IDF vectorizer fallback
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2", min_tables_limit: int = 1) -> None:
        self.model_name = model_name
        self.min_tables_limit = min_tables_limit
        self._model = None
        self._table_vectors: dict[str, list[float]] = {}
        self._cached_schema_id: str | None = None

        if HAS_SENTENCE_TRANSFORMERS:
            try:
                self._model = SentenceTransformer(self.model_name)
                logger.info(f"Loaded SentenceTransformer model '{self.model_name}' for schema embedding.")
            except Exception as err:
                logger.warning(f"Could not load SentenceTransformer model ({err}). Falling back to TF-IDF vectorizer.")

    def index_schema(self, schema: DatabaseSchema) -> None:
        """Computes and caches vector embeddings for each table in the schema."""
        self._table_vectors.clear()
        for table_name, table in schema.tables.items():
            text_repr = self._build_table_text_representation(table)
            self._table_vectors[table_name] = self._embed_text(text_repr)
        logger.info(f"Indexed embeddings for {len(self._table_vectors)} database tables.")

    def filter_schema(self, question: str, full_schema: DatabaseSchema, threshold: float = 0.35) -> DatabaseSchema:
        """Filters full schema to tables exceeding similarity threshold with FK graph expansion."""
        if not full_schema.tables:
            return full_schema

        # Re-index if schema vectors not populated
        if not self._table_vectors or len(self._table_vectors) != len(full_schema.tables):
            self.index_schema(full_schema)

        # 1. Embed Question & Compute Similarities
        q_vector = self._embed_text(question)
        scores: dict[str, float] = {}

        for table_name in full_schema.tables:
            t_vector = self._table_vectors.get(table_name, [])
            sim = self._cosine_similarity(q_vector, t_vector)
            scores[table_name] = sim

        logger.debug(f"Schema similarity scores for '{question}': {scores}")

        # 2. Select Tables Exceeding Threshold
        selected_tables: set[str] = {
            t_name for t_name, sim in scores.items() if sim >= threshold
        }

        # Fallback: If no table meets threshold, take the highest scoring table
        if not selected_tables:
            top_table = max(scores.items(), key=lambda x: x[1])[0]
            selected_tables.add(top_table)

        # 3. Foreign Key Graph Expansion
        # Always include FK target tables for selected tables to preserve JOIN integrity
        expanded_tables = set(selected_tables)
        for table_name in list(selected_tables):
            table = full_schema.tables.get(table_name)
            if not table:
                continue
            for col in table.columns:
                if col.is_foreign_key and col.foreign_table and col.foreign_table in full_schema.tables:
                    expanded_tables.add(col.foreign_table)

        # Reverse FK check for linked child tables with reasonable relevance
        for t_name, table in full_schema.tables.items():
            if t_name not in expanded_tables:
                for col in table.columns:
                    if col.is_foreign_key and col.foreign_table in selected_tables:
                        if scores.get(t_name, 0.0) >= (threshold * 0.3):
                            expanded_tables.add(t_name)

        # 4. Construct Filtered Schema
        filtered_schema = DatabaseSchema()
        for t_name in expanded_tables:
            filtered_schema.tables[t_name] = full_schema.tables[t_name]

        logger.info(
            f"Filtered schema from {len(full_schema.tables)} to {len(filtered_schema.tables)} tables for question."
        )
        return filtered_schema

    def _build_table_text_representation(self, table: TableSchema) -> str:
        """Converts table metadata into a rich textual document for vector embedding."""
        parts = [f"Table name: {table.name}."]
        if table.description:
            parts.append(f"Description: {table.description}.")

        col_names = [col.name for col in table.columns]
        parts.append(f"Columns: {', '.join(col_names)}.")

        col_descs = [f"{col.name} ({col.description})" for col in table.columns if col.description]
        if col_descs:
            parts.append(f"Column descriptions: {'; '.join(col_descs)}.")

        samples = []
        for col in table.columns:
            if col.sample_values:
                samples.append(f"{col.name}: {', '.join(map(str, col.sample_values))}")
        if samples:
            parts.append(f"Sample values: {'; '.join(samples)}.")

        return " ".join(parts)

    def _embed_text(self, text_input: str) -> list[float]:
        """Generates embedding vector using SentenceTransformer or TF-IDF vectorizer fallback."""
        if self._model is not None:
            embedding = self._model.encode(text_input, convert_to_numpy=True)
            return embedding.tolist()
        return self._tfidf_embed(text_input)

    def _tfidf_embed(self, text_input: str) -> list[float]:
        """Simple TF-IDF token vectorizer fallback."""
        words = re.findall(r"\w+", text_input.lower())
        counts = Counter(words)
        total = len(words) or 1
        # Normalize term frequencies
        vector = [counts[w] / total for w in set(words)]
        return vector

    def _cosine_similarity(self, vec1: list[float], vec2: list[float]) -> float:
        """Computes Cosine Similarity score between two vectors."""
        if not vec1 or not vec2:
            return 0.0
        
        # Handle differing lengths for fallback vectors
        min_len = min(len(vec1), len(vec2))
        if min_len == 0:
            return 0.0

        v1 = vec1[:min_len]
        v2 = vec2[:min_len]

        dot_product = sum(a * b for a, b in zip(v1, v2))
        norm1 = math.sqrt(sum(a * a for a in v1))
        norm2 = math.sqrt(sum(b * b for b in v2))

        if norm1 == 0.0 or norm2 == 0.0:
            return 0.0

        return dot_product / (norm1 * norm2)
