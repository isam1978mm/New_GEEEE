# App Notebook Output Contract

## Purpose

This document defines the required app output contract for notebook-output matching in the private/operator app workflow.

It is a contract only. It does not implement any pipeline, UI, test, or artifact changes.

It is based on:

- `docs/NOTEBOOK_APP_OUTPUT_MATCH_PLAN.md`
- `docs/NOTEBOOK_VS_APP_OUTPUTS.md`

Absolute local paths are intentionally omitted. The operator-local notebook reference bundle is referred to only as `<notebook_reference_output>/`.

## Decision

The project target is full notebook-output match for operator use.

That means:

- the app local run tree must produce the notebook-required output families
- the app may keep useful extra outputs
- renamed-equivalent outputs are acceptable only where this contract explicitly allows them
- renamed-equivalent outputs still require metadata and content parity proof
- later UI work must expose the full operator output tree, not only a small public-safe subset

This contract does not change:

- SAR math
- GRID behavior
- notebook code
- numeric tolerances
- parity report behavior
- reference manifest behavior
- artifact generation logic already in place

## Baseline

Phase 1 used:

- fresh app run ID: `da0dca61-bc35-43c2-af91-351f3fbda942`
- notebook reference inventory: `144` files, `18` directories
- app run inventory: `2441` files, `19` directories

Phase 1 showed:

- missing notebook outputs that must be implemented
- renamed-equivalent outputs that need content parity proof
- app-only outputs that should be preserved
- a few intentionally different outputs that need an explicit policy

## Required App Output Tree

The target local app tree must support this notebook-compatible structure:

```text
data/runs/<run_id>/
├── REPORT_640_Pottery_Report.tif
├── REPORT_640_Mass_Report.tif
├── REPORT_640_FINAL_Zero_Point_Targets.tif
├── DEM_GEO8_TIFS/
├── GEOTIFF_RADAR_BANDS/
├── NPY_RADAR_BANDS/
├── NPY_STACKS/
├── QA/
│   ├── RUN_MANIFEST.json
│   └── sar/
│       └── intermediates/
└── ... app-only extras allowed by this contract
```

The app may continue to emit additional operator-local outputs outside that notebook-compatible tree, as long as required notebook-compatible outputs are also present and parity-tested.

## Required Output Groups

### 1. Root Report GeoTIFFs

Required files:

- `REPORT_640_Pottery_Report.tif`
- `REPORT_640_Mass_Report.tif`
- `REPORT_640_FINAL_Zero_Point_Targets.tif`

Naming rule:

- exact notebook filename required
- no renamed-equivalent is acceptable for the contract target

Metadata checks:

- dimensions
- CRS
- transform/grid
- dtype
- band count
- nodata policy

Content parity checks:

- numeric raster parity within existing accepted tolerances

UI expectation later:

- yes, must be shown and downloadable in the operator UI

Phase 1 classification:

- currently `missing-in-app`
- required implementation targets

### 2. `DEM_GEO8_TIFS/`

Required files:

- `DEM_GEO8_TIFS/DEM_640.tif`
- `DEM_GEO8_TIFS/slope_deg_640.tif`
- `DEM_GEO8_TIFS/aspect_deg_640.tif`
- `DEM_GEO8_TIFS/roughness_100m_640.tif`
- `DEM_GEO8_TIFS/tpi_100m_640.tif`
- `DEM_GEO8_TIFS/hillshade_0to1_640.tif`

Curvature policy:

- notebook currently exposes:
  - `DEM_GEO8_TIFS/curv_laplacian_640.tif`
  - `DEM_GEO8_TIFS/curv_plan_640.tif`
  - `DEM_GEO8_TIFS/curv_profile_640.tif`
- Phase 1 found app `curvature.tif` only
- current contract decision: notebook curvature outputs remain notebook-side only for now and are classified as `intentionally-different`
- if later promoted into required parity targets, they must be added explicitly by contract revision

Naming rule:

- notebook-compatible names are required in the target tree
- renamed-equivalent root outputs are acceptable only as transitional evidence until notebook-compatible filenames are emitted

Transitional renamed-equivalents requiring content parity:

- `DEM_GEO8_TIFS/DEM_640.tif` -> `dem.tif`
- `DEM_GEO8_TIFS/slope_deg_640.tif` -> `slope.tif`
- `DEM_GEO8_TIFS/aspect_deg_640.tif` -> `aspect.tif`
- `DEM_GEO8_TIFS/roughness_100m_640.tif` -> `roughness.tif`
- `DEM_GEO8_TIFS/tpi_100m_640.tif` -> `TPI.tif`

Required implementation targets from Phase 1:

