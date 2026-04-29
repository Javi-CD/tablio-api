from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.core.exceptions import ConflictError, ForbiddenError
from app.core.security import hash_password, verify_password
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest
from app.services.auth_service import AuthService


def _make_user(**kwargs: object) -> User:
    defaults: dict[str, object] = {
        "id": uuid4(),
        "email": "user@tablio.co",
        "hashed_password": hash_password("password123"),
        "full_name": "Test User",
        "is_active": True,
        "hashed_refresh_token": None,
        "refresh_token_expires_at": None,
    }
    defaults.update(kwargs)
    user = MagicMock(spec=User)
    for k, v in defaults.items():
        setattr(user, k, v)
    return user  # type: ignore[return-value]


def _make_service(user: User | None = None) -> tuple[AuthService, AsyncMock]:
    repo = AsyncMock()
    repo.get_by_email.return_value = user
    repo.get_by_id.return_value = user
    repo.create.return_value = _make_user()
    repo.update_refresh_token.return_value = None
    return AuthService(repo), repo


class TestHashPassword:
    def test_hash_is_not_plaintext(self) -> None:
        hashed = hash_password("secret")
        assert hashed != "secret"

    def test_verify_correct_password(self) -> None:
        hashed = hash_password("secret")
        assert verify_password("secret", hashed) is True

    def test_verify_wrong_password(self) -> None:
        hashed = hash_password("secret")
        assert verify_password("wrong", hashed) is False


class TestRegister:
    async def test_register_raises_conflict_if_email_exists(self) -> None:
        service, _ = _make_service(user=_make_user())
        with pytest.raises(ConflictError):
            await service.register(
                RegisterRequest(
                    email="user@tablio.co",
                    password="password123",
                    full_name="Test",
                )
            )

    async def test_register_returns_tokens_on_success(self) -> None:
        service, _ = _make_service(user=None)
        result = await service.register(
            RegisterRequest(
                email="new@tablio.co",
                password="password123",
                full_name="New User",
            )
        )
        assert result.access_token
        assert result.refresh_token
        assert result.token_type == "bearer"


class TestLogin:
    async def test_login_raises_forbidden_if_user_not_found(self) -> None:
        service, _ = _make_service(user=None)
        with pytest.raises(ForbiddenError):
            await service.login(LoginRequest(email="x@x.co", password="pass"))

    async def test_login_raises_forbidden_if_wrong_password(self) -> None:
        service, _ = _make_service(user=_make_user())
        with pytest.raises(ForbiddenError):
            await service.login(
                LoginRequest(email="user@tablio.co", password="wrongpassword")
            )

    async def test_login_returns_tokens_on_success(self) -> None:
        service, _ = _make_service(user=_make_user())
        result = await service.login(
            LoginRequest(email="user@tablio.co", password="password123")
        )
        assert result.access_token
        assert result.refresh_token
