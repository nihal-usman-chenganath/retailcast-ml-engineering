"""Tests of business rules and time boundaries, using tiny synthetic fixtures.

The fixtures are test inputs, not portfolio data or experimental results.
"""

import numpy as np
import pandas as pd
import pytest

from src.data.prepare import (
    FEATURES, clean_sales, combine_sheets, make_daily, make_examples,
    select_products, split_examples, validate,
)


def transactions():
    return pd.DataFrame({
        "Invoice": ["100", "100", "C101", "102", "103", "104"],
        "StockCode": ["12345"] * 5 + ["POST"],
        "Description": [None] * 6,
        "Quantity": [2, 2, -2, -1, 1, 1],
        "InvoiceDate": pd.to_datetime(["2010-12-01"] * 6),
        "Price": [1, 1, 1, 1, 0, 1],
        "Customer ID": [None] * 6,
        "Country": ["United Kingdom"] * 6,
    })


def daily_series():
    return pd.DataFrame({"product_id": "12345",
                         "date": pd.date_range("2011-01-01", periods=120),
                         "units": np.arange(120), "transaction_lines": 1})


def test_cleaning_preserves_missing_customers_and_within_sheet_duplicates():
    cleaned, audit = clean_sales(transactions())
    assert cleaned.Quantity.tolist() == [2, 2]
    assert cleaned["Customer ID"].isna().all()
    assert audit["retained_exact_duplicates_beyond_first"] == 1
    exclusions = sum(v for k, v in audit.items() if k.startswith("excluded_"))
    assert audit["input_rows"] == exclusions + audit["retained_rows"]


@pytest.mark.parametrize("column,value", [("Quantity", np.inf), ("Price", "bad"),
                                          ("Quantity", 1.5), ("StockCode", "")])
def test_invalid_source_values_fail_loudly(column, value):
    frame = transactions().astype({"Quantity": "object", "Price": "object"})
    frame.loc[0, column] = value
    with pytest.raises((ValueError, TypeError)):
        validate(frame)


def test_later_export_owns_overlap_without_dropping_earlier_history():
    old = transactions().iloc[:2].copy()
    old.loc[0, "InvoiceDate"] = pd.Timestamp("2010-11-30")
    newer = transactions().iloc[:2].copy()
    result, audit = combine_sheets({"older": old, "newer": newer})
    assert len(result) == 3
    assert audit[0]["overlap_rows_excluded"] == 1
    assert int((result.InvoiceDate == pd.Timestamp("2010-12-01")).sum()) == 2


def test_no_record_day_is_zero_recorded_sales():
    sales, _ = clean_sales(transactions())
    daily = make_daily(sales, ["12345"], "2010-12-01", "2010-12-02")
    assert daily.units.tolist() == [4, 0]
    assert daily.transaction_lines.tolist() == [2, 0]


def test_feature_and_target_windows_are_correct():
    examples = make_examples(daily_series())
    first = examples.iloc[0]
    assert first.date == pd.Timestamp("2011-01-29")
    assert first.lag_1 == 27
    assert first.lag_7 == 21
    assert first.mean_7 == np.mean(np.arange(21, 28))
    assert first.mean_28 == 13.5
    assert first.target_units_7d == sum(range(28, 35))
    assert first.history_end < first.date
    assert "units" not in examples.columns
    assert examples.iloc[-1].target_end == pd.Timestamp("2011-04-30")


def test_current_and_future_sales_cannot_change_current_features():
    daily = daily_series()
    cutoff = pd.Timestamp("2011-02-15")
    before = make_examples(daily).set_index("date")
    daily.loc[daily.date >= cutoff, "units"] = 99999
    after = make_examples(daily).set_index("date")
    pd.testing.assert_series_equal(before.loc[cutoff, FEATURES], after.loc[cutoff, FEATURES])
    assert before.loc[cutoff, "target_units_7d"] != after.loc[cutoff, "target_units_7d"]


def test_product_selection_ignores_future_best_seller():
    sales = pd.DataFrame({"StockCode": ["12345", "67890", "67890"],
                          "date": pd.to_datetime(["2010-12-01", "2010-12-01", "2011-01-02"]),
                          "Quantity": [10, 1, 1000000]})
    config = {"selection_cutoff": "2011-01-01", "selection_lookback_days": 90,
              "minimum_active_days": 1, "number_of_products": 1}
    assert select_products(sales, config).StockCode.tolist() == ["12345"]


def test_split_target_windows_do_not_cross_boundaries():
    config = {"selection_cutoff": "2011-01-29", "validation_start": "2011-03-01",
              "test_start": "2011-04-01"}
    splits = split_examples(make_examples(daily_series()), config)
    assert splits["train"].target_end.max() < splits["validation"].date.min()
    assert splits["validation"].target_end.max() < splits["test"].date.min()
    assert splits["train"].date.max() == pd.Timestamp("2011-02-22")
    assert splits["validation"].date.max() == pd.Timestamp("2011-03-25")


def test_missing_calendar_days_rejected_before_rolling_features():
    with pytest.raises(ValueError, match="consecutive"):
        make_examples(daily_series().drop(index=40))
