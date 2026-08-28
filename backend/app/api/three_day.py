"""HTTP endpoints for the FlareX 3-Day Forecast module."""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from app.services.history_service import get_three_day_history
from app.services.forecast_service import get_three_day_forecast
from app.services.prediction_service import PredictionDocument
from app.services.three_day_service import (
    get_current,
    get_predictions,
)


logger = logging.getLogger(__name__)

router = APIRouter(tags=["3-Day Forecast"])


@router.get("/history", response_model=list[PredictionDocument])
async def read_history(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1),
) -> list[PredictionDocument]:
    """Return a paginated list of stored three-day forecast history records."""
    try:
        records = await get_three_day_history(skip, limit)
        logger.info("Returned %d three-day history records", len(records))
        return records
    except Exception as error:
        logger.exception("Unable to retrieve three-day history records")
        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve three-day history records.",
        ) from error


@router.post("/current/refresh")
async def update_current_forecast() -> dict[str, Any]:
    """Force a server-side refresh of the current three-day NOAA forecast."""
    try:
        return await get_three_day_forecast(force_refresh=True)
    except Exception as error:
        logger.exception("Unable to update the current three-day forecast and predictions")
        raise HTTPException(
            status_code=500,
            detail="Unable to update the current three-day forecast.",
        ) from error

@router.get("/current")
async def read_current() -> dict[str, Any]:
    """Return a cached-or-refreshed normalized three-day forecast."""
    try:
        return await get_three_day_forecast()
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@router.get("/predictions")
async def read_predictions() -> list[PredictionDocument]:
    """Return stored 3-day forecast predictions as JSON."""
    return await get_predictions()
