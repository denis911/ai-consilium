---
risk_score: 3
breaking_changes: false
effort_estimate: low
sonar_status: FAILED
---

# 🏛️ AI Consilium — Claude Structural & Security Review

> **Reviewer persona:** Structural Integrity, Modular Architecture, Security, Documentation & Test-Coverage Rigor
> **Review date:** 2026-08-03 (second pass today)
> **Commit ref:** `c267946` (latest on `main`)
> **Commits reviewed since morning:** `5294517` → `c267946` (~12 commits)
> **SonarCloud project:** `denis911_ai-consilium` — Quality Gate: ❌ **FAILED**
> **Prior review:** `2026-08-03-code-review-Claude.md`

---

## ❌ SonarCloud Quality Gate: FAILED

**The gate is failing on new code duplication: 13.9% vs the 3% threshold.**

| Metric | Value | Δ from morning | Gate |
|---|---|---|---|
| Quality Gate | ❌ FAILED | — | `new_duplicated_lines_density` = 13.9% (threshold: 3%) |
| Bugs | 0 | = | ✅ |
| Vulnerabilities | 3 | = | ✅ (Dockerfile only) |
| Code Smells | 22 | ↓ from 25 | ✅ Improving |
| Duplication (overall) | 1.5% | ↑ from 0.0% | 🔴 New |
| Lines of Code | 2 328 | ↑ from 2 231 | Expected (new `main.py` CLI) |
| Cyclomatic Complexity | 307 | ↑ from 292 | 🟡 Continues climbing |
| Security Hotspots | 0 | = | ✅ |

The root cause is confirmed via `get_duplications`: **the RAG context budget logic is duplicated verbatim between `app.py` (L189–L212) and `main.py` (L81–L103).**

---

## 🔴 Issue #1: Duplicated RAG Context Budget Logic — Quality Gate Breaker

**Files:** `app.py` L189–L212 and `main.py` L81–L103
**Sonar rule:** Implicit duplication detection (13.9% new code duplication)
**Confirmed by:** `get_duplications` API — exact block match, 22–24 lines

The entire vault RAG retrieval + budget cap loop was copy-pasted from `app.py` into `main.py`:

```python
# Identical in both files:
for r in vault_results:
    snippet_title = r['title']
    snippet_content = r['content'].strip()
    if "## 📊 Consensus Architecture" in snippet_content:
        snippet_content = snippet_content.split("## 📊 Consensus Architecture")[0].strip()
    elif "## 🔍 Multi-Model Raw Provider Responses" in snippet_content:
        snippet_content = snippet_content.split("## 🔍 Multi-Model Raw Provider Responses\")[0].strip()
    formatted_chunk = f"[Vault Note: {snippet_title}]\n{snippet_content}"
    if current_chars + len(formatted_chunk) > total_char_budget:
        remaining_budget = total_char_budget - current_chars
        if remaining_budget > 100:
            truncated_content = snippet_content[:remaining_budget - 50] + "... [Truncated for Context Budget]"
            context_chunks.append(f"[Vault Note: {snippet_title}]\n{truncated_content}")
        break
    else:
        context_chunks.append(formatted_chunk)
        current_chars += len(formatted_chunk)
```

This will immediately diverge — any future change to RAG budget logic (e.g. changing section headers, adjusting the budget cap, fixing the truncation formula) must be applied in two places. Given the project's velocity of changes, this is a real maintenance risk, not theoretical.

**Fix:** Extract a `_collect_rag_chunks(vault_results, total_char_budget=10000) -> list[str]` function into `council/rag.py` or a new `council/rag_utils.py`, and call it from both `app.py` and `main.py`. This is the minimal fix that resolves the quality gate.

