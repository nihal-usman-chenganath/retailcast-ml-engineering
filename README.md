# RetailCast — Retail Sales Forecasting & Prediction API

Status: Data preparation, EDA, modeling, and local MLflow tracking verified.
FastAPI, Docker, CI, and deployment are not implemented yet.

RetailCast will forecast next-seven-day recorded product sales using historical
retail transactions. A random forest has been trained and evaluated under the
protocol below. This is a learning and portfolio project; business impact and
suitability for live inventory decisions have not been established.

See [the project brief](docs/project-brief.md) for the proposed prediction task
and [the development journal](docs/development-journal.md) for verified progress.

Implementation will proceed through data inspection, preparation and EDA,
baseline modeling, MLflow tracking, FastAPI serving, tests, Docker, CI, and a
deployment decision. Each major phase produces a verified result and an
explanation of the implementation and its limitations.

## Run the discovery milestone (Windows PowerShell)

Open a terminal in this repository's root folder. Requires Python 3.11.

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe scripts/inspect_data.py
```

Skip the first command if `.venv` already exists. The inspection script downloads
the original UCI archive on first use, extracts only the expected workbook, and
reads both sheets without changing their contents. Later runs reuse the local
workbook. Reading the full workbook can take several minutes.

- Raw files: `data/raw/` (excluded from Git).
- Aggregate results: `reports/data-discovery.json`.
- Workbook SHA-256: included in the report to identify the inspected file.
- Library compatibility check: `.\.venv\Scripts\python.exe -m pip check`.

Dataset source: [UCI Online Retail II](https://archive.ics.uci.edu/dataset/502/online+retail+ii).
Attribution: Chen, D. (2012), UCI Machine Learning Repository,
[DOI: 10.24432/C5CG6D](https://doi.org/10.24432/C5CG6D). UCI lists the dataset under
CC BY 4.0. Downloaded files are retained locally; no dataset is published by this
repository. The discovery report contains aggregate counts, not customer records.

The discovery command only inspects source data. The preparation command below
implements the documented cleaning and forecasting examples.

## Data preparation milestone

```powershell
.\.venv\Scripts\python.exe -m src.data.prepare
.\.venv\Scripts\python.exe -m pytest -q
```

See [data preparation decisions](docs/data-preparation.md) for the precise target,
source overlap policy, selection rules, and time-based splitting. Outputs remain
local in `data/processed/`; aggregate evidence is in
`reports/data-preparation.json`.

Verified preparation output: 20 selected products; 3,500 training examples,
1,720 validation examples, and 1,260 test examples. These are forecasting rows,
not original transaction counts. See the report
for exact date boundaries and filtering counts.

## Training-data exploration

```powershell
.\.venv\Scripts\python.exe -m src.data.eda
```

The EDA script checks source checksums, analyzes the training calendar only, and
exports six charts plus `reports/training-eda.json`. It does not open validation
or test forecasting files. EDA scope guards are included in the test suite.

Key findings: 47.02% of training product-days have zero recorded sales; the
median seven-day target is 223 units and its maximum is 4,562 units. Products
vary widely in volume, and large observations have been retained.

![Training target distribution](reports/figures/training-target-distribution.png)

Read [the EDA findings](docs/training-eda.md) for all charts and limitations, and
[the baseline/evaluation protocol](docs/baseline-and-evaluation-plan.md) for the
planned model comparison. These descriptive statistics are not model accuracy.

## Model comparison and experiment tracking

All four approaches used the same 3,500 training and 1,720 validation examples.
The comparison configurations were fixed before fitting, with validation MAE
as the selection criterion.

| Candidate | Validation MAE | Validation RMSE | Validation R² |
| --- | ---: | ---: | ---: |
| Previous-week total | 311.44 | 513.10 | -0.252 |
| Four-week average | 252.93 | 425.07 | 0.141 |
| Ridge | 254.86 | 407.09 | 0.212 |
| Random forest — selected | 248.48 | 410.65 | 0.198 |

MAE and RMSE are in units per product/seven-day forecast. The forest reduced
validation MAE by **1.76%** relative to the stronger baseline, a modest gain.
Ridge had better RMSE; the declared MAE criterion determined selection.

The selected forest was refitted on 5,220 training-plus-validation examples,
then evaluated on 1,260 held-out test examples (October 1–December 2 forecast
origins, with targets ending by December 8, 2011):

| Final held-out test metric | Value |
| --- | ---: |
| MAE | 389.07 units |
| RMSE | 670.71 units |
| R² | 0.162 |

These results show limited predictive strength and uneven per-product errors.
The validation gain is not evidence of test-set superiority to the baselines,
statistical significance, stockout reduction, or financial savings. Test results
were not used to revise the model. See [results and limits](docs/model-results.md).

![Validation comparison](reports/figures/validation-model-comparison.png)

From a fresh prepared workspace, run:

```powershell
.\.venv\Scripts\python.exe -m src.models.train compare
.\.venv\Scripts\python.exe -m src.models.train finalize
.\.venv\Scripts\python.exe scripts/plot_model_results.py
```

Finalization creates a marker that blocks repeating model selection/test
evaluation in the same workspace. Preserve this record; use a fresh checkout to
reproduce the full process. Model files are ignored by Git and must be regenerated.

Open the local MLflow dashboard with:

```powershell
.\.venv\Scripts\python.exe -m mlflow ui --backend-store-uri sqlite:///mlflow.db --host 127.0.0.1 --port 5000
```

Visit http://127.0.0.1:5000 and select `RetailCast-sales-forecasting`.
The experiment contains four comparison runs and a final evaluation run.
Read [the MLflow guide](docs/modeling-and-mlflow.md) for comparison instructions,
artifact storage, and trust boundaries.

Final saved bundle: `models/final/model.joblib` and `metadata.json`.
Final model version (MLflow run ID): `fe48bb872b9b4d12aac4f7a5c42734e4`.
Local model files, row-level outputs, and tracking storage are excluded from Git.

Verification: **32 tests pass**, dependencies pass `pip check`, serialized models
preserve predictions, and saved test metrics reconcile with direct NumPy formulas.
The dashboard HTTP endpoint and all five finished runs/artifact listings were
also checked. The API and container milestones remain outstanding.
