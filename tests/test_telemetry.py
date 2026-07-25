import pytest
from council.schemas import (
    ConsiliumFinalArtifact,
    ContradictionItem,
    ModelResponsePayload,
)
from council.telemetry import DuckDBTelemetryLogger


@pytest.fixture
def sample_artifact():
    return ConsiliumFinalArtifact(
        query="Compare PostgreSQL vs DuckDB",
        consensus_score=95.0,
        agreement_points=["DuckDB is in-process OLAP"],
        contradictions=[
            ContradictionItem(
                topic="Storage Format",
                description="DuckDB is columnar, Postgres is row-based.",
                conflicting_models=["gpt-4o", "claude-3-5-haiku"],
            )
        ],
        mermaid_code="graph TD\n  A --> B",
        obsidian_title="postgres-vs-duckdb",
        tags=["database"],
        responses=[
            ModelResponsePayload(
                model_name="gpt-4o",
                response_text="Postgres response",
                latency_ms=1200.0,
                prompt_tokens=100,
                completion_tokens=50,
                cost_usd=0.003,
            ),
            ModelResponsePayload(
                model_name="claude-3-5-haiku",
                response_text="Claude response",
                latency_ms=800.0,
                prompt_tokens=80,
                completion_tokens=40,
                cost_usd=0.001,
            ),
        ],
    )


def test_telemetry_logging_and_history(sample_artifact):
    logger = DuckDBTelemetryLogger(db_path=":memory:")

    run_id = logger.log_query_run(sample_artifact)
    assert run_id.startswith("run-")

    history = logger.get_audit_history(limit=10)
    assert len(history) == 1
    record = history[0]

    assert record["run_id"] == run_id
    assert record["query"] == "Compare PostgreSQL vs DuckDB"
    assert record["consensus_score"] == 95.0
    assert record["total_tokens"] == 270
    assert record["total_cost_usd"] == pytest.approx(0.004, rel=1e-4)
    assert record["avg_latency_ms"] == 1000.0
    assert record["num_contradictions"] == 1
    assert "gpt-4o" in record["model_latencies"]

    logger.close()


def test_telemetry_summary_aggregations(sample_artifact):
    logger = DuckDBTelemetryLogger(db_path=":memory:")

    # Log 2 runs
    logger.log_query_run(sample_artifact)
    logger.log_query_run(sample_artifact)

    summary = logger.get_telemetry_summary()
    assert summary["total_queries"] == 2
    assert summary["avg_consensus_score"] == 95.0
    assert summary["total_tokens"] == 540
    assert summary["total_cost_usd"] == pytest.approx(0.008, rel=1e-4)
    assert summary["avg_latency_ms"] == 1000.0

    logger.close()
