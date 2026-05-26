# Notebook ↔ App Output Match Plan

## Decision

This project is now targeting a private/operator app workflow.

The app must match the notebook output set. The UI should expose the full run output set for the operator, not only a small public-safe subset.

Secrets and environment internals remain protected. The app must still not expose or serve:

- `.env`
- service-account JSON keys
- credentials or tokens
- raw stack traces
- server logs with secrets
- local path-map files
- unrelated local machine files
- reference bundles unless explicitly selected by the operator

## Current Situation

The notebook produces a concrete output tree with final raster/report deliverables, radar bands, DEM products, stacks, QA files, and a run manifest.

The current app has proven it can run end-to-end and currently shows/downloads a small operator-facing subset in the UI:

- `objects_index.csv`
- `clusters_summary.csv`
- `alignment_qa.json`
- `alignment_audit.json`
- `alignment_mask_selection.json`

This is not enough for the new target. The app local output tree and UI downloads must be brought into full notebook-output alignment.

## Notebook Output Tree to Match

The notebook reference output shape includes outputs like the following:

```text
<notebook_reference_output>/
├── DEM_GEO8_TIFS/
│   ├── DEM_640.tif
│   ├── roughness_100m_640.tif
│   ├── slope_deg_640.tif
│   └── tpi_100m_640.tif
├── GEOTIFF_RADAR_BANDS/
│   ├── RADAR_angle_640_*.tif
│   ├── RADAR_logRatio_dB_640_*.tif
│   ├── RADAR_VH_dB_640_*.tif
│   └── RADAR_VV_dB_640_*.tif
├── NPY_RADAR_BANDS/
│   ├── RADAR_angle_640_*.npy
│   ├── RADAR_logRatio_dB_640_*.npy
│   ├── RADAR_VH_dB_640_*.npy
│   └── RADAR_VV_dB_640_*.npy
├── NPY_STACKS/
│   ├── FINAL_TESLA_V7_2_HYPERCUBE.tif
│   ├── FINAL_TESLA_V7_2_HYPERCUBE_PATCHED_14B.tif
│   └── RADAR_STACK_HWC_640_*.npy
├── QA/
│   ├── FOCUS_MASK_17m_inside_640.tif
│   └── SUMMARY_RADAR_*.csv
├── REPORT_640_Pottery_Report.tif
├── REPORT_640_Mass_Report.tif
├── REPORT_640_FINAL_Zero_Point_Targets.tif
└── RUN_MANIFEST.json
```

The exact local reference folder should be supplied through local operator configuration or ignored local path maps. Do not commit local absolute paths or reference bundles.

## Definition of Full Match

A full app/notebook output match means:

1. Required notebook output files or filename patterns exist in the app run output folder.
2. Folder structure matches the notebook structure unless a documented equivalent name is approved.
3. Raster metadata matches where applicable:
   - dimensions
   - CRS
   - transform/grid
   - dtype
   - band count
   - nodata policy
4. Numeric raster/array values match within existing accepted tolerances where byte identity is not possible.
5. CSV and JSON outputs match required schema.
6. `RUN_MANIFEST.json` records the expected output inventory.
7. The UI can browse and download the full operator output set with correct filenames and extensions.

## Planned Goals

### Goal A — Actual output inventory comparison

Create a factual comparison between the actual notebook reference output folder and an actual successful app run folder.

Inputs:

```text
Notebook: <local notebook reference output folder>
App: data/runs/<successful_app_run_id>/
```

Deliverable:

```text
docs/NOTEBOOK_VS_APP_OUTPUTS.md
```

The comparison table must include:

| Notebook file | Notebook path | App equivalent path | Status | UI-visible | Notes |
|---|---|---|---|---|---|

Allowed statuses:

- `matched`
- `renamed-equivalent`
- `missing-in-app`
- `app-only`
- `notebook-only`
- `needs-content-parity-check`
- `intentionally-different`

Goal A must answer:

- Does the app produce the three `REPORT_640_*.tif` outputs?
- Does the app produce `DEM_GEO8_TIFS/`?
- Does the app produce `GEOTIFF_RADAR_BANDS/`?
- Does the app produce `NPY_RADAR_BANDS/`?
- Does the app produce `NPY_STACKS/`?
- Does the app produce `QA/` outputs?
- Which app outputs are renamed equivalents?
- Which notebook outputs are missing in the app?
- Which app outputs are extra app-only outputs?

No production code changes in Goal A.

### Goal B — Define the notebook-output app contract

Turn the inventory comparison into a formal app output contract.

Deliverable:

