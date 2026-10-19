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
| CI workflow | Authored and YAML-checked; hosted execution not yet possible without GitHub publication/authentication |
| Deployment | Local Docker alternative selected and working; no cloud service or hosting bill created |
| Operations | Structured request logs, counters/timing, model versions, range flags, offline feature comparison |
| README and architecture | Setup, metrics, serving, Docker, CI status, limitations, charts, and architecture documented |
| Portfolio deliverables | Journal, LinkedIn drafts, CV/profile descriptions, and interview/self-check guide prepared |
| GitHub public repository | Pending; CLI not signed in, no remote configured |
| Learner understanding | Not assessed; exercises and interview walkthrough are available |

## Remaining external release gate

The GitHub connector can access the existing personal account, but its available
tools do not create repositories. The local GitHub CLI is not authenticated.
No credentials were extracted or requested in chat. Once the account owner signs
in through `gh auth login`, repository creation/push and hosted workflow
verification can be completed using the prepared code. See `ci-and-github.md`.

The project is **not marked fully complete under the original success criteria**
until a hosted GitHub Actions run succeeds and the learner can explain the
architecture. No passing badge, live cloud URL, or comprehension claim is invented.

## Evidence files

- `reports/data-discovery.json`, `data-preparation.json`, `training-eda.json`
- `reports/model-comparison.json`, `final-evaluation.json`
- `reports/native-api-verification.json`, `container-api-verification.json`
- `reports/feature-drift.json` and `reports/figures/`
- `reports/system-verification.json` summarizes both test suites and runtime checks.
- Local test XML reports are ignored by Git to avoid publishing machine details.
- `.github/workflows/ci.yml` is configured, not proof of hosted execution.

The existing upstream test-client deprecation warning is recorded rather than
hidden; it does not prevent the current behavior/tests from passing. The earlier
automatic approval review blocked an Edge screenshot launch. Real charts and
the architecture export are available; no fake dashboard screenshot was made.
