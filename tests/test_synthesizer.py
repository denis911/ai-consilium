import pytest
import json
from unittest.mock import patch, MagicMock, AsyncMock
from council.schemas import (
    ConsiliumQueryInput,
    ModelResponsePayload,
    ConsensusMetrics,
    ConsiliumFinalArtifact,
)
from council.synthesizer import LLMJudgeSynthesizer


@pytest.fixture
def mock_synthesis_data():
    return {
        "query_input": ConsiliumQueryInput(query="Compare PostgreSQL vs DuckDB"),
        "responses": [
            ModelResponsePayload(model_name="gpt-4o", response_text="Postgres is client-server, DuckDB is in-process."),
            ModelResponsePayload(model_name="claude-3-5-haiku", response_text="DuckDB is embedded OLAP, Postgres is RDBMS."),
        ],
        "metrics": ConsensusMetrics(consensus_score=88.5, outlier_models=[]),
    }


@pytest.mark.asyncio
async def test_synthesizer_success(mock_synthesis_data):
    synthesizer = LLMJudgeSynthesizer()

    json_response = {
        "agreement_points": ["Both are open source database engines", "DuckDB is in-process OLAP"],
        "contradictions": [
            {
                "topic": "Concurrency model",
                "description": "Model A notes multi-user concurrency, Model B highlights single-user write lock",
                "conflicting_models": ["gpt-4o", "claude-3-5-haiku"]
            }
        ],
        "mermaid_code": "graph TD\n  A[PostgreSQL] --> B[OLTP]\n  C[DuckDB] --> D[OLAP]",
        "obsidian_title": "2026-07-25-postgres-vs-duckdb",
        "tags": ["database", "architecture", "consensus"]
    }

    mock_resp = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = json.dumps(json_response)
    mock_resp.choices = [mock_choice]

    with patch("litellm.acompletion", new_callable=AsyncMock) as mock_acompletion:
        mock_acompletion.return_value = mock_resp

        artifact = await synthesizer.synthesize(
            mock_synthesis_data["query_input"],
            mock_synthesis_data["responses"],
            mock_synthesis_data["metrics"],
        )

        assert isinstance(artifact, ConsiliumFinalArtifact)
        assert artifact.consensus_score == 88.5
        assert len(artifact.agreement_points) == 2
        assert len(artifact.contradictions) == 1
        assert artifact.contradictions[0].topic == "Concurrency model"
        assert artifact.obsidian_title == "2026-07-25-postgres-vs-duckdb"
        assert artifact.mermaid_code.startswith("graph TD")


@pytest.mark.asyncio
async def test_synthesizer_fallback_on_llm_error(mock_synthesis_data):
    synthesizer = LLMJudgeSynthesizer()

    with patch("litellm.acompletion", side_effect=RuntimeError("LLM API error")):
        artifact = await synthesizer.synthesize(
            mock_synthesis_data["query_input"],
            mock_synthesis_data["responses"],
            mock_synthesis_data["metrics"],
        )

        assert isinstance(artifact, ConsiliumFinalArtifact)
        assert artifact.consensus_score == 88.5
        assert len(artifact.agreement_points) >= 1
        assert "graph TD" in artifact.mermaid_code


def test_clean_json_response_nested_brackets():
    synthesizer = LLMJudgeSynthesizer()
    raw_llm_text = (
        "Here is the result:\n"
        '{"agreement_points": ["point1"], "contradictions": [{"topic": "T1", "description": "D1", "conflicting_models": ["m1"]}], '
        '"mermaid_code": "graph TD", "obsidian_title": "title", "tags": ["tag1"]}\n'
        "Hope this helps!"
    )
    parsed = synthesizer._clean_json_response(raw_llm_text)
    assert parsed["agreement_points"] == ["point1"]
    assert len(parsed["contradictions"]) == 1
    assert parsed["contradictions"][0]["topic"] == "T1"


def test_clean_json_response_mermaid_braces():
    synthesizer = LLMJudgeSynthesizer()
    raw_llm_text = (
        "Output:\n"
        '{"agreement_points": ["point1"], '
        '"mermaid_code": "graph TD\\n  subgraph S1 [Section]\\n    A{Topic} --> B[Consensus]\\n  end", '
        '"obsidian_title": "title", "tags": ["tag"]}\n'
        "Enjoy!"
    )
    parsed = synthesizer._clean_json_response(raw_llm_text)
    assert parsed["agreement_points"] == ["point1"]
    assert "subgraph S1" in parsed["mermaid_code"]


def test_clean_json_response_stray_leading_braces():
    synthesizer = LLMJudgeSynthesizer()
    raw_llm_text = "} {\"agreement_points\": [\"point1\"], \"mermaid_code\": \"\", \"obsidian_title\": \"t\", \"tags\": []}"
    parsed = synthesizer._clean_json_response(raw_llm_text)
    assert parsed["agreement_points"] == ["point1"]
