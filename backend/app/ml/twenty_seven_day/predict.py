"""Prediction utilities for twenty-seven-day forecast data."""

import logging
from pathlib import Path

import joblib
import pandas as pd
from sklearn.multioutput import MultiOutputRegressor

from app.ml.twenty_seven_day.preprocess import preprocess_dataset


logger = logging.getLogger(__name__)

TARGET_COLUMNS = [
    "radio_flux_10.7cm",
    "planetary_A_index",
    "largest_Kp_index",
]
EXCLUDED_COLUMNS = ["forecast_date", "issued_date", *TARGET_COLUMNS]
MODEL_PATH = Path(__file__).resolve().parent / "models" / "twenty_seven_day_model.joblib"


def predict() -> pd.DataFrame:
    """Load the current dataset and return twenty-seven-day forecast predictions.

    Returns:
        A dataframe whose columns match the original twenty-seven-day target
        names.

    Raises:
        FileNotFoundError: If no trained model is available at ``MODEL_PATH``.
    """
    if not MODEL_PATH.is_file():
        raise FileNotFoundError(f"Trained model not found: {MODEL_PATH}")

    model: MultiOutputRegressor = joblib.load(MODEL_PATH)
    dataframe = preprocess_dataset()
    features = _prepare_features(dataframe, model)

    logger.info("Generating twenty-seven-day predictions for %d rows", len(features))
    predictions = model.predict(features)
    return pd.DataFrame(predictions, columns=TARGET_COLUMNS, index=dataframe.index)


def _prepare_features(
    dataframe: pd.DataFrame, model: MultiOutputRegressor
) -> pd.DataFrame:
    """Remove targets and dates, then align feature columns with the model."""
    features = dataframe.drop(columns=EXCLUDED_COLUMNS, errors="ignore")
    expected_columns = getattr(model, "feature_names_in_", None)
    if expected_columns is not None:
        return features.reindex(columns=expected_columns, fill_value=0)
    return features


if __name__ == "__main__":
    print(predict().head(10).to_string())
