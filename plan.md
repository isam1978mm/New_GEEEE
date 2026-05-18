# plan.md — Codex Goal Plan for GEE Screening App v1

This file defines the Codex goals for implementing the project. Codex should read this file together with `AGENTS.md`, `docs/PRD_v0.5.md`, and `docs/DIRECTORY_TREE_v0.5.md`.

## How to use this file in Codex

For each Codex task, paste only one short instruction into the Codex Goal box, for example:

```text
Read AGENTS.md and plan.md. Implement Goal M0 only. Stop after M0 and report files changed, commands run, and test results.
```

After M0 passes, start a new Codex task:

```text
Read AGENTS.md and plan.md. Implement Goal M1 only. Stop after M1 and report files changed, commands run, and test results.
```

Do not ask Codex to implement multiple goals at once unless explicitly directed.

---

## Global rules for every goal

Codex must always follow these rules:

- Read `AGENTS.md` first.
- Read `docs/PRD_v0.5.md` for requirements.
- Read `docs/DIRECTORY_TREE_v0.5.md` for expected structure.
- Use `notebooks/new.ipynb` only as the source notebook reference.
- Make the smallest coherent change for the requested goal.
- Add or update tests for the requested goal.
- Run the listed validation commands when possible.
- Stop after the requested goal.
- Do not expand scope.
- Do not add Docker as a v1 requirement.
- Do not add PostgreSQL/Supabase as a v1 requirement.
- Do not add Redis, Celery, RQ, arq, or a separate worker process for v1.
- Do not add `ee.Authenticate()` anywhere.
- Do not expose coordinates, geometry, hashes, filesystem paths, or classifier outputs through public HTTP responses.
- Do not create API/frontend/default-pipeline access to `stages_experimental`.

---

# Goal M0 — Repository skeleton and safety foundation

## Scope

Create/update:

- `pyproject.toml`
- `README.md`
- `.env.example`
- `.gitignore`
- `app/__init__.py`
- `app/main.py`
- `app/config.py`
- `app/errors.py`
- `app/logging_config.py`
- `app/api/__init__.py`
- `app/api/health.py`
- `tests/unit/test_app_startup.py`
- `tests/unit/test_openapi_disabled.py`
- `tests/unit/test_bind_defaults.py`

## Requirements

- FastAPI app starts.
- `/healthz` returns 200.
- `/readyz` exists and returns a safe not-ready response until EE setup exists.
- `/docs`, `/redoc`, and `/openapi.json` are disabled.
- Default host setting is `127.0.0.1`.
- `ALLOW_NETWORK_BIND` defaults false.
- No Docker.
- No PostgreSQL.
- No Redis/queue worker.
- No `ee.Authenticate()`.
- Do not implement DB yet.
- Do not implement pipeline stages yet.
- Do not implement frontend yet.
- Do not implement the experimental classifier yet.

## Validation

```bash
pytest tests/unit/
```

## Stop condition

Stop after M0 and report files changed, commands run, test results, and blockers.

---

# Goal M1 — SQLite persistence and migrations

## Scope

Create/update:

- `app/db/__init__.py`
- `app/db/base.py`
- `app/db/session.py`
- `app/db/models/__init__.py`
- `app/db/models/run.py`
- `app/db/models/artifact.py`
- `app/db/models/enums.py`
- `alembic.ini`
- `alembic/env.py`
- `alembic/versions/0001_runs_and_artifacts.py`
- `tests/unit/test_db_models.py`
- `tests/integration/test_db_clean_checkout.py`

## Requirements

- SQLite database path defaults to `./data/gee_screening.db`.
- Use SQLAlchemy.
- Use Alembic.
- Runs table has id, name, status, internal coordinate fields, timestamps.
- Artifacts table has id, run_id, name, relative_path, size, internal hash field, artifact_class enum, http_servable, timestamps.
- `artifact_class` is non-null.
- No SQLite-specific advanced features that block future PostgreSQL migration.
- No Docker.
- No PostgreSQL.

## Validation

```bash
pytest tests/unit/ tests/integration/
```

## Stop condition

Stop after M1 and report files changed, commands run, test results, and blockers.

---

# Goal M2 — Redaction, public errors, and logging safety

## Scope

Create/update:

- `app/services/redaction.py`
- `app/errors.py`
- `app/logging_config.py`
- `app/api/errors.py`
- `app/main.py`
- `tests/unit/test_redaction.py`
- `tests/unit/test_public_error_handler.py`
- `tests/unit/test_logging_redaction.py`

