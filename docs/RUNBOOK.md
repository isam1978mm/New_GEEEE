# Runbook

## Purpose

This runbook covers local v1 operation of the GEE Screening Web App.

v1 is local-first:

- FastAPI binds to `127.0.0.1` by default.
- SQLite is the only supported v1 database.
- The core pipeline runs through FastAPI `BackgroundTasks`.
- The experimental classifier remains CLI-only and `FILESYSTEM_ONLY`.

This document is operational guidance, not a deployment guide.

## Install

Create a virtual environment and install the project with development dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Windows PowerShell equivalent:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

## `.env` Setup

Copy `.env.example` to `.env`.

Minimum expected settings:

- `ALLOW_NETWORK_BIND=false`
- `DATA_DIR=./data`
- `DATABASE_PATH=./data/gee_screening.db`
- `EE_SERVICE_ACCOUNT_EMAIL=<service-account-email>`
- `EE_SERVICE_ACCOUNT_KEY_PATH=<path-to-service-account-key.json>`

Notes:

- `ALLOW_NETWORK_BIND=false` keeps the app on loopback-only `127.0.0.1`.
- Earth Engine readiness depends on the service-account values being valid.
- Do not commit `.env` or service-account key files.

## Database Migration

Apply migrations before first startup and after schema changes:

```bash
alembic upgrade head
```

Check the current migration head if needed:

```bash
alembic current
alembic heads
```

SQLite discipline for v1:

- Treat SQLite as the active runtime database for v1.
- Use Alembic batch mode for future SQLite schema changes.
- Before v2, test future migrations against both SQLite and the intended PostgreSQL target.
- Do not rely on SQLite-only schema features that would block that migration path.

## Startup

Canonical local startup command:

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

What startup does:

- creates required data directories under `./data`
- opens the SQLite engine
- marks any stale `running` runs as `stale_failed`
- serves the SPA from `/`
- exposes `/healthz`, `/readyz`, `/runs`, and guarded artifact routes

## Verify Startup

Verify liveness:

```bash
curl http://127.0.0.1:8000/healthz
```

Verify readiness:

```bash
curl http://127.0.0.1:8000/readyz
```

Expected behavior:

- `/healthz` returns success when the app process is up.
- `/readyz` returns ready only when the Earth Engine service account can initialize safely.

## Stop the App Cleanly

If the server is running in the foreground shell, stop it with `Ctrl+C`.

If it was started under another process supervisor, stop it through that supervisor and wait for the process to exit cleanly before editing `.env`, rotating keys, or taking backups.

## Submit a Run

Create a run through the local API:

```bash
curl -X POST http://127.0.0.1:8000/runs \
  -H "Content-Type: application/json" \
  -d "{\"lat\": <lat>, \"lon\": <lon>, \"name\": \"<safe-public-name>\"}"
```

Request notes:

- `lat` and `lon` are accepted on input only.
- `name` is optional public text.
- coordinate-like or forbidden `name` content is rejected.

Response notes:

- the response returns public-safe run fields only
- coordinates are not echoed

## Check Run Status

List recent runs:

```bash
curl http://127.0.0.1:8000/runs
```

Inspect one run:

```bash
curl http://127.0.0.1:8000/runs/<run_id>
```

Status behavior:

- only one active core run is allowed at a time in v1
- a second `POST /runs` during `queued` or `running` returns a conflict
- `GET /runs/<run_id>` returns only public-safe run fields and publicly listable artifacts

## Retrieve Artifacts

Fetch an artifact through the guarded artifact route:

```bash
curl -OJ http://127.0.0.1:8000/runs/<run_id>/artifacts/<artifact_name>
```

Artifact access rules:

- all artifact serving goes through the guarded artifact helper
- `LOCAL_SENSITIVE` artifacts are servable only on `127.0.0.1`
- `LOCAL_SENSITIVE` artifacts are blocked if `ALLOW_NETWORK_BIND=1`
- `FILESYSTEM_ONLY` artifacts are never served
- experimental artifacts are never listed or served over HTTP

Operational implication:

- `GET /runs/<run_id>` will not list `LOCAL_SENSITIVE` or `FILESYSTEM_ONLY` artifacts as public artifacts
- retrieve only artifacts that are intentionally exposed by policy

## Parity Tests

Run the current local verification suite:

```bash
pytest tests/unit/ tests/integration/ tests/notebook_parity/
```

Reference-output parity notes:

- the notebook parity suite is expected to skip large frozen-reference checks when the reference fixture set is absent
- skip output should clearly name the missing reference file or directory
- parity mismatches fail when the required reference fixtures are present

## Earth Engine Key Rotation

When rotating the Earth Engine service-account key:

1. Stop the app cleanly.
2. Replace the key file at the new secured location.
3. Update `EE_SERVICE_ACCOUNT_KEY_PATH` in `.env` if the path changed.
4. Restart the app with the canonical `uvicorn` command.
5. Verify:

```bash
curl http://127.0.0.1:8000/readyz
```

Rotation rules:

- never use `ee.Authenticate()`
- keep service-account credentials out of git
- remove superseded local key files once the replacement is verified

## Backups

For local operational backups, stop the app first, then back up:

- `./data/gee_screening.db`
- `./data/runs/`

Recommended practice:

- keep database and run-directory backups from the same stopped state
- preserve file timestamps where practical
- treat run artifacts as sensitive local data

Restore check:

1. restore `./data/`
2. run `alembic upgrade head`
3. start the app
4. verify `/healthz` and `/readyz`
5. inspect `GET /runs`

## Stale Run Recovery

On app startup, any run left in `running` state from a prior interrupted process is marked `stale_failed`.

Operational use:

1. restart the app
2. inspect `GET /runs` or `GET /runs/<run_id>`
3. confirm interrupted runs no longer remain `running`
4. submit a new run only after the active-run slot is clear

## Windows Pytest Cache and Temp Workaround

The v1 verification workflow on Windows may need a writable temp root for pytest.

Recommended local workaround:

1. Set `TEMP` and `TMP` to a writable directory.
2. Run pytest with `--basetemp` pointing to a writable temp path.
3. If the local pytest cache is unwritable, add `-p no:cacheprovider` or use `--cache-clear`.

Example PowerShell session:

```powershell
$env:TEMP = "C:\tmp\pytest-temp"
$env:TMP = "C:\tmp\pytest-temp"
python -m pytest tests/unit/ tests/integration/ tests/notebook_parity/ --basetemp C:\tmp\pytest-temp\basetemp
```

If the cache provider is the problem:

```powershell
python -m pytest tests/unit/ tests/integration/ tests/notebook_parity/ --basetemp C:\tmp\pytest-temp\basetemp -p no:cacheprovider
```

Or:

```powershell
python -m pytest tests/unit/ tests/integration/ tests/notebook_parity/ --basetemp C:\tmp\pytest-temp\basetemp --cache-clear
```

Do not change `pyproject.toml` for this unless a future test proves that a repo-level config change is necessary.
