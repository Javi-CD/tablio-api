"""Integration tests for public menu endpoints."""

from uuid import uuid4

from httpx import AsyncClient


def _email() -> str:
    return f"{uuid4().hex[:8]}@tablio.co"


async def _register_and_login(client: AsyncClient) -> tuple[str, str]:
    email = _email()
    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Secure123!", "full_name": "Owner"},
    )
    return resp.json()["access_token"], email


async def _create_restaurant(client: AsyncClient, token: str) -> tuple[str, str]:
    resp = await client.post(
        "/api/v1/restaurants",
        json={"name": f"Resto {uuid4().hex[:6]}"},
        headers={"Authorization": f"Bearer {token}"},
    )
    body = resp.json()
    return body["id"], body["slug"]


async def _create_category(
    client: AsyncClient,
    token: str,
    restaurant_id: str,
    name: str = "Entradas",
    sort_order: int = 0,
) -> str:
    resp = await client.post(
        f"/api/v1/restaurants/{restaurant_id}/categories",
        json={"name": name, "sort_order": sort_order},
        headers={"Authorization": f"Bearer {token}"},
    )
    return resp.json()["id"]


async def _create_product(
    client: AsyncClient,
    token: str,
    restaurant_id: str,
    name: str = "Hamburguesa",
    price: str = "18000",
    category_id: str | None = None,
    is_available: bool = True,
) -> str:
    payload: dict[str, object] = {"name": name, "price": price}
    if category_id:
        payload["category_id"] = category_id
    resp = await client.post(
        f"/api/v1/restaurants/{restaurant_id}/products",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    product_id: str = resp.json()["id"]
    if not is_available:
        await client.patch(
            f"/api/v1/products/{product_id}",
            json={"is_available": False},
            headers={"Authorization": f"Bearer {token}"},
        )
    return product_id


class TestGetPublicMenu:
    async def test_returns_200_with_full_structure(self, client: AsyncClient) -> None:
        token, _ = await _register_and_login(client)
        restaurant_id, slug = await _create_restaurant(client, token)
        cat_id = await _create_category(client, token, restaurant_id)
        await _create_product(client, token, restaurant_id, category_id=cat_id)

        resp = await client.get(f"/api/v1/public/menus/{slug}")

        assert resp.status_code == 200
        body = resp.json()
        assert "restaurant" in body
        assert "categories" in body
        assert body["restaurant"]["slug"] == slug

    async def test_products_are_grouped_by_category(self, client: AsyncClient) -> None:
        token, _ = await _register_and_login(client)
        restaurant_id, slug = await _create_restaurant(client, token)
        cat_a = await _create_category(
            client, token, restaurant_id, name="Platos", sort_order=0
        )
        cat_b = await _create_category(
            client, token, restaurant_id, name="Bebidas", sort_order=1
        )
        await _create_product(
            client, token, restaurant_id, name="Tacos", category_id=cat_a
        )
        await _create_product(
            client, token, restaurant_id, name="Soda", category_id=cat_b
        )

        resp = await client.get(f"/api/v1/public/menus/{slug}")

        assert resp.status_code == 200
        categories = resp.json()["categories"]
        assert len(categories) == 2
        platos = next(c for c in categories if c["id"] == cat_a)
        bebidas = next(c for c in categories if c["id"] == cat_b)
        assert len(platos["products"]) == 1
        assert platos["products"][0]["name"] == "Tacos"
        assert len(bebidas["products"]) == 1
        assert bebidas["products"][0]["name"] == "Soda"

    async def test_categories_sorted_by_sort_order(self, client: AsyncClient) -> None:
        token, _ = await _register_and_login(client)
        restaurant_id, slug = await _create_restaurant(client, token)
        await _create_category(
            client, token, restaurant_id, name="Z Primero", sort_order=0
        )
        await _create_category(
            client, token, restaurant_id, name="A Segundo", sort_order=1
        )

        resp = await client.get(f"/api/v1/public/menus/{slug}")

        categories = resp.json()["categories"]
        assert len(categories) == 2
        assert categories[0]["name"] == "Z Primero"
        assert categories[1]["name"] == "A Segundo"

    async def test_excludes_unavailable_products(self, client: AsyncClient) -> None:
        token, _ = await _register_and_login(client)
        restaurant_id, slug = await _create_restaurant(client, token)
        cat_id = await _create_category(client, token, restaurant_id)
        await _create_product(
            client, token, restaurant_id, name="Disponible", category_id=cat_id
        )
        await _create_product(
            client,
            token,
            restaurant_id,
            name="No disponible",
            category_id=cat_id,
            is_available=False,
        )

        resp = await client.get(f"/api/v1/public/menus/{slug}")

        products = resp.json()["categories"][0]["products"]
        assert len(products) == 1
        assert products[0]["name"] == "Disponible"

    async def test_excludes_inactive_categories(self, client: AsyncClient) -> None:
        token, _ = await _register_and_login(client)
        restaurant_id, slug = await _create_restaurant(client, token)
        active_cat = await _create_category(client, token, restaurant_id, name="Activa")
        inactive_cat = await _create_category(
            client, token, restaurant_id, name="Inactiva"
        )
        await client.patch(
            f"/api/v1/categories/{inactive_cat}",
            json={"is_active": False},
            headers={"Authorization": f"Bearer {token}"},
        )

        resp = await client.get(f"/api/v1/public/menus/{slug}")

        categories = resp.json()["categories"]
        assert len(categories) == 1
        assert categories[0]["id"] == active_cat

    async def test_products_without_category_are_not_shown(
        self, client: AsyncClient
    ) -> None:
        token, _ = await _register_and_login(client)
        restaurant_id, slug = await _create_restaurant(client, token)
        await _create_category(client, token, restaurant_id)
        await _create_product(client, token, restaurant_id, name="Sin categoría")

        resp = await client.get(f"/api/v1/public/menus/{slug}")

        categories = resp.json()["categories"]
        all_products = [p for cat in categories for p in cat["products"]]
        assert all(p["name"] != "Sin categoría" for p in all_products)

    async def test_returns_404_for_unknown_slug(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/public/menus/no-existe-xyz")
        assert resp.status_code == 404

    async def test_empty_menu_returns_empty_categories(
        self, client: AsyncClient
    ) -> None:
        token, _ = await _register_and_login(client)
        restaurant_id, slug = await _create_restaurant(client, token)
        await _create_category(client, token, restaurant_id)

        resp = await client.get(f"/api/v1/public/menus/{slug}")

        assert resp.status_code == 200
        body = resp.json()
        assert len(body["categories"]) == 1
        assert body["categories"][0]["products"] == []

    async def test_requires_no_authentication(self, client: AsyncClient) -> None:
        token, _ = await _register_and_login(client)
        _, slug = await _create_restaurant(client, token)

        resp = await client.get(f"/api/v1/public/menus/{slug}")
        assert resp.status_code == 200

    async def test_product_price_is_returned(self, client: AsyncClient) -> None:
        token, _ = await _register_and_login(client)
        restaurant_id, slug = await _create_restaurant(client, token)
        cat_id = await _create_category(client, token, restaurant_id)
        await _create_product(
            client,
            token,
            restaurant_id,
            name="Pizza",
            price="25000",
            category_id=cat_id,
        )

        resp = await client.get(f"/api/v1/public/menus/{slug}")

        products = resp.json()["categories"][0]["products"]
        assert float(products[0]["price"]) == 25000.0


class TestGetPublicRestaurant:
    async def test_returns_200_with_restaurant_data(self, client: AsyncClient) -> None:
        token, _ = await _register_and_login(client)
        _, slug = await _create_restaurant(client, token)

        resp = await client.get(f"/api/v1/public/restaurants/{slug}")

        assert resp.status_code == 200
        body = resp.json()
        assert body["slug"] == slug
        assert "name" in body
        assert "owner_id" not in body

    async def test_returns_404_for_unknown_slug(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/public/restaurants/no-existe-xyz")
        assert resp.status_code == 404

    async def test_requires_no_authentication(self, client: AsyncClient) -> None:
        token, _ = await _register_and_login(client)
        _, slug = await _create_restaurant(client, token)

        resp = await client.get(f"/api/v1/public/restaurants/{slug}")
        assert resp.status_code == 200
