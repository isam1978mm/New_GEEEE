# Operator Deliverables

## Purpose

This document defines the operator-facing local deliverable set that may appear under the operator output tree.

It is intentionally narrower than "all files under `data/runs/<run_id>/`".

The operator output tree is a curated local workspace surface, not a raw filesystem browser.

## Current Policy

The operator output tree should include only:

- final science rasters and arrays that an operator may need to inspect or hand off locally
- notebook-compatible deliverables that are parity-tracked
- safe QA summaries and manifests that explain the run outcome
- public-safe candidate and alignment summaries

The operator output tree should exclude:

- runtime internals and stage manifests
- raw support tensors and staging arrays
- exact-location exports and field-ops planning files
- notebook-only legacy gaps with low operator value
- private or sensitive machine-local files

## Promoted Deliverables

These families are intentionally included in the operator output tree:

- notebook-compatible DEM deliverables under `DEM_GEO8_TIFS/`
- notebook-compatible SAR GeoTIFF and NPY deliverables under `GEOTIFF_RADAR_BANDS/` and `NPY_RADAR_BANDS/`
- notebook-compatible stack deliverables under `NPY_STACKS/`
- `AI_READY_640/*.tif`
- root `REPORT_640_*.tif`
- `QA/RUN_MANIFEST.json`
- `QA/REPORT_640_manifest.json`
- `QA/QA_GRID_*.tif`
- `QA/grid_dem/grid_guard_summary.json`
- `QA/grid_dem/dem_audit_summary.json`
- `QA/grid_dem/drift_audit.csv`
- `QA/sar/sar_pair_diagnostics.json`
- `QA/sar/sar_summary.csv`
- `QA/sar/sar_nodata_audit.csv`
- `QA/sar/sar_alignment_summary.json`
- `QA/sar/intermediates/sar_intermediate_manifest.json`
- `QA/sar/intermediates/post_rtc/*.npy`
- `QA/stacks/secret_layers_manifest.json`
- `QA/stacks/s2_indices_summary.json`
- `QA/stacks/thermal_summary.json`
- app-only science outputs: `NDVI.tif`, `NDWI.tif`, `NDMI.tif`, `NBR.tif`, `IRONOX.tif`, `IRON_SWIR.tif`, `BSI.tif`, `lst.tif`, `pca_anomaly.tif`, `pca_eigenvalues.json`
- root hypercube outputs: `hypercube.tif`, `hypercube.npy`, `hypercube_band_order.csv`, `hypercube_band_stats.csv`, `hypercube_norm_params.csv`
- candidate and alignment summaries: `objects_index.csv`, `clusters_summary.csv`, `alignment_qa.json`, `alignment_audit.csv`, `alignment_mask_selection.json`

## Audit Table

| Output or family | Current status | Why hidden or unavailable before | Operator value | Recommendation |
|---|---|---|---|---|
| `QA/grid_dem/grid_guard_summary.json` | implemented | existed as local QA only; not explicitly treated as operator deliverable | high | promote now |
| `QA/grid_dem/dem_audit_summary.json` | implemented | existed as local QA only; not explicitly treated as operator deliverable | medium | promote now |
| `QA/grid_dem/drift_audit.csv` | implemented | existed as local QA only; not explicitly treated as operator deliverable | medium | promote now |
| `QA/sar/sar_pair_diagnostics.json` | implemented | existed as local QA only; not explicitly treated as operator deliverable | medium | promote now |
| `QA/sar/sar_summary.csv` | implemented | existed as local QA only; not explicitly treated as operator deliverable | high | promote now |
| `QA/sar/sar_nodata_audit.csv` | implemented | existed as local QA only; not explicitly treated as operator deliverable | medium | promote now |
| `QA/sar/sar_alignment_summary.json` | implemented | existed as local QA only; not explicitly treated as operator deliverable | medium | promote now |
| `QA/stacks/s2_indices_summary.json` | implemented | existed as local QA only; not explicitly treated as operator deliverable | medium | promote now |
| `QA/stacks/thermal_summary.json` | implemented | existed as local QA only; not explicitly treated as operator deliverable | medium | promote now |
| `objects_index.csv` | implemented | already operator-safe, kept | high | keep visible |
| `clusters_summary.csv` | implemented | already operator-safe, kept | high | keep visible |
| `alignment_qa.json` / `alignment_audit.csv` / `alignment_mask_selection.json` | implemented | already operator-safe, kept | high | keep visible |
| `REPORT_640_*.tif` | implemented | notebook parity work completed; should remain visible | high | keep visible |
| `AI_READY_640/*.tif` | implemented | notebook-compatible secret/report family now implemented | medium | keep visible |
| `NPY_STACKS/FINAL_TESLA*` | implemented | notebook-compatible stack family now implemented | high | keep visible |
| `grid_manifest.json` | implemented | runtime/grid internal contract file | debug only | keep internal |
| `run_status_history.json` | implemented | runtime internals duplicated by UI/API status history | debug only | keep internal |
| `stage_*.manifest.json` | implemented | stage runtime internals with implementation detail | debug only | keep internal |
| `dem.npy`, `npy_radar_bands/*.npy`, `stacks/tensor_support/*` | implemented | raw support arrays used for staging, aliases, and parity proof | debug only | keep internal |
| `full_job/location/*`, `kmz/*` | implemented | exact-location exports; can carry target context | unsafe/private | keep internal |
| `full_job/field_ops/*` | implemented | field-ops planning aids can carry target context | unsafe/private | keep internal |
| `full_job/gps/*` | implemented | GPS comparison outputs can carry exact target context | unsafe/private | keep internal |
| `objects/object_mask.npy`, `objects/object_patches/*.npy` | implemented | raw local object extraction internals | debug only | keep internal |
| `QA/sar/intermediates/per_image_products_db/*` | not implemented | notebook-only pre-RTC intermediate family; production SAR does not persist it | low | document as legacy notebook-only |
| `QA/sar/intermediates/pair_median/*` | not implemented | notebook-only pre-RTC intermediate family; production SAR does not persist it | low | document as legacy notebook-only |
| `QA/sar/intermediates/final_median_pre_rtc/*` | not implemented | notebook-only pre-RTC intermediate family; production SAR does not persist it | low | document as legacy notebook-only |
| `QA/sar/intermediates/post_sample_pre_rtc/*` | not implemented | notebook-only pre-RTC intermediate family; production SAR does not persist it | low | document as legacy notebook-only |
| notebook panchromatic support families | not implemented | no app source-equivalent product family | low | future phase only if a real operator need emerges |

## Never-Expose Or Keep-Private Files

These must remain absent from the operator output tree and guarded downloads unless separately redacted and approved:

- `.env`
- credential or service-account-like files
- `PATH_MAP.local.json`
- database files
- raw log files
- cache folders
- local absolute-path maps
- coordinate-bearing exact-location exports that are not explicitly redacted

## Legacy Notebook-Only Gaps

The pre-RTC SAR intermediate families remain documented in manifests and parity docs, but they are not useful operator deliverables:

- they are notebook-only staging artifacts
- they are not needed to interpret final SAR outputs
- they should not appear as "Advanced / unavailable outputs" in the operator UI

## Future Candidates

These are reasonable future operator deliverables, but they are not implemented in this phase:

- a stable packaged run bundle or zip, if a safe curation/export policy is added
- a redacted request-zone or field-ops handoff package that removes exact coordinates
- a redacted visual map package if preview/export policy is explicitly approved
- notebook panchromatic support outputs only if a real operator workflow requires them and a source-equivalent implementation is justified
