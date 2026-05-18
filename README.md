# GEE Screening App

Local-only FastAPI scaffold for the GEE Screening Web App v1.

## Scope

This repository currently contains the M0 safety foundation only:

- FastAPI bound to `127.0.0.1` by default
- `/healthz` liveness endpoint
- `/readyz` readiness endpoint that fails safely until Earth Engine service-account configuration exists
- `/docs`, `/redoc`, and `/openapi.json` disabled

The v1 app uses service-account-only Earth Engine authentication. `ee.Authenticate()` is forbidden.

## Non-goals for v1

- No Docker requirement
- No PostgreSQL
- No Supabase
- No Redis, Celery, RQ, arq, or separate worker
- No telemetry or analytics
- No CDN-loaded frontend scripts or external fonts

## Local setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Environment

Copy `.env.example` to `.env` and fill in service-account values when ready. `ALLOW_NETWORK_BIND` defaults to `false`, so the app binds to `127.0.0.1`.

## Run

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## Tests

```bash
pytest tests/unit/
pytest tests/integration/
```
