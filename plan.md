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
- Declare explicit numeric tolerance values per stage and artifact class used in parity comparison.
- Verify and record the exact notebook `IRON_SWIR` buggy formula and its notebook cell or source reference.
- Record whether object clustering in the notebook is deterministic or seeded.
- Document how to store artifacts under `tests/notebook_parity/fixtures/reference_run_v1/`.
- Document how to compare app outputs against frozen notebook outputs.
- Do not add large binary fixtures unless already available.

Validation:

```bash
pytest tests/unit/ tests/integration/ tests/notebook_parity/
```

---

# Goal H4.5 — IRON_SWIR provenance reconciliation

Create/update:

- `docs/IRON_SWIR_PROVENANCE.md`
- `docs/OUTPUT_PARITY_CONTRACT.md` if needed
- `docs/PARITY_EXCEPTIONS.md` if needed
- `plan.md`

Requirements:

- Resolve the conflict found during H4:
  - the checked-in notebook appears to use `(B12 - B11) / (B12 + B11)`
  - while the app uses `(B11 - B12) / (B11 + B12)`
- State clearly that these are sign-flipped formulas.
- Decide and document one accepted production interpretation before H5:
  - A. app formula is canonical and notebook output is treated as `PARITY_CORRECTS`
  - B. checked-in notebook formula is canonical and app must be changed later
  - C. an older notebook revision is canonical and must be identified by commit SHA/hash
  - D. H5 compares magnitude only, with sign convention documented
- Do not silently choose one without documenting rationale.
- If no final decision can be made automatically, write `docs/IRON_SWIR_PROVENANCE.md` with the conflict, options, and a required human decision before H5.
- Update H5 requirements so H5 must read `docs/IRON_SWIR_PROVENANCE.md` and apply the accepted `IRON_SWIR` comparison rule.
- H5 must fail or skip with a clear reason if the `IRON_SWIR` provenance decision is unresolved.

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
- H5 must read `docs/IRON_SWIR_PROVENANCE.md` and apply the accepted `IRON_SWIR` comparison rule.
- H5 must apply Option A.
- H5 must compare `IRON_SWIR` against the corrected analytical/app reference using `(B11 - B12) / (B11 + B12)`.
- H5 must not silently compare against the checked-in notebook sign-flipped `IRON_SWIR` raster.
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

---

# Notebook full-job parity phase

The app must reproduce the notebook's full job work products where applicable, not only reduced core production artifacts.

Source inventory and artifact classification:

- `docs/NOTEBOOK_FULL_JOB_INVENTORY.md`
- `docs/Notebook_Cells_E.md`

Phase rules:

- `FILESYSTEM_ONLY` is the default artifact class for notebook full-job outputs.
- `LOCAL_SENSITIVE` may be used only for redacted local operator QA artifacts that contain no forbidden public content.
- `REDACTED_PUBLIC` is allowed only for already-redacted summaries.
- `PREVIEW_ONLY` is allowed only for safe previews.
- Outputs classified as out-of-scope in `docs/NOTEBOOK_FULL_JOB_INVENTORY.md` remain out-of-scope unless a later explicit goal approves a redacted derivative.
- Do not expose raw coordinates, geometry, WKT, bounds, CRS transforms, local or Drive paths, hashes/checksums, exact location outputs, or secrets.
- Do not modify `notebooks/new.ipynb` unless a goal explicitly says so.
- Do not start deployment `D0`-`D7` until the user explicitly accepts the N-phase stopping point.

Official sequence:

- `N0` -> `N1` -> `N2` -> `N3` -> `N4` -> `N5` -> `N6` -> `N7` -> `N8`

---

# Goal N0 — Accept full-job inventory baseline

Create/update:

- `docs/NOTEBOOK_FULL_JOB_INVENTORY.md` only if corrections are needed
- `plan.md` only if corrections are needed

Requirements:

- Confirm the inventory document exists.
- Confirm it records the full-job interpretation.
- Confirm it preserves the artifact-class rules above.
- Confirm it is documentation/inventory only and does not authorize implementation by itself.
- Do not change app logic.
- Do not change tests.
- Do not change the notebook.

Validation:

```bash
pytest tests/unit/ tests/integration/ tests/notebook_parity/
```

---

# Goal N1 — Full-job artifact contract and naming map

Create/update:

- `docs/NOTEBOOK_FULL_JOB_ARTIFACT_CONTRACT.md`
- `docs/NOTEBOOK_FULL_JOB_INVENTORY.md` if corrections are needed

Requirements:

