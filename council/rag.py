"""
DuckDB Local Hybrid RAG Engine for AI Consilium
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional
import duckdb
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class DuckDBRAGEngine:
    """Local embedded RAG engine using DuckDB and SentenceTransformers."""

    def __init__(
        self,
        db_path: str = ":memory:",
        embedding_model_name: str = "all-MiniLM-L6-v2",
        shared_model: Optional[Any] = None,
    ):
        self.db_path = db_path
        self.embedding_model_name = embedding_model_name
        self.model = shared_model or SentenceTransformer(embedding_model_name)
        self.conn = duckdb.connect(db_path)
        self._init_database()

    def _init_database(self) -> None:
        """Initialize database schema for vector and text search."""
        # Create documents table with 384-dimensional vector embedding column
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id VARCHAR PRIMARY KEY,
                title VARCHAR,
                content VARCHAR,
                embedding FLOAT[384],
                metadata VARCHAR
            );
        """)

    def ingest_documents(self, docs: List[Dict[str, Any]]) -> int:
        """
        Ingest a list of documents/chunks into DuckDB.
        Each doc dict must contain 'id' and 'content', optionally 'title' and 'metadata'.
        """
        if not docs:
            return 0

        ingested_count = 0
        for doc in docs:
            doc_id = str(doc["id"])
            title = str(doc.get("title", ""))
            content = str(doc["content"])
            metadata_str = json.dumps(doc.get("metadata", {}))

            # Compute local 384-d dense embedding vector
            embedding_vector = self.model.encode(content, convert_to_numpy=True).tolist()

            self.conn.execute(
                """
                INSERT OR REPLACE INTO documents (id, title, content, embedding, metadata)
                VALUES (?, ?, ?, ?::FLOAT[384], ?)
                """,
                (doc_id, title, content, embedding_vector, metadata_str),
            )
            ingested_count += 1

        logger.info(f"Ingested {ingested_count} documents into DuckDB RAG engine.")
        return ingested_count

    def search_vector(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Dense vector similarity search using DuckDB array_cosine_similarity."""
        query_vector = self.model.encode(query, convert_to_numpy=True).tolist()

        res = self.conn.execute(
            """
            SELECT id, title, content, metadata,
                   array_cosine_similarity(embedding, ?::FLOAT[384]) AS score
            FROM documents
            ORDER BY score DESC
            LIMIT ?
            """,
            (query_vector, top_k),
        ).fetchall()

        results = []
        for doc_id, title, content, metadata_str, score in res:
            results.append({
                "id": doc_id,
                "title": title,
                "content": content,
                "metadata": json.loads(metadata_str) if metadata_str else {},
                "score": float(score or 0.0),
            })
        return results

    def search_keyword(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Sparse keyword search using DuckDB full-text pattern matching."""
        terms = [t.strip() for t in query.split() if len(t.strip()) > 2]
        if not terms:
            terms = [query]

        # Simple keyword ranking based on term occurrences
        like_clauses = " OR ".join(["content ILIKE ?" for _ in terms])
        search_params = [f"%{term}%" for term in terms]

        res = self.conn.execute(
            f"""
            SELECT id, title, content, metadata, 1.0 AS score
            FROM documents
            WHERE {like_clauses}
            LIMIT ?
            """,
            (*search_params, top_k),
        ).fetchall()

        results = []
        for doc_id, title, content, metadata_str, score in res:
            results.append({
                "id": doc_id,
                "title": title,
                "content": content,
                "metadata": json.loads(metadata_str) if metadata_str else {},
                "score": float(score),
            })
        return results

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Hybrid search combining Dense Vector Similarity and Keyword Search via
        Reciprocal Rank Fusion (RRF).
        """
        vector_results = self.search_vector(query, top_k=top_k * 2)
        keyword_results = self.search_keyword(query, top_k=top_k * 2)

        rrf_scores: Dict[str, float] = {}
        docs_map: Dict[str, Dict[str, Any]] = {}

        k_constant = 60.0

        for rank, doc in enumerate(vector_results):
            doc_id = doc["id"]
            docs_map[doc_id] = doc
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + (1.0 / (k_constant + rank + 1))

        for rank, doc in enumerate(keyword_results):
            doc_id = doc["id"]
            docs_map[doc_id] = doc
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + (1.0 / (k_constant + rank + 1))

        # Sort combined documents by RRF score
        sorted_ids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)[:top_k]

        final_results = []
        for doc_id in sorted_ids:
            doc = docs_map[doc_id]
            doc["score"] = rrf_scores[doc_id]
            final_results.append(doc)

        return final_results

    def close(self) -> None:
        """Close database connection."""
        self.conn.close()
