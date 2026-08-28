"""Preprocessing utilities for twenty-seven-day forecast data."""

import logging

import pandas as pd

from app.ml.twenty_seven_day.loader import load_dataset


logger = logging.getLogger(__name__)


def preprocess_dataset(dataframe: pd.DataFrame | None = None) -> pd.DataFrame:
    """Clean and feature-engineer twenty-seven-day forecast data.

    Duplicate records are removed, date columns are retained and expanded into
    calendar features, missing values are filled by data type, and categorical
    columns are one-hot encoded. When no dataframe is supplied, the local
    training dataset is loaded first.

    Args:
        dataframe: Optional raw twenty-seven-day forecast dataframe to
            preprocess.

    Returns:
        A cleaned dataframe ready for use by prediction workflows.
    """
    dataframe = load_dataset().copy() if dataframe is None else dataframe.copy()
    original_row_count = len(dataframe)
    dataframe = dataframe.drop_duplicates().reset_index(drop=True)
    logger.info(
        "Removed %d duplicate rows from twenty-seven-day forecast data",
        original_row_count - len(dataframe),
    )

    _add_date_features(dataframe)
    _fill_missing_values(dataframe)
    dataframe = _encode_categorical_columns(dataframe)

    logger.info("Preprocessed %d rows of twenty-seven-day forecast data", len(dataframe))
    return dataframe


def _add_date_features(dataframe: pd.DataFrame) -> None:
    """Convert supported date columns and add calendar features in place."""
    for column in ("forecast_date", "issued_date"):
        if column not in dataframe.columns:
            continue

        dataframe[column] = pd.to_datetime(dataframe[column], errors="coerce")
        datetime_values = dataframe[column]
        dataframe[f"{column}_year"] = datetime_values.dt.year
        dataframe[f"{column}_month"] = datetime_values.dt.month
        dataframe[f"{column}_day"] = datetime_values.dt.day
        dataframe[f"{column}_day_of_year"] = datetime_values.dt.dayofyear


def _fill_missing_values(dataframe: pd.DataFrame) -> None:
    """Fill missing values using a type-appropriate, deterministic strategy."""
    for column in dataframe.columns:
        series = dataframe[column]
        if not series.isna().any():
            continue

        if pd.api.types.is_datetime64_any_dtype(series):
            non_null_values = series.dropna()
            fill_value = non_null_values.median() if not non_null_values.empty else pd.Timestamp("1970-01-01")
        elif pd.api.types.is_numeric_dtype(series):
            fill_value = series.median()
            if pd.isna(fill_value):
                fill_value = 0
        else:
            fill_value = "Unknown"

        dataframe[column] = series.fillna(fill_value)


def _encode_categorical_columns(dataframe: pd.DataFrame) -> pd.DataFrame:
    """One-hot encode object and categorical columns while retaining all features."""
    categorical_columns = dataframe.select_dtypes(include=["object", "category"]).columns
    if categorical_columns.empty:
        return dataframe

    return pd.get_dummies(dataframe, columns=list(categorical_columns), dtype=int)
