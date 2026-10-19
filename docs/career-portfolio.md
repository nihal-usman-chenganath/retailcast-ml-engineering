# Career portfolio wording

These drafts describe verified local engineering work and a successful hosted
GitHub Actions run. No live cloud service is claimed. Adapt them to your actual
contribution and ability to explain the implementation; the development journal
records coding-assistant support.

## AI Engineer CV

**RetailCast — Versioned ML Prediction Service | Python, scikit-learn, FastAPI, Docker**

- Built a typed REST service for seven-day recorded-sales forecasts with
  product/date validation, trusted-bundle checksum checks, model-version
  responses, structured request logging, and invalid-input handling.
- Packaged shared feature engineering and the trained estimator for consistent
  offline and API predictions; checked feature parity across 6,480 forecast rows.
- Compared two historical baselines with Ridge and random forest using
  chronological evaluation and MLflow experiment tracking.

## Machine Learning Engineer CV

**RetailCast — Reproducible Forecasting Pipeline and API**

- Prepared UCI retail transactions into leakage-aware product/day features,
  selecting 20 products from pre-training history and separating seven-day
  target windows across training, validation, and test boundaries.
- Tracked four candidate runs and one final evaluation in MLflow; the selected
  forest reduced validation MAE by 1.76% versus the stronger historical baseline.
- Serialized the model with its preprocessing, exposed versioned predictions,
  and implemented 54 tests covering data rules, temporal boundaries, loading,
  validation, consistency, and monitoring diagnostics.

## Data Scientist CV

**RetailCast — Time-Based Retail Sales Forecasting Study**

- Analyzed a 1,067,371-row source workbook, documented overlapping exports,
  missing identifiers, cancellations, and the distinction between observed
  sales and unobserved demand.
- Compared four forecasting approaches on 1,720 chronological validation
  examples using MAE, RMSE, R², and per-product errors; retained a fixed selection
  protocol despite differing metric rankings.
- Evaluated the selected refitted model on 1,260 held-out examples: MAE 389.07
  units and R² 0.162; documented limited predictive strength and uneven errors.

## MLOps Engineer CV

- Created local MLflow tracking with run-linked artifacts, configuration/source
  checksums, dependency pins, and a two-stage model-selection/final-evaluation
  workflow that guards against repeated test-driven tuning.
- Containerized a read-only inference service with a non-root user, readiness
  check, resource limits, rotated logs, and version-aware model loading.
- Automated pytest and lint checks and authored a GitHub Actions workflow for
  tests, container build, and synthetic-fixture HTTP smoke verification.

Hosted GitHub CI passed all 54 tests, lint, the Docker build, and HTTP smoke checks;
the successful run is linked in the README.

## Data Engineer CV

- Implemented reproducible schema validation and documented source-precedence
  rules for overlapping retail exports; retained missing customer identifiers
  when irrelevant to the product-level task.
- Built daily aggregates and versioned temporal feature tables with configuration,
  filtering statistics, and source/output checksums. No PostgreSQL ingestion
  service is claimed; SQLite is used by MLflow for experiment metadata.

## LinkedIn Projects description

RetailCast is a local end-to-end ML engineering project using UCI Online Retail
II. It covers source validation, chronological feature/target construction,
training-only EDA, two baselines, Ridge and random forest comparison, MLflow,
saved preprocessing/model bundles, FastAPI, Docker, automated tests, and basic
operational diagnostics. The forest achieved a modest 1.76% validation MAE
reduction over the stronger baseline; final test MAE was 389.07 units (R² 0.162).
The API demonstrates historical replay, not a live inventory recommendation tool.
The public GitHub repository includes a successful hosted workflow run.

## GitHub profile README snippet

**RetailCast — Retail Sales Forecasting & Prediction API**

An end-to-end local ML system with chronological evaluation, MLflow tracking,
shared feature engineering, typed FastAPI predictions, Docker, and automated
checks. Includes transparent baseline comparisons, documented limitations, and
a development journal and verified GitHub CI.
Repository: https://github.com/nihal-usman-chenganath/retailcast-ml-engineering.
