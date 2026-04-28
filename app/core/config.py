from pydantic import PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    # Database
    DATABASE_URL: PostgresDsn

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # Application
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # CORS — JSON array in .env
    CORS_ORIGINS: list[str] = ["http://localhost:5173"]

    # API
    API_V1_PREFIX: str = "/api/v1"


settings = Settings()