```python
# council/rag.py (or rag_utils.py)
SECTION_STRIP_MARKERS = [
    "## 📊 Consensus Architecture",
    "## 🔍 Multi-Model Raw Provider Responses",
]

def collect_rag_chunks(vault_results: list, total_char_budget: int = 10000) -> list[str]:
    """Apply content stripping and character budget cap to vault RAG results."""
    context_chunks = []
    current_chars = 0
    for r in vault_results:
        snippet_title = r["title"]
        snippet_content = r["content"].strip()
        for marker in SECTION_STRIP_MARKERS:
            if marker in snippet_content:
                snippet_content = snippet_content.split(marker)[0].strip()
                break
        formatted_chunk = f"[Vault Note: {snippet_title}]\n{snippet_content}"
        if current_chars + len(formatted_chunk) > total_char_budget:
            remaining_budget = total_char_budget - current_chars
            if remaining_budget > 100:
                truncated = snippet_content[:remaining_budget - 50] + "... [Truncated for Context Budget]"
                context_chunks.append(f"[Vault Note: {snippet_title}]\n{truncated}")
            break
        context_chunks.append(formatted_chunk)
        current_chars += len(formatted_chunk)
    return context_chunks
```

---

## 🟠 Issue #2: `main()` in `app.py` Complexity = 87 (was 54 this morning)

**Sonar rule:** `python:S3776` | **Severity:** CRITICAL | **Growing fast**

The vault RAG integration added another ~60 lines into `main()` including nested `try/except`, two `if` blocks, two RAG engine instantiations, a `for` loop with inner budget logic, and the `context_chunks` assembly. Complexity jumped from 54 → **87** in a single session — the highest in the project by far. Sonar threshold is 15.

This is now beyond the "gradual refactor" threshold. The three-helper-function split suggested in the morning review is urgent:

- `_run_rag_pipeline(user_query, rag_context_input, use_rag, consensus_engine) -> list[str]` — all RAG logic, ~40 lines
- `_run_consensus_pipeline(query_input, selected_models, use_free_tier) -> (artifact, run_id)` — steps 2–4, ~20 lines
- `_render_results(artifact, vault_path, telemetry, run_id)` — results display, ~60 lines

Keeping the main pipeline steps orchestrated but moving the implementation detail out of `main()` would bring it to ~25 complexity.

---

## 🟠 Issue #3: `run_cli` in `main.py` Complexity = 31 (new file, new issue)

**Sonar rule:** `python:S3776` | **Severity:** CRITICAL | **Newly introduced today**

`main.py`'s `run_cli()` coroutine is new and already has complexity 31, driven by:
- The RAG budget loop (same as `app.py`)
- Nested `try/except` around RAG
- The multi-branch output block (`if args_parsed.json` / `else` + `if artifact.contradictions` / `else` + `if exported_path`)

