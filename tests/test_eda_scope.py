"""Guard training-only EDA from future outcomes and stale inputs."""

import hashlib
import json

import pandas as pd
import pytest

from src.data.eda import load_training_scope
from src.data.prepare import make_examples


def write_fixture(root, leak_target=False):
    (root / "configs").mkdir()
    (root / "reports").mkdir()
    processed = root / "data/processed"
    processed.mkdir(parents=True)
    (root / "configs/data.json").write_text(json.dumps({"selection_cutoff": "2011-01-01",
                                                       "validation_start": "2011-03-01"}))
    daily = pd.DataFrame({"product_id": "12345",
                          "date": pd.date_range("2010-12-01", "2011-03-10"),
                          "units": 10, "transaction_lines": 1})
    examples = make_examples(daily)
    train = examples.loc[(examples.date >= "2011-01-01") & (examples.target_end < "2011-03-01")].copy()
    if leak_target:
        train.loc[train.index[-1], "target_end"] = pd.Timestamp("2011-03-01")
    train.to_csv(processed / "train.csv", index=False)
    # Extremely large future sales must not enter daily training summaries.
    daily.loc[daily.date >= "2011-03-01", "units"] = 999999
    daily.to_csv(processed / "daily_sales.csv", index=False)
    (processed / "test.csv").write_text("not a valid forecasting dataset")
    (processed / "validation.csv").write_text("not a valid forecasting dataset")
    checksums = {}
    for name in ["train.csv", "daily_sales.csv"]:
        with (processed / name).open("rb") as source:
            checksums[name] = hashlib.file_digest(source, "sha256").hexdigest()
    (root / "reports/data-preparation.json").write_text(json.dumps({"output_sha256": checksums}))


def test_eda_excludes_future_daily_outcomes_and_does_not_open_holdouts(tmp_path):
    write_fixture(tmp_path)
    training, daily, _ = load_training_scope(tmp_path)
    assert daily.date.min() == pd.Timestamp("2011-01-01")
    assert daily.date.max() == pd.Timestamp("2011-02-28")
    assert daily.units.max() == 10
    assert len(training) > 0


def test_eda_rejects_target_crossing_training_boundary(tmp_path):
    write_fixture(tmp_path, leak_target=True)
    with pytest.raises(ValueError, match="time boundaries"):
        load_training_scope(tmp_path)


def test_eda_rejects_modified_prepared_data(tmp_path):
    write_fixture(tmp_path)
    with (tmp_path / "data/processed/train.csv").open("a") as output:
        output.write("\n")
    with pytest.raises(ValueError, match="changed since preparation"):
        load_training_scope(tmp_path)