## Requirements

- Implement `redact()` and `verify_redacted()`.
- Public DTOs must not expose coordinates, geometry, bounds, CRS transforms, hashes, checksums, or filesystem paths.
- Pattern checks must be context-aware to avoid false positives for harmless scientific float pairs.
- FastAPI validation errors must use a custom safe error handler.
- Error responses must not echo request bodies or forbidden field names.
- Logging formatter applies redaction at INFO and above.
- If outgoing JSON verification fails, return HTTP 500 with a generic public error.

## Validation

```bash
pytest tests/unit/
```

## Stop condition

Stop after M2 and report files changed, commands run, test results, and blockers.

---

# Goal M3 — Artifact taxonomy and serving guard

## Scope

Create/update:

- `app/services/artifact_policy.py`
- `app/services/artifact_response.py`
- `app/services/storage.py`
- `app/api/artifacts.py`
- `scripts/check_no_direct_streaming.py`
- `tests/unit/test_artifact_policy.py`
- `tests/unit/test_artifact_response.py`
- `tests/unit/test_no_direct_file_streaming.py`
- `tests/integration/test_artifact_serving.py`

## Requirements

- Implement artifact class behavior for:
  - `LOCAL_SENSITIVE`
  - `REDACTED_PUBLIC`
  - `PREVIEW_ONLY`
  - `FILESYSTEM_ONLY`
- Implement `can_serve_artifact()`.
- Implement `serve_artifact_response()`.
- All artifact serving must route through `serve_artifact_response()`.
- API routes may not directly use `FileResponse`, `StreamingResponse`, `open()`, or direct filesystem streaming.
- `FILESYSTEM_ONLY` is never served.
- `LOCAL_SENSITIVE` is served only on `127.0.0.1`.
- `LOCAL_SENSITIVE` is blocked when `ALLOW_NETWORK_BIND=1`.
- Classifier outputs are never served.
- Class II redacted artifacts may be generated on demand.
- If cached, Class II artifacts must be registered as `REDACTED_PUBLIC`.

## Validation

```bash
pytest tests/unit/
pytest tests/integration/
```

## Stop condition

Stop after M3 and report files changed, commands run, test results, and blockers.

---

# Goal M4 — Earth Engine service-account session

## Scope

Create/update:

- `app/services/ee_session.py`
- `scripts/check_no_ee_authenticate.py`
- `tests/unit/test_ee_session.py`
- `tests/unit/test_no_ee_authenticate.py`

## Requirements

- EE auth is service-account only.
- No `ee.Authenticate()` anywhere.
- App readiness fails safely if EE service account cannot initialize.
- Service-account key path comes from `.env`/settings.
- No key file is committed.
- Test scanner fails if `ee.Authenticate()` appears anywhere in `app/` or `tests/`.

## Validation

```bash
pytest tests/unit/
```

## Stop condition

Stop after M4 and report files changed, commands run, test results, and blockers.

---

# Goal M5 — GRID, storage, run manifest, and run state machine

## Scope

Create/update:

- `app/services/grid.py`
- `app/services/storage.py`
- `app/pipeline/manifest.py`
- `app/services/run_state.py`
- `tests/unit/test_grid.py`
- `tests/unit/test_storage.py`
- `tests/unit/test_run_state_machine.py`

## Requirements

- Construct deterministic GRID from input lat/lon.
- Store internal coordinates only.
- Public DTOs do not expose coordinates.
- RUN directory created under `./data/runs/<run_id>/`.
- GRID manifest persisted internally.
- Stage manifests are `LOCAL_SENSITIVE`.
- On startup, stale running jobs are marked failed/stale.
- Only one active run at a time in v1.

## Validation

```bash
pytest tests/unit/
```

## Stop condition

Stop after M5 and report files changed, commands run, test results, and blockers.

---

# Goal M6 — Stage protocol and orchestrator

## Scope

Create/update:

- `app/pipeline/__init__.py`
- `app/pipeline/_base.py`
- `app/pipeline/stages/__init__.py`
- `app/pipeline/orchestrator.py`
- `tests/unit/test_stage_protocol.py`
- `tests/unit/test_orchestrator.py`
- `tests/unit/test_parity_metadata.py`

## Requirements

