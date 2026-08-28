"""Read-through caching and normalized NOAA forecast responses."""

import asyncio
import logging
from collections.abc import Awaitable, Callable
from datetime import datetime, timezone
from typing import Any

import pandas as pd

from app.config import FORECAST_CACHE_TTL_SECONDS
from app.database.collections import get_forecast_refresh_state_collection
from app.services.noaa_service import (
    dataframe_to_records,
    fetch_three_day_current,
    fetch_twenty_seven_day_current,
)
from app.services.prediction_service import (
    PredictionResult,
    generate_three_day_predictions,
    generate_twenty_seven_day_predictions,
)
from app.services.three_day_service import (
    get_current as get_three_day_current,
    get_predictions as get_three_day_predictions,
    save_current as save_three_day_current,
)
from app.services.twenty_seven_day_service import (
    get_current as get_twenty_seven_day_current,
    get_predictions as get_twenty_seven_day_predictions,
    save_current as save_twenty_seven_day_current,
)

logger = logging.getLogger(__name__)

SOURCE = "NOAA SWPC"

_locks = {
    "3day": asyncio.Lock(),
    "27day": asyncio.Lock(),
}


async def get_three_day_forecast(
    force_refresh: bool = False,
) -> dict[str, Any]:
    """Return the current 3-day NOAA forecast and AI prediction status."""
    return await _get_forecast(
        product="3day",
        force_refresh=force_refresh,
        fetcher=fetch_three_day_current,
        save_current=save_three_day_current,
        get_current=get_three_day_current,
        get_predictions=get_three_day_predictions,
        generate_predictions=generate_three_day_predictions,
    )


async def get_twenty_seven_day_forecast(
    force_refresh: bool = False,
) -> dict[str, Any]:
    """Return the current 27-day NOAA outlook and AI prediction status."""
    return await _get_forecast(
        product="27day",
        force_refresh=force_refresh,
        fetcher=fetch_twenty_seven_day_current,
        save_current=save_twenty_seven_day_current,
        get_current=get_twenty_seven_day_current,
        get_predictions=get_twenty_seven_day_predictions,
        generate_predictions=generate_twenty_seven_day_predictions,
    )


async def refresh_due_forecasts() -> list[dict[str, Any]]:
    """Refresh due NOAA products."""
    return await asyncio.gather(
        get_three_day_forecast(),
        get_twenty_seven_day_forecast(),
    )


async def _get_forecast(
    *,
    product: str,
    force_refresh: bool,
    fetcher: Callable[[], Awaitable[pd.DataFrame]],
    save_current: Callable[[list[dict[str, Any]]], Awaitable[int]],
    get_current: Callable[[], Awaitable[list[dict[str, Any]]]],
    get_predictions: Callable[[], Awaitable[list[dict[str, Any]]]],
    generate_predictions: Callable[[], Awaitable[PredictionResult]],
) -> dict[str, Any]:

    state = await _get_state(product)
    current = await get_current()

    if force_refresh or not current or _cache_expired(state):

        async with _locks[product]:

            state = await _get_state(product)
            current = await get_current()

            if force_refresh or not current or _cache_expired(state):

                try:
                    # -----------------------------------------------------
                    # 1. Fetch latest NOAA forecast
                    # -----------------------------------------------------
                    dataframe = await fetcher()

                    now = datetime.now(timezone.utc)

                    incoming_records = dataframe_to_records(dataframe)

                    changed = _forecast_changed(
                        current,
                        incoming_records,
                    )

                    # -----------------------------------------------------
                    # 2. Save NOAA data only after successful validation
                    # -----------------------------------------------------
                    if changed:
                        logger.info(
                            "NOAA %s forecast changed; saving new snapshot.",
                            product,
                        )

                        await save_current(incoming_records)

                        current = await get_current()

                    else:
                        logger.info(
                            "NOAA %s forecast unchanged.",
                            product,
                        )

                except Exception as error:

                    logger.exception(
                        "Unable to refresh %s NOAA forecast",
                        product,
                    )

                    # Never destroy a valid previous NOAA snapshot.
                    if not current:
                        raise RuntimeError(
                            f"No cached {product} NOAA forecast is available."
                        ) from error

                    state = await _save_state(
                        product,
                        issued_at=_state_datetime(
                            state,
                            "issued_at",
                        ),
                        fetched_at=_state_datetime(
                            state,
                            "fetched_at",
                        ),
                        stale=True,
                        last_error=str(error),
                        ai_status=(state or {}).get("ai_status"),
                    )

                    logger.warning(
                        "Retained stale %s NOAA snapshot after refresh failure.",
                        product,
                    )

                else:

                    # -----------------------------------------------------
                    # 3. Decide whether AI predictions must be regenerated
                    #
                    # IMPORTANT:
                    # If MongoDB contains the old "unavailable" status from
                    # the previous 16-feature model, regenerate even when
                    # NOAA itself has not changed.
                    # -----------------------------------------------------

                    previous_ai_status = (state or {}).get("ai_status")

                    should_regenerate_predictions = (
                        changed
                        or state is None
                        or not previous_ai_status
                        or previous_ai_status.get("status") != "available"
                    )

                    prediction_result = previous_ai_status

                    if should_regenerate_predictions:

                        logger.info(
                            "Generating %s AI predictions. "
                            "reason: changed=%s, state_missing=%s, "
                            "previous_status=%s",
                            product,
                            changed,
                            state is None,
                            (
                                previous_ai_status or {}
                            ).get("status"),
                        )

                        try:
                            prediction_result = (
                                await generate_predictions()
                            )

                            logger.info(
                                "Generated %s AI predictions: %s",
                                product,
                                prediction_result,
                            )

                        except Exception as error:

                            logger.exception(
                                "Unable to generate %s AI predictions",
                                product,
                            )

                            prediction_result = {
                                "status": "unavailable",
                                "records": 0,
                                "missing_features": [],
                                "message": str(error),
                            }

                    # -----------------------------------------------------
                    # 4. Save refreshed metadata
                    # -----------------------------------------------------

                    state = await _save_state(
                        product,
                        issued_at=_as_utc(
                            dataframe["issued_date"].iloc[0]
                        ),
                        fetched_at=now,
                        stale=False,
                        last_error=None,
                        ai_status=prediction_result,
                    )

    # -------------------------------------------------------------
    # 5. Read predictions from MongoDB
    # -------------------------------------------------------------

    predictions = await get_predictions()

    return _response(
        current,
        predictions,
        state,
    )


