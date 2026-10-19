# Operations and model monitoring basics

## Implemented

The API loads one verified bundle during startup. Readiness requires the model,
metadata, and history to load successfully. Each response gets a generated
request ID. Structured request logs record method, route template, status, and
elapsed milliseconds, without raw bodies, product/date values, or query strings.
Unexpected errors are logged server-side and return a generic error to clients.

`/metrics` reports current-process request, validation-failure, server-error,
prediction, range-flag counts, and mean HTTP processing latency. Counters reset
on restart and are not aggregated across workers. The endpoint's own request is
counted after its snapshot is generated. Compose rotates container logs.

Model-info and prediction responses identify the exact MLflow run used as the
model version. Training-range flags identify features outside observed training
min/max values. They are a simple diagnostic, not a statistical drift test.

## Offline distribution diagnostic

```powershell
.\.venv\Scripts\python.exe -m src.monitoring.drift
```

This reads only five numeric predictor columns, comparing training and reserved
test-period features after final evaluation. It writes `reports/feature-drift.json`
with PSI (training-quantile bins and count smoothing), means, and outside-range
fractions. It does not use outcomes, alter the model, or trigger retraining.

PSI quantifies changes in binned distributions. It is not a significance test or
a causal explanation; pooled products and overlapping windows limit interpretation.
There is no universal alarm threshold configured. A future live system would
compare fresh request-feature batches against a versioned reference and calibrate
alerts for product mix, seasonality, and operational needs.

## What a larger system would need

- Central logs/metrics, latency percentiles, alerts, durable counts, and access
  controls for observability endpoints.
- Outcomes arriving later, linked by request/model version, to measure actual
  error and distinguish input drift from performance degradation.
- Versioned artifacts, controlled rollout/rollback, new temporal validation for
  retraining, and safeguards against using a repeatedly inspected test set.
- Authenticated TLS ingress, request-size/rate limits, secret rotation, and a
  trusted artifact distribution mechanism before public exposure.

No credentials are required by the local demo. Future credentials belong in
environment variables or platform secret stores, never source code. `.env` is
ignored. There is no API endpoint for uploading arbitrary joblib/pickle files.

PostgreSQL was deliberately omitted: this read-only demo has a small aggregate
history and no transactional ingestion. A live multi-user inventory application
could justify it for transaction ingestion, forecast audit records, and queries.
MLflow's local SQLite store already provides useful SQL-backed experiment storage.
