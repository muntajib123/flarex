"""Model training utilities for three-day forecast predictions."""

import logging
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.multioutput import MultiOutputRegressor

from app.ml.three_day.preprocess import preprocess_dataset


logger = logging.getLogger(__name__)

TARGET_COLUMNS = [
    "max_Kp",
    "G_scale",
    "S1_prob",
    "R1_R2_prob",
    "R3_prob",
]

# These are the ONLY features used by the model.
#
# They are available both:
#   1. when training on historical NOAA data
#   2. when predicting future dates
#
# Do NOT add rationale_keywords or any other feature that is unknown
# for future dates.
FEATURE_COLUMNS = [
    "forecast_date_year",
    "forecast_date_month",
    "forecast_date_day",
    "forecast_date_day_of_year",
    "issued_date_year",
    "issued_date_month",
    "issued_date_day",
    "issued_date_day_of_year",
]

MODEL_PATH = (
    Path(__file__).resolve().parent
    / "models"
    / "three_day_model.joblib"
)


def train_model() -> dict[str, float]:
    """Train, evaluate, and save the three-day future prediction model."""

    dataframe = preprocess_dataset()

    _validate_training_data(dataframe)

    missing_features = [
        column
        for column in FEATURE_COLUMNS
        if column not in dataframe.columns
    ]

    if missing_features:
        raise ValueError(
            f"Missing required training features: {missing_features}"
        )

    features = dataframe[FEATURE_COLUMNS].copy()
    targets = dataframe[TARGET_COLUMNS].copy()

    # Make absolutely sure the model receives numeric values only.
    features = features.apply(pd.to_numeric, errors="coerce")

    if features.isna().any().any():
        raise ValueError(
            "Training features contain missing or non-numeric values."
        )

    if targets.isna().any().any():
        raise ValueError(
            "Training targets contain missing values."
        )

    if len(features) < 10:
        raise ValueError(
            "Not enough training records to train the three-day model."
        )

    features_train, features_test, targets_train, targets_test = train_test_split(
        features,
        targets,
        test_size=0.2,
        random_state=42,
    )

    model = MultiOutputRegressor(
        RandomForestRegressor(
            n_estimators=300,
            random_state=42,
            n_jobs=-1,
            min_samples_leaf=2,
        )
    )

    logger.info(
        "Training three-day model with %d future-safe features: %s",
        len(FEATURE_COLUMNS),
        FEATURE_COLUMNS,
    )

    model.fit(features_train, targets_train)

    predictions = model.predict(features_test)

    metrics = {
        "mae": float(
            mean_absolute_error(
                targets_test,
                predictions,
            )
        ),
        "rmse": float(
            mean_squared_error(
                targets_test,
                predictions,
            )
            ** 0.5
        ),
        "r2": float(
            r2_score(
                targets_test,
                predictions,
            )
        ),
    }

    MODEL_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    joblib.dump(model, MODEL_PATH)

    logger.info(
        "Saved three-day model to %s",
        MODEL_PATH,
    )

    return metrics


def _validate_training_data(
    dataframe: pd.DataFrame,
) -> None:
    """Validate that all targets and future-safe features exist."""

    missing_targets = [
        column
        for column in TARGET_COLUMNS
        if column not in dataframe.columns
    ]

    if missing_targets:
        raise ValueError(
            f"Missing required target columns: {missing_targets}"
        )

    missing_features = [
        column
        for column in FEATURE_COLUMNS
        if column not in dataframe.columns
    ]

    if missing_features:
        raise ValueError(
            f"Missing required feature columns: {missing_features}"
        )


if __name__ == "__main__":
    evaluation_metrics = train_model()

    print("Three-day model evaluation metrics:")

    for metric_name, metric_value in evaluation_metrics.items():
        print(
            f"{metric_name.upper()}: {metric_value:.4f}"
        )