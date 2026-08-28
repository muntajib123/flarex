"""Aggregate router for FlareX API modules."""

from fastapi import APIRouter

from app.api import history, three_day, twenty_seven_day


api_router = APIRouter(prefix="/api")


api_router.include_router(
    three_day.router,
    prefix="/3day",
    tags=["3-Day Forecast"],
)


api_router.include_router(
    twenty_seven_day.router,
    prefix="/27day",
    tags=["27-Day Forecast"],
)


api_router.include_router(
    history.router,
    prefix="/history",
    tags=["Historical Data"],
)