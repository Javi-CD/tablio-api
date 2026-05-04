import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.models.product import Product
from app.models.restaurant import Restaurant


class PublicMenuRepository:
    def __init__(self, db: AsyncSession):
        self._db = db

    async def get_restaurant_by_slug(self, slug: str) -> Restaurant | None:
        stmt = select(Restaurant).where(Restaurant.slug == slug, Restaurant.is_active)
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active_categories(self, restaurant_id: uuid.UUID) -> list[Category]:
        stmt = (
            select(Category)
            .where(Category.restaurant_id == restaurant_id, Category.is_active)
            .order_by(Category.sort_order.asc(), Category.created_at.asc())
        )
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def get_available_products(self, restaurant_id: uuid.UUID) -> list[Product]:
        stmt = select(Product).where(
            Product.restaurant_id == restaurant_id, Product.is_available
        )
        result = await self._db.execute(stmt)
        return list(result.scalars().all())
