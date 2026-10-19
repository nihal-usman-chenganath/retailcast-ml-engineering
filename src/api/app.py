"""Start: python -m uvicorn src.api.app:app --host 127.0.0.1 --port 8000."""

import json
import logging
import os
import threading
import time
import uuid
from contextlib import asynccontextmanager
from datetime import date
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.api.service import ForecastService

LOGGER = logging.getLogger("retailcast.requests")
if not LOGGER.handlers:
    LOGGER.addHandler(logging.StreamHandler())
LOGGER.setLevel(logging.INFO)
LOGGER.propagate = False
ROOT = Path(__file__).resolve().parents[2]


class PredictRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", json_schema_extra={"example": {
        "product_id": "21212", "forecast_date": "2011-11-01"}})
    product_id: Annotated[str, Field(strict=True, pattern=r"^\d{5}[A-Z]{0,2}$", max_length=7)]
    forecast_date: date

    @field_validator("forecast_date", mode="before")
    @classmethod
    def iso_date_string(cls, value):
        if not isinstance(value, str) or len(value) != 10 or value[4] != "-" or value[7] != "-":
            raise ValueError("Use a YYYY-MM-DD date string")
        return value


class PredictResponse(BaseModel):
    product_id: str
    forecast_date: date
    horizon_days: int
    predicted_units: Annotated[float, Field(ge=0, allow_inf_nan=False)]
    model_version: str
    mode: str
    out_of_training_range_features: list[str]


class RequestCounters:
    def __init__(self):
        self.lock = threading.Lock()
        self.requests = self.errors = self.validation_failures = self.predictions = self.range_flags = 0
        self.total_ms = 0.0

    def record(self, status, elapsed_ms):
        with self.lock:
            self.requests += 1
            self.errors += int(status >= 500)
            self.validation_failures += int(status == 422)
            self.total_ms += elapsed_ms

    def predicted(self, flags):
        with self.lock:
            self.predictions += 1
            self.range_flags += int(bool(flags))

    def snapshot(self):
        with self.lock:
            return {"requests": self.requests, "server_errors": self.errors,
                    "validation_failures": self.validation_failures, "predictions": self.predictions,
                    "predictions_with_range_flags": self.range_flags,
                    "mean_request_ms": self.total_ms / self.requests if self.requests else 0.0,
                    "scope": "current process since startup; not durable or aggregated"}


def create_app(bundle_path=None):
    bundle = Path(bundle_path or os.environ.get("RETAILCAST_BUNDLE", ROOT / "serving_bundle"))

    @asynccontextmanager
    async def lifespan(application):
        application.state.service = ForecastService(bundle)
        yield

    application = FastAPI(title="RetailCast Prediction API", version="1.0.0", lifespan=lifespan,
        description="Historical replay of seven-day gross recorded unit sales. Not live inventory advice.")
    application.state.counters = RequestCounters()

    @application.middleware("http")
    async def record_request(request: Request, call_next):
        request_id = uuid.uuid4().hex
        start = time.perf_counter()
        status = 500
        try:
            response = await call_next(request)
            status = response.status_code
            response.headers["X-Request-ID"] = request_id
            return response
        except Exception:
            LOGGER.exception("Internal request failure request_id=%s", request_id)
            return JSONResponse(status_code=500, content={"detail": "Internal prediction service error"},
                                headers={"X-Request-ID": request_id})
        finally:
            elapsed = (time.perf_counter() - start) * 1000
            application.state.counters.record(status, elapsed)
            LOGGER.info(json.dumps({"request_id": request_id, "method": request.method,
                "path": request.scope.get("route").path if request.scope.get("route") else "unmatched",
                "status": status, "duration_ms": round(elapsed, 3)}))

    @application.exception_handler(RequestValidationError)
    async def invalid_schema(_request, _error):
        # Do not echo raw request bodies, credentials, or untrusted input values.
        return JSONResponse(status_code=422, content={"detail": "Invalid request schema; see /docs"})

    @application.get("/health")
    def health(request: Request):
        return {"status": "ok", "model_loaded": True,
                "model_version": request.app.state.service.metadata["model_version"]}

    @application.get("/model-info")
    def model_info(request: Request):
        service = request.app.state.service
        meta = service.metadata
        return {"model_name": meta["model_name"], "model_version": meta["model_version"],
                "mode": meta.get("mode", "historical_replay"), "horizon_days": 7,
                "history_days": 28, "product_ids": meta["product_ids"],
                "first_forecast_date": str(service.first_date.date()),
                "last_forecast_date": str(service.last_date.date()),
                "target": meta["target"], "test_metrics": meta.get("test_metrics"),
                "limitations": ["Historical UK sales, not live or UAE-validated demand",
                    "Limited accuracy; not validated for inventory decisions",
                    "Range flags are diagnostics, not statistical drift detection"]}

    @application.post("/predict", response_model=PredictResponse)
    def predict(payload: PredictRequest, request: Request):
        service = request.app.state.service
        try:
            value, flags = service.predict(payload.product_id, payload.forecast_date)
        except ValueError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error
        application.state.counters.predicted(flags)
        return {"product_id": payload.product_id, "forecast_date": payload.forecast_date,
                "horizon_days": 7, "predicted_units": value,
                "model_version": service.metadata["model_version"],
                "mode": service.metadata.get("mode", "historical_replay"),
                "out_of_training_range_features": flags}

    @application.get("/metrics", description="Process-local counters and request timing; no request bodies.")
    def metrics():
        return application.state.counters.snapshot()

    return application


app = create_app()
