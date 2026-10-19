# Milestone and release status

Status date: 2026-10-19. This record distinguishes implemented software from
account-dependent publishing and the learner's ability to explain the work.

| Milestone | Status and evidence |
| --- | --- |
| Dataset/target/license | Documented; original workbook inspected and checksum recorded |
| Reproducible preparation | Implemented and executed; policy, counts, splits, and checksums recorded |
| EDA | Training-only analysis; six rendered and visually checked charts |
| Baselines and two algorithms | Two baselines plus Ridge/forest compared on the same validation rows |
| Experiment tracking | Five finished local MLflow runs with parameters, metrics, provenance, and artifacts |
| Final evaluation | Frozen selection then refit/test; actual metrics recorded without retuning |
| Serialization | Model/preprocessor saved together; checksums and save/load consistency verified |
| FastAPI | Real HTTP predictions, health, model-info, docs, input/error handling, version responses |
| Docker | Image built; non-root, read-only Compose service healthy; HTTP smoke checks passed |
| Tests and lint | All 54 tests pass on Windows and Linux; Ruff and dependency checks pass in both |
| Cross-platform predictions | All 1,260 Linux-container forecasts match saved Windows forecasts within numerical tolerance |
| CI workflow | Hosted run 39309251409 passed lint, 54 tests, dependencies, Docker build, and HTTP smoke checks |
| Deployment | Local Docker alternative selected and working; no cloud service or hosting bill created |
| Operations | Structured request logs, counters/timing, model versions, range flags, offline feature comparison |
| README and architecture | Setup, metrics, serving, Docker, CI status, limitations, charts, and architecture documented |
| Portfolio deliverables | Journal, LinkedIn drafts, CV/profile descriptions, and interview/self-check guide prepared |
| GitHub public repository | Published: nihal-usman-chenganath/retailcast-ml-engineering |
| Learner understanding | Not assessed; exercises and interview walkthrough are available |

## Verified release and remaining learning checkpoint

After account-owner device authorization, the CLI published the
[public repository](https://github.com/nihal-usman-chenganath/retailcast-ml-engineering).
[Hosted run 39309251409](https://github.com/nihal-usman-chenganath/retailcast-ml-engineering/actions/runs/39309251409)
completed successfully, including Docker startup and HTTP smoke checks. The
downloaded JUnit artifact confirms all 54 tests passed with zero failures/errors.
No raw dataset, model bundle, credentials, or local machine test reports were pushed.

The technical delivery and portfolio artifacts are complete with the allowed
local-deployment alternative. The original learning criterion remains unassessed:
the learner should complete `interview-preparation.md` and demonstrate the
architecture walkthrough. No cloud URL or comprehension claim is invented.

## Evidence files

- `reports/data-discovery.json`, `data-preparation.json`, `training-eda.json`
- `reports/model-comparison.json`, `final-evaluation.json`
- `reports/native-api-verification.json`, `container-api-verification.json`
- `reports/feature-drift.json` and `reports/figures/`
- `reports/system-verification.json` summarizes both test suites and runtime checks.
- Local test XML reports are ignored by Git to avoid publishing machine details.
- `reports/github-ci.json` and the linked GitHub run establish hosted execution.

The existing upstream test-client deprecation warning is recorded rather than
hidden; it does not prevent the current behavior/tests from passing. The earlier
automatic approval review blocked an Edge screenshot launch. Real charts and
the architecture export are available; no fake dashboard screenshot was made.