def _cache_expired(
    state: dict[str, Any] | None,
) -> bool:

    fetched_at = _state_datetime(
        state,
        "fetched_at",
    )

    if fetched_at is None:
        return True

    return (
        datetime.now(timezone.utc) - fetched_at
    ).total_seconds() >= FORECAST_CACHE_TTL_SECONDS


def _forecast_changed(
    existing: list[dict[str, Any]],
    incoming: list[dict[str, Any]],
) -> bool:
    """Compare normalized NOAA snapshots."""

    if len(existing) != len(incoming):
        return True

    ignored_keys = {"_id"}

    for old, new in zip(existing, incoming):

        old_values = {
            key: _comparable_value(value)
            for key, value in old.items()
            if key not in ignored_keys
        }

        new_values = {
            key: _comparable_value(value)
            for key, value in new.items()
            if key not in ignored_keys
        }

        if old_values != new_values:
            return True

    return False


def _comparable_value(value: Any) -> Any:

    if isinstance(value, datetime):

        timestamp = _as_utc(value)

        return timestamp.replace(
            tzinfo=None
        ).isoformat()

    return value


async def _get_state(
    product: str,
) -> dict[str, Any] | None:

    return await get_forecast_refresh_state_collection().find_one(
        {"product": product},
        {"_id": 0},
    )


async def _save_state(
    product: str,
    *,
    issued_at: datetime | None,
    fetched_at: datetime | None,
    stale: bool,
    last_error: str | None,
    ai_status: PredictionResult | None,
) -> dict[str, Any]:

    previous_state = await _get_state(product)

    last_successful_update = (
        fetched_at
        if not stale
        else _state_datetime(
            previous_state,
            "last_successful_update",
        )
    )

    state = {
        "product": product,
        "source": SOURCE,
        "issued_at": issued_at,
        "fetched_at": fetched_at,
        "last_successful_update": last_successful_update,
        "stale": stale,
        "last_error": last_error,
        "ai_status": ai_status or {
            "status": "unavailable",
            "records": 0,
            "missing_features": [],
            "message": "AI predictions are unavailable.",
        },
    }

    await get_forecast_refresh_state_collection().replace_one(
        {"product": product},
        state,
        upsert=True,
    )

    return state


def _response(
    current: list[dict[str, Any]],
    predictions: list[dict[str, Any]],
    state: dict[str, Any] | None,
) -> dict[str, Any]:

    state = state or {}

    ai_status = state.get(
        "ai_status",
        {
            "status": "unavailable",
            "records": 0,
            "missing_features": [],
            "message": "AI predictions are unavailable.",
        },
    )

    return {
        "source": state.get(
            "source",
            SOURCE,
        ),
        "issued_at": state.get(
            "issued_at"
        ),
        "fetched_at": state.get(
            "fetched_at"
        ),
        "last_successful_update": state.get(
            "last_successful_update"
        ),
        "stale": state.get(
            "stale",
            True,
        ),
        "last_error": state.get(
            "last_error"
        ),
        "forecast": current,
        "ai_status": ai_status,
        "ai_predictions": (
            predictions
            if ai_status.get("status") == "available"
            else []
        ),
    }


def _state_datetime(
    state: dict[str, Any] | None,
    key: str,
) -> datetime | None:

    value = (state or {}).get(key)

    if value is None:
        return None

    return _as_utc(value)


def _as_utc(value: Any) -> datetime:

    timestamp = pd.Timestamp(
        value
    ).to_pydatetime()

    if timestamp.tzinfo is None:
        return timestamp.replace(
            tzinfo=timezone.utc
        )

    return timestamp.astimezone(
        timezone.utc
    )