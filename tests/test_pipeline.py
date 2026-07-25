"""
End-to-End Pipeline Integration Tests & Synthetic Evaluation Benchmarks
"""

import os
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

from council.schemas import ConsiliumQueryInput, ModelResponsePayload
from council.rag import DuckDBRAGEngine
from council.providers import LLMProviderEngine
from council.consensus import ConsensusEngine
from council.synthesizer import LLMJudgeSynthesizer
from council.exporter import ObsidianExporter
from council.telemetry import DuckDBTelemetryLogger


@pytest.mark.asyncio
async def test_full_end_to_end_pipeline(tmp_path):
    """Test full end-to-end data flow from RAG ingestion to Obsidian vault export and telemetry logging."""
    vault_dir = tmp_path / "obsidian_vault"
    db_file = str(tmp_path / "test_telemetry.duckdb")

    # Step 1: Ingest Reference Context into DuckDB RAG Engine
    rag_engine = DuckDBRAGEngine(db_path=":memory:")
    rag_engine.ingest_documents([
        {
            "id": "doc1",
            "title": "DuckDB Specs",
            "content": "DuckDB is an in-process columnar SQL OLAP database designed for fast analytical queries.",
        }
    ])

    user_query = "What makes DuckDB suitable for analytical workloads?"
    rag_results = rag_engine.search(user_query, top_k=1)
    assert len(rag_results) == 1
    assert "DuckDB" in rag_results[0]["content"]

    query_input = ConsiliumQueryInput(
        query=user_query,
        context_chunks=[rag_results[0]["content"]],
        selected_models=["gpt-4o", "claude-3-5-haiku-20241022"],
    )

    # Step 2: Multi-Model Querying (Mocked LLM Completions)
    mock_responses = [
        ModelResponsePayload(
            model_name="gpt-4o",
            response_text="DuckDB performs high-speed vectorized analytical queries in-process.",
            latency_ms=1200.0,
            prompt_tokens=100,
            completion_tokens=40,
            cost_usd=0.002,
        ),
        ModelResponsePayload(
            model_name="claude-3-5-haiku-20241022",
            response_text="DuckDB is an embedded analytical database using columnar storage.",
            latency_ms=900.0,
            prompt_tokens=90,
            completion_tokens=35,
            cost_usd=0.001,
        ),
    ]

    # Step 3: Compute Consensus Matrix
    consensus_engine = ConsensusEngine()
    metrics = consensus_engine.compute_consensus(mock_responses)
    assert metrics.consensus_score >= 60.0
    assert len(metrics.outlier_models) == 0

    # Step 4: Execute LLM Judge Synthesis (Mocked Synthesis Completion)
    json_synthesis = {
        "agreement_points": ["DuckDB is in-process and uses columnar storage for OLAP."],
        "contradictions": [],
        "mermaid_code": "graph TD\n  Query --> DuckDB",
        "obsidian_title": "duckdb-analytical-workloads",
        "tags": ["duckdb", "database"],
    }

    mock_judge_resp = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = json.dumps(json_synthesis)
    mock_judge_resp.choices = [mock_choice]

    synthesizer = LLMJudgeSynthesizer()
    with patch("litellm.acompletion", new_callable=AsyncMock) as mock_acompletion:
        mock_acompletion.return_value = mock_judge_resp

        final_artifact = await synthesizer.synthesize(query_input, mock_responses, metrics)

        assert final_artifact.consensus_score == metrics.consensus_score
        assert len(final_artifact.agreement_points) == 1

    # Step 5: Log Telemetry to DuckDB
    telemetry = DuckDBTelemetryLogger(db_path=db_file)
    run_id = telemetry.log_query_run(final_artifact)
    assert run_id.startswith("run-")

    history = telemetry.get_audit_history(limit=5)
    assert len(history) == 1
    assert history[0]["query"] == user_query
    assert history[0]["total_tokens"] == 265
    telemetry.close()

    # Step 6: Export Note to Obsidian Vault
    exporter = ObsidianExporter(default_vault_path=str(vault_dir))
    exported_file = exporter.export_artifact(final_artifact)
    assert os.path.exists(exported_file)

    note_content = Path(exported_file).read_text(encoding="utf-8")
    assert "DuckDB is in-process and uses columnar storage" in note_content
    assert "```mermaid" in note_content

    rag_engine.close()


def test_consensus_precision_evaluation_benchmark():
    """Benchmark test evaluating consensus score precision across synthetic response clusters."""
    consensus_engine = ConsensusEngine()

    # Benchmark 1: Unanimous Agreement Cluster
    unanimous_responses = [
        ModelResponsePayload(model_name="m1", response_text="Python is a high-level interpreted programming language."),
        ModelResponsePayload(model_name="m2", response_text="Python is an interpreted high-level dynamic language."),
        ModelResponsePayload(model_name="m3", response_text="Python is a popular interpreted programming language."),
    ]
    unanimous_metrics = consensus_engine.compute_consensus(unanimous_responses)
    assert unanimous_metrics.consensus_score >= 80.0
    assert len(unanimous_metrics.outlier_models) == 0

    # Benchmark 2: Dissenting Outlier Cluster
    dissenting_responses = [
        ModelResponsePayload(model_name="m1", response_text="PostgreSQL uses row-oriented storage and client-server model."),
        ModelResponsePayload(model_name="m2", response_text="Postgres is a relational database with client-server architecture."),
        ModelResponsePayload(model_name="dissenting_model", response_text="Baking bread requires yeast, warm water, salt, and flour."),
    ]
    dissenting_metrics = consensus_engine.compute_consensus(dissenting_responses, outlier_threshold=0.50)
    assert "dissenting_model" in dissenting_metrics.outlier_models
    assert dissenting_metrics.consensus_score < unanimous_metrics.consensus_score
