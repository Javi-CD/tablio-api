from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.repositories.public_menu_repository import PublicMenuRepository
from app.schemas.public_menu import PublicMenuResponse, PublicRestaurantResponse
from app.services.public_menu_service import PublicMenuService

router = APIRouter(tags=["public"])


async def get_public_service(db: AsyncSession = Depends(get_db)) -> PublicMenuService:
    repo = PublicMenuRepository(db)
    return PublicMenuService(repo)


@router.get("/public/menus/{slug}", response_model=PublicMenuResponse)
async def get_public_menu(
    slug: str, service: PublicMenuService = Depends(get_public_service)
):
    return await service.get_menu(slug)


@router.get("/public/restaurants/{slug}", response_model=PublicRestaurantResponse)
async def get_public_restaurant(
    slug: str, service: PublicMenuService = Depends(get_public_service)
):
    return await service.get_restaurant(slug)
