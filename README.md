# tablio-api

Tablio Backend — REST and WebSocket API for the digital menu and online ordering platform for gastronomic businesses in Latam.

**Stack:** Python 3.12 · FastAPI · PostgreSQL 15 · SQLAlchemy 2.0 (async) · Alembic · uv · Ruff · MyPy

---

## Requirements

- [Python 3.12+](https://www.python.org/downloads/)
- [uv](https://docs.astral.sh/uv/getting-started/installation/) — package manager
- [Docker](https://www.docker.com/) and Docker Compose

## Local Setup

```bash
# 1. Clone the repository
git clone https://github.com/Javi-CD/tablio-api.git
cd tablio-api

# 2. Copy environment variables
cp .env.example .env
# Edit .env with the corresponding values

# 3. Start the database
docker compose up db -d

# 4. Create the virtual environment and install dependencies
uv sync

# 5. Apply migrations
uv run alembic upgrade head

# 6. Start the development server
uv run uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`.
Swagger Documentation: `http://localhost:8000/docs`

## Run everything with Docker

```bash
docker compose up --build
```

## Frequent commands

```bash
# Linting
uv run ruff check .

# Formatting
uv run ruff format .

# Type checking
uv run mypy app/

# Run all tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=app --cov-report=term-missing

# Create a new Alembic migration
uv run alembic revision --autogenerate -m "change description"

# Apply migrations
uv run alembic upgrade head

# Revert the last migration
uv run alembic downgrade -1

# Populate the database with development data
uv run python -m app.db.init_db --seed
```

## Project Structure

```
app/
├── main.py               # FastAPI entry point
├── core/                 # Config, security, exceptions
├── db/                   # Session, declarative base, seeders
├── models/               # SQLAlchemy models
├── schemas/              # Pydantic schemas (request/response)
├── api/
│   ├── deps.py           # Shared dependencies
│   └── routes/           # Endpoints organized by resource
├── services/             # Business logic
├── repositories/         # Database access
└── utils/                # Utilities (slugs, pagination)
tests/
├── unit/                 # Isolated service tests
├── integration/          # Endpoint tests against a real DB
└── e2e/                  # Full End-to-End flows
```

## Conventions

See [CONTRIBUTING.md](CONTRIBUTING.md) for code conventions, commits, and the PR process.

## Health check

```bash
curl http://localhost:8000/api/v1/health
# {"status": "ok", "version": "0.1.0"}
```
