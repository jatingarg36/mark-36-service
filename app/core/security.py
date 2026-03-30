from datetime import datetime, timezone
from uuid import UUID

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

ALGORITHM = "HS256"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(user_id: UUID, email: str) -> str:
    """Create a signed JWT access token."""
    now = datetime.now(timezone.utc)
    expire = now.timestamp() + settings.access_token_expire_minutes * 60
    payload = {
        "sub": str(user_id),
        "email": email,
        "exp": int(expire),
        "iat": int(now.timestamp()),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Decode and validate a JWT access token.

    Raises:
        JWTError: if the token is invalid or expired.
    """
    return jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)