- Convert the inventory into an implementation contract.
- Define the app run-directory layout for notebook-equivalent full-job outputs.
- Define filename mappings where exact notebook names are unsafe or unstable.
- Define which outputs are required app artifacts and which are internal QA artifacts.
- Define artifact class for every required output family.
- Keep `FILESYSTEM_ONLY` as the default.
- Allow `LOCAL_SENSITIVE` only for explicitly redacted operator QA files.
- Do not expose forbidden public content.
- Do not change app logic.
- Do not change tests except optional documentation-link checks.
- Do not change the notebook.

Validation:

```bash
pytest tests/unit/ tests/integration/ tests/notebook_parity/
```

---

# Goal N2 — SAR full-job artifacts

Create/update:

- `app/pipeline/stages/sar_rtc.py`
- tests for SAR full-job artifacts
- docs from N1 if mappings require clarification

Requirements:

- Add approved SAR full-job work products from the N1 contract.
- Add safe non-public diagnostics where approved.
- Add summary CSV/JSON outputs where approved.
- Add per-band and stack outputs only as specified by the N1 contract.
- Preserve existing core SAR outputs and parity behavior.
- Preserve existing SAR pairing and RTC formulas unless already documented as `PARITY_CORRECTS`.
- Do not expose SAR full-job outputs publicly.
- Do not modify unrelated stages.

Validation:

```bash
pytest tests/unit/test_sar_rtc.py
pytest tests/unit/ tests/integration/ tests/notebook_parity/
```

---

# Goal N3 — GRID, DEM, zero-shift, and alignment QA full-job artifacts

Create/update:

- relevant GRID/DEM/zero-shift/alignment modules
- tests for approved full-job GRID/DEM/alignment artifacts
- docs from N1 if mappings require clarification

Requirements:

- Add approved RUN/GRID/DEM guard outputs from the N1 contract.
- Add approved zero-shift and drift/audit outputs.
- Add redacted alignment QA summaries where safe.
- Preserve existing public redaction and artifact-serving policy.
- Preserve existing GRID and DEM core parity behavior.
- Do not modify unrelated stages.

Validation:

```bash
pytest tests/unit/test_grid.py tests/unit/test_dem.py tests/unit/test_zero_shift.py tests/unit/test_alignment_qa.py
pytest tests/unit/ tests/integration/ tests/notebook_parity/
```

---

# Goal N4 — Defensible feature-stack and science extras

Create/update:

- relevant pipeline stages for approved feature-stack outputs
- tests for approved feature-stack outputs
- docs from N1 if mappings require clarification

Requirements:

- Implement only approved science-core feature-stack outputs from the N1 contract.
- Use `docs/NOTEBOOK_FULL_JOB_INVENTORY.md` to distinguish approved science outputs from duplicate or out-of-scope sections.
- Keep out-of-scope sections out of scope unless separately approved.
- Preserve existing core pipeline parity.

Validation:

```bash
pytest tests/unit/ tests/integration/ tests/notebook_parity/
```

---

# Goal N5 — Hypercube, PCA, object, and tensor support outputs

Create/update:

- relevant hypercube/PCA/object modules
- tests for approved full-job support outputs
- docs from N1 if mappings require clarification

Requirements:

- Add approved support outputs from the N1 contract for hypercube, PCA, object extraction, and tensor/export support.
- Keep object tables public only in redacted form.
- Keep location-context side products non-public and governed by the N1 contract.
- Preserve deterministic object ordering and clustering behavior.
- Preserve existing public leakage tests.

Validation:

```bash
pytest tests/unit/test_hypercube.py tests/unit/test_pca_anomaly.py tests/unit/test_object_extract.py
pytest tests/unit/ tests/integration/ tests/notebook_parity/
```

---

# Goal N6 — DEM derivatives, S2, and thermal full-job extras

Create/update:

- relevant DEM-derivative/S2/thermal modules
- tests for approved DEM/S2/thermal full-job extras
- docs from N1 if mappings require clarification

Requirements:

- Add approved DEM derivative, selected S2, and thermal extras from the N1 contract.
- Keep non-target science layers non-public unless explicitly redacted.
- Preserve `IRON_SWIR` Option A decision and existing `PARITY_CORRECTS` handling.
- Preserve existing public leakage tests.

Validation:

```bash
pytest tests/unit/test_dem_derivatives.py tests/unit/test_s2_indices.py tests/unit/test_thermal.py
pytest tests/unit/ tests/integration/ tests/notebook_parity/
```

---

# Goal N7 — Full-job artifact inventory tests

Create/update:

