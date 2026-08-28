"""Fetch current NOAA Space Weather Prediction Center forecast products."""

import asyncio
import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen

import pandas as pd

from app.config import NOAA_HTTP_TIMEOUT_SECONDS

logger = logging.getLogger(__name__)

THREE_DAY_FORECAST_URL = (
    "https://services.swpc.noaa.gov/text/3-day-forecast.txt"
)
TWENTY_SEVEN_DAY_FORECAST_URL = (
    "https://services.swpc.noaa.gov/text/27-day-outlook.txt"
)

THREE_DAY_COLUMNS = [
    "forecast_date",
    "issued_date",
    "max_Kp",
    "G_scale",
    "S1_prob",
    "R1_R2_prob",
    "R3_prob",
    "rationale_keywords",
]

TWENTY_SEVEN_DAY_COLUMNS = [
    "issued_date",
    "forecast_date",
    "radio_flux_10.7cm",
    "planetary_A_index",
    "largest_Kp_index",
]


async def fetch_three_day_current() -> pd.DataFrame:
    """Fetch and validate NOAA's current three-day forecast.

    Returns:
        A dataframe matching the three-day forecast schema.

    Raises:
        RuntimeError: If the NOAA product cannot be fetched or parsed.
    """
    forecast_text = await _download_noaa_product(THREE_DAY_FORECAST_URL)

    try:
        dataframe = _parse_three_day_forecast(forecast_text)
    except (RuntimeError, ValueError) as error:
        logger.exception("Unable to parse the current three-day NOAA forecast")
        raise RuntimeError(
            "Unable to parse the current three-day NOAA forecast."
        ) from error

    _validate_dataframe(dataframe, THREE_DAY_COLUMNS, "three-day")

    return dataframe


async def fetch_twenty_seven_day_current() -> pd.DataFrame:
    """Fetch and validate NOAA's current twenty-seven-day forecast.

    Returns:
        A dataframe matching the twenty-seven-day forecast schema.

    Raises:
        RuntimeError: If the NOAA product cannot be fetched or parsed.
    """
    forecast_text = await _download_noaa_product(
        TWENTY_SEVEN_DAY_FORECAST_URL
    )

    try:
        dataframe = _parse_twenty_seven_day_forecast(forecast_text)
    except (RuntimeError, ValueError) as error:
        logger.exception(
            "Unable to parse the current twenty-seven-day NOAA forecast"
        )
        raise RuntimeError(
            "Unable to parse the current twenty-seven-day NOAA forecast."
        ) from error

    _validate_dataframe(
        dataframe,
        TWENTY_SEVEN_DAY_COLUMNS,
        "twenty-seven-day",
    )

    return dataframe


async def _download_noaa_product(url: str) -> str:
    """Download a NOAA text product without blocking the event loop."""
    try:
        return await asyncio.to_thread(_read_url, url)
    except (OSError, URLError, UnicodeDecodeError, RuntimeError) as error:
        logger.exception("Unable to fetch NOAA forecast from %s", url)
        raise RuntimeError(
            f"NOAA request timed out or failed for {url}."
        ) from error


def _read_url(url: str) -> str:
    """Read and decode a NOAA text response synchronously for ``to_thread``."""
    with urlopen(  # noqa: S310 - NOAA URL is constant.
        url,
        timeout=NOAA_HTTP_TIMEOUT_SECONDS,
    ) as response:
        if response.status != 200:
            raise RuntimeError(
                f"NOAA returned HTTP {response.status} for {url}."
            )

        return response.read().decode("utf-8")


def _parse_three_day_forecast(forecast_text: str) -> pd.DataFrame:
    """Parse NOAA's three-day text product into the application schema."""
    issued_date = _extract_issued_date(forecast_text)
    forecast_dates = _extract_three_day_dates(forecast_text)
    max_kp_values = _extract_kp_maxima(forecast_text)
    s1_probabilities = _extract_probability_row(
        forecast_text,
        r"S1 or greater",
    )
    r1_r2_probabilities = _extract_probability_row(
        forecast_text,
        r"R1-R2",
    )
    r3_probabilities = _extract_probability_row(
        forecast_text,
        r"R3 or greater",
    )
    rationale_keywords = _extract_rationale_keywords(forecast_text)

    records = [
        {
            "forecast_date": forecast_date,
            "issued_date": issued_date,
            "max_Kp": max_kp_values[index],
            "G_scale": _kp_to_g_scale(max_kp_values[index]),
            "S1_prob": s1_probabilities[index],
            "R1_R2_prob": r1_r2_probabilities[index],
            "R3_prob": r3_probabilities[index],
            "rationale_keywords": rationale_keywords,
        }
        for index, forecast_date in enumerate(forecast_dates)
    ]

    return pd.DataFrame(records, columns=THREE_DAY_COLUMNS)


