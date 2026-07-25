import os
import pytest
from pathlib import Path
from council.schemas import (
    ConsiliumFinalArtifact,
    ContradictionItem,
    ModelResponsePayload,
)
from council.exporter import ObsidianExporter


@pytest.fixture
def sample_artifact():
    return ConsiliumFinalArtifact(
        query="Compare PostgreSQL vs DuckDB",
        consensus_score=92.5,
        agreement_points=["DuckDB is in-process OLAP", "PostgreSQL is client-server OLTP"],
        contradictions=[
            ContradictionItem(
                topic="Storage Format",
                description="DuckDB uses columnar storage, Postgres uses row storage.",
                conflicting_models=["gpt-4o", "claude-3-5-haiku"],
            )
        ],
        mermaid_code="graph TD\n  A[Query] --> B[DuckDB]",
        obsidian_title="postgres-vs-duckdb-analysis",
        tags=["database", "architecture"],
        responses=[
            ModelResponsePayload(model_name="gpt-4o", response_text="Postgres response..."),
            ModelResponsePayload(model_name="claude-3-5-haiku", response_text="Claude response..."),
        ],
    )


def test_format_markdown(sample_artifact):
    exporter = ObsidianExporter()
    md = exporter.format_markdown(sample_artifact)

    assert "title: \"postgres-vs-duckdb-analysis\"" in md
    assert "consensus_score: 92.5" in md
    assert "tags: [\"database\", \"architecture\"]" in md
    assert "## ✅ Unanimous & Verified Points of Agreement" in md
    assert "DuckDB is in-process OLAP" in md
    assert "## ⚠️ Audit Log: Contradictions & Disagreements" in md
    assert "Storage Format" in md
    assert "```mermaid" in md
    assert "graph TD" in md


def test_export_artifact_to_temp_dir(sample_artifact, tmp_path):
    exporter = ObsidianExporter(default_vault_path=str(tmp_path))
    file_path = exporter.export_artifact(sample_artifact)

    assert os.path.exists(file_path)
    path_obj = Path(file_path)
    assert path_obj.suffix == ".md"
    assert "postgres-vs-duckdb-analysis" in path_obj.name

    content = path_obj.read_text(encoding="utf-8")
    assert "Compare PostgreSQL vs DuckDB" in content
    assert "consensus_score: 92.5" in content
