import uuid

from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.restaurant import Restaurant
from app.repositories.restaurant_repository import RestaurantRepository
from app.schemas.restaurant import RestaurantCreate, RestaurantUpdate
from app.utils.slug import ensure_unique_slug, generate_slug


class RestaurantService:
    def __init__(self, repo: RestaurantRepository) -> None:
        self._repo = repo

    async def create(self, owner_id: uuid.UUID, data: RestaurantCreate) -> Restaurant:
        base_slug = generate_slug(data.name)
        slug = await ensure_unique_slug(base_slug, self._repo.get_by_slug)
        return await self._repo.create(
            owner_id=owner_id,
            name=data.name,
            slug=slug,
            description=data.description,
            logo_url=data.logo_url,
            phone=data.phone,
            address=data.address,
        )

    async def get_by_owner(self, owner_id: uuid.UUID) -> Restaurant | None:
        return await self._repo.get_by_owner_id(owner_id)

    async def update(
        self,
        restaurant_id: uuid.UUID,
        owner_id: uuid.UUID,
        data: RestaurantUpdate,
    ) -> Restaurant:
        restaurant = await self._repo.get_by_id(restaurant_id)
        if restaurant is None:
            raise NotFoundError("Restaurant not found.")
        if restaurant.owner_id != owner_id:
            raise ForbiddenError("Not authorized to modify this restaurant.")

        fields: dict[str, object] = {}
        if data.name is not None:
            fields["name"] = data.name
        if data.description is not None:
            fields["description"] = data.description
        if data.logo_url is not None:
            fields["logo_url"] = data.logo_url
        if data.phone is not None:
            fields["phone"] = data.phone
        if data.address is not None:
            fields["address"] = data.address

        if data.slug is not None:
            new_slug = await ensure_unique_slug(
                data.slug, self._repo.get_by_slug, exclude_id=restaurant_id
            )
            fields["slug"] = new_slug

        if fields:
            restaurant = await self._repo.update(restaurant, **fields)
        return restaurant
