import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, get_db
from app.core.exceptions import BusinessRuleError, ForbiddenError, NotFoundError
from app.core.limiter import limiter
from app.models.order import Order, OrderStatus
from app.repositories.order_repository import OrderRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.restaurant_repository import RestaurantRepository
from app.schemas.order import (
    OrderCreate,
    OrderResponse,
    OrderStatusUpdate,
    PaginatedOrderResponse,
)
from app.services.order_service import OrderService
from app.utils.pagination import PaginationParams

router = APIRouter(tags=["orders"])


def _get_service(db: Annotated[AsyncSession, Depends(get_db)]) -> OrderService:
    return OrderService(
        OrderRepository(db),
        RestaurantRepository(db),
        ProductRepository(db),
    )


def _order_response(order: Order) -> OrderResponse:
    return OrderResponse.model_validate(order)


@router.post(
    "/public/restaurants/{slug}/orders",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("20/minute")
async def create_order(
    request: Request,  # noqa: ARG001 — required by slowapi rate limiter
    slug: str,
    data: OrderCreate,
    service: Annotated[OrderService, Depends(_get_service)],
) -> OrderResponse:
    try:
        order = await service.create_order(slug=slug, data=data)
    except NotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except ForbiddenError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)
        ) from exc
    return _order_response(order)


@router.get(
    "/restaurants/{restaurant_id}/orders",
    response_model=PaginatedOrderResponse,
)
async def list_orders(
    restaurant_id: uuid.UUID,
    current_user: CurrentUser,
    service: Annotated[OrderService, Depends(_get_service)],
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    status_filter: Annotated[OrderStatus | None, Query(alias="status")] = None,
) -> PaginatedOrderResponse:
    try:
        result = await service.list_orders(
            restaurant_id=restaurant_id,
            owner_id=current_user.id,
            pagination=PaginationParams(page=page, limit=limit),
            status=status_filter,
        )
    except NotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except ForbiddenError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)
        ) from exc

    return PaginatedOrderResponse(
        items=[_order_response(o) for o in result.items],
        total=result.total,
        page=result.page,
        limit=result.limit,
        pages=result.pages,
    )


@router.get("/orders/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: uuid.UUID,
    current_user: CurrentUser,
    service: Annotated[OrderService, Depends(_get_service)],
) -> OrderResponse:
    try:
        order = await service.get_order(order_id=order_id, owner_id=current_user.id)
    except NotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except ForbiddenError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)
        ) from exc
    return _order_response(order)


@router.patch("/orders/{order_id}/status", response_model=OrderResponse)
async def update_order_status(
    order_id: uuid.UUID,
    data: OrderStatusUpdate,
    current_user: CurrentUser,
    service: Annotated[OrderService, Depends(_get_service)],
) -> OrderResponse:
    try:
        order = await service.update_status(
            order_id=order_id, owner_id=current_user.id, data=data
        )
    except NotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except ForbiddenError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)
        ) from exc
    except BusinessRuleError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    return _order_response(order)
