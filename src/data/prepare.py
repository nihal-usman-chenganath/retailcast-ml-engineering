"""Prepare recorded gross unit sales and time-safe forecasting examples.

Run from repository root: python -m src.data.prepare
"""

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.features.history import build_history_features

ROOT = Path(__file__).resolve().parents[2]
REQUIRED = {"Invoice", "StockCode", "Description", "Quantity", "InvoiceDate",
            "Price", "Customer ID", "Country"}
FEATURES = ["lag_1", "lag_7", "mean_7", "mean_28", "std_28", "weekday", "month"]


def validate(frame):
    """Reject schema/type errors instead of silently dropping malformed records."""
    if set(frame.columns) != REQUIRED:
        raise ValueError("Source columns do not match the documented workbook schema")
    frame = frame.copy()
    if frame[["Invoice", "StockCode", "InvoiceDate", "Quantity", "Price"]].isna().any().any():
        raise ValueError("Missing required invoice, product, date, quantity, or price")
    frame["InvoiceDate"] = pd.to_datetime(frame["InvoiceDate"], errors="raise")
    for name in ["Quantity", "Price"]:
        frame[name] = pd.to_numeric(frame[name], errors="raise")
        if not np.isfinite(frame[name]).all():
            raise ValueError(f"Non-finite values in {name}")
    if (frame["Quantity"] % 1 != 0).any():
        raise ValueError("Quantity must contain whole units")
    frame["Invoice"] = frame["Invoice"].astype("string").str.strip()
    frame["StockCode"] = frame["StockCode"].astype("string").str.strip().str.upper()
    if frame[["Invoice", "StockCode"]].eq("").any().any():
        raise ValueError("Empty invoice or product identifier")
    return frame


def combine_sheets(sheets):
    """Later sheets own overlapping date ranges; retain duplicates within sheets.

    This avoids counting the repeated December 2010 export twice without assuming
    that identical transaction lines within one export are erroneous.
    """
    ordered = sorted(((name, validate(frame)) for name, frame in sheets.items()),
                     key=lambda item: item[1]["InvoiceDate"].min())
    parts, audit = [], []
    for i, (name, frame) in enumerate(ordered):
        if frame.empty:
            raise ValueError(f"Empty sheet: {name}")
        boundary = ordered[i + 1][1]["InvoiceDate"].min().normalize() if i + 1 < len(ordered) else None
        keep = frame if boundary is None else frame.loc[frame["InvoiceDate"] < boundary]
        audit.append({"sheet": name, "input_rows": len(frame), "retained_rows": len(keep),
                      "overlap_rows_excluded": len(frame) - len(keep),
                      "exclusive_end": str(boundary) if boundary is not None else None})
        parts.append(keep)
    return pd.concat(parts, ignore_index=True), audit


def clean_sales(frame):
    """Define gross recorded merchandise sales; exclusions are sequential counts."""
    frame = validate(frame)
    counts = {"input_rows": len(frame)}
    rules = [
        ("cancellations", ~frame["Invoice"].str.upper().str.startswith("C")),
        ("nonpositive_quantity", frame["Quantity"] > 0),
        ("nonpositive_price", frame["Price"] > 0),
        # Restrictive, auditable merchandise-code heuristic; not a product catalog.
        ("non_merchandise_code_pattern", frame["StockCode"].str.fullmatch(r"\d{5}[A-Z]{0,2}")),
    ]
    for name, mask in rules:
        before = len(frame)
        frame = frame.loc[mask.reindex(frame.index)]
        counts[f"excluded_{name}"] = before - len(frame)
    counts["retained_rows"] = len(frame)
    counts["retained_rows_missing_customer_id"] = int(frame["Customer ID"].isna().sum())
    counts["retained_exact_duplicates_beyond_first"] = int(frame.duplicated().sum())
    frame = frame.assign(date=frame["InvoiceDate"].dt.normalize())
    return frame, counts


def select_products(sales, config):
    cutoff = pd.Timestamp(config["selection_cutoff"])
    start = cutoff - pd.Timedelta(days=config["selection_lookback_days"])
    historical = sales.loc[sales["date"].between(start, cutoff, inclusive="left")]
    ranked = historical.groupby("StockCode").agg(
        units=("Quantity", "sum"), active_days=("date", "nunique"))
    ranked = ranked.loc[ranked.active_days >= config["minimum_active_days"]]
    ranked = ranked.reset_index().sort_values(["units", "StockCode"], ascending=[False, True])
    selected = ranked.head(config["number_of_products"])
    if len(selected) != config["number_of_products"]:
        raise ValueError("Not enough eligible products for the configured selection policy")
    return selected


