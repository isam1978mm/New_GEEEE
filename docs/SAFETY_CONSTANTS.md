# Safety Constants

These constants define the v1 deployment and data-exposure boundary.

## Surface

- FastAPI binds to `127.0.0.1` by default.
- `/docs`, `/redoc`, and `/openapi.json` stay disabled.
- The SPA is served locally from the app process.
- No CDN-loaded scripts, external fonts, telemetry, or analytics are allowed.

## Auth and runtime

- Earth Engine uses service-account authentication only.
- `ee.Authenticate()` is forbidden anywhere in `app/` and `tests/`.
- v1 uses SQLite plus FastAPI `BackgroundTasks`.
- v1 does not require Docker.
- v1 does not use PostgreSQL, Supabase, Redis, Celery, RQ, arq, or a separate worker.

## Redaction

Public HTTP responses must not expose:

- latitude or longitude
- raw coordinates or geometry
- bounds, bbox, or CRS transforms
- filesystem paths or absolute paths
- hashes, checksums, or fingerprints
- coordinate-bearing CSV columns

Outgoing JSON passes through the redaction verifier before it leaves the app.

## Artifact policy

Artifacts must always be assigned exactly one class:

- `LOCAL_SENSITIVE`
- `REDACTED_PUBLIC`
- `PREVIEW_ONLY`
- `FILESYSTEM_ONLY`

All artifact downloads route through `serve_artifact_response()` and `can_serve_artifact()`.

- `FILESYSTEM_ONLY` is never served.
- `LOCAL_SENSITIVE` is blocked when `ALLOW_NETWORK_BIND=1`.
- Experimental outputs are always `FILESYSTEM_ONLY`.

## Experimental boundary

- `app.pipeline.stages_experimental` requires `ENABLE_EXPERIMENTAL=1` to import.
- The only allowed execution path is `python -m app.pipeline.stages_experimental.run --run-id <id>`.
- The API, frontend, background tasks, and core orchestrator must not invoke the experimental module.
