import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from main import parse_args, run_cli
from council.schemas import ConsiliumFinalArtifact, ModelResponsePayload


def test_parse_args_defaults():
    args = parse_args(["--query", "What is DuckDB?"])
    assert args.query == "What is DuckDB?"
    assert args.free_tier is False
    assert args.export is False
    assert args.json is False


def test_parse_args_flags():
    args = parse_args([
        "--query", "Compare DBs",
        "--free-tier",
        "--export",
        "--vault-path", "/tmp/vault",
        "--json"
    ])
    assert args.query == "Compare DBs"
    assert args.free_tier is True
    assert args.export is True
    assert args.vault_path == "/tmp/vault"
    assert args.json is True


@pytest.mark.asyncio
async def test_run_cli_mocked(tmp_path, capsys):
    args = parse_args(["--query", "What is DuckDB?", "--export", "--vault-path", str(tmp_path), "--json"])

    mock_resp = [
        ModelResponsePayload(model_name="gpt-4o", response_text="DuckDB is an in-process OLAP engine.")
    ]
    mock_artifact = ConsiliumFinalArtifact(
        query="What is DuckDB?",
        consensus_score=100.0,
        agreement_points=["DuckDB is in-process"],
        obsidian_title="duckdb-cli-test",
        responses=mock_resp,
    )

    with patch("council.providers.LLMProviderEngine.query_concurrently", new_callable=AsyncMock, return_value=mock_resp), \
         patch("council.synthesizer.LLMJudgeSynthesizer.synthesize", new_callable=AsyncMock, return_value=mock_artifact), \
         patch("council.telemetry.DuckDBTelemetryLogger.log_query_run", return_value="run-123"):

        await run_cli(args)

        captured = capsys.readouterr()
        assert "What is DuckDB?" in captured.out
        assert "consensus_score" in captured.out
