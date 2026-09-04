---
name: ponytail
description: >-
  Audit code for over-engineering, bloat, dead code, and speculative complexity using Ponytail lean-coding principles. Use when the user asks for /ponytail-review, lean code audit, diff minimization, or anti-bloat evaluation.
---

# ✂️ Ponytail Lean-Coding & Anti-Bloat Skill

This skill provides an on-demand audit mechanism to evaluate git diffs, proposed features, or existing modules against **Ponytail lean-coding principles**.

## When to Use

- When the user types `/ponytail-review` in chat.
- When reviewing a PR or git diff before committing.
- When auditing existing repository modules to identify dead code, speculative wrappers, or opportunities for code deletion.

---

## The Ponytail Audit Rubric

When auditing code, apply the following four checks strictly:

### 1. The "Ask Why First" & Minimal Viable Diff Check
- **Question**: Is every newly introduced class, function, or helper strictly necessary to fulfill the task requirements?
- **Red Flags**:
  - Helpers added "just in case" or for hypothetical future use cases.
  - Multi-line refactors in unrelated sections of the file.
  - Opportunistic reformatting that bloats the diff.
- **Remedy**: Strip all non-essential changes until only the minimal viable diff remains.

### 2. The Premature Abstraction Check
- **Question**: Does the code wrap an existing framework (DuckDB, LiteLLM, Streamlit, Pydantic) with unnecessary layers of indirection?
- **Red Flags**:
  - Wrapper classes that merely pass through calls to library functions.
  - Custom abstraction factories where a single direct function call suffices.
  - Generic config or handler hierarchies for single-use logic.
- **Remedy**: Collapse abstractions into direct, idiomatic framework calls.

### 3. The Dead Code & Duplication Check
- **Question**: Can existing code be deleted or consolidated?
- **Red Flags**:
  - Unused imports, orphaned variables, or uncalled internal helpers.
  - Duplicate logic implemented across multiple files instead of reusing existing utilities.
  - Commented-out legacy code or obsolete docstrings.
- **Remedy**: Propose explicit deletion of dead lines.

### 4. The Test & Doc Integrity Guardrail
- **Question**: Has production code been pruned without weakening tests or documentation?
- **Rule**: Lean coding applies to **production code**. Full `pytest` test suite coverage, edge-case assertions, and clean public docstrings must remain intact.

---

## Execution Workflow

1. **Target Identification**:
   - If auditing recent changes: inspect `git diff HEAD~1..HEAD` or `git status`.
   - If auditing a specific file/module: read the target source file(s).
2. **Evaluation**:
   - Apply the 4 rubric checks above.
3. **Structured Report**:
   - Deliver findings in a concise format:
     - **Over-Engineering Findings**: Speculative abstractions or unnecessary wrappers.
     - **Dead Code Identified**: Specific lines/functions eligible for immediate deletion.
     - **Minimal Viable Diff (MVD) Recommendations**: Exact surgical replacements.
     - **Estimated LoC Reduction**: Number of lines saved by adopting the lean design.
