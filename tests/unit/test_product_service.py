from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.category import Category
from app.models.product import Product
from app.models.restaurant import Restaurant
from app.schemas.product import ProductCreate, ProductUpdate
from app.services.product_service import ProductService


def _make_restaurant(owner_id: object = None) -> Restaurant:
    r = MagicMock(spec=Restaurant)
    r.id = uuid4()
    r.owner_id = owner_id or uuid4()
    return r


def _make_category(restaurant_id: object = None) -> Category:
    c = MagicMock(spec=Category)
    c.id = uuid4()
    c.restaurant_id = restaurant_id or uuid4()
    return c


def _make_product(restaurant_id: object = None) -> Product:
    p = MagicMock(spec=Product)
    p.id = uuid4()
    p.restaurant_id = restaurant_id or uuid4()
    p.name = "Hamburguesa"
    p.price = Decimal("18000")
    p.is_available = True
    return p


def _make_service(
    restaurant: Restaurant | None = None,
    category: Category | None = None,
    product: Product | None = None,
    product_list: list[Product] | None = None,
) -> ProductService:
    repo = AsyncMock()
    repo.create.return_value = product or _make_product()
    repo.get_by_id.return_value = product
    repo.list_by_restaurant.return_value = product_list or []
    repo.update.return_value = product or _make_product()

    restaurant_repo = AsyncMock()
    restaurant_repo.get_by_id.return_value = restaurant

    category_repo = AsyncMock()
    category_repo.get_by_id.return_value = category

    return ProductService(repo, restaurant_repo, category_repo)


class TestCreateProduct:
    async def test_create_raises_not_found_when_restaurant_missing(self) -> None:
        service = _make_service(restaurant=None)
        with pytest.raises(NotFoundError):
            await service.create(
                restaurant_id=uuid4(),
                owner_id=uuid4(),
                data=ProductCreate(name="Pizza", price=Decimal("25000")),
            )

    async def test_create_raises_forbidden_when_not_owner(self) -> None:
        owner_id = uuid4()
        restaurant = _make_restaurant(owner_id=uuid4())
        service = _make_service(restaurant=restaurant)
        with pytest.raises(ForbiddenError):
            await service.create(
                restaurant_id=restaurant.id,
                owner_id=owner_id,
                data=ProductCreate(name="Pizza", price=Decimal("25000")),
            )

    async def test_create_raises_not_found_when_category_missing(self) -> None:
        owner_id = uuid4()
        restaurant = _make_restaurant(owner_id=owner_id)
        service = _make_service(restaurant=restaurant, category=None)
        with pytest.raises(NotFoundError):
            await service.create(
                restaurant_id=restaurant.id,
                owner_id=owner_id,
                data=ProductCreate(
                    name="Pizza", price=Decimal("25000"), category_id=uuid4()
                ),
            )

    async def test_create_raises_forbidden_when_category_wrong_restaurant(
        self,
    ) -> None:
        owner_id = uuid4()
        restaurant = _make_restaurant(owner_id=owner_id)
        # Category belongs to a different restaurant
        category = _make_category(restaurant_id=uuid4())
        service = _make_service(restaurant=restaurant, category=category)
        with pytest.raises(ForbiddenError):
            await service.create(
                restaurant_id=restaurant.id,
                owner_id=owner_id,
                data=ProductCreate(
                    name="Pizza",
                    price=Decimal("25000"),
                    category_id=category.id,
                ),
            )

    async def test_create_returns_product_on_success(self) -> None:
        owner_id = uuid4()
        restaurant = _make_restaurant(owner_id=owner_id)
        prod = _make_product(restaurant_id=restaurant.id)
        service = _make_service(restaurant=restaurant, product=prod)
        result = await service.create(
            restaurant_id=restaurant.id,
            owner_id=owner_id,
            data=ProductCreate(name="Hamburguesa", price=Decimal("18000")),
        )
        assert result.id == prod.id


class TestUpdateProduct:
    async def test_update_raises_not_found_when_product_missing(self) -> None:
        service = _make_service(product=None)
        with pytest.raises(NotFoundError):
            await service.update(
                product_id=uuid4(),
                owner_id=uuid4(),
                data=ProductUpdate(name="Nuevo"),
            )

    async def test_update_raises_forbidden_when_not_owner(self) -> None:
        owner_id = uuid4()
        restaurant = _make_restaurant(owner_id=uuid4())
        prod = _make_product(restaurant_id=restaurant.id)
        service = _make_service(restaurant=restaurant, product=prod)
        with pytest.raises(ForbiddenError):
            await service.update(
                product_id=prod.id,
                owner_id=owner_id,
                data=ProductUpdate(name="Nuevo"),
            )

    async def test_update_returns_updated_product(self) -> None:
        owner_id = uuid4()
        restaurant = _make_restaurant(owner_id=owner_id)
        prod = _make_product(restaurant_id=restaurant.id)
        service = _make_service(restaurant=restaurant, product=prod)
        result = await service.update(
            product_id=prod.id,
            owner_id=owner_id,
            data=ProductUpdate(name="Actualizado"),
        )
        assert result is not None


class TestDeleteProduct:
    async def test_delete_raises_not_found_when_product_missing(self) -> None:
        service = _make_service(product=None)
        with pytest.raises(NotFoundError):
            await service.delete(product_id=uuid4(), owner_id=uuid4())

    async def test_delete_soft_deletes_product(self) -> None:
        owner_id = uuid4()
        restaurant = _make_restaurant(owner_id=owner_id)
        prod = _make_product(restaurant_id=restaurant.id)
        repo = AsyncMock()
        repo.get_by_id.return_value = prod
        repo.update.return_value = prod
        restaurant_repo = AsyncMock()
        restaurant_repo.get_by_id.return_value = restaurant
        category_repo = AsyncMock()
        service = ProductService(repo, restaurant_repo, category_repo)

        await service.delete(product_id=prod.id, owner_id=owner_id)

        repo.update.assert_called_once_with(prod, is_available=False)
