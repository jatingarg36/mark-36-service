from abc import ABC, abstractmethod


class OAuthProvider(ABC):
    """Abstract base class for OAuth 2.0 provider integrations.

    To add a new provider (e.g. GitHub, Microsoft, Apple):
    1. Create a new file under ``app/modules/auth/oauth/``.
    2. Subclass ``OAuthProvider`` and implement all three abstract methods.
    3. Register the new provider in the auth router — no changes to
       ``service.py`` or the base class are required.
    """

    @abstractmethod
    async def get_authorization_url(self) -> str:
        """Return the provider's OAuth authorisation URL to redirect the user to."""
        ...

    @abstractmethod
    async def exchange_code_for_token(self, code: str) -> dict:
        """Exchange an authorisation code for an access (and optionally refresh) token.

        Returns the raw token response as a dict.
        """
        ...

    @abstractmethod
    async def get_user_info(self, access_token: str) -> dict:
        """Fetch the authenticated user's profile from the provider.

        Returns a dict that must contain at minimum:
          - ``id``    (str) — provider-specific unique user identifier
          - ``email`` (str)
          - ``name``  (str)
        """
        ...
