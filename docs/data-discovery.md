# Dataset discovery — first inspection

The unmodified UCI Online Retail II workbook was inspected with
`scripts/inspect_data.py`. The machine-readable evidence is
`../reports/data-discovery.json`, including sheet-level counts and a SHA-256
checksum. These are full-source quality checks, not a model evaluation or an
analysis used to select features from future test outcomes.

## Measured results

| Check | Result |
| --- | ---: |
| Transaction rows across two sheets | 1,067,371 |
| Columns | 8 |
| Unique product codes, including possible non-merchandise codes | 5,305 |
| Missing descriptions | 4,382 |
| Missing customer identifiers | 243,007 |
| Exact duplicate rows beyond the first occurrence | 34,335 |
| Invoice rows whose identifier begins with C | 19,494 |
| Rows with negative quantities | 22,950 |
| Rows with zero or negative prices | 6,207 |

The timestamps range from 2009-12-01 07:45:00 to 2011-12-09 12:50:00.
Issue counts can overlap and must not be summed as the number of affected rows.
No rows have been deleted or modified.

## What this means for our next decisions

1. A transaction line is not one forecast example. We must construct product/day
   histories and forward seven-day targets.
2. Missing customer IDs do not automatically invalidate product-level sales.
   Customer identity is not required for our proposed target.
3. Cancellations and negative quantities overlap but are not identical checks.
   We must define whether to forecast gross recorded sales or net quantities.
4. Identical rows are candidates for investigation, not proof of duplicate ingestion.
5. Product codes and invoice numbers are identifiers, even when they look numeric.
   `Customer ID` was inferred as a float because of missing values; it is not a
   continuous measurement.
6. The last recorded day ends at 12:50. We must establish complete target windows
   rather than assuming the final day or week is fully observed.
7. Product selection and model choices must use training-period information.
   We have not chosen products, split dates, or a cleaning policy yet.

## Learning exercise

Open the JSON report and find the missing customer ID count. Explain why removing
every row without a customer ID might discard useful information for product
sales forecasting. Also explain why randomly splitting transaction rows would
not simulate predicting future sales.

## Discovery milestone communication

- Learning summary: verified the source workbook and inspected its actual schema.
- Main concept: data quality flags require decisions based on the prediction task.
- Screenshot: the aggregate counts and source checksum in the JSON report.
- Technical challenge: the workbook uses `Price` and `Invoice`, whereas the web
  documentation describes `UnitPrice` and `InvoiceNo`. The loader checks the
  workbook's actual column names and raises an error for an unexpected schema.

### LinkedIn draft — project introduction and discovery

I'm building RetailCast to learn how to turn a sales forecasting experiment into
a reproducible prediction service.

The proposed question: using information available at a daily cutoff, how many
units of a product will sell over the next seven days?

With coding-assistant support, I set up an isolated Python environment and ran a
repeatable inspection of UCI's Online Retail II dataset. Across 1,067,371 rows,
the report found 243,007 missing customer IDs, 34,335 repeated rows beyond their
first occurrence, and 22,950 rows with negative quantities.

The first engineering decision is deciding what those records mean for this
task. Missing customer identity does not necessarily make a product sale unusable,
and a repeated row is not automatically safe to delete.

One boundary is already clear: this data records sales, not unmet demand during
stockouts. I won't claim the model estimates that missing demand.

Next: define cancellation handling, construct daily histories, and design
chronological splits before training. No model results yet.

Dataset and attribution: Chen, D. (2012), Online Retail II, UCI Machine Learning
Repository, https://doi.org/10.24432/C5CG6D (CC BY 4.0).

#MachineLearning #DataEngineering #Python #MLOps #DemandForecasting

Publish only after reviewing the report and explaining these decisions yourself.
