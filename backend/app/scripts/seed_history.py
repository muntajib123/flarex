"""Seed MongoDB history collections with preprocessed local forecast datasets.

Run from the backend directory with ``python -m app.scripts.seed_history``.
"""

import asyncio
import logging
from typing import Any

import pandas as pd
from motor.motor_asyncio import AsyncIOMotorCollection

from app.database.collections import (
    get_three_day_history_collection,
    get_twenty_seven_day_history_collection,
)
from app.database.mongodb import close_mongo_connection, connect_to_mongo
from app.ml.three_day.preprocess import preprocess_dataset as preprocess_three_day
from app.ml.twenty_seven_day.preprocess import (
    preprocess_dataset as preprocess_twenty_seven_day,
)


logger = logging.getLogger(__name__)


async def seed_history() -> dict[str, int]:
    """Replace MongoDB history collections with the local preprocessed datasets.

    Returns:
        The inserted document counts, keyed by collection name.
    """
    three_day_records = _dataframe_to_records(preprocess_three_day())
    twenty_seven_day_records = _dataframe_to_records(preprocess_twenty_seven_day())

    await connect_to_mongo()
    try:
        three_day_count = await _replace_collection(
            get_three_day_history_collection(), three_day_records
        )
        twenty_seven_day_count = await _replace_collection(
            get_twenty_seven_day_history_collection(), twenty_seven_day_records
        )
    finally:
        await close_mongo_connection()

    results = {
        "three_day_history": three_day_count,
        "twenty_seven_day_history": twenty_seven_day_count,
    }
    logger.info("Seeded history collections: %s", results)
    return results


async def _replace_collection(
    collection: AsyncIOMotorCollection,
    records: list[dict[str, Any]],
) -> int:
    """Delete a collection's records and insert the supplied records in bulk."""
    await collection.delete_many({})
    if not records:
        logger.warning("No records available for collection '%s'", collection.name)
        return 0

    result = await collection.insert_many(records)
    logger.info("Inserted %d records into '%s'", len(result.inserted_ids), collection.name)
    return len(result.inserted_ids)


def _dataframe_to_records(dataframe: pd.DataFrame) -> list[dict[str, Any]]:
    """Convert dataframe rows into MongoDB-safe dictionaries without NaN values."""
    records: list[dict[str, Any]] = []
    for row in dataframe.to_dict(orient="records"):
        record = {
            column: _serialize_value(value)
            for column, value in row.items()
            if not _is_missing(value)
        }
        records.append(record)
    return records


def _is_missing(value: Any) -> bool:
    """Return whether a scalar dataframe value is missing."""
    return bool(pd.isna(value))


def _serialize_value(value: Any) -> Any:
    """Convert pandas timestamps and scalar types into MongoDB-compatible values."""
    if isinstance(value, pd.Timestamp):
        return value.to_pydatetime()
    if hasattr(value, "item"):
        return value.item()
    return value


async def main() -> None:
    """Seed both history collections and print their inserted-record counts."""
    inserted_counts = await seed_history()
    print(f"three_day_history: {inserted_counts['three_day_history']} records inserted")
    print(
        "twenty_seven_day_history: "
        f"{inserted_counts['twenty_seven_day_history']} records inserted"
    )


if __name__ == "__main__":
    asyncio.run(main())
