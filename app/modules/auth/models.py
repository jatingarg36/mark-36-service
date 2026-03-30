from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

from beanie import Document, Indexed
from pydantic import BaseModel, Field


class OAuthAccount(BaseModel):
    provider: str
    provider_user_id: str
    linked_at: datetime = Field(default_factory=datetime.utcnow)


class User(Document):
    id: UUID = Field(default_factory=uuid4)  # type: ignore[assignment]
    email: Indexed(str, unique=True)  # type: ignore[valid-type]
    name: str
    avatar_url: Optional[str] = None
    oauth_accounts: List[OAuthAccount] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "users"
        indexes = [
            [("email", 1)],
            [("oauth_accounts.provider", 1), ("oauth_accounts.provider_user_id", 1)],
        ]