- tests for full-job artifact inventory and classification
- docs from N1 if mappings require clarification

Requirements:

- Add tests that verify required full-job artifact families from the N1 contract are emitted by the app stages that own them.
- Add tests that verify artifact classes follow the N1 contract.
- Add tests that verify full-job outputs are not publicly listed unless explicitly redacted.
- Add tests that verify `FILESYSTEM_ONLY` full-job outputs are never served over HTTP.
- Preserve existing H5 reference-output tests and public leakage tests.

Validation:

```bash
pytest tests/unit/ tests/integration/ tests/notebook_parity/
```

---

# Goal N8 — Full-job runbook update

Create/update:

- `docs/RUNBOOK.md`
- `docs/NOTEBOOK_FULL_JOB_ARTIFACT_CONTRACT.md` if needed

Requirements:

- Document how an operator retrieves/copies the full notebook-equivalent output set from the local run directory.
- Document which outputs are public, local-sensitive, and filesystem-only.
- Document that notebook Drive-first behavior maps to local app run directories unless explicit Drive integration is later approved.
- Document that full-job outputs are local artifacts, not public API products.

Validation:

```bash
pytest tests/unit/ tests/integration/ tests/notebook_parity/
```

At the end of the new section, use this command template:

`/goal Read AGENTS.md and plan.md. Execute Goal N0 only. Stop after N0 and report files changed, commands run, test results, and blockers.`

---

# Full notebook local-output expansion phase

The N-phase made the app comparable to the approved science-core notebook workflow. The F-phase expands the app toward the user-approved full notebook local-output workflow.

This phase is local-output first. It may generate exact-location artifacts, classifier outputs, KMZ, GeoJSON, focus-mask products, GPS comparison reports, and local path/reference reports only as local run artifacts unless a later explicit goal changes access policy.

Source inventory:

- docs/NOTEBOOK_FULL_JOB_INVENTORY.md
- docs/Notebook_Cells_E.md
- docs/NOTEBOOK_FULL_JOB_ARTIFACT_CONTRACT.md

User-approved scope:

- Add safe map/manual pin UI.
- Keep local outputs under the user's PC run directory: data/runs/<run_id>/.
- Add duplicate notebook stack variants where useful:
  - NANO stack family
  - SIGMA0 master variants
  - GPHYS master
  - RAD master cube
  - ULTIMATE GPHYS scan
  - Tesla v7.2 stack variants
- Add domain/treasure-specific feature stacks only as local-only experimental outputs with neutral external names.
- Add 17m focus-mask and exact target-zone analysis.
- Add exact lat/lon GeoJSON and KMZ outputs as FILESYSTEM_ONLY.
- Add hard classifiers and target labels as local-only experimental outputs with neutral names.
- Keep training scaffolding and CNN/Swin/YOLO/SegFormer inference on hold.
- Add field-operations KMZ outputs as FILESYSTEM_ONLY.
- Add Drive/reference-file locator utilities, but do not scan secret folders and do not expose local/Drive paths publicly.
- Add GPS point comparison reports as FILESYSTEM_ONLY.
- Keep broken or experimental model-build cells excluded unless rebuilt cleanly in a separate approved ML phase.

F-phase access rules:

- FILESYSTEM_ONLY is allowed for exact-location artifacts.
- Exact lat/lon, GeoJSON, KMZ, WKT, target-zone outputs, classifier target outputs, GPS comparison reports, and path inventories must not be public-listed.
- These outputs must not be served over HTTP unless a later explicit local-only download goal changes artifact policy with tests.
- No new public coordinate, geometry, path, target, or classifier leakage is allowed.
- Core app public responses remain redacted.
- Do not modify notebooks/new.ipynb unless a goal explicitly says so.
- Training/deep-learning inference remains on hold.

Official sequence:

- F0 -> F1 -> F2 -> F3 -> F4 -> F5 -> F6 -> F7 -> F8 -> F9

---

# Goal F0 — Record full notebook local-output expansion contract

Create/update:

- plan.md
- docs/NOTEBOOK_FULL_JOB_ARTIFACT_CONTRACT.md
- docs/NOTEBOOK_FULL_JOB_INVENTORY.md if corrections are needed

Requirements:

- Record the user-approved F-phase scope.
- Convert the approved excluded/missing notebook sections into an implementation contract.
- Define which outputs remain FILESYSTEM_ONLY.
- Define which outputs may be experimental local outputs.
- Define which outputs remain on hold:
  - training scaffolding
  - CNN/Swin/YOLO/SegFormer inference
  - broken model-build cells
