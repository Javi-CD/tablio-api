from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.exceptions import NotFoundError
from app.repositories.public_menu_repository import PublicMenuRepository
from app.schemas.public_menu import PublicMenuResponse, PublicRestaurantResponse
from app.services.public_menu_service import PublicMenuService

router = APIRouter(tags=["public"])


def _get_service(db: Annotated[AsyncSession, Depends(get_db)]) -> PublicMenuService:
    return PublicMenuService(PublicMenuRepository(db))


@router.get("/public/menus/{slug}", response_model=PublicMenuResponse)
async def get_public_menu(
    slug: str,
    service: Annotated[PublicMenuService, Depends(_get_service)],
) -> PublicMenuResponse:
    try:
        return await service.get_menu(slug)
    except NotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc


@router.get(
    "/public/restaurants/{slug}",
    response_model=PublicRestaurantResponse,
)
async def get_public_restaurant(
    slug: str,
    service: Annotated[PublicMenuService, Depends(_get_service)],
) -> PublicRestaurantResponse:
    try:
        return await service.get_restaurant(slug)
    except NotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
