import logging

from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import settings

logger = logging.getLogger(__name__)

_client: AsyncIOMotorClient | None = None


async def connect_to_mongo() -> None:
    """Create Motor client and initialise Beanie with all document models."""
    global _client

    # Import here to avoid circular deps; models must be registered centrally
    from app.modules.auth.models import User  # noqa: F401

    _client = AsyncIOMotorClient(settings.mongodb_url)
    db = _client[settings.mongodb_db_name]

    await init_beanie(database=db, document_models=[User])
    logger.info("Connected to MongoDB: %s / %s", settings.mongodb_url, settings.mongodb_db_name)


async def close_mongo_connection() -> None:
    global _client
    if _client is not None:
        _client.close()
        _client = None
        logger.info("MongoDB connection closed.")
