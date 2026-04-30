import uuid

from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.product import Product
from app.repositories.category_repository import CategoryRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.restaurant_repository import RestaurantRepository
from app.schemas.product import ProductCreate, ProductUpdate


class ProductService:
    def __init__(
        self,
        repo: ProductRepository,
        restaurant_repo: RestaurantRepository,
        category_repo: CategoryRepository,
    ) -> None:
        self._repo = repo
        self._restaurant_repo = restaurant_repo
        self._category_repo = category_repo

    async def _assert_ownership(
        self, restaurant_id: uuid.UUID, owner_id: uuid.UUID
    ) -> None:
        restaurant = await self._restaurant_repo.get_by_id(restaurant_id)
        if restaurant is None:
            raise NotFoundError("Restaurant not found.")
        if restaurant.owner_id != owner_id:
            raise ForbiddenError("Not authorized to modify this restaurant.")

    async def _assert_category_belongs(
        self, category_id: uuid.UUID, restaurant_id: uuid.UUID
    ) -> None:
        category = await self._category_repo.get_by_id(category_id)
        if category is None:
            raise NotFoundError("Category not found.")
        if category.restaurant_id != restaurant_id:
            raise ForbiddenError("Category does not belong to this restaurant.")

    async def create(
        self,
        restaurant_id: uuid.UUID,
        owner_id: uuid.UUID,
        data: ProductCreate,
    ) -> Product:
        await self._assert_ownership(restaurant_id, owner_id)
        if data.category_id is not None:
            await self._assert_category_belongs(data.category_id, restaurant_id)
        return await self._repo.create(
            restaurant_id=restaurant_id,
            name=data.name,
            price=data.price,
            description=data.description,
            image_url=data.image_url,
            category_id=data.category_id,
        )

    async def list_by_restaurant(
        self,
        restaurant_id: uuid.UUID,
        owner_id: uuid.UUID,
        include_unavailable: bool = True,
    ) -> list[Product]:
        await self._assert_ownership(restaurant_id, owner_id)
        return await self._repo.list_by_restaurant(
            restaurant_id, include_unavailable=include_unavailable
        )

    async def update(
        self,
        product_id: uuid.UUID,
        owner_id: uuid.UUID,
        data: ProductUpdate,
    ) -> Product:
        product = await self._repo.get_by_id(product_id)
        if product is None:
            raise NotFoundError("Product not found.")
        await self._assert_ownership(product.restaurant_id, owner_id)

        if data.category_id is not None:
            await self._assert_category_belongs(data.category_id, product.restaurant_id)

        fields = dict(data.model_dump(exclude_unset=True))
        if not fields:
            return product
        return await self._repo.update(product, **fields)

    async def delete(self, product_id: uuid.UUID, owner_id: uuid.UUID) -> None:
        product = await self._repo.get_by_id(product_id)
        if product is None:
            raise NotFoundError("Product not found.")
        await self._assert_ownership(product.restaurant_id, owner_id)
        await self._repo.update(product, is_available=False)
