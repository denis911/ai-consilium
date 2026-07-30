import pytest
from pathlib import Path

from council.schemas import ConsiliumFinalArtifact, ModelResponsePayload, ConsiliumQueryInput
from council.exporter import ObsidianExporter
from council.providers import LLMProviderEngine


def test_exporter_escapes_code_fences():
    exporter = ObsidianExporter()
    artifact = ConsiliumFinalArtifact(
        query="Test code fence escaping",
        consensus_score=100.0,
        responses=[
            ModelResponsePayload(
                model_name="test-model",
                response_text="Here is a fence:\n```python\nprint('hello')\n```",
            )
        ],
    )
    formatted = exporter.format_markdown(artifact)
    assert "~~~python" in formatted
    assert "```text\nHere is a fence:\n~~~python\nprint('hello')\n~~~" in formatted


def test_exporter_validates_mermaid_syntax():
    exporter = ObsidianExporter()

    valid_artifact = ConsiliumFinalArtifact(
        query="Valid Mermaid Test",
        consensus_score=90.0,
        mermaid_code="graph TD\n  A --> B",
    )
    assert "```mermaid" in exporter.format_markdown(valid_artifact)

    invalid_artifact = ConsiliumFinalArtifact(
        query="Invalid Mermaid Test",
        consensus_score=90.0,
        mermaid_code="This is just plain text, not a valid diagram token",
    )
    assert "```mermaid" not in exporter.format_markdown(invalid_artifact)


def test_dockerignore_exists_and_contains_secrets():
    dockerignore_path = Path(".dockerignore")
    assert dockerignore_path.exists()
    content = dockerignore_path.read_text(encoding="utf-8")
    assert ".env" in content
    assert ".git" in content
    assert "*.duckdb" in content
