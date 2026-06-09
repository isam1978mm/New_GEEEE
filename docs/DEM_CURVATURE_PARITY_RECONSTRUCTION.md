# DEM Curvature Parity Reconstruction

## 1. Purpose

Phase 4D investigates the three missing notebook DEM curvature variant outputs and records whether they are ready for a later implementation slice:

```text
curv_laplacian_640.tif
curv_plan_640.tif
curv_profile_640.tif
```

Faithful notebook-to-Python-app conversion remains the objective. Phase 4D preserves the notebook output names as parity requirements, but it does not implement new DEM formulas.

## 2. Scope

Phase 4D covers source inspection, formula/status reconstruction, a machine-readable registry, and a JSON report helper for the DEM curvature variants.

Files inspected for this phase:

```text
notebook_gaps_coverage.md
gaps.md
docs/PARITY_PHASE_0_OUTPUT_INVENTORY_LOCK.md
docs/parity_expected_outputs.json
docs/PARITY_MODE_CONTRACT.md
docs/MISSING_RASTER_FAMILIES_CONTRACT.md
docs/REPORT_640_PARITY_VERIFICATION_CONTRACT.md
docs/SECRET_LAYERS_PARITY_VERIFICATION_CONTRACT.md
docs/Notebook_Cells_E.md
docs/APP_NOTEBOOK_OUTPUT_CONTRACT.md
docs/NOTEBOOK_VS_APP_OUTPUTS.md
docs/PRD_v0.5.md
app/pipeline/parity/missing_rasters.py
app/pipeline/stages/dem.py
app/pipeline/stages/dem_derivatives.py
app/pipeline/stages/feature_stacks.py
```

`Notebook cells.md` was not present at repository root. `docs/Notebook_Cells_E.md` was present and inspected as the notebook source-reference summary.

## 3. Non-Goals

Phase 4D does not:

- change DEM formulas;
- change raster math;
- generate DEM curvature rasters;
- call Earth Engine;
- integrate with the live pipeline;
- alter API, frontend, database, migrations, classifier logic, or artifact serving;
- rename existing outputs;
- decide public/shared exposure.

No formulas were changed in Phase 4D.

## 4. Current App DEM/Terrain Stage Findings

`app/pipeline/stages/dem.py` writes:

```text
dem.tif
dem.npy
DEM_GEO8_TIFS/DEM_640.tif
QA/grid_dem/dem_audit_summary.json
```

`app/pipeline/stages/dem_derivatives.py` writes app-native DEM derivatives:

```text
slope.tif
aspect.tif
curvature.tif
TPI.tif
TRI.tif
roughness.tif
TWI.tif
```

It also writes notebook-compatible DEM aliases:

```text
DEM_GEO8_TIFS/DEM_640.tif
DEM_GEO8_TIFS/slope_deg_640.tif
DEM_GEO8_TIFS/aspect_deg_640.tif
DEM_GEO8_TIFS/roughness_100m_640.tif
DEM_GEO8_TIFS/tpi_100m_640.tif
DEM_GEO8_TIFS/hillshade_0to1_640.tif
```

The current app curvature formula in `compute_dem_derivatives()` is:

```text
d2z_dxx + d2z_dyy
```

That is a Laplacian-style curvature. It is written as root `curvature.tif`, not as `DEM_GEO8_TIFS/curv_laplacian_640.tif`.

`app/pipeline/stages/feature_stacks.py` consumes root `curvature.tif` as one science-core band. It does not write `curv_laplacian_640.tif`, `curv_plan_640.tif`, or `curv_profile_640.tif`.

## 5. Notebook Formula Findings

`docs/Notebook_Cells_E.md` identifies notebook cell 104 as `DEM_GEO8_TIFS (PRO)` and describes it as deriving DEM-based layers including slope, aspect, curvature, TPI, TRI, and roughness on the master grid. It does not include the exact formulas for:

```text
curv_laplacian_640.tif
curv_plan_640.tif
curv_profile_640.tif
```

Existing parity docs identify these three output names and state that the app currently writes one `curvature.tif` instead of the notebook's three curvature rasters. No inspected source or document provides exact plan-curvature or profile-curvature equations.

File existence is not parity proof. The app's `curvature.tif` is not automatically equivalent to all three notebook curvature variants.

## 6. Output-By-Output Status Table

| Output | Family | Current app status | Formula status | Implementation status | Runtime verified | Notebook-value parity verified |
| --- | --- | --- | --- | --- | --- | --- |
| `curv_laplacian_640.tif` | DEM/terrain outputs | App writes root `curvature.tif` and `DEM_GEO8_TIFS/curv_laplacian_640.tif`. | `existing_app_equivalent_found` | `runtime_implemented_reference_pending` | **true** | false |
| `curv_plan_640.tif` | DEM/terrain outputs | App writes `DEM_GEO8_TIFS/curv_plan_640.tif`. | `authoritative_formula_found` | `runtime_implemented_reference_pending` | **true** | false |
| `curv_profile_640.tif` | DEM/terrain outputs | App writes `DEM_GEO8_TIFS/curv_profile_640.tif`. | `authoritative_formula_found` | `runtime_implemented_reference_pending` | **true** | false |

