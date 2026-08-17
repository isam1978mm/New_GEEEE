# GEE Screening App

Local-first GEE screening web app v1.

## Scope

v1 includes:

- The defensible core screening pipeline.
- A quarantined experimental classifier module that is neutralized, CLI-only, and filesystem-only.

The default app surface is local-only. FastAPI binds to `127.0.0.1` by default, `/docs`, `/redoc`, and `/openapi.json` are disabled, and artifact downloads go only through the guarded artifact route.

**Canonical local backend:** `http://127.0.0.1:8007`. Port `8007` is the project convention; do not substitute Uvicorn's default `8000`.

VPS deployment is a separate future milestone and is not assumed by the local-first track.

A local-only Generic OIDC development harness is available at [docs/LOCAL_1_OIDC_DEV_HARNESS.md](docs/LOCAL_1_OIDC_DEV_HARNESS.md) for testing the OIDC valid-token path on a developer machine with no real provider, secret, token, or deployment.

The local operator UI token handoff contract is documented at [docs/LOCAL_2_OPERATOR_UI_TOKEN_HANDOFF.md](docs/LOCAL_2_OPERATOR_UI_TOKEN_HANDOFF.md). It remains local-only and adds no login UI and no token storage.

The full local auth regression closeout is documented at [docs/LOCAL_3_FULL_AUTH_REGRESSION_CLOSEOUT.md](docs/LOCAL_3_FULL_AUTH_REGRESSION_CLOSEOUT.md). The local Generic OIDC readiness track is complete; VPS deployment remains separate and not started.

D1 real frozen-reference collection remains outside Git and is documented in [docs/D1_REAL_REFERENCE_COLLECTION_OUTSIDE_GIT.md](docs/D1_REAL_REFERENCE_COLLECTION_OUTSIDE_GIT.md). Real references are operator-owned outside Git only; notebook-value parity remains unverified until the real Phase E/E3/E4 verifiers pass.

Operator auth UI planning and the pre-implementation checklist are documented at [docs/UI_AUTH_OPERATOR_LOGIN_PLAN_AND_CHECKLIST.md](docs/UI_AUTH_OPERATOR_LOGIN_PLAN_AND_CHECKLIST.md).

The operator auth login/logout UX wireframe and state model are documented at [docs/UI_AUTH_1_LOGIN_LOGOUT_UX_STATE_MODEL.md](docs/UI_AUTH_1_LOGIN_LOGOUT_UX_STATE_MODEL.md).

A local operator session shell is implemented for development use only. It keeps the operator session in page memory, forwards it through the existing private-preview handoff path, and adds no real provider, provider SDK, persistence, Supabase, or VPS deployment.

The real map point picker replacement is documented at [docs/UI_MAP_1_REAL_POINT_PICKER.md](docs/UI_MAP_1_REAL_POINT_PICKER.md). It replaces the fake local grid picker with a tile-based map click target picker while keeping external tiles controlled by Settings.

## Safety constants

- Earth Engine auth is service-account only.
- `ee.Authenticate()` is forbidden.
- No Docker requirement for v1.
- No PostgreSQL, Supabase, Redis, Celery, RQ, arq, or separate worker for v1.
- No telemetry or analytics.
- No CDN-loaded scripts or external fonts.
- No public API response may expose coordinates, geometry, bounds, filesystem paths, hashes, or CRS transforms.
- Experimental outputs are always `FILESYSTEM_ONLY` and are never listed or served over HTTP.

See [docs/SAFETY_CONSTANTS.md](docs/SAFETY_CONSTANTS.md), [docs/PIPELINE.md](docs/PIPELINE.md), and [docs/EXPERIMENTAL_MODULE.md](docs/EXPERIMENTAL_MODULE.md).

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
- Local FastAPI commands use port `8007`.
- `EE_SERVICE_ACCOUNT_EMAIL` and `EE_SERVICE_ACCOUNT_KEY_PATH` are required for Earth Engine readiness.
- `DATA_DIR` and `DATABASE_PATH` default to `./data` and `./data/gee_screening.db`.

## Run the app

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8007
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
