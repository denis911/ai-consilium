---
risk_score: 2
breaking_changes: false
effort_estimate: medium
sonar_status: PASSED
---

# 🏛️ AI Consilium — Claude Structural & Security Review

> **Reviewer persona:** Structural Integrity, Modular Architecture, Security, Documentation & Test-Coverage Rigor
> **Review date:** 2026-08-03
> **Commit ref:** `0c3317c` (latest on `main`)
> **Commits reviewed:** last ~25 commits (2026-07-31 → 2026-08-03)
> **SonarCloud project:** `denis911_ai-consilium` — Quality Gate: ✅ **PASSED**
> **Prior review:** `2026-08-01-code-review-Claude.md`

---

## SonarCloud Dashboard (Fresh — Scanned 2026-08-02)

| Metric | Value | Δ from last review | Assessment |
|---|---|---|---|
| Quality Gate | ✅ PASSED | — | All new-code conditions green |
| Bugs | 0 | = | ✅ Clean |
| Vulnerabilities | 3 | = | 🟠 Dockerfile only (unchanged) |
| Code Smells | 25 | ↑ from 16 | 🟡 New smells introduced by `_sanitize_mermaid_code` + OpenRouter fallback logic |
| Duplication | 0.0% | = | ✅ Excellent |
| Lines of Code | 2 231 | ↑ from 2 123 | Expected — new features added |
| Cyclomatic Complexity | 292 | ↑ from 263 | 🟡 Two new high-complexity functions |
| Technical Debt Ratio | 0.4% | ↑ from 0.2% | Still very low overall |
| Security Hotspots | 0 | = | ✅ All reviewed and clear |

The gate passing is correct — all new-code conditions pass. The upward trend in complexity and smells is the main story this review.

---

## What's New Since 2026-08-01 — Changes Reviewed

| Commit | Change |
|---|---|
| `c683725` | Model slug updates: xAI → `grok-4.5`, Anthropic → `claude-sonnet-5` |
| `ceff480` | xAI: `grok-2-1212`; fix `completion_cost` dict; disable LiteLLM background telemetry workers |
| `81adb9f` | Anthropic slug, xAI Grok-2, DeepSeek OpenRouter slug |
| `0b98049` | Streamlit `use_container_width` → `width='stretch'` |
| `caeed0b` | All 6 provider API key indicators in sidebar |
| `6e12e26` | Mermaid paren sanitizer + reveal direct API errors in fallback |
| `9d2288c` | Mermaid syntax sanitizer + OpenRouter fallback for direct API errors |
| `b3cc0b5` | Auto-quote decision nodes; migrate to `st.html` |
| `9e833d8` | Responsive Mermaid renderer; silence Pydantic warnings |
| `6b8e944` | Clean up Mermaid code block init and formatting |

---

## 🟠 Issues Requiring Attention

### 1. `_sanitize_mermaid_code` Cognitive Complexity = 24 — Newly Introduced (synthesizer.py L30)

**Sonar Rule:** `python:S3776` | **Severity:** CRITICAL

The new `_sanitize_mermaid_code` module-level function has complexity 24 against a threshold of 15. It contains:
- Two nested `re.sub` with inline `def` closures (`fix_decision_node`, `fix_node_parens`) — each closure adds complexity
- A manual `& node split` expansion block with `if/for/continue`
- Regex string manipulation across 5 separate mutation steps

This is real complexity, not a false positive. The closure-inside-loop pattern is also a minor performance concern: `fix_decision_node` and `fix_node_parens` are defined fresh on every loop iteration (once per Mermaid line).

**Fix:** Define the two closures as named module-level functions, and extract the `& node` expander into its own helper:

```python
def _fix_decision_node(m) -> str: ...      # module level
def _fix_node_parens(m) -> str: ...        # module level
def _expand_and_nodes(line: str) -> list[str]: ...  # module level

def _sanitize_mermaid_code(code: str) -> str:
    ...
    for line in lines:
        line = line.replace(...)
        line = re.sub(r'...', _fix_decision_node, line)
        line = re.sub(r'...', _fix_node_parens, line)
        expanded = _expand_and_nodes(line)
        cleaned_lines.extend(expanded)
```