- Do not change app logic.
- Do not change tests except optional documentation-link checks.
- Do not change the notebook.

Validation:

- pytest tests/unit/ tests/integration/ tests/notebook_parity/

---

# Goal F1 — Safe map/manual pin UI

Create/update:

- frontend map/pin UI files as needed
- API/frontend tests as needed
- docs if needed

Requirements:

- Add a safe operator workflow for selecting a point manually.
- The selected point may be submitted to /runs.
- Do not display exact coordinates in public run responses.
- Do not emit public WKT, GeoJSON, or ROI geometry.
- Any ROI/WKT debug output must be local-only or FILESYSTEM_ONLY.
- Preserve existing API redaction behavior.
- Do not change notebook code.

Validation:

- pytest tests/unit/ tests/integration/ tests/notebook_parity/

---

# Goal F2 — Notebook stack-variant local outputs

Create/update:

- relevant stack/output stages
- tests for approved stack families
- docs/contract updates if mappings require clarification

Requirements:

- Add approved duplicate/variant stack families only as local outputs.
- Use neutral names for app outputs.
- Implement only useful, reproducible formulas from the notebook inventory.
- Avoid blind duplication of broken or near-identical notebook cells.
- Stack outputs default to FILESYSTEM_ONLY.
- No target/classifier public exposure.
- Preserve existing science-core outputs and parity behavior.

Validation:

- pytest tests/unit/ tests/integration/ tests/notebook_parity/

---

# Goal F3 — 17m focus-mask and exact target-zone local outputs

Create/update:

- local focus-mask stage or module
- tests for focus-mask artifacts
- docs/contract updates if needed

Requirements:

- Add 17m focus-mask and exact target-zone analysis approved by the user.
- Outputs must be FILESYSTEM_ONLY.
- Exact coordinates, geometry, WKT, GeoJSON, bounds, CRS transforms, and target-zone context must not appear in public API responses.
- Do not public-list focus-mask artifacts.
- Do not serve focus-mask artifacts over HTTP unless a later explicit local-only download goal changes policy with tests.

Validation:

- pytest tests/unit/ tests/integration/ tests/notebook_parity/

---

# Goal F4 — Exact-location GeoJSON and KMZ local outputs

Create/update:

- local GeoJSON/KMZ export module
- tests for artifact classes and access blocking
- docs/contract updates if needed

Requirements:

- Add exact lat/lon GeoJSON and KMZ outputs approved by the user.
- Outputs must be FILESYSTEM_ONLY.
- Outputs must be written under the local run directory.
- They must not be public-listed.
- They must not be served through normal artifact routes.
- Add tests proving these artifacts are inaccessible over HTTP by default.
- Do not change public redaction rules.

Validation:

- pytest tests/unit/ tests/integration/ tests/notebook_parity/

---

# Goal F5 — Hard classifiers and neutral target-label local outputs

Create/update:

- experimental/local classifier module as needed
- tests for neutral names and filesystem-only outputs
- docs/contract updates if needed

Requirements:

- Add hard classifier/target-label logic only as local experimental outputs.
- Use neutral external names such as Class_A, Class_B, etc.
- Keep original/domain label mapping only in approved documentation if needed.
- Classifier outputs must be FILESYSTEM_ONLY.
- No classifier outputs are public-listed.
- No classifier outputs are served over HTTP by default.
- Do not connect this to the public frontend by default.
- Do not implement training or deep-learning inference in this goal.

Validation:

- pytest tests/unit/ tests/integration/ tests/notebook_parity/

---

# Goal F6 — Field-operations KMZ and local report outputs

Create/update:

- local report/KMZ exporter module
- tests for artifact classes and access blocking
- docs/contract updates if needed

Requirements:

- Add field-operations KMZ outputs approved by the user.
- Add local-only report outputs needed to reproduce notebook field-operation deliverables.
- Outputs must be FILESYSTEM_ONLY.
- Do not public-list or serve these files by default.
- Keep exact-location and target context out of public API responses.

Validation:

- pytest tests/unit/ tests/integration/ tests/notebook_parity/

---

# Goal F7 — Drive/reference locator utilities

Create/update:

- local utility scripts or modules
- tests for path redaction and no secret-folder scanning
- docs/contract updates if needed

Requirements:

- Add Drive/reference-file locator utilities approved by the user.
- Utilities may support local path discovery and reference-file matching.
- Do not scan secret folders.
- Do not print or expose local/Drive paths through public API responses.
- Any path inventory report must be FILESYSTEM_ONLY.
- Prefer local filesystem utilities over Drive integration unless Drive is explicitly required.

