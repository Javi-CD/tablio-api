import uuid
from dataclasses import dataclass
from decimal import Decimal

from app.core.exceptions import BusinessRuleError, ForbiddenError, NotFoundError
from app.core.websocket_manager import ws_manager
from app.models.order import Order, OrderStatus
from app.repositories.order_repository import OrderItemData, OrderRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.restaurant_repository import RestaurantRepository
from app.schemas.order import OrderCreate, OrderStatusUpdate
from app.utils.pagination import PaginationParams, total_pages

_VALID_TRANSITIONS: dict[OrderStatus, set[OrderStatus]] = {
    OrderStatus.PENDING: {OrderStatus.ACCEPTED, OrderStatus.CANCELLED},
    OrderStatus.ACCEPTED: {OrderStatus.PREPARING, OrderStatus.CANCELLED},
    OrderStatus.PREPARING: {OrderStatus.COMPLETED, OrderStatus.CANCELLED},
    OrderStatus.COMPLETED: set(),
    OrderStatus.CANCELLED: set(),
}


@dataclass
class OrderListResult:
    items: list[Order]
    total: int
    page: int
    limit: int
    pages: int


class OrderService:
    def __init__(
        self,
        order_repo: OrderRepository,
        restaurant_repo: RestaurantRepository,
        product_repo: ProductRepository,
    ) -> None:
        self._order_repo = order_repo
        self._restaurant_repo = restaurant_repo
        self._product_repo = product_repo

    async def create_order(self, slug: str, data: OrderCreate) -> Order:
        restaurant = await self._restaurant_repo.get_by_slug(slug)
        if restaurant is None:
            raise NotFoundError("Restaurant not found.")

        items: list[OrderItemData] = []
        total_amount = Decimal("0")

        for item_in in data.items:
            product = await self._product_repo.get_by_id(item_in.product_id)
            if product is None or not product.is_available:
                raise NotFoundError(
                    f"Product {item_in.product_id} not found or unavailable."
                )
            if product.restaurant_id != restaurant.id:
                raise ForbiddenError(
                    f"Product {item_in.product_id} does not belong to this restaurant."
                )
            subtotal = product.price * item_in.quantity
            total_amount += subtotal
            items.append(
                OrderItemData(
                    product_id=product.id,
                    product_name=product.name,
                    unit_price=product.price,
                    quantity=item_in.quantity,
                    subtotal=subtotal,
                )
            )

        order = await self._order_repo.create(
            restaurant_id=restaurant.id,
            customer_name=data.customer_name,
            customer_phone=data.customer_phone,
            customer_notes=data.customer_notes,
            order_type=data.order_type,
            table_number=data.table_number,
            total_amount=total_amount,
            items=items,
        )

        await ws_manager.broadcast(
            restaurant.id,
            {
                "event": "new_order",
                "order_id": str(order.id),
                "customer_name": order.customer_name,
                "total_amount": str(order.total_amount),
                "status": order.status.value,
            },
        )
        return order

    async def list_orders(
        self,
        restaurant_id: uuid.UUID,
        owner_id: uuid.UUID,
        pagination: PaginationParams,
        status: OrderStatus | None = None,
    ) -> OrderListResult:
        restaurant = await self._restaurant_repo.get_by_id(restaurant_id)
        if restaurant is None:
            raise NotFoundError("Restaurant not found.")
        if restaurant.owner_id != owner_id:
            raise ForbiddenError("Not authorized.")

        orders, total = await self._order_repo.list_by_restaurant(
            restaurant_id, pagination, status
        )
        return OrderListResult(
            items=orders,
            total=total,
            page=pagination.page,
            limit=pagination.limit,
            pages=total_pages(total, pagination.limit),
        )

    async def get_order(self, order_id: uuid.UUID, owner_id: uuid.UUID) -> Order:
        order = await self._order_repo.get_by_id(order_id)
        if order is None:
            raise NotFoundError("Order not found.")
        restaurant = await self._restaurant_repo.get_by_id(order.restaurant_id)
        if restaurant is None or restaurant.owner_id != owner_id:
            raise ForbiddenError("Not authorized.")
        return order

    async def update_status(
        self, order_id: uuid.UUID, owner_id: uuid.UUID, data: OrderStatusUpdate
    ) -> Order:
        order = await self._order_repo.get_by_id(order_id)
        if order is None:
            raise NotFoundError("Order not found.")
        restaurant = await self._restaurant_repo.get_by_id(order.restaurant_id)
        if restaurant is None or restaurant.owner_id != owner_id:
            raise ForbiddenError("Not authorized.")

        allowed = _VALID_TRANSITIONS[order.status]
        if data.status not in allowed:
            raise BusinessRuleError(
                f"Cannot transition from '{order.status.value}'"
                f" to '{data.status.value}'."
            )

        updated = await self._order_repo.update_status(order, data.status)

        await ws_manager.broadcast(
            order.restaurant_id,
            {
                "event": "order_updated",
                "order_id": str(updated.id),
                "status": updated.status.value,
            },
        )
        return updated
