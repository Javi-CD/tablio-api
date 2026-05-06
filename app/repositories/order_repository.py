import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.order import Order, OrderStatus, OrderType
from app.models.order_item import OrderItem
from app.utils.pagination import PaginationParams


@dataclass
class OrderItemData:
    product_id: uuid.UUID | None
    product_name: str
    unit_price: Decimal
    quantity: int
    subtotal: Decimal


class OrderRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(
        self,
        restaurant_id: uuid.UUID,
        customer_name: str,
        customer_phone: str | None,
        customer_notes: str | None,
        order_type: OrderType,
        table_number: str | None,
        total_amount: Decimal,
        items: list[OrderItemData],
    ) -> Order:
        order = Order(
            restaurant_id=restaurant_id,
            customer_name=customer_name,
            customer_phone=customer_phone,
            customer_notes=customer_notes,
            order_type=order_type,
            table_number=table_number,
            total_amount=total_amount,
        )
        self._db.add(order)
        await self._db.flush()

        for item in items:
            self._db.add(
                OrderItem(
                    order_id=order.id,
                    product_id=item.product_id,
                    product_name=item.product_name,
                    unit_price=item.unit_price,
                    quantity=item.quantity,
                    subtotal=item.subtotal,
                )
            )

        await self._db.commit()
        result = await self._get_with_items(order.id)
        assert result is not None
        return result

    async def get_by_id(self, order_id: uuid.UUID) -> Order | None:
        return await self._get_with_items(order_id)

    async def list_by_restaurant(
        self,
        restaurant_id: uuid.UUID,
        pagination: PaginationParams,
        status: OrderStatus | None = None,
    ) -> tuple[list[Order], int]:
        base = select(Order).where(Order.restaurant_id == restaurant_id)
        if status is not None:
            base = base.where(Order.status == status)

        count_result = await self._db.execute(
            select(func.count()).select_from(base.subquery())
        )
        total: int = count_result.scalar_one()

        stmt = (
            base.options(selectinload(Order.items))
            .order_by(Order.created_at.desc())
            .offset(pagination.offset())
            .limit(pagination.limit)
        )
        result = await self._db.execute(stmt)
        orders = list(result.scalars().all())
        return orders, total

    async def update_status(self, order: Order, new_status: OrderStatus) -> Order:
        order.status = new_status
        order.updated_at = datetime.now(UTC)
        await self._db.commit()
        result = await self._get_with_items(order.id)
        assert result is not None
        return result

    async def _get_with_items(self, order_id: uuid.UUID) -> Order | None:
        result = await self._db.execute(
            select(Order).where(Order.id == order_id).options(selectinload(Order.items))
        )
        return result.scalar_one_or_none()
