"""Forecast contracts, train-only preprocessing, metrics, and persistence."""

import json

import joblib
import numpy as np
import pandas as pd
import pytest

from src.models.estimators import MODEL_FEATURES, build_model
from src.models.metrics import regression_metrics
from src.models.train import compare, finalize, select_winner


@pytest.fixture
def features():
    rows = 40
    return pd.DataFrame({"product_id": ["12345", "67890"] * (rows // 2),
                         "lag_1": np.arange(rows), "lag_7": np.arange(rows) + 1,
                         "mean_7": np.arange(rows) + 2, "mean_28": np.arange(rows) + 3,
                         "std_28": np.ones(rows), "weekday": np.arange(rows) % 7,
                         "month": np.ones(rows)})[MODEL_FEATURES]


@pytest.mark.parametrize("candidate", [
    {"kind": "baseline", "window": 7}, {"kind": "baseline", "window": 28},
    {"kind": "ridge", "alpha": 10},
    {"kind": "random_forest", "n_estimators": 8, "max_depth": 3,
     "min_samples_leaf": 2, "n_jobs": 1},
])
def test_prediction_serialization_roundtrip_and_nonnegative_policy(features, candidate, tmp_path):
    model = build_model(candidate).fit(features, np.arange(len(features)) * 7)
    expected = model.predict(features)
    assert expected.shape == (len(features),)
    assert (expected >= 0).all()
    path = tmp_path / "model.joblib"
    joblib.dump(model, path)
    np.testing.assert_array_equal(joblib.load(path).predict(features), expected)


@pytest.mark.parametrize("window", [7, 28])
def test_baseline_is_exact_previous_window_average(features, window):
    model = build_model({"kind": "baseline", "window": window}).fit(features, np.zeros(len(features)))
    np.testing.assert_array_equal(model.predict(features), features[f"mean_{window}"] * 7)


def test_preprocessor_statistics_are_fitted_on_training_only(features):
    model = build_model({"kind": "ridge", "alpha": 10}).fit(features, np.arange(len(features)))
    scaler = model.estimator_.named_steps["preprocessing"].named_transformers_["numeric"]
    expected = scaler.mean_.copy()
    future = features.copy()
    future["mean_28"] = 100000
    model.predict(future)
    np.testing.assert_array_equal(scaler.mean_, expected)
    assert scaler.mean_[3] == features.mean_28.mean()


def test_target_column_cannot_enter_predictor(features):
    model = build_model({"kind": "baseline", "window": 7}).fit(features, np.zeros(len(features)))
    with pytest.raises(ValueError, match="exactly these model features"):
        model.predict(features.assign(target_units_7d=999))


def test_unknown_product_is_rejected(features):
    model = build_model({"kind": "ridge", "alpha": 10}).fit(features, np.zeros(len(features)))
    features.loc[0, "product_id"] = "NEW"
    with pytest.raises(ValueError, match="Unknown product"):
        model.predict(features)


@pytest.mark.parametrize("column,value", [("mean_7", np.inf), ("lag_1", -1),
                                          ("weekday", 7), ("month", 0)])
def test_invalid_features_rejected(features, column, value):
    features[column] = features[column].astype(float)
    features.loc[0, column] = value
    with pytest.raises(ValueError):
        build_model({"kind": "baseline", "window": 7}).fit(features, np.zeros(len(features)))


def test_metrics_have_known_units_and_allow_negative_r_squared():
    values = regression_metrics([0, 10], [0, 0])
    assert values["mae"] == 5
    assert values["rmse"] == pytest.approx(np.sqrt(50))
    assert values["r2"] == -1
    assert regression_metrics([0, 0], [1, 1])["r2"] is None


def test_selection_uses_validation_mae_instead_of_training_error():
    rows = [{"name": "baseline", "train": {"mae": 10}, "validation": {"mae": 5}},
            {"name": "overfit", "train": {"mae": 0}, "validation": {"mae": 20}}]
    assert select_winner(rows)["name"] == "baseline"
    rows[1]["validation"]["mae"] = 5
    assert select_winner(rows)["name"] == "baseline"


@pytest.mark.parametrize("action", [compare, finalize])
def test_test_evaluation_marker_prevents_retuning_or_repeat_test(action, tmp_path, monkeypatch):
    monkeypatch.setattr("src.models.train.ROOT", tmp_path)
    marker = tmp_path / "models/final/test_evaluation_started.json"
    marker.parent.mkdir(parents=True)
    marker.write_text(json.dumps({"run_id": "already-started"}))
    with pytest.raises(FileExistsError):
        action({}, {})
