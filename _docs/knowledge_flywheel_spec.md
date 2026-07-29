# Design Document: Obsidian Knowledge Base Flywheel (Cold Start vs. Warm Start)

> **Document Status:** Draft / Specification  
> **Author:** Denis K & AI Consilium Core Architecture Team  
> **Related GitHub Issues:** [#14](https://github.com/denis911/ai-consilium/issues/14), [#15](https://github.com/denis911/ai-consilium/issues/15), [#16](https://github.com/denis911/ai-consilium/issues/16)

---

## 📌 Executive Summary & Vision

The **Obsidian Knowledge Base Flywheel** expands AI Consilium from an isolated multi-model consensus research tool into a **self-reinforcing, local-first knowledge engine**.

Instead of treating Retrieval-Augmented Generation (RAG) as a static database lookup, AI Consilium manages the complete lifecycle of knowledge:
1. **Cold Start (Knowledge Generation):** When starting with an empty vault, consensus research queries generate structured `.md` notes with Mermaid diagrams, automatically building a rich local Obsidian vault note-by-note.
2. **Warm Start (Context Grounding & RAG):** When an Obsidian vault contains existing notes, AI Consilium bulk-indexes the `.md` files into DuckDB (VSS + FTS) to automatically ground future consensus queries in past research decisions.
3. **Retrieval Benchmark & Observability:** Empirical evaluation scripts (`evaluate_retrieval.py`) calculate **Hit Rate** and **MRR**, while user feedback ratings (+1 / -1) monitor continuous system performance.

---

## 🏗️ Architecture & Data Flow Diagram

```
                         +-----------------------------------+
                         |      AI CONSILIUM ENGINE          |
                         +-----------------+-----------------+
                                           |
                   +-----------------------+-----------------------+
                   |                                               |
                   v                                               v
        [❄️ COLD START MODE]                             [🔥 WARM START MODE]
  No existing vault notes found                    Vault folder contains .md notes
                   |                                               |
                   v                                               v
  User asks high-stakes queries                    Auto-scans vault & ingests via
  across multi-model ensemble                      DuckDB RAG (Dense Vector + FTS)
                   |                                               |
                   v                                               v
  Exports structured .md notes with                Grounds multi-LLM consensus
  Mermaid charts to Obsidian vault                 queries with retrieved vault notes
                   |                                               |
                   +-----------------------+-----------------------+
                                           |
                                           v
                       +---------------------------------------+
                       |    📊 RETRIEVAL EVALUATION BENCHMARK  |
                       | Calculates Hit Rate @ K & MRR @ K    |
                       | to measure search precision over time  |
                       +---------------------------------------+
```

---

## 🛠️ Feature Specifications & Implementation Roadmap

### 1. ❄️ Cold Start Mode: Knowledge Base Generation & Obsidian Exporter
- **Concept:** Solopreneurs and founders frequently start with zero structured notes. As they ask high-stakes architecture, accounting, and legal questions, AI Consilium executes multi-LLM consensus scoring, synthesizes points of agreement and contradiction logs, and exports formatted Markdown notes.
- **Key Modules:** [`council/exporter.py`](file:///c:/tmp/ai-consilium/council/exporter.py)
- **Output:** Structured `.md` files featuring YAML frontmatter (`tags`, `date`, `consensus_score`, `models_queried`), executive summaries, and rendered Mermaid.js diagrams directly saved into `OBSIDIAN_VAULT_PATH` (`C:\ai-memory\ai-concilium`).

---

### 2. 🔥 Warm Start Mode: Bulk Vault Ingestion & Grounded RAG (Task #16)
- **Concept:** When `OBSIDIAN_VAULT_PATH` contains pre-existing `.md` notes, AI Consilium ingests and indexes the local markdown vault to ground new research queries.
- **Key Module:** `ingest.py` / `council/ingest.py`
- **Specification:**
  - Recursively scans `OBSIDIAN_VAULT_PATH` for `.md` files.
  - Extracts title, YAML frontmatter tags, markdown section headings (`##`), and text blocks.
  - Computes 384-dimensional dense vector embeddings using local CPU `SentenceTransformers` (`all-MiniLM-L6-v2`).
  - Populates DuckDB tables (`ai_consilium.duckdb`) supporting hybrid dense vector (`vss`) and sparse full-text search (`fts`).
  - Enables automatic retrieval grounding in Streamlit Web UI (`app.py`) and CLI mode (`main.py`).

---

### 3. 📊 RAG Retrieval Evaluation Script (Hit Rate & MRR Benchmark) (Task #14)
- **Concept:** Provide empirical metrics measuring how accurately DuckDB hybrid RAG retrieves relevant Obsidian notes for user queries.
- **Key Module:** `evaluate_retrieval.py`
- **Metrics Calculated:**
  - **Hit Rate @ K:** Percentage of test queries where the true target document appears in the top $K$ retrieved results.
  - **Mean Reciprocal Rank (MRR @ K):** Average of reciprocal ranks ($1 / \text{rank}$) for the first correct document across test queries.
- **Search Strategy Comparison:** Compares Dense Vector Search (`vss`), Sparse Full-Text Search (`fts`), and Reciprocal Rank Fusion (RRF).

---

### 4. 👍 User Feedback Logging & Observability (Task #15)
- **Concept:** Track user satisfaction metrics (+1 / -1 ratings) alongside token usage, latencies, and estimated USD costs.
- **Key Modules:** [`council/telemetry.py`](file:///c:/tmp/ai-consilium/council/telemetry.py), [`app.py`](file:///c:/tmp/ai-consilium/app.py)
- **Specification:**
  - Extends DuckDB `query_logs` table schema with `user_rating` (`INTEGER`: `+1`, `-1`, `NULL`) and `user_feedback_comment` (`VARCHAR`).
  - Renders interactive feedback buttons ("👍 Helpful Consensus", "👎 Inaccurate / Hallucinated") in Streamlit Tab 1.
  - Displays user approval percentage metrics in Streamlit Tab 2 (Audit History & Telemetry Console).

---

## 🔮 Future Roadmap & Discussion Topics

1. **Multi-Vault Directory Support:** Allow switching between different Obsidian vaults (e.g. `architecture_vault`, `legal_vault`, `finance_vault`).
2. **Automated File Watcher:** Implement a background file watcher (`watchdog`) to auto-index modified Obsidian `.md` notes in real-time.
3. **Custom Markdown Templates:** Allow users to customize YAML frontmatter keys and section layouts for Obsidian export.
