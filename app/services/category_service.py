import uuid

from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.category import Category
from app.repositories.category_repository import CategoryRepository
from app.repositories.restaurant_repository import RestaurantRepository
from app.schemas.category import CategoryCreate, CategoryUpdate


class CategoryService:
    def __init__(
        self,
        repo: CategoryRepository,
        restaurant_repo: RestaurantRepository,
    ) -> None:
        self._repo = repo
        self._restaurant_repo = restaurant_repo

    async def _assert_ownership(
        self, restaurant_id: uuid.UUID, owner_id: uuid.UUID
    ) -> None:
        restaurant = await self._restaurant_repo.get_by_id(restaurant_id)
        if restaurant is None:
            raise NotFoundError("Restaurant not found.")
        if restaurant.owner_id != owner_id:
            raise ForbiddenError("Not authorized to modify this restaurant.")

    async def create(
        self,
        restaurant_id: uuid.UUID,
        owner_id: uuid.UUID,
        data: CategoryCreate,
    ) -> Category:
        await self._assert_ownership(restaurant_id, owner_id)
        return await self._repo.create(
            restaurant_id=restaurant_id,
            name=data.name,
            description=data.description,
            sort_order=data.sort_order,
        )

    async def list_by_restaurant(
        self, restaurant_id: uuid.UUID, owner_id: uuid.UUID
    ) -> list[Category]:
        await self._assert_ownership(restaurant_id, owner_id)
        return await self._repo.list_by_restaurant(restaurant_id, active_only=False)

    async def update(
        self,
        category_id: uuid.UUID,
        owner_id: uuid.UUID,
        data: CategoryUpdate,
    ) -> Category:
        category = await self._repo.get_by_id(category_id)
        if category is None:
            raise NotFoundError("Category not found.")
        await self._assert_ownership(category.restaurant_id, owner_id)

        fields = dict(data.model_dump(exclude_unset=True))
        if not fields:
            return category
        return await self._repo.update(category, **fields)

    async def delete(self, category_id: uuid.UUID, owner_id: uuid.UUID) -> None:
        category = await self._repo.get_by_id(category_id)
        if category is None:
            raise NotFoundError("Category not found.")
        await self._assert_ownership(category.restaurant_id, owner_id)
        await self._repo.update(category, is_active=False)
