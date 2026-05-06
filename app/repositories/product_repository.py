import uuid
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product


class ProductRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list_by_restaurant(
        self, restaurant_id: uuid.UUID, include_unavailable: bool = False
    ) -> list[Product]:
        stmt = select(Product).where(Product.restaurant_id == restaurant_id)
        if not include_unavailable:
            stmt = stmt.where(Product.is_available.is_(True))
        stmt = stmt.order_by(Product.created_at)
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def list_by_category(
        self, category_id: uuid.UUID, include_unavailable: bool = False
    ) -> list[Product]:
        stmt = select(Product).where(Product.category_id == category_id)
        if not include_unavailable:
            stmt = stmt.where(Product.is_available.is_(True))
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, product_id: uuid.UUID) -> Product | None:
        result = await self._db.execute(select(Product).where(Product.id == product_id))
        return result.scalar_one_or_none()

    async def create(
        self,
        restaurant_id: uuid.UUID,
        name: str,
        price: Decimal,
        description: str | None = None,
        image_url: str | None = None,
        category_id: uuid.UUID | None = None,
    ) -> Product:
        product = Product(
            restaurant_id=restaurant_id,
            name=name,
            price=price,
            description=description,
            image_url=image_url,
            category_id=category_id,
        )
        self._db.add(product)
        await self._db.commit()
        await self._db.refresh(product)
        return product

    async def update(self, product: Product, **fields: object) -> Product:
        for key, value in fields.items():
            setattr(product, key, value)
        product.updated_at = datetime.now(UTC)
        await self._db.commit()
        await self._db.refresh(product)
        return product
