import inspect

from app.core.config import settings
from app.core.exceptions import (
    BusinessRuleError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
    TablioError,
)
from app.db.base import Base
from app.db.session import get_db


def test_api_prefix_is_configured() -> None:
    assert settings.API_V1_PREFIX == "/api/v1"
    assert settings.ALGORITHM == "HS256"
    assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 60
    assert settings.REFRESH_TOKEN_EXPIRE_DAYS == 30


def test_exception_hierarchy() -> None:
    assert issubclass(NotFoundError, TablioError)
    assert issubclass(ForbiddenError, TablioError)
    assert issubclass(ConflictError, TablioError)
    assert issubclass(BusinessRuleError, TablioError)


def test_base_metadata_exists() -> None:
    assert Base.metadata is not None


def test_get_db_is_async_generator() -> None:
    assert inspect.isasyncgenfunction(get_db)
