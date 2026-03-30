"""Tests for auth service layer."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest

from app.modules.auth.models import OAuthAccount, User
from app.modules.auth.service import (
    _issue_tokens,
    _upsert_user,
    handle_oauth_callback,
    refresh_tokens,
    revoke_refresh_token,
)


def _make_user(email: str = "test@example.com") -> User:
    return User(
        id=uuid4(),
        email=email,
        name="Test User",
        oauth_accounts=[],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


# ---------------------------------------------------------------------------
# _upsert_user
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_upsert_user_creates_new_user() -> None:
    with (
        patch("app.modules.auth.service.User.find_one", new_callable=AsyncMock, return_value=None),
        patch("app.modules.auth.service.User.insert", new_callable=AsyncMock) as mock_insert,
    ):
        user = _make_user()
        mock_insert.return_value = None

        # Patch User constructor to return our mock user
        with patch("app.modules.auth.service.User", return_value=user) as MockUser:
            MockUser.find_one = AsyncMock(return_value=None)
            result = await _upsert_user(
                email="new@example.com",
                name="New User",
                avatar_url=None,
                provider="google",
                provider_user_id="google-123",
            )
        # Result should be a User-like object
        assert result is not None


@pytest.mark.asyncio
async def test_upsert_user_links_new_provider() -> None:
    existing = _make_user()
    existing.oauth_accounts = []

    with (
        patch("app.modules.auth.service.User.find_one", new_callable=AsyncMock, return_value=existing),
        patch.object(existing, "save", new_callable=AsyncMock),
    ):
        result = await _upsert_user(
            email=existing.email,
            name=existing.name,
            avatar_url=None,
            provider="google",
            provider_user_id="g-999",
        )
    assert any(a.provider == "google" for a in result.oauth_accounts)


@pytest.mark.asyncio
async def test_upsert_user_skips_duplicate_provider_link() -> None:
    existing = _make_user()
    existing.oauth_accounts = [
        OAuthAccount(provider="google", provider_user_id="g-999", linked_at=datetime.utcnow())
    ]

    with (
        patch("app.modules.auth.service.User.find_one", new_callable=AsyncMock, return_value=existing),
        patch.object(existing, "save", new_callable=AsyncMock),
    ):
        result = await _upsert_user(
            email=existing.email,
            name=existing.name,
            avatar_url=None,
            provider="google",
            provider_user_id="g-999",
        )
    # Still only one google account
    google_accounts = [a for a in result.oauth_accounts if a.provider == "google"]
    assert len(google_accounts) == 1


# ---------------------------------------------------------------------------
# refresh_tokens
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_refresh_tokens_raises_on_invalid_token() -> None:
    from fastapi import HTTPException

    with patch("app.modules.auth.service.get_refresh_token_user", new_callable=AsyncMock, return_value=None):
        with pytest.raises(HTTPException) as exc_info:
            await refresh_tokens("bad-token")
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_refresh_tokens_rotates_token() -> None:
    user = _make_user()
    user_id = str(user.id)
    old_rt = str(uuid4())

    with (
        patch("app.modules.auth.service.get_refresh_token_user", new_callable=AsyncMock, return_value=user_id),
        patch("app.modules.auth.service.User.get", new_callable=AsyncMock, return_value=user),
        patch("app.modules.auth.service.delete_refresh_token", new_callable=AsyncMock) as mock_delete,
        patch("app.modules.auth.service.store_refresh_token", new_callable=AsyncMock),
        patch("app.modules.auth.service.create_access_token", return_value="new.access.token"),
    ):
        result = await refresh_tokens(old_rt)

    mock_delete.assert_called_once_with(old_rt)
    assert result.access_token == "new.access.token"
    assert result.refresh_token != old_rt


# ---------------------------------------------------------------------------
# revoke_refresh_token
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_revoke_refresh_token() -> None:
    token = str(uuid4())
    with patch("app.modules.auth.service.delete_refresh_token", new_callable=AsyncMock) as mock_del:
        await revoke_refresh_token(token)
    mock_del.assert_called_once_with(token)
