"""Auth business logic.

Responsibilities:
- OAuth callback handling (upsert user, link provider account)
- JWT access token issuance
- Refresh token lifecycle: issue, rotate, revoke
"""

import logging
from datetime import datetime
from uuid import uuid4

from fastapi import HTTPException, status

from app.core.config import settings
from app.core.redis import (
    delete_refresh_token,
    get_refresh_token_user,
    store_refresh_token,
)
from app.core.security import create_access_token
from app.modules.auth.models import OAuthAccount, User
from app.modules.auth.oauth.base import OAuthProvider
from app.modules.auth.schemas import TokenResponse

logger = logging.getLogger(__name__)


async def handle_oauth_callback(provider: OAuthProvider, code: str) -> TokenResponse:
    """Exchange the OAuth code for user info, upsert the user, and return tokens."""
    # 1. Exchange code for provider access token
    token_data = await provider.exchange_code_for_token(code)
    provider_access_token: str = token_data["access_token"]

    # 2. Fetch user profile from provider
    user_info = await provider.get_user_info(provider_access_token)
    provider_name: str = _resolve_provider_name(provider)
    provider_user_id: str = user_info["id"]

    # 3. Upsert user document
    user = await _upsert_user(
        email=user_info["email"],
        name=user_info["name"],
        avatar_url=user_info.get("avatar_url"),
        provider=provider_name,
        provider_user_id=provider_user_id,
    )

    # 4. Issue tokens
    return await _issue_tokens(user)


async def refresh_tokens(refresh_token: str) -> TokenResponse:
    """Rotate refresh token and issue a new access token."""
    user_id = await get_refresh_token_user(refresh_token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    user = await User.get(user_id)  # type: ignore[arg-type]
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    # Rotate: revoke old, issue new
    await delete_refresh_token(refresh_token)
    return await _issue_tokens(user)


async def revoke_refresh_token(refresh_token: str) -> None:
    """Logout — invalidate the refresh token in Redis."""
    await delete_refresh_token(refresh_token)


# ---------------------------------------------------------------------------
# Internals
# ---------------------------------------------------------------------------

async def _upsert_user(
    *,
    email: str,
    name: str,
    avatar_url: str | None,
    provider: str,
    provider_user_id: str,
) -> User:
    """Find or create a user by email, then link the OAuth account if not already present."""
    existing = await User.find_one(User.email == email)

    if existing is None:
        # First login — create user
        oauth_account = OAuthAccount(
            provider=provider,
            provider_user_id=provider_user_id,
        )
        user = User(
            email=email,
            name=name,
            avatar_url=avatar_url,
            oauth_accounts=[oauth_account],
        )
        await user.insert()
        logger.info("Created new user %s via %s", user.id, provider)
    else:
        user = existing
        # Link provider account if not already linked
        already_linked = any(
            a.provider == provider and a.provider_user_id == provider_user_id
            for a in user.oauth_accounts
        )
        if not already_linked:
            user.oauth_accounts.append(
                OAuthAccount(provider=provider, provider_user_id=provider_user_id)
            )
        user.updated_at = datetime.utcnow()
        await user.save()
        logger.info("Returning user %s logged in via %s", user.id, provider)

    return user


async def _issue_tokens(user: User) -> TokenResponse:
    access_token = create_access_token(user.id, user.email)
    refresh_token = str(uuid4())
    await store_refresh_token(
        refresh_token,
        str(user.id),
        settings.refresh_token_expire_seconds,
    )
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


def _resolve_provider_name(provider: OAuthProvider) -> str:
    """Derive a short provider identifier from the class name (e.g. 'Google')."""
    return type(provider).__name__.replace("OAuthProvider", "").lower()
