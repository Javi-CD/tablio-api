from app.core.exceptions import NotFoundError
from app.repositories.public_menu_repository import PublicMenuRepository
from app.schemas.public_menu import (
    PublicCategoryResponse,
    PublicMenuResponse,
    PublicProductResponse,
    PublicRestaurantResponse,
)


class PublicMenuService:
    def __init__(self, repository: PublicMenuRepository):
        self._repo = repository

    async def get_menu(self, slug: str) -> PublicMenuResponse:
        restaurant = await self._repo.get_restaurant_by_slug(slug)
        if not restaurant:
            raise NotFoundError("Restaurant not found or inactive.")

        categories = await self._repo.get_active_categories(restaurant.id)
        products = await self._repo.get_available_products(restaurant.id)

        # Group products by category_id
        products_by_cat = {}
        for p in products:
            if p.category_id not in products_by_cat:
                products_by_cat[p.category_id] = []
            products_by_cat[p.category_id].append(
                PublicProductResponse(
                    id=p.id,
                    name=p.name,
                    description=p.description,
                    price=str(p.price),
                    image_url=p.image_url,
                )
            )

        # Build category responses with nested products
        category_responses = []
        for cat in categories:
            cat_products = products_by_cat.get(cat.id, [])
            category_responses.append(
                PublicCategoryResponse(
                    id=cat.id,
                    name=cat.name,
                    description=cat.description,
                    sort_order=cat.sort_order,
                    products=cat_products,
                )
            )

        return PublicMenuResponse(
            restaurant=PublicRestaurantResponse.from_orm(restaurant),
            categories=category_responses,
        )

    async def get_restaurant(self, slug: str) -> PublicRestaurantResponse:
        restaurant = await self._repo.get_restaurant_by_slug(slug)
        if not restaurant:
            raise NotFoundError("Restaurant not found or inactive.")
        return PublicRestaurantResponse.from_orm(restaurant)
