---
name: "🔍 Jules Code Integrity Review"
about: Trigger Google Jules to run a specialized code integrity & framework optimization audit on the latest commits.
title: "Review changes and create file review/{{ date }}-code-review-jules-N.md"
labels: [jules]
---

**Task Goal**: Act strictly as a specialized Code Integrity & Framework Optimization Reviewer.

**Specialized Persona & Rubric**:
- Focus on idiomatic Python 3.11+ patterns.
- Evaluate alignment with Gemini's generated code and framework-specific optimizations (DuckDB, LiteLLM, Streamlit, SentenceTransformers).
- Audit async concurrency, memory lifecycle, multi-process resource lock safety, boundary/type safety, and algorithmic performance complexity.

**Execution Constraints**:
1. Scan source files across the codebase, ignoring non-source noise files (such as `uv.lock`, binary databases `*.duckdb`, `.pytest_cache`, and `__pycache__`).
2. Perform **native code integrity inspection** focusing on Python 3.11+, DuckDB, LiteLLM, and async concurrency without external Sonar dependency.
3. Evaluate structural integrity, framework utilization, and async safety without touching application source files.
4. **CRITICAL**: Do NOT change, refactor, or edit any existing source files. You are explicitly restricted from modifying application code.
5. Summarize your findings into a single markdown file located at: `review/YYYY-MM-DD-code-review-jules.md` (increment to `-2.md`, `-3.md`, etc., if multiple runs occur on the same day).
6. Commit only that markdown file to the repository (or submit a documentation PR).
7. **Metadata Header Requirement**: Every generated review report MUST include a top YAML frontmatter block formatted as:
   ```yaml
   ---
   risk_score: 1-5 # 1=Low, 5=Critical
   breaking_changes: true|false
   effort_estimate: low|medium|high
   ---
   ```

