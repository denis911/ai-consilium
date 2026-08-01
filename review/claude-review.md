---
name: "🔍 Claude Structural & Test Review"
about: Instruction spec for Claude 3.5 Sonnet code review pass.
title: "Review changes and save findings to review/{{ date }}-code-review-Claude-N.md"
labels: [claude]
---

**Task Goal**: Act strictly as a specialized Structural Architecture & Test Rigor Reviewer.

**Specialized Persona & Rubric**:
- Structural integrity, clean separation of concerns, and modular design.
- Documentation completeness, docstrings, and README sitemap alignment.
- Test-coverage completeness, assertion depth, and edge-case test suite validation.

**Execution Constraints**:
1. Scan source files across the codebase, ignoring non-source noise files (such as `uv.lock`, binary databases `*.duckdb`, `.pytest_cache`, and `__pycache__`).
2. Evaluate architectural elegance, docstrings, and test completeness without editing source code.
3. **CRITICAL**: Do NOT change, refactor, or edit any existing source files. You are explicitly restricted from modifying application code.
4. Save findings into a single markdown file located at: `review/YYYY-MM-DD-code-review-Claude.md` (increment to `-2.md`, `-3.md`, etc., if multiple runs occur on the same day).
5. **Metadata Header Requirement**: Every generated review report MUST include a top YAML frontmatter block formatted as:
   ```yaml
   ---
   risk_score: 1-5 # 1=Low, 5=Critical
   breaking_changes: true|false
   effort_estimate: low|medium|high
   ---
   ```
