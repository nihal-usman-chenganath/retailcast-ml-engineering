# Interview preparation and architecture walkthrough

## A 90-second explanation

“RetailCast forecasts seven-day gross recorded unit sales for 20 established
products. I started with UCI's historical retail workbook and found overlapping
exports, cancellations, missing identifiers, and repeated rows. The pipeline
uses a documented export-precedence rule and builds calendar-aligned daily
histories. Features use only information before each forecast cutoff.

“I selected products before the training period and split examples by time,
excluding targets that cross split boundaries. I compared two simple historical
forecasts, Ridge, and a forest, tracking runs in MLflow. The forest won validation
MAE by only 1.76% over the stronger baseline. Its final test MAE was 389.07 units
and R² was 0.162, so I describe the predictive result as limited.

“The engineering result is a repeatable service: shared feature code, a verified
model bundle, FastAPI input validation, model-version responses, Docker, and
tests. It is historical replay and a local deployment. I have not measured
inventory savings or claimed production forecasting suitability.”

## Questions and answer anchors

1. **Why this dataset?** Public real transaction history, explicit attribution
   license, realistic quality issues, enough chronology for a temporal study.
   It is old UK data and does not validate UAE performance.
2. **What is the target?** Gross qualifying recorded units on the forecast day
   plus the next six days. It is not net returns-adjusted sales or true demand.
3. **How did you avoid leakage?** Pre-training product selection; shifted lag
   and rolling features; train-fitted preprocessing; date-based splits; no target
   window crossing boundaries; frozen selection before final test access.
4. **Why not random splits?** Future retail patterns and related overlapping
   target windows could enter training for earlier predictions.
5. **Why Ridge and a forest?** A cheap linear reference versus nonlinear trees.
   Baselines expose whether complexity earns its cost. No claim they exhaust
   all forecasting methods.
6. **Why select the forest when Ridge has better RMSE?** MAE was the declared
   criterion before comparison. Changing metrics afterward would alter the
   selection rule to fit results.
7. **What does MAE 389 mean?** About 389 units of absolute error per product's
   seven-day test forecast on average, not 389 units per day or a percentage.
8. **What does negative R² mean?** Worse squared error than a constant mean
   reference on that evaluated set; it is possible and should not be hidden.
9. **What did MLflow add?** Linked parameters, metrics, run IDs, artifacts,
   configuration, and source/data provenance without manual spreadsheet copying.
10. **Why serialize preprocessing with the estimator?** Serving must apply the
    same learned transforms as training. Feature parity and save/load tests
    check this contract.
11. **How is inference time-safe?** A product/date request retrieves features
    computed from earlier days only. Dates before the fitted model's development
    cutoff or beyond available history are rejected.
12. **What does Docker solve?** Packages dependencies and startup behavior. It
    does not guarantee good forecasts, security, or identical performance on
    every machine.
13. **How do invalid requests behave?** Typed schema and catalog/date checks
    return 422; internal failures return generic 500; counters and request IDs
    support diagnosis.
14. **What is the monitoring scope?** Process-local timing/error counts, version
    tracking, range flags, and offline distribution comparison. No durable alerting
    or statistically calibrated drift detector is claimed.
15. **How would you scale?** First measure load/memory, externalize history and
    durable metrics, add authenticated ingress, use reproducible artifact
    distribution, and scale stateless instances. Avoid introducing Kubernetes
    without a workload that needs it.
16. **What would you improve next?** More appropriate product/seasonality
    modeling, business acceptance criteria, richer available-at-cutoff signals,
    and a new evaluation design. Do not tune against the already inspected test.
17. **Did GitHub CI actually run?** Yes: the README links a successful hosted
    run with 54 passing tests, Docker build, and HTTP smoke checks. The authored
    workflow alone would not have established this.
18. **What did you personally do?** Describe decisions you understand and work
    with coding-assistant support accurately, using the development journal.

## Practical self-checks

- Trace a July 1 forecast: history ends June 30 and its target ends July 7.
- Explain why a valid model prediction can be a poor inventory decision.
- Locate the chosen MLflow run, model checksum, and actual test metrics.
- Demonstrate one valid request, one 422 response, and a service restart.
- Explain why a changed checksum should fail startup rather than be ignored.

These are prepared exercises. Passing tests does not establish that the learner
has completed or understood this interview walkthrough.
