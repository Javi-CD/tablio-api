import os

# Set test environment variables BEFORE importing the app.
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5433/tablio_test",
)
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production")
