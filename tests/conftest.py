import asyncio
import os
import sys

# psycopg async requires SelectorEventLoop on Windows (ProactorEventLoop not supported).
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Set test environment variables BEFORE importing the app.
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:postgres@localhost:5433/tablio_test",
)
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production")