- `DEM_GEO8_TIFS/hillshade_0to1_640.tif`

Metadata checks:

- dimensions
- CRS
- transform/grid
- dtype
- band count
- nodata policy

Content parity checks:

- numeric raster parity within existing accepted tolerances

UI expectation later:

- yes, operator UI must show and download the DEM GeoTIFF group

### 3. `GEOTIFF_RADAR_BANDS/`

Required notebook-compatible radar GeoTIFF family:

- `GEOTIFF_RADAR_BANDS/RADAR_VV_dB_640_*.tif`
- `GEOTIFF_RADAR_BANDS/RADAR_VH_dB_640_*.tif`
- `GEOTIFF_RADAR_BANDS/RADAR_logRatio_dB_640_*.tif`
- `GEOTIFF_RADAR_BANDS/RADAR_angle_640_*.tif`

Naming rule:

- notebook-compatible family names are required in the target tree
- renamed-equivalent root outputs are acceptable only as transitional evidence until notebook-compatible filenames are emitted

Transitional renamed-equivalents requiring content parity:

- notebook SAR GeoTIFF family -> `VV_dB.tif`, `VH_dB.tif`, `logRatio_dB.tif`, `incidence.tif`

Notebook-only support rasters observed in Phase 1:

- `PAN_LS_Panchromatic_640.tif`
- `PAN_S2_Panchromatic_10m_640.tif`
- `S1_ASC_VV_Filtered_640.tif`
- `S1_ASC_VH_Filtered_640.tif`
- `S1_DESC_VV_Filtered_640.tif`
- `S1_DESC_VH_Filtered_640.tif`

Current contract decision:

- these remain outside the required match target for now
- classify as notebook-only unless later promoted by contract revision

Metadata checks:

- dimensions
- CRS
- transform/grid
- dtype
- band count
- nodata policy

Content parity checks:

- numeric raster parity within existing accepted tolerances

UI expectation later:

- yes, operator UI must show and download the radar GeoTIFF group

### 4. `NPY_RADAR_BANDS/`

Required notebook-compatible NPY family:

- `NPY_RADAR_BANDS/RADAR_VV_dB_640_*.npy`
- `NPY_RADAR_BANDS/RADAR_VH_dB_640_*.npy`
- `NPY_RADAR_BANDS/RADAR_logRatio_dB_640_*.npy`
- `NPY_RADAR_BANDS/RADAR_angle_640_*.npy`

Naming rule:

- notebook-compatible family names are required in the target tree
- renamed-equivalent app outputs are acceptable only as transitional evidence until notebook-compatible filenames are emitted

Transitional renamed-equivalents requiring content parity:

- notebook SAR NPY family -> `npy_radar_bands/VV_dB.npy`, `VH_dB.npy`, `logRatio_dB.npy`, `incidence.npy`

Notebook-only support NPYs observed in Phase 1:

- panchromatic support NPYs
- filtered S1 support NPYs

Current contract decision:

- these remain notebook-only for now unless later promoted

Checks:

- shape
- dtype
- value parity within existing accepted tolerances

UI expectation later:

- yes, operator UI must show and download the radar NPY group

### 5. `NPY_STACKS/`

Required notebook-compatible stack outputs:

- `NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE.npy`
- `NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE.tif`
- `NPY_STACKS/RADAR_STACK_HWC_640_*.npy`

Naming rule:

- notebook-compatible names are required in the target tree
- renamed-equivalent app outputs are acceptable only as transitional evidence until notebook-compatible names are emitted

Transitional renamed-equivalents requiring content parity:

- `NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE.npy` -> `hypercube.npy`
- `NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE.tif` -> `hypercube.tif`
- `NPY_STACKS/RADAR_STACK_HWC_640_*.npy` -> `stacks/tensor_support/radar_linear_support_stack.npy`

Notebook-only stack files observed in Phase 1:

- `FINAL_TESLA_V7_2_HYPERCUBE_PATCHED_14B.tif`
- `FINAL_TESLA_V7_2_HYPERCUBE_RES_2p5M.npy`
- `FINAL_TESLA_V7_2_HYPERCUBE_RES_2p5M.tif`
- `PAN_LAYERS_STACK_640.npy`
- `S1_FILTERED_LAYERS_STACK_640.npy`

Current contract decision:

- these remain notebook-only for now unless later promoted

Checks:

- raster metadata checks for TIFFs
- NPY shape/dtype/value parity

UI expectation later:

- yes, operator UI must show and download stack outputs

### 6. `QA/`

Required notebook-compatible QA outputs:

- `QA/FOCUS_MASK_17m_inside_640.tif`
- `QA/SUMMARY_RADAR_*.csv`
- `QA/QA_GRID_dx_m_640.tif`
- `QA/QA_GRID_dy_m_640.tif`
- `QA/QA_GRID_validmask_640.tif`
- `QA/RUN_MANIFEST.json`

Naming rule:

- notebook-compatible names are required in the target tree
- some current app outputs are acceptable transitional equivalents only if parity passes

Transitional renamed-equivalents requiring content parity:

- `QA/FOCUS_MASK_17m_inside_640.tif` -> `full_job/focus/focus_zone_17m.tif`
- `QA/SUMMARY_RADAR_*.csv` -> `qa/sar/sar_summary.csv`

Required implementation targets from Phase 1:

- `QA/QA_GRID_dx_m_640.tif`
- `QA/QA_GRID_dy_m_640.tif`
- `QA/QA_GRID_validmask_640.tif`
- `QA/RUN_MANIFEST.json`

Current intentionally-different QA files:

- `QA/QA_RADAR_META_*.json`
- `QA/QA_RADAR_CELL25_PAIR_IDS_*.json`
- `QA/QA_S1_MASTER_UNITS.json`

Current contract decision:

- the app may keep `qa/sar/sar_pair_diagnostics.json`
- but the notebook-compatible QA files are still required implementation targets if the full notebook-output match claim is to be made

Checks:

- raster metadata and numeric parity for QA rasters
- CSV schema/content parity for `SUMMARY_RADAR_*.csv`
- JSON key/schema parity for `RUN_MANIFEST.json` and QA manifests

UI expectation later:

- yes, operator UI must show and download the QA group

### 7. `QA/sar/intermediates/`

Required notebook-compatible SAR intermediate outputs:

- `QA/sar/intermediates/sar_intermediate_manifest.json`
- `QA/sar/intermediates/per_image_products_db/*.npy`
- `QA/sar/intermediates/pair_median/*.npy`
- `QA/sar/intermediates/final_median_pre_rtc/*.npy`
- `QA/sar/intermediates/post_sample_pre_rtc/*.npy`
- `QA/sar/intermediates/post_rtc/*.npy`

Naming rule:

- notebook-compatible layout and names required
- no renamed-equivalent currently accepted for a full match claim

Required implementation targets from Phase 1:

- `QA/sar/intermediates/sar_intermediate_manifest.json`
- `QA/sar/intermediates/*.npy`

Checks:

- inventory existence
- NPY shape/dtype/value parity
- manifest inventory parity

UI expectation later:

- yes, for operator use in the private app

### 8. `QA/RUN_MANIFEST.json`

Required file:

- `QA/RUN_MANIFEST.json`

Naming rule:

- exact notebook-compatible filename required
- no current app substitute is sufficient for a full match claim

Current app files that are useful but not sufficient:

- `grid_manifest.json`
- `run_status_history.json`
- `stage_*.manifest.json`

Checks:

- JSON key/schema parity
- manifest inventory parity

UI expectation later:

- yes, must be downloadable

## Phase 1 Findings Classified

### Missing-in-app outputs that must be implemented

- `REPORT_640_Pottery_Report.tif`
- `REPORT_640_Mass_Report.tif`
- `REPORT_640_FINAL_Zero_Point_Targets.tif`
- `DEM_GEO8_TIFS/hillshade_0to1_640.tif`
- `QA/QA_GRID_dx_m_640.tif`
- `QA/QA_GRID_dy_m_640.tif`
- `QA/QA_GRID_validmask_640.tif`
- `QA/RUN_MANIFEST.json`
- `QA/sar/intermediates/sar_intermediate_manifest.json`
- `QA/sar/intermediates/*.npy`

### Renamed-equivalent outputs acceptable only if parity passes

- `DEM_GEO8_TIFS/DEM_640.tif` -> `dem.tif`
- `DEM_GEO8_TIFS/slope_deg_640.tif` -> `slope.tif`
- `DEM_GEO8_TIFS/aspect_deg_640.tif` -> `aspect.tif`
- `DEM_GEO8_TIFS/roughness_100m_640.tif` -> `roughness.tif`
- `DEM_GEO8_TIFS/tpi_100m_640.tif` -> `TPI.tif`
- notebook SAR GeoTIFF family -> `VV_dB.tif`, `VH_dB.tif`, `logRatio_dB.tif`, `incidence.tif`
- notebook SAR NPY family -> `npy_radar_bands/VV_dB.npy`, `VH_dB.npy`, `logRatio_dB.npy`, `incidence.npy`
- `NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE.npy` -> `hypercube.npy`
- `NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE.tif` -> `hypercube.tif`
- `NPY_STACKS/RADAR_STACK_HWC_640_*.npy` -> `stacks/tensor_support/radar_linear_support_stack.npy`
- `QA/FOCUS_MASK_17m_inside_640.tif` -> `full_job/focus/focus_zone_17m.tif`
- `QA/SUMMARY_RADAR_*.csv` -> `qa/sar/sar_summary.csv`

