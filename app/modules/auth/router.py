"""Auth and User routers.

Auth routes  → prefix /auth  (mounted by main.py)
Users routes → prefix /users (mounted by main.py)
"""

from datetime import datetime
from urllib.parse import urlencode

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import RedirectResponse

from app.core.config import settings
from app.core.dependencies import CurrentUser
from app.modules.auth.oauth.google import GoogleOAuthProvider
from app.modules.auth.schemas import (
    LogoutRequest,
    RefreshRequest,
    TokenResponse,
    UserResponse,
    UserUpdateRequest,
)
from app.modules.auth.service import (
    handle_oauth_callback,
    refresh_tokens,
    revoke_refresh_token,
)

# ---------------------------------------------------------------------------
# Auth router  —  /auth/…
# ---------------------------------------------------------------------------
auth_router = APIRouter(tags=["auth"])


@auth_router.get("/google/login", summary="Get Google OAuth authorization URL")
async def google_login() -> dict:
    provider = GoogleOAuthProvider()
    url = await provider.get_authorization_url()
    return {"authorization_url": url}


@auth_router.get(
    "/google/callback",
    summary="Handle Google OAuth callback — redirects to frontend with tokens",
)
async def google_callback(code: str = Query(..., description="Authorization code from Google")) -> RedirectResponse:
    provider = GoogleOAuthProvider()
    try:
        token_response: TokenResponse = await handle_oauth_callback(provider, code)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth callback failed: {exc}",
        ) from exc

    # Redirect to the frontend with tokens as query params.
    # The frontend reads, stores, and immediately strips these from the URL bar.
    params = urlencode({
        "access_token": token_response.access_token,
        "refresh_token": token_response.refresh_token,
    })
    redirect_url = f"{settings.frontend_redirect_uri}?{params}"
    return RedirectResponse(url=redirect_url, status_code=status.HTTP_302_FOUND)



@auth_router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Rotate refresh token and issue new access token",
)
async def refresh(body: RefreshRequest) -> TokenResponse:
    return await refresh_tokens(body.refresh_token)


@auth_router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Invalidate refresh token",
)
async def logout(body: LogoutRequest) -> None:
    await revoke_refresh_token(body.refresh_token)


# ---------------------------------------------------------------------------
# Users router  —  /users/…
# ---------------------------------------------------------------------------
users_router = APIRouter(tags=["users"])


@users_router.get(
    "/me",
    response_model=UserResponse,
    summary="Get authenticated user's profile",
)
async def get_me(current_user: CurrentUser) -> UserResponse:
    return UserResponse.model_validate(current_user)


@users_router.patch(
    "/me",
    response_model=UserResponse,
    summary="Update authenticated user's profile",
)
async def update_me(body: UserUpdateRequest, current_user: CurrentUser) -> UserResponse:
    if body.name is not None:
        current_user.name = body.name
    if body.avatar_url is not None:
        current_user.avatar_url = body.avatar_url
    current_user.updated_at = datetime.utcnow()
    await current_user.save()
    return UserResponse.model_validate(current_user)
