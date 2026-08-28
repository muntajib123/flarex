"""MongoDB persistence operations for forecast predictions."""

import logging
from collections.abc import Callable
from pathlib import Path
from datetime import timedelta
from typing import Any

import joblib
import pandas as pd
from motor.motor_asyncio import AsyncIOMotorCollection

from app.database.collections import (
    get_three_day_current_collection,
    get_three_day_predictions_collection,
    get_twenty_seven_day_current_collection,
    get_twenty_seven_day_predictions_collection,
)
from app.ml.three_day.preprocess import (
    preprocess_dataset as preprocess_three_day_dataset,
)
from app.ml.twenty_seven_day.preprocess import (
    preprocess_dataset as preprocess_twenty_seven_day_dataset,
)


PredictionDocument = dict[str, Any]
PredictionResult = dict[str, Any]

logger = logging.getLogger(__name__)

THREE_DAY_TARGET_COLUMNS = ["max_Kp", "G_scale", "S1_prob", "R1_R2_prob", "R3_prob"]
TWENTY_SEVEN_DAY_TARGET_COLUMNS = [
    "radio_flux_10.7cm",
    "planetary_A_index",
    "largest_Kp_index",
]
DATE_COLUMNS = ["forecast_date", "issued_date"]
ML_DIRECTORY = Path(__file__).resolve().parents[1] / "ml"


async def save_predictions(
    collection: AsyncIOMotorCollection,
    predictions: list[PredictionDocument],
) -> int:
    """Insert prediction documents and return the number successfully saved.

    An empty list is treated as a no-op because MongoDB does not accept an empty
    document list for ``insert_many``.
    """
    if not predictions:
        return 0

    result = await collection.insert_many(predictions)
    return len(result.inserted_ids)


async def replace_predictions(
    collection: AsyncIOMotorCollection,
    predictions: list[PredictionDocument],
) -> int:
    """Delete all existing predictions, insert replacements, and return their count."""
    await delete_predictions(collection)
    return await save_predictions(collection, predictions)


async def get_latest_predictions(
    collection: AsyncIOMotorCollection,
) -> list[PredictionDocument]:
    """Return every prediction document without MongoDB's internal ``_id`` field."""
    cursor = collection.find({}, {"_id": 0})
    return await cursor.to_list(length=None)


async def delete_predictions(collection: AsyncIOMotorCollection) -> int:
    """Delete every prediction document and return the number removed."""
    result = await collection.delete_many({})
    return result.deleted_count


async def generate_three_day_predictions() -> PredictionResult:
    """Generate and store predictions for the latest current three-day forecast.

    Returns:
        A status dictionary containing the number of stored prediction records.

    Raises:
        RuntimeError: If current data, the model, preprocessing, or persistence
            cannot be completed.
    """
    return await _generate_predictions(
        forecast_name="three-day",
        get_current_collection=get_three_day_current_collection,
        get_prediction_collection=get_three_day_predictions_collection,
        models_directory=ML_DIRECTORY / "three_day" / "models",
        target_columns=THREE_DAY_TARGET_COLUMNS,
        preprocessor=preprocess_three_day_dataset,
        horizon_days=3,
    )


async def generate_twenty_seven_day_predictions() -> PredictionResult:
    """Generate and store predictions for the latest current 27-day forecast.

    Returns:
        A status dictionary containing the number of stored prediction records.

    Raises:
        RuntimeError: If current data, the model, preprocessing, or persistence
            cannot be completed.
    """
    return await _generate_predictions(
        forecast_name="twenty-seven-day",
        get_current_collection=get_twenty_seven_day_current_collection,
        get_prediction_collection=get_twenty_seven_day_predictions_collection,
        models_directory=ML_DIRECTORY / "twenty_seven_day" / "models",
        target_columns=TWENTY_SEVEN_DAY_TARGET_COLUMNS,
        preprocessor=preprocess_twenty_seven_day_dataset,
        horizon_days=27,
    )