Validation:

- pytest tests/unit/ tests/integration/ tests/notebook_parity/

---

# Goal F8 — GPS point comparison reports

Create/update:

- local GPS comparison module or script
- tests for report generation and access blocking
- docs/contract updates if needed

Requirements:

- Add GPS point comparison reports approved by the user.
- Reports must be FILESYSTEM_ONLY.
- Exact GPS/reference/target coordinates must not be public-listed or served by default.
- Reports must stay under the local run directory or an approved local comparison output directory.
- Do not add public API exposure.

Validation:

- pytest tests/unit/ tests/integration/ tests/notebook_parity/

---

# Goal F9 — Full notebook local-output comparison report

Create/update:

- comparison script or test utilities
- docs/runbook updates
- tests if needed

Requirements:

- Compare notebook local-output inventory against app local-output inventory.
- Produce a report showing:
  - covered outputs
  - missing approved outputs
  - intentionally excluded outputs
  - on-hold outputs
  - artifact class for each output family
- The report must be local-only unless explicitly redacted.
- Keep training/deep-learning inference and broken model-build cells excluded/on hold.
- Do not expose exact coordinates, KMZ, GeoJSON, GPS reports, classifier outputs, or local paths publicly.

Validation:

- pytest tests/unit/ tests/integration/ tests/notebook_parity/

At the end of the F-phase section, use this command template:

/goal Read AGENTS.md and plan.md. Execute Goal F0 only. Stop after F0 and report files changed, commands run, test results, and blockers.

---

# Goal F10 - Add notebook-style SAR NPY band exports

Reason:

The live notebook-vs-app family comparison showed one remaining notebook-only output family:

- SAR NPY bands

Notebook output family:

- NPY_RADAR_BANDS/RADAR_VV_dB_*.npy
- NPY_RADAR_BANDS/RADAR_VH_dB_*.npy
- NPY_RADAR_BANDS/RADAR_logRatio_dB_*.npy
- NPY_RADAR_BANDS/RADAR_angle_*.npy

Current app output family:

- VV_dB.tif
- VH_dB.tif
- logRatio_dB.tif
- incidence.tif

Requirements:

- Add notebook-style SAR per-band NPY exports to the app.
- Write outputs under the local run directory.
- Use stable app filenames:
  - npy_radar_bands/VV_dB.npy
  - npy_radar_bands/VH_dB.npy
  - npy_radar_bands/logRatio_dB.npy
  - npy_radar_bands/incidence.npy
- Register every SAR NPY export as FILESYSTEM_ONLY.
- Set http_servable=False for every SAR NPY export.
- Do not public-list SAR NPY exports.
- Do not serve SAR NPY exports through normal artifact routes.
- Preserve existing SAR GeoTIFF outputs.
- Preserve existing SAR RTC parity tests.
- Add or update tests proving:
  - the NPY files are written
  - artifact classes are FILESYSTEM_ONLY
  - HTTP serving is disabled
  - the full-job inventory/access tests include the new files
- Do not change notebook code.
- Do not add Drive behavior.
- Do not expose coordinates, geometry, paths, hashes, or exact ROI context in public API responses.

Validation:

- pytest tests/unit/ tests/integration/ tests/notebook_parity/

Stop after F10 and report files changed, commands run, test results, and blockers.

---

# Goal F11 - Numeric and deterministic-content parity report

Reason:

The F10 live notebook-vs-app comparison proved output-family parity for the downloaded notebook run, with no remaining NOTEBOOK_ONLY output families.

F11 must prove whether the actual numeric/content results match, not only whether files exist.

Scope:

- Compare matched notebook and app science outputs using numeric parity.
- Compare deterministic report/content outputs using canonicalized content parity.
- Do not require full folder byte-for-byte identity.
- Do not compare on-hold training, CNN, Swin, YOLO, SegFormer, or broken model-build cells.
- Do not change notebook code.
- Do not expose coordinates, paths, geometry, hashes, or exact ROI context through public API responses.

Required comparison families:

- RUN/grid manifest
- DEM core
- DEM derivatives
- SAR GeoTIFF bands
- SAR NPY bands
- Radar/tensor stack
- Tesla/hypercube family where file mapping is available
- Focus mask 17m
- Exact-location GeoJSON/KMZ by canonical geometry/content comparison, not raw zip bytes
- Final intelligence reports where deterministic mapping is available
- Alignment/QA summaries after removing timestamps, local paths, run IDs, and other unstable fields

Output:

