"""Database operations for the FlareX 3-Day Forecast module."""

from app.database.collections import (
    get_three_day_current_collection,
    get_three_day_history_collection,
    get_three_day_predictions_collection,
)
from app.services.prediction_service import (
    PredictionDocument,
    get_latest_predictions,
    replace_predictions,
)


async def save_history(data: list[PredictionDocument]) -> int:
    """Replace the stored 3-day forecast history and return the saved count."""
    return await replace_predictions(get_three_day_history_collection(), data)


async def save_current(data: list[PredictionDocument]) -> int:
    """Replace the current 3-day forecast data and return the saved count."""
    return await replace_predictions(get_three_day_current_collection(), data)


async def save_predictions(data: list[PredictionDocument]) -> int:
    """Replace stored 3-day forecast predictions and return the saved count."""
    return await replace_predictions(get_three_day_predictions_collection(), data)


async def get_history() -> list[PredictionDocument]:
    """Return all stored 3-day forecast history documents."""
    return await get_latest_predictions(get_three_day_history_collection())


async def get_current() -> list[PredictionDocument]:
    """Return all current 3-day forecast data documents."""
    return await get_latest_predictions(get_three_day_current_collection())


async def get_predictions() -> list[PredictionDocument]:
    """Return all stored 3-day forecast prediction documents."""
    return await get_latest_predictions(get_three_day_predictions_collection())