This reduces `_sanitize_mermaid_code` to ~8 complexity and makes each transformation independently testable.

---

### 2. `_query_single_provider` Cognitive Complexity = 33 (providers.py L105)

**Sonar Rule:** `python:S3776` | **Severity:** CRITICAL

The OpenRouter fallback logic doubled the size and complexity of `_query_single_provider`. The function now:
1. Builds `call_kwargs`
2. Conditionally adds OpenRouter headers (first call)
3. Attempts the direct `litellm.acompletion()`
4. On failure: looks up `_get_openrouter_fallback_slug()`
5. Mutates `call_kwargs` again for the fallback
6. Conditionally adds headers again (fallback call)
7. Attempts the fallback `litellm.acompletion()`
8. On fallback failure: re-raises the original error
9. Catches `TimeoutError`, `Exception` at the outer level

The result is a triple-nested try/except with two near-duplicate `asyncio.wait_for` blocks. This is a genuine structural problem: the two `wait_for` blocks are identical except for which model is in `call_kwargs`.

**Fix:** Extract a `_execute_llm_call(call_kwargs, timeout_val) -> response` coroutine and call it from both the primary and fallback paths:

```python
async def _execute_llm_call(self, call_kwargs: dict, timeout_val: float):
    """Single litellm call with optional asyncio timeout wrapper."""
    if timeout_val > 0:
        return await asyncio.wait_for(litellm.acompletion(**call_kwargs), timeout=timeout_val)
    return await litellm.acompletion(**call_kwargs)
```

This reduces `_query_single_provider` from 33 to ~15 complexity.

---

### 3. Duplicate String Literals — Define Constants (providers.py)

**Sonar Rules:** `python:S1192` | **Severity:** CRITICAL (×3 new issues)

Sonar flagged three new string duplication violations introduced since the last review:
- `"anthropic/claude-sonnet-5"` appears 3 times: `DEFAULT_MODELS` L22, `model_key_mapping` L82, `_get_openrouter_fallback_slug` L99
- `"xai/grok-4.5"` appears 3 times: `DEFAULT_MODELS` L25, `model_key_mapping` L85, `_get_openrouter_fallback_slug` L100
- `"openrouter/"` prefix appears 3+ times in conditional checks

If a model slug needs to change again (as happened multiple times in the past two weeks: `grok-2` → `grok-2-1212` → `grok-4.5`; `claude-3-5-sonnet` → `claude-sonnet-5`), you currently have to update it in 3 places and risk a mismatch. This was the root cause of the key-mismatch bugs found in reviews #2 and #3.

**Fix:** Define module-level slug constants:

```python
# council/providers.py
MODEL_CLAUDE     = "anthropic/claude-sonnet-5"
MODEL_XAI        = "xai/grok-4.5"
MODEL_O3         = "o3-mini"
MODEL_GEMINI     = "gemini/gemini-2.5-flash"
MODEL_PERPLEXITY = "perplexity/sonar"
MODEL_DEEPSEEK   = "openrouter/deepseek/deepseek-r1"
OPENROUTER_PREFIX = "openrouter/"

DEFAULT_MODELS = [MODEL_O3, MODEL_CLAUDE, MODEL_GEMINI, MODEL_PERPLEXITY, MODEL_XAI, MODEL_DEEPSEEK]
```

One-line change when a slug needs updating. Zero risk of mismatches between `DEFAULT_MODELS`, `model_key_mapping`, and `_get_openrouter_fallback_slug`.

---

### 4. `_sanitize_mermaid_code` Has a Subtle Variable Shadowing Bug (synthesizer.py L39)

```python
for line in lines:
    l = line          # ← shadows outer scope with single-char variable
    l = l.replace(...)
    ...
    l = re.sub(r'...', fix_decision_node, l)
```

Using `l` as a variable name is both a Sonar `python:S1066` trigger and a genuine readability/debugging hazard — `l` is visually indistinguishable from `1` in many fonts. The `& node` block at the end also uses `l` but then discards it:

```python
if " & " in l and "-->" in l:    # uses `l`
    ...
    continue
cleaned_lines.append(l)          # also uses `l`
```

This is correct but only because `l` was last set by the preceding `re.sub`. If a future edit reorders transformations and sets `l` to something else before the `& node` check, the logic breaks silently.

**Fix:** Use a descriptive name (`line` is fine since the outer `for line in lines` loop variable is immediately reassigned):
```python
for raw_line in lines:
    line = raw_line
    line = line.replace(...)
    ...
```

---

### 5. Conflicting System Prompt Still Present (synthesizer.py L105-L121)

This was flagged in `2026-07-31-code-review-Claude-3.md` and is **still unresolved**. The system prompt remains a concatenation of two conflicting instructions (missing a separator between the closing `}` of the JSON schema example and the start of the second sentence):

```python
"}"                                          # ← end of JSON example
"You are an executive AI Consilium..."       # ← immediately concatenated, no \n
```

The LLM receives: `}You are an executive AI Consilium Synthesizer...`. Frontier models handle this gracefully, but it's technically malformed and will cause issues with stricter models or future Anthropic instruction-following rules. The `responses_formatted` variable computed at L98-L101 is also still dead code — built but never referenced in the prompt.

This has been open for 3 days across 3 reviews. Simple fix — 5 minutes.

---

### 6. `render_mermaid_diagram` Injects Unsanitized Mermaid Code into HTML (app.py L86-97)

**Security classification:** Low-severity XSS vector (mitigated by context)

```python
def render_mermaid_diagram(mermaid_code: str):
    html_code = f"""
    <div class="mermaid" ...>
      {mermaid_code}        ← injected directly into HTML
    </div>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/..."></script>
    """
    st.html(html_code)
```

`mermaid_code` comes from an LLM response that has been through `_sanitize_mermaid_code()` but not through HTML escaping. If a model outputs Mermaid containing `</div><script>alert(1)</script>`, it would be injected into the page DOM. In a single-user local app this is low risk — the attacker would have to compromise the LLM response. In a multi-user or hosted deployment it's a meaningful XSS vector.

`_sanitize_mermaid_code` already strips the ```` ```mermaid ```` fences. Adding `html.escape()` before injection, then letting Mermaid's JS renderer parse the escaped text, is the correct fix:

```python
import html as html_lib

def render_mermaid_diagram(mermaid_code: str):
    safe_code = html_lib.escape(mermaid_code)
    html_code = f"""
    <div class="mermaid" ...>
      {safe_code}
    </div>
    ...
    """
    st.html(html_code)
