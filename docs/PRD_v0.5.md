# Product Requirements Document — GEE Screening Web App

**Status:** Draft v0.5
**Author:** Project owner, with Claude as orchestrator/validator
**Date:** 2026-05-16
**Repo visibility:** Private
**Deployment surface:** Local only (`127.0.0.1` bind, VPS deferred pending legal review)
**Storage backend:** SQLite (PostgreSQL/Supabase deferred to v2)

---

## Changelog from v0.4

| Change | Sections touched |
|---|---|
| **Experimental classifier moved into v1**. v1 now includes the notebook classifier logic as an isolated, opt-in, CLI-only experimental module. The previous empty-stub-only plan is removed. | §2, §6.2, §8, §9, §10, §11, §12, §14, §15, §17, Appendix A |
| **Neutral class vocabulary is mandatory at implementation time.** The classifier may reproduce notebook logic, thresholds, and calculation flow, but all source-notebook label families are mapped to `Class_A` … `Class_N` before entering `app/`, `tests/`, logs, filenames, or outputs. | §6.2, §9, §13, §16, docs contract |
| **Experimental CLI added to v1.** The only allowed invocation is `ENABLE_EXPERIMENTAL=1 python -m app.pipeline.stages_experimental.run --run-id <id>`. No API, frontend, background task, core orchestrator, or default pipeline path may invoke it. | §6.2, §9, §17 |
| **Experimental outputs are Class IV only.** Classifier outputs, including KMZ/KML/GeoJSON/class CSVs/heatmaps, write only under `<run_dir>/experimental/` and are never listed or served by HTTP. | §6.2, §14, §9 |
| **Classifier test style clarified.** The classifier has no scientific ground-truth or notebook-parity claim. v1 uses contract/golden-fixture tests to verify deterministic reproduction of notebook classifier logic after neutralization. | §6.2, §15, §9 |
| **Directory sketch reconciled for classifier-in-v1 scope.** The tree now includes `stages_experimental/run.py`, `classifier.py`, `classes.py`, `inputs.py`, `outputs.py`, and related tests/policy checks. | `DIRECTORY_TREE_v0.5.md` |

§§ 1, 3, 4, 5, 6.1, 6.3–6.6, 7, 13, 14, 16 otherwise retain the v0.4 safety posture unless explicitly changed below.

---

## 1. Overview

A FastAPI-based web application for satellite-imagery anomaly screening using Google Earth Engine (GEE), built as a production-grade reimplementation of an existing Colab research notebook. The app accepts a region of interest, runs a fixed processing pipeline against Sentinel-1 SAR, Sentinel-2 optical, Landsat thermal, and DEM data, and surfaces anomaly candidates and per-stage scientific outputs to a single operator via a single-page web frontend.

The application is built for personal, local, research-grade use. It is not deployed, not multi-user, not a service offered to anyone.

---

## 2. Purpose

The source Colab notebook contains substantial duplication of stage variants and mixes two distinct bodies of work:

1. A **defensible scientific pipeline** of approximately 30 cells covering grid lock, SAR RTC, DEM derivatives, S2 spectral indices, thermal LST, hypercube assembly, PCA anomaly detection, and object extraction — all standard, published remote-sensing techniques.
2. An **experimental classifier module** that applies rule-based and ML labels on top of the hypercube. These labels are not supported by validated ground truth and exist as research artifacts only.

The notebook is also fragile: cell-order dependency, manual Drive/Colab juggling, one known code bug (`IRON_SWIR` formula), no persistence, no service-account-only EE auth, no redaction of outputs. The purpose of this app is to:

- Re-host the defensible pipeline in a reproducible, tested, persistence-backed architecture.
- Establish the engineering surface (DB, redaction DTOs, service-account EE session, parity tests, artifact taxonomy) the operator's broader `GEE_screening` project discipline requires.
- Port the experimental classifier logic into v1 only as an isolated, opt-in, CLI-only research module, with all label families neutralized before they enter source code, tests, logs, filenames, or outputs.
- Keep the classifier outside the API/frontend/default pipeline so that reproducing notebook logic does not create a public-serving surface or imply scientific validation.

---

## 3. Non-Goals

Stated explicitly so they don't drift in over time:

- **Not a treasure-detection tool.** No claim is made that the classifier module identifies any specific archaeological, mineral, or cultural-property feature.
- **Not a deployed service.** No public hostname, no multi-user auth, no API keys, no rate limiting, no usage metrics, no telemetry.
- **Not for use against sanctioned terrain or heritage zones.** The default ROI is configurable but ships pointing at a research-safe demo region. Operator is responsible for ROI selection.
- **Not a substitute for ground-based archaeological survey, legal counsel, or remote-sensing peer review.**
- **Not a re-export tool for coordinate-bearing artifacts over the network.** Coordinate-bearing artifacts have a defined HTTP exposure policy (§14); KMZ and experimental-module outputs are never network-served.
- **Not an OGC-compliant GIS server.** No WMS, WFS, WCS endpoints. The tile renderer (§6.4) is local preview-only.

---

## 4. Users & Scope

- **Single user:** the project owner, on their own development machine.
- **Single deployment target:** `localhost`, FastAPI bound to `127.0.0.1`.
- **No auth model:** loopback-only binding is the auth model.
- **Source control:** private GitHub repository. Code is reviewed by Claude via paste/file-share at milestone boundaries, not commit-by-commit.
- **Re-evaluation triggers:** the operator commits to consulting a legal advisor before (a) changing deployment surface to anything other than `127.0.0.1`, or (b) sharing the repository publicly, or (c) materially changing the default ROI.

---

## 5. Safety Constants

These are the operator's immutable constants for the broader `GEE_screening` project. They apply unchanged to this app.

| # | Constant |
|---|---|
| C1 | Lawful desk-based remote-sensing triage scope only. |
| C2 | Public/default output must redact exact coordinates, geometry, fingerprints, and hashes. |
| C3 | All runtime gates default-off. |
| C4 | No automatic imagery ordering. |
| C5 | Service-account-only EE authentication. No `ee.Authenticate()` interactive flow. |
| C6 | No service account key committed to repo. |
| C7 | No public exposure of exact coordinates or geometry. |

These constants are reproduced verbatim in `docs/SAFETY_CONSTANTS.md` and referenced by `README.md`.

---

## 6. Functional Requirements

### 6.1 Core Pipeline (defensible, always loaded)

The app must implement, in order, the following stages. Each stage maps to specific cells in the source notebook (see Appendix A) and has a parity test against captured notebook output on the reference ROI, with a declared parity category per §15.

| Stage | Output artifacts |
|---|---|
| Grid construction | `GRID` manifest (EPSG, scale, size, crsTransform, bounds), persisted JSON |
| DEM ingest | `dem.tif`, `dem.npy` |
| Zero-shift gate | Pass/fail report; halts pipeline on any drift |
| Sentinel-1 RTC | `VV_dB.tif`, `VH_dB.tif`, `logRatio_dB.tif`, `incidence.tif` |
| DEM derivatives | `slope.tif`, `aspect.tif`, `curvature.tif`, `TPI.tif`, `TRI.tif`, `roughness.tif`, `TWI.tif` |
| Thermal LST | `lst.tif` |
| S2 spectral indices | `NDVI.tif`, `NDWI.tif`, `NDMI.tif`, `NBR.tif`, `IRONOX.tif`, `IRON_SWIR.tif`, `BSI.tif` |
| Hypercube assembly | `hypercube.tif`, `hypercube.npy` |
| PCA anomaly | `pca_anomaly.tif`, eigenvalue report |
| Object extraction | `objects_index.csv`, `clusters_summary.csv`, per-object NPY patches |
| Alignment QA | `alignment_qa.json`, pass/fail |

#### Functional notes:

- **F-1:** All stages must run against the same `GRID` manifest. Any stage producing output not byte-aligned to `GRID` (CRS, transform, size, nodata) must fail with a structured `GridDriftError`.
- **F-2:** The `IRON_SWIR` formula must be `(B11 − B12) / (B11 + B12)`. The notebook's `(B11 − B12) / (B11 − B12)` formula is a known bug. The parity test for this stage uses category `PARITY_CORRECTS` (see §15) and asserts the corrected output against an analytically-derived reference, not the notebook output.
- **F-3:** Each stage is independently re-runnable from an existing RUN's persisted state.
- **F-4:** Each stage produces, in addition to its primary artifacts, a `stage_<name>.manifest.json` describing inputs, outputs, parameters, timestamps, and a hash of each output. These manifests are **Class I (Local-sensitive)** artifacts (§14). Redacted copies (Class II) may be served via `/runs/{id}` detail responses.

### 6.2 Experimental Classifier Module — Included in v1, Opt-In, CLI-Only

v1 includes the notebook's experimental classifier logic, but only inside a quarantined package with neutral terminology and filesystem-only outputs. This module is a reproduction of notebook calculation logic for continued private research. It is not part of the defensible pipeline, is not invoked by the web app, and makes no ground-truth or real-world accuracy claim.

#### v1 deliverables for the experimental module:

- `app/pipeline/stages_experimental/__init__.py` — the gate. Raises `ImportError("Experimental module not enabled")` unless `ENABLE_EXPERIMENTAL=1`.
- `app/pipeline/stages_experimental/run.py` — the only executable entrypoint. Invoked as:

  ```bash
  ENABLE_EXPERIMENTAL=1 python -m app.pipeline.stages_experimental.run --run-id <id>
  ```

- `app/pipeline/stages_experimental/classifier.py` — neutralized reproduction of the notebook classifier logic.
- `app/pipeline/stages_experimental/classes.py` — neutral identifiers `Class_A` through `Class_N` and neutral metadata only.
- `app/pipeline/stages_experimental/inputs.py` — validates that the referenced core RUN is `done`, required artifacts exist, required artifact classes are acceptable, and inputs are consistent with the RUN `GRID` before classifier execution. Called by `run.py` before invoking `classifier.py`.
- `app/pipeline/stages_experimental/outputs.py` — writes Class IV filesystem-only outputs under `<run_dir>/experimental/`.
- `app/pipeline/stages_experimental/README.md` — states: local-only, experimental, no deployment surface, no scientific validation claim.
- `tests/unit/test_experimental_gate.py` — proves import gating and no API/frontend/default-pipeline access.
- `tests/unit/test_experimental_neutral_terms.py` — proves code, logs, filenames, and generated outputs use only neutral class identifiers.
- `tests/integration/test_experimental_cli.py` — runs the CLI against a frozen completed RUN fixture and verifies deterministic filesystem-only outputs.

