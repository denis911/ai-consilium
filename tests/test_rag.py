import pytest
from council.rag import DuckDBRAGEngine


@pytest.fixture
def sample_docs():
    return [
        {
            "id": "doc1",
            "title": "DuckDB Overview",
            "content": "DuckDB is an embedded analytical SQL database management system designed for fast OLAP queries.",
            "metadata": {"source": "obsidian/duckdb.md"},
        },
        {
            "id": "doc2",
            "title": "PostgreSQL Architecture",
            "content": "PostgreSQL is a powerful open-source client-server relational database system supporting transactions.",
            "metadata": {"source": "obsidian/postgres.md"},
        },
        {
            "id": "doc3",
            "title": "Vector Embeddings",
            "content": "SentenceTransformers models produce dense 384-dimensional semantic embeddings for fast similarity search.",
            "metadata": {"source": "obsidian/embeddings.md"},
        },
    ]


def test_rag_ingest_and_vector_search(sample_docs):
    rag = DuckDBRAGEngine(db_path=":memory:")
    count = rag.ingest_documents(sample_docs)
    assert count == 3

    # Vector search for analytical database
    results = rag.search_vector("analytical query database", top_k=2)
    assert len(results) > 0
    assert results[0]["id"] == "doc1"
    assert "DuckDB" in results[0]["content"]

    rag.close()


def test_rag_keyword_search(sample_docs):
    rag = DuckDBRAGEngine(db_path=":memory:")
    rag.ingest_documents(sample_docs)

    results = rag.search_keyword("PostgreSQL client-server", top_k=1)
    assert len(results) == 1
    assert results[0]["id"] == "doc2"

    rag.close()


def test_rag_hybrid_rrf_search(sample_docs):
    rag = DuckDBRAGEngine(db_path=":memory:")
    rag.ingest_documents(sample_docs)

    results = rag.search("dense 384-dimensional embeddings", top_k=2)
    assert len(results) >= 1
    assert results[0]["id"] == "doc3"
    assert "score" in results[0]

    rag.close()


def test_rag_empty_search():
    rag = DuckDBRAGEngine(db_path=":memory:")
    results = rag.search("anything", top_k=5)
    assert results == []
    rag.close()
