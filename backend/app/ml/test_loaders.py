"""Smoke-test the forecast dataset loaders.

Run from the backend directory with ``python -m app.ml.test_loaders``.
"""

from collections.abc import Callable

import pandas as pd

from app.ml.three_day.loader import load_dataset as load_three_day_dataset
from app.ml.twenty_seven_day.loader import (
    load_dataset as load_twenty_seven_day_dataset,
)


def print_dataset_details(name: str, loader: Callable[[], pd.DataFrame]) -> None:
    """Load a dataset and print its key details or a meaningful error message."""
    try:
        dataframe = loader()
    except Exception as error:
        print(f"Failed to load {name} dataset: {error}")
        return

    print(f"Dataset: {name}")
    print(f"Shape: {dataframe.shape}")
    print(f"Columns: {list(dataframe.columns)}")
    print("First 5 rows:")
    print(dataframe.head())
    print()


def main() -> None:
    """Load and display diagnostics for both forecast datasets."""
    print_dataset_details("Three-day forecast", load_three_day_dataset)
    print_dataset_details("Twenty-seven-day forecast", load_twenty_seven_day_dataset)


if __name__ == "__main__":
    main()
