"""Integration tests for /api/v1/auth/* endpoints.

Each test uses a unique email (uuid-prefixed) to avoid conflicts
between runs without requiring table truncation.
"""

from uuid import uuid4

from httpx import AsyncClient


def _email() -> str:
    return f"{uuid4().hex[:8]}@tablio.co"


class TestRegister:
    async def test_register_returns_201_and_tokens(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/api/v1/auth/register",
            json={"email": _email(), "password": "Secure123!", "full_name": "Test"},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert "access_token" in body
        assert "refresh_token" in body
        assert body["token_type"] == "bearer"

    async def test_register_duplicate_email_returns_409(
        self, client: AsyncClient
    ) -> None:
        email = _email()
        payload = {"email": email, "password": "Secure123!", "full_name": "Test"}
        await client.post("/api/v1/auth/register", json=payload)
        resp = await client.post("/api/v1/auth/register", json=payload)
        assert resp.status_code == 409

    async def test_register_short_password_returns_422(
        self, client: AsyncClient
    ) -> None:
        resp = await client.post(
            "/api/v1/auth/register",
            json={"email": _email(), "password": "short", "full_name": "Test"},
        )
        assert resp.status_code == 422


class TestLogin:
    async def test_login_returns_tokens(self, client: AsyncClient) -> None:
        email = _email()
        await client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": "Secure123!", "full_name": "User"},
        )
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "Secure123!"},
        )
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    async def test_login_wrong_password_returns_401(self, client: AsyncClient) -> None:
        email = _email()
        await client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": "Secure123!", "full_name": "User"},
        )
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "WrongPass!"},
        )
        assert resp.status_code == 401

    async def test_login_unknown_email_returns_401(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "nobody@tablio.co", "password": "whatever"},
        )
        assert resp.status_code == 401


class TestMe:
    async def test_me_returns_user_data(self, client: AsyncClient) -> None:
        email = _email()
        reg = await client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": "Secure123!", "full_name": "Full Name"},
        )
        token = reg.json()["access_token"]
        resp = await client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 200
        assert resp.json()["email"] == email

    async def test_me_without_token_returns_401(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/auth/me")
        assert resp.status_code == 401


class TestRefreshAndLogout:
    async def test_refresh_issues_new_access_token(self, client: AsyncClient) -> None:
        reg = await client.post(
            "/api/v1/auth/register",
            json={"email": _email(), "password": "Secure123!", "full_name": "User"},
        )
        refresh_token = reg.json()["refresh_token"]
        resp = await client.post(
            "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
        )
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    async def test_logout_clears_refresh_token(self, client: AsyncClient) -> None:
        reg = await client.post(
            "/api/v1/auth/register",
            json={"email": _email(), "password": "Secure123!", "full_name": "User"},
        )
        tokens = reg.json()
        access_token = tokens["access_token"]
        refresh_token = tokens["refresh_token"]

        await client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        resp = await client.post(
            "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
        )
        assert resp.status_code == 401
