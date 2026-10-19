"""API behavior uses explicit synthetic fixtures, never invented real metrics."""

import json

import pytest
from fastapi.testclient import TestClient

from src.api.app import create_app
from src.api.bundle import export_bundle
from src.api.service import BundleError, ForecastService, sha256


@pytest.fixture
def bundle(tmp_path):
    path = tmp_path / "bundle"
    export_bundle(path, fixture=True)
    return path


@pytest.fixture
def client(bundle):
    with TestClient(create_app(bundle)) as active:
        yield active


def test_health_and_model_info_expose_version_and_fixture_mode(client):
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["model_loaded"] is True
    assert health.headers["X-Request-ID"]
    info = client.get("/model-info").json()
    assert info["mode"] == "synthetic_ci_fixture"
    assert info["model_version"] == "ci-fixture"
    assert info["first_forecast_date"] == "2011-02-01"


def test_predict_is_deterministic_with_correct_schema(client):
    payload = {"product_id": "12345", "forecast_date": "2011-02-01"}
    first = client.post("/predict", json=payload)
    second = client.post("/predict", json=payload)
    assert first.status_code == 200
    assert first.json() == second.json()
    assert first.json()["predicted_units"] == 7  # Exact synthetic baseline fixture.
    assert first.json()["horizon_days"] == 7


@pytest.mark.parametrize("payload", [
    {}, {"product_id": "12345"},
    {"product_id": 12345, "forecast_date": "2011-02-01"},
    {"product_id": "12345", "forecast_date": "invalid"},
    {"product_id": "12345", "forecast_date": 1296518400},
    {"product_id": "12345", "forecast_date": "2011-02-30"},
    {"product_id": "12345", "forecast_date": "2011-02-01", "mean_7": 999},
    {"product_id": "99999", "forecast_date": "2011-02-01"},
    {"product_id": "12345", "forecast_date": "2011-01-31"},
    {"product_id": "12345", "forecast_date": "2026-01-01"},
])
def test_invalid_requests_are_422_and_counted(client, payload):
    assert client.post("/predict", json=payload).status_code == 422
    assert client.get("/metrics").json()["validation_failures"] == 1


def test_malformed_json_and_unknown_route(client):
    assert client.post("/predict", content="{bad", headers={"Content-Type": "application/json"}).status_code == 422
    assert client.get("/unknown").status_code == 404
    assert client.get("/openapi.json").status_code == 200
    assert client.get("/docs").status_code == 200


def test_model_or_history_tampering_fails_startup(bundle):
    with (bundle / "model.joblib").open("ab") as output:
        output.write(b"changed")
    with pytest.raises(BundleError, match="Model checksum"):
        ForecastService(bundle)


def test_history_tampering_fails_before_model_loading(bundle):
    with (bundle / "history.csv").open("a") as output:
        output.write("\n")
    with pytest.raises(BundleError, match="History checksum"):
        ForecastService(bundle)


def test_missing_bundle_fails_startup(tmp_path):
    with pytest.raises(BundleError):
        with TestClient(create_app(tmp_path / "missing")):
            pass


def test_unexpected_prediction_failure_is_generic_500_and_counted(client, monkeypatch):
    def fail(*_args):
        raise RuntimeError("private internal message")
    monkeypatch.setattr(client.app.state.service, "predict", fail)
    response = client.post("/predict", json={"product_id": "12345", "forecast_date": "2011-02-01"})
    assert response.status_code == 500
    assert "private internal message" not in response.text
    assert client.get("/metrics").json()["server_errors"] == 1


def test_future_history_changes_cannot_change_earlier_prediction(bundle):
    import pandas as pd
    original = ForecastService(bundle).feature_row("12345", "2011-02-01")
    history = pd.read_csv(bundle / "history.csv")
    history.loc[history.date >= "2011-02-01", "units"] = 10000
    history.to_csv(bundle / "history.csv", index=False)
    meta = json.loads((bundle / "metadata.json").read_text())
    meta["history_sha256"] = sha256(bundle / "history.csv")
    (bundle / "metadata.json").write_text(json.dumps(meta))
    changed = ForecastService(bundle).feature_row("12345", "2011-02-01")
    pd.testing.assert_frame_equal(original, changed)
