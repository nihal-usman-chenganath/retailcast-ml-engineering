# LinkedIn drafts — serving, Docker, and the local system

These are drafts backed by local project evidence. Nothing has been posted.
Replace release-status statements only after the corresponding check succeeds.

## Post 4 — From a model to a request/response contract

RetailCast now accepts a product code and a forecast date over HTTP.

The client does not calculate rolling averages. The server uses the same
historical-feature function as preparation, and I checked parity across all
6,480 existing forecasting examples. Features for a date use earlier sales only.

The API rejects unknown products, malformed requests, dates before the model's
development cutoff, and dates beyond available history. Responses include the
exact model version and clearly label the service as historical replay.

Startup also checks model/history checksums and runtime compatibility before
loading the trusted local bundle. A checksum is an integrity check, not a way
to make arbitrary pickle files safe.

With coding-assistant support, I added API tests, structured request timing,
validation-failure counters, and real HTTP smoke checks. The recorded sales model
still has limited accuracy; serving it does not change that limitation.

#FastAPI #Pydantic #MachineLearning #MLOps #Python

Evidence: `reports/native-api-verification.json`, `/docs`, and the API tests.
Challenge resolved: shared feature engineering and explicit date availability
prevent clients from accidentally asking the frozen model for unsupported dates.

## Post 5 — What the container actually packages

RetailCast's inference image packages a saved model, aggregate history, source,
and a small inference dependency set. The full MLflow/training environment stays
outside the serving image.

The local Compose setup uses a non-root user, read-only root filesystem,
localhost port mapping, resource limits, a health check, and rotated logs.
The model produces the same structured responses through HTTP inside Docker.

I also authored a GitHub Actions workflow for linting, tests, container build,
and a synthetic-fixture HTTP smoke check. The fixture is explicitly labelled and
is not used to claim forecasting performance. Hosted GitHub Actions passed
lint, all 54 tests, Docker build, and HTTP smoke checks.

The main lesson is that packaging and testing need evidence: a Dockerfile alone
does not prove a container runs, and a workflow file alone does not prove CI passed.

#Docker #SoftwareTesting #GitHubActions #MLOps #Python

Evidence: container verification report, Compose health output, and test reports.
Challenge resolved: Docker CLI installation did not mean the engine was running;
starting Desktop's Linux engine was a separate prerequisite.

## Final local-system post

RetailCast now connects a retail dataset to a versioned local prediction API.

The workflow covers validation and daily feature engineering, chronological
evaluation, two historical baselines, Ridge/random forest comparison, local
MLflow, serialization, FastAPI, Docker, automated checks, and basic monitoring.

The modeling result is intentionally reported without embellishment: forest
validation MAE 248.48 versus 252.93 for the stronger baseline (1.76% lower).
Final test MAE was 389.07 units and R² was 0.162. These are limited forecasts,
not evidence of stockout reduction or financial impact.

The engineering evidence includes shared-feature parity across 6,480 examples,
five tracked MLflow runs, versioned/checksummed artifacts, and 54 tests. A local
container serves real predictions with request validation and operational logs.

The source is public and hosted GitHub CI passed. Cloud hosting is optional;
I selected a documented local deployment after reviewing
current hosting costs and free-tier restrictions.

My next learning goal is explaining each boundary: which data exists at the
forecast cutoff, what a metric measures, and what the service cannot claim.

Dataset: Chen, D. (2012), Online Retail II, UCI Machine Learning Repository,
https://doi.org/10.24432/C5CG6D (CC BY 4.0).

#MachineLearningEngineering #MLOps #FastAPI #Docker #MLflow #DataScience

GitHub: https://github.com/nihal-usman-chenganath/retailcast-ml-engineering
CI evidence: https://github.com/nihal-usman-chenganath/retailcast-ml-engineering/actions/runs/39309251409

Architecture: use the README Mermaid diagram or exported PNG. Charts: use the
validation comparison and test forecast history. No LinkedIn post was published
automatically.
