"""Application-lifecycle scheduler for NOAA forecast refreshes."""

import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import Any

from app.config import FORECAST_SCHEDULER_INTERVAL_SECONDS
from app.services.forecast_service import refresh_due_forecasts


logger = logging.getLogger(__name__)
RefreshOperation = Callable[[], Awaitable[list[dict[str, Any]]]]


class ForecastScheduler:
    """Periodically invoke the cache-aware refresh operation without overlaps."""

    def __init__(
        self,
        refresh_operation: RefreshOperation = refresh_due_forecasts,
        interval_seconds: int = FORECAST_SCHEDULER_INTERVAL_SECONDS,
    ) -> None:
        self._refresh_operation = refresh_operation
        self._interval_seconds = interval_seconds
        self._task: asyncio.Task[None] | None = None
        self._stop_event = asyncio.Event()
        self._cycle_lock = asyncio.Lock()

    async def start(self) -> None:
        """Start the background loop once for this FastAPI process."""
        if self._task is not None and not self._task.done():
            return
        self._stop_event.clear()
        self._task = asyncio.create_task(self._run(), name="forecast-refresh-scheduler")
        logger.info("Forecast scheduler started (interval=%ss).", self._interval_seconds)

    async def stop(self) -> None:
        """Stop the loop and wait for the in-progress cycle to finish or cancel."""
        self._stop_event.set()
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self._task = None
        logger.info("Forecast scheduler stopped.")

    async def run_once(self) -> bool:
        """Run one refresh cycle, skipping it when a prior cycle is still active."""
        if self._cycle_lock.locked():
            logger.warning("Forecast scheduler cycle skipped; refresh already running.")
            return False
        async with self._cycle_lock:
            logger.info("Scheduler NOAA check started.")
            try:
                results = await self._refresh_operation()
            except Exception:
                # Individual product failures are handled by forecast_service; this is a final guard.
                logger.exception("Scheduler NOAA check failed.")
                return False
            for product, result in zip(("3day", "27day"), results):
                if result.get("stale"):
                    logger.warning("Scheduler retained stale %s NOAA snapshot.", product)
                else:
                    logger.info("Scheduler completed %s NOAA check.", product)
            return True

    async def _run(self) -> None:
        while not self._stop_event.is_set():
            await self.run_once()
            try:
                await asyncio.wait_for(
                    self._stop_event.wait(), timeout=self._interval_seconds
                )
            except asyncio.TimeoutError:
                continue


_scheduler: ForecastScheduler | None = None


def get_forecast_scheduler() -> ForecastScheduler:
    """Return the process-local scheduler used by the FastAPI lifespan."""
    global _scheduler
    if _scheduler is None:
        _scheduler = ForecastScheduler()
    return _scheduler
