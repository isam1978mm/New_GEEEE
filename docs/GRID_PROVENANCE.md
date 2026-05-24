# GRID Provenance Decision

This document records the GRID provenance decision after the notebook-grid validation baseline closed F11/F24 parity.

## Decision

**Option B: keep production `build_run_grid()` app-authoritative.**

Notebook-exact GRID remains a local validation and replay path only. Production `/runs` continues to construct the app GRID from the submitted run coordinates through `app.services.grid.build_grid_manifest()`.

## Current Production Behavior

- Public run creation accepts only the public run request fields defined by `RunCreate`.
- `POST /runs` stores internal coordinates and immediately writes `grid_manifest.json` using `build_run_grid()`.
- Normal pipeline execution currently recomputes `build_run_grid()` from the stored internal coordinates unless an internal `grid_spec_override` is explicitly supplied.
- The stored `grid_manifest.json` is an internal artifact, but it is not yet the source used to replay normal runs.

## Notebook GRID Behavior

Notebook Cell 14 uses GRID values derived from prior notebook state:

- `NewRoi6KM` must already exist.
- `SelectedPoint` must already exist.
- The notebook uses Earth Engine geometry operations and `getInfo()` to obtain the authoritative ROI bounds.
- The notebook writes path-bearing runtime metadata as part of the same setup flow.

Therefore Cell 14 is **Notebook-state-dependent**, not pure deterministic local Python. It is not safe to adopt directly into production `build_run_grid()` without a separate GRID convention/version design.

## Notebook-Exact Validation Override

The local validation path reads notebook `QA_RADAR_META*.json` and constructs a `GridSpec` from:

- CRS
- SCALE
- OUT_SIZE
- NODATA
- `crsTransform`
- `bounds_utm`

That override is internal-only and local-only. It is not exposed through public API requests or public DTOs.

## Accepted Validation Baseline

The accepted notebook-grid validation baseline proves output parity when the app uses the notebook-exact GRID:

- F24 post-RTC SAR: MATCH 100%.
- F11 SAR NPY bands: PASS 100%.
- F11 DEM, SAR GeoTIFF, radar DB stack, selected DEM derivatives, and focus mask rows: PASS where notebook counterparts exist.
- Current F11 baseline has no FAIL rows.

## Sanitized GRID Comparison

For the accepted validation run, app-authoritative GRID from `build_run_grid()` compared to frozen notebook metadata shows:

- CRS equality: true, EPSG 32637.
- SCALE equality: true, value 10.
- OUT_SIZE equality: true, value 640.
- NODATA equality: true, value -9999.0.
- Transform equality: false.
- Bounds equality: false.
- Origin delta in pixel offsets: `dx=0.026556`, `dy=0.022979`.

No raw coordinates, raw projected coordinates, raw bounds, or raw transform values are included here.

## Replay And Versioning Risk

Changing production `build_run_grid()` retroactively would create a GRID convention change. Existing runs under `data/runs/*` were generated with the old app-authoritative convention. If the code changes without replay protection:

- Existing runs may no longer be reproducible from their stored run coordinates.
- Historical parity reports may silently shift because recomputed GRID differs from the original run GRID.
- Existing accepted baselines would describe an older convention while current code would produce a new convention.

The current replay behavior is not sufficient for a production GRID convention change because normal pipeline execution recomputes GRID from stored internal coordinates instead of loading the stored run `grid_manifest.json`.

## Recommended Path

Keep Option B now. Before revisiting Option A, implement explicit GRID convention versioning and replay protection:

- Store a GRID convention version in `grid_manifest.json`.
- Persist the convention version in run/stage metadata.
- Make pipeline replay load the stored `grid_manifest.json` for existing runs rather than recomputing GRID from coordinates.
- Gate any new notebook-exact production convention behind an explicit version, for example `app-grid-v1` versus `notebook-cell14-grid-v1`.
- Add tests proving old runs replay with their original stored GRID after the default convention changes.
- Only after that design exists should a normal no-override validation run be used to consider changing production GRID behavior.

## Scope Wording

Production GRID remains app-authoritative for new `/runs`. Notebook-exact GRID is accepted only as a local validation/replay mechanism for parity investigations and does not change public API behavior, SAR science logic, pair selection, selected image IDs, tolerances, or notebook code.
