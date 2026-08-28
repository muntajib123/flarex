"""API routes for historical forecast data."""

from fastapi import APIRouter, Query

from app.services.history_service import (
    get_three_day_history,
    get_twenty_seven_day_history,
)

router = APIRouter()


@router.get("/3day")
async def three_day_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
):
    return await get_three_day_history(
        skip=skip,
        limit=limit,
    )


@router.get("/27day")
async def twenty_seven_day_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
):
    return await get_twenty_seven_day_history(
        skip=skip,
        limit=limit,
    )