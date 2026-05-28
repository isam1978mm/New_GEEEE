# Notebook Secret/Report Layer Contract

## Purpose

This document formalizes the notebook-only secret/report layer family that feeds the notebook `FINAL_TESLA_V7_2_HYPERCUBE` outputs.

It is a contract only. It does not implement formulas, pipeline generation, UI, API, or parity tolerances.

## Notebook-Only Layer Family

The frozen notebook reference family requires these nine layers:

### Secret layers

- `AI_READY_640_Secret_Gold_Halo.tif`
- `AI_READY_640_Secret_Silver_Oxide.tif`
- `AI_READY_640_Secret_Tunnel_Ceiling.tif`
- `AI_READY_640_Secret_Thermal_Inertia.tif`
- `AI_READY_640_Secret_Chemical_Protector.tif`
- `AI_READY_640_Secret_Hidden_Doors.tif`

### Report layers

- `REPORT_640_FINAL_Zero_Point_Targets.tif`
- `REPORT_640_Mass_Report.tif`
- `REPORT_640_Pottery_Report.tif`

## Known Notebook Formulas

Known formulas and logic recovered from `notebooks/new.ipynb`:

- `AI_READY_640_Secret_Gold_Halo`
  - `B12 / (B8 + eps)`
- `AI_READY_640_Secret_Silver_Oxide`
  - `B2 / (B1 + eps)`
- `AI_READY_640_Secret_Tunnel_Ceiling`
  - `B8 - B4`
- `AI_READY_640_Secret_Thermal_Inertia`
  - `l9_col / focal_mean(l9_col, 500m)`
- `AI_READY_640_Secret_Chemical_Protector`
  - `B1 / (B11 + eps)`
- `AI_READY_640_Secret_Hidden_Doors`
  - `hillshade(315, 35) - hillshade(135, 35)`
- `REPORT_640_Mass_Report`
  - `B12 * ST_B10 / 1000`
- `REPORT_640_Pottery_Report`
  - `B12 / B11`
- `REPORT_640_FINAL_Zero_Point_Targets`
  - threshold intersection of:
    - `GoldAlloy_Signal`
    - `IronOxide_Hardness`
    - `VegRoot_Anomaly`

## Final Tesla Contract

The notebook `FINAL_TESLA_V7_2_HYPERCUBE` family is assembled from exactly these nine notebook layers:

1. `AI_READY_640_Secret_Gold_Halo`
2. `AI_READY_640_Secret_Silver_Oxide`
3. `AI_READY_640_Secret_Tunnel_Ceiling`
4. `AI_READY_640_Secret_Thermal_Inertia`
5. `AI_READY_640_Secret_Chemical_Protector`
6. `AI_READY_640_Secret_Hidden_Doors`
7. `REPORT_640_FINAL_Zero_Point_Targets`
8. `REPORT_640_Mass_Report`
9. `REPORT_640_Pottery_Report`

Expected notebook stack outputs:

- `NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE.tif`
- `NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE.npy`
- `NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE_PATCHED_14B.tif`

## Current App Status

Current app status is intentionally:

- `not_implemented_no_source_equivalent` for all three `REPORT_640_*` rasters
- `not_implemented_no_source_equivalent` for the notebook `FINAL_TESLA_V7_2_HYPERCUBE` family

Reason:

- the app does not currently emit the exact raw notebook behavior/source layers required for this family
- the app `hypercube.tif` and `hypercube.npy` are a different 21-channel science product
- the app `ai_ready_support_stack` is an implemented subset/support tensor, not the notebook `AI_READY_640_Secret_*` raster family

## Source-Equivalence Rule

Until these exact notebook layers are implemented:

- `REPORT_640_*` must remain not implemented
- notebook `FINAL_TESLA_V7_2_HYPERCUBE*` outputs must remain not implemented
- the app must not alias the 21-channel science hypercube as notebook `FINAL_TESLA`
- the operator output tree must show these notebook outputs under `not_implemented[]`, not under implemented outputs

## Non-Goals

This contract does not approve:

- implementing the nine layers yet
- changing pipeline generation
- changing SAR, DEM, GRID, or stack math
- changing tolerances
- changing notebook code