async def _generate_predictions(
    forecast_name: str,
    get_current_collection: Callable[[], AsyncIOMotorCollection],
    get_prediction_collection: Callable[[], AsyncIOMotorCollection],
    models_directory: Path,
    target_columns: list[str],
    preprocessor: Callable[[pd.DataFrame], pd.DataFrame],
    horizon_days: int,
) -> PredictionResult:
    """Predict a horizon immediately after the current NOAA forecast."""
    try:
        current_collection = get_current_collection()
        current_records = await current_collection.find({}, {"_id": 0}).to_list(
            length=None
        )
        if not current_records:
            raise ValueError(f"No current {forecast_name} forecast records are available.")

        current_dataframe = pd.DataFrame(current_records)
        model = _load_latest_model(models_directory)
        future_dataframe = _build_future_dataframe(current_dataframe, horizon_days)
        processed_dataframe = preprocessor(future_dataframe)
        features = _prepare_features(processed_dataframe, target_columns, model)
        missing_features = _missing_model_features(features, model)
        if missing_features:
            await replace_predictions(get_prediction_collection(), [])
            return {
                "status": "unavailable",
                "records": 0,
                "missing_features": missing_features,
                "message": "Required model features are unavailable for the future horizon.",
            }
        predictions = model.predict(features)
        prediction_records = _prediction_records(
            processed_dataframe,
            predictions,
            target_columns,
        )
        prediction_collection = get_prediction_collection()
        inserted_count = await replace_predictions(
            prediction_collection,
            prediction_records,
        )
    except Exception as error:
        logger.exception("Unable to generate %s predictions", forecast_name)
        raise RuntimeError(f"Unable to generate {forecast_name} predictions.") from error

    logger.info("Generated %d %s prediction records", inserted_count, forecast_name)
    return {"records": inserted_count, "status": "available"}


def _load_latest_model(models_directory: Path) -> Any:
    """Load the most recently modified Joblib model from a model directory."""
    model_paths = list(models_directory.glob("*.joblib"))
    if not model_paths:
        raise FileNotFoundError(f"No trained model found in {models_directory}")

    latest_model_path = max(model_paths, key=lambda path: path.stat().st_mtime)
    logger.info("Loading trained model from %s", latest_model_path)
    return joblib.load(latest_model_path)


def _prepare_features(
    dataframe: pd.DataFrame,
    target_columns: list[str],
    model: Any,
) -> pd.DataFrame:
    """Remove unavailable target/date fields and align features to the model."""
    features = dataframe.drop(columns=[*DATE_COLUMNS, *target_columns], errors="ignore")
    expected_columns = getattr(model, "feature_names_in_", None)
    if expected_columns is not None:
        return features.reindex(columns=expected_columns)
    return features


def _missing_model_features(dataframe: pd.DataFrame, model: Any) -> list[str]:
    """Return required model features that cannot be validly supplied."""
    expected_columns = getattr(model, "feature_names_in_", None)
    if expected_columns is None:
        return []
    return [column for column in expected_columns if column not in dataframe or dataframe[column].isna().any()]


def _build_future_dataframe(
    current_dataframe: pd.DataFrame,
    horizon_days: int,
) -> pd.DataFrame:
    """Build only date-derived model inputs after the authoritative NOAA horizon."""
    if "forecast_date" not in current_dataframe or "issued_date" not in current_dataframe:
        raise ValueError("Current NOAA data is missing required date columns.")

    final_date = pd.to_datetime(current_dataframe["forecast_date"], errors="raise").max()
    issued_date = pd.to_datetime(current_dataframe["issued_date"], errors="raise").max()
    prediction_dates = [final_date + timedelta(days=offset) for offset in range(1, horizon_days + 1)]
    return pd.DataFrame(
        {"forecast_date": prediction_dates, "issued_date": [issued_date] * horizon_days}
    )


def _prediction_records(
    dataframe: pd.DataFrame,
    predictions: Any,
    target_columns: list[str],
) -> list[PredictionDocument]:
    """Attach forecast dates to predictions and serialize them for MongoDB."""
    prediction_dataframe = pd.DataFrame(
        predictions,
        columns=target_columns,
        index=dataframe.index,
    )
    for column in reversed(DATE_COLUMNS):
        if column in dataframe.columns:
            prediction_dataframe.insert(0, column, dataframe[column])

    return [_mongo_safe_record(row) for row in prediction_dataframe.to_dict("records")]


def _mongo_safe_record(record: PredictionDocument) -> PredictionDocument:
    """Convert pandas and NumPy scalar values into BSON-compatible values."""
    converted_record: PredictionDocument = {}
    for column, value in record.items():
        if bool(pd.isna(value)):
            continue
        if isinstance(value, pd.Timestamp):
            converted_record[column] = value.to_pydatetime()
        elif hasattr(value, "item"):
            converted_record[column] = value.item()
        else:
            converted_record[column] = value
    return converted_record
