import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.restaurant import Restaurant


class RestaurantRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_by_id(self, restaurant_id: uuid.UUID) -> Restaurant | None:
        result = await self._db.execute(
            select(Restaurant).where(Restaurant.id == restaurant_id)
        )
        return result.scalar_one_or_none()

    async def get_by_owner_id(self, owner_id: uuid.UUID) -> Restaurant | None:
        result = await self._db.execute(
            select(Restaurant).where(Restaurant.owner_id == owner_id)
        )
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Restaurant | None:
        result = await self._db.execute(
            select(Restaurant).where(Restaurant.slug == slug)
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        owner_id: uuid.UUID,
        name: str,
        slug: str,
        description: str | None = None,
        logo_url: str | None = None,
        phone: str | None = None,
        address: str | None = None,
    ) -> Restaurant:
        restaurant = Restaurant(
            owner_id=owner_id,
            name=name,
            slug=slug,
            description=description,
            logo_url=logo_url,
            phone=phone,
            address=address,
        )
        self._db.add(restaurant)
        await self._db.commit()
        await self._db.refresh(restaurant)
        return restaurant

    async def update(self, restaurant: Restaurant, **fields: object) -> Restaurant:
        from datetime import UTC, datetime

        for key, value in fields.items():
            setattr(restaurant, key, value)
        restaurant.updated_at = datetime.now(UTC)
        await self._db.commit()
        await self._db.refresh(restaurant)
        return restaurant
