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
- Audit async concurrency, memory lifecycle, and resource lock safety.

**Execution Constraints**:
1. Scan all files modified in the latest commit(s).
2. Evaluate structural integrity, framework utilization, and async safety without touching application source files.
3. **CRITICAL**: Do NOT change, refactor, or edit any existing source files. You are explicitly restricted from modifying application code.
4. Summarize your findings into a single markdown file located at: `review/YYYY-MM-DD-code-review-jules.md` (increment to `-2.md`, `-3.md`, etc., if multiple runs occur on the same day).
5. Commit only that markdown file to the repository (or submit a documentation PR).

