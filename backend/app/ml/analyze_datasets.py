"""Print exploratory summaries for the preprocessed forecast datasets.

Run from the backend directory with ``python -m app.ml.analyze_datasets``.
"""

from collections.abc import Callable

import pandas as pd

from app.ml.three_day.preprocess import preprocess_dataset as preprocess_three_day
from app.ml.twenty_seven_day.preprocess import (
    preprocess_dataset as preprocess_twenty_seven_day,
)


def analyze_dataset(name: str, preprocessor: Callable[[], pd.DataFrame]) -> None:
    """Load a preprocessed dataset and print a formatted exploratory summary."""
    print("=" * 80)
    print(f"{name} DATASET")
    print("=" * 80)

    try:
        dataframe = preprocessor()
    except Exception as error:
        print(f"Unable to preprocess {name.lower()} dataset: {error}\n")
        return

    print(f"\nShape: {dataframe.shape}")
    print(f"\nColumn names:\n{list(dataframe.columns)}")
    print(f"\nData types:\n{dataframe.dtypes.to_string()}")
    print(f"\nMissing values per column:\n{dataframe.isna().sum().to_string()}")
    print(f"\nDuplicate rows: {dataframe.duplicated().sum()}")

    _print_date_details(dataframe)
    _print_numeric_summary(dataframe)

    print("\nFirst 5 rows:")
    print(dataframe.head().to_string())
    print()


def _print_date_details(dataframe: pd.DataFrame) -> None:
    """Print forecast-date range and issued-date cardinality when available."""
    if "forecast_date" in dataframe.columns:
        forecast_dates = pd.to_datetime(dataframe["forecast_date"], errors="coerce")
        print(
            "\nForecast date range: "
            f"{forecast_dates.min()} to {forecast_dates.max()}"
        )
    else:
        print("\nForecast date range: forecast_date column not available")

    if "issued_date" in dataframe.columns:
        print(f"Unique issued_date values: {dataframe['issued_date'].nunique()}")
    else:
        print("Unique issued_date values: issued_date column not available")


def _print_numeric_summary(dataframe: pd.DataFrame) -> None:
    """Print descriptive statistics for numeric columns, if present."""
    numeric_dataframe = dataframe.select_dtypes(include="number")
    print("\nSummary statistics for numeric columns:")
    if numeric_dataframe.empty:
        print("No numeric columns available.")
        return

    print(numeric_dataframe.describe().to_string())


def main() -> None:
    """Analyze both forecast datasets."""
    analyze_dataset("Three-day forecast", preprocess_three_day)
    analyze_dataset("Twenty-seven-day forecast", preprocess_twenty_seven_day)


if __name__ == "__main__":
    main()
