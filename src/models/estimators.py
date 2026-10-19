"""Explicit feature selection and training-fitted preprocessing pipelines."""

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, RegressorMixin, clone
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.utils.validation import check_is_fitted

from src.data.prepare import FEATURES

MODEL_FEATURES = ["product_id", *FEATURES]
TARGET = "target_units_7d"


def validate_features(frame):
    """Enforce the model-facing contract; identifiers are labels, never numbers."""
    if not isinstance(frame, pd.DataFrame) or frame.empty:
        raise ValueError("Features must be a nonempty pandas DataFrame")
    if set(frame.columns) != set(MODEL_FEATURES):
        raise ValueError(f"Expected exactly these model features: {MODEL_FEATURES}")
    if frame.isna().any().any():
        raise ValueError("Missing model feature values")
    if not frame.product_id.map(lambda value: isinstance(value, str) and bool(value.strip())).all():
        raise ValueError("Product identifiers must be nonempty strings")
    values = frame[FEATURES].to_numpy(dtype=float)
    if not np.isfinite(values).all() or (values < 0).any():
        raise ValueError("Numeric features must be finite and nonnegative")
    if not frame.weekday.between(0, 6).all() or not frame.month.between(1, 12).all():
        raise ValueError("Invalid calendar feature range")
    if (frame.weekday % 1 != 0).any() or (frame.month % 1 != 0).any():
        raise ValueError("Calendar features must be whole numbers")
    return frame.loc[:, MODEL_FEATURES]


class HistoricalAverage(RegressorMixin, BaseEstimator):
    """No learned coefficients: forecast seven times a trailing daily mean."""

    def __init__(self, window=7):
        self.window = window

    def fit(self, X, y=None):
        if self.window not in (7, 28):
            raise ValueError("Baseline window must be 7 or 28 days")
        self.n_features_in_ = X.shape[1]
        return self

    def predict(self, X):
        check_is_fitted(self)
        return X[f"mean_{self.window}"].to_numpy(dtype=float) * 7


class NonnegativeForecast(RegressorMixin, BaseEstimator):
    """Apply the same contract and nonnegative policy for every candidate."""

    def __init__(self, estimator):
        self.estimator = estimator

    def fit(self, X, y):
        features = validate_features(X)
        target = np.asarray(y, dtype=float)
        if target.ndim != 1 or len(target) != len(features):
            raise ValueError("Target must be one dimensional with one value per row")
        if not np.isfinite(target).all() or (target < 0).any():
            raise ValueError("Training targets must be finite and nonnegative")
        self.estimator_ = clone(self.estimator).fit(features, target)
        self.product_ids_ = sorted(features.product_id.unique().tolist())
        self.n_features_in_ = len(MODEL_FEATURES)
        return self

    def predict(self, X):
        check_is_fitted(self, "estimator_")
        features = validate_features(X)
        unknown = set(features.product_id) - set(self.product_ids_)
        if unknown:
            raise ValueError("Unknown product ID; this model supports only its trained catalog")
        prediction = np.asarray(self.estimator_.predict(features), dtype=float)
        if prediction.shape != (len(features),) or not np.isfinite(prediction).all():
            raise ValueError("Estimator produced invalid predictions")
        return np.maximum(prediction, 0)


def build_model(candidate, seed=42):
    kind = candidate["kind"]
    if kind == "baseline":
        estimator = HistoricalAverage(window=candidate["window"])
    else:
        transformer = ColumnTransformer([
            ("product", OneHotEncoder(handle_unknown="error", sparse_output=False), ["product_id"]),
            ("numeric", StandardScaler() if kind == "ridge" else "passthrough", FEATURES),
        ], remainder="drop")
        if kind == "ridge":
            regression = Ridge(alpha=candidate["alpha"], solver="svd")
        elif kind == "random_forest":
            regression = RandomForestRegressor(
                n_estimators=candidate["n_estimators"], max_depth=candidate["max_depth"],
                min_samples_leaf=candidate["min_samples_leaf"], n_jobs=candidate["n_jobs"],
                random_state=seed)
        else:
            raise ValueError(f"Unknown model kind: {kind}")
        estimator = Pipeline([("preprocessing", transformer), ("regression", regression)])
    return NonnegativeForecast(estimator)
