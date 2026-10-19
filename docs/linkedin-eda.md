# LinkedIn draft — what training-data exploration changed

Before fitting RetailCast's first forecasting model, I explored only the
training period and recorded the comparison protocol.

Across 20 selected products from January–June 2011:
- 47.02% of product-days had no recorded qualifying sale.
- The median seven-day sales target was 223 units; the maximum was 4,562.
- 514 of 3,500 weekly targets were zero.

These findings affect evaluation choices. Ordinary percentage errors are awkward
with zero targets, so MAE will be the main comparison metric. RMSE will help
expose large misses. Per-product errors will show which items the overall score
may hide.

The selection was made using pre-2011 sales. Some of those previously active
products have very low training-period sales, and I'm keeping them in scope
rather than removing harder cases after seeing their outcomes.

The first forecasts to compare will be simple: last week's recorded total and
an average based on the preceding four weeks. Ridge and random forest models
will need to demonstrate value beyond those references.

With coding-assistant support, I created six charts and added checks that reject
training targets crossing the validation boundary or prepared files that no
longer match their recorded checksums. All 15 current tests pass.

No model accuracy is claimed yet. A correlation in the training data does not
establish improvement on future forecasts.

Source: Chen, D. (2012), Online Retail II, UCI Machine Learning Repository,
https://doi.org/10.24432/C5CG6D (CC BY 4.0).

#MachineLearning #TimeSeries #DataScience #Python #MLOps

## Sharing notes

- Suggested screenshot: `reports/figures/training-target-distribution.png`.
- Main concept: choose a meaningful evaluation protocol before comparing models.
- Technical challenge: prevent future daily records from entering EDA when the
  prepared daily file spans all periods; filter at the training calendar boundary
  and test that extreme future values cannot enter training summaries.
- Review and adapt before publishing. Nothing has been posted automatically.
