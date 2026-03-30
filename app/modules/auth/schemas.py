from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, field_validator


# ---------------------------------------------------------------------------
# Auth responses
# ---------------------------------------------------------------------------

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


# ---------------------------------------------------------------------------
# User responses
# ---------------------------------------------------------------------------

class OAuthAccountSchema(BaseModel):
    provider: str
    provider_user_id: str
    linked_at: datetime

    model_config = {"from_attributes": True}


class UserResponse(BaseModel):
    id: UUID
    email: str
    name: str
    avatar_url: Optional[str] = None
    oauth_accounts: list[OAuthAccountSchema] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# User update
# ---------------------------------------------------------------------------

class UserUpdateRequest(BaseModel):
    name: Optional[str] = None
    avatar_url: Optional[str] = None

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("name must not be blank")
        return v
