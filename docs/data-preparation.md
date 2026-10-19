# Data preparation decisions

## Target and scope

Predict **gross recorded merchandise units** over seven calendar days starting
at the forecast date. Exclude cancellation invoices, nonpositive quantities,
nonpositive prices, and product codes outside the explicit merchandise-code
heuristic (five digits followed by zero to two letters).

This code-pattern rule is a conservative heuristic, not a verified product
catalog. It can exclude legitimate codes; this is a limitation, not evidence
that all excluded records are wrong. It is not a learned rule.

Missing customer IDs and descriptions are retained: the forecasting task needs
product codes, quantities, and dates, not customer identity. Malformed required
values raise errors. Returns are not subtracted from the target, so the result
must not be described as net sales, revenue, or true customer demand.

## Overlapping exports and duplicates

The sheets' date ranges overlap in December 2010. For each earlier sheet, the
next sheet owns dates starting at its first calendar day. This is an explicit
source-precedence assumption, not a reconciliation against the retailer's system.
Excluded overlap rows are counted in the report.

Within-sheet identical rows remain intact. Repeated identical invoice lines may
be valid; without a unique line identifier there is insufficient evidence to
delete them. The preparation report counts retained duplicates.

## Product selection

Select 20 products using only the 90 days before 2011-01-01, requiring sales on
at least 60 distinct days. Rank eligible products by recorded units, breaking
ties by product code. Training forecast dates begin on 2011-01-01, after this
selection period. No validation/test sales determine which products are chosen.

This deliberately favors established, frequently sold products. It does not
demonstrate performance for new products or the full catalog. No product is
removed because of weak future performance.

## Daily histories and missing days

Aggregate qualifying transaction quantities by product and calendar date. A day
without a qualifying transaction becomes zero **recorded** sales and zero lines.
That assumption relies on source capture completeness; it does not establish
that the retailer was open or the product was in stock. No calendar or inventory
data is available to make those distinctions.

Use the source's naive timestamps as recorded; do not reinterpret them as Dubai
time. Drop the final source calendar day conservatively because its capture may
be partial. This is not proof that all earlier days are complete.

## Features and forecast cutoff

Each forecast is made at the start of its date:

- `lag_1`: units recorded on the previous calendar day.
- `lag_7`: units recorded seven days earlier.
- `mean_7`: average units over the preceding seven calendar days.
- `mean_28`, `std_28`: average and population standard deviation over the
  preceding 28 calendar days.
- `weekday`, `month`: calendar information known at prediction time.
- `product_id`: identifier available for later categorical encoding.

No feature includes sales from the forecast date. Require the full history
window. Sum the forecast day's units and the following six days to construct
`target_units_7d`; exclude rows without the complete forward window. Raw daily
units and transaction counts are omitted from model-facing example files.

No scalers, encoders, imputers, or models are fitted in this phase. Any learned
preprocessing in the modeling phase must be fitted on training data only.

## Chronological evaluation

- Training forecast dates begin 2011-01-01; training targets end before July 1.
- Validation forecast dates begin July 1; validation targets end before October 1.
- Test forecast dates begin October 1; targets must end by the last retained day.

This removes the final six forecast origins before each split boundary, whose
targets would extend into the next period. Within a split, adjacent seven-day
targets overlap: evaluation examples are correlated, not independent samples.

The intended evaluation is daily rolling-origin replay: after each day passes,
its observed sales can be used for the next forecast. It is not a claim that we
can forecast an entire test quarter using only information from October 1.
Validation drives model choices; test results remain reserved for final evaluation.

## Reproduction and evidence

From the repository root using the project interpreter:

```powershell
.\.venv\Scripts\python.exe -m src.data.prepare
.\.venv\Scripts\python.exe -m pytest -q
```

Rules are recorded in `configs/data.json`. The script writes daily sales,
selection statistics, and three example CSVs to ignored `data/processed/`.
`reports/data-preparation.json` records sequential exclusions, date boundaries,
row counts, configuration, and source/output checksums. Sequential exclusion
counts are mutually exclusive; they differ from overlapping discovery flags.

Tests cover source validation, overlap handling, preserving missing customer
IDs and within-sheet duplicates, zero recorded-sales days, exact feature/target
arithmetic, future perturbation, product selection, and split-window isolation.

## Learning checkpoint

For a forecast made at the start of July 1, the last seven days of sales must
come from June 24–30. July 1–7 sales construct the target, not an input feature.
