# AI Consilium (Dual-Engine Consensus Research Agent)

## Project Vision & Mission
To eliminate AI hallucination, bias, and context drift in high-stakes domain research for solopreneurs and startup founders by establishing a deterministic software harness that cross-examines multiple frontier LLMs, computes consensus and contradictions, generates structured visualizations (e.g., Mermaid.js Gantt charts), and exports validated insights directly into a local Obsidian vault.

## Primary Audience & Pain Point
- **Target Audience:** High-Stakes Solopreneurs and Startup Founders acting as their own legal, technical, and product teams.
- **Pain Point:** Founders cannot afford corporate retainers for legal/accounting/architectural cross-checking, but cannot risk single-LLM hallucinations derailing their infrastructure or legal compliance.
- **Value Proposition:** Transforms unpredictable single LLM outputs into an auditable, multi-model consensus engine that strictly logs contradictions before committing knowledge to a local wiki/Obsidian vault.

## SDD Architecture Overview
1. **RAG Knowledge Retrieval Engine (DuckDB):** Ingests local Obsidian notes / reference docs into an embedded DuckDB vector store (VSS extension + FTS keyword search) for fast, zero-dependency local hybrid search.
2. **Multi-Model Querying Engine (LiteLLM + OpenRouter Fallback):** Asynchronously queries 5 frontier LLMs (OpenAI, Anthropic, Gemini, Perplexity, Grok) concurrently via LiteLLM using individual provider keys, with seamless zero-cost fallback to 5 OpenRouter free-tier models (`:free`) for $0 testing.
3. **Hybrid Consensus & Contradiction Synthesizer:** Computes pairwise semantic embedding similarity across responses to generate a mathematical Consensus Score (0–100%) and detect statistical outliers, followed by an LLM-as-a-Judge qualitative synthesis.
4. **Structured Artifact Generator:** Generates structured schemas, markdown documents, and dynamic Mermaid.js visualizations (e.g., Gantt charts, architecture diagrams).
5. **Dual Interface & Obsidian Exporter:** Streamlit interactive web dashboard (real-time progress, gauge metrics, Mermaid rendering, vault export) + command-line CLI.
6. **Embedded Monitoring & Audit Log (DuckDB + Streamlit):** Logs execution history, provider latencies, token usage, cost estimations, and consensus scores to DuckDB, rendered in an interactive Streamlit Audit tab.
7. **Packaging & Deployment (`uv` + Docker):** Modern `uv` workspace (`pyproject.toml` + `uv.lock`) with clean `Dockerfile` and `docker-compose.yml` for 1-command containerized deployment (`docker compose up`).
8. **Obsidian Vault Exporter:** Saves notes to `OBSIDIAN_VAULT_PATH` configured via `.env` (or fallback to `./output_vault/`). Uses clean, human-readable file titles based on query keywords with YAML frontmatter metadata (tags, timestamp, consensus score).

## LLM Zoomcamp Capstone Alignment
Designed from the ground up to meet maximum evaluation criteria for the DataTalksClub LLM Zoomcamp Capstone project.
