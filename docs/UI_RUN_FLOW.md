# UI Run Flow

## Purpose

This document defines the intended real operator run flow before further UI implementation.

The current blank pin workspace is not the authoritative AOI picker. A production run must start from explicit target coordinates entered by the operator.

## Primary Target Input

The primary run input is a form with:

- latitude
- longitude
- optional run name

Validation rules:

- the queue button stays disabled until latitude and longitude are valid
- latitude must be in the range `-90` to `90`
- longitude must be in the range `-180` to `180`
- optional run name remains public text and must pass the existing run-name safety rules

Map rules:

- no external map tiles are introduced yet
- the fake or blank map is not the authoritative AOI picker
- any later map interaction must write into the explicit latitude and longitude fields before it can queue a run

## Run Creation

When the operator queues a run:

- the UI sends `POST /runs` with `lat`, `lon`, and `name`
- the backend stores coordinates internally
- public API responses do not expose coordinates
- public UI history and status views must not show coordinates

## Backend Execution Flow

The backend execution flow is:

- create the run record
- build the production GRID with `build_run_grid(lat, lon)`
- save the internal grid manifest
- run pipeline stages
- update the run status as work advances or fails

Production GRID remains app-authoritative. Notebook-exact GRID remains validation/replay-only.

## Safe Run Statuses

The public UI may display these run statuses:

- `queued`
- `running`
- `done`
- `failed`
- `stale_failed`
- `cancelled`

## Pipeline Step Progress Design

The public progress model should use safe stage names only. It must not expose coordinates, bounds, transforms, local paths, notebook paths, internal GRID override controls, or stack traces.

Safe stage names:

- GRID setup
- DEM
- Zero shift
- SAR RTC
- Sentinel-2 indices
- DEM derivatives
- Thermal
- Feature stacks
- Focus mask
- Location exports
- Field ops exports
- GPS comparison
- Hypercube
- PCA anomaly
- Object extraction
- Alignment QA

Safe stage statuses:

- `pending`
- `running`
- `done`
- `failed`
- `skipped`

## UI Progress Display

The UI should show:

- overall run status
- current stage
- stage checklist
- public-safe failed state when a run fails

Polling behavior:

- poll `GET /runs/{run_id}` every 2 seconds while the run is active
- active statuses are `queued` and `running`
- stop polling on terminal state
- terminal states are `done`, `failed`, `stale_failed`, and `cancelled`

## Artifacts

Artifact display rules:

- show artifacts only after the run is `done`
- show only public-safe artifacts returned by the API
- downloads use `/runs/{run_id}/artifacts/{artifact_name}`
- `FILESYSTEM_ONLY` artifacts never render
- experimental outputs never render

## Run History and Lookup

Run history and lookup should show only public-safe fields:

- `run_id`
- `name`
- `status`
- `created_at`

Rules:

- do not show coordinates
- load a selected run with `GET /runs/{run_id}`
- resume polling if the selected run is active
- show artifacts if the selected run is `done`
- show a public-safe failed state if the selected run failed

## Non-Goals

- no SAR math change
- no GRID behavior change
- no notebook code change
- no tolerance change
- no reference manifest change
- no notebook-exact GRID control in public UI
- no fresh-ROI notebook parity claim
- no external map tiles yet

## Implementation Goals

Goal A: backend stage progress model/API

- add a public-safe stage progress representation
- use only the safe stage names and statuses defined here
- keep coordinates, transforms, local paths, and internal controls out of public DTOs

Goal B: UI target input and progress rendering

- replace the authoritative blank-map input with validated latitude and longitude fields
- keep optional run name support
- render overall status, current stage, and stage checklist
- keep recent-run history, lookup, artifact loading, and guarded downloads

Goal C: final browser smoke test and fixes

- run the local UI smoke test against the implemented flow
- verify create-run, status polling, lookup/history, progress display, artifacts, and guarded downloads
- verify public surfaces do not leak restricted fields
- make only narrow fixes found by the smoke test
