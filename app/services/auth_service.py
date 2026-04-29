import uuid
from datetime import UTC, datetime, timedelta

from app.core.config import settings
from app.core.exceptions import ConflictError, ForbiddenError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)
from app.schemas.user import UserResponse


class AuthService:
    def __init__(self, user_repo: UserRepository) -> None:
        self._repo = user_repo

    async def register(self, data: RegisterRequest) -> TokenResponse:
        existing = await self._repo.get_by_email(data.email)
        if existing is not None:
            raise ConflictError("Email already registered.")
        hashed = hash_password(data.password)
        user = await self._repo.create(
            email=data.email,
            hashed_password=hashed,
            full_name=data.full_name,
        )
        return await self._issue_tokens(user)

    async def login(self, data: LoginRequest) -> TokenResponse:
        user = await self._repo.get_by_email(data.email)
        if user is None or not verify_password(data.password, user.hashed_password):
            raise ForbiddenError("Invalid credentials.")
        if not user.is_active:
            raise ForbiddenError("Account is inactive.")
        return await self._issue_tokens(user)

    async def refresh(self, data: RefreshRequest) -> TokenResponse:
        from jose import JWTError

        try:
            user_id, jti = decode_refresh_token(data.refresh_token)
        except JWTError as exc:
            raise ForbiddenError("Invalid or expired refresh token.") from exc

        user = await self._repo.get_by_id(uuid.UUID(user_id))
        if user is None or not user.is_active:
            raise ForbiddenError("Invalid or expired refresh token.")
        if user.hashed_refresh_token is None or not verify_password(
            jti, user.hashed_refresh_token
        ):
            raise ForbiddenError("Invalid or expired refresh token.")
        if user.refresh_token_expires_at is not None:
            expires = user.refresh_token_expires_at
            if expires.tzinfo is None:
                expires = expires.replace(tzinfo=UTC)
            if expires < datetime.now(UTC):
                raise ForbiddenError("Invalid or expired refresh token.")
        return await self._issue_tokens(user)

    async def logout(self, user_id: uuid.UUID) -> None:
        await self._repo.update_refresh_token(
            user_id=user_id,
            hashed_token=None,
            expires_at=None,
        )

    async def get_me(self, user: User) -> UserResponse:
        return UserResponse.model_validate(user)

    async def _issue_tokens(self, user: User) -> TokenResponse:
        access_token = create_access_token(str(user.id))
        refresh_token_jwt, jti = create_refresh_token(str(user.id))
        expires = datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        await self._repo.update_refresh_token(
            user_id=user.id,
            hashed_token=hash_password(jti),
            expires_at=expires,
        )
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token_jwt,
            token_type="bearer",  # noqa: S106
        )
