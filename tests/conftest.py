import os

# Set test environment variables BEFORE importing the app.
# Settings are loaded at module import time, so env vars must be set first.
# In CI these are injected by the workflow; locally the developer needs .env.
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/tablio_test",
)
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production")

from collections.abc import AsyncGenerator  # noqa: E402

import pytest_asyncio  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
