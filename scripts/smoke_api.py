"""Check a running HTTP service without assuming a particular model catalog."""

import argparse
import json
import time
import urllib.error
import urllib.request


def smoke(base, wait_seconds=0):
    deadline = time.monotonic() + wait_seconds
    while True:
        try:
            with urllib.request.urlopen(base + "/health", timeout=2) as response:
                if response.status == 200:
                    break
        except (OSError, urllib.error.URLError):
            if time.monotonic() >= deadline:
                raise
        if time.monotonic() >= deadline:
            raise TimeoutError("API did not become ready")
        time.sleep(1)
    def get(path):
        with urllib.request.urlopen(base + path, timeout=30) as response:
            return json.load(response)
    assert get("/health")["model_loaded"] is True
    info = get("/model-info")
    payload = {"product_id": info["product_ids"][0], "forecast_date": info["first_forecast_date"]}
    request = urllib.request.Request(base + "/predict", data=json.dumps(payload).encode(),
                                    headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=30) as response:
        result = json.load(response)
        assert response.headers["X-Request-ID"]
    assert result["predicted_units"] >= 0
    assert result["model_version"] == info["model_version"]
    invalid = urllib.request.Request(base + "/predict", data=b'{}',
                                    headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(invalid, timeout=30)
        raise AssertionError("Invalid request unexpectedly accepted")
    except urllib.error.HTTPError as error:
        assert error.code == 422
    assert get("/metrics")["validation_failures"] >= 1
    assert get("/openapi.json")["info"]["title"] == "RetailCast Prediction API"
    print(json.dumps({"request": payload, "actual_response": result}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--wait-seconds", type=int, default=0)
    args = parser.parse_args()
    smoke(args.base_url.rstrip("/"), args.wait_seconds)
