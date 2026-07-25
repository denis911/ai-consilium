import pytest
from council.schemas import ModelResponsePayload
from council.consensus import ConsensusEngine


def test_consensus_unanimous():
    engine = ConsensusEngine()
    responses = [
        ModelResponsePayload(model_name="gpt-4o", response_text="DuckDB is a fast in-process analytical database."),
        ModelResponsePayload(model_name="claude-3-5-haiku", response_text="DuckDB is an in-process analytical SQL database engine."),
        ModelResponsePayload(model_name="gemini-2.5-flash", response_text="DuckDB is a fast embedded OLAP database."),
    ]

    metrics = engine.compute_consensus(responses)

    assert metrics.consensus_score > 70.0
    assert len(metrics.outlier_models) == 0
    assert "gpt-4o" in metrics.pairwise_similarity
    assert metrics.pairwise_similarity["gpt-4o"]["gpt-4o"] == 1.0


def test_consensus_single_outlier():
    engine = ConsensusEngine()
    responses = [
        ModelResponsePayload(model_name="model1", response_text="PostgreSQL uses client-server architecture with MVCC."),
        ModelResponsePayload(model_name="model2", response_text="Postgres is a relational client-server database using MVCC."),
        ModelResponsePayload(model_name="model_outlier", response_text="Baking chocolate cake requires cocoa powder, flour, sugar, and eggs."),
    ]

    metrics = engine.compute_consensus(responses, outlier_threshold=0.50)

    assert "model_outlier" in metrics.outlier_models
    assert len(metrics.outlier_models) == 1
    # Check pairwise similarity between model1 and model_outlier is low
    assert metrics.pairwise_similarity["model1"]["model_outlier"] < 0.40


def test_consensus_empty_and_single_responses():
    engine = ConsensusEngine()

    # Empty list
    metrics_empty = engine.compute_consensus([])
    assert metrics_empty.consensus_score == 0.0
    assert metrics_empty.outlier_models == []

    # Single response
    single = [ModelResponsePayload(model_name="gpt-4o", response_text="Single answer.")]
    metrics_single = engine.compute_consensus(single)
    assert metrics_single.consensus_score == 100.0
    assert metrics_single.outlier_models == []
