"""Two-stage experiment workflow: compare on validation, then finalize once.

python -m src.models.train compare
python -m src.models.train finalize
"""

import argparse
import hashlib
import json
import platform
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

import joblib
import mlflow
import numpy as np
import pandas as pd
import sklearn

from src.models.estimators import MODEL_FEATURES, TARGET, build_model, validate_features
from src.models.metrics import per_product_metrics, regression_metrics

ROOT = Path(__file__).resolve().parents[2]


def checksum(path):
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def source_fingerprint():
    paths = [*sorted((ROOT / "src/models").glob("*.py")),
             ROOT / "src/data/prepare.py", ROOT / "configs/data.json",
             ROOT / "configs/training.json", ROOT / "requirements.txt"]
    return {path.relative_to(ROOT).as_posix(): checksum(path) for path in paths}


def load_split(name, preparation):
    path = ROOT / "data/processed" / f"{name}.csv"
    if checksum(path) != preparation["output_sha256"][path.name]:
        raise ValueError(f"{name} input checksum does not match preparation")
    frame = pd.read_csv(path, dtype={"product_id": str},
                        parse_dates=["date", "history_end", "target_end"])
    validate_features(frame.loc[:, MODEL_FEATURES])
    if frame.duplicated(["product_id", "date"]).any():
        raise ValueError(f"Duplicate {name} product/date keys")
    if not (frame.history_end < frame.date).all():
        raise ValueError(f"Invalid {name} historical cutoff")
    if not ((frame.target_end - frame.date).dt.days == 6).all():
        raise ValueError(f"Invalid {name} target horizon")
    if not np.isfinite(frame[TARGET]).all() or (frame[TARGET] < 0).any():
        raise ValueError(f"Invalid {name} targets")
    expected = preparation["splits"][name]
    if len(frame) != expected["rows"] or str(frame.date.min().date()) != expected["first_forecast_date"]:
        raise ValueError(f"Unexpected {name} row count or first date")
    if str(frame.date.max().date()) != expected["last_forecast_date"] or str(frame.target_end.max().date()) != expected["last_target_date"]:
        raise ValueError(f"Unexpected {name} date boundary")
    return frame


def configure_tracking(config):
    uri = "sqlite:///" + (ROOT / "mlflow.db").as_posix()
    mlflow.set_tracking_uri(uri)
    name = config["experiment_name"]
    experiment = mlflow.get_experiment_by_name(name)
    if experiment is None:
        experiment_id = mlflow.create_experiment(name, artifact_location=(ROOT / "mlartifacts").as_uri())
    else:
        experiment_id = experiment.experiment_id
    mlflow.set_experiment(experiment_id=experiment_id)
    return uri


def log_provenance(config, preparation):
    try:
        revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
        dirty = bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip())
    except (OSError, subprocess.CalledProcessError):
        revision, dirty = "unavailable", True
    mlflow.set_tags({"git_revision": revision, "git_dirty": str(dirty),
                     "target": "seven_day_gross_recorded_units", "evaluation": "daily_rolling_origin",
                     "selection_metric": config["selection_metric"],
                     "source_sha256": preparation["source_sha256"]})
    mlflow.log_params({"seed": config["seed"], "prediction_floor": 0,
                       "python_version": platform.python_version(),
                       "sklearn_version": sklearn.__version__,
                       "features": ",".join(MODEL_FEATURES)})
    mlflow.log_dict(source_fingerprint(), "provenance/source_checksums.json")
    mlflow.log_artifact(str(ROOT / "configs/training.json"), "provenance")
    mlflow.log_artifact(str(ROOT / "configs/data.json"), "provenance")
    mlflow.log_artifact(str(ROOT / "reports/data-preparation.json"), "provenance")
    mlflow.log_artifact(str(ROOT / "requirements.txt"), "provenance")


def log_metrics(prefix, values):
    mlflow.log_metrics({f"{prefix}_{key}": value for key, value in values.items() if value is not None})