#### Functional notes:

- **F-5:** Import gate. `app.pipeline.stages_experimental` cannot be imported unless `ENABLE_EXPERIMENTAL=1` is set. With the flag set, import exposes only the package's internal CLI and neutral modules; it does not register FastAPI routes, frontend controls, core pipeline stages, background tasks, or orchestrator hooks.
- **F-6:** CLI-only invocation. The classifier may run only via `python -m app.pipeline.stages_experimental.run --run-id <id>` with `ENABLE_EXPERIMENTAL=1`. No HTTP route, API module, frontend asset, core pipeline module, production orchestrator module, startup hook, or BackgroundTasks path may import, reference, or invoke `stages_experimental`. Tests may import it only under the env flag. Policy tests enforce this with an AST/grep scan that excludes files inside `app/pipeline/stages_experimental/` itself.
- **F-7:** Output boundary. All classifier outputs are written under `./data/runs/<run_id>/experimental/` and are recorded, if indexed at all, as `ArtifactClass.FILESYSTEM_ONLY`. They are never listed in public artifact lists, never served by `/artifacts/{name}`, never rendered by the SPA, and never converted to Class II or Class III views.
- **F-8:** Neutral terminology. The app-side classifier uses only `Class_A` through `Class_N` and neutral field names such as `class_id`, `class_score`, `class_family`, and `classifier_version`. Source-notebook label families are forbidden in `app/`, `tests/`, logs, generated filenames, generated manifests, and generated outputs. The mapping from neutral identifiers to source-notebook labels lives only in `docs/CLASS_MAPPING.md`, which is project-private and exempt from the forbidden-term scanner.
- **F-9:** No parity or validation claim. The classifier has no notebook-parity test and no scientific ground-truth claim. It has **experimental contract tests** that assert deterministic reproduction of notebook classifier logic after neutralization: same fixture inputs, same thresholds/decision flow, same neutral class IDs, same output schema, all outputs Class IV.
- **F-32:** Dependency boundary. Experimental-only dependencies must be declared as an optional dependency group, for example `project.optional-dependencies.experimental`. The default install path for the core web app does not install heavyweight ML/segmentation packages unless the operator explicitly installs the experimental extra.
- **F-33:** Input boundary. The classifier consumes only completed RUN artifacts produced by the core pipeline, primarily `hypercube`, `pca_anomaly`, object tables, and relevant stage manifests. `app/pipeline/stages_experimental/inputs.py` owns this validation and is called by `run.py` before classifier execution. It must refuse to run if the core RUN status is not `done` or if required artifacts are missing, have unacceptable artifact classes, or are grid-inconsistent.
- **F-34:** No automatic imagery ordering or external side effects. The classifier may not call GEE, order imagery, upload artifacts, hit external APIs, or write outside the RUN directory. It is a local post-processing step over already-produced artifacts.


### 6.3 Web API

