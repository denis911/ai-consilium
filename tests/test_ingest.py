import os
import pytest
from pathlib import Path
from ingest import parse_markdown_file, scan_and_ingest_directory


def test_parse_markdown_file_with_yaml(tmp_path):
    md_file = tmp_path / "test_note.md"
    md_file.write_text(
        '---\ntitle: "Test Note Title"\ntags: ["tag1", "tag2"]\n---\n\n## Section\nThis is test content.',
        encoding="utf-8",
    )

    parsed = parse_markdown_file(md_file)
    assert parsed is not None
    assert parsed["title"] == "Test Note Title"
    assert parsed["tags"] == ["tag1", "tag2"]
    assert "This is test content." in parsed["content"]


def test_scan_and_ingest_directory(tmp_path):
    vault_dir = tmp_path / "obsidian_vault"
    vault_dir.mkdir()

    note1 = vault_dir / "note1.md"
    note1.write_text("# Note 1\nDuckDB is fast.", encoding="utf-8")

    note2 = vault_dir / "note2.md"
    note2.write_text("# Note 2\nPostgres uses row storage.", encoding="utf-8")

    db_path = str(tmp_path / "test_ingest.duckdb")
    count = scan_and_ingest_directory(str(vault_dir), db_path=db_path)
    assert count == 2