def select_winner(results):
    if not results or any(not np.isfinite(row["validation"]["mae"]) for row in results):
        raise ValueError("Selection requires finite validation scores")
    best = min(row["validation"]["mae"] for row in results)
    # Configuration order ranks simpler candidates first for numerical ties.
    return next(row for row in results if np.isclose(row["validation"]["mae"], best,
                                                    rtol=1e-12, atol=1e-10))


def compare(config, preparation):
    if (ROOT / "models/final/test_evaluation_started.json").exists():
        raise FileExistsError("Test evaluation already started; do not retune against this held-out test")
    train = load_split("train", preparation)
    validation = load_split("validation", preparation)
    if train.target_end.max() >= validation.date.min():
        raise ValueError("Training targets overlap validation forecast origins")
    results = []
    for candidate in config["candidates"]:
        print(f"Comparing {candidate['name']}...", flush=True)
        folder = ROOT / "models/candidates" / candidate["name"]
        folder.mkdir(parents=True, exist_ok=True)
        with mlflow.start_run(run_name=candidate["name"], tags={"phase": "validation_comparison"}) as run:
            log_provenance(config, preparation)
            mlflow.log_params({**candidate, "train_rows": len(train), "validation_rows": len(validation)})
            model = build_model(candidate, config["seed"])
            start = time.perf_counter()
            model.fit(train[MODEL_FEATURES], train[TARGET])
            fit_seconds = time.perf_counter() - start
            train_predictions = model.predict(train[MODEL_FEATURES])
            start = time.perf_counter()
            predictions = model.predict(validation[MODEL_FEATURES])
            prediction_seconds = time.perf_counter() - start
            training_metrics = regression_metrics(train[TARGET], train_predictions)
            validation_metrics = regression_metrics(validation[TARGET], predictions)
            row = {"name": candidate["name"], "candidate": candidate, "run_id": run.info.run_id,
                   "train": training_metrics, "validation": validation_metrics,
                   "fit_seconds": fit_seconds, "validation_batch_prediction_seconds": prediction_seconds}
            log_metrics("train", training_metrics)
            log_metrics("validation", validation_metrics)
            mlflow.log_metrics({"fit_seconds": fit_seconds, "validation_batch_prediction_seconds": prediction_seconds})
            joblib.dump(model, folder / "model.joblib")
            reloaded = joblib.load(folder / "model.joblib")  # Own, locally generated trusted artifact.
            np.testing.assert_allclose(reloaded.predict(validation[MODEL_FEATURES]), predictions, rtol=1e-12, atol=1e-12)
            write_json(folder / "metrics.json", row)
            write_json(folder / "validation_by_product.json",
                       per_product_metrics(validation.product_id, validation[TARGET], predictions))
            mlflow.log_artifacts(str(folder), artifact_path="model_and_evaluation")
            results.append(row)
    winner = select_winner(results)
    selection = {"selected_name": winner["name"], "selected_candidate": winner["candidate"],
                 "selected_run_id": winner["run_id"], "selection_metric": "validation_mae",
                 "selected_validation_metrics": winner["validation"],
                 "comparison": results, "source_checksums": source_fingerprint(),
                 "preparation_report_sha256": checksum(ROOT / "reports/data-preparation.json"),
                 "selection_frozen_at_utc": datetime.now(timezone.utc).isoformat(),
                 "test_used_for_selection": False}
    write_json(ROOT / "models/selection.json", selection)
    write_json(ROOT / "reports/model-comparison.json", selection)
    print(json.dumps({"selected": winner["name"], "validation": winner["validation"]}, indent=2))


