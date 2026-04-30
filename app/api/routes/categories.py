import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, get_db
from app.core.exceptions import ForbiddenError, NotFoundError
from app.repositories.category_repository import CategoryRepository
from app.repositories.restaurant_repository import RestaurantRepository
from app.schemas.category import CategoryCreate, CategoryResponse, CategoryUpdate
from app.services.category_service import CategoryService

router = APIRouter(tags=["categories"])


def _get_service(db: Annotated[AsyncSession, Depends(get_db)]) -> CategoryService:
    return CategoryService(CategoryRepository(db), RestaurantRepository(db))


@router.post(
    "/restaurants/{restaurant_id}/categories",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_category(
    restaurant_id: uuid.UUID,
    data: CategoryCreate,
    current_user: CurrentUser,
    service: Annotated[CategoryService, Depends(_get_service)],
) -> CategoryResponse:
    try:
        category = await service.create(
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
    return CategoryResponse.model_validate(category)


@router.get(
    "/restaurants/{restaurant_id}/categories",
    response_model=list[CategoryResponse],
)
async def list_categories(
    restaurant_id: uuid.UUID,
    current_user: CurrentUser,
    service: Annotated[CategoryService, Depends(_get_service)],
) -> list[CategoryResponse]:
    try:
        categories = await service.list_by_restaurant(
            restaurant_id=restaurant_id,
            owner_id=current_user.id,
        )
    except NotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except ForbiddenError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)
        ) from exc
    return [CategoryResponse.model_validate(c) for c in categories]


@router.patch("/categories/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: uuid.UUID,
    data: CategoryUpdate,
    current_user: CurrentUser,
    service: Annotated[CategoryService, Depends(_get_service)],
) -> CategoryResponse:
    try:
        category = await service.update(
            category_id=category_id,
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
    return CategoryResponse.model_validate(category)


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: uuid.UUID,
    current_user: CurrentUser,
    service: Annotated[CategoryService, Depends(_get_service)],
) -> None:
    try:
        await service.delete(category_id=category_id, owner_id=current_user.id)
    except NotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except ForbiddenError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)
        ) from exc
