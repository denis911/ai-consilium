# AI Consilium — Project Backlog & Micro-Task Roadmap (`tasks.md`)

## Overview
This document contains the independent, session-sized micro-tasks for building **AI Consilium**. Every task follows a strict template, is self-contained with explicit inputs and outputs, and can be executed independently.

---

## 1. Setup Empty Project Workspace with Passing Test
Goal: Initialize the `uv` Python project structure, configuration files, and a baseline `pytest` test suite.
Description: Create the project directory structure, `pyproject.toml` with `uv` dependency management, `.env.example`, `.gitignore`, and a basic `tests/test_basic.py` file. Verify that running `pytest` passes cleanly in a fresh environment.

## 2. Pydantic Data Contract Schemas
Goal: Define strict Pydantic v2 data models for query inputs, provider responses, consensus metrics, and export artifacts.
Description: Implement `council/schemas.py` containing validated Pydantic models for `ConsiliumQueryInput`, `ModelResponsePayload`, `ConsensusMetrics`, `ContradictionItem`, and `ConsiliumFinalArtifact`. Add unit tests in `tests/test_schemas.py` to verify schema validation and serialization.

## 3. Asynchronous Multi-LLM Provider Engine
Goal: Build an async multi-model client using LiteLLM to query OpenAI, Anthropic, Gemini, Perplexity, and Grok concurrently.
Description: Implement `council/providers.py` using `asyncio.gather()` and LiteLLM to request answers from all configured provider API keys simultaneously. Gracefully isolate individual provider timeouts or missing API keys so that failed requests log errors without crashing the pipeline.

## 4. OpenRouter Free Model Fallback Router
Goal: Implement a zero-cost provider fallback routing requests through OpenRouter's free model tier (`:free`).
Description: Extend the provider engine to detect when only an `OPENROUTER_API_KEY` is present and route queries across 5 free models (`gemini-2.0-flash:free`, `deepseek-r1:free`, `llama-3.3-70b:free`, `qwen-2.5-72b:free`, `mistral-small:free`). Include unit tests mocking OpenRouter API responses.

## 5. DuckDB Local Hybrid RAG Engine
Goal: Build an embedded DuckDB database wrapper for hybrid dense vector and sparse keyword search over local notes.
Description: Implement `council/rag.py` to initialize an embedded DuckDB file (`ai_consilium.duckdb`) with `vss` and `fts` extensions. Add methods to ingest markdown documents, compute local embeddings using `sentence-transformers`, and execute hybrid RRF (Reciprocal Rank Fusion) search queries.

## 6. Hybrid Embedding Consensus Matrix & Outlier Detector
Goal: Calculate pairwise cosine embedding similarities across all 5 LLM responses to compute a numerical Consensus Score (0–100%).
Description: Implement `council/consensus.py` to vectorize the 5 model responses using local `sentence-transformers` embeddings, compute a 5x5 pairwise similarity matrix, calculate the average consensus confidence score, and flag statistical outlier responses whose similarity drops below a configurable threshold.

## 7. LLM-as-a-Judge Qualitative Synthesizer
Goal: Implement a qualitative synthesis module using a lead LLM to audit contradictions and generate consensus points.
Description: Implement `council/synthesizer.py` to send the 5 raw LLM responses, RAG context, and numerical embedding scores to a lead synthesizer model (e.g. Gemini 2.5 Flash). Require the synthesizer to return a validated `ConsensusSynthesisOutput` containing agreement points, contradiction logs, and Mermaid.js diagram code.

## 8. Obsidian Vault & Mermaid Diagram Exporter
Goal: Export generated consensus artifacts directly into a local Obsidian vault as clean markdown notes.
Description: Implement `council/exporter.py` to write formatted markdown files to `OBSIDIAN_VAULT_PATH` configured in `.env`. Ensure note titles are derived from query keywords, include complete YAML frontmatter metadata (tags, timestamp, consensus score, models queried), and embed valid Mermaid.js charts.

## 9. DuckDB Telemetry & Audit Query Logger
Goal: Log query metrics, model latencies, token consumption, estimated costs, and consensus scores to DuckDB.
Description: Implement `council/telemetry.py` to manage a `query_logs` table inside DuckDB. Provide methods to record detailed telemetry for each execution run and query historical audit metrics for display in the UI.

## 10. Streamlit Interactive Dashboard & Audit Console
Goal: Build a Streamlit web interface with real-time query progress bars, interactive consensus gauges, Mermaid rendering, and audit history.
Description: Implement `app.py` creating a multi-tab Streamlit dashboard. Tab 1 ("Consilium Research") allows submitting queries, displaying live LLM responses, rendering Mermaid diagrams, and exporting to Obsidian; Tab 2 ("Audit & Telemetry") presents DuckDB execution logs and analytics charts.

## 11. Command-Line CLI Entrypoint
Goal: Create a standalone command-line CLI script for executing consensus queries from the terminal.
Description: Implement `main.py` using `argparse` or `click` to allow running `python main.py --query "..." --export`. Output formatted JSON or markdown to stdout and optionally trigger the Obsidian vault export automatically.

## 12. Docker & Docker Compose Containerization
Goal: Package the application into a reproducible Docker container and compose file.
Description: Write a multi-stage `Dockerfile` leveraging `uv` for fast dependency installation and a `docker-compose.yml` file to launch the Streamlit app on port 8501 with volume mounts for the local Obsidian vault and DuckDB database.

## 13. End-to-End Test Suite & Evaluation Benchmark
Goal: Create automated end-to-end integration tests verifying pipeline reliability, RAG performance, and test coverage.
Description: Implement integration tests in `tests/test_pipeline.py` verifying full end-to-end flow execution from query input to Obsidian export. Add synthetic benchmarks to validate consensus scoring accuracy on known agreement vs contradiction test cases.
