"""Shared serving/preparation arithmetic, independent of downloaded datasets."""

import numpy as np
import pandas as pd

from src.data.prepare import FEATURES, make_examples
from src.features.history import build_history_features


def test_shared_features_equal_independent_historical_window():
    dates = pd.date_range("2011-01-01", periods=80)
    units = np.arange(80) ** 2
    daily = pd.DataFrame({"product_id": "12345", "date": dates, "units": units})
    examples = make_examples(daily).set_index("date")
    shared = build_history_features(daily).set_axis(dates)
    for index in [28, 40, 70]:
        prior = units[index - 28:index]
        assert shared.iloc[index].mean_28 == prior.mean()
        assert np.isclose(shared.iloc[index].std_28, prior.std())
        np.testing.assert_allclose(examples.loc[dates[index], FEATURES].astype(float), shared.iloc[index])
