import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category


class CategoryRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list_by_restaurant(
        self, restaurant_id: uuid.UUID, active_only: bool = True
    ) -> list[Category]:
        stmt = select(Category).where(Category.restaurant_id == restaurant_id)
        if active_only:
            stmt = stmt.where(Category.is_active.is_(True))
        stmt = stmt.order_by(Category.sort_order, Category.created_at)
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, category_id: uuid.UUID) -> Category | None:
        result = await self._db.execute(
            select(Category).where(Category.id == category_id)
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        restaurant_id: uuid.UUID,
        name: str,
        description: str | None,
        sort_order: int,
    ) -> Category:
        category = Category(
            restaurant_id=restaurant_id,
            name=name,
            description=description,
            sort_order=sort_order,
        )
        self._db.add(category)
        await self._db.commit()
        await self._db.refresh(category)
        return category

    async def update(self, category: Category, **fields: object) -> Category:
        for key, value in fields.items():
            setattr(category, key, value)
        category.updated_at = datetime.now(UTC)
        await self._db.commit()
        await self._db.refresh(category)
        return category
