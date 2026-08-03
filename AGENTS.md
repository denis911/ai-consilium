Commands

- `uv sync` - install dependencies
- `uv run pytest` - the whole suite
- `uv run pytest tests/test_home.py` - one test file

Rules

- Dependencies are added in `pyproject.toml`. Do not add one without asking.
- **Context7 MCP Verification Rule:** All coding agents MUST double-check library/framework syntax (LiteLLM model slugs, Streamlit UI parameters, DuckDB methods, Mermaid diagram syntax) using Context7 MCP server (`resolve-library-id`, `query-docs`) or direct API `/v1/models` endpoints BEFORE implementing code changes to eliminate API deprecation and syntax bugs.
- **Streamlit UI Best Practices:**
  - Use `width="stretch"` for full-width buttons and widgets (never use deprecated `use_container_width`).
  - Use `st.html(html_code)` for inline HTML/JS components (never use deprecated `st.components.v1.html`).
  - Silence harmless Pydantic serialization warnings via `warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")`.
- **Mermaid Diagram Sanitization:**
  - Enforce `flowchart TD` top-to-bottom layout with concise 5-8 word nodes.
  - Wrap decision node text containing parens or special characters in quotes (`C{"Label (parens)?"}`).
  - Convert arrow labels to standard `A -->|Text| B` format.
  - Strip hallucinated `Unsupported markdown: list` text.

Workflow & Dual-Review Pipeline

1. **Coding Phase:** The primary coding agent (Gemini 3.6 Flash / Antigravity) implements feature requests or bug fixes based on groomed GitHub issues.
2. **Testing & DoD:** The coding agent runs the full test suite (`uv run pytest`), commits code changes directly to `main`, pushes to GitHub, and closes the coding issue.
3. **Dual-Review Phase (Specialized Personas, SonarCloud MCP & Noise Reduction):**
   - After a commit, allow 3–5 minutes for background CI / SonarCloud scanning to complete.
   - Reviewers inspect the codebase while ignoring non-source noise (`uv.lock`, binary databases `*.duckdb`, `.pytest_cache`, `__pycache__`).
   - Every reviewer report MUST start with a standardized YAML frontmatter header (`risk_score: 1-5`, `breaking_changes: true|false`, `effort_estimate: low|medium|high`).
   - **Claude 3.5 Sonnet (`review/claude-review.md`):** Focuses on *Structural Integrity, Modular Architecture, Security Vulnerability Bounds (Path Traversal, Prompt/SQL Injections via SonarCloud MCP `denis911_ai-consilium`), Documentation, & Test-Coverage Rigor*. Results saved to `review/YYYY-MM-DD-code-review-Claude-N.md`.
   - **Google Jules (`review/jules-review.md`):** Triggered by creating a GitHub issue tagged `[jules]` (`gh issue create --title "[jules] Code Review Request..." --body "..."`). Google Jules (cloud agent) performs the code review independently and submits a GitHub Pull Request (PR) containing `review/YYYY-MM-DD-code-review-jules-N.md`.
4. **PR Merge & Execution Phase:**
   - Coding agent merges Jules' PR via `gh pr merge <PR_NUM> --merge` (or `--squash`).
   - Coding agent pulls `main` locally (`git pull origin main`).
   - Coding agent reads and discusses the review report with the user, grooming any critical findings (`risk_score >= 3`) into new high-priority GitHub issues before proceeding.