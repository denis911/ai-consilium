# Ponytail: Lean Coding & Anti-Overengineering Guardrails

This project enforces **Ponytail** lean-coding principles for all implementation and bug-fixing tasks.

## Core Directives

1. **Ask "Why?" First (Minimal Viable Diff)**:
   - Before introducing any new code, function, or file, challenge whether it is strictly required to fulfill the issue.
   - Aim for the smallest, most surgical diff that satisfies the requirements and passes the automated test suite.
   - Never perform opportunistic refactoring, unsolicited stylistic reformatting, or speculative code organization.

2. **Resist Premature Abstraction**:
   - Do not build generic frameworks, abstract wrapper classes, or deep inheritance hierarchies when a simple, direct function will do.
   - Avoid creating extra layers of indirection around existing libraries (such as DuckDB, LiteLLM, or Streamlit). Use framework idioms directly.
   - Do not build for hypothetical future extensions; solve only the concrete requirement described in the issue.

3. **Delete Rather Than Add**:
   - Whenever touching an existing module, identify and eliminate dead code, redundant helpers, and obsolete comments.
   - Prefer reusing existing functions across the repository over implementing duplicate logic.

4. **Preserve Test Rigor and Documentation**:
   - Lean coding applies strictly to **production logic**. 
   - Never cut corners on test coverage: comprehensive `pytest` assertions, edge-case coverage, and clear docstrings for public interfaces remain mandatory.
