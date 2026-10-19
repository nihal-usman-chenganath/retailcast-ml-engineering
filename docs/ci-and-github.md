# Automated checks and GitHub publication

## What the workflow does

`.github/workflows/ci.yml` runs on pushes, pull requests, and manual dispatch:

1. Check out code and set up Python 3.11.9.
2. Install pinned dependencies and run Ruff code-quality checks.
3. Run pytest and dependency consistency checks.
4. Create a labelled synthetic fixture bundle, build Docker, and check HTTP
   behavior inside the container.
5. Retain the test report; stop the CI container even if checks fail.

The fixture demonstrates container/service mechanics without requiring the raw
dataset or publishing a real model. It is labelled `synthetic_ci_fixture`, has no
portfolio accuracy metrics, and refuses to overwrite an existing bundle. The
real trained bundle is verified separately on this machine. The workflow does
not publish an image or deploy a service.

Only read access to repository contents is requested. Forked pull requests do
not receive deployment credentials. No secrets are needed for these checks.
Official action usage: [checkout](https://github.com/actions/checkout) and
[setup-python](https://github.com/actions/setup-python).

## Run the code checks locally

```powershell
.\.venv\Scripts\python.exe -m ruff check src scripts tests
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m pip check
```

These verify local checks; they are not proof that a hosted GitHub Actions run
has executed. The CLI was not authenticated when publication was attempted, and
this project has no GitHub remote. Hosted execution is therefore pending.

## Publish once authentication is available

All commands below run from the repository root. The project is intended for
the existing `nihal-usman-chenganath` portfolio account. Authentication must be
completed by the account owner; do not paste passwords/tokens into chat or code.

```powershell
gh auth login
gh repo create retailcast-ml-engineering --public --source . --remote origin --push
gh run list --limit 5
```

Before publishing, review `git ls-files`: raw/processed data, bundles, model
pickles, `.env` files, databases, caches, and local logs are ignored. Publishing
the code does not publish those ignored assets. If the repository name already
exists, inspect it before adding a remote; never overwrite an unrelated project.

Once the workflow is visible:

```powershell
gh run watch
```

For a failed check, open its first failed step. Installation errors usually
indicate dependency/network issues; lint errors identify code locations; pytest
failures show expected versus actual behavior; Docker failures expose build or
startup logs. Fix locally, rerun the affected checks, commit, and push a new run.

Do not add a passing badge or claim successful GitHub CI until a hosted run is
actually green. There is no fabricated public repository URL in this project.
