import pytest
from pydantic import ValidationError
from council.schemas import (
    ConsiliumQueryInput,
    ModelResponsePayload,
    ContradictionItem,
    ConsensusMetrics,
    ConsiliumFinalArtifact,
)


def test_query_input_valid():
    inp = ConsiliumQueryInput(query="Compare PostgreSQL vs DuckDB", selected_models=["gpt-4o", "claude-3-5-haiku"])
    assert inp.query == "Compare PostgreSQL vs DuckDB"
    assert len(inp.selected_models) == 2


def test_query_input_invalid_empty():
    with pytest.raises(ValidationError):
        ConsiliumQueryInput(query="")

    with pytest.raises(ValidationError):
        ConsiliumQueryInput(query="   ")


def test_model_response_payload_valid_and_json():
    resp = ModelResponsePayload(
        model_name="gpt-4o",
        response_text="DuckDB is an in-process OLAP database.",
        latency_ms=150.5,
        prompt_tokens=100,
        completion_tokens=50,
        cost_usd=0.002,
    )
    assert resp.latency_ms == 150.5
    json_data = resp.model_dump_json()
    assert "DuckDB" in json_data

    # Deserialization test
    loaded = ModelResponsePayload.model_validate_json(json_data)
    assert loaded.model_name == "gpt-4o"
    assert loaded.cost_usd == 0.002


def test_model_response_payload_invalid_metrics():
    with pytest.raises(ValidationError):
        ModelResponsePayload(model_name="gpt-4o", response_text="test", latency_ms=-10.0)

    with pytest.raises(ValidationError):
        ModelResponsePayload(model_name="gpt-4o", response_text="test", prompt_tokens=-1)


def test_contradiction_item():
    item = ContradictionItem(
        topic="Licensing",
        description="Model A claims MIT, Model B claims Apache 2.0",
        conflicting_models=["gpt-4o", "claude-3-5-haiku"],
    )
    assert item.topic == "Licensing"
    assert len(item.conflicting_models) == 2


def test_consensus_metrics_validation():
    metrics = ConsensusMetrics(consensus_score=85.5, outlier_models=["grok-2"])
    assert metrics.consensus_score == 85.5

    with pytest.raises(ValidationError):
        ConsensusMetrics(consensus_score=105.0)

    with pytest.raises(ValidationError):
        ConsensusMetrics(consensus_score=-5.0)


def test_final_artifact_serialization():
    artifact = ConsiliumFinalArtifact(
        query="PostgreSQL vs DuckDB",
        consensus_score=92.0,
        agreement_points=["DuckDB is vectorized", "Postgres is client-server"],
        tags=["database", "architecture"],
    )
    json_str = artifact.model_dump_json()
    assert "PostgreSQL vs DuckDB" in json_str

    deserialized = ConsiliumFinalArtifact.model_validate_json(json_str)
    assert deserialized.consensus_score == 92.0
    assert deserialized.tags == ["database", "architecture"]