def _parse_twenty_seven_day_forecast(
    forecast_text: str,
) -> pd.DataFrame:
    """Parse NOAA's 27-day text product into the application schema."""
    issued_date = _extract_issued_date(forecast_text)

    row_pattern = re.compile(
        r"\b(\d{4})\s+([A-Za-z]{3})\s+(\d{1,2})\s+"
        r"(\d+(?:\.\d+)?)\s+"
        r"(\d+(?:\.\d+)?)\s+"
        r"(\d+(?:\.\d+)?)\b"
    )

    records = []

    for (
        year,
        month,
        day,
        radio_flux,
        planetary_a,
        largest_kp,
    ) in row_pattern.findall(forecast_text):
        try:
            forecast_date = datetime.strptime(
                f"{year} {month} {day}",
                "%Y %b %d",
            )
        except ValueError as error:
            raise RuntimeError(
                "NOAA 27-day product contains an invalid forecast date."
            ) from error

        records.append(
            {
                "issued_date": issued_date,
                "forecast_date": forecast_date,
                "radio_flux_10.7cm": float(radio_flux),
                "planetary_A_index": float(planetary_a),
                "largest_Kp_index": float(largest_kp),
            }
        )

    return pd.DataFrame(
        records,
        columns=TWENTY_SEVEN_DAY_COLUMNS,
    )


def _extract_issued_date(forecast_text: str) -> datetime:
    """Extract the publication date from a NOAA text product."""
    issued_match = re.search(
        r":Issued:\s*(\d{4}\s+[A-Za-z]{3}\s+\d{1,2})"
        r"(?:\s+(\d{4})\s*UTC)?",
        forecast_text,
    )

    if issued_match is None:
        issued_match = re.search(
            r"\bIssued\s+(\d{4}-\d{2}-\d{2})\b",
            forecast_text,
        )

        if issued_match is None:
            raise RuntimeError(
                "NOAA product does not contain an issued date."
            )

        return datetime.strptime(
            issued_match.group(1),
            "%Y-%m-%d",
        ).replace(tzinfo=timezone.utc)

    value = issued_match.group(1)
    issue_time = issued_match.group(2)

    if issue_time:
        value = f"{value} {issue_time}"
        return datetime.strptime(
            value,
            "%Y %b %d %H%M",
        ).replace(tzinfo=timezone.utc)

    return datetime.strptime(
        value,
        "%Y %b %d",
    ).replace(tzinfo=timezone.utc)


def _extract_three_day_dates(
    forecast_text: str,
) -> list[datetime]:
    """Extract the three forecast dates from NOAA's Kp forecast heading."""
    date_match = re.search(
        r"NOAA Kp index breakdown\s+"
        r"([A-Za-z]{3})\s+(\d{1,2})"
        r"-(?:([A-Za-z]{3})\s+)?(\d{1,2})\s+(\d{4})",
        forecast_text,
    )

    if date_match is None:
        raise RuntimeError(
            "NOAA three-day product does not contain forecast dates."
        )

    start_month, start_day, end_month, end_day, year = (
        date_match.groups()
    )

    start_date = datetime.strptime(
        f"{year} {start_month} {start_day}",
        "%Y %b %d",
    )

    end_month = end_month or start_month

    end_date = datetime.strptime(
        f"{year} {end_month} {end_day}",
        "%Y %b %d",
    )

    if end_date < start_date:
        end_date = end_date.replace(
            year=end_date.year + 1
        )

    dates = [
        start_date + timedelta(days=offset)
        for offset in range(3)
    ]

    if dates[-1] != end_date:
        raise RuntimeError(
            "NOAA three-day product does not define exactly three dates."
        )

    return dates


