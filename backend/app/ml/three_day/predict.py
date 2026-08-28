"""Prediction utilities for three-day forecast data."""

import logging
from pathlib import Path

import joblib
import pandas as pd
from sklearn.multioutput import MultiOutputRegressor

from app.ml.three_day.preprocess import preprocess_dataset


logger = logging.getLogger(__name__)

TARGET_COLUMNS = ["max_Kp", "G_scale", "S1_prob", "R1_R2_prob", "R3_prob"]
EXCLUDED_COLUMNS = ["forecast_date", "issued_date", *TARGET_COLUMNS]
MODEL_PATH = Path(__file__).resolve().parent / "models" / "three_day_model.joblib"


def predict() -> pd.DataFrame:
    """Load the current dataset and return three-day forecast predictions.

    Returns:
        A dataframe whose columns match the original three-day target names.

    Raises:
        FileNotFoundError: If no trained model is available at ``MODEL_PATH``.
    """
    if not MODEL_PATH.is_file():
        raise FileNotFoundError(f"Trained model not found: {MODEL_PATH}")

    model: MultiOutputRegressor = joblib.load(MODEL_PATH)
    dataframe = preprocess_dataset()
    features = _prepare_features(dataframe, model)

    logger.info("Generating three-day predictions for %d rows", len(features))
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
