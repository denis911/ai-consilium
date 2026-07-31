"""
Obsidian Vault & Mermaid Diagram Exporter for AI Consilium
"""

import os
import re
import datetime
import logging
from pathlib import Path
from typing import Optional

from council.schemas import ConsiliumFinalArtifact

logger = logging.getLogger(__name__)

VALID_MERMAID_TOKENS = (
    "graph",
    "flowchart",
    "sequencediagram",
    "classdiagram",
    "statediagram",
    "erdiagram",
    "gantt",
    "pie",
    "mindmap",
    "gitgraph",
    "architecture",
)


class ObsidianExporter:
    """Exporter for saving Consilium research artifacts as structured Markdown notes in an Obsidian vault."""

    def __init__(self, default_vault_path: Optional[str] = None):
        self.default_vault_path = default_vault_path or os.environ.get(
            "OBSIDIAN_VAULT_PATH", "./output_vault"
        )

    def _sanitize_filename(self, title: str) -> str:
        """Sanitize title string for safe filesystem usage."""
        clean = title.strip().lower()
        clean = re.sub(r"[^\w\s-]", "", clean)
        clean = re.sub(r"[\s_]+", "-", clean)
        return clean or "consensus-research-report"

    def _is_valid_mermaid(self, mermaid_code: str) -> bool:
        """Check if mermaid_code begins with a recognized diagram type token."""
        if not mermaid_code or not mermaid_code.strip():
            return False
        first_line = mermaid_code.strip().splitlines()[0].strip().lower()
        return any(first_line.startswith(token) for token in VALID_MERMAID_TOKENS)

    def format_markdown(self, artifact: ConsiliumFinalArtifact) -> str:
        """Format ConsiliumFinalArtifact into a clean Markdown document with YAML frontmatter."""
        now_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        models_queried = [r.model_name for r in artifact.responses] if artifact.responses else []

        tags_str = ", ".join([f'"{t}"' for t in artifact.tags])

        yaml_frontmatter = (
            "---\n"
            f'title: "{artifact.obsidian_title or artifact.query}"\n'
            f"date: \"{now_str}\"\n"
            f"consensus_score: {artifact.consensus_score:.1f}\n"
            f"tags: [{tags_str}]\n"
            f"models_queried: {models_queried}\n"
            "---\n\n"
        )

        md_body = f"# 🤖 AI Consilium Research: {artifact.query}\n\n"
        md_body += f"> **Consensus Confidence Score:** `{artifact.consensus_score:.1f}%`  \n"
        md_body += f"> **Generated:** `{now_str}`\n\n"

        # Points of Agreement Section
        md_body += "## ✅ Unanimous & Verified Points of Agreement\n"
        if artifact.agreement_points:
            for pt in artifact.agreement_points:
                md_body += f"- {pt}\n"
        else:
            md_body += "- *No explicit agreement points recorded.*\n"
        md_body += "\n"

        # Contradiction Log Section
        md_body += "## ⚠️ Audit Log: Contradictions & Disagreements\n"
        if artifact.contradictions:
            for c in artifact.contradictions:
                models_str = ", ".join(c.conflicting_models) if c.conflicting_models else "Multiple models"
                md_body += f"### 📌 {c.topic}\n"
                md_body += f"- **Explanation:** {c.description}\n"
                md_body += f"- **Conflicting Models:** `{models_str}`\n\n"
        else:
            md_body += "- *Zero contradictions detected across model ensemble.*\n\n"

        # Mermaid Diagram Section (with token syntax validation)
        if artifact.mermaid_code and self._is_valid_mermaid(artifact.mermaid_code):
            md_body += "## 📊 Consensus Architecture & Process Flow\n"
            md_body += "```mermaid\n"
            md_body += f"{artifact.mermaid_code.strip()}\n"
            md_body += "```\n\n"

        # Individual Model Raw Responses Section (escaping code fences)
        if artifact.responses:
            md_body += "## 🔍 Multi-Model Raw Provider Responses\n"
            for resp in artifact.responses:
                escaped_text = resp.response_text.replace("```", "~~~")
                md_body += f"<details>\n"
                md_body += f"<summary><b>{resp.model_name}</b> (Status: <code>{resp.status}</code>, Latency: <code>{resp.latency_ms:.1f}ms</code>)</summary>\n\n"
                md_body += f"```text\n{escaped_text}\n```\n"
                md_body += f"</details>\n\n"

        return yaml_frontmatter + md_body

    def export_artifact(
        self,
        artifact: ConsiliumFinalArtifact,
        vault_path: Optional[str] = None,
    ) -> str:
        """
        Export artifact into the target Obsidian vault directory as a Markdown file.
        Returns the absolute string path of the created file.
        """
        target_dir_str = vault_path or self.default_vault_path
        target_dir = Path(target_dir_str).resolve()
        target_dir.mkdir(parents=True, exist_ok=True)

        date_prefix = datetime.datetime.now().strftime("%Y-%m-%d")
        safe_title = self._sanitize_filename(artifact.obsidian_title or artifact.query)
        filename = f"{date_prefix}-{safe_title}.md"
        target_file = (target_dir / filename).resolve()

        # Path traversal security check
        if not target_file.is_relative_to(target_dir.resolve()):
            raise ValueError(f"Unsafe export path resolved outside vault: {target_file}")

        content = self.format_markdown(artifact)

        # Atomic write to temporary file before replacing
        tmp_file = target_dir / f".tmp-{filename}"
        tmp_file.write_text(content, encoding="utf-8")
        tmp_file.replace(target_file)

        logger.info(f"Exported Consilium research note to {target_file}")
        return str(target_file)
