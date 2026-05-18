\# AGENTS.md — GEE Screening App



\## Source of truth



Primary documents:



1\. `docs/PRD\_v0.5.md`

2\. `docs/DIRECTORY\_TREE\_v0.5.md`

3\. `notebooks/new.ipynb` as source notebook reference only



Follow `docs/PRD\_v0.5.md` over any older document.



The fixed PRD footer must read:



`End of PRD v0.5.`



\## Project goal



Build the GEE Screening Web App v1.



v1 includes:



1\. The defensible core GEE screening pipeline.

2\. The experimental classifier logic, but only as a neutralized, CLI-only, filesystem-only module.



\## Hard safety rules



\- Do not use `ee.Authenticate()` anywhere.

\- Earth Engine auth must be service-account only.

\- FastAPI must bind to `127.0.0.1` by default.

\- `/docs`, `/redoc`, and `/openapi.json` must be disabled.

\- No Docker for v1.

\- No PostgreSQL for v1.

\- No Supabase for v1.

\- No Redis, Celery, RQ, arq, or separate worker for v1.

\- v1 uses SQLite and FastAPI `BackgroundTasks`.

\- No coordinate-bearing public API responses.

\- No hashes, filesystem paths, geometry, bounds, raw coordinates, or CRS transforms in public DTOs.

\- All public JSON responses must pass the redaction contract.

\- All artifact serving must go through `serve\_artifact\_response()` and `can\_serve\_artifact()`.

\- Direct `FileResponse`, `StreamingResponse`, `open()`, or path streaming from API routes is forbidden outside the approved artifact-serving helper.

\- No telemetry.

\- No analytics.

\- No CDN-loaded frontend scripts.

\- No external fonts.



\## Experimental classifier rules



v1 includes classifier logic under:



`app/pipeline/stages\_experimental/`



Required v1 files:



\- `app/pipeline/stages\_experimental/\_\_init\_\_.py`

\- `app/pipeline/stages\_experimental/run.py`

\- `app/pipeline/stages\_experimental/inputs.py`

\- `app/pipeline/stages\_experimental/classes.py`

\- `app/pipeline/stages\_experimental/classifier.py`

\- `app/pipeline/stages\_experimental/outputs.py`

\- `app/pipeline/stages\_experimental/README.md`



Responsibilities:



\- `\_\_init\_\_.py` enforces `ENABLE\_EXPERIMENTAL=1`.

\- `run.py` is the only CLI entrypoint.

\- `inputs.py` validates that the core RUN status is `done`, required artifacts exist, required artifacts have correct classes, and required artifacts are GRID-consistent.

\- `classes.py` defines neutral class identifiers only: `Class\_A`, `Class\_B`, `Class\_C`, etc.

\- `classifier.py` implements neutralized classifier logic.

\- `outputs.py` writes classifier outputs as `FILESYSTEM\_ONLY`.

\- `README.md` documents local-only experimental status.



The classifier:



\- requires `ENABLE\_EXPERIMENTAL=1`;

\- runs only through CLI:

&#x20; `python -m app.pipeline.stages\_experimental.run --run-id <id>`;

\- is never called by FastAPI routes;

\- is never called by the frontend;

\- is never called by BackgroundTasks;

\- is never called by the core orchestrator;

\- is never run automatically after the core pipeline;

\- uses only neutral class identifiers: `Class\_A`, `Class\_B`, `Class\_C`, etc.;

\- writes all outputs as `FILESYSTEM\_ONLY`;

\- writes only under `./data/runs/<run\_id>/experimental/`;

\- never serves, lists, previews, tiles, or downloads classifier outputs through HTTP.



Original notebook classifier labels may appear only in:



`docs/CLASS\_MAPPING.md`



They must not appear in:



\- `app/`

\- `tests/`

\- logs

\- filenames

\- API responses

\- frontend files



\## Core pipeline rules



For `PARITY\_REPRODUCES` stages:



\- reproduce notebook operations and calculations;

\- use the same GRID;

\- use the same data-selection rules;

\- use the same formulas;

\- use the same processing order;

\- use the same numeric parameters;

\- outputs should match notebook reference artifacts except normalized metadata such as timestamps.



For `PARITY\_CORRECTS` stages:



\- intentionally differ only where the PRD says to correct a known notebook bug.

\- `IRON\_SWIR` must use:

&#x20; `(B11 - B12) / (B11 + B12)`



For `PARITY\_REPLACES` stages:



\- replace Colab/Drive/UI/auth-specific behavior with app infrastructure.



\## Artifact rules



Every artifact must have exactly one class:



\- `LOCAL\_SENSITIVE`

\- `REDACTED\_PUBLIC`

\- `PREVIEW\_ONLY`

\- `FILESYSTEM\_ONLY`



Classifier outputs are always:



`FILESYSTEM\_ONLY`



No artifact may be written without a class.



No artifact may be streamed without passing through:



`can\_serve\_artifact()`



No API route may directly stream files.



\## Redaction rules



Public DTOs must not expose:



\- latitude

\- longitude

\- raw coordinates

\- geometry

\- bounds

\- bbox

\- CRS transform

\- filesystem path

\- absolute path

\- hash

\- checksum

\- fingerprint

\- KMZ/KML/GeoJSON inline content

\- exact GRID transform

\- coordinate-bearing CSV columns



Run names are user-controlled public text and must be sanitized or rejected if they contain coordinate-like patterns or forbidden terms.



FastAPI validation errors must not echo request bodies or forbidden field names.



Outgoing JSON must be verified before response.



\## Storage and runtime



\- SQLite database path defaults to `./data/gee\_screening.db`.

\- `./data/` is gitignored.

\- Use SQLAlchemy and Alembic.

\- Do not use SQLite-specific advanced features that would block future PostgreSQL migration.

\- v1 allows one active run at a time.

\- Stages must not hold DB transactions open across EE calls, raster exports, or long computation.

\- Runs stuck in `running` after process restart must be marked stale or failed on startup.



\## Development process



Work milestone by milestone.



For every Codex task:



1\. inspect the relevant PRD section first;

2\. make the smallest coherent change;

3\. add or update tests;

4\. run tests if possible;

5\. report files changed, commands run, test results, and remaining work;

6\. stop after the requested milestone.



Do not expand scope unless explicitly asked.



\## Standard commands



Install:



```bash

python -m venv .venv

source .venv/bin/activate

pip install -e ".\[dev]"

