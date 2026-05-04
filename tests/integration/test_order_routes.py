"""Integration tests for order endpoints."""

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


async def _create_restaurant(client: AsyncClient, token: str) -> dict[str, str]:
    resp = await client.post(
        "/api/v1/restaurants",
        json={"name": f"Resto {uuid4().hex[:6]}"},
        headers={"Authorization": f"Bearer {token}"},
    )
    return resp.json()


async def _create_product(
    client: AsyncClient,
    token: str,
    restaurant_id: str,
    name: str = "Hamburguesa",
    price: str = "18000",
) -> dict[str, str]:
    resp = await client.post(
        f"/api/v1/restaurants/{restaurant_id}/products",
        json={"name": name, "price": price},
        headers={"Authorization": f"Bearer {token}"},
    )
    return resp.json()


class TestCreateOrder:
    async def test_create_returns_201(self, client: AsyncClient) -> None:
        token, _ = await _register_and_login(client)
        restaurant = await _create_restaurant(client, token)
        product = await _create_product(client, token, restaurant["id"])

        resp = await client.post(
            f"/api/v1/public/restaurants/{restaurant['slug']}/orders",
            json={
                "customer_name": "Juan Pérez",
                "order_type": "table",
                "table_number": "5",
                "items": [{"product_id": product["id"], "quantity": 2}],
            },
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["customer_name"] == "Juan Pérez"
        assert body["status"] == "pending"
        assert float(body["total_amount"]) == 36000.0
        assert len(body["items"]) == 1
        item = body["items"][0]
        assert item["product_name"] == "Hamburguesa"
        assert float(item["unit_price"]) == 18000.0
        assert item["quantity"] == 2
        assert float(item["subtotal"]) == 36000.0

    async def test_create_calculates_total_server_side(
        self, client: AsyncClient
    ) -> None:
        token, _ = await _register_and_login(client)
        restaurant = await _create_restaurant(client, token)
        p1 = await _create_product(client, token, restaurant["id"], "A", "10000")
        p2 = await _create_product(client, token, restaurant["id"], "B", "5000")

        resp = await client.post(
            f"/api/v1/public/restaurants/{restaurant['slug']}/orders",
            json={
                "customer_name": "Cliente",
                "order_type": "pickup",
                "items": [
                    {"product_id": p1["id"], "quantity": 3},
                    {"product_id": p2["id"], "quantity": 2},
                ],
            },
        )
        assert resp.status_code == 201
        assert float(resp.json()["total_amount"]) == 40000.0

    async def test_create_with_unknown_restaurant_returns_404(
        self, client: AsyncClient
    ) -> None:
        resp = await client.post(
            "/api/v1/public/restaurants/non-existent-slug/orders",
            json={
                "customer_name": "Test",
                "order_type": "table",
                "items": [{"product_id": str(uuid4()), "quantity": 1}],
            },
        )
        assert resp.status_code == 404

    async def test_create_with_unknown_product_returns_404(
        self, client: AsyncClient
    ) -> None:
        token, _ = await _register_and_login(client)
        restaurant = await _create_restaurant(client, token)

        resp = await client.post(
            f"/api/v1/public/restaurants/{restaurant['slug']}/orders",
            json={
                "customer_name": "Test",
                "order_type": "table",
                "items": [{"product_id": str(uuid4()), "quantity": 1}],
            },
        )
        assert resp.status_code == 404

    async def test_create_rejects_product_from_other_restaurant(
        self, client: AsyncClient
    ) -> None:
        token1, _ = await _register_and_login(client)
        token2, _ = await _register_and_login(client)
        restaurant1 = await _create_restaurant(client, token1)
        restaurant2 = await _create_restaurant(client, token2)
        product_of_r2 = await _create_product(client, token2, restaurant2["id"])

        resp = await client.post(
            f"/api/v1/public/restaurants/{restaurant1['slug']}/orders",
            json={
                "customer_name": "Test",
                "order_type": "table",
                "items": [{"product_id": product_of_r2["id"], "quantity": 1}],
            },
        )
        assert resp.status_code == 403

    async def test_create_requires_at_least_one_item(self, client: AsyncClient) -> None:
        token, _ = await _register_and_login(client)
        restaurant = await _create_restaurant(client, token)

        resp = await client.post(
            f"/api/v1/public/restaurants/{restaurant['slug']}/orders",
            json={"customer_name": "Test", "order_type": "table", "items": []},
        )
        assert resp.status_code == 422

    async def test_snapshots_product_name_and_price(self, client: AsyncClient) -> None:
        token, _ = await _register_and_login(client)
        restaurant = await _create_restaurant(client, token)
        product = await _create_product(
            client, token, restaurant["id"], "Original", "20000"
        )

        order_resp = await client.post(
            f"/api/v1/public/restaurants/{restaurant['slug']}/orders",
            json={
                "customer_name": "Test",
                "order_type": "table",
                "items": [{"product_id": product["id"], "quantity": 1}],
            },
        )
        assert order_resp.status_code == 201

        # Rename + reprice the product
        await client.patch(
            f"/api/v1/products/{product['id']}",
            json={"name": "Nuevo Nombre", "price": "99000"},
            headers={"Authorization": f"Bearer {token}"},
        )

        # Snapshot in the order should be unchanged
        item = order_resp.json()["items"][0]
        assert item["product_name"] == "Original"
        assert float(item["unit_price"]) == 20000.0


class TestListOrders:
    async def test_list_returns_paginated(self, client: AsyncClient) -> None:
        token, _ = await _register_and_login(client)
        restaurant = await _create_restaurant(client, token)
        product = await _create_product(client, token, restaurant["id"])

        for _ in range(3):
            await client.post(
                f"/api/v1/public/restaurants/{restaurant['slug']}/orders",
                json={
                    "customer_name": "Cliente",
                    "order_type": "table",
                    "items": [{"product_id": product["id"], "quantity": 1}],
                },
            )

        resp = await client.get(
            f"/api/v1/restaurants/{restaurant['id']}/orders",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] >= 3
        assert "items" in body
        assert body["page"] == 1

    async def test_list_filter_by_status(self, client: AsyncClient) -> None:
        token, _ = await _register_and_login(client)
        restaurant = await _create_restaurant(client, token)
        product = await _create_product(client, token, restaurant["id"])

        order_resp = await client.post(
            f"/api/v1/public/restaurants/{restaurant['slug']}/orders",
            json={
                "customer_name": "Test",
                "order_type": "table",
                "items": [{"product_id": product["id"], "quantity": 1}],
            },
        )
        order_id = order_resp.json()["id"]

        await client.patch(
            f"/api/v1/orders/{order_id}/status",
            json={"status": "accepted"},
            headers={"Authorization": f"Bearer {token}"},
        )

        resp = await client.get(
            f"/api/v1/restaurants/{restaurant['id']}/orders?status=accepted",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert all(o["status"] == "accepted" for o in resp.json()["items"])

    async def test_list_requires_auth(self, client: AsyncClient) -> None:
        resp = await client.get(f"/api/v1/restaurants/{uuid4()}/orders")
        assert resp.status_code == 401

    async def test_list_returns_403_for_non_owner(self, client: AsyncClient) -> None:
        token_owner, _ = await _register_and_login(client)
        token_other, _ = await _register_and_login(client)
        restaurant = await _create_restaurant(client, token_owner)

        resp = await client.get(
            f"/api/v1/restaurants/{restaurant['id']}/orders",
            headers={"Authorization": f"Bearer {token_other}"},
        )
        assert resp.status_code == 403


class TestGetOrder:
    async def test_get_returns_order(self, client: AsyncClient) -> None:
        token, _ = await _register_and_login(client)
        restaurant = await _create_restaurant(client, token)
        product = await _create_product(client, token, restaurant["id"])

        create_resp = await client.post(
            f"/api/v1/public/restaurants/{restaurant['slug']}/orders",
            json={
                "customer_name": "Juan",
                "order_type": "delivery",
                "items": [{"product_id": product["id"], "quantity": 1}],
            },
        )
        order_id = create_resp.json()["id"]

        resp = await client.get(
            f"/api/v1/orders/{order_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == order_id

    async def test_get_nonexistent_returns_404(self, client: AsyncClient) -> None:
        token, _ = await _register_and_login(client)
        resp = await client.get(
            f"/api/v1/orders/{uuid4()}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404


class TestUpdateOrderStatus:
    async def test_valid_transition_pending_to_accepted(
        self, client: AsyncClient
    ) -> None:
        token, _ = await _register_and_login(client)
        restaurant = await _create_restaurant(client, token)
        product = await _create_product(client, token, restaurant["id"])

        order_resp = await client.post(
            f"/api/v1/public/restaurants/{restaurant['slug']}/orders",
            json={
                "customer_name": "Test",
                "order_type": "table",
                "items": [{"product_id": product["id"], "quantity": 1}],
            },
        )
        order_id = order_resp.json()["id"]

        resp = await client.patch(
            f"/api/v1/orders/{order_id}/status",
            json={"status": "accepted"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "accepted"

    async def test_full_happy_path_transition(self, client: AsyncClient) -> None:
        token, _ = await _register_and_login(client)
        restaurant = await _create_restaurant(client, token)
        product = await _create_product(client, token, restaurant["id"])

        order_resp = await client.post(
            f"/api/v1/public/restaurants/{restaurant['slug']}/orders",
            json={
                "customer_name": "Test",
                "order_type": "table",
                "items": [{"product_id": product["id"], "quantity": 1}],
            },
        )
        order_id = order_resp.json()["id"]
        headers = {"Authorization": f"Bearer {token}"}

        for transition in ("accepted", "preparing", "completed"):
            resp = await client.patch(
                f"/api/v1/orders/{order_id}/status",
                json={"status": transition},
                headers=headers,
            )
            assert resp.status_code == 200
            assert resp.json()["status"] == transition

    async def test_invalid_transition_returns_422(self, client: AsyncClient) -> None:
        token, _ = await _register_and_login(client)
        restaurant = await _create_restaurant(client, token)
        product = await _create_product(client, token, restaurant["id"])

        order_resp = await client.post(
            f"/api/v1/public/restaurants/{restaurant['slug']}/orders",
            json={
                "customer_name": "Test",
                "order_type": "table",
                "items": [{"product_id": product["id"], "quantity": 1}],
            },
        )
        order_id = order_resp.json()["id"]

        resp = await client.patch(
            f"/api/v1/orders/{order_id}/status",
            json={"status": "completed"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422

    async def test_cancel_from_pending(self, client: AsyncClient) -> None:
        token, _ = await _register_and_login(client)
        restaurant = await _create_restaurant(client, token)
        product = await _create_product(client, token, restaurant["id"])

        order_resp = await client.post(
            f"/api/v1/public/restaurants/{restaurant['slug']}/orders",
            json={
                "customer_name": "Test",
                "order_type": "table",
                "items": [{"product_id": product["id"], "quantity": 1}],
            },
        )
        order_id = order_resp.json()["id"]

        resp = await client.patch(
            f"/api/v1/orders/{order_id}/status",
            json={"status": "cancelled"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "cancelled"

    async def test_update_requires_auth(self, client: AsyncClient) -> None:
        resp = await client.patch(
            f"/api/v1/orders/{uuid4()}/status",
            json={"status": "accepted"},
        )
        assert resp.status_code == 401
