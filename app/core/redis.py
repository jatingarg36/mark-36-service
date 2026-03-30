import logging

import redis.asyncio as aioredis

from app.core.config import settings

logger = logging.getLogger(__name__)

_redis: aioredis.Redis | None = None

REFRESH_TOKEN_PREFIX = "refresh_token:"


def _key(token: str) -> str:
    return f"{REFRESH_TOKEN_PREFIX}{token}"


async def connect_to_redis() -> None:
    global _redis
    _redis = aioredis.from_url(settings.redis_url, decode_responses=True)
    await _redis.ping()
    logger.info("Connected to Redis: %s", settings.redis_url)


async def close_redis_connection() -> None:
    global _redis
    if _redis is not None:
        await _redis.aclose()
        _redis = None
        logger.info("Redis connection closed.")


def get_redis() -> aioredis.Redis:
    if _redis is None:
        raise RuntimeError("Redis is not connected. Call connect_to_redis() first.")
    return _redis


# ---------------------------------------------------------------------------
# Refresh-token helpers
# ---------------------------------------------------------------------------

async def store_refresh_token(token: str, user_id: str, ttl_seconds: int) -> None:
    """Persist a refresh token with TTL."""
    await get_redis().setex(_key(token), ttl_seconds, user_id)


async def get_refresh_token_user(token: str) -> str | None:
    """Return the user_id bound to a refresh token, or None if absent/expired."""
    return await get_redis().get(_key(token))


async def delete_refresh_token(token: str) -> None:
    """Revoke a refresh token (logout or rotation)."""
    await get_redis().delete(_key(token))
