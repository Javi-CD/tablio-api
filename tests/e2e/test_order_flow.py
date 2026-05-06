"""E2E test: full order lifecycle from public creation to admin completion."""

from uuid import uuid4

from httpx import AsyncClient


def _email() -> str:
    return f"{uuid4().hex[:8]}@tablio.co"


async def test_full_order_lifecycle(client: AsyncClient) -> None:
    # 1. Register and log in as restaurant owner
    email = _email()
    register_resp = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Secure123!", "full_name": "Chef"},
    )
    assert register_resp.status_code == 201
    token = register_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create restaurant
    restaurant_resp = await client.post(
        "/api/v1/restaurants",
        json={"name": f"E2E Resto {uuid4().hex[:6]}"},
        headers=headers,
    )
    assert restaurant_resp.status_code == 201
    restaurant = restaurant_resp.json()
    restaurant_id = restaurant["id"]
    slug = restaurant["slug"]

    # 3. Create a category and two products
    category_resp = await client.post(
        f"/api/v1/restaurants/{restaurant_id}/categories",
        json={"name": "Platos"},
        headers=headers,
    )
    assert category_resp.status_code == 201

    product1_resp = await client.post(
        f"/api/v1/restaurants/{restaurant_id}/products",
        json={"name": "Pizza Margarita", "price": "25000"},
        headers=headers,
    )
    assert product1_resp.status_code == 201
    product1_id = product1_resp.json()["id"]

    product2_resp = await client.post(
        f"/api/v1/restaurants/{restaurant_id}/products",
        json={"name": "Gaseosa", "price": "5000"},
        headers=headers,
    )
    assert product2_resp.status_code == 201
    product2_id = product2_resp.json()["id"]

    # 4. Customer places an order via public endpoint (no auth)
    order_resp = await client.post(
        f"/api/v1/public/restaurants/{slug}/orders",
        json={
            "customer_name": "María García",
            "customer_phone": "3001234567",
            "customer_notes": "Sin cebolla",
            "order_type": "table",
            "table_number": "7",
            "items": [
                {"product_id": product1_id, "quantity": 2},
                {"product_id": product2_id, "quantity": 1},
            ],
        },
    )
    assert order_resp.status_code == 201
    order = order_resp.json()
    order_id = order["id"]

    assert order["status"] == "pending"
    assert order["customer_name"] == "María García"
    assert order["table_number"] == "7"
    assert float(order["total_amount"]) == 55000.0  # 2*25000 + 1*5000
    assert len(order["items"]) == 2

    # 5. Admin lists orders and sees the new order
    list_resp = await client.get(
        f"/api/v1/restaurants/{restaurant_id}/orders",
        headers=headers,
    )
    assert list_resp.status_code == 200
    list_body = list_resp.json()
    assert list_body["total"] >= 1
    order_ids = [o["id"] for o in list_body["items"]]
    assert order_id in order_ids

    # 6. Admin fetches order detail
    detail_resp = await client.get(
        f"/api/v1/orders/{order_id}",
        headers=headers,
    )
    assert detail_resp.status_code == 200
    assert detail_resp.json()["id"] == order_id

    # 7. Admin accepts the order
    accept_resp = await client.patch(
        f"/api/v1/orders/{order_id}/status",
        json={"status": "accepted"},
        headers=headers,
    )
    assert accept_resp.status_code == 200
    assert accept_resp.json()["status"] == "accepted"

    # 8. Admin starts preparing
    prepare_resp = await client.patch(
        f"/api/v1/orders/{order_id}/status",
        json={"status": "preparing"},
        headers=headers,
    )
    assert prepare_resp.status_code == 200
    assert prepare_resp.json()["status"] == "preparing"

    # 9. Admin completes the order
    complete_resp = await client.patch(
        f"/api/v1/orders/{order_id}/status",
        json={"status": "completed"},
        headers=headers,
    )
    assert complete_resp.status_code == 200
    assert complete_resp.json()["status"] == "completed"

    # 10. No further transitions are allowed from completed
    invalid_resp = await client.patch(
        f"/api/v1/orders/{order_id}/status",
        json={"status": "cancelled"},
        headers=headers,
    )
    assert invalid_resp.status_code == 422

    # 11. Filter by status to confirm completed order shows up
    filter_resp = await client.get(
        f"/api/v1/restaurants/{restaurant_id}/orders?status=completed",
        headers=headers,
    )
    assert filter_resp.status_code == 200
    completed_ids = [o["id"] for o in filter_resp.json()["items"]]
    assert order_id in completed_ids
