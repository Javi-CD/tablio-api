import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, get_db
from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.repositories.restaurant_repository import RestaurantRepository
from app.schemas.restaurant import (
    RestaurantCreate,
    RestaurantResponse,
    RestaurantUpdate,
)
from app.services.restaurant_service import RestaurantService

router = APIRouter(prefix="/restaurants", tags=["restaurants"])


def _get_service(db: Annotated[AsyncSession, Depends(get_db)]) -> RestaurantService:
    return RestaurantService(RestaurantRepository(db))


@router.post("", response_model=RestaurantResponse, status_code=status.HTTP_201_CREATED)
async def create_restaurant(
    data: RestaurantCreate,
    current_user: CurrentUser,
    service: Annotated[RestaurantService, Depends(_get_service)],
) -> RestaurantResponse:
    try:
        restaurant = await service.create(owner_id=current_user.id, data=data)
    except ConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc
    return RestaurantResponse.model_validate(restaurant)


@router.get("/me", response_model=RestaurantResponse)
async def get_my_restaurant(
    current_user: CurrentUser,
    service: Annotated[RestaurantService, Depends(_get_service)],
) -> RestaurantResponse:
    restaurant = await service.get_by_owner(owner_id=current_user.id)
    if restaurant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Restaurant not found."
        )
    return RestaurantResponse.model_validate(restaurant)


@router.patch("/{restaurant_id}", response_model=RestaurantResponse)
async def update_restaurant(
    restaurant_id: uuid.UUID,
    data: RestaurantUpdate,
    current_user: CurrentUser,
    service: Annotated[RestaurantService, Depends(_get_service)],
) -> RestaurantResponse:
    try:
        restaurant = await service.update(
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
    except ConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc
    return RestaurantResponse.model_validate(restaurant)