### Renamed-equivalent outputs that should also be emitted under notebook-compatible names

All renamed-equivalent items listed above must eventually be emitted again under notebook-compatible names if the app is going to claim full notebook-output match rather than equivalence-by-mapping only.

### App-only outputs that should be kept

- `objects_index.csv`
- `clusters_summary.csv`
- `alignment_qa.json`
- `alignment_audit.csv`
- `alignment_mask_selection.json`
- `grid_manifest.json`
- `run_status_history.json`
- `stage_*.manifest.json`
- Sentinel-2 index outputs
- `TRI.tif`
- `TWI.tif`
- `lst.tif`
- `full_job/*`
- `kmz/*`
- object masks and patches

These are allowed app-only extras. They should not block notebook matching as long as required notebook-compatible outputs are also present.

### Intentionally-different outputs

- notebook curvature triple versus app single `curvature.tif`
- notebook focus companion JSON versus app `full_job/focus/focus_zone_summary.json`
- notebook SAR provenance QA JSON files versus app `qa/sar/sar_pair_diagnostics.json`

These may remain intentionally different only if the contract explicitly says they are outside the required full-match target. Otherwise they must later be aligned.

### Outputs needing content parity checks

- all DEM renamed-equivalent rasters
- all SAR renamed-equivalent rasters
- all SAR renamed-equivalent NPY bands
- `hypercube.tif`
- `hypercube.npy`
- `stacks/tensor_support/radar_linear_support_stack.npy`
- `full_job/focus/focus_zone_17m.tif`
- `qa/sar/sar_summary.csv`
- `qa/sar/sar_pair_diagnostics.json`

## App-Only Output Preservation Rule

The app may keep operator-useful outputs that the notebook reference does not expose, provided:

- they do not replace required notebook-compatible outputs
- they do not weaken parity checks
- they do not hide missing required notebook outputs
- they can be grouped separately in the UI later as app-only extras

## Artifact Naming Correction

The current app output is:

- `alignment_audit.csv`

It is not:

- `alignment_audit.json`

Any later UI/download contract must use the actual file type and extension.

## Parity Proof Levels

Every required output group must ultimately satisfy these proof levels as applicable:

1. inventory existence
2. raster metadata parity:
   - dimensions
   - CRS
   - transform/grid
   - dtype
   - band count
   - nodata
3. numeric raster parity within existing tolerances
4. NPY shape/dtype/value parity
5. CSV schema/content parity
6. JSON key/schema parity
7. manifest inventory parity
8. UI browse/download parity

Proof expectations by output class:

- report GeoTIFFs: 1, 2, 3, 8
- DEM GeoTIFFs: 1, 2, 3, 8
- SAR GeoTIFFs: 1, 2, 3, 8
- SAR NPY bands: 1, 4, 8
- stack TIFFs/NPYs: 1, 2 or 4, 3 or 4, 8
- QA rasters: 1, 2, 3, 8
- QA CSV/JSON: 1, 5 or 6, 8
- run manifest: 1, 6, 7, 8

## UI Requirement

Because this is a private/operator app, later UI work must expose the full operator output tree, including:

- reports
- DEM GeoTIFFs
- radar GeoTIFFs
- radar NPY bands
- stacks and hypercube outputs
- QA outputs
- run manifest
- app-only extras grouped separately

The UI contract later must preserve:

- real filenames and extensions
- browseable output grouping
- downloadable files through guarded routes

## Future Implementation Phases

### Phase 3

Implement missing local app outputs.

### Phase 4

Register and show the full operator output tree in the UI.

### Phase 5

Add notebook-output parity tests.

### Phase 6

Run final full-run verification.

## Immediate Recommendation

Proceed to Phase 3 next.

Priority order inside Phase 3 should be:

1. emit the three root report GeoTIFFs
2. emit notebook-compatible `DEM_GEO8_TIFS/`
3. emit notebook-compatible `GEOTIFF_RADAR_BANDS/` and `NPY_RADAR_BANDS/`
4. emit notebook-compatible `NPY_STACKS/`
5. emit notebook-compatible `QA/` outputs including `QA/RUN_MANIFEST.json`
6. emit notebook-compatible `QA/sar/intermediates/`

No notebook-output match claim should be made until those required groups exist and the defined parity proof levels pass.