- Every Stage subclass declares `parity_category`.
- `PARITY_CORRECTS` and `PARITY_REPLACES` require `parity_reason`.
- Orchestrator refuses stages without parity metadata.
- Every artifact emission requires `artifact_class`.
- Writes without `artifact_class` raise `ArtifactClassError`.
- Orchestrator persists stage status.
- Orchestrator does not import or invoke `stages_experimental`.

## Validation

```bash
pytest tests/unit/
```

## Stop condition

Stop after M6 and report files changed, commands run, test results, and blockers.

---

# Goal M7 — DEM ingest and zero-shift gate

## Scope

Create/update:

- `app/pipeline/stages/grid.py`
- `app/pipeline/stages/dem.py`
- `app/pipeline/stages/zero_shift.py`
- `tests/unit/test_dem.py`
- `tests/unit/test_zero_shift.py`
- `tests/notebook_parity/test_dem_parity.py`

## Requirements

- Reproduce notebook DEM ingest calculations.
- Reproduce zero-shift gate logic.
- All outputs align to GRID.
- Drift raises `GridDriftError`.
- Artifacts are classified.
- Parity category is `PARITY_REPRODUCES`.

## Validation

```bash
pytest tests/unit/
pytest tests/notebook_parity/test_dem_parity.py
```

## Stop condition

Stop after M7 and report files changed, commands run, test results, and blockers.

---

# Goal M8 — Sentinel-1 SAR RTC stage

## Scope

Create/update:

- `app/pipeline/stages/sar_rtc.py`
- `tests/unit/test_sar_rtc.py`
- `tests/notebook_parity/test_sar_parity.py`

## Requirements

- Reproduce notebook SAR RTC calculations for the canonical SAR cell.
- Produce `VV_dB.tif`, `VH_dB.tif`, `logRatio_dB.tif`, `incidence.tif`.
- Preserve GRID alignment.
- No `ee.Authenticate()`.
- Artifact classes assigned.
- Parity category is `PARITY_REPRODUCES`.

## Validation

```bash
pytest tests/unit/test_sar_rtc.py
pytest tests/notebook_parity/test_sar_parity.py
```

## Stop condition

Stop after M8 and report files changed, commands run, test results, and blockers.

---

# Goal M9 — Sentinel-2 indices with corrected IRON_SWIR

## Scope

Create/update:

- `app/pipeline/stages/s2_indices.py`
- `tests/unit/test_s2_indices.py`
- `tests/notebook_parity/test_s2_parity.py`
- `docs/PARITY_EXCEPTIONS.md` if needed

## Requirements

- Produce NDVI, NDWI, NDMI, NBR, IRONOX, IRON_SWIR, and BSI.
- `IRON_SWIR` must use `(B11 - B12) / (B11 + B12)`.
- Do not use the notebook bug formula.
- The stage parity category is `PARITY_CORRECTS` because of `IRON_SWIR`.
- Test asserts the corrected formula.
- Other S2 calculations reproduce notebook behavior where applicable.
- Outputs align to GRID.

## Validation

```bash
pytest tests/unit/test_s2_indices.py
pytest tests/notebook_parity/test_s2_parity.py
```

## Stop condition

Stop after M9 and report files changed, commands run, test results, and blockers.

---

# Goal M10 — DEM derivatives and thermal LST

## Scope

Create/update:

- `app/pipeline/stages/dem_derivatives.py`
- `app/pipeline/stages/thermal.py`
- `tests/unit/test_dem_derivatives.py`
- `tests/unit/test_thermal.py`
- `tests/notebook_parity/test_dem_derivatives_parity.py`
- `tests/notebook_parity/test_thermal_parity.py`

## Requirements

- Reproduce DEM derivative calculations.
- Reproduce Landsat thermal LST stage.
- Outputs align to GRID.
- Artifacts are classified.
- Parity category is `PARITY_REPRODUCES` unless PRD says otherwise.

## Validation

```bash
pytest tests/unit/
pytest tests/notebook_parity/test_dem_derivatives_parity.py
pytest tests/notebook_parity/test_thermal_parity.py
```

## Stop condition

Stop after M10 and report files changed, commands run, test results, and blockers.

---

# Goal M11 — Hypercube assembly and PCA anomaly

## Scope

Create/update:

