# Prediction API

## What a request means

Submit a supported product code and a forecast date. The server retrieves the
recorded daily history, computes the same features used in preparation, and
returns gross recorded units expected over that date and the following six days.

The frozen model was developed through September 30, 2011. Serving starts on
October 1 so a forecast cannot predate data used to fit the model. Available
history supports forecast dates through December 9, 2011. This is historical
replay, not a live 2026 retail feed. No target/outcome values are required by
the API, and clients cannot supply their own engineered features.

## Run locally (PowerShell, repository root)

```powershell
.\.venv\Scripts\python.exe -m src.api.bundle
.\.venv\Scripts\python.exe -m uvicorn src.api.app:app --host 127.0.0.1 --port 8001
```

The first command copies the trusted final model and an aggregate sales history
into ignored `serving_bundle/`, recording checksums and training feature ranges.
The second starts Uvicorn, the HTTP server hosting FastAPI. Keep its terminal
running. `/docs` provides interactive Swagger UI; `/redoc` provides another
documentation view; `/openapi.json` is the machine-readable contract.

## Endpoints

| Method and path | Purpose |
| --- | --- |
| `GET /health` | Readiness after model/history load, plus model version |
| `GET /model-info` | Supported products, dates, target, version, limits, test metrics |
| `POST /predict` | Validate a product/date and predict seven-day gross units |
| `GET /metrics` | Process-local counts, validation failures, errors, mean latency |

Invalid schemas, unknown products, and unsupported dates return 422. Missing or
corrupt bundles fail startup rather than returning placeholder predictions.
Unexpected inference failures return a generic 500 and are logged server-side.

## Example

```powershell
$body = @{ product_id = '21212'; forecast_date = '2011-10-01' } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri 'http://127.0.0.1:8001/predict' -ContentType 'application/json' -Body $body
```

Actual response captured from the frozen local model:

```json
{
  "product_id": "21212",
  "forecast_date": "2011-10-01",
  "horizon_days": 7,
  "predicted_units": 760.379753318479,
  "model_version": "fe48bb872b9b4d12aac4f7a5c42734e4",
  "mode": "historical_replay",
  "out_of_training_range_features": []
}
```

Fractional unit forecasts are valid numeric estimates, not an instruction to
order fractional products. A missing range flag does not mean a prediction is
accurate or in distribution.

`scripts/smoke_api.py` checks a running service. `scripts/verify_local_service.py`
captures real examples and a small warmed, sequential timing sample. These
checks do not establish throughput or production latency guarantees.

## Configuration and security boundary

`RETAILCAST_BUNDLE` optionally selects a server-controlled bundle directory.
Never accept model paths or uploaded pickle/joblib files from API clients.
Checksums detect changed bytes but do not authenticate an untrusted source.
The history contains aggregate product units, not customer IDs or descriptions.

The demo binds to localhost. Before exposing it publicly, add gateway
authentication, TLS, request-size/rate limits, and a deployment-specific secrets
and access policy. Those controls are not implemented by this local demo.