def make_daily(sales, products, start, end):
    index = pd.MultiIndex.from_product(
        [products, pd.date_range(start, end)], names=["product_id", "date"])
    subset = sales.loc[sales["StockCode"].isin(products)]
    grouped = subset.groupby(["StockCode", "date"]).agg(
        units=("Quantity", "sum"), transaction_lines=("Quantity", "size"))
    grouped.index.names = ["product_id", "date"]
    # Zero means no qualifying sales were recorded; it does not mean in stock.
    daily = grouped.reindex(index, fill_value=0).reset_index()
    return daily


def make_examples(daily, horizon=7, history=28):
    if horizon < 1 or history < 7:
        raise ValueError("Positive horizon and at least seven history days required")
    parts = []
    for product, group in daily.groupby("product_id", sort=True):
        group = group.sort_values("date").reset_index(drop=True).copy()
        units = group["units"]
        group[FEATURES] = build_history_features(group, history)
        group["target_units_7d"] = units.iloc[::-1].rolling(horizon, min_periods=horizon).sum().iloc[::-1]
        group["target_end"] = group["date"] + pd.Timedelta(days=horizon - 1)
        group["history_end"] = group["date"] - pd.Timedelta(days=1)
        # Exclude contemporaneous units and line counts from model-facing data.
        columns = ["product_id", "date", "history_end", "target_end", *FEATURES, "target_units_7d"]
        parts.append(group.loc[:, columns].dropna())
    return pd.concat(parts, ignore_index=True)


def split_examples(examples, config):
    start = pd.Timestamp(config["selection_cutoff"])
    validation = pd.Timestamp(config["validation_start"])
    test = pd.Timestamp(config["test_start"])
    if not start < validation < test:
        raise ValueError("Split boundaries must be strictly chronological")
    train = examples.loc[(examples.date >= start) & (examples.target_end < validation)]
    valid = examples.loc[(examples.date >= validation) & (examples.target_end < test)]
    held_out = examples.loc[examples.date >= test]
    return {"train": train, "validation": valid, "test": held_out}


def main():
    config = json.loads((ROOT / "configs/data.json").read_text())
    if config["horizon_days"] != 7 or config["history_days"] != 28:
        raise ValueError("Version 1 feature/target names require a 7-day horizon and 28-day history")
    workbook = ROOT / "data/raw/online_retail_II.xlsx"
    print("Reading original workbook (this can take several minutes)...", flush=True)
    sheets = pd.read_excel(workbook, sheet_name=None, engine="openpyxl")
    combined, overlap_audit = combine_sheets(sheets)
    # Exclude the final source day conservatively because capture may be partial.
    last_day = combined.InvoiceDate.max().normalize()
    complete = combined.loc[combined.InvoiceDate < last_day]
    sales, cleaning = clean_sales(complete)
    selected = select_products(sales, config)
    daily = make_daily(sales, selected.StockCode.tolist(), sales.date.min(), last_day - pd.Timedelta(days=1))
    examples = make_examples(daily, config["horizon_days"], config["history_days"])
    splits = split_examples(examples, config)
    destination = ROOT / "data/processed"
    destination.mkdir(parents=True, exist_ok=True)
    daily.to_csv(destination / "daily_sales.csv", index=False)
    selected.to_csv(destination / "selected_products.csv", index=False)
    report = {"config": config, "sheet_overlap_policy": overlap_audit,
              "excluded_final_source_day": str(last_day.date()),
              "excluded_final_source_day_rows": len(combined) - len(complete),
              "cleaning_sequential_counts": cleaning,
              "selected_product_count": len(selected), "daily_rows": len(daily),
              "feature_columns": ["product_id", *FEATURES], "splits": {}}
    for name, split in splits.items():
        if split.empty or split[[*FEATURES, "target_units_7d"]].isna().any().any():
            raise ValueError(f"Empty or incomplete {name} split")
        split.to_csv(destination / f"{name}.csv", index=False)
        report["splits"][name] = {"rows": len(split),
            "first_forecast_date": str(split.date.min().date()),
            "last_forecast_date": str(split.date.max().date()),
            "last_target_date": str(split.target_end.max().date())}
    with workbook.open("rb") as source:
        report["source_sha256"] = hashlib.file_digest(source, "sha256").hexdigest()
    report["output_sha256"] = {}
    for file in sorted(destination.glob("*.csv")):
        with file.open("rb") as source:
            report["output_sha256"][file.name] = hashlib.file_digest(source, "sha256").hexdigest()
    (ROOT / "reports/data-preparation.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
