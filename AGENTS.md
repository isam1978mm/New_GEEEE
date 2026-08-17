# AGENTS.md — GEE Screening App

## Source of truth

Primary documents:

1. `docs/PRD_v0.5.md`
2. `docs/DIRECTORY_TREE_v0.5.md`
3. `notebooks/new.ipynb` as source notebook reference only

Follow `docs/PRD_v0.5.md` over any older document.

The fixed PRD footer must read:

`End of PRD v0.5.`

## Canonical local runtime

- The operator's canonical FastAPI port is **8007**.
- The canonical local backend base URL is **`http://127.0.0.1:8007`**.
- When giving local app, `curl`, PowerShell, browser, health-check, readiness-check, or API commands, use port **8007** unless the operator explicitly changes it.
- **Do not infer or substitute Uvicorn's default port 8000.** Port 8000 is not the project port.
- Purpose-specific local test harnesses may use their own explicitly documented ports (for example OIDC/JWKS harness ports); those do not change the main app port of 8007.

## Project goal

Build the GEE Screening Web App v1.

v1 includes:

1. The defensible core GEE screening pipeline.
2. The experimental classifier logic, but only as a neutralized, CLI-only, filesystem-only module.

## Hard safety rules

- Do not use `ee.Authenticate()` anywhere.
- Earth Engine auth must be service-account only.
- FastAPI must bind to `127.0.0.1` by default.
- `/docs`, `/redoc`, and `/openapi.json` must be disabled.
- No Docker for v1.
- No PostgreSQL for v1.
- No Supabase for v1.
- No Redis, Celery, RQ, arq, or separate worker for v1.
- v1 uses SQLite and FastAPI `BackgroundTasks`.
- No coordinate-bearing public API responses.
- No hashes, filesystem paths, geometry, bounds, raw coordinates, or CRS transforms in public DTOs.
- All public JSON responses must pass the redaction contract.
- All artifact serving must go through `serve_artifact_response()` and `can_serve_artifact()`.
- Direct `FileResponse`, `StreamingResponse`, `open()`, or path streaming from API routes is forbidden outside the approved artifact-serving helper.
- No telemetry.
- No analytics.
- No CDN-loaded frontend scripts.
- No external fonts.

## Experimental classifier rules

v1 includes classifier logic under:

`app/pipeline/stages_experimental/`

Required v1 files:

- `app/pipeline/stages_experimental/__init__.py`
- `app/pipeline/stages_experimental/run.py`
- `app/pipeline/stages_experimental/inputs.py`
- `app/pipeline/stages_experimental/classes.py`
- `app/pipeline/stages_experimental/classifier.py`
- `app/pipeline/stages_experimental/outputs.py`
- `app/pipeline/stages_experimental/README.md`

Responsibilities:

- `__init__.py` enforces `ENABLE_EXPERIMENTAL=1`.
- `run.py` is the only CLI entrypoint.
- `inputs.py` validates that the core RUN status is `done`, required artifacts exist, required artifacts have correct classes, and required artifacts are GRID-consistent.
- `classes.py` defines neutral class identifiers only: `Class_A`, `Class_B`, `Class_C`, etc.
- `classifier.py` implements neutralized classifier logic.
- `outputs.py` writes classifier outputs as `FILESYSTEM_ONLY`.
- `README.md` documents local-only experimental status.

The classifier:

- requires `ENABLE_EXPERIMENTAL=1`;
- runs only through CLI:
  `python -m app.pipeline.stages_experimental.run --run-id <id>`;
- is never called by FastAPI routes;
- is never called by the frontend;
- is never called by BackgroundTasks;
- is never called by the core orchestrator;
- is never run automatically after the core pipeline;
- uses only neutral class identifiers: `Class_A`, `Class_B`, `Class_C`, etc.;
- writes all outputs as `FILESYSTEM_ONLY`;
- writes only under `./data/runs/<run_id>/experimental/`;
- never serves, lists, previews, tiles, or downloads classifier outputs through HTTP.

Original notebook classifier labels may appear only in:

`docs/CLASS_MAPPING.md`

They must not appear in:

- `app/`
- `tests/`
- logs
- filenames
- API responses
- frontend files

## Core pipeline rules

For `PARITY_REPRODUCES` stages:

- reproduce notebook operations and calculations;
- use the same GRID;
- use the same data-selection rules;
- use the same formulas;
- use the same processing order;
- use the same numeric parameters;
- outputs should match notebook reference artifacts except normalized metadata such as timestamps.

For `PARITY_CORRECTS` stages:

- intentionally differ only where the PRD says to correct a known notebook bug.
- `IRON_SWIR` must use:
  `(B11 - B12) / (B11 + B12)`

For `PARITY_REPLACES` stages:

- replace Colab/Drive/UI/auth-specific behavior with app infrastructure.

## Artifact rules

Every artifact must have exactly one class:

- `LOCAL_SENSITIVE`
- `REDACTED_PUBLIC`
- `PREVIEW_ONLY`
- `FILESYSTEM_ONLY`

Classifier outputs are always:

`FILESYSTEM_ONLY`

No artifact may be written without a class.

No artifact may be streamed without passing through:

`can_serve_artifact()`

No API route may directly stream files.

## Redaction rules

Public DTOs must not expose:

- latitude
- longitude
- raw coordinates
- geometry
- bounds
- bbox
- CRS transform
- filesystem path
- absolute path
- hash
- checksum
- fingerprint
- KMZ/KML/GeoJSON inline content
- exact GRID transform
- coordinate-bearing CSV columns

Run names are user-controlled public text and must be sanitized or rejected if they contain coordinate-like patterns or forbidden terms.

FastAPI validation errors must not echo request bodies or forbidden field names.

Outgoing JSON must be verified before response.

## Storage and runtime

- SQLite database path defaults to `./data/gee_screening.db`.
- `./data/` is gitignored.
- Use SQLAlchemy and Alembic.
- Do not use SQLite-specific advanced features that would block future PostgreSQL migration.
- v1 allows one active run at a time.
- Stages must not hold DB transactions open across EE calls, raster exports, or long computation.
- Runs stuck in `running` after process restart must be marked stale or failed on startup.

## Development process

Work milestone by milestone.

For every Codex task:

1. inspect the relevant PRD section first;
2. make the smallest coherent change;
3. add or update tests;
4. run tests if possible;
5. report files changed, commands run, test results, and remaining work;
6. stop after the requested milestone.

Do not expand scope unless explicitly asked.

## Standard commands

Install:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Run tests:

```bash
pytest tests/unit/
pytest tests/integration/
pytest tests/notebook_parity/
```

Run app:

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8007
```

## Forbidden implementation choices

Do not add:

- Docker as a v1 requirement;
- PostgreSQL as a v1 requirement;
- Supabase as a v1 requirement;
- Redis or queue broker;
- public auth;
- public deployment config;
- telemetry;
- analytics;
- CDN-loaded frontend scripts;
- external fonts;
- automatic imagery ordering;
- classifier API routes;
- classifier frontend controls;
- classifier BackgroundTasks invocation;
- classifier core-orchestrator invocation.
