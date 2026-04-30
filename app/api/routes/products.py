import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, get_db
from app.core.exceptions import ForbiddenError, NotFoundError
from app.repositories.category_repository import CategoryRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.restaurant_repository import RestaurantRepository
from app.schemas.product import ProductCreate, ProductResponse, ProductUpdate
from app.services.product_service import ProductService

router = APIRouter(tags=["products"])


def _get_service(db: Annotated[AsyncSession, Depends(get_db)]) -> ProductService:
    return ProductService(
        ProductRepository(db),
        RestaurantRepository(db),
        CategoryRepository(db),
    )


@router.post(
    "/restaurants/{restaurant_id}/products",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_product(
    restaurant_id: uuid.UUID,
    data: ProductCreate,
    current_user: CurrentUser,
    service: Annotated[ProductService, Depends(_get_service)],
) -> ProductResponse:
    try:
        product = await service.create(
            restaurant_id=restaurant_id,
            owner_id=current_user.id,
            data=data,
        )
    except NotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except ForbiddenError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)
        ) from exc
    return ProductResponse.model_validate(product)


@router.get(
    "/restaurants/{restaurant_id}/products",
    response_model=list[ProductResponse],
)
async def list_products(
    restaurant_id: uuid.UUID,
    current_user: CurrentUser,
    service: Annotated[ProductService, Depends(_get_service)],
) -> list[ProductResponse]:
    try:
        products = await service.list_by_restaurant(
            restaurant_id=restaurant_id,
            owner_id=current_user.id,
            include_unavailable=True,
        )
    except NotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except ForbiddenError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)
        ) from exc
    return [ProductResponse.model_validate(p) for p in products]


@router.patch("/products/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: uuid.UUID,
    data: ProductUpdate,
    current_user: CurrentUser,
    service: Annotated[ProductService, Depends(_get_service)],
) -> ProductResponse:
    try:
        product = await service.update(
            product_id=product_id,
            owner_id=current_user.id,
            data=data,
        )
    except NotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except ForbiddenError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)
        ) from exc
    return ProductResponse.model_validate(product)


@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: uuid.UUID,
    current_user: CurrentUser,
    service: Annotated[ProductService, Depends(_get_service)],
) -> None:
    try:
        await service.delete(product_id=product_id, owner_id=current_user.id)
    except NotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except ForbiddenError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)
        ) from exc
