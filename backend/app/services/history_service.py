"""Read paginated historical forecast records from MongoDB."""

import logging
from collections.abc import Callable
from typing import Any

from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo.errors import PyMongoError

from app.database.collections import (
    get_three_day_history_collection,
    get_twenty_seven_day_history_collection,
)


logger = logging.getLogger(__name__)

HistoryRecord = dict[str, Any]


async def get_three_day_history(
    skip: int = 0,
    limit: int = 50,
) -> list[HistoryRecord]:
    """Return a paginated list of three-day historical forecast records.

    Database failures are logged and result in an empty list.
    """
    return await _get_history_records(
        get_three_day_history_collection,
        skip,
        limit,
    )


async def get_twenty_seven_day_history(
    skip: int = 0,
    limit: int = 50,
) -> list[HistoryRecord]:
    """Return a paginated list of twenty-seven-day historical forecast records.

    Database failures are logged and result in an empty list.
    """
    return await _get_history_records(
        get_twenty_seven_day_history_collection,
        skip,
        limit,
    )


async def _get_history_records(
    get_collection: Callable[[], AsyncIOMotorCollection],
    skip: int,
    limit: int,
) -> list[HistoryRecord]:
    """Fetch records from a history collection, excluding MongoDB's ``_id``."""
    try:
        collection = get_collection()
        cursor = collection.find({}, {"_id": 0}).skip(skip).limit(limit)
        records = await cursor.to_list(length=limit)
        logger.info(
            "Retrieved %d records from '%s' (skip=%d, limit=%d)",
            len(records),
            collection.name,
            skip,
            limit,
        )
        return records
    except (PyMongoError, RuntimeError):
        logger.exception(
            "Failed to retrieve history records (skip=%d, limit=%d)",
            skip,
            limit,
        )
        return []
