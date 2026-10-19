"""Verify a trusted local bundle and prepare leakage-safe inference features."""

import hashlib
import json
import platform
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn

from src.features.history import build_history_features
from src.models.estimators import MODEL_FEATURES


def sha256(path):
    with Path(path).open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


class BundleError(RuntimeError):
    """The service cannot safely initialize its local model/data bundle."""


class ForecastService:
    def __init__(self, bundle):
        bundle = Path(bundle)
        try:
            self.metadata = json.loads((bundle / "metadata.json").read_text())
            meta = self.metadata
            if meta["features"] != MODEL_FEATURES or meta["history_days"] != 28 or meta["horizon_days"] != 7:
                raise BundleError("Bundle feature contract does not match this service")
            if meta["sklearn_version"] != sklearn.__version__ or meta["joblib_version"] != joblib.__version__:
                raise BundleError("Model library versions do not match this environment")
            if meta["python_version"].split(".")[:2] != platform.python_version().split(".")[:2]:
                raise BundleError("Python major/minor version does not match the model")
            if sha256(bundle / "model.joblib") != meta["model_sha256"]:
                raise BundleError("Model checksum mismatch")
            if sha256(bundle / "history.csv") != meta["history_sha256"]:
                raise BundleError("History checksum mismatch")
            history = pd.read_csv(bundle / "history.csv", dtype={"product_id": str}, parse_dates=["date"])
            if set(history.columns) != {"product_id", "date", "units"} or history.isna().any().any():
                raise BundleError("Invalid history schema or missing values")
            if not np.isfinite(history.units).all() or (history.units < 0).any() or (history.units % 1 != 0).any():
                raise BundleError("Invalid gross unit history")
            if set(history.product_id) != set(meta["product_ids"]):
                raise BundleError("History catalog differs from model catalog")
            ranges = history.groupby("product_id").date.agg(["min", "max", "size"])
            if ranges["min"].nunique() != 1 or ranges["max"].nunique() != 1:
                raise BundleError("Products must share the same history coverage")
            self.history = history
            self.first_date = max(history.date.min() + pd.Timedelta(days=28),
                                  pd.Timestamp(meta["development_target_end"]) + pd.Timedelta(days=1))
            self.last_date = history.date.max() + pd.Timedelta(days=1)
            if self.first_date > self.last_date:
                raise BundleError("No forecast dates remain after development cutoff")
            feature_frames = []
            for product, group in history.groupby("product_id", sort=True):
                group = group.sort_values("date").reset_index(drop=True)
                extended = pd.concat([group, pd.DataFrame({"product_id": [product],
                    "date": [self.last_date], "units": [0]})], ignore_index=True)
                features = build_history_features(extended)
                features["date"] = extended.date
                features["product_id"] = product
                feature_frames.append(features)
            self.features = pd.concat(feature_frames, ignore_index=True).set_index(["product_id", "date"])
            # Pickle-based loading is restricted to the trusted, checksum-verified bundle.
            self.model = joblib.load(bundle / "model.joblib")
            if sorted(self.model.product_ids_) != sorted(meta["product_ids"]):
                raise BundleError("Serialized model catalog differs from metadata")
        except BundleError:
            raise
        except (OSError, ValueError, KeyError, AttributeError, TypeError) as error:
            raise BundleError("Unable to initialize model bundle") from error

    def feature_row(self, product, forecast_date):
        cutoff = pd.Timestamp(forecast_date)
        if product not in self.metadata["product_ids"]:
            raise ValueError("Unknown product_id; see /model-info for the supported catalog")
        if not self.first_date <= cutoff <= self.last_date:
            raise ValueError(f"forecast_date must be between {self.first_date.date()} and {self.last_date.date()}")
        row = self.features.loc[[(product, cutoff)]].reset_index()
        return row.loc[:, MODEL_FEATURES]

    def predict(self, product, forecast_date):
        row = self.feature_row(product, forecast_date)
        value = float(self.model.predict(row)[0])
        # Range flag, not a drift or correctness decision.
        training_ranges = self.metadata.get("training_feature_ranges", {})
        flags = [column for column, bounds in training_ranges.items()
                 if float(row.iloc[0][column]) < bounds["min"] or float(row.iloc[0][column]) > bounds["max"]]
        return value, flags
