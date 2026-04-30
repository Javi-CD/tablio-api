"""Integration tests for categories endpoints."""

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


async def _create_restaurant(
    client: AsyncClient, token: str, name: str = "Mi Local"
) -> str:
    resp = await client.post(
        "/api/v1/restaurants",
        json={"name": name},
        headers={"Authorization": f"Bearer {token}"},
    )
    return resp.json()["id"]


class TestCreateCategory:
    async def test_create_returns_201(self, client: AsyncClient) -> None:
        token, _ = await _register_and_login(client)
        restaurant_id = await _create_restaurant(client, token)
        resp = await client.post(
            f"/api/v1/restaurants/{restaurant_id}/categories",
            json={"name": "Entradas", "sort_order": 0},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["name"] == "Entradas"
        assert body["sort_order"] == 0
        assert body["is_active"] is True

    async def test_create_requires_auth(self, client: AsyncClient) -> None:
        resp = await client.post(
            f"/api/v1/restaurants/{uuid4()}/categories",
            json={"name": "Entradas"},
        )
        assert resp.status_code == 401

    async def test_create_returns_403_for_non_owner(self, client: AsyncClient) -> None:
        token_owner, _ = await _register_and_login(client)
        token_other, _ = await _register_and_login(client)
        restaurant_id = await _create_restaurant(client, token_owner)
        resp = await client.post(
            f"/api/v1/restaurants/{restaurant_id}/categories",
            json={"name": "Postres"},
            headers={"Authorization": f"Bearer {token_other}"},
        )
        assert resp.status_code == 403

    async def test_create_returns_404_for_nonexistent_restaurant(
        self, client: AsyncClient
    ) -> None:
        token, _ = await _register_and_login(client)
        resp = await client.post(
            f"/api/v1/restaurants/{uuid4()}/categories",
            json={"name": "Sopas"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404


class TestListCategories:
    async def test_list_returns_all_categories(self, client: AsyncClient) -> None:
        token, _ = await _register_and_login(client)
        restaurant_id = await _create_restaurant(client, token)
        for name in ["Entradas", "Principales", "Postres"]:
            await client.post(
                f"/api/v1/restaurants/{restaurant_id}/categories",
                json={"name": name},
                headers={"Authorization": f"Bearer {token}"},
            )
        resp = await client.get(
            f"/api/v1/restaurants/{restaurant_id}/categories",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 3

    async def test_list_includes_inactive_categories(self, client: AsyncClient) -> None:
        token, _ = await _register_and_login(client)
        restaurant_id = await _create_restaurant(client, token)
        create_resp = await client.post(
            f"/api/v1/restaurants/{restaurant_id}/categories",
            json={"name": "Temporada"},
            headers={"Authorization": f"Bearer {token}"},
        )
        category_id = create_resp.json()["id"]
        await client.delete(
            f"/api/v1/categories/{category_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        resp = await client.get(
            f"/api/v1/restaurants/{restaurant_id}/categories",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        items = resp.json()
        assert any(c["id"] == category_id for c in items)
        deleted = next(c for c in items if c["id"] == category_id)
        assert deleted["is_active"] is False


class TestUpdateCategory:
    async def test_update_name_and_sort_order(self, client: AsyncClient) -> None:
        token, _ = await _register_and_login(client)
        restaurant_id = await _create_restaurant(client, token)
        create_resp = await client.post(
            f"/api/v1/restaurants/{restaurant_id}/categories",
            json={"name": "Original", "sort_order": 0},
            headers={"Authorization": f"Bearer {token}"},
        )
        category_id = create_resp.json()["id"]
        resp = await client.patch(
            f"/api/v1/categories/{category_id}",
            json={"name": "Actualizada", "sort_order": 5},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["name"] == "Actualizada"
        assert body["sort_order"] == 5

    async def test_update_returns_403_for_non_owner(self, client: AsyncClient) -> None:
        token_owner, _ = await _register_and_login(client)
        token_other, _ = await _register_and_login(client)
        restaurant_id = await _create_restaurant(client, token_owner)
        create_resp = await client.post(
            f"/api/v1/restaurants/{restaurant_id}/categories",
            json={"name": "Exclusiva"},
            headers={"Authorization": f"Bearer {token_owner}"},
        )
        category_id = create_resp.json()["id"]
        resp = await client.patch(
            f"/api/v1/categories/{category_id}",
            json={"name": "Hackeada"},
            headers={"Authorization": f"Bearer {token_other}"},
        )
        assert resp.status_code == 403


class TestDeleteCategory:
    async def test_delete_returns_204(self, client: AsyncClient) -> None:
        token, _ = await _register_and_login(client)
        restaurant_id = await _create_restaurant(client, token)
        create_resp = await client.post(
            f"/api/v1/restaurants/{restaurant_id}/categories",
            json={"name": "Para Borrar"},
            headers={"Authorization": f"Bearer {token}"},
        )
        category_id = create_resp.json()["id"]
        resp = await client.delete(
            f"/api/v1/categories/{category_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 204

    async def test_delete_returns_403_for_non_owner(self, client: AsyncClient) -> None:
        token_owner, _ = await _register_and_login(client)
        token_other, _ = await _register_and_login(client)
        restaurant_id = await _create_restaurant(client, token_owner)
        create_resp = await client.post(
            f"/api/v1/restaurants/{restaurant_id}/categories",
            json={"name": "Protegida"},
            headers={"Authorization": f"Bearer {token_owner}"},
        )
        category_id = create_resp.json()["id"]
        resp = await client.delete(
            f"/api/v1/categories/{category_id}",
            headers={"Authorization": f"Bearer {token_other}"},
        )
        assert resp.status_code == 403

    async def test_delete_nonexistent_returns_404(self, client: AsyncClient) -> None:
        token, _ = await _register_and_login(client)
        resp = await client.delete(
            f"/api/v1/categories/{uuid4()}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404
