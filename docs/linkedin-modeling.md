# LinkedIn draft — baselines, MLflow, and a modest model gain

RetailCast's first model comparison produced a useful result: the more complex
model won by less than I might have expected.

I compared two historical baselines, Ridge, and a random forest on the same
1,720 chronological validation examples. The forest's MAE was 248.48 units per
product/seven-day forecast, versus 252.93 for the stronger four-week baseline.
That is a 1.76% validation MAE reduction, not an accuracy percentage.

Ridge had slightly better RMSE. I kept the predeclared MAE selection rule rather
than switching metrics after seeing the results.

After selection, I refitted the forest on training plus validation data and
evaluated it on the reserved test period. Test MAE was 389.07 units and R² was
0.162. Those results show limited forecasting strength; they do not establish
business value or improvement over the baselines on test.

The engineering milestone is reproducibility: with coding-assistant support,
I built separate comparison/finalization commands, training-fitted preprocessing
pipelines, and local MLflow tracking. Five finished runs contain metrics,
parameters, checksums, and saved model artifacts. Serialization checks preserve
predictions, and all 32 current tests pass.

My main lesson: keep a strong baseline, declare how models will be selected, and
report the final outcome even when the numbers are modest. The forest's extra
complexity has only a small validation benefit here.

Next is serving the versioned model through FastAPI, with explicit input
validation and clear limits on what the predictions represent.

Dataset: Chen, D. (2012), Online Retail II, UCI Machine Learning Repository,
https://doi.org/10.24432/C5CG6D (CC BY 4.0).

#MachineLearning #MLflow #MLOps #TimeSeries #Python #ModelEvaluation

## Evidence and sharing notes

- Chart: `reports/figures/validation-model-comparison.png`.
- Additional evidence: `test-forecast-history.png` and `test-product-errors.png`.
- Dashboard: http://127.0.0.1:5000, experiment `RetailCast-sales-forecasting`.
- Main concept: validation selection and final held-out evaluation are different.
- Technical challenge: package the same input contract, preprocessing, and
  prediction floor with each saved estimator and verify save/load consistency.
- A dashboard screenshot was not captured because automatic approval review
  blocked the browser launch. No mock dashboard screenshot was created.
- Review/adapt before posting. No LinkedIn message has been published.
