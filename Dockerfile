# Multi-stage Dockerfile using uv for fast, reproducible dependency builds
FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim AS builder

WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy dependency specification files
COPY pyproject.toml uv.lock ./

# Install dependencies without root project
RUN uv sync --frozen --no-install-project --no-dev

# Final production stage
FROM python:3.11-slim-bookworm

WORKDIR /app

# Copy virtual environment and binary binaries from builder stage
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Copy application source code and docs
COPY . /app

# Expose Streamlit default port
EXPOSE 8501

# Streamlit environment settings
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0

# Launch Streamlit Application
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
