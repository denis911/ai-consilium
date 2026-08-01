Commands

- `uv sync` - install dependencies
- `uv run pytest` - the whole suite
- `uv run pytest tests/test_home.py` - one test file

Rules

- Dependencies are added in `pyproject.toml`. Do not add one without asking.

Workflow & Multi-Agent Tri-Review Pipeline

1. **Coding Phase:** The primary coding agent (Gemini 3.6 Flash / Antigravity) implements feature requests or bug fixes based on groomed GitHub issues.
2. **Testing & DoD:** The coding agent runs the full test suite (`uv run pytest`), commits code changes directly to `main`, pushes to GitHub, and closes the coding issue.
3. **Tri-Review Phase (Specialized Personas, SonarCloud MCP & Noise Reduction):**
   - After a commit, allow 3–5 minutes for background CI / SonarCloud scanning to complete.
   - Reviewers inspect the codebase while ignoring non-source noise (`uv.lock`, binary databases `*.duckdb`, `.pytest_cache`, `__pycache__`).
   - Every reviewer report MUST start with a standardized YAML frontmatter header (`risk_score: 1-5`, `breaking_changes: true|false`, `effort_estimate: low|medium|high`).
   - **Claude 3.5 Sonnet (`review/claude-review.md`):** Focuses on *Structural Integrity, Modular Architecture, Documentation, and Test-Coverage Rigor*. Optionally queries SonarCloud MCP (`denis911_ai-consilium`). Results saved to `review/YYYY-MM-DD-code-review-Claude-N.md`.
   - **Google Jules (`review/jules-review.md`):** Triggered via `[jules]` tagged issue. Performs *Native Idiomatic Code Alignment, DuckDB/LiteLLM Framework Optimizations, & Async Concurrency* audits without Sonar MCP dependency. Results saved to `review/YYYY-MM-DD-code-review-jules-N.md`.
   - **OpenAI Codex (`review/codex-review.md`):** Focuses on *Security Vulnerabilities, Boundary Conditions, Type Safety, and Algorithmic Performance*. Optionally queries SonarCloud MCP (`denis911_ai-consilium`). Results saved to `review/YYYY-MM-DD-code-review-Codex-N.md`.
4. **"Two-Out-Of-Three" Majority Rule & Risk-Based Grooming:**
   - **High-Priority Critical Items:** Any flaw with `risk_score >= 3` or flagged by **at least 2 out of 3 reviewers** is groomed into a high-priority GitHub issue.
   - **Lower-Priority Quality Refinements:** Single-reviewer nitpicks or low risk items (`risk_score < 3`) are groomed as lower-priority tasks.
5. **PR Merge & Execution:** Merge Jules' PR via `gh pr merge <PR_NUM> --merge`, pull `main` locally, groom consensus findings into new GitHub issues, and proceed with coding.