Extracting `collect_rag_chunks()` (fixing issue #1) would immediately reduce this by ~10 points. The output rendering could be extracted to a `_print_cli_output(artifact, exported_path)` helper.

---

## 🟠 Issue #4: Three New Backtracking Regex Warnings in `_sanitize_mermaid_code` (synthesizer.py L85, L88, L91)

**Sonar rule:** `python:S8786` — *Super-linear performance due to backtracking*
**Severity:** MAJOR (×3 new issues)

Three of the four regexes in `_sanitize_mermaid_code` are flagged:

```python
# L85 — new issue today
re.sub(r'(\b[A-Za-z0-9_]+)\[([^\]]*[\(\)\:\,][^\]]*)\]', _fix_square_bracket_node, line)

# L88 — flagged since morning
re.sub(r'(\b\w+)\s+--\s+([^\-\>]+)\s+-->\s+(\b\w+)', r'\1 -->|\2| \3', line)

# L91 — flagged since morning
re.sub(r'(\b[A-Za-z0-9_]+)\(([^)]*[\(\:\-][^)]*)\)', _fix_node_parens, line)
```

The nested character-class alternations `[^\]]*[\(\)\:\,][^\]]*` and `[^)]*[\(\:\-][^)]*` are the backtracking triggers — each contains two `[^X]*` quantifiers around a required character class, which can cause exponential backtracking on long node labels with no matching special characters.

For Mermaid lines from LLMs these are typically short (< 100 chars), so practical impact is minimal. But Sonar is technically correct — the pattern `[^X]*[Y][^X]*` is equivalent to `[^Y]*Y[^X]*` only when X≠Y, which is nearly always better expressed as an atomic group or possessive quantifier.

**Pragmatic fix:** Add `re.compile()` at module level with `re.DOTALL` off (already the case), and use anchored patterns where possible. For `_fix_square_bracket_node`, the pattern can be simplified:
```python
# Instead of [^\]]*[\(\)\:\,][^\]]*
# Use: match brackets containing any of the target chars, processed minimally
r'(\b[A-Za-z0-9_]+)\[([^\]"]*[(),:][ -][^\]"]*)\]'
```
Alternatively, mark these as `Won't Fix` in Sonar with a rationale note — LLM Mermaid output is bounded in size and the backtracking risk is academic here.

---

## 🟡 Issue #5: `ConsensusEngine()` Instantiated Fresh in `main.py` CLI — No Caching

**File:** `main.py` L116

```python
consensus_engine = ConsensusEngine()   # loads 90MB SentenceTransformer from disk
```

In the Streamlit app, `ConsensusEngine` is correctly `@st.cache_resource`-cached. In the CLI, it's instantiated fresh every run. For a single-invocation CLI tool this is fine — no re-runs within one process. But the `DuckDBRAGEngine` for vault RAG (L79) does **not** pass `shared_model=consensus_engine.model`, meaning the CLI loads the SentenceTransformer **twice** if `--rag` is used:

```python
# main.py
rag_engine = DuckDBRAGEngine(db_path="ai_consilium.duckdb")   # loads its own model instance
...
consensus_engine = ConsensusEngine()                            # loads a second instance
```

This doubles startup memory and time. Fix: instantiate `ConsensusEngine` first, then pass its model:

```python
consensus_engine = ConsensusEngine()
if args_parsed.rag:
    rag_engine = DuckDBRAGEngine(db_path="ai_consilium.duckdb", shared_model=consensus_engine.model)
```

---

## 🟡 Issue #6: LiteLLM Config Set Both at Module Level AND in `__init__` (providers.py + synthesizer.py)

**Files:** `providers.py` L66-70, `providers.py` L78-81, `synthesizer.py` L103-106, `synthesizer.py` L115-118

```python
# Module-level (providers.py L66-70):
litellm.suppress_debug_info = True
litellm.turn_off_message_logging = True
litellm.telemetry = False
litellm.set_verbose = False

# __init__ again (providers.py L78-81) — identical:
litellm.suppress_debug_info = True
litellm.turn_off_message_logging = True
litellm.telemetry = False
litellm.set_verbose = False
```

Same 4-line block appears 4 times across the codebase. This is minor but adds noise and will lead to drift if someone adds a new flag to one block but forgets the others. Extract to a `_configure_litellm()` module-level function called once, or move the config to a single `council/litellm_config.py` module imported by both `providers.py` and `synthesizer.py`.

---

## ✅ Positive Changes Since Morning — Well Done

| Change | Assessment |
|---|---|
| Model slug constants (`MODEL_O3`, `MODEL_CLAUDE`, etc.) | ✅ **Directly resolves morning issue #3** — Sonar's S1192 duplication flags for those strings are now gone |
| `_execute_llm_call()` extracted as standalone coroutine | ✅ **Resolves morning issue #2** — complexity of `_query_single_provider` dropped from 33 → 25 (still above threshold, but improved) |
| `_fix_decision_node`, `_fix_node_parens`, `_expand_and_nodes` extracted to module level | ✅ **Resolves morning issue #1** — closures no longer defined per-iteration |
| `_fix_square_bracket_node` added for `D[Text (parens)]` case | ✅ New sanitization rule correctly handles another Mermaid hallucination pattern |
| Duplicate date prefix stripping in `obsidian_title` export | ✅ Correct fix for the `2026-08-03-2026-08-03-title` filename bug |
| `context_chunks` added to `ConsiliumFinalArtifact` schema | ✅ Enables RAG provenance display in UI — good data lineage |
| `html_lib` imported and available in `app.py` | ✅ The `html.escape()` infrastructure is in place (though not yet used in `render_mermaid_diagram`) — see below |
| Vault RAG sidebar toggle (default OFF) | ✅ Safe cold-start default |
| Conflicting system prompt fixed — `}\n` separator added | ✅ **Resolves the persistent prompt issue from 2026-07-31** — finally clean |
| Dead `responses_formatted` variable removed | ✅ Clean |
| `html_lib` imported | Note: it's imported but `render_mermaid_diagram` still injects `mermaid_code` without escaping (see below) |

---

## 🟡 Issue #7: `render_mermaid_diagram` Still Injects Unsanitized Code (app.py L93)

**Flagged in morning review — still unresolved.**

`html_lib` is now imported (`import html as html_lib` at L86) but not used in `render_mermaid_diagram`:

```python
def render_mermaid_diagram(mermaid_code: str):
    html_code = f"""
    <div class="mermaid" ...>
{mermaid_code}    ← not escaped
    </div>
    ...
    """
    st.html(html_code)
```

The import is there — the fix is one line:
```python
safe_code = html_lib.escape(mermaid_code)
# then use safe_code in the f-string
```

---

## Summary Scorecard

| Area | Morning | Evening | Notes |
|---|---|---|---|
| Quality Gate | ✅ PASSED | ❌ FAILED | New duplication in RAG budget loop |
| Bugs | 0 | 0 | ✅ |
| Duplication | 0% | 1.5% overall / 13.9% new | 🔴 Gate breaker |
| `app.py` `main()` complexity | 54 | 87 | 🔴 Growing fast |
| `main.py` `run_cli()` complexity | N/A (new) | 31 | 🟠 New issue |
| Model slug constants | ❌ Duplicated | ✅ Fixed | Morning fix landed |
| Mermaid helpers extracted | ❌ Closures in loop | ✅ Fixed | Morning fix landed |
| Prompt conflicts | ❌ Persisted | ✅ Fixed | Morning fix landed |
| `html_lib` escape | ❌ Missing | ⚠️ Imported but unused | One line away |
| LiteLLM config deduplication | 🟡 x4 repeats | 🟡 x4 repeats | Not addressed |
| Double model load in CLI `--rag` | N/A | 🟡 New | `shared_model` not passed |

---

## Priority Action List — Evening Pass

| Priority | Finding | File | Effort |
|---|---|---|---|
| 🔴 **Fix now — Gate breaker** | Extract `collect_rag_chunks()` to eliminate duplication | `app.py`, `main.py`, `council/rag.py` | ~20 lines |
| 🟠 Soon | Refactor `main()` into 3 helper functions (complexity 87→~25) | `app.py` | ~30 lines |
| 🟠 Soon | Extract `_print_cli_output()` from `run_cli()` (complexity 31→~15) | `main.py` | ~10 lines |
| 🟡 Quick win | Add `html_lib.escape()` in `render_mermaid_diagram` | `app.py` L93 | 1 line |
| 🟡 Quick win | Pass `shared_model=consensus_engine.model` to `DuckDBRAGEngine` in CLI | `main.py` L79 | 1 line |
| 🟡 Cleanup | Deduplicate 4× LiteLLM config into one function/module | `providers.py`, `synthesizer.py` | ~10 lines |
| 🟢 Consider | Mark S7483 (LiteLLM `timeout=`) as `Won't Fix` in SonarCloud | Sonar UI | 2 clicks |
| 🟢 Consider | Mark S8786 backtracking regex warnings as `Won't Fix` for Mermaid sanitizer | Sonar UI | 3 clicks |

---

*Review conducted in read-only mode. No source files modified. SonarCloud MCP used for static analysis — gate status confirmed as of 2026-08-03T19:30 UTC scan.*
