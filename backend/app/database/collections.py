"""Accessors for FlareX MongoDB collections."""

from motor.motor_asyncio import AsyncIOMotorCollection

from app.database.mongodb import get_database


THREE_DAY_HISTORY = "three_day_history"
THREE_DAY_CURRENT = "three_day_current"
THREE_DAY_PREDICTIONS = "three_day_predictions"

TWENTY_SEVEN_DAY_HISTORY = "twenty_seven_day_history"
TWENTY_SEVEN_DAY_CURRENT = "twenty_seven_day_current"
TWENTY_SEVEN_DAY_PREDICTIONS = "twenty_seven_day_predictions"
FORECAST_REFRESH_STATE = "forecast_refresh_state"


def get_three_day_history_collection() -> AsyncIOMotorCollection:
    """Return the collection containing historical three-day forecast data."""
    return get_database()[THREE_DAY_HISTORY]


def get_three_day_current_collection() -> AsyncIOMotorCollection:
    """Return the collection containing current three-day forecast data."""
    return get_database()[THREE_DAY_CURRENT]


def get_three_day_predictions_collection() -> AsyncIOMotorCollection:
    """Return the collection containing three-day forecast predictions."""
    return get_database()[THREE_DAY_PREDICTIONS]


def get_twenty_seven_day_history_collection() -> AsyncIOMotorCollection:
    """Return the collection containing historical 27-day forecast data."""
    return get_database()[TWENTY_SEVEN_DAY_HISTORY]


def get_twenty_seven_day_current_collection() -> AsyncIOMotorCollection:
    """Return the collection containing current 27-day forecast data."""
    return get_database()[TWENTY_SEVEN_DAY_CURRENT]


def get_twenty_seven_day_predictions_collection() -> AsyncIOMotorCollection:
    """Return the collection containing 27-day forecast predictions."""
    return get_database()[TWENTY_SEVEN_DAY_PREDICTIONS]


def get_forecast_refresh_state_collection() -> AsyncIOMotorCollection:
    """Return the collection containing NOAA refresh metadata."""
    return get_database()[FORECAST_REFRESH_STATE]