- Add a local-only parity report writer, for example:
  - scripts/compare_notebook_app_outputs.py
- The script must accept:
  - --notebook-root
  - --app-run-dir
  - --output-dir
- The report must be written under a local output directory, for example:
  - data/reports/numeric_parity_<run_id>.json
  - data/reports/numeric_parity_<run_id>.csv
- Reports are FILESYSTEM_ONLY local operator outputs.

Numeric comparison requirements:

- For rasters:
  - compare CRS
  - compare width and height
  - compare transform
  - compare band count
  - compare nodata policy where available
  - compare dtype or record accepted dtype conversion
  - compare values using exact equality where possible
  - otherwise compare max absolute difference, mean absolute difference, count of differing pixels, and percent matching
- For NPY:
  - compare shape
  - compare dtype
  - compare finite/nodata masks where applicable
  - compare values using exact equality where possible
  - otherwise compare max absolute difference, mean absolute difference, count of differing cells, and percent matching
- For CSV:
  - canonicalize row order where a stable key exists
  - canonicalize float formatting
  - compare deterministic columns
  - ignore unstable timestamps, absolute paths, run IDs, hashes, and local/Drive path fields
- For JSON/GeoJSON:
  - canonicalize key order
  - canonicalize numeric precision
  - ignore unstable timestamps, absolute paths, run IDs, hashes, and local/Drive path fields
  - compare feature counts and geometry/content where safe
- For KMZ:
  - do not compare raw zip bytes
  - inspect contained KML where possible
  - compare canonical feature count, stable names, and coordinate precision only for local FILESYSTEM_ONLY reports

Tolerance policy:

- Default exact comparison for integer/mask arrays.
- Default tolerance for float arrays:
  - absolute tolerance 1e-5
  - relative tolerance 1e-5
- Allow per-family tolerance overrides only if documented in the report.
- Any tolerance override must be visible in the output report.

Report fields:

- family
- notebook_file
- app_file
- comparison_type
- status
- shape_match
- crs_match
- transform_match
- dtype_match
- exact_equal
- max_abs_diff
- mean_abs_diff
- differing_count
- matching_percent
- tolerance_used
- skipped_reason
- notes

Status values:

- PASS
- FAIL
- SKIP_UNMAPPED
- SKIP_MISSING_NOTEBOOK
- SKIP_MISSING_APP
- SKIP_UNSUPPORTED_CONTAINER

Tests:

- Add unit tests for numeric array comparison.
- Add unit tests for raster metadata comparison using small synthetic rasters.
- Add unit tests for CSV/JSON canonicalization.
- Add integration or script tests proving the report is local-only and does not embed local absolute paths or exact coordinates in any public surface.
- Existing tests must continue to pass.

Validation:

- pytest tests/unit/ tests/integration/ tests/notebook_parity/

Stop after F11 and report files changed, commands run, test results, and blockers.

---

# Goal F12 - Diagnose and reconcile numeric parity failures

Reason:

F11 created the numeric/content parity report tool and the first live report was generated against the downloaded notebook output and app run.

The report showed:

- 13 FAIL rows
- 31 SKIP_MISSING_NOTEBOOK rows
- 0 PASS rows

F12 must diagnose the cause of these failures before changing science algorithms.

Do not force parity by weakening tolerances.
Do not mark failures as pass without evidence.
Do not change the notebook.

Primary observed failure types:

- raster CRS/transform metadata missing or mismatched
- nodata policy mismatch
- SAR VV/VH/logRatio/incidence numeric mismatch
- DEM derivative numeric mismatch
- radar tensor stack numeric mismatch
- focus mask near-match with only a few pixel differences
- missing notebook mappings or notebook outputs stored outside the selected notebook root

Scope:

- Diagnose each F11 FAIL and SKIP row.
- Produce a local-only diagnosis report explaining the likely cause of each mismatch.
- Reconcile only safe/obvious issues, such as:
  - notebook root discovery
  - multi-root notebook search
  - filename mapping gaps
  - metadata extraction/reporting clarity
  - nodata normalization comparison logic
  - comparison report wording
- Do not change core science formulas until the diagnosis proves the exact cause.
- Do not hide or downgrade true numeric mismatches.
- Do not change notebook code.
- Do not expose coordinates, geometry, local paths, hashes, CRS transforms, or exact ROI context through public API responses.

Required inputs:

- F11 numeric parity JSON/CSV report
- notebook output root
- optional second notebook output root, such as the downloaded Radar_GRD_RTC folder
- app run directory

Create/update:

