import logging
import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router as router
from app.database.mongodb import close_mongo_connection, connect_to_mongo
from app.services.scheduler_service import get_forecast_scheduler


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Manage FlareX application startup and shutdown resources."""
    try:
        await asyncio.wait_for(connect_to_mongo(), timeout=10)
    except asyncio.TimeoutError as error:
        raise RuntimeError("MongoDB startup connection timed out.") from error
    logger.info("FlareX has started.")
    scheduler = get_forecast_scheduler()
    await scheduler.start()

    try:
        yield
    finally:
        await scheduler.stop()
        await close_mongo_connection()
        logger.info("FlareX has stopped.")

app = FastAPI(
    title="FlareX API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
def home():
    return {
        "application": "FlareX",
        "status": "Running",
        "modules": [
            "3-Day Forecast",
            "27-Day Forecast"
        ]
    }
