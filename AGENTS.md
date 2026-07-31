Commands

- `uv sync` - install dependencies
- `uv run pytest` - the whole suite
- `uv run pytest tests/test_home.py` - one test file

Rules

- Dependencies are added in `pyproject.toml`. Do not add one without asking.

Workflow & Multi-Agent Tri-Review Pipeline

1. **Coding Phase:** The primary coding agent (Gemini 3.6 Flash / Antigravity) implements feature requests or bug fixes based on groomed GitHub issues.
2. **Testing & DoD:** The coding agent runs the full test suite (`uv run pytest`), commits code changes directly to `main`, pushes to GitHub, and closes the coding issue.
3. **Tri-Review Phase (Specialized Personas & Noise Reduction):**
   - **Claude 3.5 Sonnet (`review/claude-review.md`):** Focuses on *Structural Integrity, Modular Architecture, Documentation, and Test-Coverage Rigor*. Results saved to `review/YYYY-MM-DD-code-review-Claude-N.md`.
   - **Google Jules (`review/jules-review.md`):** Triggered via `[jules]` tagged issue. Focuses on *Idiomatic Code Alignment, DuckDB/LiteLLM Framework Optimizations, & Async Concurrency*. Results saved to `review/YYYY-MM-DD-code-review-jules-N.md`.
   - **OpenAI Codex (`review/codex-review.md`):** Focuses on *Security Vulnerabilities, Boundary Conditions, Type Safety, and Algorithmic Performance*. Results saved to `review/YYYY-MM-DD-code-review-Codex-N.md`.
4. **"Two-Out-Of-Three" Majority Rule & Grooming:**
   - **High-Priority Critical Items:** Any performance, logic, security, or structural flaw flagged by **at least 2 out of 3 reviewers** is groomed into a high-priority GitHub issue.
   - **Lower-Priority Quality Refinements:** Single-reviewer nitpicks are groomed as lower-priority tasks.
5. **PR Merge & Execution:** Merge Jules' PR via `gh pr merge <PR_NUM> --merge`, pull `main` locally, groom consensus findings into new GitHub issues, and proceed with coding.