Six endpoints, all bound to `127.0.0.1`. JSON endpoints return redacted DTOs per §13; the artifact endpoint streams bytes only through the §14 artifact policy and F-25 response helper.

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/runs` | Create a new RUN. Body: `{lat, lon, name?}`. Validates, constructs `GRID`, enqueues background task. |
| `GET` | `/runs` | List recent RUNs. |
| `GET` | `/runs/{id}` | Get RUN detail and artifact list. |
| `GET` | `/runs/{id}/artifacts/{name}` | Stream a named artifact, subject to §14 classification via F-21 and F-25. |
| `GET` | `/healthz` | Liveness probe. |
| `GET` | `/readyz` | Readiness probe. Fails if EE service-account session cannot initialize. |

`/openapi.json`, `/docs`, and `/redoc` are disabled in v1. They are not part of the public surface because OpenAPI schemas would expose accepted internal field names such as `lat` and `lon`.

#### Functional notes:

- **F-10:** Every JSON endpoint returns a `*Public` DTO. The artifact endpoint either returns a file response approved by F-25 or an `ErrorPublic` DTO. `*Internal` models never cross the HTTP boundary.
- **F-11:** The redaction transform lives in a single file (`app/services/redaction.py`) and is unit-tested per §13.
- **F-12:** All artifact serving — across every route, every code path, every future endpoint — routes through the central guard `can_serve_artifact()` (F-21) and the sole response helper `serve_artifact_response()` (F-25). Direct streaming of files without the helper is a typed exception (`ArtifactServeViolation`) and a policy-test failure.
- **F-13:** The `POST /runs` endpoint **accepts** `lat` and `lon` as input. After acceptance, those values are stored internally (DB, in the relevant non-public fields) but never echoed in the response, never logged at INFO or above, and never returned in any subsequent `GET` response. The response to `POST /runs` contains the run `id`, sanitized `name` (if supplied and if it passes the public-text redaction verifier), and `status` only. Operator-supplied names are treated as public text and are rejected or redacted if they contain coordinates, forbidden archaeology-specific terms, hashes, filesystem paths, or other §13 forbidden patterns.
- **F-21:** Central artifact-serve guard. Single source of truth for whether an artifact may be served over HTTP.

  ```python
  def can_serve_artifact(
      artifact: ArtifactInternal,
      settings: Settings,
  ) -> ArtifactServeDecision:
      """
      Returns a decision object with .allow: bool and .reason: str.
      The reason is logged after redaction but is never returned in HTTP response bodies.
      """
      if artifact.artifact_class == ArtifactClass.FILESYSTEM_ONLY:
          return ArtifactServeDecision(allow=False, reason="class_iv_filesystem_only")
      if artifact.artifact_class == ArtifactClass.LOCAL_SENSITIVE and settings.allow_network_bind:
          return ArtifactServeDecision(allow=False, reason="class_i_blocked_under_network_bind")
      if not artifact.http_servable:
          return ArtifactServeDecision(allow=False, reason="artifact_not_http_servable")
      return ArtifactServeDecision(allow=True, reason="ok")
  ```

- **F-25:** Sole artifact response helper. `serve_artifact_response(run_id, artifact_name, settings)` is the only function allowed to open or stream files under `./data/runs/`. It loads the artifact record, calls `can_serve_artifact()`, performs path normalization and traversal checks, logs the redacted decision, and then returns the response. FastAPI route handlers may not instantiate `FileResponse`, `StreamingResponse`, call `open()`, use `sendfile`, or otherwise stream bytes from run storage directly. `tests/policy/test_no_direct_file_streaming.py` performs an AST scan to enforce this, with `app/services/artifact_response.py` as the only approved exception.
- **F-26:** Public error handling. FastAPI default validation responses are disabled/replaced. All `RequestValidationError`, `HTTPException`, and unhandled exceptions are converted into a generic `ErrorPublic` DTO and passed through `verify_redacted()` before return. Error responses never include request bodies, raw validation `loc` entries containing forbidden field names, internal paths, exception reprs, hashes, or coordinates.
- **F-27:** OpenAPI/docs disabled. `FastAPI(openapi_url=None, docs_url=None, redoc_url=None)` is the v1 default. Any future re-enablement requires an ADR because schemas can reveal internal input fields even when endpoint responses are redacted.

### 6.4 Frontend (SPA)

Single-page application served as static files from the FastAPI app.

#### Required views:

- **Map view:** MapLibre or Leaflet, click-to-place ROI center, shows current RUN's footprint as a polygon. **Default basemap is a blank canvas** with a coordinate graticule overlay. External tile providers (OSM, MapTiler, etc.) are gated behind `ALLOW_EXTERNAL_TILES` env var (off by default). The list of permitted external providers is configurable; no provider is enabled implicitly.
- **Job panel:** List of recent RUNs with status (queued / running / failed / done), elapsed time, and link to detail.
- **Result viewer:** Per-RUN page showing alignment QA pass/fail, stage timings, list of available artifacts, and a tile-rendered preview of selected raster artifacts (DEM hillshade, anomaly heatmap, RGB composite). Tile rendering via `titiler` or equivalent exposes only Class III relative, non-georeferenced previews and no WMS/WFS/OGC endpoints. Under normal v1 operation it is served on `127.0.0.1`; if `ALLOW_NETWORK_BIND=1` is explicitly set, only Class II and Class III HTTP surfaces remain available.
- **Artifact downloads:** Download buttons for each artifact, routed through the `/artifacts/{name}` endpoint and therefore subject to F-12, F-21, and §14.

#### Functional notes:

- **F-14:** The frontend never displays experimental-module outputs. Those are Class IV filesystem-only artifacts and are not listed in public artifact lists, not previewed, and not downloadable through HTTP.
- **F-15:** The frontend never renders raw lat/lon values as user-visible text. Map markers are positional but the underlying numeric coordinates are not surfaced as labels, tooltips, or hover text.
- **F-16:** No third-party analytics, telemetry, error reporting, CDN-loaded scripts, or external font services. All assets ship with the app. The only allowed external network traffic from the frontend is to whichever tile provider is explicitly enabled via `ALLOW_EXTERNAL_TILES`.

### 6.5 Storage & Persistence

- **F-17:** **SQLite** via Alembic-managed migrations for v1. Database file at `./data/gee_screening.db`, gitignored. Two tables to start: `runs` and `artifacts`. Schema captured in `alembic/versions/0001_runs_and_artifacts.py`. Connection via SQLAlchemy with `aiosqlite` driver.
- **F-18:** Artifact binaries stored on the local filesystem under `./data/runs/<run_id>/`. The `artifacts` table indexes them by name, hash, manifest fields, and an `artifact_class` enum (`LOCAL_SENSITIVE` / `REDACTED_PUBLIC` / `PREVIEW_ONLY` / `FILESYSTEM_ONLY` per §14).
- **F-19:** RUN manifests (the `GRID` dict, stage manifests, and run metadata) are persisted as both DB rows and on-disk JSON for redundancy and post-mortem inspection. On-disk JSON manifests are Class I (Local-sensitive); redacted DB-derived views served via the API are Class II.
- **F-20 (v2 migration path):** The DB layer uses SQLAlchemy with no SQLite-specific features (no `JSON1` raw queries, no `WITHOUT ROWID`, no FTS5). Migration to PostgreSQL (and from there, Supabase) is a v2 concern and should require only an Alembic config change and connection-string update.
- **F-22 (no Docker in v1):** v1 does not require Docker, `docker-compose.yml`, or any container runtime. If `docker-compose.yml` exists in the repo at v1 freeze, it is named `docker-compose.optional.yml` and contains only the v2 Postgres + worker stack with a header comment marking it as not-for-v1.
- **F-28 (SQLite session discipline):** No DB session or transaction may remain open across EE calls, export polling, file download/export, raster IO, PCA computation, object extraction, tile rendering, or any other long-running operation. Stages open short-lived sessions only to read/write run status, manifests, and artifact records. A unit/integration test exercises a long dummy stage and asserts the DB connection is released between status updates.
- **F-29 (redacted cache discipline):** Class II artifacts generated on demand may be cached only under `./data/runs/<run_id>/_redacted/`. Cached Class II files must be recorded in the `artifacts` table as `REDACTED_PUBLIC`, must be regenerable from Class I sources, and must never contain hashes, absolute paths, exact coordinates, geometry, CRS transforms, or coordinate columns.

### 6.6 Worker / job execution

- **F-23:** v1 uses FastAPI `BackgroundTasks` for pipeline execution. No separate worker process, no Redis, no queue broker. The pipeline runs in the same process as the API server. The orchestrator persists `runs.status` transitions to DB so the SPA can poll for progress.
- **F-24 (v2 concern):** Migration to a real queue (`arq`, `RQ`, Celery) is a v2 concern triggered by concurrency needs. v1's single-worker assumption is what makes SQLite locking acceptable.
- **F-30 (crash/stale-run semantics):** v1 jobs are **not crash-resumable**. If the API process exits while a run is `running`, the run is marked `stale_failed` on next startup with a public-safe error code. The operator may manually re-run stages from persisted state, but automatic recovery/resume is out of scope for v1.
- **F-31 (single active run):** v1 permits at most one active pipeline run at a time. A second `POST /runs` while another run is `queued` or `running` returns a public-safe conflict response. This protects SQLite locking and the single-process BackgroundTasks model.

---

## 7. Non-Functional Requirements

| # | Requirement |
|---|---|
| N-1 | **Reproducibility:** identical input → output matching the declared parity category (§15). Verified by `tests/notebook_parity/`. |
| N-2 | **Determinism:** any stage that uses randomness must accept and persist a seed. |
| N-3 | **Performance (non-blocking benchmark, not acceptance):** target ≤ 15 min for full pipeline on a 640 × 640 tile on a single workstation, no GPU. Measured and recorded per release; does not block v1 acceptance. |
| N-4 | **EE auth:** service-account only. App refuses to start if the SA key file is missing or invalid. No `ee.Authenticate()` call may exist anywhere in the codebase. |
| N-5 | **Secrets handling:** SA key path read from `.env`, never committed. `.gitignore` enforces this. Pre-commit hook scans for known key patterns. |
| N-6 | **Logging:** structured logs (JSON) to stdout, with PII / coordinate redaction at the formatter level (§13). Log files are gitignored. |
| N-7 | **Error handling:** structured exceptions (`StageError`, `GridDriftError`, `RedactionViolationError`, `ArtifactServeViolation`, `ArtifactClassError`, etc.). No `raise RuntimeError("❌ ...")` patterns. |
| N-8 | **Test coverage:** all stages have unit tests. All endpoints have integration tests. The redaction transform has a dedicated test suite that programmatically inspects every endpoint's JSON output for forbidden fields. All tests run locally and via pre-commit hooks; full CI is out of scope for v1. |
| N-9 | **Bind address:** FastAPI binds `127.0.0.1` by default. Binding to `0.0.0.0` requires explicit `ALLOW_NETWORK_BIND=1` env var. The app logs a loud warning at startup if that flag is set, and Class I (Local-sensitive) artifacts become unservable in that mode via F-21. |
| N-10 | **No coordinate leakage in tests:** test fixtures use a deliberately uninteresting reference ROI documented in `docs/PARITY_PROTOCOL.md`. No production ROIs appear in committed code or fixtures. |
| N-11 | **Artifact classification enforcement:** every artifact written to disk is recorded in the `artifacts` table with a non-null `artifact_class`. Writes without a class raise `ArtifactClassError`. Reads route through F-21 and F-25 unconditionally. |
| N-12 | **Parity category as code metadata:** every `Stage` subclass declares `parity_category: ParityCategory` (and `parity_reason: str` when category is `PARITY_CORRECTS` or `PARITY_REPLACES`) as class attributes. The orchestrator's stage registry refuses to register a stage without these. Test collection refuses to collect a parity test whose declared category disagrees with the stage's class attribute. |
| N-13 | **No automatic API schema exposure:** `/openapi.json`, `/docs`, and `/redoc` are disabled in v1. Any future enablement requires an ADR and a schema-redaction review. |
| N-14 | **Public-safe errors:** all error responses, including validation errors, use `ErrorPublic` and pass `verify_redacted()` before leaving the app. Default FastAPI 422 bodies are not allowed. |
| N-15 | **No direct file streaming:** route handlers may not directly use `FileResponse`, `StreamingResponse`, `open()`, `Path.open()`, `aiofiles.open()`, or `sendfile` for files under `./data/runs/`. The only approved path is `serve_artifact_response()`, which calls F-21. |
| N-16 | **SQLite lock avoidance:** DB transactions are short-lived and never span long-running EE, file, or raster operations. v1 allows only one active run at a time. |
| N-17 | **Crash semantics:** v1 pipeline jobs are not crash-resumable. Startup marks stale `running` jobs as `stale_failed` and exposes only a public-safe status/error code. |
| N-18 | **Experimental classifier containment:** the classifier is optional, env-gated, CLI-only, neutral-terms-only, filesystem-only, and excluded from API/frontend/default-pipeline invocation. Contract tests verify deterministic neutralized logic and Class IV outputs. |

---

## 8. Out of Scope (v1)

Items deliberately excluded from this release:

- Multi-user authentication, accounts, sessions.
- Public deployment, hostname, TLS, reverse proxy configuration.
- Automatic imagery ordering or commercial-imagery integration.
- KMZ/KML/GeoJSON exports through the API. The experimental CLI may produce them as Class IV filesystem-only artifacts under `<run_dir>/experimental/`, but no HTTP path may serve or list them.
- Coordinate-bearing API responses, including in error messages.
- Mobile/responsive frontend optimization beyond what MapLibre provides for free.
- Notebook-to-app migration tooling. The notebook stays in place as a reference.
- Continuous integration (CI) against the private repo. Substantive checks run as local tests and pre-commit hooks; CI is a follow-up decision.
- Any OGC-compliant output (WMS, WFS, WCS).
- Sharing, exporting, or publishing pipeline outputs to any external service.
- PostgreSQL backend, `docker-compose`, container runtime requirement (deferred to v2; see F-20, F-22).
- Separate worker/queue process (deferred to v2; see F-24).
- Crash-resumable or distributed jobs. v1 marks stale runs failed and supports manual re-run from persisted state only.
- Public API documentation / OpenAPI exposure. `/openapi.json`, `/docs`, and `/redoc` are disabled in v1.
- Public release of private notebook-migration documentation without a separate scrub/redaction pass.

---

## 9. Acceptance Criteria

The v1 release is "done" when all of the following are true:

| # | Criterion |
|---|---|
| A-1 | `pytest tests/unit/` passes. |
| A-2 | `pytest tests/integration/` passes against a clean DB on a fresh checkout. |
| A-3 | `pytest tests/notebook_parity/` passes — every defensible-stage artifact matches its declared parity category (§15) against the reference run captured per `docs/PARITY_PROTOCOL.md`. The stage's `parity_category` class attribute and the test's category decorator must agree, or test collection fails (N-12). |
| A-4 | The app starts with `uvicorn app.main:app --host 127.0.0.1 --port 8000` and `GET /healthz` returns 200. `/openapi.json`, `/docs`, and `/redoc` return 404 or are otherwise unavailable. |
| A-5 | The app refuses to start if the EE service-account key is missing or invalid (verified by a startup test that runs without the key). |
| A-6 | Every endpoint's JSON response is verified to contain no forbidden field per §13 by the redaction test suite, including success responses, validation errors, conflicts, artifact denials, and unhandled-exception fallbacks. |
| A-7 | The experimental package cannot be imported unless `ENABLE_EXPERIMENTAL=1` is set. With the flag set, the package imports but registers no API route, frontend control, core stage, startup hook, background task, or orchestrator hook. Verified by `tests/unit/test_experimental_gate.py`. |
| A-8 | The experimental classifier runs only through `ENABLE_EXPERIMENTAL=1 python -m app.pipeline.stages_experimental.run --run-id <id>` against a completed RUN. No FastAPI route, API module, frontend asset, production orchestrator module, or core pipeline module references `stages_experimental`. Verified by policy tests and `tests/integration/test_experimental_cli.py`. |
| A-9 | No forbidden archaeology-specific term appears in any source file under `app/` or `tests/`, in any log output, generated output, generated filename, or committed filename. Project documentation is private by default; `docs/CLASS_MAPPING.md` and notebook-migration documentation may contain source-notebook terminology only if explicitly marked private and excluded from publication. Verified by a grep/AST test in the pre-commit suite. |
| A-10 | Every artifact written has a recorded `artifact_class` per §14, and every artifact-serving code path routes through `serve_artifact_response()`, which calls `can_serve_artifact()`. Direct `FileResponse`, `StreamingResponse`, `open()`, `Path.open()`, `aiofiles.open()`, and `sendfile` usage from route handlers is blocked by `tests/policy/test_no_direct_file_streaming.py`. |
| A-11 | The SPA, served from the running app, allows the operator to: pick a point on a blank/local map → submit a RUN → see it progress through stages → view results → download artifacts subject to §14 rules. External tiles are unavailable unless `ALLOW_EXTERNAL_TILES` is explicitly set. The SPA never lists or previews Class IV experimental outputs. |
| A-12 | A clean clone of the repo on a clean machine can complete A-1 through A-11 and A-13 through A-20 with only the setup steps in `README.md` and **no Docker**. The experimental classifier may require installing the explicit experimental optional dependency group. |
| A-13 | Malformed `POST /runs` requests do not return default FastAPI 422 bodies. They return generic `ErrorPublic` DTOs that pass `verify_redacted()` and do not expose `lat`, `lon`, request input, internal schema names, or validation locations containing forbidden fields. |
| A-14 | Operator-supplied run names containing coordinate-like patterns, forbidden archaeology-specific terms, hashes, or absolute paths are rejected or redacted before storage in public fields. |
| A-15 | With `ALLOW_NETWORK_BIND=1`, Class I (`LOCAL_SENSITIVE`) artifacts cannot be downloaded, Class IV (`FILESYSTEM_ONLY`) artifacts are still 404, and Class II / Class III artifacts remain available only through their approved redacted/preview code paths. |
| A-16 | If the process exits while a run is `running`, the next startup marks it `stale_failed` and exposes only a public-safe status/error code. |
| A-17 | A policy test confirms no DB transaction remains open across a simulated long-running stage boundary, and a concurrency test confirms a second active run is rejected while one is queued/running. |
| A-18 | The experimental classifier's frozen-fixture contract test passes: same neutralized decision flow, same neutral class IDs, deterministic output schema, and no source-notebook label strings in code/logs/filenames/outputs. |
| A-19 | All experimental classifier outputs are written only under `./data/runs/<run_id>/experimental/`, are marked or treated as `FILESYSTEM_ONLY`, and are never served, listed, or previewed through HTTP. |
| A-20 | The default install/test path for the core app does not require experimental-only dependencies. Experimental dependencies are installed only through the documented optional extra. |


## 10. Open and Decided Questions

### Decided in v0.2 / v0.3 / v0.5:

- **Q-3 (RESOLVED, v1):** Whether the experimental module gets ported. **Decided: yes, in v1**, but only as an env-gated, CLI-only, neutral-terms-only, filesystem-output-only experimental module. It is not part of the API, frontend, default pipeline, or defensible parity surface.
- **Q-storage (RESOLVED, SQLite for v1):** Storage backend. **Decided: SQLite.** Postgres/Supabase deferred to v2.
- **Q-worker (RESOLVED, BackgroundTasks for v1):** Job execution surface. **Decided: FastAPI BackgroundTasks.** Real queue deferred to v2.
- **Q-docker (RESOLVED, no Docker in v1):** Container runtime. **Decided: not required.** `docker-compose.optional.yml` may exist but is v2 path.

### Still open:

- **Q-1:** Tile-renderer choice (`titiler` vs. `terracotta` vs. custom). Revisit at frontend stage.
- **Q-4:** Default demo ROI selection. Revisit before first map-view implementation. Must be non-sanctioned, non-heritage, scientifically uninteresting.
- **Q-5:** Whether to expose the `notebook_parity` reference run as an in-repo fixture or as a Git-LFS / external-storage artifact. Decide at parity-suite scaffolding stage.
- **Q-6:** Pre-commit hook framework (`pre-commit` package vs. custom shell hooks). Trivial decision, defer to first hook implementation.
- **Q-7:** Directory sketch reconciliation. The standalone `docs/DIRECTORY_SKETCH.md` (separate from this PRD) needs editing to match v0.5 decisions: SQLite, no Docker, no separate worker, BackgroundTasks, and classifier-in-v1 under `stages_experimental/`. Action: revise the sketch in lockstep with freezing this PRD.

---

## 11. Risks & Mitigations

| Risk | Severity | Mitigation |
|---|---|---|
| Operator changes mind and deploys to VPS or makes repo public without re-applying safety constants. | High | Bind-address default + experimental CLI-only isolation + endpoint redaction + F-21/F-25 artifact guard make accidental public exposure architecturally hard. Operator has committed to legal review before changing surface. |
| Project documentation containing notebook terminology is mistaken for publishable source. | Medium | §16 narrows the publishability target to `app/`, `tests/`, filenames, hooks, and logs. Appendix A and notebook-migration docs are explicitly private unless scrubbed. |
| Experimental terminology leaks into defensible code paths or commits. | Medium | A-9 grep/AST test in pre-commit. Runtime classifier uses only `Class_A`–`Class_N`; mapping docs isolated/private. |
| Experimental classifier becomes accidentally invocable through the web app. | High | F-6/A-8: CLI-only invocation, no API/frontend/orchestrator references, AST/grep policy tests, and Class IV outputs only. |
| Experimental classifier outputs leak over HTTP. | High | F-7/F-21/F-25/A-19: outputs live under `experimental/`, are `FILESYSTEM_ONLY`, are never listed, and `can_serve_artifact()` always denies them. |
| Notebook parity drift over time (notebook is updated, app falls behind). | Medium | Parity tests are local-blocking via pre-commit. Operator owns deciding when to re-baseline against an updated notebook. |
| EE service-account key accidentally committed. | High | `.gitignore` + pre-commit hook scanning for known key patterns + N-5 enforcement. |
| Stage produces output not byte-aligned to GRID, silently propagating drift. | High | Zero-shift gate (F-1) halts pipeline on any drift. Every stage's manifest records hash and transform. |
| Future code path streams a file directly without consulting the artifact guard. | High | `serve_artifact_response()` is the only approved serving helper; it calls F-21. AST policy tests block direct `FileResponse`, `StreamingResponse`, `open()`, and `sendfile` use in route handlers. |
| FastAPI default docs or validation errors leak internal coordinate field names. | High | `/openapi.json`, `/docs`, and `/redoc` disabled; custom validation/error handlers return `ErrorPublic` and pass `verify_redacted()`. |
| Redaction false positives block harmless scientific output. | Medium | §13.2 makes float-pair checks context-aware and explicitly exempts declared non-spatial values such as eigenvalues and summary stats. |
| Tile-provider request logs leak viewed ROI. | Medium | External tiles off by default. When enabled, operator accepts the leak via explicit env flag. |
| Preview tiles reveal non-georeferenced visual anomaly patterns. | Medium | Class III leakage boundary is explicit. Previews do not reveal exact coordinates but are not public-publication artifacts. |
| Operator (or future contributor) reinstates archaeology terms in code. | Medium | A-9 grep/AST test in pre-commit blocks the commit. |
| Pipeline runtime exceeds N-3 benchmark on operator's hardware. | Low | N-3 is non-blocking. Document actual runtimes; optimize in v2. |
| SQLite locking under accidental concurrent access. | Low | v1 uses one active run at a time (F-31), short DB sessions (F-28), and no separate worker process. Concurrency is a v2 concern that comes with the Postgres migration. |
| API process crashes mid-pipeline and leaves a stale run. | Medium | F-30/N-17 mark stale `running` jobs as `stale_failed` at next startup. v1 does not promise crash-resumable jobs. |
| Stage registered without a parity category. | Medium | N-12: orchestrator refuses to register; test collection refuses to collect. Cannot reach production. |

---

## 12. Glossary

- **Defensible pipeline:** the ~30 cells of the source notebook implementing standard published remote-sensing techniques. Has parity tests with declared categories per §15.
- **Experimental module:** the notebook classifier logic ported into v1 as an env-gated, CLI-only, neutral-terms-only research module. It is not part of the defensible pipeline and has contract tests, not scientific validation or parity claims.
- **RUN:** one execution of the pipeline against one ROI, producing a set of artifacts persisted to disk and indexed in DB.
- **GRID:** the immutable manifest fixing CRS, scale, size, and crsTransform for a RUN. All stage outputs must align to it byte-for-byte. Public DTOs do not expose the transform, origin, bounds, or EPSG zone.
- **Redaction DTO:** the `*Public` Pydantic model returned from API endpoints, programmatically stripped per §13.
- **ErrorPublic:** the public-safe error DTO returned for validation errors, artifact denials, conflicts, and unhandled exceptions. It contains only fixed enum codes and redacted text.
- **Parity test:** a test that asserts the app's stage output matches its declared parity category against captured notebook output on a known reference ROI.
- **Coordinate-bearing artifact:** any artifact whose contents contain or trivially recover exact geographic coordinates. Class I (Local-sensitive) or Class IV (Filesystem-only) per §14.
- **Local-sensitive (Class I):** an artifact that may be served over loopback (`127.0.0.1`) but is refused when the app is bound to a network interface.
- **Artifact serve guard:** `can_serve_artifact()`, the policy function that decides whether an artifact class may be served over HTTP in the current settings.
- **Artifact response helper:** `serve_artifact_response()`, the only approved function that opens or streams artifact bytes under `./data/runs/`.

---

## 13. Redaction Contract

The redaction transform `app/services/redaction.py` is the load-bearing boundary between internal state and HTTP responses. This section is normative.

### 13.1 Forbidden public fields (by name)

Any field whose key matches one of the following (case-insensitive) must not appear in a `*Public` DTO or public error response:

```
lat, latitude, lon, lng, long, longitude
x, y                    (when paired with a CRS/coordinate/spatial context)
coords, coordinates
geometry, geom
bounds, bbox
extent
crs, epsg, projection, spatial_ref
crs_transform, crsTransform, transform
origin, ul_x, ul_y, lr_x, lr_y
pixel_size, gsd
hash, sha, sha256, md5, checksum, fingerprint
filesystem_path, abs_path, full_path
request_body, input, raw_input
traceback, stacktrace, exception_repr
```

`epsg` and `crs` are forbidden as public fields because the UTM zone can reveal approximate location. Public DTOs may expose only the generic field `grid.crs_family = "utm"` if a CRS label is needed for UI copy; no zone, EPSG code, transform, origin, or bounds may be returned.

### 13.2 Forbidden public patterns

Independent of field name, any value matching one of the following patterns must be redacted:

- A WKT or GeoJSON geometry literal.
- A KMZ/KML/GeoJSON file as inline content.
- A 32+ character hex string (likely a hash).
- An absolute filesystem path containing `/home/`, `/Users/`, `/mnt/`, or starting with a drive letter.
- A pair of floats in plausible WGS84 ranges (`-90.0 ≤ latitude ≤ 90.0`, `-180.0 ≤ longitude ≤ 180.0`) **only when schema context suggests spatial meaning**.

The float-pair rule is deliberately context-aware. It applies when the keys, parent object name, or schema type contain spatial terms such as `coord`, `point`, `center`, `vertex`, `bbox`, `bounds`, `geometry`, `location`, `roi`, `lat`, `lon`, `x`, `y`, `utm`, `crs`, `transform`, or `origin`. It does **not** apply to declared non-spatial values such as eigenvalues, summary statistics, histogram bins, model scores, PCA loadings, durations, sizes, counts, or percentages unless those values are nested under a spatial parent.

### 13.3 Coordinate columns in tabular artifacts

CSV artifacts served as Class II must not contain columns whose header (case-insensitive) is `lat`, `lon`, `latitude`, `longitude`, `x`, `y`, `geometry`, `wkt`, `geojson`, `easting`, `northing`, `utm_x`, or `utm_y`.

The Class II view of `objects_index.csv` may include only non-georeferenced pixel-space descriptors:

```
object_id
row_min, row_max
col_min, col_max
width_px, height_px
area_px
score
class_label        (only neutral labels, if present)
```

Pixel offsets are allowed only because public DTOs never include the grid origin, transform, EPSG zone, bounds, or any other value needed to recover exact geographic coordinates. Pixel offsets may not appear in the same response as a Class I manifest or any georeferencing metadata.

### 13.4 Permitted public fields

The following are explicitly allowed in `*Public` DTOs after they pass `verify_redacted()`:

- `id` (UUID or autoincrement, not coordinate-derived)
- `name` (operator-supplied label, after public-text redaction/rejection)
- `status`, `created_at`, `updated_at`
- `stage_name`, `stage_status`, `stage_duration_ms`
- `artifact_name`, `artifact_class`, `artifact_size_bytes`
- `grid.crs_family` (generic label only, e.g. `"utm"`)
- `grid.scale_m` (constant v1 output scale, e.g. `10`)
- `grid.size_px` (constant v1 tile size, e.g. `640`)
- `eigenvalues` (PCA eigenvalues — informational, not coordinate-derived)
- `row_*`, `col_*`, `width_px`, `height_px`, `area_px` fields in redacted Class II object tables
- Error `code` values from a fixed public enum, after the error formatter has run the same redaction transform.

### 13.5 Public text fields

Public text fields include `name`, public error messages, artifact display labels, and any user-visible frontend text derived from backend values.

Public text is rejected or redacted if it contains:

- coordinate-like pairs,
- forbidden archaeology-specific terms,
- a 32+ character hex string,
- an absolute filesystem path,
- a KMZ/KML/GeoJSON/WKT literal,
- a service-account-looking email or credential fragment.

The preferred behavior for `name` is rejection with a generic `invalid_public_name` error code rather than silent mutation.

### 13.6 Enforcement

- The redaction transform is a single function `redact(internal_model) -> public_model` with unit tests per forbidden field and pattern.
- The FastAPI app installs a response middleware that re-runs a `verify_redacted(payload)` check on every outgoing JSON response. If verification fails, the response is replaced with HTTP 500 and a `RedactionViolationError` is logged.
- Logging uses a custom JSON formatter that applies the same redaction rules to all log records at INFO level and above.
- FastAPI validation errors are handled by a custom exception handler. Default 422 bodies are not used because they can expose internal field names and request input.
- `/openapi.json`, `/docs`, and `/redoc` are disabled in v1. Schema exposure is treated as an HTTP-boundary leak unless a future ADR explicitly re-enables and redacts it.
- `verify_redacted()` is tested against successful responses, validation errors, unhandled exception fallbacks, artifact-denial responses, and log-record examples.

---

## 14. Artifact Taxonomy

Every artifact in the system is assigned exactly one of four classes at write time. The class is recorded in the `artifacts` table as an enum and is immutable for that artifact. Reads route through `serve_artifact_response()` (F-25), which calls `can_serve_artifact()` (F-21), unconditionally.

### Class I — Local-sensitive (enum: `LOCAL_SENSITIVE`)

- **Contents:** raw stage outputs with full georeference: GeoTIFFs (DEM, SAR, S2 indices, hypercube, PCA anomaly), `.npy` arrays with associated transforms, stage manifest JSON files containing geometry/hashes.
- **HTTP exposure:** served by `/artifacts/{name}` **only when the app is bound to `127.0.0.1`** and only through `serve_artifact_response()`. With `ALLOW_NETWORK_BIND=1` set, F-21 returns `allow=False, reason="class_i_blocked_under_network_bind"` and the endpoint responds 451 (Unavailable For Legal Reasons) with a public-safe error code.
- **Frontend exposure:** referenced by name in the artifact list, rendered into Class III previews for the result viewer, available as direct downloads to the localhost operator.
- **Storage:** `./data/runs/<run_id>/`.

### Class II — Redacted-public (enum: `REDACTED_PUBLIC`)

- **Contents:** derived from Class I via redaction. Object table CSV with coordinate columns stripped. RUN summary JSON without geometry. Stage manifests with hashes and paths removed. Eigenvalue reports (already coordinate-free).
- **HTTP exposure:** served on any bind, including with `ALLOW_NETWORK_BIND=1`, through approved redacted-generation code paths only.
- **Frontend exposure:** fully visible in the SPA.
- **Storage:** generated on demand from Class I. May be cached under `./data/runs/<run_id>/_redacted/` only if the cached file is registered as `REDACTED_PUBLIC` in the `artifacts` table and remains fully regenerable from Class I sources. No unregistered redacted cache files are allowed.

### Class III — Preview-only (enum: `PREVIEW_ONLY`)

- **Contents:** rendered PNG / WebP tiles or thumbnails of raster artifacts. Low-resolution (≤ 1024 px per side), no embedded georeference, no world file.
- **HTTP exposure:** served on any bind via the tile renderer at `/tiles/<run_id>/<artifact>/{z}/{x}/{y}.png`. Tile coordinates are relative to the artifact extent, not georeferenced.
- **Frontend exposure:** rendered into the map view as a local overlay.
- **Storage:** generated on demand by `titiler` (or chosen equivalent); may be cached under `./data/runs/<run_id>/_previews/` and registered as `PREVIEW_ONLY`.
- **Leakage boundary:** Class III previews may reveal visual anomaly patterns, raster texture, or relative object layout. They are allowed under network bind only because they do **not** expose exact coordinates, georeference, CRS transform, or source file metadata. They are not public-publication artifacts and should not be shared outside the operator's local workflow without separate review.

### Class IV — Filesystem-only (enum: `FILESYSTEM_ONLY`)

- **Contents:** KMZ files, KML files, any GeoJSON with exact coordinates, and anything written by `stages_experimental/` in v1 or later.
- **HTTP exposure:** **never served by HTTP under any flag.** F-21 always returns `allow=False, reason="class_iv_filesystem_only"`. The `/artifacts/{name}` endpoint responds 404 for any Class IV artifact regardless of bind address or env flags.
- **Frontend exposure:** never. Not listed in artifact lists. The operator accesses them via filesystem only.
- **Storage:** `./data/runs/<run_id>/experimental/` for experimental classifier outputs, or `./data/runs/<run_id>/kmz/` for any other local-only KMZ/KML artifacts.

### 14.1 Classification at write time

The stage protocol (`_base.py`) requires every artifact emission to specify its class. There is no "default" class; writes without an explicit class raise `ArtifactClassError`. This is the enforcement mechanism for N-11.

### 14.2 Class transitions

An artifact's class is immutable. To produce a "less restricted" view of a Class I artifact, a separate Class II artifact is generated via the redaction transform. The Class I original is retained. Class II artifacts generated on demand may be cached only under `_redacted/` and registered as `REDACTED_PUBLIC`.

### 14.3 Sole serving path

The only approved way to serve artifact bytes is:

```
api route -> serve_artifact_response() -> can_serve_artifact() -> path normalization -> response
```

Any route, service, tile endpoint, or future feature that bypasses this path for files under `./data/runs/` is a policy violation. The exception is the tile renderer's internal read path for Class III preview generation, which must still use the artifact registry to load its source artifact and must never expose the source file bytes directly.

---

## 15. Parity Categories

Every parity test in `tests/notebook_parity/` declares one of three categories. The category determines what the test asserts. **Per N-12, the category is also declared as a class attribute on the `Stage` subclass it tests, and the orchestrator refuses to register stages without it.**

### `PARITY_REPRODUCES`

The stage's output is expected to be byte-identical to the notebook's output on the reference ROI (modulo timestamp metadata in TIFF headers, which is normalized before comparison).

Used when: the notebook implementation is correct and the app is a direct port.

Examples: DEM ingest, SAR RTC, DEM derivatives, hypercube assembly, PCA anomaly, object extraction, alignment QA.

### `PARITY_CORRECTS`

The stage's output is expected to **differ** from the notebook in a documented, intentional way. The test asserts the corrected output against an analytically-derived or peer-reference value, not the notebook's output.

Used when: the notebook has a known bug or formula error.

Examples: `IRON_SWIR` (notebook denominator `B11 − B12` → app denominator `B11 + B12`). Each `PARITY_CORRECTS` test includes a docstring linking to the original bug and the corrected formula's reference. The stage class declares `parity_reason: str` explaining the correction.

### `PARITY_REPLACES`

The stage has no direct notebook equivalent, or replaces a notebook behavior that was Colab-specific, unsafe, or out of scope. The test asserts only the app's contract; no comparison to notebook output is made.

Used when: the function exists only in the app.

Examples: service-account EE init (replaces `ee.Authenticate()`), the FastAPI bind-address guard, the redaction transform, the artifact classifier itself. The stage class declares `parity_reason: str` explaining what was replaced and why.

### Declaration — code metadata, not docs

Every stage that produces a parity-testable artifact declares its category as a class attribute:

```python
from app.pipeline._base import Stage, ParityCategory

