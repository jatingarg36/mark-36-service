"""FastAPI application entry point for mark-36-service."""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import close_mongo_connection, connect_to_mongo
from app.core.redis import close_redis_connection, connect_to_redis
from app.modules.auth.router import auth_router, users_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="mark-36-service",
    version="0.1.0",
    description="Modular Python backend service — auth module",
)

# ---------------------------------------------------------------------------
# CORS (adjust origins before deploying behind NGINX)
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------

@app.on_event("startup")
async def startup() -> None:
    logger.info("Starting up mark-36-service …")
    await connect_to_mongo()
    await connect_to_redis()
    logger.info("mark-36-service is ready.")


@app.on_event("shutdown")
async def shutdown() -> None:
    logger.info("Shutting down mark-36-service …")
    await close_mongo_connection()
    await close_redis_connection()

# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/health", tags=["health"], summary="Health check")
async def health() -> dict:
    return {"status": "ok"}

# ---------------------------------------------------------------------------
# Routers
# To add a new module: import its router and call app.include_router() below.
# ---------------------------------------------------------------------------

app.include_router(auth_router, prefix="/auth")
app.include_router(users_router, prefix="/users")
