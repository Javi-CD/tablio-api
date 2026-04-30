import uuid

from app.core.exceptions import NotFoundError
from app.repositories.public_menu_repository import PublicMenuRepository
from app.schemas.public_menu import (
    PublicCategoryResponse,
    PublicMenuResponse,
    PublicProductResponse,
    PublicRestaurantResponse,
)


class PublicMenuService:
    def __init__(self, repo: PublicMenuRepository) -> None:
        self._repo = repo

    async def get_menu(self, slug: str) -> PublicMenuResponse:
        restaurant = await self._repo.get_restaurant_by_slug(slug)
        if restaurant is None:
            raise NotFoundError(f"Restaurant with slug '{slug}' not found.")

        categories = await self._repo.get_active_categories(restaurant.id)
        products = await self._repo.get_available_products(restaurant.id)

        products_by_category: dict[uuid.UUID, list[PublicProductResponse]] = {}
        for product in products:
            if product.category_id is None:
                continue
            bucket = products_by_category.setdefault(product.category_id, [])
            bucket.append(PublicProductResponse.model_validate(product))

        menu_categories = [
            PublicCategoryResponse(
                id=cat.id,
                name=cat.name,
                description=cat.description,
                sort_order=cat.sort_order,
                products=products_by_category.get(cat.id, []),
            )
            for cat in categories
        ]

        return PublicMenuResponse(
            restaurant=PublicRestaurantResponse.model_validate(restaurant),
            categories=menu_categories,
        )

    async def get_restaurant(self, slug: str) -> PublicRestaurantResponse:
        restaurant = await self._repo.get_restaurant_by_slug(slug)
        if restaurant is None:
            raise NotFoundError(f"Restaurant with slug '{slug}' not found.")
        return PublicRestaurantResponse.model_validate(restaurant)