```text
docs/APP_NOTEBOOK_OUTPUT_CONTRACT.md
```

The contract must define:

- required folders
- required files and filename patterns
- required raster metadata checks
- required NPY checks
- required CSV/JSON schemas
- required manifest entries
- UI download expectations
- allowed app-only extra outputs
- allowed renamed-equivalent outputs, if any

No science logic changes in Goal B.

### Goal C — Implement missing local app outputs

Make the app write notebook-equivalent outputs into the app run folder.

Likely implementation areas:

- DEM stage
- SAR RTC stage
- DEM derivatives stage
- zero shift / focus mask stage
- hypercube / stack stage
- QA/report stage
- object/report generation stage
- run manifest writer
- artifact registration

Expected local app tree:

```text
data/runs/<run_id>/
├── DEM_GEO8_TIFS/
├── GEOTIFF_RADAR_BANDS/
├── NPY_RADAR_BANDS/
├── NPY_STACKS/
├── QA/
├── REPORT_640_Pottery_Report.tif
├── REPORT_640_Mass_Report.tif
├── REPORT_640_FINAL_Zero_Point_Targets.tif
└── RUN_MANIFEST.json
```

Do not remove useful existing app outputs unless there is a deliberate migration decision.

### Goal D — Register full output inventory for downloads

Because this is a private/operator app, register the full run output set as downloadable operator artifacts.

The UI should browse outputs by group:

- Reports
- DEM GeoTIFFs
- Radar GeoTIFFs
- Radar NPY bands
- Stacks / Hypercube
- QA
- Object extraction
- Manifest
- App-only extras

Each downloadable item should show:

- filename
- relative output group
- file type
- size if available
- download button

Download URLs must preserve real filenames and extensions.

Still do not serve secrets, `.env`, keys, database files, local path maps, or server logs with sensitive content.

### Goal E — Add output parity tests

Add tests that prevent drift from the notebook output contract.

Test levels:

1. Inventory test: every required notebook output or pattern exists in app output.
2. Raster metadata test: dimensions, CRS, transform, dtype, band count, and nodata match.
3. Numeric parity test: raster/array values match within existing accepted tolerances.
4. CSV/JSON schema test: required columns/keys exist.
5. Manifest test: `RUN_MANIFEST.json` records expected outputs.
6. UI artifact test: full operator output tree is visible/downloadable.

These tests should be separate from public-surface UI tests.

### Goal F — Final full-run verification

Run one operator proof run from the UI and verify output match.

Required verification:

- run state is `Done`
- all stages are `done`
- app output tree matches the notebook output contract
- UI shows full output tree
- these files download correctly:
  - `REPORT_640_Pottery_Report.tif`
  - `REPORT_640_Mass_Report.tif`
  - `REPORT_640_FINAL_Zero_Point_Targets.tif`
  - `objects_index.csv`
  - `RUN_MANIFEST.json`

## Non-Goals

Do not change these unless a later approved goal explicitly requires it:

- SAR math
- GRID behavior
- notebook code
- numeric tolerances
- reference manifest behavior
- parity report behavior
- Earth Engine authentication behavior
- deployment/VPS setup

## Safety Rules

Do not commit:

- `.env`
- service-account key JSON files
- `PATH_MAP.local.json`
- `data/runs/`
- `data/reports/`
- reference bundles
- local notebooks or Colab exports unless explicitly approved
- `gee_screening_app.egg-info/`
- unrelated dirty files

Do not expose in UI/API:

- credentials
- service-account key contents
- raw stack traces
- local absolute paths outside the run-output browsing contract
- database files
- server logs containing secrets

## Next Immediate Goal

Start with Goal A only.

Suggested prompt:

```text
/goal Compare actual notebook output folder against actual successful app run folder. Do not change code.

Create docs/NOTEBOOK_VS_APP_OUTPUTS.md with a file-by-file comparison between:

Notebook:
<local notebook reference output folder>

App:
data/runs/<successful_app_run_id>/

For each notebook file, identify:
- app equivalent path if present
- status: matched, renamed-equivalent, missing-in-app, app-only, notebook-only, needs-content-parity-check, intentionally-different
- UI-visible yes/no
- notes

Also list app-only outputs.

Do not change pipeline, UI, tests, SAR math, GRID behavior, notebook code, tolerances, parity report behavior, or reference manifest behavior.

Return:
1. Files inspected
2. Files changed
3. Summary counts
4. Missing notebook outputs in app
5. App-only outputs
6. Renamed/equivalent outputs
7. Recommended implementation phases
8. Any blocker
```
