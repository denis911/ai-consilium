Commands

- `uv sync` - install dependencies
- `uv run pytest` - the whole suite
- `uv run pytest tests/test_home.py` - one test file

Rules

- Dependencies are added in `pyproject.toml`. Do not add one without asking.

Workflow & Dual Review Pipeline

1. **Coding Phase:** The primary coding agent (Gemini 3.6 Flash / Antigravity) implements feature requests or bug fixes based on groomed GitHub issues.
2. **Testing & DoD:** The coding agent runs the full test suite (`uv run pytest`), commits code changes directly to `main`, pushes to GitHub, and closes the coding issue.
3. **Claude Review Phase:** Code is reviewed in a separate conversation context with Claude.
4. **Jules Review Trigger:** A GitHub issue labeled `jules` (e.g. `[jules]`) is created to trigger Google Jules for a secondary code integrity review. Jules inspects the codebase, writes findings to `review/YYYY-MM-DD-code-review-jules.md`, and commits only that review file.