- app/services/numeric_parity_diagnostics.py or equivalent
- scripts/diagnose_numeric_parity_failures.py
- tests/unit/test_numeric_parity_diagnostics.py
- tests/integration/test_numeric_parity_diagnostics_script.py
- docs/NUMERIC_PARITY_DIAGNOSIS.md if useful
- app/services/numeric_parity_report.py only if needed for safe mapping/reporting fixes
- scripts/compare_notebook_app_outputs.py only if needed for multi-root input support

Requirements:

- Add a local-only diagnostic report writer.
- The script must accept:
  - --parity-report
  - --app-run-dir
  - --output-dir
  - --notebook-root
  - optional repeated --notebook-root for multi-root notebook search
- The diagnostic report must be written under a local output directory, for example:
  - data/reports/numeric_parity_diagnosis_<run_id>.json
  - data/reports/numeric_parity_diagnosis_<run_id>.csv
- Reports are FILESYSTEM_ONLY local operator outputs.
- Reports must not embed absolute local paths.
- Reports must use root labels or relative paths only.

Diagnostic categories:

- PASS_CONFIRMED
- FAIL_NUMERIC_MISMATCH
- FAIL_METADATA_MISMATCH
- FAIL_NODATA_POLICY_MISMATCH
- FAIL_DTYPE_MISMATCH
- FAIL_SHAPE_MISMATCH
- FAIL_BAND_ORDER_OR_STACK_ORDER
- FAIL_SOURCE_SELECTION_MISMATCH
- FAIL_ALGORITHM_MISMATCH
- SKIP_NOTEBOOK_FILE_NOT_FOUND
- SKIP_APP_FILE_NOT_FOUND
- SKIP_UNMAPPED_OUTPUT
- SKIP_UNSUPPORTED_CONTAINER
- NEEDS_MULTI_ROOT_SEARCH
- NEEDS_MANUAL_REVIEW

For each failed row, report:

- family
- notebook_file
- app_file
- original_status
- diagnosis_category
- evidence
- max_abs_diff
- mean_abs_diff
- differing_count
- matching_percent
- metadata_flags
- recommended_next_action
- safe_to_auto_reconcile true/false

Specific diagnosis rules:

- If shape matches but CRS/transform missing from notebook raster, diagnose metadata issue separately from numeric issue.
- If shape and dtype match but matching percent is near zero for SAR bands, diagnose likely SAR source-selection, orbit/pairing, RTC, filtering, or algorithm mismatch.
- If logRatio mismatch mirrors VV/VH mismatch, diagnose it as downstream SAR mismatch, not independent bug unless evidence says otherwise.
- If focus mask differs by fewer than 10 pixels, diagnose as near-match edge/boundary tolerance issue, not major algorithm mismatch.
- If notebook output is missing from the selected root but the known second downloaded notebook folder may contain it, diagnose NEEDS_MULTI_ROOT_SEARCH.
- If F11 cannot compare because a notebook filename is missing but the family was present in the family-level inventory, diagnose mapping/root issue.
- If numeric mismatch appears caused by nodata handling, diagnose nodata policy mismatch and recommend nodata normalization comparison before algorithm changes.
- If app-only outputs are not present in the downloaded notebook run, keep them as app-only and do not call them app failures.

Allowed reconciliation in F12:

- Add multi-root notebook search support to the F11 report script if needed.
- Improve filename mappings where evidence is clear.
- Improve raster comparison notes so metadata mismatch and numeric mismatch are reported separately.
- Add nodata-normalized comparison metrics in addition to raw comparison metrics.
- Add band-order diagnostics for stacks/hypercubes.

Not allowed in F12:

- Do not rewrite SAR RTC science logic.
- Do not rewrite DEM derivative science logic.
- Do not rewrite tensor/hypercube science logic.
- Do not modify notebook code.
- Do not weaken tolerances just to make failures pass.
- Do not expose sensitive paths or coordinates in public API responses.
- Do not serve F11/F12 reports over HTTP.

Validation:

- pytest tests/unit/ tests/integration/ tests/notebook_parity/

Stop after F12 and report files changed, commands run, test results, and blockers.

---

# Goal F13 - Reconcile SAR source-selection and metadata parity

Reason:

F12 diagnosed the numeric parity failures. The main blocker is SAR mismatch:

- SAR GeoTIFF VV/VH/logRatio/incidence rows diagnose as FAIL_SOURCE_SELECTION_MISMATCH
- SAR NPY logRatio/incidence rows diagnose as FAIL_SOURCE_SELECTION_MISMATCH
- radar tensor stack mismatch is likely downstream from SAR mismatch or stack band order
- DEM and focus-mask issues are secondary and should not be mixed into this goal