- `app/pipeline/stages/hypercube.py`
- `app/pipeline/stages/pca_anomaly.py`
- `tests/unit/test_hypercube.py`
- `tests/unit/test_pca_anomaly.py`
- `tests/notebook_parity/test_hypercube_parity.py`
- `tests/notebook_parity/test_pca_parity.py`

## Requirements

- Reproduce notebook hypercube assembly.
- Reproduce PCA anomaly calculations.
- Persist eigenvalue report.
- Outputs align to GRID.
- Randomness, if any, is seeded and persisted.
- Artifacts are classified.
- Parity category is `PARITY_REPRODUCES`.

## Validation

```bash
pytest tests/unit/
pytest tests/notebook_parity/test_hypercube_parity.py
pytest tests/notebook_parity/test_pca_parity.py
```

## Stop condition

Stop after M11 and report files changed, commands run, test results, and blockers.

---

# Goal M12 — Object extraction and alignment QA

## Scope

Create/update:

- `app/pipeline/stages/object_extract.py`
- `app/pipeline/stages/alignment_qa.py`
- `tests/unit/test_object_extract.py`
- `tests/unit/test_alignment_qa.py`
- `tests/notebook_parity/test_objects_parity.py`
- `tests/notebook_parity/test_alignment_parity.py`

## Requirements

- Reproduce notebook object extraction.
- Reproduce `clusters_summary` behavior where part of the defensible pipeline.
- Produce per-object NPY patches.
- Reproduce alignment QA checks.
- Public object tables must not expose coordinates.
- Class II object CSV uses row/column pixel offsets only.
- Outputs align to GRID.
- Artifacts are classified.
- Parity category is `PARITY_REPRODUCES`.

## Validation

```bash
pytest tests/unit/
pytest tests/notebook_parity/test_objects_parity.py
pytest tests/notebook_parity/test_alignment_parity.py
```

## Stop condition

Stop after M12 and report files changed, commands run, test results, and blockers.

---

# Goal M13 — Notebook parity suite and fixture protocol

## Scope

Create/update:

- `tests/notebook_parity/README.md`
- `docs/PARITY_PROTOCOL.md`
- `docs/PARITY_EXCEPTIONS.md`
- `tests/notebook_parity/conftest.py`
- `tests/notebook_parity/fixtures/reference_run/README.md`
- `tests/unit/test_parity_category_consistency.py`

## Requirements

- Document how reference notebook outputs are captured.
- Document known corrections, especially `IRON_SWIR`.
- Tests know the difference between `PARITY_REPRODUCES`, `PARITY_CORRECTS`, and `PARITY_REPLACES`.
- Test collection fails if a parity test category disagrees with the Stage class metadata.
- Do not commit huge binary fixtures unless PRD decision says to.

## Validation

```bash
pytest tests/unit/test_parity_category_consistency.py
pytest tests/notebook_parity/
```

## Stop condition

Stop after M13 and report files changed, commands run, test results, and blockers.

---

# Goal M14 — Experimental classifier neutralization

## Scope

Create/update:

- `app/pipeline/stages_experimental/__init__.py`
- `app/pipeline/stages_experimental/classes.py`
- `app/pipeline/stages_experimental/classifier.py`
- `app/pipeline/stages_experimental/README.md`
- `docs/CLASS_MAPPING.md`
- `tests/unit/test_experimental_gate.py`
- `tests/unit/test_forbidden_terms.py`

## Requirements

- `ENABLE_EXPERIMENTAL=1` is required to import the package.
- Classifier code uses only neutral identifiers: `Class_A` through `Class_N`.
- Original notebook label mapping lives only in `docs/CLASS_MAPPING.md`.
- No archaeology-specific terms in `app/`, `tests/`, logs, filenames, API responses, or frontend.
- Do not create HTTP routes.
- Do not create frontend controls.
- Do not connect the classifier to `BackgroundTasks`.
- Do not connect the classifier to the core orchestrator.
- Do not implement output writing yet; that is M15.
- Do not implement `inputs.py` yet unless required for type references; full input validation is M15.

## Validation

```bash
pytest tests/unit/test_experimental_gate.py
pytest tests/unit/test_forbidden_terms.py
```

## Stop condition

Stop after M14 and report files changed, commands run, test results, and blockers.

---

# Goal M15 — Experimental CLI runner, input validation, and Class IV outputs

## Scope

Create/update:

- `app/pipeline/stages_experimental/run.py`
- `app/pipeline/stages_experimental/inputs.py`
- `app/pipeline/stages_experimental/outputs.py`
- `app/pipeline/stages_experimental/classifier.py` if needed
- `tests/unit/test_experimental_inputs.py`
- `tests/unit/test_experimental_outputs.py`
- `tests/integration/test_experimental_cli.py`

## Requirements

- `run.py` is the only allowed CLI entrypoint:
  `python -m app.pipeline.stages_experimental.run --run-id <id>`
- `inputs.py` validates:
  - `ENABLE_EXPERIMENTAL=1` is set;
  - RUN exists;
  - RUN status is `done`;
  - required core artifacts exist;
  - required artifacts are GRID-consistent;
  - required artifacts have allowed artifact classes;
  - missing or inconsistent inputs fail safely before `classifier.py` runs.
- `outputs.py` writes only under `./data/runs/<run_id>/experimental/`.
- `outputs.py` records every classifier artifact as `artifact_class = FILESYSTEM_ONLY`.
- Classifier outputs are never listed, served, previewed, tiled, or downloadable through HTTP.
- No FastAPI route may import or invoke `stages_experimental`.
- No frontend code may invoke `stages_experimental`.
- No BackgroundTasks path may invoke `stages_experimental`.
- No core orchestrator path may invoke `stages_experimental`.
- No archaeology-specific terms in `app/`, `tests/`, logs, filenames, API responses, or frontend.
- Do not serve KMZ/KML/GeoJSON over HTTP.
- Do not expose classifier artifacts through `/runs/{id}` or `/artifacts/{name}`.

## Validation

```bash
pytest tests/unit/test_experimental_inputs.py
pytest tests/unit/test_experimental_outputs.py
pytest tests/integration/test_experimental_cli.py
pytest tests/unit/test_forbidden_terms.py
```

## Stop condition

Stop after M15 and report files changed, commands run, test results, and blockers.

---

# Goal M16 — Frontend SPA

## Scope

Create/update:

- `frontend/index.html`
- `frontend/app.js`
- `frontend/style.css`
- `frontend/vendor/` if needed
- `app/main.py` static mount if needed
- `tests/integration/test_frontend_static.py`

## Requirements

- Single-page app served locally.
- Blank basemap by default.
- External tiles disabled by default.
- No CDN-loaded scripts.
- No external fonts.
- No analytics.
- No telemetry.
- No raw lat/lon text displayed.
- Artifact downloads go through guarded API endpoint.
- Experimental outputs are not shown.
- Class IV artifacts are not listed.

## Validation

```bash
pytest tests/integration/test_frontend_static.py
```

## Stop condition

Stop after M16 and report files changed, commands run, test results, and blockers.

---

# Goal M17 — Full integration, documentation, and release checklist

## Scope

Create/update:

- `README.md`
- `docs/SAFETY_CONSTANTS.md`
- `docs/PIPELINE.md`
- `docs/EXPERIMENTAL_MODULE.md`
- `docs/THREAT_MODEL.md` if not already covered
- `tests/integration/test_full_run.py`
- `tests/integration/test_no_coordinate_leakage.py`
- `tests/integration/test_no_experimental_http_surface.py`

## Requirements

- Clean checkout setup works without Docker.
- README explains local-only scope.
- README explains service-account setup without committing key.
- README explains v1 classifier CLI-only behavior.
- Full integration tests pass.
- No `ee.Authenticate()`.
- No forbidden terms outside allowed docs.
- No coordinate/hash/path leakage.
- All artifact routes pass through guard.
- App starts on `127.0.0.1`.
- `/healthz` works.
- `/readyz` reflects EE readiness.

## Validation

```bash
pytest tests/unit/
pytest tests/integration/
pytest tests/notebook_parity/
```

## Stop condition

Stop after M17 and report release readiness.

---

# Fix-only prompt for failed tests

Use this when a goal fails tests:

```text
Read AGENTS.md and plan.md. Fix only the failing tests from the current goal. Do not expand scope and do not start the next goal.

Test output:
<paste output here>
```

---

# Standard Codex Goal prompts

## Start M0

```text
Read AGENTS.md and plan.md. Implement Goal M0 only. Stop after M0 and report files changed, commands run, and test results.
```

## Continue to any later goal

Replace `M1` with the goal number you want:

```text
Read AGENTS.md and plan.md. Implement Goal M1 only. Stop after M1 and report files changed, commands run, and test results.
```
