"""Consistent unit-based metrics and per-product error reports."""

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, r2_score, root_mean_squared_error


def regression_metrics(actual, predicted):
    actual, predicted = np.asarray(actual, dtype=float), np.asarray(predicted, dtype=float)
    if actual.ndim != 1 or predicted.shape != actual.shape or len(actual) < 2:
        raise ValueError("Metrics require equal one-dimensional arrays with at least two rows")
    if not np.isfinite(actual).all() or not np.isfinite(predicted).all():
        raise ValueError("Metrics require finite values")
    return {"mae": float(mean_absolute_error(actual, predicted)),
            "rmse": float(root_mean_squared_error(actual, predicted)),
            "r2": float(r2_score(actual, predicted)) if np.var(actual) > 0 else None}


def per_product_metrics(product_ids, actual, predicted):
    frame = pd.DataFrame({"product_id": np.asarray(product_ids),
                          "actual": np.asarray(actual), "predicted": np.asarray(predicted)})
    rows = []
    for product, group in frame.groupby("product_id", sort=True):
        rows.append({"product_id": product, "examples": len(group),
                     **regression_metrics(group.actual, group.predicted)})
    return rows
