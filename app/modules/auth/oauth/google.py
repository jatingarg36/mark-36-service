import httpx

from app.core.config import settings
from app.modules.auth.oauth.base import OAuthProvider

_GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
_GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
_GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"

_SCOPES = "openid email profile"


class GoogleOAuthProvider(OAuthProvider):
    """Google OAuth 2.0 implementation using the standard authorization-code flow."""

    async def get_authorization_url(self) -> str:
        params = {
            "client_id": settings.google_client_id,
            "redirect_uri": settings.google_redirect_uri,
            "response_type": "code",
            "scope": _SCOPES,
            "access_type": "offline",
            "prompt": "consent",
        }
        query = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{_GOOGLE_AUTH_URL}?{query}"

    async def exchange_code_for_token(self, code: str) -> dict:
        payload = {
            "code": code,
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "redirect_uri": settings.google_redirect_uri,
            "grant_type": "authorization_code",
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(_GOOGLE_TOKEN_URL, data=payload)
            resp.raise_for_status()
            return resp.json()

    async def get_user_info(self, access_token: str) -> dict:
        headers = {"Authorization": f"Bearer {access_token}"}
        async with httpx.AsyncClient() as client:
            resp = await client.get(_GOOGLE_USERINFO_URL, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        # Normalise to a canonical shape consumed by service.py
        return {
            "id": data["sub"],
            "email": data["email"],
            "name": data.get("name", data.get("email", "")),
            "avatar_url": data.get("picture"),
        }
