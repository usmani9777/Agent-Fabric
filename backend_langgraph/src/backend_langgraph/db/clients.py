from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from redis.asyncio import Redis

from backend_langgraph.core.config import get_settings

_mongo_client: AsyncIOMotorClient[Any] | None = None
_redis_client: Redis | None = None


def get_mongo_client() -> AsyncIOMotorClient[Any]:
    global _mongo_client
    if _mongo_client is None:
        settings = get_settings()
        _mongo_client = AsyncIOMotorClient(settings.mongo_uri, uuidRepresentation="standard")
    return _mongo_client


def get_database() -> AsyncIOMotorDatabase[Any]:
    settings = get_settings()
    return get_mongo_client()[settings.mongo_database]


def get_redis_client() -> Redis:
    global _redis_client
    if _redis_client is None:
        settings = get_settings()
        _redis_client = Redis.from_url(settings.redis_url, decode_responses=True)
    return _redis_client


@asynccontextmanager
async def lifespan_clients() -> AsyncIterator[None]:
    get_mongo_client()
    get_redis_client()
    yield

    global _mongo_client, _redis_client
    if _mongo_client is not None:
        _mongo_client.close()
        _mongo_client = None
    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = None


async def reset_clients() -> None:
    global _mongo_client, _redis_client
    if _mongo_client is not None:
        _mongo_client.close()
        _mongo_client = None
    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = None