```

Mermaid.js parses the text content of the `<div>`, so HTML-escaping the raw code won't break rendering.

---

### 7. `main()` Complexity Still at 54 (app.py L100)

**Sonar Rule:** `python:S3776` | **Severity:** CRITICAL | **Open since:** 2026-07-30

`main()` has grown from 51 → 54 complexity. This has been flagged in every review. The `render_mermaid_diagram` extraction is a good sign (function-per-concern thinking), but the main() body itself wasn't refactored. Three helper functions would bring this under the threshold:

- `_render_sidebar(telemetry) -> (use_free_tier, selected_models, vault_path)` (~20 lines)
- `_run_research_pipeline(query, rag_input, selected_models, use_free_tier) -> artifact, run_id` (~30 lines)
- `_render_results(artifact, vault_path, telemetry, run_id)` (~40 lines)

This is the single highest-impact structural refactor available in the codebase.

---

## ✅ Positive Changes — Well Done

| Change | Assessment |
|---|---|
| `litellm.turn_off_message_logging = True` + `litellm.telemetry = False` | ✅ Correct — stops background threads from interfering with Streamlit |
| OpenRouter fallback when direct API fails | ✅ Good resilience pattern; well-thought-out |
| `_get_openrouter_fallback_slug()` as separate method | ✅ Clean separation of mapping from query logic |
| `width="stretch"` replacing deprecated `use_container_width` | ✅ Per AGENTS.md Streamlit rules — consistent |
| `st.html()` for Mermaid rendering | ✅ Per AGENTS.md rules; correct API |
| Free-tier disclaimer caption | ✅ Addressed from 2026-08-01 review |
| `completion_cost` dict/float branch handling | ✅ Correct defensive extraction |
| Pydantic warning suppression at module level | ✅ Matches AGENTS.md rules |
| All 6 API key indicators in sidebar | ✅ Good UX — no longer missing xAI/OpenRouter |
| `fallback_mermaid` now uses `flowchart TD` + runs through `_sanitize_mermaid_code` | ✅ Consistent |

---

## ⚠️ Unchanged Sonar Issues (Carried Over — Not Newly Introduced)

These were flagged in prior reviews and remain open. Carrying forward for completeness:

| Issue | File | Rule | Effort |
|---|---|---|---|
| `logger.error()` in except → should be `logger.exception()` | `providers.py` L216, `ingest.py` L92 | S8572 | 2 lines |
| Redundant `f""` without interpolation | `exporter.py` L106, L109 | S3457 | 2 lines |
| Backtracking regex in YAML frontmatter parser | `ingest.py` L36 | S8786 | 5 lines |
| `compute_consensus` complexity = 21 | `consensus.py` | S3776 | ~10 lines |
| `format_markdown` complexity = 18 | `exporter.py` | S3776 | ~8 lines |
| `_extract_outermost_json` complexity = 29 | `synthesizer.py` | S3776 | ~5 lines |
| `COPY . /app` in Dockerfile | `Dockerfile` | docker:S6470 | 2 lines |
| Container runs as root | `Dockerfile` | docker:S6471 | 2 lines |

---

## Priority Action List — Today's New Items Only

| Priority | Finding | File | Effort | Sonar |
|---|---|---|---|---|
| 🟠 Soon | Extract closures from `_sanitize_mermaid_code`; reduce complexity to <15 | `synthesizer.py` L30 | ~20 lines | S3776 |
| 🟠 Soon | Extract `_execute_llm_call` coroutine; reduce `_query_single_provider` to <15 | `providers.py` L105 | ~10 lines | S3776 |
| 🟠 Soon | Define slug constants; eliminate 3× string duplication | `providers.py` | ~10 lines | S1192 |
| 🟠 Persistent | Clean up conflicting system prompt + remove dead `responses_formatted` variable | `synthesizer.py` L98-L121 | 5 min | — |
| 🟡 Security | HTML-escape `mermaid_code` before injecting into `st.html()` | `app.py` L90 | 2 lines | — |
| 🟡 Style | Rename `l` → `line` in `_sanitize_mermaid_code` loop | `synthesizer.py` L39 | 1 line | — |
| 🟢 Structural | Refactor `main()` into 3 helper functions | `app.py` | ~30 lines | S3776 |

---

## Model Roster Assessment (Updated)

`DEFAULT_MODELS` as of 2026-08-03:
```python
["o3-mini", "anthropic/claude-sonnet-5", "gemini/gemini-2.5-flash", "perplexity/sonar", "xai/grok-4.5", "openrouter/deepseek/deepseek-r1"]
```

This is now **6 models** (previously 5). The addition is noted — wider ensemble = better disagreement detection, but also ~20% higher per-query cost and latency. One item to verify: `claude-sonnet-5` is a very new model slug — confirm it is available in your Anthropic account tier and via the API `/v1/models` endpoint before treating it as primary. LiteLLM may route to an older slug silently if the new one is unrecognized.

`xai/grok-4.5` was similarly a rapid iteration from `grok-2` → `grok-2-1212` → `grok-4.5` over a few days. Both new slugs are worth a one-time `curl` verification before each wave of commits that rely on them.

This is exactly what the **Context7 MCP Verification Rule** in `AGENTS.md` is designed to catch — worth enforcing before each model slug change.

---

*Review conducted in read-only mode. No source files modified. SonarCloud MCP used for static analysis enrichment (data timestamp: 2026-08-02T20:09 UTC).*