def _extract_kp_maxima(
    forecast_text: str,
) -> list[float]:
    """Calculate daily maximum Kp values from NOAA's 3-hour Kp table."""
    kp_section_match = re.search(
        r"NOAA Kp index breakdown.*?(?=Rationale:)",
        forecast_text,
        flags=re.DOTALL,
    )

    if kp_section_match is None:
        raise RuntimeError(
            "NOAA three-day product does not contain a Kp table."
        )

    row_pattern = re.compile(
        r"\b\d{2}-\d{2}UT\s+"
        r"(\d+(?:\.\d+)?)(?:\s+\(G\d\))?\s+"
        r"(\d+(?:\.\d+)?)(?:\s+\(G\d\))?\s+"
        r"(\d+(?:\.\d+)?)(?:\s+\(G\d\))?"
    )

    kp_rows = row_pattern.findall(
        kp_section_match.group(0)
    )

    if len(kp_rows) != 8:
        raise RuntimeError(
            "NOAA three-day product contains an invalid Kp table."
        )

    return [
        max(float(row[day]) for row in kp_rows)
        for day in range(3)
    ]


def _extract_probability_row(
    forecast_text: str,
    label: str,
) -> list[float]:
    """Extract the three daily percentage values from a named NOAA forecast row."""
    probability_match = re.search(
        rf"{label}\s+"
        r"(\d+(?:\.\d+)?)%\s+"
        r"(\d+(?:\.\d+)?)%\s+"
        r"(\d+(?:\.\d+)?)%",
        forecast_text,
    )

    if probability_match is None:
        raise RuntimeError(
            f"NOAA three-day product does not contain '{label}' values."
        )

    return [
        float(value) / 100
        for value in probability_match.groups()
    ]


def _extract_rationale_keywords(
    forecast_text: str,
) -> str:
    """Create a compact rationale category from notable NOAA forecast wording."""
    normalized_text = forecast_text.lower()
    keywords = []

    if (
        "coronal hole" in normalized_text
        or "high speed stream" in normalized_text
    ):
        keywords.append("ch hss")

    if (
        "coronal mass ejection" in normalized_text
        or " cme" in normalized_text
    ):
        keywords.append("cme")

    if "storm" in normalized_text:
        keywords.append("storm")

    if "quiet" in normalized_text:
        keywords.append("quiet")

    return ",".join(keywords) if keywords else "unknown"


def _kp_to_g_scale(max_kp: float) -> int:
    """Map NOAA's maximum Kp index to its geomagnetic storm scale."""
    if max_kp >= 9:
        return 5
    if max_kp >= 8:
        return 4
    if max_kp >= 7:
        return 3
    if max_kp >= 6:
        return 2
    if max_kp >= 5:
        return 1

    return 0


def _validate_dataframe(
    dataframe: pd.DataFrame,
    required_columns: list[str],
    forecast_name: str,
) -> None:
    """Ensure a parsed forecast has all required fields and usable records."""
    missing_columns = [
        column
        for column in required_columns
        if column not in dataframe.columns
    ]

    if missing_columns:
        raise RuntimeError(
            f"Parsed {forecast_name} forecast is missing fields: "
            f"{missing_columns}"
        )

    if dataframe.empty:
        raise RuntimeError(
            f"Parsed {forecast_name} forecast contains no records."
        )

    if dataframe[required_columns].isna().any().any():
        raise RuntimeError(
            f"Parsed {forecast_name} forecast contains missing values."
        )

    if dataframe["forecast_date"].duplicated().any():
        raise RuntimeError(
            f"Parsed {forecast_name} forecast contains duplicate dates."
        )

    if not dataframe["forecast_date"].is_monotonic_increasing:
        raise RuntimeError(
            f"Parsed {forecast_name} forecast dates are not chronological."
        )

    expected_count = 3 if forecast_name == "three-day" else 27

    if len(dataframe) != expected_count:
        raise RuntimeError(
            f"Parsed {forecast_name} forecast has "
            f"{len(dataframe)} records; "
            f"expected {expected_count}."
        )


def dataframe_to_records(
    dataframe: pd.DataFrame,
) -> list[dict[str, Any]]:
    """Convert dataframe records to MongoDB-safe dictionaries."""
    records: list[dict[str, Any]] = []

    for row in dataframe.to_dict(orient="records"):
        records.append(
            {
                column: (
                    value.to_pydatetime()
                    if isinstance(value, pd.Timestamp)
                    else value
                )
                for column, value in row.items()
            }
        )

    return records