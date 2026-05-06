"""Integration tests for /api/v1/restaurants/{id}/products and /products/* endpoints."""

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


async def _create_restaurant(client: AsyncClient, token: str) -> str:
    resp = await client.post(
        "/api/v1/restaurants",
        json={"name": f"Resto {uuid4().hex[:6]}"},
        headers={"Authorization": f"Bearer {token}"},
    )
    return resp.json()["id"]


async def _create_category(
    client: AsyncClient, token: str, restaurant_id: str, name: str = "Principal"
) -> str:
    resp = await client.post(
        f"/api/v1/restaurants/{restaurant_id}/categories",
        json={"name": name},
        headers={"Authorization": f"Bearer {token}"},
    )
    return resp.json()["id"]


class TestCreateProduct:
    async def test_create_returns_201(self, client: AsyncClient) -> None:
        token, _ = await _register_and_login(client)
        restaurant_id = await _create_restaurant(client, token)
        resp = await client.post(
            f"/api/v1/restaurants/{restaurant_id}/products",
            json={"name": "Hamburguesa", "price": "18000"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["name"] == "Hamburguesa"
        assert float(body["price"]) == 18000.0
        assert body["is_available"] is True

    async def test_create_with_category(self, client: AsyncClient) -> None:
        token, _ = await _register_and_login(client)
        restaurant_id = await _create_restaurant(client, token)
        category_id = await _create_category(client, token, restaurant_id)
        resp = await client.post(
            f"/api/v1/restaurants/{restaurant_id}/products",
            json={
                "name": "Ensalada",
                "price": "12000",
                "category_id": category_id,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        assert resp.json()["category_id"] == category_id

    async def test_create_with_invalid_image_url_returns_422(
        self, client: AsyncClient
    ) -> None:
        token, _ = await _register_and_login(client)
        restaurant_id = await _create_restaurant(client, token)
        resp = await client.post(
            f"/api/v1/restaurants/{restaurant_id}/products",
            json={"name": "Pizza", "price": "20000", "image_url": "not-a-url"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422

    async def test_create_requires_auth(self, client: AsyncClient) -> None:
        resp = await client.post(
            f"/api/v1/restaurants/{uuid4()}/products",
            json={"name": "Pizza", "price": "20000"},
        )
        assert resp.status_code == 401

    async def test_create_returns_403_for_non_owner(self, client: AsyncClient) -> None:
        token_owner, _ = await _register_and_login(client)
        token_other, _ = await _register_and_login(client)
        restaurant_id = await _create_restaurant(client, token_owner)
        resp = await client.post(
            f"/api/v1/restaurants/{restaurant_id}/products",
            json={"name": "Pizza", "price": "20000"},
            headers={"Authorization": f"Bearer {token_other}"},
        )
        assert resp.status_code == 403

    async def test_create_rejects_category_from_other_restaurant(
        self, client: AsyncClient
    ) -> None:
        token1, _ = await _register_and_login(client)
        token2, _ = await _register_and_login(client)
        restaurant1 = await _create_restaurant(client, token1)
        restaurant2 = await _create_restaurant(client, token2)
        category_of_r2 = await _create_category(client, token2, restaurant2)
        resp = await client.post(
            f"/api/v1/restaurants/{restaurant1}/products",
            json={
                "name": "Sopa",
                "price": "8000",
                "category_id": category_of_r2,
            },
            headers={"Authorization": f"Bearer {token1}"},
        )
        assert resp.status_code == 403


class TestListProducts:
    async def test_list_returns_all_including_unavailable(
        self, client: AsyncClient
    ) -> None:
        token, _ = await _register_and_login(client)
        restaurant_id = await _create_restaurant(client, token)
        for name, available in [("A", True), ("B", True), ("C", False)]:
            create_resp = await client.post(
                f"/api/v1/restaurants/{restaurant_id}/products",
                json={"name": name, "price": "10000"},
                headers={"Authorization": f"Bearer {token}"},
            )
            if not available:
                product_id = create_resp.json()["id"]
                await client.delete(
                    f"/api/v1/products/{product_id}",
                    headers={"Authorization": f"Bearer {token}"},
                )
        resp = await client.get(
            f"/api/v1/restaurants/{restaurant_id}/products",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 3


class TestUpdateProduct:
    async def test_update_name_and_price(self, client: AsyncClient) -> None:
        token, _ = await _register_and_login(client)
        restaurant_id = await _create_restaurant(client, token)
        create_resp = await client.post(
            f"/api/v1/restaurants/{restaurant_id}/products",
            json={"name": "Original", "price": "10000"},
            headers={"Authorization": f"Bearer {token}"},
        )
        product_id = create_resp.json()["id"]
        resp = await client.patch(
            f"/api/v1/products/{product_id}",
            json={"name": "Actualizado", "price": "15000"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["name"] == "Actualizado"
        assert float(body["price"]) == 15000.0

    async def test_toggle_availability(self, client: AsyncClient) -> None:
        token, _ = await _register_and_login(client)
        restaurant_id = await _create_restaurant(client, token)
        create_resp = await client.post(
            f"/api/v1/restaurants/{restaurant_id}/products",
            json={"name": "Tacos", "price": "9000"},
            headers={"Authorization": f"Bearer {token}"},
        )
        product_id = create_resp.json()["id"]
        resp = await client.patch(
            f"/api/v1/products/{product_id}",
            json={"is_available": False},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["is_available"] is False

    async def test_update_returns_403_for_non_owner(self, client: AsyncClient) -> None:
        token_owner, _ = await _register_and_login(client)
        token_other, _ = await _register_and_login(client)
        restaurant_id = await _create_restaurant(client, token_owner)
        create_resp = await client.post(
            f"/api/v1/restaurants/{restaurant_id}/products",
            json={"name": "Exclusivo", "price": "30000"},
            headers={"Authorization": f"Bearer {token_owner}"},
        )
        product_id = create_resp.json()["id"]
        resp = await client.patch(
            f"/api/v1/products/{product_id}",
            json={"name": "Hackeado"},
            headers={"Authorization": f"Bearer {token_other}"},
        )
        assert resp.status_code == 403


class TestDeleteProduct:
    async def test_delete_returns_204(self, client: AsyncClient) -> None:
        token, _ = await _register_and_login(client)
        restaurant_id = await _create_restaurant(client, token)
        create_resp = await client.post(
            f"/api/v1/restaurants/{restaurant_id}/products",
            json={"name": "Temporal", "price": "5000"},
            headers={"Authorization": f"Bearer {token}"},
        )
        product_id = create_resp.json()["id"]
        resp = await client.delete(
            f"/api/v1/products/{product_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 204

    async def test_delete_nonexistent_returns_404(self, client: AsyncClient) -> None:
        token, _ = await _register_and_login(client)
        resp = await client.delete(
            f"/api/v1/products/{uuid4()}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404
