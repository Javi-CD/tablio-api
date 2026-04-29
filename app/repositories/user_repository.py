import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        result = await self._db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        result = await self._db.execute(select(User).where(User.email == email.lower()))
        return result.scalar_one_or_none()

    async def create(
        self,
        email: str,
        hashed_password: str,
        full_name: str,
    ) -> User:
        user = User(
            email=email.lower(),
            hashed_password=hashed_password,
            full_name=full_name,
        )
        self._db.add(user)
        await self._db.commit()
        await self._db.refresh(user)
        return user

    async def update_refresh_token(
        self,
        user_id: uuid.UUID,
        hashed_token: str | None,
        expires_at: datetime | None,
    ) -> None:
        user = await self.get_by_id(user_id)
        if user is not None:
            user.hashed_refresh_token = hashed_token
            user.refresh_token_expires_at = expires_at
            user.updated_at = datetime.now(UTC)
            await self._db.commit()
