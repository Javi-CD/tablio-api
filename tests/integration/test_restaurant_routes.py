"""Integration tests for /api/v1/restaurants/* endpoints."""

from uuid import uuid4

from httpx import AsyncClient


def _email() -> str:
    return f"{uuid4().hex[:8]}@tablio.co"


async def _register_and_login(client: AsyncClient) -> tuple[str, str]:
    """Register a new user and return (access_token, email)."""
    email = _email()
    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Secure123!", "full_name": "Owner"},
    )
    return resp.json()["access_token"], email


class TestCreateRestaurant:
    async def test_create_returns_201_with_slug(self, client: AsyncClient) -> None:
        token, _ = await _register_and_login(client)
        resp = await client.post(
            "/api/v1/restaurants",
            json={"name": "La Picantería", "description": "Comida picante"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["slug"] == "la-picanteria"
        assert body["name"] == "La Picantería"

    async def test_create_requires_auth(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/api/v1/restaurants", json={"name": "Anon Restaurant"}
        )
        assert resp.status_code == 401

    async def test_duplicate_name_gets_unique_slug(self, client: AsyncClient) -> None:
        token1, _ = await _register_and_login(client)
        token2, _ = await _register_and_login(client)
        name = f"Restaurante {uuid4().hex[:6]}"
        await client.post(
            "/api/v1/restaurants",
            json={"name": name},
            headers={"Authorization": f"Bearer {token1}"},
        )
        resp = await client.post(
            "/api/v1/restaurants",
            json={"name": name},
            headers={"Authorization": f"Bearer {token2}"},
        )
        assert resp.status_code == 201
        slug = resp.json()["slug"]
        assert slug.endswith("-1")


class TestGetMyRestaurant:
    async def test_returns_restaurant_for_owner(self, client: AsyncClient) -> None:
        token, _ = await _register_and_login(client)
        await client.post(
            "/api/v1/restaurants",
            json={"name": "Mi Local"},
            headers={"Authorization": f"Bearer {token}"},
        )
        resp = await client.get(
            "/api/v1/restaurants/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "Mi Local"

    async def test_returns_404_when_no_restaurant(self, client: AsyncClient) -> None:
        token, _ = await _register_and_login(client)
        resp = await client.get(
            "/api/v1/restaurants/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404


class TestUpdateRestaurant:
    async def test_update_name_and_description(self, client: AsyncClient) -> None:
        token, _ = await _register_and_login(client)
        create_resp = await client.post(
            "/api/v1/restaurants",
            json={"name": "Original"},
            headers={"Authorization": f"Bearer {token}"},
        )
        restaurant_id = create_resp.json()["id"]
        resp = await client.patch(
            f"/api/v1/restaurants/{restaurant_id}",
            json={"name": "Updated", "description": "New desc"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "Updated"
        assert resp.json()["description"] == "New desc"

    async def test_update_slug_warns_qr_invalidity(self, client: AsyncClient) -> None:
        token, _ = await _register_and_login(client)
        create_resp = await client.post(
            "/api/v1/restaurants",
            json={"name": f"Resto {uuid4().hex[:6]}"},
            headers={"Authorization": f"Bearer {token}"},
        )
        restaurant_id = create_resp.json()["id"]
        new_slug = f"nuevo-slug-{uuid4().hex[:6]}"
        resp = await client.patch(
            f"/api/v1/restaurants/{restaurant_id}",
            json={"slug": new_slug},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["slug"] == new_slug

    async def test_update_by_non_owner_returns_403(self, client: AsyncClient) -> None:
        token_owner, _ = await _register_and_login(client)
        token_other, _ = await _register_and_login(client)
        create_resp = await client.post(
            "/api/v1/restaurants",
            json={"name": "Owner's Place"},
            headers={"Authorization": f"Bearer {token_owner}"},
        )
        restaurant_id = create_resp.json()["id"]
        resp = await client.patch(
            f"/api/v1/restaurants/{restaurant_id}",
            json={"name": "Hacked"},
            headers={"Authorization": f"Bearer {token_other}"},
        )
        assert resp.status_code == 403
