"""Plot saved experiment outputs without retraining or selecting a model."""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def save(fig, path, footer):
    fig.get_layout_engine().set(rect=(0, .07, 1, .93))
    fig.text(.01, .008, footer, fontsize=8, color="#555555")
    fig.savefig(path, dpi=170, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def main():
    comparison = json.loads((ROOT / "reports/model-comparison.json").read_text())
    final = json.loads((ROOT / "reports/final-evaluation.json").read_text())
    figures = ROOT / "reports/figures"
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                         "axes.spines.top": False, "axes.spines.right": False,
                         "axes.titleweight": "bold"})
    rows = comparison["comparison"]
    labels = [row["name"].replace("_", " ") for row in rows]
    colors = ["#CB651D" if row["name"] == comparison["selected_name"] else "#2463A6" for row in rows]
    fig, axes = plt.subplots(1, 3, figsize=(13, 5), layout="constrained")
    for ax, metric in zip(axes, ["mae", "rmse", "r2"]):
        scores = [row["validation"][metric] for row in rows]
        bars = ax.barh(np.arange(len(rows)), scores, color=colors)
        ax.set_yticks(np.arange(len(rows)), labels if metric == "mae" else [""] * len(rows))
        ax.invert_yaxis()
        ax.bar_label(bars, fmt="%.2f", padding=4, fontsize=9)
        ax.set_title(metric.upper() + (" (lower is better)" if metric != "r2" else " (higher is better)"))
        ax.set_xlabel("Units / seven-day forecast" if metric != "r2" else "R-squared")
        if metric != "r2":
            ax.set_xlim(0, max(scores) * 1.25)
        else:
            ax.set_xlim(min(0, min(scores) - .15), max(1, max(scores) + .15))
        ax.grid(axis="x", alpha=.15)
    save(fig, figures / "validation-model-comparison.png",
         "RetailCast | Same 1,720 validation examples | Orange: selected by MAE | UCI Online Retail II")

    predictions = pd.read_csv(ROOT / "models/final/test_predictions.csv", parse_dates=["date"])
    totals = predictions.groupby("date")[["target_units_7d", "predicted_units_7d"]].sum()
    fig, ax = plt.subplots(figsize=(11, 5), layout="constrained")
    ax.plot(totals.index, totals.target_units_7d, color="#2463A6", linewidth=2, label="Recorded target")
    ax.plot(totals.index, totals.predicted_units_7d, color="#CB651D", linewidth=2, label="Selected model forecast")
    ax.set(title="Final model: seven-day totals across 20 products", xlabel="Forecast start date",
           ylabel="Units across products over the next seven days")
    ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b %Y"))
    ax.legend(frameon=False)
    ax.grid(axis="y", alpha=.15)
    save(fig, figures / "test-forecast-history.png",
         "RetailCast | Held-out test after selection/refit | Adjacent target weeks overlap | UCI Online Retail II")

    products = pd.DataFrame(final["test_by_product"]).sort_values("mae")
    fig, ax = plt.subplots(figsize=(10, 7), layout="constrained")
    bars = ax.barh(products.product_id, products.mae, color="#2463A6")
    ax.bar_label(bars, fmt="%.1f", padding=3, fontsize=9)
    ax.set_xlim(0, products.mae.max() * 1.15)
    ax.set(title="Final model: errors differ across products", xlabel="Test MAE (units / seven-day forecast)",
           ylabel="Product code")
    ax.grid(axis="x", alpha=.15)
    save(fig, figures / "test-product-errors.png",
         "RetailCast | 63 test forecasts per product | Gross recorded sales, not unmet demand | UCI Online Retail II")
    print("Created validation comparison, test forecast history, and per-product test-error charts.")


if __name__ == "__main__":
    main()
