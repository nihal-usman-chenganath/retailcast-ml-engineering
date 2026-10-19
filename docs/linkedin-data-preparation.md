# LinkedIn milestone draft — data preparation

RetailCast now has a reproducible data-preparation pipeline. It forecasts gross
recorded product sales over the next seven days using UCI Online Retail II.

An issue surfaced before any modeling: the workbook's two sheets overlap in
December 2010. Concatenating them without a source policy would count overlapping
records twice. The pipeline gives the later export precedence for that period,
excluding 22,523 rows from the earlier sheet. This is a documented assumption;
the retailer's original system is not available for reconciliation.

I also separated data quality from task requirements. Missing customer IDs remain
usable for product-level sales, while cancellations and nonpositive quantities
are excluded from this gross-sales target. Identical within-export lines remain
because there is no unique line identifier proving they are ingestion errors.

For leakage prevention:
- Product selection uses only history before the first training forecast.
- Features use days before each forecast cutoff.
- Training, validation, and test periods follow calendar order.
- Seven-day targets cannot cross a split boundary.

The result: 20 selected products with 3,500 training, 1,720 validation, and 1,260
test examples. Twelve preparation tests pass, including a future-sales
perturbation test. Another check reconciled 180 real feature/target windows.

This milestone was implemented with coding-assistant support. Next is
training-only EDA and baseline modeling; no accuracy results yet.

Dataset: Chen, D. (2012), Online Retail II, UCI Machine Learning Repository,
https://doi.org/10.24432/C5CG6D (CC BY 4.0).

#MachineLearning #DataEngineering #TimeSeries #Python #MLOps

## Suggested evidence

- Screenshot the split dates and counts in `reports/data-preparation.json`.
- Include the passing pytest terminal output.
- Explain the July 1 cutoff example from `docs/data-preparation.md`.

Review and adapt this draft before publishing; no post has been published.
