"""Capture actual HTTP examples and a small sequential localhost timing sample."""

import argparse
import json
import time
import urllib.error
import urllib.request
from pathlib import Path

import numpy as np


def verify(base, output, samples=30):
    def request(path, payload=None):
        data = json.dumps(payload).encode() if payload is not None else None
        req = urllib.request.Request(base + path, data=data,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.load(response), response.headers.get("X-Request-ID")
    health, _ = request("/health")
    info, _ = request("/model-info")
    payload = {"product_id": "21212", "forecast_date": "2011-10-01"}
    response, request_id = request("/predict", payload)
    assert health["model_loaded"] and response["model_version"] == info["model_version"]
    assert response["mode"] == "historical_replay" and request_id
    durations = []
    for _ in range(samples):
        start = time.perf_counter()
        repeat, _ = request("/predict", payload)
        durations.append((time.perf_counter() - start) * 1000)
        assert repeat == response
    statuses = {}
    for name, bad in {"missing_fields": {}, "unknown_product": {**payload, "product_id": "99999"},
                      "unavailable_date": {**payload, "forecast_date": "2026-01-01"}}.items():
        try:
            request("/predict", bad)
            raise AssertionError("Expected 422")
        except urllib.error.HTTPError as error:
            assert error.code == 422
            statuses[name] = error.code
    metrics, _ = request("/metrics")
    document, _ = request("/openapi.json")
    assert "/predict" in document["paths"]
    result = {"base_url": base, "health": health, "request": payload, "actual_response": response,
              "invalid_request_statuses": statuses, "process_metrics_snapshot": metrics,
              "timing": {"samples": samples, "p50_ms": float(np.percentile(durations, 50)),
                         "p95_ms": float(np.percentile(durations, 95)),
                         "scope": "Sequential localhost HTTP, one warmed model; not a load/capacity benchmark"}}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--output", type=Path, default=Path("reports/api-verification.json"))
    args = parser.parse_args()
    verify(args.base_url.rstrip("/"), args.output)
