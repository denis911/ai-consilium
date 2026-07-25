# AI Consilium — High-Level Technical Specification (SDD Phase 1)

## Executive Summary
**AI Consilium (Dual-Engine Consensus Research Agent)** is a deterministic software harness designed for solopreneurs and startup founders who make high-stakes legal, tax, and architectural decisions. By querying 5 frontier LLMs concurrently with RAG-retrieved local context, mathematically computing consensus via embedding similarity, and generating auditable notes and Mermaid visualizations directly into an Obsidian vault, it eliminates single-LLM hallucination risks.

---

## High-Level Architecture Diagram

```
                                  +-----------------------+
                                  | Local Obsidian Vault /|
                                  | Reference Documents   |
                                  +-----------+-----------+
                                              |
                                              v
                                  +-----------------------+
                                  |   DuckDB RAG Engine   |
                                  | (Hybrid VSS + FTS)    |
                                  +-----------+-----------+
                                              |
                                              v
+------------------+              +-----------------------+
|  User Input Query| -----------> | Multi-Model Provider  |
|  (Streamlit/CLI) |              |  Engine (Async HTTP)  |
+------------------+              +-----------+-----------+
                                              |
                     +------------------------+------------------------+
                     |            |           |           |            |
                     v            v           v           v            v
                 OpenAI       Anthropic    Gemini     Perplexity      Grok
                 (gpt-4o)      (claude)   (flash)      (sonar)       (xai)
                     |            |           |           |            |
                     +------------------------+------------------------+
                                              |
                                              v
                                  +-----------------------+
                                  |  Hybrid Consensus &   |
                                  | Contradiction Engine  |
                                  | (Embedding + Judge)   |
                                  +-----------+-----------+
                                              |
                                   +----------+----------+
                                   |                     |
                                   v                     v
                        +--------------------+  +--------------------+
                        | Streamlit UI /     |  | Obsidian Exporter  |
                        | Audit History Tab  |  | (Human-Readable MD)|
                        +--------------------+  +--------------------+
```

---

## 8 Core Architectural Pillars

1. **Target Audience & Core Problem:**
   - Designed for high-stakes solopreneurs acting as their own legal, technical, and product teams.
   - Eliminates single-LLM hallucination and context drift by cross-examining multiple frontier models.

2. **RAG Knowledge Retrieval Engine (DuckDB):**
   - Uses embedded **DuckDB** with Vector Search (`vss`) and Full-Text Search (`fts`) extensions for fast, local-first hybrid retrieval.

3. **Multi-Model Querying Engine (LiteLLM + OpenRouter Fallback):**
   - Asynchronous Python engine hitting 5 frontier LLMs concurrently using **LiteLLM**: OpenAI, Anthropic, Gemini, Perplexity, and Grok.
   - **Zero-Cost Free Tier Support:** Includes built-in support for OpenRouter's 100% free model tier (`:free`), allowing $0 local testing across 5 free models (Gemini 2.0 Flash, DeepSeek R1, Llama 3.3 70B, Qwen 2.5 72B, Mistral Small) using a single OpenRouter API key.

4. **Hybrid Consensus & Contradiction Synthesizer:**
   - Calculates numerical pairwise cosine embedding similarity to compute a **Consensus Score (0–100%)** and identify statistical outliers.
   - Uses LLM-as-a-Judge qualitative synthesis to log explicit points of agreement vs contradiction.

5. **Structured Artifact & Diagram Generator:**
   - Generates structured JSON schemas, markdown notes, and dynamic **Mermaid.js** visualizations (Gantt charts, architecture diagrams).

6. **Dual Interface & Obsidian Vault Exporter:**
   - **Streamlit Web Dashboard:** Live query progress, interactive Consensus gauge, Mermaid viewer, audit history tab.
   - **CLI Mode:** Command-line execution (`python main.py --query "..."`).
   - **Obsidian Exporter:** Exports clean, human-readable `.md` notes titled by key tags into `OBSIDIAN_VAULT_PATH` configured via `.env`.

7. **Observability & Audit Logging:**
   - Direct logging of execution history, provider latencies, token counts, cost estimations, and consensus scores to DuckDB, displayed in the Streamlit Audit Tab.

8. **Packaging & Deployment (`uv` + Docker):**
   - Managed with `uv` (`pyproject.toml` + `uv.lock`).
   - Containerized with `Dockerfile` and `docker-compose.yml` for single-command deployment (`docker compose up`).

---

## LLM Zoomcamp Capstone Scoring Matrix (Target: 36/36+ Points)

| Rubric Criteria | Score Target | Technical Implementation in AI Consilium |
| :--- | :--- | :--- |
| **Problem Description** | 2 / 2 points | Clear high-stakes business case for solopreneurs in [`mission.md`](file:///c:/tmp/ai-consilium/_docs/mission.md). |
| **RAG Pipeline & Retrieval** | 6 / 6 points | DuckDB Hybrid Search (Vector VSS + Keyword FTS) over Obsidian notes. |
| **RAG Evaluation Metrics** | 6 / 6 points | Pairwise embedding similarity matrix + LLM-as-a-Judge consensus evaluation. |
| **Monitoring & Observability**| 6 / 6 points | DuckDB `query_logs` table tracking latency, tokens, cost, and consensus scores in Streamlit. |
| **User Interface** | 6 / 6 points | Dual Streamlit Web App + CLI interface with live Mermaid rendering. |
| **Deployment & Containerization**| 6 / 6 points | `Dockerfile` + `docker-compose.yml` reproducible containerized setup. |
| **Reproducibility** | 4 / 4 points | Modern `uv` environment (`pyproject.toml`), clean `.env.example`, step-by-step README. |
