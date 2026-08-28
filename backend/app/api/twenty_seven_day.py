"""HTTP endpoints for the FlareX 27-Day Forecast module."""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from app.services.history_service import get_twenty_seven_day_history
from app.services.forecast_service import get_twenty_seven_day_forecast
from app.services.prediction_service import PredictionDocument
from app.services.twenty_seven_day_service import (
    get_current,
    get_predictions,
)


logger = logging.getLogger(__name__)

router = APIRouter(tags=["27-Day Forecast"])


@router.get("/history", response_model=list[PredictionDocument])
async def read_history(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1),
) -> list[PredictionDocument]:
    """Return a paginated list of stored twenty-seven-day history records."""
    try:
        records = await get_twenty_seven_day_history(skip, limit)
        logger.info("Returned %d twenty-seven-day history records", len(records))
        return records
    except Exception as error:
        logger.exception("Unable to retrieve twenty-seven-day history records")
        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve twenty-seven-day history records.",
        ) from error


@router.post("/current/refresh")
async def update_current_forecast() -> dict[str, Any]:
    """Force a server-side refresh of the current 27-day NOAA outlook."""
    try:
        return await get_twenty_seven_day_forecast(force_refresh=True)
    except Exception as error:
        logger.exception(
            "Unable to update the current twenty-seven-day forecast and predictions"
        )
        raise HTTPException(
            status_code=500,
            detail="Unable to update the current twenty-seven-day forecast.",
        ) from error

@router.get("/current")
async def read_current() -> dict[str, Any]:
    """Return a cached-or-refreshed normalized 27-day forecast."""
    try:
        return await get_twenty_seven_day_forecast()
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@router.get("/predictions")
async def read_predictions() -> list[PredictionDocument]:
    """Return stored 27-day forecast predictions as JSON."""
    return await get_predictions()
