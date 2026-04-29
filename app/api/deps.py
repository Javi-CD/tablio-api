import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.db.session import get_db as get_db  # re-export for routes
from app.models.user import User
from app.repositories.user_repository import UserRepository

_bearer = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(_bearer)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        user_id = decode_access_token(credentials.credentials)
    except JWTError:
        raise exc from None

    repo = UserRepository(db)
    user = await repo.get_by_id(uuid.UUID(user_id))
    if user is None or not user.is_active:
        raise exc
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
