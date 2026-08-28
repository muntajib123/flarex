"""Regression tests for NOAA parsing and dynamic prediction horizons."""

import asyncio
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import AsyncMock, patch

import joblib
import pandas as pd

from app.ml.three_day.preprocess import preprocess_dataset as preprocess_three_day
from app.services.forecast_service import _cache_expired
from app.services.forecast_service import _forecast_changed
from app.services.forecast_service import _get_forecast_with_timeout
from app.services.forecast_service import _get_forecast
from app.services.noaa_service import (
    TWENTY_SEVEN_DAY_COLUMNS,
    _parse_three_day_forecast,
    _parse_twenty_seven_day_forecast,
    _validate_dataframe,
    _download_noaa_product,
)
from app.services.prediction_service import (
    _build_future_dataframe,
    _missing_model_features,
    _prepare_features,
)
from app.services.scheduler_service import ForecastScheduler


def _three_day_product() -> str:
    rows = "\n".join(f"{hour:02d}-{hour + 3:02d}UT 2.0 3.0 4.0" for hour in range(0, 24, 3))
    return f""":Issued: 2026 Dec 29 1230 UTC
NOAA Kp index breakdown Dec 30-Jan 01 2026
{rows}
S1 or greater 1% 2% 3%
R1-R2 4% 5% 6%
R3 or greater 0% 1% 2%
Rationale: Quiet conditions expected.
"""


def _twenty_seven_day_product() -> str:
    start = datetime(2026, 12, 20)
    records = [
        f"{(start + timedelta(days=index)).strftime('%Y %b %d')} 100 10 3"
        for index in range(27)
    ]
    return ":Issued: 2026 Dec 19 2205 UTC\n" + "\n".join(records)


class ForecastPipelineTests(unittest.TestCase):
    def test_existing_models_load_with_their_original_feature_orders(self):
        root = Path(__file__).resolve().parents[1] / "app" / "ml"
        three_day_model = joblib.load(root / "three_day" / "models" / "three_day_model.joblib")
        twenty_seven_day_model = joblib.load(
            root / "twenty_seven_day" / "models" / "twenty_seven_day_model.joblib"
        )
        self.assertEqual(three_day_model.n_features_in_, 16)
        self.assertEqual(twenty_seven_day_model.n_features_in_, 8)
        self.assertIn("rationale_keywords_storm", three_day_model.feature_names_in_)
        self.assertEqual(
            list(twenty_seven_day_model.feature_names_in_),
            [
                "forecast_date_year",
                "forecast_date_month",
                "forecast_date_day",
                "forecast_date_day_of_year",
                "issued_date_year",
                "issued_date_month",
                "issued_date_day",
                "issued_date_day_of_year",
            ],
        )

    def test_three_day_parser_extracts_issue_time_and_year_rollover_dates(self):
        dataframe = _parse_three_day_forecast(_three_day_product())
        self.assertEqual(len(dataframe), 3)
        self.assertEqual(dataframe["forecast_date"].dt.strftime("%Y-%m-%d").tolist(), ["2026-12-30", "2026-12-31", "2027-01-01"])
        self.assertEqual(dataframe["issued_date"].iloc[0].tzinfo, timezone.utc)
        self.assertEqual(dataframe["max_Kp"].tolist(), [2.0, 3.0, 4.0])

    def test_twenty_seven_day_parser_extracts_chronological_horizon(self):
        dataframe = _parse_twenty_seven_day_forecast(_twenty_seven_day_product())
        self.assertEqual(len(dataframe), 27)
        self.assertTrue(dataframe["forecast_date"].is_monotonic_increasing)
        self.assertEqual(dataframe["forecast_date"].iloc[-1].strftime("%Y-%m-%d"), "2027-01-15")

    def test_malformed_noaa_product_is_rejected(self):
        with self.assertRaises(RuntimeError):
            _parse_three_day_forecast(":Issued: 2026 Dec 29 1230 UTC")
        malformed = _parse_twenty_seven_day_forecast(
            ":Issued: 2026 Dec 19 2205 UTC\n2026 Dec 20 100 10 3"
        )
        with self.assertRaises(RuntimeError):
            _validate_dataframe(malformed, TWENTY_SEVEN_DAY_COLUMNS, "twenty-seven-day")

    def test_prediction_dates_follow_noaa_final_date_across_year_boundary(self):
        current = pd.DataFrame(
            {
                "forecast_date": ["2026-12-30", "2026-12-31", "2027-01-01"],
                "issued_date": ["2026-12-29T12:30:00Z"] * 3,
            }
        )
        future = _build_future_dataframe(current, 3)
        self.assertEqual(future["forecast_date"].dt.strftime("%Y-%m-%d").tolist(), ["2027-01-02", "2027-01-03", "2027-01-04"])

    def test_twenty_seven_day_predictions_start_after_noaa_horizon(self):
        current = pd.DataFrame(
            {
                "forecast_date": ["2026-08-28", "2026-09-23"],
                "issued_date": ["2026-08-27T12:00:00Z"] * 2,
            }
        )
        future = _build_future_dataframe(current, 27)
        self.assertEqual(len(future), 27)
        self.assertEqual(future["forecast_date"].iloc[0].strftime("%Y-%m-%d"), "2026-09-24")
        self.assertEqual(future["forecast_date"].iloc[-1].strftime("%Y-%m-%d"), "2026-10-20")

    def test_three_day_future_rationale_is_reported_missing_not_zero_filled(self):
        class Model:
            feature_names_in_ = pd.Index(["forecast_date_year", "rationale_keywords_quiet"])

        future = _build_future_dataframe(
            pd.DataFrame({"forecast_date": ["2026-08-30"], "issued_date": ["2026-08-29"]}),
            3,
        )
        features = _prepare_features(preprocess_three_day(future), [], Model())
        self.assertEqual(_missing_model_features(features, Model()), ["rationale_keywords_quiet"])
        self.assertTrue(features["rationale_keywords_quiet"].isna().all())

    def test_cache_expiry(self):
        self.assertFalse(_cache_expired({"fetched_at": datetime.now(timezone.utc)}))
        self.assertTrue(_cache_expired({"fetched_at": datetime.now(timezone.utc) - timedelta(hours=1)}))

    def test_snapshot_change_detection(self):
        current = [{"forecast_date": datetime(2026, 8, 28), "value": 3}]
        same = [{"forecast_date": datetime(2026, 8, 28), "value": 3}]
        changed = [{"forecast_date": datetime(2026, 8, 28), "value": 4}]
        self.assertFalse(_forecast_changed(current, same))
        self.assertTrue(_forecast_changed(current, changed))


