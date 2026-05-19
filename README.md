# GEE Screening App

Local-first GEE screening web app v1.

## Scope

v1 includes:

- The defensible core screening pipeline.
- A quarantined experimental classifier module that is neutralized, CLI-only, and filesystem-only.

The default app surface is local-only. FastAPI binds to `127.0.0.1` by default, `/docs`, `/redoc`, and `/openapi.json` are disabled, and artifact downloads go only through the guarded artifact route.

## Safety constants

- Earth Engine auth is service-account only.
- `ee.Authenticate()` is forbidden.
- No Docker requirement for v1.
- No PostgreSQL, Supabase, Redis, Celery, RQ, arq, or separate worker for v1.
- No telemetry or analytics.
- No CDN-loaded scripts or external fonts.
- No public API response may expose coordinates, geometry, bounds, filesystem paths, hashes, or CRS transforms.
- Experimental outputs are always `FILESYSTEM_ONLY` and are never listed or served over HTTP.

See [docs/SAFETY_CONSTANTS.md](/C:/Dev/New_GEE/docs/SAFETY_CONSTANTS.md), [docs/PIPELINE.md](/C:/Dev/New_GEE/docs/PIPELINE.md), and [docs/EXPERIMENTAL_MODULE.md](/C:/Dev/New_GEE/docs/EXPERIMENTAL_MODULE.md).

## Local setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

The core app runs without Docker. SQLite defaults to `./data/gee_screening.db`.

## Configuration

Copy `.env.example` to `.env`.

Core settings:

- `ALLOW_NETWORK_BIND=false` keeps the app on `127.0.0.1`.
- `EE_SERVICE_ACCOUNT_EMAIL` and `EE_SERVICE_ACCOUNT_KEY_PATH` are required for Earth Engine readiness.
- `DATA_DIR` and `DATABASE_PATH` default to `./data` and `./data/gee_screening.db`.

## Run the app

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

The root path serves the local SPA. `/healthz` returns liveness. `/readyz` returns ready only when the Earth Engine service account can initialize.

## Experimental classifier

The experimental module is opt-in and never runs from the web app, frontend, background tasks, or the core orchestrator.

The only allowed invocation is:

```bash
ENABLE_EXPERIMENTAL=1 python -m app.pipeline.stages_experimental.run --run-id <id>
```

Rules:

- Import requires `ENABLE_EXPERIMENTAL=1`.
- Inputs must come from a completed core run.
- Outputs write only under `./data/runs/<run_id>/experimental/`.
- Every experimental artifact is `FILESYSTEM_ONLY`.
- No experimental output is listed, previewed, tiled, or downloadable through HTTP.

## Tests

```bash
pytest tests/unit/
pytest tests/integration/
pytest tests/notebook_parity/
```

The notebook parity suite covers only the defensible core stages. The experimental classifier has contract tests outside `tests/notebook_parity/`.
