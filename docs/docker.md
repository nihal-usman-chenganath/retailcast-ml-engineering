# Docker and local deployment

An **image** is a packaged application filesystem plus startup instructions.
A **container** is a running instance of that image. Our image contains only
inference dependencies, source code, the saved model, and aggregate history.
MLflow, notebooks, raw Excel files, local databases, and secrets stay outside it.

## Build and run (PowerShell, repository root)

Prerequisite: Docker Desktop is running with its Linux engine. The final model
and prepared history must exist locally.

```powershell
.\.venv\Scripts\python.exe -m src.api.bundle
docker compose build
docker compose up -d
.\.venv\Scripts\python.exe scripts/smoke_api.py --wait-seconds 60
```

The bundle command prepares the three files needed for inference. `compose build`
executes the Dockerfile to create the image. `compose up -d` runs it in the
background. The smoke script waits for readiness and checks real HTTP requests.

Open http://127.0.0.1:8000/docs. The native Windows service, if running, uses
port 8001, so it can coexist with the container on port 8000.

Equivalent direct image build:

```powershell
docker build -t retailcast:local .
docker run --rm -p 127.0.0.1:8002:8000 retailcast:local
```

That container is accessible on port 8002. The left side is the host port; the
right side is the container's internal port. `--rm` removes that container when
it exits; it does not remove source data or the image.

## Inspect and stop

```powershell
docker compose ps
docker compose logs --tail 30 api
docker stats --no-stream
docker compose down
```

`ps` shows state/health, `logs` shows request events, and `stats` reports current
resource usage. `down` stops/removes this project's container/network; generated
model/history files remain in the project folder.

## Runtime choices

- Python 3.11 base image pinned by digest; model loading checks Python major/minor
  and exact scikit-learn/joblib versions. Refresh dependency/base pins in a tested
  maintenance change rather than silently following mutable versions.
- Non-root user, read-only root filesystem under Compose, dropped capabilities,
  no privilege escalation, bounded writable `/tmp`, log rotation, 768 MiB memory
  and one CPU configured for the local Compose service.
- Port mapped only to localhost. No Docker registry push or cloud deployment is
  performed by these commands.
- The Dockerfile supports a `PORT` environment variable for a future host and
  includes a real HTTP health check. Health status may take 30 seconds to update.

## Troubleshooting

| Symptom | Meaning and action |
| --- | --- |
| Missing Docker engine pipe | Docker CLI exists but Desktop/Linux engine is not running; start Desktop |
| `serving_bundle` missing during build | Run the bundle command after training/preparation |
| Port already allocated | Stop the conflicting local service or change the host-side port |
| Checksum/version startup error | Rebuild a trusted bundle with matching dependencies; do not disable checks |
| Dependency download timeout | Check network access and rerun the build; cached completed layers are reused |

The `docker` Python package installed by MLflow is not the Docker engine. The
container verification requires the actual Desktop engine, which is checked
separately.