class S2IndicesStage(Stage):
    name = "s2_indices"
    parity_category = ParityCategory.PARITY_CORRECTS
    parity_reason = "IRON_SWIR denominator corrected from notebook bug (B11-B12) to (B11+B12)"

    def run(self, grid, paths) -> StageResult:
        ...
```

The orchestrator's stage registry validates these attributes at app startup. Missing or invalid: app refuses to start. Inconsistent with the parity test's decorator: test collection fails.

This means the category lives in *one* place — the code — and docs / Appendix A read from it, not the other way around.


### Experimental classifier contract tests — not parity tests

The experimental classifier is not a `Stage` in the core orchestrator and does not receive a `ParityCategory`. Its tests live outside `tests/notebook_parity/`.

Classifier tests assert implementation contracts only:

- import requires `ENABLE_EXPERIMENTAL=1`;
- CLI refuses incomplete or grid-inconsistent RUNs;
- frozen fixture input produces deterministic neutral class IDs and stable schema;
- source-notebook label strings are absent from code, logs, filenames, manifests, and outputs;
- every output is Class IV / `FILESYSTEM_ONLY`;
- no HTTP route, frontend asset, or core orchestrator path references the package.

These tests prove containment and deterministic reproduction of the notebook's classifier decision flow after neutralization. They do **not** assert archaeological, mineral, cultural-property, or real-world detection accuracy.

---

## 16. Threat Model

The safety constraints in this PRD exist to mitigate specific accidents the operator could plausibly make. Each accident below traces to defenses in the document.

**1. Accidental public exposure of the source package.** Operator pushes to GitHub and the visibility flips public, or pushes a working branch to the wrong remote. **Defense:** the source package (`app/`), tests (`tests/`), filenames, hooks, and runtime logs do not embed coordinates, hashes, archaeology-specific terms, or credentials. A-9 (grep/AST), N-5 (key scan), §10 Q-4 (research-safe default ROI). Project documentation that preserves notebook migration terminology is private by default and must be scrubbed before any public release. The publishability target for v1 is the source package and tests, not the full private project notebook history.

**2. Accidental coordinate, hash, or schema leakage via API.** An endpoint, validation error, OpenAPI schema, error message, or log record contains a value that lets a reader correlate the RUN to a specific place or to another database. **Defense:** §13 (Redaction Contract), disabled OpenAPI/docs, custom public error handlers, middleware verification on every outgoing JSON response, and log formatter redaction.

**3. Accidental resurrection of experimental labels.** Operator (or future contributor) adds `Gold_Detector`, `archeo_dictionary`, etc., back into the code under time pressure or curiosity. **Defense:** A-9 grep/AST test in pre-commit, blocks the commit before it reaches the repo. `docs/CLASS_MAPPING.md` and private notebook-migration docs are the only approved places for source-notebook terminology.

**4. Accidental committed secrets.** EE service-account key, `.env` contents, or other credentials end up in a tracked file. **Defense:** `.gitignore` patterns, pre-commit secret-pattern scan (N-5), N-4 startup test that refuses to run without a valid key (so misconfiguration is loud).

**5. Accidental use of interactive EE auth.** Code adds `ee.Authenticate()` back, either from a copy-paste or because a contributor doesn't know the constraint. **Defense:** C5 (constant), N-4 (no `ee.Authenticate()` in codebase, enforced by grep), `app/services/ee_session.py` as the only EE init path.

**6. Future-self changing deployment surface without realizing the safety impact.** Operator decides to "just try it on the VPS" and binds to `0.0.0.0`. **Defense:** N-9 (explicit env flag), F-21 (Class I artifacts unservable in that mode), startup warning log, the operator's own commitment in §4 to legal review before changing surface.

**7. Accidental visual-output sharing.** A preview tile or screenshot is non-georeferenced but still reveals an anomaly pattern or relative object layout. **Defense:** Class III explicitly states this residual leakage; previews are allowed because they do not reveal exact coordinates, but they are not public-publication artifacts. Sharing them outside the local workflow requires separate review.

**8. Accidental stale job trust.** The local server crashes mid-pipeline and a stale `running` run appears valid. **Defense:** F-30/N-17 mark stale runs as `stale_failed` at startup and expose only public-safe status/error codes.

**Out of scope:** sophisticated targeted attacks against the operator's machine, GitHub account compromise, EE service-account compromise via key exfiltration outside this app's control, and legal compulsion of data disclosure. These are real risks but not ones this PRD's architecture addresses — they require process responses, not code.

**Defense priority:** when two design choices conflict, the one that better mitigates accidents #1 and #6 (public exposure / deployment-surface change) wins. These are the highest-likelihood scenarios.

---

## 17. Implementation Milestones

These milestones do not weaken the v1 acceptance criteria. They exist so implementation can proceed in safe slices.

| Milestone | Scope | Exit condition |
|---|---|---|
| M0 | Skeleton app, settings, SQLite/Alembic, structured errors, redaction middleware, disabled docs/OpenAPI, service-account EE init stub/tests. | `healthz` works, `readyz` fails safely without key, redaction and error tests pass. |
| M1 | RUN model, artifact model, artifact taxonomy, `can_serve_artifact()`, `serve_artifact_response()`, storage paths, no-direct-streaming policy test. | All four artifact classes have integration tests. |
| M2 | Grid construction, DEM ingest, zero-shift gate, manifests, short DB-session discipline. | Grid/DEM/zero-shift unit and parity tests pass. |
| M3 | SAR RTC, S2 indices including `IRON_SWIR` correction, DEM derivatives, thermal LST. | Stage unit tests and declared parity-category tests pass. |
| M4 | Hypercube, PCA anomaly, object extraction, alignment QA. | Full pipeline integration test passes on reference ROI. |
| M5 | SPA: blank map, run creation, job panel, result viewer, Class II downloads, Class III previews, Class I localhost-only downloads. | A-11 passes locally with external tiles off. |
| M6 | Experimental classifier: env gate, CLI entrypoint, neutral class IDs, optional dependencies, Class IV outputs, frozen-fixture contract test. | A-7 through A-9 and A-18 through A-20 pass; no API/frontend/default-pipeline path can invoke the classifier. |
| M7 | Policy freeze: forbidden-term scans, no `ee.Authenticate()`, no direct file streaming, stale-run handling, README clean-clone setup. | A-1 through A-20 pass on a clean machine with no Docker. |

---

## Appendix A — Notebook Migration Matrix

**Privacy note:** Appendix A preserves source-notebook terminology for migration accuracy. It is project-private documentation. It is not part of the source-package publishability target described in §16, and it must be scrubbed or removed before any public release.

Disposition of source notebook cells for v1.

**Columns:**

- **Cell:** index in `new.ipynb` (0-based).
- **Title:** the cell's first comment / header, abbreviated.
- **PRD stage:** which stage in §6.1 (or `n/a` if not a defensible stage).
- **Destination:** app module path or `[discard]` / `[defer-v2]` / `[reference-only]`. Experimental classifier rows included in v1 point to `app/pipeline/stages_experimental/`.
- **Decision:** `reproduce` / `correct` / `replace` / `defer` / `discard`.
- **Parity category:** `PARITY_REPRODUCES` / `PARITY_CORRECTS` / `PARITY_REPLACES` / `EXPERIMENTAL_CONTRACT` / `—` (when not applicable, i.e. for discard/defer).
- **Artifact:** primary output (if any).
- **Test:** parity test file or `n/a`.
- **Notes:** anything non-obvious.

### A.1 Setup, installs, working dirs (cells 0–8)

| Cell | Title | PRD stage | Destination | Decision | Parity | Artifact | Test | Notes |
|---|---|---|---|---|---|---|---|---|
| 0 | `ColabFolder` constant | n/a | `app/config.py` | replace | PARITY_REPLACES | n/a | n/a | Replaced by config.py settings. |
| 1–4 | `!pip install …` | n/a | `pyproject.toml` | replace | PARITY_REPLACES | n/a | n/a | Dependency management moves to project metadata. |
| 5 | Imports + `Pair01/Pair02` setup | n/a | `app/main.py`, `app/pipeline/orchestrator.py` | replace | PARITY_REPLACES | n/a | n/a | Folder-tree side effects become RUN dir creation. |
| 6, 7 | Refined Lee filter functions | SAR RTC | `app/pipeline/stages/sar_rtc.py` | reproduce | PARITY_REPRODUCES | n/a | unit | Two near-identical cells; ship the merged version. |
| 8 | `drive.mount` | n/a | [discard] | discard | — | n/a | n/a | Colab-specific. |

### A.2 Map, point picker, ROI (cells 9–13)

| Cell | Title | PRD stage | Destination | Decision | Parity | Artifact | Test | Notes |
|---|---|---|---|---|---|---|---|---|
| 9 | `geemap.Map` with point picker | n/a | `frontend/` (SPA map view) | replace | PARITY_REPLACES | n/a | integration | Replaced by MapLibre/Leaflet SPA view. |
| 10 | Colab JS auto-scroll | n/a | [discard] | discard | — | n/a | n/a | Colab-specific UI hack. |
| 11 | Print `SelectedPoint` formats | n/a | [discard] | discard | — | n/a | n/a | Debug. |
| 12, 13 | ROI construction (15 km / 6.4 km, UTM) | Grid construction | `app/services/grid.py` | reproduce | PARITY_REPRODUCES | `GRID` manifest | `tests/unit/test_grid.py` | UTM zone derived from input lon. |

### A.3 RUN folder + grid manifest + DEM (cells 14–18)

| Cell | Title | PRD stage | Destination | Decision | Parity | Artifact | Test | Notes |
|---|---|---|---|---|---|---|---|---|
| 14 | RUN folder tree + `GRID` + `PATHS` | Grid construction | `app/services/storage.py`, `app/pipeline/manifest.py` | replace | PARITY_REPLACES | RUN dir | integration | Replaced by DB-backed RUN model. |
| 15 | Copernicus DEM ingest | DEM ingest | `app/pipeline/stages/dem.py` | reproduce | PARITY_REPRODUCES | `dem.tif` | `test_dem_parity.py` | |
| 16 | RUN+GRID guard | n/a | `app/services/storage.py` | replace | PARITY_REPLACES | n/a | unit | Replaced by stage protocol enforcement. |
| 17 | ZERO-SHIFT GATE | Zero-shift gate | `app/pipeline/stages/zero_shift.py` | reproduce | PARITY_REPRODUCES | pass/fail report | `test_zero_shift.py` | |
| 18 | Audit all tifs vs grid | Zero-shift gate | `app/pipeline/stages/zero_shift.py` | reproduce | PARITY_REPRODUCES | audit report | `test_zero_shift.py` | Folded into cell 17's stage. |

### A.4 Sentinel-1 GRD → RTC pipeline (cells 19–24)

| Cell | Title | PRD stage | Destination | Decision | Parity | Artifact | Test | Notes |
|---|---|---|---|---|---|---|---|---|
| 19 | `SAR_CORE`: `to_grid`, `finalize_for_export` | SAR RTC | `app/pipeline/stages/sar_rtc.py` | reproduce | PARITY_REPRODUCES | n/a | unit | |
| 20 | MASTER-MATCHED QA, orbit/track selection | SAR RTC | `app/pipeline/stages/sar_rtc.py` | reproduce | PARITY_REPRODUCES | selection JSON | `test_sar_parity.py` | |
| 21 | VV_dB, VH_dB, incidence — no Copernicus-DEM in GEE | SAR RTC | `app/pipeline/stages/sar_rtc.py` | reproduce | PARITY_REPRODUCES | VV/VH dB tifs | `test_sar_parity.py` | |
| 22 | `ee.Authenticate()` fallback | n/a | `app/services/ee_session.py` | replace | PARITY_REPLACES | n/a | `test_ee_session.py` | C5 forbids `ee.Authenticate()`. |
| 23 | Grid helpers, dB-safe | SAR RTC | `app/pipeline/stages/sar_rtc.py` | reproduce | PARITY_REPRODUCES | n/a | unit | |
| 24 | Master S1 cell (FINAL vRUN) | SAR RTC | `app/pipeline/stages/sar_rtc.py` | reproduce | PARITY_REPRODUCES | full SAR stack | `test_sar_parity.py` | The authoritative SAR cell among many variants. |

### A.5 Drive-export waits, pixel-alignment QA (cells 25–35)

| Cell | Title | PRD stage | Destination | Decision | Parity | Artifact | Test | Notes |
|---|---|---|---|---|---|---|---|---|
| 25 | Drive-export wait loop | n/a | [discard] | discard | — | n/a | n/a | Colab-specific. |
| 26 | Per-band stats / nodata audit | Alignment QA | `app/pipeline/stages/alignment_qa.py` | reproduce | PARITY_REPRODUCES | audit report | unit | |
| 27 | Pixel-center alignment test | Alignment QA | `app/pipeline/stages/alignment_qa.py` | reproduce | PARITY_REPRODUCES | alignment_qa.json | `test_alignment.py` | |
| 28 | Rebuild `logRatio_dB` if missing | SAR RTC | `app/pipeline/stages/sar_rtc.py` | reproduce | PARITY_REPRODUCES | logRatio tif | `test_sar_parity.py` | Becomes unconditional in app. |
| 29 | Edge-consistency test | Alignment QA | `app/pipeline/stages/alignment_qa.py` | reproduce | PARITY_REPRODUCES | edge report | `test_alignment.py` | |
| 30, 31 | Guard cells | n/a | `app/pipeline/orchestrator.py` | replace | PARITY_REPLACES | n/a | unit | Guard logic moves into stage protocol. |
| 32 | `!ls` shell debug | n/a | [discard] | discard | — | n/a | n/a | |
| 33 | Stack NPY → per-band TIFFs | SAR RTC | `app/pipeline/stages/sar_rtc.py` | reproduce | PARITY_REPRODUCES | per-band TIFs | `test_sar_parity.py` | |
| 34, 35 | Georef + guard checks | n/a | `app/pipeline/orchestrator.py` | replace | PARITY_REPLACES | n/a | unit | |

### A.6 Feature / index stacks (cells 36–55)

| Cell | Title | PRD stage | Destination | Decision | Parity | Artifact | Test | Notes |
|---|---|---|---|---|---|---|---|---|
| 36–45 | "Nano / Treasure / Geophysics" stacks | n/a | [defer-v2] | defer | — | n/a | n/a | Many duplicate variants of similar features; not part of cheat-sheet's defensible set. |
| 46 | Arabic comment | n/a | [discard] | discard | — | n/a | n/a | Single-line note, no code. |
| 47–54 | Various refined/sigma/gphys/ULTIMATE stacks | n/a | [defer-v2] | defer | — | n/a | n/a | Same as 36–45. Consolidate selectively in v2. |
| 55 | Empty | n/a | [discard] | discard | — | n/a | n/a | |

*Rationale: most of these cells are duplicate variants of features that better belong consolidated. v1 ports only the canonical S2 indices via the operator's cheat sheet (cells 81, 83 plus the formulas).*

### A.7 Hypercube, PCA, object extraction (cells 56–71)

| Cell | Title | PRD stage | Destination | Decision | Parity | Artifact | Test | Notes |
|---|---|---|---|---|---|---|---|---|
| 56 | Arch intel physics features | n/a | [defer-v2] | defer | — | n/a | n/a | |
| 57 | GOLDEN AUDITOR 640 | Alignment QA | `app/pipeline/stages/alignment_qa.py` | reproduce | PARITY_REPRODUCES | audit CSV | `test_alignment.py` | |
| 58 | HYPERCUBE SCI 640 | Hypercube assembly | `app/pipeline/stages/hypercube.py` | reproduce | PARITY_REPRODUCES | hypercube.tif/.npy | `test_hypercube_parity.py` | |
| 59 | HCUBE quick check | Hypercube assembly | `app/pipeline/stages/hypercube.py` (assert) | reproduce | PARITY_REPRODUCES | n/a | unit | Sanity assertion. |
| 60–65 | Aux geophys / metal / SAR arch indices | n/a | [defer-v2] | defer | — | n/a | n/a | Variant proliferation; not in defensible set. |
| 66 | PCA ANOMALY TARGET MAP 640 | PCA anomaly | `app/pipeline/stages/pca_anomaly.py` | reproduce | PARITY_REPRODUCES | pca_anomaly.tif | `test_pca_parity.py` | |
| 67 | Duplicate of 66 | n/a | [discard] | discard | — | n/a | n/a | |
| 68 | PCA candidate labels → objects_index.csv | Object extraction | `app/pipeline/stages/object_extract.py` | reproduce | PARITY_REPRODUCES | objects_index.csv | `test_objects_parity.py` | |
| 69 | AI object classify + cluster summary (DBSCAN) | Object extraction | `app/pipeline/stages/object_extract.py` | reproduce | PARITY_REPRODUCES | clusters_summary.csv | `test_objects_parity.py` | DBSCAN over the object table. |
| 70 | AI context export + tagging | Object extraction | `app/pipeline/stages/object_extract.py` | reproduce | PARITY_REPRODUCES | per-object NPY patches | `test_objects_parity.py` | |
| 71 | Watershed / regionprops auto-extraction | Object extraction | `app/pipeline/stages/object_extract.py` | reproduce | PARITY_REPRODUCES | proposals + mask | `test_objects_parity.py` | |

### A.8 Tensor exports, alignment QA (cells 72–79)

| Cell | Title | PRD stage | Destination | Decision | Parity | Artifact | Test | Notes |
|---|---|---|---|---|---|---|---|---|
| 72, 73 | Bonus / simulator features | n/a | [defer-v2] | defer | — | n/a | n/a | |
| 74 | AI-ready tensor export (robust-normalize) | Hypercube assembly | `app/pipeline/stages/hypercube.py` (option) | reproduce | PARITY_REPRODUCES | normalized stack | `test_hypercube_parity.py` | Option flag on the hypercube stage. |
| 75 | Duplicate of 74 | n/a | [discard] | discard | — | n/a | n/a | |
| 76, 77 | S2 era pulls (2022–2026, cloud<3) | S2 spectral indices | `app/pipeline/stages/s2_indices.py` | reproduce | PARITY_REPRODUCES | S2 composites | `test_s2_parity.py` | |
| 78 | Drive/Colab twin pixel-match QA | n/a | [discard] | discard | — | n/a | n/a | Colab-specific path comparison. |
| 79 | Full TIF alignment QA (≤ 0.25 px) | Alignment QA | `app/pipeline/stages/alignment_qa.py` | reproduce | PARITY_REPRODUCES | alignment_qa.json | `test_alignment.py` | |

### A.9 Stragglers + DEM-matched S2 masks (cells 80–103)

| Cell | Title | PRD stage | Destination | Decision | Parity | Artifact | Test | Notes |
|---|---|---|---|---|---|---|---|---|
| 80 | Tiny inspector | n/a | [discard] | discard | — | n/a | n/a | |
| 81 | DEM-matched S2 (cloud<3) | S2 spectral indices | `app/pipeline/stages/s2_indices.py` | reproduce | PARITY_REPRODUCES | S2 masked composite | `test_s2_parity.py` | |
| 82 | Master-ref tif sanity | n/a | [discard] | discard | — | n/a | n/a | |
| 83 | S2 collection rebuild (grid lock variant) | S2 spectral indices | `app/pipeline/stages/s2_indices.py` | reproduce | PARITY_REPRODUCES | n/a | unit | Folded into the canonical S2 stage. |
| 84 | Master-grid audit | Alignment QA | `app/pipeline/stages/alignment_qa.py` | reproduce | PARITY_REPRODUCES | audit CSV | `test_alignment.py` | |
| 85 | EE export task cancel | n/a | [discard] | discard | — | n/a | n/a | Colab-specific. |
| 86 | Drive refresh hack | n/a | [discard] | discard | — | n/a | n/a | |
| 87–94 | Path verification / DEM-anchored checks / Tesla v7.2 protocols | n/a | [discard] | discard | — | n/a | n/a | Consolidated into alignment_qa stage. |
| 95–103 | "Tesla v7.2 Atomic Inference / Fusion Center" | Experimental classifier | `app/pipeline/stages_experimental/classifier.py` | reproduce-neutralized | EXPERIMENTAL_CONTRACT | neutral class scores / reports | `test_experimental_cli.py` | Port only the decision logic required by the classifier; source labels become `Class_A` … `Class_N`. |

### A.10 DEM_GEO8 + thermal + Zero-Point report + focus mask (cells 104–119)

| Cell | Title | PRD stage | Destination | Decision | Parity | Artifact | Test | Notes |
|---|---|---|---|---|---|---|---|---|
| 104 | DEM_GEO8_TIFS (slope, aspect, curvature, TPI, TRI, roughness, TWI) | DEM derivatives | `app/pipeline/stages/dem_derivatives.py` | reproduce | PARITY_REPRODUCES | 7 DEM derivative TIFs | `test_dem_derivatives_parity.py` | |
| 105, 106 | Landsat 9 TOA aligned to DEM grid | Thermal LST | `app/pipeline/stages/thermal.py` | reproduce | PARITY_REPRODUCES | n/a | unit | |
| 107 | Duplicate of 104 | n/a | [discard] | discard | — | n/a | n/a | |
| 108 | S1 GRD re-pull | n/a | [discard] | discard | — | n/a | n/a | Consolidated into sar_rtc. |
| 109 | Open DEM + write derivatives | DEM derivatives | `app/pipeline/stages/dem_derivatives.py` | reproduce | PARITY_REPRODUCES | n/a | unit | |
| 110 | Drive file locator | n/a | [discard] | discard | — | n/a | n/a | |
| 111 | Debug zero-point report | n/a | [discard] | discard | — | n/a | n/a | |
| 112 | DEM-source derived layers | DEM derivatives | `app/pipeline/stages/dem_derivatives.py` | reproduce | PARITY_REPRODUCES | n/a | unit | |
| 113 | S1 mask inspector (best anchor) | Alignment QA | `app/pipeline/stages/alignment_qa.py` | reproduce | PARITY_REPRODUCES | mask selection JSON | unit | |
| 114, 115, 116, 117 | Hypercube-anchored derived rasters / guards | Hypercube assembly | `app/pipeline/stages/hypercube.py` | reproduce | PARITY_REPRODUCES | n/a | unit | |
| 118 | FOCUS_MASK validation | Experimental classifier | `app/pipeline/stages_experimental/classifier.py` | reproduce-neutralized | EXPERIMENTAL_CONTRACT | focus mask metadata | `test_experimental_cli.py` | Local post-processing only; outputs Class IV. |
| 119 | ROI-constrained 17 m FOCUS | Experimental classifier | `app/pipeline/stages_experimental/classifier.py` | reproduce-neutralized | EXPERIMENTAL_CONTRACT | focus-region report | `test_experimental_cli.py` | Neutralized; no API/frontend exposure. |

### A.11 Tesla v7.2 hard classifiers (cells 120–135)

| Cell | Title | PRD stage | Destination | Decision | Parity | Artifact | Test | Notes |
|---|---|---|---|---|---|---|---|---|
| 120 | `display(top_df)` | n/a | [discard] | discard | — | n/a | n/a | One-liner debug. |
| 121–135 | CORE-9 / FOCUS-17M / hard target classifier / multi-target subpixel centering | Experimental classifier | `app/pipeline/stages_experimental/classifier.py`, `classes.py` | reproduce-neutralized | EXPERIMENTAL_CONTRACT | neutral class table / Class IV outputs | `test_experimental_cli.py`, `test_experimental_neutral_terms.py` | v1 includes logic with neutral class IDs only. |

### A.12 Outputs sanity + KMZ generation (cells 136–162)

| Cell | Title | PRD stage | Destination | Decision | Parity | Artifact | Test | Notes |
|---|---|---|---|---|---|---|---|---|
| 136, 137 | `os.listdir` debug | n/a | [discard] | discard | — | n/a | n/a | |
| 138 | Markdown header | n/a | [discard] | discard | — | n/a | n/a | |
| 139 | KMZ generation (heatmap + 3D targets) | Experimental classifier | `app/pipeline/stages_experimental/outputs.py` | reproduce-neutralized | EXPERIMENTAL_CONTRACT | KMZ/KML Class IV files | `test_experimental_cli.py` | Filesystem-only under `experimental/`; never HTTP-served. |
| 140 | AI Requirements Mapper | n/a | [discard] | discard | — | n/a | n/a | Notebook-only meta cell. |
| 141 | RUN layer inventory + 17M mask rebuild | Experimental classifier | `app/pipeline/stages_experimental/classifier.py` | reproduce-neutralized | EXPERIMENTAL_CONTRACT | inventory / mask metadata | `test_experimental_cli.py` | Consumes completed RUN artifacts only. |
| 142, 143 | Amer update / thermal-anomaly inspection | n/a | [discard] | discard | — | n/a | n/a | |
| 144 | Empty | n/a | [discard] | discard | — | n/a | n/a | |
| 145 | Landsat day LST builder | Thermal LST | `app/pipeline/stages/thermal.py` | reproduce | PARITY_REPRODUCES | lst.tif | `test_thermal_parity.py` | |
| 146 | Thermal anomaly variant | n/a | [discard] | discard | — | n/a | n/a | Consolidate into cell-145 stage. |
| 147 | Tensor builder | Hypercube assembly | `app/pipeline/stages/hypercube.py` | reproduce | PARITY_REPRODUCES | n/a | unit | |
| 148 | YOLO/CNN/Swin tensor builder | n/a | [defer-v2] | defer | — | n/a | n/a | Model-training / segmentation experiments remain outside v1 unless needed for the selected rule-based classifier contract. |
| 149 | Detection-result GeoJSON | Experimental classifier | `app/pipeline/stages_experimental/outputs.py` | reproduce-neutralized | EXPERIMENTAL_CONTRACT | GeoJSON Class IV file | `test_experimental_cli.py` | Filesystem-only; exact coordinates never HTTP-served. |
| 150–162 | AI library installs / KMZ variants / simplekml / target-only KMZs | Experimental classifier / optional deps | `pyproject.toml`, `app/pipeline/stages_experimental/outputs.py` | reproduce-neutralized where needed | EXPERIMENTAL_CONTRACT | Class IV local exports | `test_experimental_cli.py` | Only export logic required by the classifier is ported; heavyweight ML deps remain optional. |

### A.13 Training, inference, CNN, GPS comparison (cells 163–243)

| Cell | Title | PRD stage | Destination | Decision | Parity | Artifact | Test | Notes |
|---|---|---|---|---|---|---|---|---|
| 163–178 | Training scaffolding / inference engine class / object detector | Experimental classifier | `app/pipeline/stages_experimental/classifier.py` or [defer-v2] | selective reproduce-neutralized | EXPERIMENTAL_CONTRACT / — | neutral classifier outputs | `test_experimental_cli.py` | Port only runtime inference/decision logic needed for v1; training scaffolding remains deferred. |
| 179–202 | Various classifier iterations / metal fingerprint / strategic scanner / field-mapping | Experimental classifier | `app/pipeline/stages_experimental/classifier.py`, `outputs.py` | selective reproduce-neutralized | EXPERIMENTAL_CONTRACT | neutral class reports / Class IV maps | `test_experimental_cli.py` | Consolidate the final selected classifier path; duplicate/obsolete variants documented but not all ported. |
| 203–215 | Drive scans / era pulls / radar pulls / numpy I/O | n/a | [discard] | discard | — | n/a | n/a | Consolidated into stages. |
| 216–230 | Reference-tif utilities / GPS-point comparison | n/a | [discard] | discard | — | n/a | n/a | |
| 231 | RGB-like 3-layer stack | Hypercube assembly | `app/pipeline/stages/hypercube.py` (export) | reproduce | PARITY_REPRODUCES | n/a | unit | |
| 232 | smp.UnetPlusPlus Swin-Base attempt | n/a | [defer-v2] | defer | — | n/a | n/a | Heavy segmentation model attempt remains out of v1 unless explicitly selected later by ADR. |
| 233 | Broken `class ArcheoAI_Leader` (`def init`) | n/a | [discard] | discard | — | n/a | n/a | Confirmed bug: missing `__init__` dunders; class never constructs. |
| 234 | Incidence-angle correction | SAR RTC | `app/pipeline/stages/sar_rtc.py` | reproduce | PARITY_REPRODUCES | n/a | unit | Folded into cell-24 stage. |
| 235–243 | Final model, dictionary, KMZ field map, trace, live map overlay | Experimental classifier | `app/pipeline/stages_experimental/classifier.py`, `classes.py`, `outputs.py` | reproduce-neutralized | EXPERIMENTAL_CONTRACT | neutral class outputs / Class IV KMZ | `test_experimental_cli.py` | Notebook labels neutralized before code entry; no live map overlay in app. |
| 244 | Markdown stub | n/a | [discard] | discard | — | n/a | n/a | |

### A.14 Migration matrix summary

| Category | Cell count |
|---|---|
| `reproduce` (PARITY_REPRODUCES) | 35 |
| `correct` (PARITY_CORRECTS, IRON_SWIR only) | 1 |
| `replace` (PARITY_REPLACES, no notebook equivalent / Colab-specific) | 9 |
| `experimental_contract` (v1 neutralized classifier surface) | ~55 |
| `defer` (v2 or later ML/training/unused experimental variants) | ~20 |
| `discard` (duplicates, dead code, debug, bugs) | ~125 |
| **Total** | **245** |

The defensible v1 surface is approximately 45 cells' worth of work consolidated into 11 core stage files plus supporting services. v1 also includes a neutralized, CLI-only experimental classifier surface consolidated from the selected classifier cells. Remaining duplicate, training-only, broken, Colab-specific, or obsolete cells are deferred or discarded.

---

## Document control

This PRD is a living document, but changes to §3 (Non-Goals), §5 (Safety Constants), §6.2 (Experimental Module), §8 (Out of Scope), §13 (Redaction Contract), §14 (Artifact Taxonomy), §15 (Parity Categories), §16 (Threat Model), §17 (Implementation Milestones), and §11 (Risks) require a written ADR (Architecture Decision Record) and explicit re-authorization per the operator's project discipline. Other sections, and the migration matrix in Appendix A, may be amended freely as implementation proceeds.

End of PRD v0.5.
