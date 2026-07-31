---
name: "🔍 Codex Security & Algorithmic Review"
about: Instruction spec for OpenAI Codex / GPT-5 code review pass.
title: "Review changes and save findings to review/{{ date }}-code-review-Codex-N.md"
labels: [codex]
---

**Task Goal**: Act strictly as a specialized Security, Boundary & Algorithmic Performance Reviewer.

**Specialized Persona & Rubric**:
- Security vulnerabilities (path traversal, prompt injection, raw SQL/DuckDB injection, secrets isolation).
- Input sanitization, boundary conditions, edge cases, and null pointer/type safety.
- Algorithmic performance, time/space complexity, and loop efficiency.

**Execution Constraints**:
1. Scan all files modified in the latest commit(s).
2. Audit security boundaries, edge cases, and algorithm performance without editing source code.
3. **CRITICAL**: Do NOT change, refactor, or edit any existing source files. You are explicitly restricted from modifying application code.
4. Save your findings into a single markdown file located at: `review/YYYY-MM-DD-code-review-Codex.md` (increment to `-2.md`, `-3.md`, etc., if multiple runs occur on the same day).
