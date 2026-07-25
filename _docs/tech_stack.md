# AI Consilium — Technical Stack Specification (`tech_stack.md`)

## Executive Summary
This document specifies the definitive technical stack for **AI Consilium**. Following Spec-Driven Design (SDD) principles, each selected technology has been chosen for maximum simplicity, local-first zero-dependency execution, and complete alignment with the **DataTalksClub LLM Zoomcamp Capstone rubric** (Target Score: 36/36+ points).

---

## Definitive Winning Technical Stack

```
+-----------------------------------------------------------------------------------+
| 1. USER INTERFACE          | Streamlit (Interactive Dashboard & Audit Tab)        |
+----------------------------+------------------------------------------------------+
| 2. DATA VALIDATION SCHEMAS | Pydantic v2 (Strict JSON Output Contracts)           |
+----------------------------+------------------------------------------------------+
| 3. ASYNC ORCHESTRATION     | LiteLLM + Python asyncio (5 Frontier APIs & Free)    |
+----------------------------+------------------------------------------------------+
| 4. HYBRID RAG & AUDIT DB   | DuckDB (Embedded Vector VSS + Keyword FTS)           |
+----------------------------+------------------------------------------------------+
| 5. EMBEDDING ENGINE        | FastEmbed / sentence-transformers (all-MiniLM-L6-v2) |
+----------------------------+------------------------------------------------------+
| 6. EXPORTER & VISUALS      | Mermaid.js + Atomic Python pathlib (Obsidian Vault)  |
+----------------------------+------------------------------------------------------+
| 7. PACKAGING & DEPLOYMENT  | uv Workspace (pyproject.toml) + Docker Compose       |
+-----------------------------------------------------------------------------------+
```

---

## Component Specifications

### 1. User Interface: Streamlit (`app.py`)
- **Role:** Single-page interactive dashboard & monitoring console.
- **Key Capabilities:**
  - Real-time query progress trackers across the 5 LLM providers.
  - Interactive Consensus Gauge metric (0–100%).
  - Built-in Mermaid.js diagram viewer.
  - Dedicated **Audit History & Telemetry Tab** reading from DuckDB.
  - One-click "Export to Obsidian Vault" action.

### 2. Data Validation: Pydantic v2
- **Role:** Strict schema contract enforcement for multi-model outputs and LLM-as-a-Judge evaluations.
- **Key Schemas:**
  - `ConsiliumQueryInput`: Query text, retrieved RAG context chunks, target model selection.
  - `ModelResponsePayload`: Raw response string, latency in ms, token usage, cost estimate.
  - `ConsensusSynthesisOutput`: Numerical consensus score, verified consensus points, contradiction log, generated Mermaid chart syntax, recommended Obsidian note title/tags.

### 3. Async Orchestration: LiteLLM + `asyncio`
- **Role:** Parallel HTTP prompt execution engine (`council/providers.py`).
- **Key Capabilities:**
  - Concurrent `asyncio.gather()` execution across 5 frontier models: OpenAI (`gpt-4o`), Anthropic (`claude-3-5-haiku`), Gemini (`gemini-2.5-flash`), Perplexity (`sonar`), xAI (`grok-2`).
  - Built-in 1-click fallback to OpenRouter's 100% free tier (`:free`) for $0 developer testing.
  - Isolate and gracefully catch provider timeouts/failures without breaking the pipeline.

### 4. Hybrid RAG & Audit Storage: DuckDB (`council/rag.py` & `telemetry.py`)
- **Role:** Embedded, zero-dependency local database file (`ai_consilium.duckdb`).
- **Key Capabilities:**
  - **Dense Vector Search:** Uses DuckDB `vss` extension with HNSW indexing for cosine distance embedding retrieval.
  - **Sparse Keyword Search:** Uses DuckDB `fts` extension for BM25 text ranking.
  - **Audit Logging:** Stores query execution records, per-model latencies, token consumption, and consensus scores in a `query_logs` table.

### 5. Local Embedding Engine: FastEmbed / `sentence-transformers`
- **Role:** Offline CPU embedding generation (`all-MiniLM-L6-v2`).
- **Key Capabilities:**
  - 384-dimensional dense vector representations.
  - 100% offline, zero API fees, fast CPU inference (<50ms).

### 6. Exporter & Visualizations: Mermaid.js & `pathlib` (`council/exporter.py`)
- **Role:** Output formatter for local knowledge bases.
- **Key Capabilities:**
  - Direct atomic file writes to `OBSIDIAN_VAULT_PATH` configured in `.env`.
  - Human-readable file titles based on query keywords and tags (e.g. `2026-07-25-postgres-vs-duckdb.md`).
  - YAML frontmatter inclusion (tags, date, consensus score, models queried).

### 7. Packaging & Containerization: `uv` & Docker
- **Role:** Deterministic environment and 1-command deployment.
- **Key Files:** `pyproject.toml`, `uv.lock`, `Dockerfile`, `docker-compose.yml`.
