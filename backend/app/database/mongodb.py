"""Asynchronous MongoDB connection management."""

from __future__ import annotations

import logging

from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase

from app.config import get_settings

logger = logging.getLogger(__name__)

_client: AsyncMongoClient | None = None


async def connect_db() -> AsyncMongoClient:
    """Create the shared client and verify connectivity."""
    global _client
    settings = get_settings()
    if _client is None:
        _client = AsyncMongoClient(settings.mongo_uri, serverSelectionTimeoutMS=5000)
    await _client.admin.command("ping")
    logger.info("Connected to MongoDB database '%s'", settings.mongo_db_name)
    return _client


async def close_db() -> None:
    """Close the shared client if it is open."""
    global _client
    if _client is not None:
        await _client.close()
        _client = None
        logger.info("MongoDB connection closed")


def get_client() -> AsyncMongoClient:
    """Return the shared client, creating it lazily."""
    global _client
    if _client is None:
        settings = get_settings()
        _client = AsyncMongoClient(settings.mongo_uri, serverSelectionTimeoutMS=5000)
    return _client


def get_database() -> AsyncDatabase:
    """Return the configured e_sewasathi database."""
    settings = get_settings()
    return get_client()[settings.mongo_db_name]