class NOAARequestTimeoutTests(unittest.IsolatedAsyncioTestCase):
    async def test_noaa_request_timeout_is_reported(self):
        async def slow_to_thread(*_args):
            await asyncio.sleep(1)

        with patch("app.services.noaa_service.NOAA_HTTP_TIMEOUT_SECONDS", 0.01), patch(
            "app.services.noaa_service.asyncio.to_thread",
            side_effect=slow_to_thread,
        ), patch(
            "app.services.noaa_service.logger.exception"
        ):
            with self.assertRaisesRegex(RuntimeError, "timed out or failed"):
                await _download_noaa_product("https://services.swpc.noaa.gov/example")

    async def test_forecast_request_has_a_hard_deadline(self):
        async def slow_forecast(**_kwargs):
            await asyncio.sleep(1)

        with patch("app.services.forecast_service.FORECAST_REQUEST_TIMEOUT_SECONDS", 0.01), patch(
            "app.services.forecast_service._get_forecast", side_effect=slow_forecast
        ):
            with self.assertRaisesRegex(RuntimeError, "Forecast request timed out"):
                await _get_forecast_with_timeout(product="27day")

    async def test_noaa_failure_retains_existing_snapshot(self):
        existing = [{"forecast_date": datetime(2026, 8, 28), "issued_date": datetime(2026, 8, 27)}]
        prior_state = {
            "source": "NOAA SWPC",
            "issued_at": datetime(2026, 8, 27, tzinfo=timezone.utc),
            "fetched_at": datetime.now(timezone.utc) - timedelta(hours=1),
            "last_successful_update": datetime(2026, 8, 27, tzinfo=timezone.utc),
            "ai_status": {"status": "available"},
        }

        async def failed_fetch():
            raise RuntimeError("NOAA unavailable")

        save_state = AsyncMock(
            return_value={**prior_state, "stale": True, "last_error": "NOAA unavailable"}
        )
        with patch("app.services.forecast_service._get_state", AsyncMock(return_value=prior_state)), patch(
            "app.services.forecast_service._save_state", save_state
        ):
            response = await _get_forecast(
                product="3day",
                force_refresh=True,
                fetcher=failed_fetch,
                save_current=AsyncMock(),
                get_current=AsyncMock(return_value=existing),
                get_predictions=AsyncMock(return_value=[]),
                generate_predictions=AsyncMock(),
            )
        self.assertTrue(response["stale"])
        self.assertEqual(response["forecast"], existing)
        self.assertEqual(response["last_error"], "NOAA unavailable")


class SchedulerTests(unittest.IsolatedAsyncioTestCase):
    async def test_scheduler_starts_runs_and_stops(self):
        calls = []

        async def refresh():
            calls.append("refresh")
            return [{"stale": False}, {"stale": False}]

        scheduler = ForecastScheduler(refresh_operation=refresh, interval_seconds=3600)
        await scheduler.start()
        await asyncio.sleep(0)
        await scheduler.stop()
        self.assertEqual(calls, ["refresh"])

    async def test_scheduler_prevents_overlapping_cycles(self):
        started = asyncio.Event()
        release = asyncio.Event()

        async def refresh():
            started.set()
            await release.wait()
            return [{"stale": False}, {"stale": False}]

        scheduler = ForecastScheduler(refresh_operation=refresh, interval_seconds=3600)
        first_cycle = asyncio.create_task(scheduler.run_once())
        await started.wait()
        self.assertFalse(await scheduler.run_once())
        release.set()
        self.assertTrue(await first_cycle)


if __name__ == "__main__":
    unittest.main()
