"""Training-only EDA: aggregate reports and exportable PNG figures.

Run: python -m src.data.eda
Validation and test example files are never opened by this module.
"""

import hashlib
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.data.prepare import FEATURES

ROOT = Path(__file__).resolve().parents[2]
SALES_FEATURES = ["lag_1", "lag_7", "mean_7", "mean_28", "std_28"]
TARGET = "target_units_7d"
BLUE, ORANGE = "#2463A6", "#CB651D"


def load_training_scope(root=ROOT):
    config = json.loads((root / "configs/data.json").read_text())
    preparation = json.loads((root / "reports/data-preparation.json").read_text())
    for name in ["train.csv", "daily_sales.csv"]:
        with (root / "data/processed" / name).open("rb") as source:
            checksum = hashlib.file_digest(source, "sha256").hexdigest()
        if checksum != preparation["output_sha256"][name]:
            raise ValueError(f"{name} changed since preparation; rerun preparation first")
    training = pd.read_csv(root / "data/processed/train.csv", dtype={"product_id": str},
                           parse_dates=["date", "history_end", "target_end"])
    daily = pd.read_csv(root / "data/processed/daily_sales.csv", dtype={"product_id": str},
                        parse_dates=["date"])
    start = pd.Timestamp(config["selection_cutoff"])
    end = pd.Timestamp(config["validation_start"])
    daily = daily.loc[(daily.date >= start) & (daily.date < end)].copy()
    if training.empty or daily.empty:
        raise ValueError("Training scope cannot be empty")
    if not ((training.date >= start) & (training.target_end < end)
            & (training.history_end < training.date)).all():
        raise ValueError("Training examples violate time boundaries")
    if not set(training.product_id) == set(daily.product_id):
        raise ValueError("Training and daily product sets differ")
    numeric = training[[*FEATURES, TARGET]]
    if numeric.isna().any().any() or not np.isfinite(numeric).all().all():
        raise ValueError("Training numeric fields must be finite and complete")
    if (numeric < 0).any().any() or (daily.units < 0).any():
        raise ValueError("Recorded gross sales and derived features cannot be negative")
    if training.duplicated(["product_id", "date"]).any() or daily.duplicated(["product_id", "date"]).any():
        raise ValueError("Duplicate product/date keys")
    return training, daily, preparation


