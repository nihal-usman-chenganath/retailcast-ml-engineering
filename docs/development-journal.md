# Development journal

## 2026-10-19 — Topic selection and initial environment inspection

- Selected RetailCast as a separate project from GreenSupply AI.
- Chose next-seven-day recorded product sales as the proposed prediction task.
- Identified UCI Online Retail II as the proposed public dataset.
- Confirmed the workspace was empty at initial inspection.
- Verified Python 3.14.3 and Git 2.53.0.windows.1 are available.
- Found an existing Python 3.11.9 installation, created `.venv` with it, and
  verified that its interpreter uses an isolated virtual environment.
- Created the project brief, starter README, journal, and ignore rules with
  coding-assistant support. The learner has not yet confirmed this checkpoint.
- No data downloaded, model trained, API implemented, or tests run yet.

### Learning checkpoint

Why can transaction history support a recorded-sales forecast without revealing
how many customers wanted to buy an item that was out of stock?

### Next steps

Confirm the learner can run the environment check, then inspect the dataset.
Capture a VS Code screenshot of the project brief for the discovery milestone.
Prepare the first LinkedIn post after the initial data inspection confirms scope.

## 2026-10-19 — Original dataset downloaded and inspected

- Installed pinned discovery dependencies in `.venv`; `pip check` found no
  broken requirements.
- Added and executed `scripts/inspect_data.py` against the original UCI workbook.
- Confirmed 1,067,371 transaction rows across two sheets and eight columns.
- Saved aggregate quality counts, timestamps, schema, and the workbook checksum
  in `reports/data-discovery.json`. The original data remains unchanged and
  excluded from Git; nothing was uploaded.
- Added findings, a learner exercise, and a LinkedIn draft to
  `docs/data-discovery.md`.
- The script completed successfully; syntax compilation also passed. No model
  or API exists yet. The learner's discovery checkpoint remains pending.
- Next: confirm understanding, then define cleaning rules and chronological
  splits. Product selection will use training-period information only.

## 2026-10-19 — Data preparation and forecasting examples

- Implemented `src/data/prepare.py`, with fixed scope in `configs/data.json`.
- Detected source-sheet date overlap: the later export owns December 2010 onward.
  Excluded 22,523 earlier-sheet rows under this documented precedence policy.
- Excluded 1,633 rows on the final source day conservatively because that day's
  capture may be incomplete.
- Defined gross recorded merchandise units with sequential exclusion rules.
  Retained 1,013,327 qualifying source rows; did not delete missing customer IDs
  or identical lines within authoritative source periods.
- Selected 20 products from only the 90 days before 2011-01-01, requiring at
  least 60 days with recorded qualifying sales.
- Generated 14,760 daily product rows and 3,500 / 1,720 / 1,260 training /
  validation / test forecasting examples.
- Added lagged sales, rolling historical statistics, calendar features, and
  seven-day forward targets. Purged targets crossing split boundaries.
- All 12 pytest cases passed. Independently checked 180 real feature/target
  windows covering every selected product and split; output checksums matched.
  `pip check` reported no broken requirements.
- Coding-assistant implemented and executed this milestone at the learner's
  request; no manual command execution or understanding check is claimed.
- Next milestone: training-only EDA, visualizations, and baseline design.

## 2026-10-19 — Training-only EDA and baseline protocol

- Implemented and ran `python -m src.data.eda` against checksum-verified inputs.
  Restricted analysis to January–June 2011 training outcomes. Did not open
  validation/test forecasting files or evaluate their outcomes.
- Created and visually inspected six standalone PNG charts covering time series,
  product activity, targets, weekdays, feature distributions, and correlations.
  Corrected footer/axis-label overlaps found in the initial visual review.
- Recorded actual aggregate results in `reports/training-eda.json` and explained
  their meaning and limits in `docs/training-eda.md`.
- Found 47.02% zero-sales product-days, 514 zero targets, a median seven-day
  target of 223 units, and a maximum seven-day target of 4,562 units.
- Preserved extreme values and the original product selection. No transformations
  used only for plotting have been silently introduced into model features.
- Defined previous-week and four-week-average baselines, Ridge and random forest
  candidates, and validation-based selection before fitting any models.
- Added three scope/provenance tests. All 15 tests passed without warnings after
  pinning the plotting parser to a compatible version; `pip check` passed.
- Prepared an EDA LinkedIn draft with actual measurements and the target chart.
- Next: implement baselines, candidate model pipelines, and MLflow tracking;
  compare on validation, freeze selection, then evaluate the final model on test.

## 2026-10-19 — Baselines, learned models, MLflow, and final evaluation

- Implemented two historical baselines, Ridge, and a fixed-seed random forest.
  Added model-facing validation, product-category handling, and a shared
  nonnegative prediction floor. Learned preprocessing is fitted with its model.
- Recorded configurations before running the comparison. Source implementation
  commit: `0ae70ef`; actual source checksums are recorded with every run.
- Ran all four candidates on the same train/validation rows and tracked the
  results locally with MLflow (SQLite metadata and local artifacts).
- Selected the forest by validation MAE: 248.4836 versus 252.9289 for the stronger
  baseline, a 1.7575% validation reduction. Ridge's RMSE was slightly better;
  selection followed the previously recorded MAE criterion.
- Frozen selection run: `c13c6e0868d840f79affd1c661f165f5`.
- Refit on 5,220 development rows and evaluated the final model on 1,260 test
  examples. MAE 389.0710, RMSE 670.7093, R² 0.16155. No test-driven tuning followed.
- Final run/version: `fe48bb872b9b4d12aac4f7a5c42734e4`. Saved the trusted local
  joblib bundle and metadata; no raw data or model was uploaded.
- All 32 tests passed; dependency check passed. Verified save/load consistency,
  model checksum, and test metrics using direct NumPy formulas on saved outputs.
- Started and checked the localhost MLflow dashboard (HTTP 200), verified five
  finished runs and their artifacts through its HTTP API, and created/visually
  reviewed three result charts. Wrote the results/limitations and LinkedIn draft.
- Automatic approval review blocked the Edge launch for a dashboard screenshot
  with reason "blocked by policy". The dashboard works, but no screenshot was
  captured. The server also reported Windows job-backend and upstream WSGI
  warnings; tracking and dashboard checks passed without that job backend.
- This is an engineering milestone with modest predictive results, not a claim
  of a useful inventory optimization model. Next: FastAPI serving and API tests.
