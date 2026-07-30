"""
RAG Retrieval Evaluation Script (Hit Rate & MRR Benchmark) for AI Consilium
"""

import sys
import logging
from typing import List, Dict, Any, Tuple
from council.rag import DuckDBRAGEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("eval")

# Synthetic Benchmark Evaluation Dataset (Questions & Ground Truth Document IDs)
BENCHMARK_DOCUMENTS = [
    {
        "id": "doc_duckdb_olap",
        "title": "DuckDB OLAP Performance",
        "content": "DuckDB is an in-process columnar SQL OLAP database engine optimized for fast analytical queries on local CPU.",
    },
    {
        "id": "doc_postgres_oltp",
        "title": "PostgreSQL OLTP Specs",
        "content": "PostgreSQL is a traditional client-server relational database management system using row-oriented storage.",
    },
    {
        "id": "doc_litellm_async",
        "title": "LiteLLM Multi-Provider Async",
        "content": "LiteLLM provides unified asynchronous completion calls across OpenAI, Anthropic, Gemini, and OpenRouter APIs.",
    },
    {
        "id": "doc_obsidian_mermaid",
        "title": "Obsidian Vault Formatting",
        "content": "Obsidian notes store human-readable Markdown with YAML frontmatter, tags, and rendered Mermaid.js diagrams.",
    },
    {
        "id": "doc_consensus_matrix",
        "title": "Embedding Consensus Distance",
        "content": "Consensus Engine computes pairwise cosine similarity matrices across 384-dimensional SentenceTransformer vector embeddings.",
    },
]

BENCHMARK_EVAL_CASES = [
    {
        "query": "Which database is an in-process columnar SQL OLAP engine?",
        "expected_doc_id": "doc_duckdb_olap",
    },
    {
        "query": "How does PostgreSQL handle client-server row-oriented relational storage?",
        "expected_doc_id": "doc_postgres_oltp",
    },
    {
        "query": "What library provides unified async calls to OpenAI, Anthropic, and OpenRouter?",
        "expected_doc_id": "doc_litellm_async",
    },
    {
        "query": "How are Markdown notes formatted in an Obsidian vault with Mermaid diagrams?",
        "expected_doc_id": "doc_obsidian_mermaid",
    },
    {
        "query": "How does the consensus engine measure cosine similarity across embeddings?",
        "expected_doc_id": "doc_consensus_matrix",
    },
]


def calculate_hit_rate(results_list: List[List[Dict[str, Any]]], expected_ids: List[str]) -> float:
    """Calculate Hit Rate (fraction of queries where expected doc is in top-K results)."""
    if not expected_ids:
        return 0.0

    hits = 0
    for results, target_id in zip(results_list, expected_ids):
        found_ids = [r["id"] for r in results]
        if target_id in found_ids:
            hits += 1

    return round((hits / len(expected_ids)) * 100.0, 2)


def calculate_mrr(results_list: List[List[Dict[str, Any]]], expected_ids: List[str]) -> float:
    """Calculate Mean Reciprocal Rank (MRR@K)."""
    if not expected_ids:
        return 0.0

    reciprocal_ranks = []
    for results, target_id in zip(results_list, expected_ids):
        found_ids = [r["id"] for r in results]
        if target_id in found_ids:
            rank = found_ids.index(target_id) + 1
            reciprocal_ranks.append(1.0 / rank)
        else:
            reciprocal_ranks.append(0.0)

    return round(float(sum(reciprocal_ranks) / len(expected_ids)), 4)


def run_benchmark_eval(top_k: int = 3) -> Dict[str, Any]:
    """Execute evaluation benchmark comparing RRF hybrid search performance."""
    logger.info("Initializing in-memory DuckDB RAG Engine for benchmark evaluation...")
    rag_engine = DuckDBRAGEngine(db_path=":memory:")
    rag_engine.ingest_documents(BENCHMARK_DOCUMENTS)

    retrieved_results = []
    expected_ids = []

    for test_case in BENCHMARK_EVAL_CASES:
        q = test_case["query"]
        target_id = test_case["expected_doc_id"]

        search_res = rag_engine.search(q, top_k=top_k)
        retrieved_results.append(search_res)
        expected_ids.append(target_id)

    hit_rate = calculate_hit_rate(retrieved_results, expected_ids)
    mrr = calculate_mrr(retrieved_results, expected_ids)

    rag_engine.close()

    return {
        "total_test_cases": len(BENCHMARK_EVAL_CASES),
        "top_k": top_k,
        "hit_rate_percentage": hit_rate,
        "mrr_score": mrr,
    }


def main():
    print("\n" + "=" * 60)
    print("📊 AI CONSILIUM — RAG RETRIEVAL EVALUATION BENCHMARK")
    print("=" * 60)

    metrics = run_benchmark_eval(top_k=3)

    print(f"Total Benchmark Test Cases: {metrics['total_test_cases']}")
    print(f"Top-K Window: @{metrics['top_k']}")
    print(f"🎯 Hit Rate @ {metrics['top_k']}: {metrics['hit_rate_percentage']:.1f}%")
    print(f"📈 Mean Reciprocal Rank (MRR @ {metrics['top_k']}): {metrics['mrr_score']:.4f}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
