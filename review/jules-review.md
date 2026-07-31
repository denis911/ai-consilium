---
name: "🔍 Jules Code Review"
about: Trigger Jules to run a second-layer audit on the latest commits.
title: "Review changes and create file review/{{ date }}-code-review-jules"
labels: [jules]
---

**Task Goal**: Act strictly as a secondary Code Integrity Reviewer.

**Execution Constraints**:
1. Scan all files modified in the latest commit.
2. Evaluate the structural integrity of the code and audit Gemini's newly generated unit tests for logic flaws or hallucinations.
3. **CRITICAL**: Do NOT change, refactor, or edit any existing source files. You are explicitly restricted from modifying application code.
4. Summarize your findings, edge-case evaluations, and potential security bugs into a single markdown file located at: `review/{{ date }}-code-review-jules.md`.
5. Commit only that markdown file to the repository.

