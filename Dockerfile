FROM python:3.12-slim

WORKDIR /app

# Install uv from its official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# Copy manifests first to take advantage of layer caching
COPY pyproject.toml uv.lock* ./

# Install only production dependencies (without dev extras)
RUN uv sync --no-extra dev 2>/dev/null || uv sync

# Copy source code
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini ./

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
