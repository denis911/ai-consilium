# AI Consilium — Technical Stack Specification (`tech_stack.md`)

## Overview
This specification details the component-level architectural choices for **AI Consilium**, evaluating technical trade-offs across simplicity, performance, developer experience, and maximum alignment with the **LLM Zoomcamp Capstone evaluation criteria**.

---

## 1. User Interface Layer (UI)

| Option | Technology Stack | Pros | Cons | Recommendation |
| :--- | :--- | :--- | :--- | :--- |
| **Option A (Recommended)** | **Streamlit** | - Industry standard for LLM Zoomcamp capstone apps.<br>- Native components for Markdown, JSON, dynamic charts, metrics, and progress bars.<br>- Single-file Python UI (`app.py`), zero HTML/JS required. | - Full page re-runs on state change (mitigated by `@st.cache_resource` / `@st.cache_data`). | **PRIMARY CHOICE** (Max evaluation points, easiest setup) |
| **Option B** | **Marimo** | - Next-generation reactive Python notebook/app.<br>- DAG-based reactivity prevents unnecessary re-renders.<br>- Built-in state management. | - Slightly less familiar to traditional capstone evaluators.<br>- Smaller ecosystem of third-party UI widgets. | Strong alternative for reactive DAG workflows |
| **Option C** | **FastAPI + Jinja2/HTMX** | - Production-grade asynchronous REST API backend.<br>- Decoupled front-end. | - High boilerplate code.<br>- Requires separate frontend & backend serving logic. | Over-engineered for local desktop tool |

---

## 2. Data & RAG Storage Layer

| Option | Technology Stack | Pros | Cons | Recommendation |
| :--- | :--- | :--- | :--- | :--- |
| **Option A (Recommended)** | **DuckDB (VSS + FTS)** | - Single-file serverless database (zero container daemon required).<br>- Native **Vector Search (`vss`)** for dense cosine similarity.<br>- Native **Full-Text Search (`fts`)** for BM25 keyword matching.<br>- Perfect for both RAG embeddings and local query audit logs. | - Requires `vss` extension initialization SQL commands on startup. | **PRIMARY CHOICE** (Blazing fast, zero setup, local-first) |
| **Option B** | **LanceDB** | - Embedded columnar vector database built on Arrow.<br>- Very fast vector search. | - Less flexible for relational metadata and audit logging compared to DuckDB. | Good vector alternative |
| **Option C** | **ChromaDB / Qdrant in Docker** | - Dedicated vector database with rich client libraries. | - Adds external service dependency or background container process. | Higher operational friction |

---

## 3. LLM Async Orchestration Layer

| Option | Technology Stack | Pros | Cons | Recommendation |
| :--- | :--- | :--- | :--- | :--- |
| **Option A (Recommended)** | **LiteLLM + `asyncio`** | - Single unified async interface (`await acompletion()`) for OpenAI, Anthropic, Gemini, Perplexity, and Grok.<br>- Supports OpenRouter `:free` models natively.<br>- Handles fallback handling, retries, and timeout handling out of the box. | - Adds 1 lightweight wrapper library dependency. | **PRIMARY CHOICE** (Cleanest code, handles 5 providers gracefully) |
| **Option B** | **Native SDKs (`httpx` + `openai` + `anthropic` + `google-genai`)** | - Zero intermediate wrappers.<br>- Direct control over raw HTTP requests and headers. | - Requires writing custom async wrappers for 5 distinct response schemas. | High maintenance overhead |
| **Option C** | **LangChain / LlamaIndex** | - High-level framework abstraction. | - Heavy abstraction, breaking changes, slow startup time, difficult to debug. | Avoid (Over-abstracted) |

---

## 4. Data Validation & Schema Contract Layer

| Option | Technology Stack | Pros | Cons | Recommendation |
| :--- | :--- | :--- | :--- | :--- |
| **Option A (Recommended)** | **Pydantic v2** | - Strict type validation & JSON schema generation.<br>- Native integration with LiteLLM structured outputs.<br>- Ensures LLM-as-a-Judge outputs guaranteed JSON schema. | - Minimal learning curve for v2 syntax. | **PRIMARY CHOICE** (Ensures deterministic outputs) |
| **Option B** | **Standard Python `dataclasses` + `json`** | - Zero external dependencies. | - Requires manual parsing and type checking of LLM outputs. | Prone to LLM schema drift |

---

## 5. Embedding Model Layer

| Option | Technology Stack | Pros | Cons | Recommendation |
| :--- | :--- | :--- | :--- | :--- |
| **Option A (Recommended)** | **FastEmbed / `sentence-transformers` (`all-MiniLM-L6-v2`)** | - **100% Local & Free** (runs on CPU in <50ms).<br>- 384-dimensional embeddings (small memory footprint).<br>- Zero API key usage or rate limits for vectorization. | - Runs on local CPU (requires one-time ~80MB model download). | **PRIMARY CHOICE** (100% offline RAG vectorization) |
| **Option B** | **OpenAI API (`text-embedding-3-small`)** | - High quality 1536-dim embeddings. | - Costs money per embedding, requires network call, rate limited. | Paid API dependency |

---

## 6. Visualization & Vault Export Layer

- **Mermaid.js Renderer:** Renders dynamic Gantt charts, system architecture diagrams, and flowchart Markdown directly inside Streamlit using `streamlit-mermaid` or custom HTML component.
- **Obsidian Note Writer:** Uses standard Python `pathlib` with atomic file writes. Note titles derived from sanitized query tags/keywords, containing structured YAML frontmatter (tags, date, consensus score, models queried).

---

## 🏆 Recommended Target Stack Combination

```text
+-----------------------------------------------------------------------+
| UI Layer: STREAMLIT (Single App + Audit History Tab)                  |
+-----------------------------------------------------------------------+
| Schema Layer: PYDANTIC V2 (Strict Consensus & Contradiction Contracts)|
+-----------------------------------------------------------------------+
| Orchestration: LITELLM + PYTHON ASYNCIO (5 Parallel Providers)        |
+-----------------------------------------------------------------------+
| RAG & Audit DB: DUCKDB (Embedded VSS Vector Search + BM25 FTS)        |
+-----------------------------------------------------------------------+
| Embedding Engine: FASTEMBED / SENTENCE-TRANSFORMERS (all-MiniLM-L6)   |
+-----------------------------------------------------------------------+
| Environment & Infra: UV + DOCKER & DOCKER-COMPOSE                     |
+-----------------------------------------------------------------------+
```
