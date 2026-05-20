# plan.md — Codex `/goal` Plan for GEE Screening App v1

This file defines the implementation goals for Codex. Codex should use this file together with:

- `AGENTS.md`
- `docs/PRD_v0.5.md`
- `docs/DIRECTORY_TREE_v0.5.md`
- `notebooks/new.ipynb`

## How to activate Codex Goals

The Codex Goal feature is a slash command. Use `/goal`, not a normal chat prompt.

Official behavior to follow:

- `/goal <objective>` sets the active goal.
- `/goal` shows the current goal.
- `/goal pause` pauses it.
- `/goal resume` resumes it.
- `/goal clear` clears it.
- If `/goal` is not available, enable Goals with `/experimental`, or enable `goals = true` under `[features]` in Codex `config.toml`.
- Goal text must be short, so the goal should point Codex to this file instead of restating the whole plan.

## Exact command to start

Paste this into Codex:

```text
/goal Read AGENTS.md and plan.md. Execute Goal M0 only. Stop after M0 and report files changed, commands run, test results, and blockers.
```

Do not start M1 until the user explicitly asks.

## Fix-only command

If a goal fails tests, paste:

```text
/goal Read AGENTS.md and plan.md. Fix only the failing tests from the current goal. Do not expand scope and do not start the next goal.
```

Then paste the test output in the normal prompt after the goal is set.

---

## Global rules for every goal

Codex must always:

- read `AGENTS.md` first;
- read this `plan.md`;
- follow `docs/PRD_v0.5.md` as the source of truth;
- use `docs/DIRECTORY_TREE_v0.5.md` for expected structure;
- use `notebooks/new.ipynb` only as the source notebook reference;
- implement only the requested goal;
- add or update tests for the requested goal;
- run the listed validation commands when possible;
- stop after the requested goal;
- not expand scope.

Hard prohibitions for v1:

- no Docker requirement;
- no PostgreSQL/Supabase requirement;
- no Redis/Celery/RQ/arq/separate worker;
- no `ee.Authenticate()` anywhere;
- no public coordinates, geometry, hashes, paths, or classifier outputs;
- no API/frontend/default-pipeline access to `stages_experimental`.

---

# Goal M0 — Repository skeleton and safety foundation

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

Requirements:

- FastAPI app starts.
- `/healthz` returns 200.
- `/readyz` exists and returns safe not-ready until EE setup exists.
- `/docs`, `/redoc`, and `/openapi.json` are disabled.
- Default host is `127.0.0.1`.
- `ALLOW_NETWORK_BIND` defaults false.
- No Docker, PostgreSQL, Redis, queue worker, or `ee.Authenticate()`.
- Do not implement DB, stages, frontend, or experimental classifier yet.

Validation:

```bash
pytest tests/unit/
```

Stop after M0.

---

# Goal M1 — SQLite persistence and migrations

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

Requirements:

- SQLite database defaults to `./data/gee_screening.db`.
- Use SQLAlchemy and Alembic.
- Runs table has id, name, status, internal coordinate fields, timestamps.
- Artifacts table has id, run_id, name, relative_path, size, internal hash, artifact_class enum, http_servable, timestamps.
- `artifact_class` is non-null.
- Avoid SQLite-specific advanced features that block future PostgreSQL migration.

Validation:

```bash
pytest tests/unit/ tests/integration/
```

Stop after M1.

---

# Goal M2 — Redaction, public errors, and logging safety

Create/update:

- `app/services/redaction.py`
- `app/errors.py`
- `app/logging_config.py`
- `app/api/errors.py`
- `app/main.py`
- `tests/unit/test_redaction.py`
- `tests/unit/test_public_error_handler.py`
- `tests/unit/test_logging_redaction.py`

Requirements:

- Implement `redact()` and `verify_redacted()`.
- Public DTOs must not expose coordinates, geometry, bounds, CRS transforms, hashes, checksums, or filesystem paths.
- Pattern checks are context-aware to avoid false positives.
- FastAPI validation errors use a custom safe handler.
- Error responses do not echo request bodies or forbidden field names.
- Logging formatter redacts at INFO and above.
- Outgoing JSON verification failure returns generic HTTP 500.

Validation:

```bash
pytest tests/unit/
```

Stop after M2.

---

# Goal M3 — Artifact taxonomy and serving guard

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

Requirements:

- Implement `LOCAL_SENSITIVE`, `REDACTED_PUBLIC`, `PREVIEW_ONLY`, `FILESYSTEM_ONLY`.
- Implement `can_serve_artifact()` and `serve_artifact_response()`.
- All artifact serving routes through `serve_artifact_response()`.
- API routes may not directly use `FileResponse`, `StreamingResponse`, `open()`, or direct filesystem streaming.
- `FILESYSTEM_ONLY` is never served.
- `LOCAL_SENSITIVE` is served only on `127.0.0.1` and blocked under `ALLOW_NETWORK_BIND=1`.
- Classifier outputs are never served.
- Class II redacted artifacts may be generated on demand and cached only as `REDACTED_PUBLIC`.

Validation:

```bash
pytest tests/unit/
pytest tests/integration/
```

Stop after M3.

---

# Goal M4 — Earth Engine service-account session

Create/update:

- `app/services/ee_session.py`
- `scripts/check_no_ee_authenticate.py`
- `tests/unit/test_ee_session.py`
- `tests/unit/test_no_ee_authenticate.py`

Requirements:

- EE auth is service-account only.
- No `ee.Authenticate()` anywhere.
- Readiness fails safely if EE service account cannot initialize.
- Key path comes from `.env`/settings.
- Scanner fails if `ee.Authenticate()` appears in `app/` or `tests/`.

Validation:

```bash
pytest tests/unit/
```

Stop after M4.

---

# Goal M5 — GRID, storage, run manifest, and run state machine

Create/update:

- `app/services/grid.py`
- `app/services/storage.py`
- `app/pipeline/manifest.py`
- `app/services/run_state.py`
- `tests/unit/test_grid.py`
- `tests/unit/test_storage.py`
- `tests/unit/test_run_state_machine.py`

Requirements:

- Deterministic GRID from input lat/lon.
- Coordinates stored internally only.
- RUN directory under `./data/runs/<run_id>/`.
- GRID manifest persisted internally.
- Stage manifests are `LOCAL_SENSITIVE`.
- Stale running jobs marked failed/stale on startup.
- One active run at a time in v1.

Validation:

```bash
pytest tests/unit/
```

Stop after M5.

---

# Goal M6 — Stage protocol and orchestrator

Create/update:

- `app/pipeline/__init__.py`
- `app/pipeline/_base.py`
- `app/pipeline/stages/__init__.py`
- `app/pipeline/orchestrator.py`
- `tests/unit/test_stage_protocol.py`
- `tests/unit/test_orchestrator.py`
- `tests/unit/test_parity_metadata.py`

Requirements:

- Every Stage subclass declares `parity_category`.
- `PARITY_CORRECTS` and `PARITY_REPLACES` require `parity_reason`.
- Orchestrator refuses stages without parity metadata.
- Every artifact emission requires `artifact_class`.
- Writes without `artifact_class` raise `ArtifactClassError`.
- Orchestrator persists stage status.
- Orchestrator never imports/invokes `stages_experimental`.

Validation:

```bash
pytest tests/unit/
```

Stop after M6.

---

# Goal M7 — DEM ingest and zero-shift gate

Create/update:

- `app/pipeline/stages/grid.py`
- `app/pipeline/stages/dem.py`
- `app/pipeline/stages/zero_shift.py`
- `tests/unit/test_dem.py`
- `tests/unit/test_zero_shift.py`
- `tests/notebook_parity/test_dem_parity.py`

Requirements:

- Reproduce notebook DEM ingest and zero-shift logic.
- All outputs align to GRID.
- Drift raises `GridDriftError`.
- Artifacts are classified.
- Parity category is `PARITY_REPRODUCES`.

Validation:

```bash
pytest tests/unit/
pytest tests/notebook_parity/test_dem_parity.py
```

Stop after M7.

---

# Goal M8 — Sentinel-1 SAR RTC stage

Create/update:

- `app/pipeline/stages/sar_rtc.py`
- `tests/unit/test_sar_rtc.py`
- `tests/notebook_parity/test_sar_parity.py`

Requirements:

- Reproduce canonical notebook SAR RTC calculations.
- Produce `VV_dB.tif`, `VH_dB.tif`, `logRatio_dB.tif`, `incidence.tif`.
- Preserve GRID alignment.
- No `ee.Authenticate()`.
- Artifact classes assigned.
- Parity category is `PARITY_REPRODUCES`.

Validation:

```bash
pytest tests/unit/test_sar_rtc.py
pytest tests/notebook_parity/test_sar_parity.py
```

Stop after M8.

---

# Goal M9 — Sentinel-2 indices with corrected IRON_SWIR

Create/update:

- `app/pipeline/stages/s2_indices.py`
- `tests/unit/test_s2_indices.py`
- `tests/notebook_parity/test_s2_parity.py`
- `docs/PARITY_EXCEPTIONS.md` if needed

Requirements:

- Produce NDVI, NDWI, NDMI, NBR, IRONOX, IRON_SWIR, BSI.
- `IRON_SWIR` must use `(B11 - B12) / (B11 + B12)`.
- Do not use notebook bug formula.
- Stage parity category is `PARITY_CORRECTS` because of `IRON_SWIR`.
- Other S2 calculations reproduce notebook behavior where applicable.
- Outputs align to GRID.

Validation:

```bash
pytest tests/unit/test_s2_indices.py
pytest tests/notebook_parity/test_s2_parity.py
```

Stop after M9.

---

# Goal M10 — DEM derivatives and thermal LST

Create/update:

- `app/pipeline/stages/dem_derivatives.py`
- `app/pipeline/stages/thermal.py`
- `tests/unit/test_dem_derivatives.py`
- `tests/unit/test_thermal.py`
- `tests/notebook_parity/test_dem_derivatives_parity.py`
- `tests/notebook_parity/test_thermal_parity.py`

Requirements:

- Reproduce DEM derivative calculations and Landsat thermal LST stage.
- Outputs align to GRID.
- Artifacts are classified.
- Parity category is `PARITY_REPRODUCES` unless PRD says otherwise.

Validation:

```bash
pytest tests/unit/
pytest tests/notebook_parity/test_dem_derivatives_parity.py
pytest tests/notebook_parity/test_thermal_parity.py
```

Stop after M10.

---

# Goal M11 — Hypercube assembly and PCA anomaly

Create/update:

- `app/pipeline/stages/hypercube.py`
- `app/pipeline/stages/pca_anomaly.py`
- `tests/unit/test_hypercube.py`
- `tests/unit/test_pca_anomaly.py`
- `tests/notebook_parity/test_hypercube_parity.py`
- `tests/notebook_parity/test_pca_parity.py`

Requirements:

- Reproduce notebook hypercube assembly and PCA anomaly calculations.
- Persist eigenvalue report.
- Outputs align to GRID.
- Randomness, if any, is seeded and persisted.
- Artifacts are classified.
- Parity category is `PARITY_REPRODUCES`.

Validation:

```bash
pytest tests/unit/
pytest tests/notebook_parity/test_hypercube_parity.py
pytest tests/notebook_parity/test_pca_parity.py
```

Stop after M11.

---

# Goal M12 — Object extraction and alignment QA

Create/update:

- `app/pipeline/stages/object_extract.py`
- `app/pipeline/stages/alignment_qa.py`
- `tests/unit/test_object_extract.py`
- `tests/unit/test_alignment_qa.py`
- `tests/notebook_parity/test_objects_parity.py`
- `tests/notebook_parity/test_alignment_parity.py`

Requirements:

- Reproduce notebook object extraction, cluster summary behavior, per-object NPY patches, and alignment QA.
- Public object tables must not expose coordinates.
- Class II object CSV uses row/column pixel offsets only.
- Outputs align to GRID.
- Artifacts are classified.
- Parity category is `PARITY_REPRODUCES`.

Validation:

```bash
pytest tests/unit/
pytest tests/notebook_parity/test_objects_parity.py
pytest tests/notebook_parity/test_alignment_parity.py
```

Stop after M12.

---

# Goal M13 — Notebook parity suite and fixture protocol

Create/update:

- `tests/notebook_parity/README.md`
- `docs/PARITY_PROTOCOL.md`
- `docs/PARITY_EXCEPTIONS.md`
- `tests/notebook_parity/conftest.py`
- `tests/notebook_parity/fixtures/reference_run/README.md`
- `tests/unit/test_parity_category_consistency.py`

Requirements:

- Document reference notebook output capture.
- Document corrections, especially `IRON_SWIR`.
- Tests distinguish `PARITY_REPRODUCES`, `PARITY_CORRECTS`, and `PARITY_REPLACES`.
- Test collection fails if parity test category disagrees with Stage metadata.
- Do not commit huge binary fixtures unless PRD decision says to.

Validation:

```bash
pytest tests/unit/test_parity_category_consistency.py
pytest tests/notebook_parity/
```

Stop after M13.

---

# Goal M14 — Experimental classifier neutralization

Create/update:

- `app/pipeline/stages_experimental/__init__.py`
- `app/pipeline/stages_experimental/classes.py`
- `app/pipeline/stages_experimental/classifier.py`
- `app/pipeline/stages_experimental/README.md`
- `docs/CLASS_MAPPING.md`
- `tests/unit/test_experimental_gate.py`
- `tests/unit/test_forbidden_terms.py`

Requirements:

- `ENABLE_EXPERIMENTAL=1` is required to import the package.
- Classifier code uses only neutral IDs `Class_A` through `Class_N`.
- Original notebook label mapping lives only in `docs/CLASS_MAPPING.md`.
- No archaeology-specific terms in `app/`, `tests/`, logs, filenames, API responses, or frontend.
- No HTTP routes, frontend controls, BackgroundTasks connection, or core orchestrator connection.
- Do not implement output writing yet; that is M15.
- Do not implement full `inputs.py` yet unless required for type references.

Validation:

```bash
pytest tests/unit/test_experimental_gate.py
pytest tests/unit/test_forbidden_terms.py
```

Stop after M14.

---

# Goal M15 — Experimental CLI runner, input validation, and Class IV outputs

Create/update:

- `app/pipeline/stages_experimental/run.py`
- `app/pipeline/stages_experimental/inputs.py`
- `app/pipeline/stages_experimental/outputs.py`
- `app/pipeline/stages_experimental/classifier.py` if needed
- `tests/unit/test_experimental_inputs.py`
- `tests/unit/test_experimental_outputs.py`
- `tests/integration/test_experimental_cli.py`

Requirements:

- `run.py` is the only CLI entrypoint: `python -m app.pipeline.stages_experimental.run --run-id <id>`.
- `inputs.py` validates `ENABLE_EXPERIMENTAL=1`, RUN exists, RUN status is `done`, required artifacts exist, artifacts are GRID-consistent, and artifacts have allowed classes.
- Missing or inconsistent inputs fail safely before `classifier.py` runs.
- `outputs.py` writes only under `./data/runs/<run_id>/experimental/`.
- Every classifier artifact is `FILESYSTEM_ONLY`.
- Classifier outputs are never listed, served, previewed, tiled, or downloadable through HTTP.
- No FastAPI/frontend/BackgroundTasks/orchestrator path may invoke `stages_experimental`.
- No archaeology-specific terms in forbidden paths.

Validation:

```bash
pytest tests/unit/test_experimental_inputs.py
pytest tests/unit/test_experimental_outputs.py
pytest tests/integration/test_experimental_cli.py
pytest tests/unit/test_forbidden_terms.py
```

Stop after M15.

---

# Goal M16 — Frontend SPA

Create/update:

- `frontend/index.html`
- `frontend/app.js`
- `frontend/style.css`
- `frontend/vendor/` if needed
- `app/main.py` static mount if needed
- `tests/integration/test_frontend_static.py`

Requirements:

- Single-page app served locally.
- Blank basemap by default.
- External tiles disabled by default.
- No CDN scripts, external fonts, analytics, or telemetry.
- No raw lat/lon text displayed.
- Artifact downloads go through guarded API.
- Experimental outputs are not shown.
- Class IV artifacts are not listed.

Validation:

```bash
pytest tests/integration/test_frontend_static.py
```

Stop after M16.

---

# Goal M17 — Full integration, documentation, and release checklist

Create/update:

- `README.md`
- `docs/SAFETY_CONSTANTS.md`
- `docs/PIPELINE.md`
- `docs/EXPERIMENTAL_MODULE.md`
- `docs/THREAT_MODEL.md` if not already covered
- `tests/integration/test_full_run.py`
- `tests/integration/test_no_coordinate_leakage.py`
- `tests/integration/test_no_experimental_http_surface.py`

Requirements:

- Clean checkout works without Docker.
- README explains local-only scope, service-account setup, and classifier CLI-only behavior.
- Full integration tests pass.
- No `ee.Authenticate()`.
- No forbidden terms outside allowed docs.
- No coordinate/hash/path leakage.
- All artifact routes pass through guard.
- App starts on `127.0.0.1`.
- `/healthz` works.
- `/readyz` reflects EE readiness.

Validation:

```bash
pytest tests/unit/
pytest tests/integration/
pytest tests/notebook_parity/
```

Stop after M17 and report release readiness.

---

# Production-hardening phase

v1 is accepted. The next phase is production-by-parity:
Given the same ROI/input settings, the app must reproduce the notebook's operational/calculation outputs, except explicitly documented `PARITY_CORRECTS` cases.

Official sequence:

- `H0` -> `H1` -> `H2` -> `H3` -> `H4` -> `H5` -> `H6` -> `H7`
- `H3` already runs the `H2` scanner if present.
- Do not start deployment `D0`-`D7` until at least `H1`-`H3` are complete.

---

# Goal H0 — Freeze accepted v1 baseline

Requirements:

- Confirm working tree is clean.
- Tag `v1-accepted` if not already tagged.
- Confirm the current working tree and `HEAD` are compared against `v1-accepted`.
- Do not modify source files.
- The current full suite must pass.

Validation:

```bash
git status
git tag --list v1-accepted
git diff v1-accepted --stat
pytest tests/unit/ tests/integration/ tests/notebook_parity/
```

---

# Goal H1 — Production parity contract

Create/update:

- `docs/OUTPUT_PARITY_CONTRACT.md`

Requirements:

- Define the production output parity goal.
- Define required artifact parity for GRID, DEM, SAR RTC, DEM derivatives, thermal LST, Sentinel-2 indices, hypercube, PCA, object extraction, cluster summary, and alignment QA.
- Define comparison rules for rasters, NPY, CSV, JSON, manifests, and sidecars.
- Document allowed `PARITY_CORRECTS` exceptions, especially `IRON_SWIR` with corrected `B11+B12` denominator.
- State clearly that this is not real-world detection-accuracy validation.
- Add a rollback/recovery rule:
  - If a parity test fails, the offending stage must be rolled back to its accepted M-phase implementation pending PRD/parity-contract review.
  - No band-aid fixes that bypass the parity contract.
  - This applies to SAR RTC, S2, hypercube, PCA, objects, and all other parity stages.

Validation:

```bash
pytest tests/unit/ tests/integration/ tests/notebook_parity/
```

---

# Goal H2 — Notebook safety scanner

Create/update:

- `scripts/check_notebook_safety.py`
- `tests/unit/test_notebook_safety.py`

Requirements:

- Scan `notebooks/*.ipynb`.
- Fail on `ee.Authenticate(`.
- Fail on hardcoded absolute local paths.
- Fail on coordinate-like content in code cells or outputs unless explicitly allowlisted.
- Support an explicit allowlist mechanism for legitimate explanatory notebook cells:
  - source marker: `# parity: allow-coord`
  - or notebook cell metadata: `"parity_allow_coord": true`
- Require each allowlisted coordinate-like cell to include a reason string.
- Fail on coordinate-like content without the allowlist marker and reason.
- Fail on real service-account key paths.
- Fail on forbidden classifier source terms outside `docs/CLASS_MAPPING.md`.
- Allow documented `PARITY_CORRECTS` notes for `IRON_SWIR`.

Validation:

```bash
pytest tests/unit/test_notebook_safety.py
pytest tests/unit/ tests/integration/ tests/notebook_parity/
```

---

# Goal H3 — GitHub Actions CI

Create/update:

- `.github/workflows/ci.yml`

Requirements:

