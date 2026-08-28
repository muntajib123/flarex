"""Dataset loading utilities for three-day forecasts."""

import logging
from pathlib import Path

import pandas as pd


logger = logging.getLogger(__name__)


def load_dataset() -> pd.DataFrame:
    """Load and clean the locally stored three-day forecast dataset.

    Returns:
        A non-empty dataframe sorted chronologically by ``forecast_date`` when
        that column is available.

    Raises:
        ValueError: If the data directory contains no CSV file or the selected
            CSV produces an empty dataframe.
    """
    data_directory = Path(__file__).resolve().parent / "data"
    csv_files = sorted(data_directory.glob("*.csv"))

    if not csv_files:
        raise ValueError(f"No CSV file found in data directory: {data_directory}")

    csv_path = csv_files[0]
    logger.info("Loading three-day forecast dataset from %s", csv_path)
    dataframe = pd.read_csv(csv_path)

    if dataframe.empty:
        raise ValueError(f"Forecast dataset is empty: {csv_path}")

    for column in ("forecast_date", "issued_date"):
        if column in dataframe.columns:
            dataframe[column] = pd.to_datetime(dataframe[column], errors="coerce")

    if "forecast_date" in dataframe.columns:
        dataframe = dataframe.sort_values("forecast_date").reset_index(drop=True)

    logger.info("Loaded %d rows from %s", len(dataframe), csv_path)
    return dataframe
