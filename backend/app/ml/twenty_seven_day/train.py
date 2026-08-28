"""Model training utilities for twenty-seven-day forecast predictions."""

import logging
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
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


def train_model() -> dict[str, float]:
    """Train, evaluate, and save a multi-output twenty-seven-day forecast model.

    Returns:
        Evaluation metrics averaged across all target columns.

    Raises:
        ValueError: If required target columns or usable feature columns are absent.
    """
    dataframe = preprocess_dataset()
    _validate_training_data(dataframe)

    feature_columns = [
        column for column in dataframe.columns if column not in EXCLUDED_COLUMNS
    ]
    features = dataframe[feature_columns]
    targets = dataframe[TARGET_COLUMNS]

    features_train, features_test, targets_train, targets_test = train_test_split(
        features,
        targets,
        random_state=42,
    )
    model = MultiOutputRegressor(
        RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    )
    logger.info(
        "Training twenty-seven-day model with %d features", len(feature_columns)
    )
    model.fit(features_train, targets_train)

    predictions = model.predict(features_test)
    metrics = {
        "mae": float(mean_absolute_error(targets_test, predictions)),
        "rmse": float(mean_squared_error(targets_test, predictions) ** 0.5),
        "r2": float(r2_score(targets_test, predictions)),
    }

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    logger.info("Saved twenty-seven-day model to %s", MODEL_PATH)
    return metrics


def _validate_training_data(dataframe: pd.DataFrame) -> None:
    """Ensure the dataframe contains all targets and at least one feature."""
    missing_targets = [column for column in TARGET_COLUMNS if column not in dataframe]
    if missing_targets:
        raise ValueError(f"Missing required target columns: {missing_targets}")

    feature_columns = [
        column for column in dataframe.columns if column not in EXCLUDED_COLUMNS
    ]
    if not feature_columns:
        raise ValueError("No usable feature columns remain after excluding dates and targets")


if __name__ == "__main__":
    evaluation_metrics = train_model()
    print("Twenty-seven-day model evaluation metrics:")
    for metric_name, metric_value in evaluation_metrics.items():
        print(f"{metric_name.upper()}: {metric_value:.4f}")