def save_figure(fig, directory, filename):
    # Reserve a footer band so provenance never overlaps axis labels.
    fig.get_layout_engine().set(rect=(0, 0.07, 1, 0.93))
    fig.text(0.01, 0.008, "RetailCast | UCI Online Retail II | Training period only",
             fontsize=8, color="#555555")
    fig.savefig(directory / filename, dpi=170, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def create_figures(training, daily, directory):
    directory.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                         "axes.spines.top": False, "axes.spines.right": False,
                         "axes.titleweight": "bold", "axes.labelcolor": "#333333"})

    totals = daily.groupby("date").units.sum()
    fig, ax = plt.subplots(figsize=(11, 4.8), layout="constrained")
    ax.plot(totals.index, totals.values, color=BLUE, alpha=0.5, linewidth=1,
            label="Recorded units per day")
    ax.plot(totals.index, totals.rolling(7, min_periods=7).mean(), color=ORANGE,
            linewidth=2, label="Trailing 7-day mean")
    ax.set(title="Daily sales across the 20 selected products", ylabel="Gross recorded units",
           xlabel="Training calendar date")
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax.legend(frameon=False)
    ax.grid(axis="y", alpha=0.15)
    save_figure(fig, directory, "training-sales-history.png")

    profiles = daily.groupby("product_id").agg(
        mean_daily_units=("units", "mean"), zero_day_share=("units", lambda s: s.eq(0).mean()))
    profiles = profiles.sort_values("mean_daily_units")
    fig, axes = plt.subplots(1, 2, figsize=(11, 7), layout="constrained", sharey=True)
    positions = np.arange(len(profiles))
    axes[0].barh(positions, profiles.mean_daily_units, color=BLUE)
    axes[0].set_yticks(positions, labels=profiles.index)
    axes[0].set(title="Typical daily volume differs by product", xlabel="Mean recorded units / day",
                ylabel="Product code")
    axes[1].barh(positions, profiles.zero_day_share * 100, color=ORANGE)
    axes[1].set(title="Days with no recorded qualifying sale", xlabel="Zero-sales days (%)")
    for ax in axes:
        ax.grid(axis="x", alpha=0.15)
    save_figure(fig, directory, "training-product-profiles.png")

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6), layout="constrained")
    axes[0].hist(training[TARGET], bins=45, color=BLUE, edgecolor="white")
    axes[0].set(title="Seven-day sales target: original scale", xlabel="Recorded units / seven days",
                ylabel="Forecast examples")
    axes[1].hist(np.log1p(training[TARGET]), bins=40, color=BLUE, edgecolor="white")
    axes[1].set(title="Same target: compressed scale", xlabel="log(1 + recorded units)",
                ylabel="Forecast examples")
    save_figure(fig, directory, "training-target-distribution.png")

    weekday = daily.assign(weekday=daily.date.dt.dayofweek).groupby("weekday").units.mean().reindex(range(7))
    fig, ax = plt.subplots(figsize=(9, 4.6), layout="constrained")
    ax.bar(range(7), weekday, color=BLUE)
    ax.set_xticks(range(7), ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"])
    ax.set(title="Recorded sales by weekday", ylabel="Mean units per product-day",
           xlabel="Calendar weekday (zero-sales days included)")
    ax.grid(axis="y", alpha=0.15)
    save_figure(fig, directory, "training-weekday-pattern.png")

    fig, axes = plt.subplots(2, 3, figsize=(12, 7), layout="constrained")
    for ax, column in zip(axes.flat, SALES_FEATURES):
        ax.hist(np.log1p(training[column]), bins=30, color=BLUE, edgecolor="white")
        ax.set(title=column, xlabel=f"log(1 + {column})", ylabel="Forecast examples")
    axes.flat[-1].scatter(np.log1p(training.mean_28), np.log1p(training[TARGET]),
                          s=8, alpha=0.15, color=BLUE, edgecolors="none")
    axes.flat[-1].set(title="Past volume versus future sales", xlabel="log(1 + preceding 28-day mean)",
                      ylabel="log(1 + seven-day target)")
    save_figure(fig, directory, "training-feature-distributions.png")

    correlation = training[[*SALES_FEATURES, TARGET]].corr(method="spearman")
    fig, ax = plt.subplots(figsize=(8, 6.3), layout="constrained")
    matrix = ax.imshow(correlation, cmap="RdBu_r", vmin=-1, vmax=1)
    ax.set_xticks(range(len(correlation)), correlation.columns, rotation=35, ha="right")
    ax.set_yticks(range(len(correlation)), correlation.index)
    ax.set_title("Rank correlations among sales features and target")
    for i in range(len(correlation)):
        for j in range(len(correlation)):
            value = correlation.iloc[i, j]
            ax.text(j, i, f"{value:.2f}", ha="center", va="center",
                    color="white" if abs(value) > 0.65 else "#222222")
    fig.colorbar(matrix, ax=ax, label="Spearman correlation")
    save_figure(fig, directory, "training-correlations.png")
    return profiles, weekday, correlation


def main():
    training, daily, preparation = load_training_scope()
    figures = ROOT / "reports/figures"
    profiles, weekday, correlation = create_figures(training, daily, figures)
    target = training[TARGET]
    per_product_outliers = {}
    for product, group in training.groupby("product_id"):
        q1, q3 = group[TARGET].quantile([0.25, 0.75])
        upper = float(q3 + 1.5 * (q3 - q1))
        per_product_outliers[product] = {"upper_iqr_fence": upper,
            "examples_above_upper_fence": int((group[TARGET] > upper).sum())}
    quantiles = target.quantile([0, .25, .5, .75, .9, .95, .99, 1])
    report = {
        "scope": "Training outcomes only; validation/test example files not read",
        "training_examples": len(training), "daily_product_rows": len(daily),
        "daily_start": str(daily.date.min().date()), "daily_end": str(daily.date.max().date()),
        "product_count": int(training.product_id.nunique()),
        "training_missing_values": {k: int(v) for k, v in training.isna().sum().items()},
        "target_quantiles": {str(q): float(v) for q, v in quantiles.items()},
        "target_mean": float(target.mean()), "zero_target_share": float(target.eq(0).mean()),
        "zero_daily_sales_share": float(daily.units.eq(0).mean()),
        "training_recorded_units": int(daily.units.sum()),
        "daily_max_units_single_product": int(daily.units.max()),
        "per_product": profiles.to_dict(orient="index"),
        "weekday_mean_product_day_units": {str(k): float(v) for k, v in weekday.items()},
        "spearman_correlations": correlation.to_dict(),
        "per_product_target_outlier_flags": per_product_outliers,
        "outlier_policy": "Diagnostic only; no clipping or removal performed",
        "inputs_sha256": {name: preparation["output_sha256"][name]
                          for name in ["train.csv", "daily_sales.csv"]},
        "figures": [file.relative_to(ROOT).as_posix() for file in sorted(figures.glob("training-*.png"))],
    }
    (ROOT / "reports/training-eda.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: report[k] for k in ["training_examples", "daily_product_rows", "product_count",
          "target_quantiles", "target_mean", "zero_target_share", "zero_daily_sales_share",
          "training_recorded_units", "daily_max_units_single_product", "weekday_mean_product_day_units",
          "figures"]}, indent=2))


if __name__ == "__main__":
    main()
