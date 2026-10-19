"""Offline feature-distribution diagnostic, not a retraining trigger."""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

FEATURES = ["lag_1", "lag_7", "mean_7", "mean_28", "std_28"]


def population_stability_index(reference, current, bins=10):
    reference, current = np.asarray(reference, dtype=float), np.asarray(current, dtype=float)
    if not len(reference) or not len(current) or not np.isfinite(reference).all() or not np.isfinite(current).all():
        raise ValueError("PSI requires nonempty finite reference/current samples")
    internal = np.unique(np.quantile(reference, np.linspace(0, 1, bins + 1)[1:-1]))
    edges = np.r_[-np.inf, internal, np.inf]
    expected = np.histogram(reference, bins=edges)[0].astype(float) + .5
    observed = np.histogram(current, bins=edges)[0].astype(float) + .5
    expected /= expected.sum()
    observed /= observed.sum()
    return float(np.sum((observed - expected) * np.log(observed / expected)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", type=Path, default=Path("data/processed/train.csv"))
    parser.add_argument("--current", type=Path, default=Path("data/processed/test.csv"))
    parser.add_argument("--output", type=Path, default=Path("reports/feature-drift.json"))
    args = parser.parse_args()
    # Read only predictors; test outcomes never enter this diagnostic.
    reference = pd.read_csv(args.reference, usecols=FEATURES)
    current = pd.read_csv(args.current, usecols=FEATURES)
    result = {"scope": "Offline pooled feature comparison after final evaluation; not model tuning",
              "reference": args.reference.as_posix(), "current": args.current.as_posix(),
              "reference_rows": len(reference), "current_rows": len(current),
              "method": "PSI using training quantile bins and 0.5-count smoothing",
              "limitations": ["Not a statistical significance test", "Pooled products can obscure product-specific shifts",
                "Overlapping windows create dependent samples", "No automatic retraining or causal explanation"],
              "features": {}}
    for column in FEATURES:
        result["features"][column] = {"psi": population_stability_index(reference[column], current[column]),
            "reference_mean": float(reference[column].mean()), "current_mean": float(current[column].mean()),
            "current_outside_reference_range_fraction": float(((current[column] < reference[column].min()) |
                (current[column] > reference[column].max())).mean())}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
