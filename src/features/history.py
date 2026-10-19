"""Calendar-aligned features shared by preparation and serving."""

import pandas as pd


def build_history_features(daily, history=28):
    """One product, consecutive daily rows; each feature uses earlier rows only."""
    if history < 7:
        raise ValueError("At least seven history days are required")
    frame = daily.sort_values("date").reset_index(drop=True)
    if frame.date.duplicated().any() or not frame.date.diff().dropna().eq(pd.Timedelta(days=1)).all():
        raise ValueError("Daily input must have unique consecutive calendar dates per product")
    units = frame.units
    past = units.shift(1)
    return pd.DataFrame({
        "lag_1": past, "lag_7": units.shift(7),
        "mean_7": past.rolling(7, min_periods=7).mean(),
        "mean_28": past.rolling(history, min_periods=history).mean(),
        "std_28": past.rolling(history, min_periods=history).std(ddof=0),
        "weekday": frame.date.dt.dayofweek, "month": frame.date.dt.month,
    })
