from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.category import Category
from app.models.restaurant import Restaurant
from app.schemas.category import CategoryCreate, CategoryUpdate
from app.services.category_service import CategoryService


def _make_restaurant(owner_id: object = None) -> Restaurant:
    r = MagicMock(spec=Restaurant)
    r.id = uuid4()
    r.owner_id = owner_id or uuid4()
    return r


def _make_category(restaurant_id: object = None) -> Category:
    c = MagicMock(spec=Category)
    c.id = uuid4()
    c.restaurant_id = restaurant_id or uuid4()
    c.name = "Entradas"
    c.description = None
    c.sort_order = 0
    c.is_active = True
    return c


def _make_service(
    restaurant: Restaurant | None = None,
    category: Category | None = None,
    category_list: list[Category] | None = None,
) -> CategoryService:
    repo = AsyncMock()
    repo.create.return_value = category or _make_category()
    repo.get_by_id.return_value = category
    repo.list_by_restaurant.return_value = category_list or []
    repo.update.return_value = category or _make_category()

    restaurant_repo = AsyncMock()
    restaurant_repo.get_by_id.return_value = restaurant

    return CategoryService(repo, restaurant_repo)


class TestCreateCategory:
    async def test_create_raises_not_found_when_restaurant_missing(self) -> None:
        service = _make_service(restaurant=None)
        with pytest.raises(NotFoundError):
            await service.create(
                restaurant_id=uuid4(),
                owner_id=uuid4(),
                data=CategoryCreate(name="Sopas"),
            )

    async def test_create_raises_forbidden_when_not_owner(self) -> None:
        owner_id = uuid4()
        restaurant = _make_restaurant(owner_id=uuid4())
        service = _make_service(restaurant=restaurant)
        with pytest.raises(ForbiddenError):
            await service.create(
                restaurant_id=restaurant.id,
                owner_id=owner_id,
                data=CategoryCreate(name="Sopas"),
            )

    async def test_create_returns_category_on_success(self) -> None:
        owner_id = uuid4()
        restaurant = _make_restaurant(owner_id=owner_id)
        cat = _make_category(restaurant_id=restaurant.id)
        service = _make_service(restaurant=restaurant, category=cat)
        result = await service.create(
            restaurant_id=restaurant.id,
            owner_id=owner_id,
            data=CategoryCreate(name="Sopas", sort_order=1),
        )
        assert result.id == cat.id


class TestListCategories:
    async def test_list_returns_all_categories(self) -> None:
        owner_id = uuid4()
        restaurant = _make_restaurant(owner_id=owner_id)
        cats = [_make_category(restaurant.id), _make_category(restaurant.id)]
        service = _make_service(restaurant=restaurant, category_list=cats)
        result = await service.list_by_restaurant(
            restaurant_id=restaurant.id, owner_id=owner_id
        )
        assert len(result) == 2


class TestUpdateCategory:
    async def test_update_raises_not_found_when_category_missing(self) -> None:
        service = _make_service(category=None)
        with pytest.raises(NotFoundError):
            await service.update(
                category_id=uuid4(),
                owner_id=uuid4(),
                data=CategoryUpdate(name="Nueva"),
            )

    async def test_update_raises_forbidden_when_not_owner(self) -> None:
        owner_id = uuid4()
        restaurant = _make_restaurant(owner_id=uuid4())
        cat = _make_category(restaurant_id=restaurant.id)
        service = _make_service(restaurant=restaurant, category=cat)
        with pytest.raises(ForbiddenError):
            await service.update(
                category_id=cat.id,
                owner_id=owner_id,
                data=CategoryUpdate(name="Nueva"),
            )

    async def test_update_returns_updated_category(self) -> None:
        owner_id = uuid4()
        restaurant = _make_restaurant(owner_id=owner_id)
        cat = _make_category(restaurant_id=restaurant.id)
        service = _make_service(restaurant=restaurant, category=cat)
        result = await service.update(
            category_id=cat.id,
            owner_id=owner_id,
            data=CategoryUpdate(name="Actualizada"),
        )
        assert result is not None


class TestDeleteCategory:
    async def test_delete_raises_not_found_when_category_missing(self) -> None:
        service = _make_service(category=None)
        with pytest.raises(NotFoundError):
            await service.delete(category_id=uuid4(), owner_id=uuid4())

    async def test_delete_raises_forbidden_when_not_owner(self) -> None:
        owner_id = uuid4()
        restaurant = _make_restaurant(owner_id=uuid4())
        cat = _make_category(restaurant_id=restaurant.id)
        service = _make_service(restaurant=restaurant, category=cat)
        with pytest.raises(ForbiddenError):
            await service.delete(category_id=cat.id, owner_id=owner_id)

    async def test_delete_soft_deletes_category(self) -> None:
        owner_id = uuid4()
        restaurant = _make_restaurant(owner_id=owner_id)
        cat = _make_category(restaurant_id=restaurant.id)
        repo = AsyncMock()
        repo.get_by_id.return_value = cat
        repo.update.return_value = cat
        restaurant_repo = AsyncMock()
        restaurant_repo.get_by_id.return_value = restaurant
        service = CategoryService(repo, restaurant_repo)

        await service.delete(category_id=cat.id, owner_id=owner_id)

        repo.update.assert_called_once_with(cat, is_active=False)
