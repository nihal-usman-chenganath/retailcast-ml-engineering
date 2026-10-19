# Baselines and evaluation plan

This protocol is recorded before fitting or comparing models. No performance
improvement is claimed yet.

## Two forecasts to beat

1. **Previous-week total**: `7 * mean_7`. Repeating each weekday's most recent
   observed sales gives this total over a complete seven-day horizon.
2. **Four-week average**: `7 * mean_28`. This smooths one-week fluctuations using
   the average of the previous four complete weeks' totals.

These baselines need no parameter fitting and use only data available before
the forecast cutoff. If the last seven days total 140 units, the first baseline
predicts 140 units for the next seven days. This is an illustrative calculation,
not an actual RetailCast prediction.

The previous-week forecast can react quickly but repeat unusual orders. The
four-week forecast is smoother but may respond slowly to changes. A learned
model must earn its additional complexity through measured results.

## Candidate learned models

- Regularized linear regression (Ridge), using training-fitted product encoding
  and numeric scaling: simple, inexpensive, and a useful linear reference.
- Random forest regression: captures nonlinear relationships without numeric
  scaling, but uses more memory and is less directly interpretable.

Model pipelines will explicitly select only the documented feature columns.
Dates, history boundaries, target boundaries, and the target itself must not
enter the model. Product IDs must be treated as categories, not numeric quantities.
Any encoding or scaling must be fitted only on training rows.

Use fixed random seeds and a small documented configuration set. Implement and
check baselines before fitting learned models. Keep extreme valid sales in the
initial comparison; do not delete outliers merely to improve scores.

## Metrics and selection

- **MAE**, primary: mean absolute error in units per product/seven-day forecast.
- **RMSE**, secondary: penalizes large misses more heavily, in the same units.
- **R-squared**, context: compares squared error with a constant mean reference;
  it can be negative and does not prove operational value.
- Per-product MAE and sample counts: expose uneven performance hidden by a
  pooled metric. High-volume products can contribute large absolute errors.

Do not use MAPE as the primary measure because zero and near-zero targets make
percentage errors unstable or undefined. Compare all forecasts on exactly the
same rows. Baseline forecasts must also be recorded in MLflow with the same
metrics and data provenance.

Select using validation MAE; retain the baseline if learned models do not beat
it. Resolve numerical ties in favor of the simpler approach. Apply any
nonnegative clipping consistently and record it as part of the model policy.

After choosing the configuration, freeze the decision and record its run ID.
Refit any learned preprocessing and selected estimator on training plus
validation rows, then evaluate once on the reserved test set. Do not choose
models or adjust preprocessing based on test scores. Report the model-selection
validation results separately from the final refitted model's test results.

## Forecast timing and limitations

Evaluation replays a forecast at the start of each day. Earlier observed sales
within validation or test may supply features for later forecasts in that same
period. This is daily rolling-origin evaluation, not a fixed-origin quarterly
forecast. The fitted model remains fixed throughout each evaluated period.

Neighboring examples have overlapping target weeks, so their errors are not
independent. Do not treat the raw row count as independent evidence or compute
ordinary independent-sample confidence intervals. Performance applies to the
selected established products, not new products, all retail businesses, or UAE
retail specifically.

## Next implementation milestone

Implement these baselines, model pipelines, metrics, reproducible training, and
MLflow tracking together. This document defines the protocol; it does not claim
that those components are already implemented.
