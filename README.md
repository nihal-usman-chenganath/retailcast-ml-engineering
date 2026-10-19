# RetailCast — Retail Sales Forecasting & Prediction API

Status: Data preparation implemented and verified; modeling has not started.

RetailCast will forecast next-seven-day recorded product sales using historical
retail transactions. It is a learning and portfolio project; no model has been
trained, and no performance or business impact has been established.

See [the project brief](docs/project-brief.md) for the proposed prediction task
and [the development journal](docs/development-journal.md) for verified progress.

Implementation will proceed through data inspection, preparation and EDA,
baseline modeling, MLflow tracking, FastAPI serving, tests, Docker, CI, and a
deployment decision. Each major phase requires a working result and a learning
checkpoint before proceeding.

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
`reports/data-preparation.json`. No model, API, or deployment is implemented yet.

Verified preparation output: 20 selected products; 3,500 training examples,
1,720 validation examples, and 1,260 test examples. These are forecasting rows,
not original transaction counts. The 12 preparation tests pass. See the report
for exact date boundaries and filtering counts.
