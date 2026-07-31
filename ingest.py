"""
Bulk Obsidian Vault Directory Ingestion CLI & Auto-Sync Script for AI Consilium
"""

import os
import sys
import re
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

import duckdb
from council.rag import DuckDBRAGEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ingest")


def parse_markdown_file(file_path: Path, target_dir: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    """Parse title, YAML tags, and content from a single Markdown file."""
    try:
        raw_text = file_path.read_text(encoding="utf-8").strip()
    except Exception as e:
        logger.warning(f"Could not read file {file_path}: {e}")
        return None

    if not raw_text:
        return None

    title = file_path.stem
    tags = []
    content = raw_text

    # Extract YAML frontmatter if present
    yaml_match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", raw_text, re.DOTALL)
    if yaml_match:
        yaml_text = yaml_match.group(1)
        content = yaml_match.group(2).strip()

        # Extract title from frontmatter
        title_match = re.search(r'title:\s*"(.*?)"', yaml_text)
        if title_match:
            title = title_match.group(1)

        # Extract tags from frontmatter
        tags_match = re.search(r"tags:\s*\[(.*?)\]", yaml_text)
        if tags_match:
            tags_str = tags_match.group(1)
            tags = [t.strip().strip('"').strip("'") for t in tags_str.split(",") if t.strip()]

    doc_id = str(file_path.relative_to(target_dir)) if target_dir and file_path.is_relative_to(target_dir) else str(file_path.name)

    return {
        "id": doc_id,
        "title": title,
        "content": content,
        "tags": tags,
        "path": str(file_path),
    }


def scan_and_ingest_directory(
    directory_path: str,
    db_path: str = "ai_consilium.duckdb",
) -> int:
    """Recursively scan directory for .md files and ingest them into DuckDB RAG database."""
    target_dir = Path(directory_path).resolve()
    if not target_dir.exists():
        logger.warning(f"Directory path does not exist: {target_dir}")
        return 0

    md_files = list(target_dir.rglob("*.md"))
    if not md_files:
        logger.info(f"No .md files found in directory: {target_dir}")
        return 0

    logger.info(f"Found {len(md_files)} markdown files in {target_dir}. Parsing documents...")
    documents = []
    for md_file in md_files:
        parsed = parse_markdown_file(md_file, target_dir=target_dir)
        if parsed and parsed["content"].strip():
            documents.append(parsed)

    if not documents:
        logger.info("No non-empty markdown documents parsed.")
        return 0

    try:
        rag_engine = DuckDBRAGEngine(db_path=db_path)
    except duckdb.IOException as e:
        logger.error(f"❌ Connection Lock Failed: Could not open database at '{db_path}'. Is Streamlit app running? Error: {e}")
        return 0

    count = rag_engine.ingest_documents(documents)
    rag_engine.close()

    logger.info(f"Successfully ingested {count} documents into DuckDB RAG database at {db_path}.")
    return count


def parse_args(args=None):
    parser = argparse.ArgumentParser(description="AI Consilium — Bulk Obsidian Vault Ingestion CLI")
    parser.add_argument(
        "--dir",
        "-d",
        type=str,
        default=None,
        help="Path to Obsidian vault directory (defaults to OBSIDIAN_VAULT_PATH or ./output_vault)",
    )
    parser.add_argument(
        "--db-path",
        type=str,
        default="ai_consilium.duckdb",
        help="Path to DuckDB database file",
    )
    return parser.parse_args(args)


def main():
    args = parse_args()
    vault_dir = args.dir or os.environ.get("OBSIDIAN_VAULT_PATH", "C:/ai-memory/ai-concilium")
    print(f"\n📂 AI Consilium Bulk Ingestion: Scanning `{vault_dir}`...")
    count = scan_and_ingest_directory(vault_dir, db_path=args.db_path)
    print(f"✅ Ingested {count} notes into DuckDB RAG database (`{args.db_path}`).\n")


if __name__ == "__main__":
    main()
