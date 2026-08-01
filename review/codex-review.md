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
1. Scan source files across the codebase, ignoring non-source noise files (such as `uv.lock`, binary databases `*.duckdb`, `.pytest_cache`, and `__pycache__`).
2. **Optional SonarCloud MCP Enrichment**: Attempt to query SonarQube MCP (`projectKey: denis911_ai-consilium`) for security hotspots, vulnerability ratings, and cognitive complexity metrics.
   - Treat Sonar data as strictly **optional**—if SonarCloud or MCP is unavailable, skip it gracefully and proceed with native code review.
   - **Filter Python Glitches**: Filter out Java-centric or non-idiomatic static analysis false positives.
3. Audit security boundaries, edge cases, and algorithm performance without editing source code.
4. **CRITICAL**: Do NOT change, refactor, or edit any existing source files. You are explicitly restricted from modifying application code.
5. Save your findings into a single markdown file located at: `review/YYYY-MM-DD-code-review-Codex.md` (increment to `-2.md`, `-3.md`, etc., if multiple runs occur on the same day).
6. **Metadata Header Requirement**: Every generated review report MUST include a top YAML frontmatter block formatted as:
   ```yaml
   ---
   risk_score: 1-5 # 1=Low, 5=Critical
   breaking_changes: true|false
   effort_estimate: low|medium|high
   sonar_status: PASSED|FAILED|SKIPPED
   ---
   ```
