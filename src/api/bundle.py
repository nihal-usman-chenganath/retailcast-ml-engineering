"""Create a minimal local serving bundle; --fixture is ONLY for CI mechanics."""

import argparse
import json
import platform
import shutil
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn

from src.api.service import sha256
from src.models.estimators import MODEL_FEATURES, build_model

ROOT = Path(__file__).resolve().parents[2]


def export_bundle(destination, fixture=False):
    destination = Path(destination)
    if fixture and (destination / "metadata.json").exists():
        raise FileExistsError("Refusing to overwrite an existing bundle with a test fixture")
    destination.mkdir(parents=True, exist_ok=True)
    if fixture:
        history = pd.DataFrame({"product_id": "12345",
            "date": pd.date_range("2011-01-01", "2011-04-30"), "units": 1})
        features = pd.DataFrame({"product_id": ["12345"], "lag_1": [1], "lag_7": [1],
            "mean_7": [1], "mean_28": [1], "std_28": [0], "weekday": [0], "month": [1]})
        model = build_model({"kind": "baseline", "window": 7}).fit(features, np.array([7]))
        joblib.dump(model, destination / "model.joblib")
        metadata = {"model_name": "synthetic_ci_fixture", "model_version": "ci-fixture",
            "mode": "synthetic_ci_fixture", "features": MODEL_FEATURES, "product_ids": ["12345"],
            "history_days": 28, "horizon_days": 7, "development_target_end": "2011-01-31",
            "python_version": platform.python_version(), "sklearn_version": sklearn.__version__,
            "joblib_version": joblib.__version__, "target": "synthetic_ci_test_only"}
    else:
        source = ROOT / "models/final"
        metadata = json.loads((source / "metadata.json").read_text())
        if sha256(source / "model.joblib") != metadata["model_sha256"]:
            raise ValueError("Final model checksum mismatch")
        for name in ["daily_sales.csv", "train.csv"]:
            if sha256(ROOT / "data/processed" / name) != metadata["data_checksums"][name]:
                raise ValueError(f"Prepared {name} checksum mismatch")
        shutil.copyfile(source / "model.joblib", destination / "model.joblib")
        history = pd.read_csv(ROOT / "data/processed/daily_sales.csv", dtype={"product_id": str},
                              parse_dates=["date"])[["product_id", "date", "units"]]
        training = pd.read_csv(ROOT / "data/processed/train.csv")
        metadata["mode"] = "historical_replay"
        metadata["training_feature_ranges"] = {name: {"min": float(training[name].min()),
            "max": float(training[name].max())} for name in ["lag_1", "lag_7", "mean_7", "mean_28", "std_28"]}
    history.to_csv(destination / "history.csv", index=False)
    metadata["model_sha256"] = sha256(destination / "model.joblib")
    metadata["history_sha256"] = sha256(destination / "history.csv")
    (destination / "metadata.json").write_text(json.dumps(metadata, indent=2, allow_nan=False) + "\n")
    print(f"Created {metadata['mode']} bundle at {destination}")
    return metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "serving_bundle")
    parser.add_argument("--fixture", action="store_true", help="Synthetic CI fixture; no real model metrics")
    args = parser.parse_args()
    export_bundle(args.output, args.fixture)


if __name__ == "__main__":
    main()
