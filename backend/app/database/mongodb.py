"""MongoDB connection lifecycle helpers for FlareX."""

import logging
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import PyMongoError

from app.config import DATABASE_NAME, MONGODB_URI


logger = logging.getLogger(__name__)

_mongo_client: Optional[AsyncIOMotorClient] = None
_database: Optional[AsyncIOMotorDatabase] = None


async def connect_to_mongo() -> None:
    """Create and verify the application's shared asynchronous MongoDB client.

    This function is intended for the FastAPI application's startup lifecycle.
    It pings MongoDB before exposing the client so startup fails clearly when the
    database is unavailable or misconfigured.

    Raises:
        RuntimeError: If MongoDB configuration is missing or the connection fails.
    """
    global _mongo_client, _database

    if _mongo_client is not None:
        return

    if not MONGODB_URI:
        logger.error("MongoDB connection was not configured.")
        raise RuntimeError("MONGODB_URI is not configured.")

    mongo_client: Optional[AsyncIOMotorClient] = None

    try:
        mongo_client = AsyncIOMotorClient(
            MONGODB_URI,
            serverSelectionTimeoutMS=5_000,
        )
        await mongo_client.admin.command("ping")
    except PyMongoError as error:
        logger.exception("Unable to connect to MongoDB.")
        if mongo_client is not None:
            mongo_client.close()
        raise RuntimeError("Unable to connect to MongoDB.") from error

    _mongo_client = mongo_client
    _database = mongo_client[DATABASE_NAME]
    logger.info("Connected to MongoDB database '%s'.", DATABASE_NAME)


async def close_mongo_connection() -> None:
    """Close the shared MongoDB client during the application shutdown lifecycle."""
    global _mongo_client, _database

    if _mongo_client is not None:
        _mongo_client.close()
        logger.info("Closed MongoDB connection.")

    _mongo_client = None
    _database = None


def get_database() -> AsyncIOMotorDatabase:
    """Return the initialized MongoDB database instance.

    Raises:
        RuntimeError: If the database lifecycle has not been initialized.
    """
    if _database is None:
        raise RuntimeError(
            "MongoDB has not been initialized. Call connect_to_mongo() first."
        )

    return _database