def finalize(config, preparation):
    folder = ROOT / "models/final"
    marker = folder / "test_evaluation_started.json"
    if marker.exists():
        raise FileExistsError("Final test evaluation already started; results must not drive retuning")
    selection = json.loads((ROOT / "models/selection.json").read_text())
    if source_fingerprint() != selection["source_checksums"]:
        raise ValueError("Training code/configuration changed after selection; compare again before test access")
    if checksum(ROOT / "reports/data-preparation.json") != selection["preparation_report_sha256"]:
        raise ValueError("Prepared data changed after selection")
    train, validation = load_split("train", preparation), load_split("validation", preparation)
    development = pd.concat([train, validation], ignore_index=True)
    model = build_model(selection["selected_candidate"], config["seed"])
    with mlflow.start_run(run_name="final-" + selection["selected_name"], tags={"phase": "final_test"}) as run:
        log_provenance(config, preparation)
        mlflow.set_tag("selection_run_id", selection["selected_run_id"])
        mlflow.log_params({**selection["selected_candidate"], "development_rows": len(development)})
        model.fit(development[MODEL_FEATURES], development[TARGET])
        folder.mkdir(parents=True, exist_ok=True)
        model_path = folder / "model.joblib"
        joblib.dump(model, model_path)
        reloaded = joblib.load(model_path)
        np.testing.assert_allclose(reloaded.predict(validation[MODEL_FEATURES]),
                                   model.predict(validation[MODEL_FEATURES]), rtol=1e-12, atol=1e-12)
        # Freeze this event BEFORE any test example file is opened.
        write_json(marker, {"run_id": run.info.run_id, "selection_run_id": selection["selected_run_id"],
                            "started_at_utc": datetime.now(timezone.utc).isoformat()})
        test = load_split("test", preparation)
        if development.target_end.max() >= test.date.min():
            raise ValueError("Development targets overlap test forecast origins")
        predictions = reloaded.predict(test[MODEL_FEATURES])
        metrics = regression_metrics(test[TARGET], predictions)
        metadata = {"model_name": selection["selected_name"], "model_version": run.info.run_id,
                    "selection_run_id": selection["selected_run_id"], "model_sha256": checksum(model_path),
                    "features": MODEL_FEATURES, "product_ids": model.product_ids_,
                    "target": "gross_recorded_units_next_7_calendar_days",
                    "forecast_cutoff": "start of forecast date; source timestamps as recorded",
                    "prediction_floor": 0, "history_days": 28, "horizon_days": 7,
                    "python_version": platform.python_version(), "sklearn_version": sklearn.__version__,
                    "joblib_version": joblib.__version__, "source_checksums": selection["source_checksums"],
                    "data_checksums": preparation["output_sha256"],
                    "development_rows": len(development), "test_rows": len(test),
                    "development_target_end": str(development.target_end.max().date()),
                    "test_first_forecast": str(test.date.min().date()),
                    "test_last_forecast": str(test.date.max().date()),
                    "validation_metrics_before_refit": selection["selected_validation_metrics"],
                    "test_metrics": metrics}
        log_metrics("test", metrics)
        log_metrics("development_fit", regression_metrics(development[TARGET], model.predict(development[MODEL_FEATURES])))
        write_json(folder / "metadata.json", metadata)
        by_product = per_product_metrics(test.product_id, test[TARGET], predictions)
        write_json(folder / "test_by_product.json", by_product)
        write_json(ROOT / "reports/final-evaluation.json", {**metadata, "test_by_product": by_product})
        prediction_rows = test[["product_id", "date", TARGET]].copy()
        prediction_rows["predicted_units_7d"] = predictions
        prediction_rows.to_csv(folder / "test_predictions.csv", index=False)
        mlflow.log_artifacts(str(folder), artifact_path="model_and_evaluation")
        print(json.dumps({"selected": selection["selected_name"], "final_run_id": run.info.run_id,
                          "test": metrics}, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=["compare", "finalize"])
    args = parser.parse_args()
    config = json.loads((ROOT / "configs/training.json").read_text())
    if config["selection_metric"] != "validation_mae" or not config["clip_predictions_at_zero"]:
        raise ValueError("Version 1 requires validation MAE selection and nonnegative clipping")
    preparation = json.loads((ROOT / "reports/data-preparation.json").read_text())
    configure_tracking(config)
    (compare if args.stage == "compare" else finalize)(config, preparation)


if __name__ == "__main__":
    main()