F13 must isolate why the notebook and app SAR outputs differ numerically before changing science logic.

Do not force parity by weakening tolerances.
Do not rewrite SAR formulas until the source-selection diagnosis proves the exact cause.
Do not change notebook code.

Scope:

- Diagnose and reconcile SAR source-selection parity first.
- Compare notebook SAR selection metadata against app SAR selection metadata.
- Compare image/date/orbit/pair/filter/RTC inputs before changing calculations.
- Improve app SAR metadata capture if needed.
- Improve F11/F12 reports if needed to show SAR source identity clearly.
- Do not work on DEM derivatives, hypercube, object extraction, field ops, GPS, or CNN/training in this goal.

Required SAR families:

- VV_dB
- VH_dB
- logRatio_dB
- incidence / angle
- SAR NPY equivalents
- radar_linear_support_stack only as downstream diagnostic, not as primary fix

Create/update:

- app/pipeline/stages/sar_rtc.py if metadata capture or safe source-selection reconciliation is needed
- app/services/numeric_parity_report.py if SAR comparison metadata needs clearer reporting
- app/services/numeric_parity_diagnostics.py if SAR diagnosis needs clearer categories/evidence
- scripts/compare_notebook_app_outputs.py only if needed
- scripts/diagnose_numeric_parity_failures.py only if needed
- tests/unit/test_sar_rtc.py
- tests/unit/test_numeric_parity_report.py if needed
- tests/unit/test_numeric_parity_diagnostics.py if needed
- tests/notebook_parity/test_sar_parity.py if applicable
- docs/SAR_SOURCE_SELECTION_PARITY.md

Required diagnosis work:

- Capture or report, where available:
  - Sentinel-1 collection id
  - selected image ids or stable image labels
  - acquisition dates
  - orbit direction
  - relative orbit number if available
  - VV/VH pair count
  - pair time delta
  - date window
  - ROI/grid label only, not public coordinates
  - selected band list
  - whether angle/incidence came from notebook angle band or app incidence band
  - whether local DEM RTC path was used
  - whether speckle/refined-Lee filtering was used
  - whether dB-to-linear-to-dB processing was used
- Compare notebook QA selection files such as SUMMARY_RADAR*.csv or SAR selection JSON if available.
- Compare app SAR stage metadata and manifests.
- Explain whether mismatch is caused by:
  - different Sentinel-1 source image selection
  - different orbit/pair selection
  - different date window
  - different RTC/filtering path
  - different angle/incidence source
  - different nodata policy
  - different band naming only
  - comparison mapping issue

Allowed reconciliation:

- Make app SAR source-selection rules match the notebook if the notebook rule is clearly identified and safe.
- Add missing SAR selection metadata to local-only manifests/reports.
- Add deterministic source-selection tests with synthetic metadata.
- Add diagnostics showing source-selection mismatch clearly.
- Add nodata-normalized SAR comparison metrics.
- Add angle/incidence mapping notes if notebook uses angle and app uses incidence.
- Add local-only operator reports.

Not allowed in F13:

- Do not weaken numeric tolerance to hide SAR mismatch.
- Do not mark mismatched SAR outputs as PASS.
- Do not change notebook code.
- Do not expose coordinates, geometry, paths, hashes, CRS transforms, or exact ROI context through public API responses.
- Do not serve F11/F12/F13 reports over HTTP.
- Do not rewrite DEM derivative, hypercube, tensor, object extraction, field ops, GPS, or experimental classifier logic.
- Do not change SAR science formulas unless the diagnosis proves the app differs from the notebook and the change is narrowly scoped.

Output:

- Add or update a local-only SAR source-selection parity report, for example:
  - data/reports/sar_source_selection_parity_<run_id>.json
  - data/reports/sar_source_selection_parity_<run_id>.csv
- Reports are FILESYSTEM_ONLY local operator outputs.
- Reports must not embed absolute local paths or public coordinates.

Tests:

- Add tests proving SAR source-selection metadata is captured without public leakage.
- Add tests proving SAR diagnosis distinguishes source-selection mismatch from pure numeric mismatch.
- Add tests proving angle/incidence mapping is documented.
- Add tests proving reports are local-only and do not expose coordinates/paths/hashes.
- Existing tests must continue to pass.

Validation:

- pytest tests/unit/ tests/integration/ tests/notebook_parity/

Stop after F13 and report files changed, commands run, test results, and blockers.

