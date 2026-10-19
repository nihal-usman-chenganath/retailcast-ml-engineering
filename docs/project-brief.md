# Project brief

## Business question

Using only information available at a forecast cutoff, how many units of a
selected product will be sold during the next seven calendar days?

The potential user is a retail operations analyst investigating sales forecasts
as one input to inventory planning. Inventory improvements are not measured by
this project unless a separate evaluation is added.

## Proposed data source

- Dataset: UCI Online Retail II.
- Source: https://archive.ics.uci.edu/dataset/502/online+retail+ii
- Attribution: Chen, D. (2012). Online Retail II [Dataset]. UCI Machine Learning
  Repository. https://doi.org/10.24432/C5CG6D.
- License listed by UCI: Creative Commons Attribution 4.0 International.
- UCI reports 1,067,371 transaction records spanning December 2009 to December
  2011 from a UK online retailer. These are source descriptions, not locally
  verified statistics in this brief. The workbook has now been downloaded and
  inspected; see `../reports/data-discovery.json` for measured statistics.

## Proposed first version

- Select a small set of products with sufficient history after inspecting data.
- Define a cutoff as the start of a calendar day; features use earlier records.
- Predict recorded units sold over that day and the following six days.
- Forecast gross recorded merchandise units; see `data-preparation.md` for the
  implemented exclusion rules and zero-recorded-sales assumption.
- Use chronological splits and separate target windows across split boundaries.
- Compare a simple historical-sales baseline with at least two appropriate ML
  algorithms. Final models and metrics will be chosen before experimentation.
- Demonstrate historical forecast replay, not a live connection to a retailer.
- Expose GET /health, GET /model-info, and POST /predict after training works.

## Important limitations

Recorded sales are not true demand: stock availability and unmet demand are not
observed. Historical UK transactions do not establish performance for UAE retail.
Raw transaction counts are not the number of usable forecasting examples.
No accuracy, latency, deployment, or cost claims have been established.

## Phase 1 acceptance criteria

1. Confirm the prediction question and explain the sales-versus-demand distinction.
2. Verify a compatible Python environment and Git installation.
3. Inspect the original dataset and document its schema and quality concerns.
4. Finalize scope and data definitions before model implementation.

## Implemented preparation scope

The initial implementation selects 20 established products using pre-2011
history only. Chronological examples are prepared for January–June 2011 training,
July–September validation, and October–December testing, with target-window
separation and incomplete final windows excluded. No model has been fitted.
