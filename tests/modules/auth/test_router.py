"""Tests for auth router endpoints."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.modules.auth.schemas import TokenResponse


@pytest.fixture
def mock_tokens() -> TokenResponse:
    return TokenResponse(
        access_token="test.access.token",
        refresh_token=str(uuid4()),
    )


@pytest.mark.asyncio
async def test_health_check() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_google_login_returns_authorization_url() -> None:
    with patch(
        "app.modules.auth.router.GoogleOAuthProvider.get_authorization_url",
        new_callable=AsyncMock,
        return_value="https://accounts.google.com/o/oauth2/v2/auth?client_id=test",
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/auth/google/login")
    assert resp.status_code == 200
    data = resp.json()
    assert "authorization_url" in data
    assert "accounts.google.com" in data["authorization_url"]


@pytest.mark.asyncio
async def test_google_callback_success(mock_tokens: TokenResponse) -> None:
    with patch(
        "app.modules.auth.router.handle_oauth_callback",
        new_callable=AsyncMock,
        return_value=mock_tokens,
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/auth/google/callback", params={"code": "test-code"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["access_token"] == "test.access.token"
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_google_callback_failure() -> None:
    with patch(
        "app.modules.auth.router.handle_oauth_callback",
        new_callable=AsyncMock,
        side_effect=Exception("provider error"),
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/auth/google/callback", params={"code": "bad-code"})
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_refresh_token(mock_tokens: TokenResponse) -> None:
    with patch(
        "app.modules.auth.router.refresh_tokens",
        new_callable=AsyncMock,
        return_value=mock_tokens,
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/auth/refresh",
                json={"refresh_token": str(uuid4())},
            )
    assert resp.status_code == 200
    assert "access_token" in resp.json()


@pytest.mark.asyncio
async def test_logout() -> None:
    with patch(
        "app.modules.auth.router.revoke_refresh_token",
        new_callable=AsyncMock,
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/auth/logout",
                json={"refresh_token": str(uuid4())},
            )
    assert resp.status_code == 204