- Run on `push` and `pull_request` to `main`.
- Use Python `3.11` or `3.12`.
- Optional Python version matrix for `3.11` and `3.12` if runtime permits.
- Install project with dev dependencies.
- Run `pytest tests/unit/test_no_ee_authenticate.py tests/unit/test_forbidden_terms.py -v`.
- Run `pytest tests/unit/ tests/integration/ tests/notebook_parity/`.
- Run `scripts/check_no_ee_authenticate.py`.
- Run `scripts/check_no_direct_streaming.py`.
- Run `scripts/check_notebook_safety.py` if present.
- Do not require real Earth Engine credentials.
- Do not upload sensitive artifacts.

Validation:

```bash
pytest tests/unit/ tests/integration/ tests/notebook_parity/
```

---

# Goal H4 — Reference notebook fixture capture protocol

Create/update:

- `docs/REFERENCE_CAPTURE_PROTOCOL.md`
- `tests/notebook_parity/fixtures/reference_run_v1/README.md`

Requirements:

- Document how to run `notebooks/new.ipynb` on the canonical ROI.
- Document which notebook outputs must be exported.
- Document required metadata: notebook hash, environment, date, Earth Engine datasets, ROI label, grid manifest.
- Document how to store artifacts under `tests/notebook_parity/fixtures/reference_run_v1/`.
- Document how to compare app outputs against frozen notebook outputs.
- Do not add large binary fixtures unless already available.

Validation:

```bash
pytest tests/unit/ tests/integration/ tests/notebook_parity/
```

---

# Goal H5 — Reference-output comparison tests

Create/update:

- `tests/notebook_parity/test_reference_outputs_contract.py` or equivalent split tests

Requirements:

- Add tests that skip cleanly if large frozen reference artifacts are absent.
- Missing large frozen reference artifacts must be reported as pytest `SKIPPED`, not passed.
- The skip reason must state exactly which reference artifact directory or file is missing.
- CI logs must show skip counts clearly.
- When reference artifacts are present, compare app outputs against notebook outputs according to `docs/OUTPUT_PARITY_CONTRACT.md`.
- When reference artifacts are present, tests must fail on parity mismatch, not skip.
- Compare raster shape, transform, CRS, nodata, band order, dtype policy, and numeric tolerance.
- Compare CSV/JSON deterministically.
- Respect documented `PARITY_CORRECTS` exceptions.

Validation:

```bash
pytest tests/notebook_parity/
```

---

# Goal H6 — Production runbook

Create/update:

- `docs/RUNBOOK.md`

Requirements:

- Explain install, `.env` setup, migration, app startup, submitting a run, checking status, artifact retrieval, parity tests, EE key rotation, backups, stale run recovery, and local temp pytest workaround.
- Document the canonical local startup command:
  - `uvicorn app.main:app --host 127.0.0.1 --port 8000`
- Document how to verify startup and readiness:
  - `curl http://127.0.0.1:8000/healthz`
  - `curl http://127.0.0.1:8000/readyz`
- Document how to stop the app cleanly.
- Document the Windows pytest cache/temp workaround used during v1 verification:
  - set `TEMP` and `TMP` to a writable directory
  - run pytest with `--basetemp` pointing to a writable temp path
  - optionally use `-p no:cacheprovider` or `--cache-clear` if the local pytest cache is unwritable
- Do not require changing `pyproject.toml` unless a future test proves it is needed.
- Include Alembic/SQLite migration discipline note: use batch mode for future SQLite schema changes and test future migrations against SQLite and PostgreSQL target before v2.

Validation:

```bash
pytest tests/unit/ tests/integration/ tests/notebook_parity/
```

---

# Goal H7 — Live EE validation checklist

Create/update:

- `docs/LIVE_EE_VALIDATION.md`

Requirements:

- Checklist for service-account-only live Earth Engine validation.
- Include `/readyz` check.
- Include canonical ROI live run.
- Include comparison against notebook reference outputs.
- Include public API leakage checks.
- Include instruction not to commit `.env`, keys, or live artifacts.

Validation:

```bash
pytest tests/unit/ tests/integration/ tests/notebook_parity/
```

At the end of the new section, use this command template:

`/goal Read AGENTS.md and plan.md. Execute Goal H1 only. Stop after H1 and report files changed, commands run, test results, and blockers.`