Status meaning: runtime implemented; frozen reference comparison pending. Notebook-value parity is not verified.

## 7. Formula Status For Each Output

Allowed formula statuses:

```text
exact_formula_found
approximate_formula_found
no_formula_found
existing_app_equivalent_found
unknown_needs_reference
```

`curv_laplacian_640.tif`:

- Formula status: `existing_app_equivalent_found`
- Source: `app/pipeline/stages/dem_derivatives.py`
- Rationale: app `curvature.tif` computes `d2z_dxx + d2z_dyy`, which is Laplacian-style curvature. Runtime output is now written as `DEM_GEO8_TIFS/curv_laplacian_640.tif`.
- Caveat: exact notebook formula text was not found, so notebook-value parity still requires frozen reference comparison.

`curv_plan_640.tif`:

- Formula status: `authoritative_formula_found`
- Source: `notebooks/new.ipynb` — formula text recovered in Phase 4D3.
- Rationale: `curv_plan = (r*q*q - 2*s*p*q + t*p*p) / ((p*p + q*q + 1e-12) * (den_sqrt + 1e-12))`. Runtime output is now written as `DEM_GEO8_TIFS/curv_plan_640.tif`.
- Caveat: notebook-value parity still requires frozen reference comparison.

`curv_profile_640.tif`:

- Formula status: `authoritative_formula_found`
- Source: `notebooks/new.ipynb` — formula text recovered in Phase 4D3.
- Rationale: `curv_profile = -(r*p*p + 2*s*p*q + t*q*q) / (den_3_2 + 1e-12)`. Runtime output is now written as `DEM_GEO8_TIFS/curv_profile_640.tif`.
- Caveat: notebook-value parity still requires frozen reference comparison.

## 8. Required Inputs

Known or likely required inputs for `curv_laplacian_640.tif`:

```text
DEM
cell size / transform
second derivatives
nodata mask
```

Known or likely required inputs for `curv_plan_640.tif` and `curv_profile_640.tif`:

```text
DEM
cell size / transform
slope
aspect
first derivatives
second derivatives
nodata mask
```

Exact plan/profile input ordering and normalization cannot be locked until notebook formulas or reference outputs are recovered.

## 9. Implementation Risk

Risk is low for a later `curv_laplacian_640.tif` alias or dedicated writer only if frozen notebook reference comparison proves that app `curvature.tif` matches notebook `curv_laplacian_640.tif` within accepted tolerance.

Risk is high for `curv_plan_640.tif` and `curv_profile_640.tif` because the exact notebook equations are not available. Implementing generic terrain plan/profile curvature formulas now would risk inventing outputs rather than preserving notebook parity.

## 10. Required Tests For Later Implementation

A later implementation slice must add tests for:

- output presence under `DEM_GEO8_TIFS/`;
- original notebook filenames preserved;
- no coordinate-bearing/public/shared defaults;
- CRS, transform, width, height, band count, dtype, and nodata matching current grid;
- nodata propagation;
- numeric comparison against frozen notebook references;
- separate tests for Laplacian, plan, and profile curvature formulas;
- no changes to existing `curvature.tif` behavior unless explicitly approved.

## 11. Required Reference Notebook Outputs

Notebook-value parity requires frozen reference files:

```text
DEM_GEO8_TIFS/curv_laplacian_640.tif
DEM_GEO8_TIFS/curv_plan_640.tif
DEM_GEO8_TIFS/curv_profile_640.tif
```

Reference metadata should include width, height, CRS, transform, dtype, nodata, and band count. Numeric comparison should record max absolute difference, mean absolute difference, compared pixel count, and nodata/NaN count.

## 12. Recommended Phase 4D2 Implementation Plan

1. Capture or provide frozen notebook reference outputs for all three curvature variants.
2. Compare app `curvature.tif` to notebook `curv_laplacian_640.tif`.
3. If the Laplacian comparison passes, implement a notebook-parity alias or dedicated writer for `DEM_GEO8_TIFS/curv_laplacian_640.tif`.
4. Recover exact notebook formulas for `curv_plan_640.tif` and `curv_profile_640.tif`.
5. Implement plan/profile curvature only after the formulas and reference expectations are clear.
6. Keep the implementation isolated to notebook parity mode and avoid public/shared exposure decisions.

Recommended next Phase 4D2 target:

```text
curv_laplacian_640.tif
```

Reason: the app has a Laplacian-style `curvature.tif` candidate equivalent, but it still requires frozen notebook reference comparison before implementation.

## 13. Confirmation

No DEM formulas, raster math, existing output names, live pipeline behavior, API behavior, frontend behavior, database models, migrations, classifier logic, or artifact serving policy were changed in Phase 4D.
