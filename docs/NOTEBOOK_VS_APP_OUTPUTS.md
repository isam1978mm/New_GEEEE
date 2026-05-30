# Notebook Vs App Outputs

## 2026-05-30 Parity Closeout Update

This document's Phase 1 inventory tables are historical and do not represent the final parity classification.

Current closeout status for the notebook-compatible stack family:

- `NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE.tif` is implemented and parity passing.
- `NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE.npy` is implemented and parity passing.
- `NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE_PATCHED_14B.tif` is implemented as a frozen-compatible 13-band artifact and parity passing.
- `NPY_STACKS/RADAR_STACK_HWC_640_app.npy` remains an accepted classified strict `xfail`.

RADAR stack classification:

- frozen `RADAR_STACK_HWC` equals `np.stack` of frozen SAR band references exactly
- app `RADAR_STACK_HWC_640_app.npy` equals `np.stack` of app SAR band outputs exactly
- the remaining app-vs-reference mismatch is inherited from the upstream SAR dB band residual
- no `RADAR_STACK` reference refresh is needed
- no SAR math, SAR band reference refresh, or tolerance change is approved

Comparison date: `2026-05-26`

Fresh app run ID: `da0dca61-bc35-43c2-af91-351f3fbda942`

Notebook reference folder: `<notebook_reference_output>/`

Absolute local paths are intentionally omitted. Coordinate-bearing notebook filename stamps are redacted below as `<radar_stamp>` or `<radar_config>`.

## Summary

| Inventory | Files | Directories | Notes |
|---|---:|---:|---|
| Notebook reference output | 144 | 18 | Frozen operator-local notebook reference bundle |
| Fresh app run output | 2441 | 19 | Dominated by `objects/object_patches/*.npy` |

Notebook status totals from this Phase 1 inventory:

| Status | Count |
|---|---:|
| `renamed-equivalent` | 18 |
| `missing-in-app` | 55 |
| `notebook-only` | 64 |
| `intentionally-different` | 7 |

## Notebook Output Inventory

Top-level notebook inventory counts:

| Group | File count |
|---|---:|
| root files | 24 |
| `DEM_GEO8_TIFS/` | 9 |
| `GEOTIFF_RADAR_BANDS/` | 10 |
| `NPY_RADAR_BANDS/` | 10 |
| `NPY_STACKS/` | 8 |
| `OPT/` | 4 |
| `QA/` | 79 |

Key notebook groups observed:

- root reports: `REPORT_640_Pottery_Report.tif`, `REPORT_640_Mass_Report.tif`, `REPORT_640_FINAL_Zero_Point_Targets.tif`
- DEM family under `DEM_GEO8_TIFS/`
- radar GeoTIFF family under `GEOTIFF_RADAR_BANDS/`
- radar NPY family under `NPY_RADAR_BANDS/`
- stack outputs under `NPY_STACKS/`
- panchromatic support outputs under `OPT/`
- QA manifests, focus-mask outputs, radar provenance, and SAR intermediate arrays under `QA/`

## App Run Output Inventory

Top-level app inventory counts:

| Group | File count |
|---|---:|
| root files | 73 |
| `full_job/` | 11 |
| `kmz/` | 2 |
| `npy_radar_bands/` | 4 |
| `objects/` | 2319 |
| `qa/` | 18 |
| `stacks/` | 14 |

Key app groups observed:

- root rasters: `dem.tif`, `VV_dB.tif`, `VH_dB.tif`, `logRatio_dB.tif`, `incidence.tif`, `hypercube.tif`, `pca_anomaly.tif`, `NDVI.tif`, `NDWI.tif`, `NDMI.tif`, `NBR.tif`, `IRONOX.tif`, `IRON_SWIR.tif`, `BSI.tif`, `slope.tif`, `aspect.tif`, `roughness.tif`, `TPI.tif`, `TRI.tif`, `TWI.tif`, `curvature.tif`, `lst.tif`
- run metadata: `grid_manifest.json`, `run_status_history.json`, `stage_*.manifest.json`
- SAR NPY outputs: `npy_radar_bands/`
- stacked tensors: `stacks/tensor_support/`
- focus/location/field-op support outputs: `full_job/`, `kmz/`
- object extraction outputs: `objects_index.csv`, `clusters_summary.csv`, `objects/object_mask.npy`, `objects/object_patches/*.npy`
- QA summaries: `qa/grid_dem/`, `qa/sar/`, `qa/stacks/`, `qa/alignment/`, `qa/parity/`

## File-By-File Comparison

For repeated notebook families, one row may represent a concrete filename pattern that was confirmed in the actual notebook tree.

| Notebook file | Notebook relative path | App equivalent relative path | Status | UI-visible/downloadable | Notes |
|---|---|---|---|---|---|
| `REPORT_640_Pottery_Report.tif` | `REPORT_640_Pottery_Report.tif` |  | `missing-in-app` | no | Notebook final report raster is not written by the app run. |
| `REPORT_640_Mass_Report.tif` | `REPORT_640_Mass_Report.tif` |  | `missing-in-app` | no | Notebook final report raster is not written by the app run. |
| `REPORT_640_FINAL_Zero_Point_Targets.tif` | `REPORT_640_FINAL_Zero_Point_Targets.tif` |  | `missing-in-app` | no | Notebook zero-point target report is not written by the app run. |
| `AI_BEH_*` series | `AI_BEH_*.tif` |  | `notebook-only` | no | Thirteen notebook AI-ready behavior rasters exist in the reference output and are not written by the app run. |
| `AI_READY_*` series | `AI_READY_*.tif` |  | `notebook-only` | no | Six notebook AI-ready secret/behavior rasters exist in the reference output and are not written by the app run. |
| `REF_DEM_UTM37_10m_640_GEE_ALIGNED.npy` | `REF_DEM_UTM37_10m_640_GEE_ALIGNED.npy` |  | `notebook-only` | no | Notebook reference DEM export is not written by the app run. |
| `REF_DEM_UTM37_10m_640_GEE_ALIGNED.tif` | `REF_DEM_UTM37_10m_640_GEE_ALIGNED.tif` |  | `notebook-only` | no | Notebook reference DEM export is not written by the app run. |
| `DEM_640.tif` | `DEM_GEO8_TIFS/DEM_640.tif` | `dem.tif` | `renamed-equivalent` | no | App writes the DEM at run root instead of `DEM_GEO8_TIFS/`. |
| `slope_deg_640.tif` | `DEM_GEO8_TIFS/slope_deg_640.tif` | `slope.tif` | `renamed-equivalent` | no | Filename and folder differ. |
| `aspect_deg_640.tif` | `DEM_GEO8_TIFS/aspect_deg_640.tif` | `aspect.tif` | `renamed-equivalent` | no | Filename and folder differ. |
| `roughness_100m_640.tif` | `DEM_GEO8_TIFS/roughness_100m_640.tif` | `roughness.tif` | `renamed-equivalent` | no | Filename and folder differ. |
| `tpi_100m_640.tif` | `DEM_GEO8_TIFS/tpi_100m_640.tif` | `TPI.tif` | `renamed-equivalent` | no | Filename and folder differ. |
| `curv_laplacian_640.tif` | `DEM_GEO8_TIFS/curv_laplacian_640.tif` | `curvature.tif` | `intentionally-different` | no | App currently writes one curvature derivative instead of the notebook's three curvature rasters. |
| `curv_plan_640.tif` | `DEM_GEO8_TIFS/curv_plan_640.tif` | `curvature.tif` | `intentionally-different` | no | App currently writes one curvature derivative instead of the notebook's three curvature rasters. |
| `curv_profile_640.tif` | `DEM_GEO8_TIFS/curv_profile_640.tif` | `curvature.tif` | `intentionally-different` | no | App currently writes one curvature derivative instead of the notebook's three curvature rasters. |
| `hillshade_0to1_640.tif` | `DEM_GEO8_TIFS/hillshade_0to1_640.tif` |  | `missing-in-app` | no | No hillshade-equivalent app raster was found. |
| `PAN_LS_Panchromatic_640.tif` | `GEOTIFF_RADAR_BANDS/PAN_LS_Panchromatic_640.tif` |  | `notebook-only` | no | Notebook panchromatic support raster has no direct app file. |
| `PAN_S2_Panchromatic_10m_640.tif` | `GEOTIFF_RADAR_BANDS/PAN_S2_Panchromatic_10m_640.tif` |  | `notebook-only` | no | Notebook panchromatic support raster has no direct app file. |
| `RADAR_VV_dB_640_<radar_stamp>_<radar_config>.tif` | `GEOTIFF_RADAR_BANDS/RADAR_VV_dB_640_<radar_stamp>_<radar_config>.tif` | `VV_dB.tif` | `renamed-equivalent` | no | App writes the same logical SAR band at run root. |
| `RADAR_VH_dB_640_<radar_stamp>_<radar_config>.tif` | `GEOTIFF_RADAR_BANDS/RADAR_VH_dB_640_<radar_stamp>_<radar_config>.tif` | `VH_dB.tif` | `renamed-equivalent` | no | App writes the same logical SAR band at run root. |
| `RADAR_logRatio_dB_640_<radar_stamp>_<radar_config>.tif` | `GEOTIFF_RADAR_BANDS/RADAR_logRatio_dB_640_<radar_stamp>_<radar_config>.tif` | `logRatio_dB.tif` | `renamed-equivalent` | no | App writes the same logical SAR band at run root. |
| `RADAR_angle_640_<radar_stamp>_<radar_config>.tif` | `GEOTIFF_RADAR_BANDS/RADAR_angle_640_<radar_stamp>_<radar_config>.tif` | `incidence.tif` | `renamed-equivalent` | no | Notebook angle corresponds to app incidence naming. |
| `S1_ASC_VV_Filtered_640.tif` | `GEOTIFF_RADAR_BANDS/S1_ASC_VV_Filtered_640.tif` |  | `notebook-only` | no | Notebook-only radar support raster; no direct app file found. |
| `S1_ASC_VH_Filtered_640.tif` | `GEOTIFF_RADAR_BANDS/S1_ASC_VH_Filtered_640.tif` |  | `notebook-only` | no | Notebook-only radar support raster; no direct app file found. |
| `S1_DESC_VV_Filtered_640.tif` | `GEOTIFF_RADAR_BANDS/S1_DESC_VV_Filtered_640.tif` |  | `notebook-only` | no | Notebook-only radar support raster; no direct app file found. |
| `S1_DESC_VH_Filtered_640.tif` | `GEOTIFF_RADAR_BANDS/S1_DESC_VH_Filtered_640.tif` |  | `notebook-only` | no | Notebook-only radar support raster; no direct app file found. |
| `PAN_LS_Panchromatic_640.npy` | `NPY_RADAR_BANDS/PAN_LS_Panchromatic_640.npy` |  | `notebook-only` | no | Notebook panchromatic support NPY has no direct app file. |
| `PAN_S2_Panchromatic_10m_640.npy` | `NPY_RADAR_BANDS/PAN_S2_Panchromatic_10m_640.npy` |  | `notebook-only` | no | Notebook panchromatic support NPY has no direct app file. |
| `RADAR_VV_dB_640_<radar_stamp>_<radar_config>.npy` | `NPY_RADAR_BANDS/RADAR_VV_dB_640_<radar_stamp>_<radar_config>.npy` | `npy_radar_bands/VV_dB.npy` | `renamed-equivalent` | no | App writes the same logical SAR band under `npy_radar_bands/`. |
| `RADAR_VH_dB_640_<radar_stamp>_<radar_config>.npy` | `NPY_RADAR_BANDS/RADAR_VH_dB_640_<radar_stamp>_<radar_config>.npy` | `npy_radar_bands/VH_dB.npy` | `renamed-equivalent` | no | App writes the same logical SAR band under `npy_radar_bands/`. |
| `RADAR_logRatio_dB_640_<radar_stamp>_<radar_config>.npy` | `NPY_RADAR_BANDS/RADAR_logRatio_dB_640_<radar_stamp>_<radar_config>.npy` | `npy_radar_bands/logRatio_dB.npy` | `renamed-equivalent` | no | App writes the same logical SAR band under `npy_radar_bands/`. |
| `RADAR_angle_640_<radar_stamp>_<radar_config>.npy` | `NPY_RADAR_BANDS/RADAR_angle_640_<radar_stamp>_<radar_config>.npy` | `npy_radar_bands/incidence.npy` | `renamed-equivalent` | no | Notebook angle corresponds to app incidence naming. |
| `S1_ASC_VV_Filtered_640.npy` | `NPY_RADAR_BANDS/S1_ASC_VV_Filtered_640.npy` |  | `notebook-only` | no | Notebook-only radar support NPY; no direct app file found. |
| `S1_ASC_VH_Filtered_640.npy` | `NPY_RADAR_BANDS/S1_ASC_VH_Filtered_640.npy` |  | `notebook-only` | no | Notebook-only radar support NPY; no direct app file found. |
| `S1_DESC_VV_Filtered_640.npy` | `NPY_RADAR_BANDS/S1_DESC_VV_Filtered_640.npy` |  | `notebook-only` | no | Notebook-only radar support NPY; no direct app file found. |
| `S1_DESC_VH_Filtered_640.npy` | `NPY_RADAR_BANDS/S1_DESC_VH_Filtered_640.npy` |  | `notebook-only` | no | Notebook-only radar support NPY; no direct app file found. |
| `FINAL_TESLA_V7_2_HYPERCUBE.npy` | `NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE.npy` | `hypercube.npy` | `renamed-equivalent` | no | App writes the hypercube at run root. |
| `FINAL_TESLA_V7_2_HYPERCUBE.tif` | `NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE.tif` | `hypercube.tif` | `renamed-equivalent` | no | App writes the hypercube GeoTIFF at run root. |
| `RADAR_STACK_HWC_640_<radar_stamp>_<radar_config>.npy` | `NPY_STACKS/RADAR_STACK_HWC_640_<radar_stamp>_<radar_config>.npy` | `stacks/tensor_support/radar_linear_support_stack.npy` | `renamed-equivalent` | no | App writes a radar support stack under `stacks/tensor_support/`. |
| `FINAL_TESLA_V7_2_HYPERCUBE_PATCHED_14B.tif` | `NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE_PATCHED_14B.tif` |  | `implemented / passes parity` | no | Implemented as frozen-compatible 13-band artifact and passes parity. Filename says 14B, but the frozen artifact has 13 bands; no fake 14th band or fake AI_READY_640_Magnetic_Anomaly was created. |
| `FINAL_TESLA_V7_2_HYPERCUBE_RES_2p5M.npy` | `NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE_RES_2p5M.npy` |  | `notebook-only` | no | Notebook resampled hypercube NPY has no direct app file yet. |
| `FINAL_TESLA_V7_2_HYPERCUBE_RES_2p5M.tif` | `NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE_RES_2p5M.tif` |  | `notebook-only` | no | Notebook resampled hypercube TIFF has no direct app file yet. |
| `PAN_LAYERS_STACK_640.npy` | `NPY_STACKS/PAN_LAYERS_STACK_640.npy` |  | `notebook-only` | no | Notebook panchromatic stack has no direct app file yet. |
| `S1_FILTERED_LAYERS_STACK_640.npy` | `NPY_STACKS/S1_FILTERED_LAYERS_STACK_640.npy` |  | `notebook-only` | no | Notebook filtered S1 stack has no direct app file yet. |
| `PAN_LS_Panchromatic_640.npy` | `OPT/PAN_NPY_640/PAN_LS_Panchromatic_640.npy` |  | `notebook-only` | no | Notebook panchromatic support export has no direct app output yet. |
| `PAN_S2_Panchromatic_10m_640.npy` | `OPT/PAN_NPY_640/PAN_S2_Panchromatic_10m_640.npy` |  | `notebook-only` | no | Notebook panchromatic support export has no direct app output yet. |
| `PAN_LS_Panchromatic_640.tif` | `OPT/PAN_TIFS_640/PAN_LS_Panchromatic_640.tif` |  | `notebook-only` | no | Notebook panchromatic support export has no direct app output yet. |
| `PAN_S2_Panchromatic_10m_640.tif` | `OPT/PAN_TIFS_640/PAN_S2_Panchromatic_10m_640.tif` |  | `notebook-only` | no | Notebook panchromatic support export has no direct app output yet. |
| `AI_*` QA series | `QA/AI_*` |  | `notebook-only` | no | Notebook AI/hard-decision QA files are not present in the current app run. |
| `FOCUS_MASK_17m_inside_640.tif` | `QA/FOCUS_MASK_17m_inside_640.tif` | `full_job/focus/focus_zone_17m.tif` | `renamed-equivalent` | no | App focus mask is stored under `full_job/focus/`. |
| `FOCUS_MASK_17m_inside_640.json` | `QA/FOCUS_MASK_17m_inside_640.json` | `full_job/focus/focus_zone_summary.json` | `intentionally-different` | no | App writes a focus summary JSON rather than the notebook's companion JSON shape. |
| `QA_GRID_dx_m_640.tif` | `QA/QA_GRID_dx_m_640.tif` |  | `missing-in-app` | no | Grid QA raster is not written by the app run. |
| `QA_GRID_dy_m_640.tif` | `QA/QA_GRID_dy_m_640.tif` |  | `missing-in-app` | no | Grid QA raster is not written by the app run. |
| `QA_GRID_validmask_640.tif` | `QA/QA_GRID_validmask_640.tif` |  | `missing-in-app` | no | Grid QA raster is not written by the app run. |
| `QA_RADAR_CELL25_PAIR_IDS_<pair_stamp>.json` | `QA/QA_RADAR_CELL25_PAIR_IDS_<pair_stamp>.json` | `qa/sar/sar_pair_diagnostics.json` | `intentionally-different` | no | Pair IDs are tracked inside the app SAR diagnostics rather than a dedicated notebook file. |
| `QA_S1_MASTER_UNITS.json` | `QA/QA_S1_MASTER_UNITS.json` | `qa/sar/sar_pair_diagnostics.json` | `intentionally-different` | no | MASTER and pairs-used provenance is folded into app SAR diagnostics instead of a notebook-style standalone file. |
| `QA_RADAR_META_<radar_stamp>_<radar_config>.json` | `QA/QA_RADAR_META_<radar_stamp>_<radar_config>.json` | `qa/sar/sar_pair_diagnostics.json` | `intentionally-different` | no | App stores SAR provenance and pairing diagnostics in a differently structured QA file. |
| `SUMMARY_RADAR_<radar_stamp>_<radar_config>.csv` | `QA/SUMMARY_RADAR_<radar_stamp>_<radar_config>.csv` | `qa/sar/sar_summary.csv` | `renamed-equivalent` | no | App SAR summary is in `qa/sar/` with a generic filename. |
| `RUN_MANIFEST.json` | `QA/RUN_MANIFEST.json` |  | `missing-in-app` | no | App has no notebook-style `RUN_MANIFEST.json`; it uses `grid_manifest.json`, `run_status_history.json`, and `stage_*.manifest.json`. |
| `per_image_products_db` arrays | `QA/sar/intermediates/per_image_products_db/pair{0..3}_{asc|desc}_{VV_dB|VH_dB|angle}.npy` |  | `missing-in-app` | no | 24 notebook SAR intermediate arrays were not found in the fresh app run. |
| `pair_median` arrays | `QA/sar/intermediates/pair_median/pair{0..3}_{VV_dB|VH_dB|angle}.npy` |  | `missing-in-app` | no | 12 notebook SAR intermediate arrays were not found in the fresh app run. |
| `final_median_pre_rtc` arrays | `QA/sar/intermediates/final_median_pre_rtc/final_{VV_dB|VH_dB|angle}.npy` |  | `missing-in-app` | no | 3 notebook SAR intermediate arrays were not found in the fresh app run. |
| `post_sample_pre_rtc` arrays | `QA/sar/intermediates/post_sample_pre_rtc/final_{VV_dB|VH_dB|angle}.npy` |  | `missing-in-app` | no | 3 notebook SAR intermediate arrays were not found in the fresh app run. |
| `post_rtc` arrays | `QA/sar/intermediates/post_rtc/final_{VV_dB|VH_dB|logRatio_dB|angle}.npy` | `npy_radar_bands/{VV_dB|VH_dB|logRatio_dB|incidence}.npy` | `matched-via-alias` | no | Persisted by the SAR stage as byte-equal copies of the canonical final SAR arrays under `npy_radar_bands/`; see `sar_intermediate_manifest.json#stages.post_rtc.source_mapping`. |
| `sar_intermediate_manifest.json` | `QA/sar/intermediates/sar_intermediate_manifest.json` |  | `missing-in-app` | no | This fresh app run did not export the notebook-style SAR intermediate manifest. |
| empty notebook `SAR/` folder | `SAR/` |  | `intentionally-different` | no | Empty notebook folder is not reproduced by the app run. |
| empty notebook `THERM/` folder | `THERM/` |  | `intentionally-different` | no | Empty notebook folder is not reproduced by the app run. |

## Missing Notebook Outputs In App

Phase 1 gaps that are clearly absent from the fresh app run:

- `REPORT_640_Pottery_Report.tif`
- `REPORT_640_Mass_Report.tif`
- `REPORT_640_FINAL_Zero_Point_Targets.tif`
- `DEM_GEO8_TIFS/hillshade_0to1_640.tif`
- `QA/QA_GRID_dx_m_640.tif`
- `QA/QA_GRID_dy_m_640.tif`
- `QA/QA_GRID_validmask_640.tif`
- `QA/RUN_MANIFEST.json`
- `QA/sar/intermediates/sar_intermediate_manifest.json`
- all notebook SAR intermediate arrays under `QA/sar/intermediates/`

## App-Only Outputs

Current app outputs that have no direct notebook file counterpart in the reference bundle include:

- `objects_index.csv`
- `clusters_summary.csv`
- `alignment_qa.json`
- `alignment_audit.csv`
- `alignment_mask_selection.json`
- `grid_manifest.json`
- `run_status_history.json`
- `stage_*.manifest.json`
- root spectral-index rasters: `NDVI.tif`, `NDWI.tif`, `NDMI.tif`, `NBR.tif`, `IRONOX.tif`, `IRON_SWIR.tif`, `BSI.tif`
- root terrain outputs not present in the frozen notebook set: `TRI.tif`, `TWI.tif`
- `lst.tif`
- tensor support stacks under `stacks/tensor_support/`
- optical support mask under `stacks/optical_support/`
- field-op, GPS, focus, and KMZ support outputs under `full_job/` and `kmz/`
- `objects/object_mask.npy`
- `objects/object_patches/*.npy` (2318 patch arrays in this fresh run)

Note: the local app run currently writes `alignment_audit.csv`, while the UI artifact naming work has been using the logical artifact name `alignment_audit`.

## Renamed Or Equivalent Outputs

Notebook-to-app path equivalences identified in this inventory:

- `DEM_GEO8_TIFS/DEM_640.tif` -> `dem.tif`
- `DEM_GEO8_TIFS/slope_deg_640.tif` -> `slope.tif`
- `DEM_GEO8_TIFS/aspect_deg_640.tif` -> `aspect.tif`
- `DEM_GEO8_TIFS/roughness_100m_640.tif` -> `roughness.tif`
- `DEM_GEO8_TIFS/tpi_100m_640.tif` -> `TPI.tif`
- `GEOTIFF_RADAR_BANDS/RADAR_VV_dB_640_<radar_stamp>_<radar_config>.tif` -> `VV_dB.tif`
- `GEOTIFF_RADAR_BANDS/RADAR_VH_dB_640_<radar_stamp>_<radar_config>.tif` -> `VH_dB.tif`
- `GEOTIFF_RADAR_BANDS/RADAR_logRatio_dB_640_<radar_stamp>_<radar_config>.tif` -> `logRatio_dB.tif`
- `GEOTIFF_RADAR_BANDS/RADAR_angle_640_<radar_stamp>_<radar_config>.tif` -> `incidence.tif`
- `NPY_RADAR_BANDS/RADAR_VV_dB_640_<radar_stamp>_<radar_config>.npy` -> `npy_radar_bands/VV_dB.npy`
- `NPY_RADAR_BANDS/RADAR_VH_dB_640_<radar_stamp>_<radar_config>.npy` -> `npy_radar_bands/VH_dB.npy`
- `NPY_RADAR_BANDS/RADAR_logRatio_dB_640_<radar_stamp>_<radar_config>.npy` -> `npy_radar_bands/logRatio_dB.npy`
- `NPY_RADAR_BANDS/RADAR_angle_640_<radar_stamp>_<radar_config>.npy` -> `npy_radar_bands/incidence.npy`
- `NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE.npy` -> `hypercube.npy`
- `NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE.tif` -> `hypercube.tif`
- `NPY_STACKS/RADAR_STACK_HWC_640_<radar_stamp>_<radar_config>.npy` -> `stacks/tensor_support/radar_linear_support_stack.npy`
- `QA/FOCUS_MASK_17m_inside_640.tif` -> `full_job/focus/focus_zone_17m.tif`
- `QA/SUMMARY_RADAR_<radar_stamp>_<radar_config>.csv` -> `qa/sar/sar_summary.csv`

## Outputs Needing Content Parity Checks

Phase 1 does not check values. The following equivalents still need content-level parity work later:

- `dem.tif`
- `slope.tif`
- `aspect.tif`
- `roughness.tif`
- `TPI.tif`
- `VV_dB.tif`
- `VH_dB.tif`
- `logRatio_dB.tif`
- `incidence.tif`
- `npy_radar_bands/VV_dB.npy`
- `npy_radar_bands/VH_dB.npy`
- `npy_radar_bands/logRatio_dB.npy`
- `npy_radar_bands/incidence.npy`
- `hypercube.tif`
- `hypercube.npy`
- `stacks/tensor_support/radar_linear_support_stack.npy`
- `full_job/focus/focus_zone_17m.tif`
- `qa/sar/sar_summary.csv`
- `qa/sar/sar_pair_diagnostics.json`

## Immediate Goal-A Findings

- The fresh app run completes end to end, but its local folder shape still differs materially from the notebook output tree.
- The three top-level notebook report TIFFs are missing.
- There is no notebook-style `RUN_MANIFEST.json` in the app run.
- Core DEM and SAR outputs do exist, but they are currently renamed and re-foldered.
- The frozen notebook reference contains a large QA/intermediate footprint that this fresh app run does not reproduce.
- The app currently produces many operator-local extras that are not represented in the notebook reference tree.

## Post Phase 3A-3F Audit

Audit date: `2026-05-26`

Fresh app run ID: `2ed977ce-8ded-42d8-9ea0-5fafdee9547a`

Absolute local paths are intentionally omitted. The inventory below uses run-relative paths only.

QA casing verification run ID: `86b6c713-21c6-4ece-8f43-0397ad0f7be2`

The QA casing blocker found in the initial Post Phase 3A-3F audit is resolved by commit `04287a0` (`Canonicalize notebook QA output folder casing`). `QA/` is now the canonical notebook-compatible folder, lowercase `qa/` is no longer produced as a separate top-level folder, and notebook-compatible QA outputs land under `QA/`.

### Fresh Run Summary

| Inventory | Count |
|---|---:|
| App run files | 644 |
| App run directories | 24 |

Top-level output groups observed:

- `DEM_GEO8_TIFS/`
- `GEOTIFF_RADAR_BANDS/`
- `NPY_RADAR_BANDS/`
- `NPY_STACKS/`
- `full_job/`
- `kmz/`
- `npy_radar_bands/`
- `objects/`
- `QA/`
- `stacks/`

### Newly Matched Notebook-Compatible Outputs

These outputs were missing or renamed-only in the Phase 1 inventory and now exist in the fresh app run under notebook-compatible names or patterns:

| Notebook-compatible output | Status | Notes |
|---|---|---|
| `DEM_GEO8_TIFS/DEM_640.tif` | `matched` | Notebook-compatible DEM alias exists. |
| `DEM_GEO8_TIFS/slope_deg_640.tif` | `matched` | Notebook-compatible slope alias exists. |
| `DEM_GEO8_TIFS/aspect_deg_640.tif` | `matched` | Notebook-compatible aspect alias exists. |
| `DEM_GEO8_TIFS/roughness_100m_640.tif` | `matched` | Notebook-compatible roughness alias exists. |
| `DEM_GEO8_TIFS/tpi_100m_640.tif` | `matched` | Notebook-compatible TPI alias exists. |
| `DEM_GEO8_TIFS/hillshade_0to1_640.tif` | `matched` | Hillshade output exists. |
| `GEOTIFF_RADAR_BANDS/RADAR_angle_640_*.tif` | `matched` | Notebook-compatible SAR angle GeoTIFF exists. |
| `GEOTIFF_RADAR_BANDS/RADAR_logRatio_dB_640_*.tif` | `matched` | Notebook-compatible SAR log-ratio GeoTIFF exists. |
| `GEOTIFF_RADAR_BANDS/RADAR_VH_dB_640_*.tif` | `matched` | Notebook-compatible SAR VH GeoTIFF exists. |
| `GEOTIFF_RADAR_BANDS/RADAR_VV_dB_640_*.tif` | `matched` | Notebook-compatible SAR VV GeoTIFF exists. |
| `NPY_RADAR_BANDS/RADAR_angle_640_*.npy` | `matched` | Notebook-compatible SAR angle NPY exists. |
| `NPY_RADAR_BANDS/RADAR_logRatio_dB_640_*.npy` | `matched` | Notebook-compatible SAR log-ratio NPY exists. |
| `NPY_RADAR_BANDS/RADAR_VH_dB_640_*.npy` | `matched` | Notebook-compatible SAR VH NPY exists. |
| `NPY_RADAR_BANDS/RADAR_VV_dB_640_*.npy` | `matched` | Notebook-compatible SAR VV NPY exists. |
| `NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE.tif` | `matched` | Notebook-compatible hypercube GeoTIFF exists. |
| `NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE.npy` | `matched` | Notebook-compatible hypercube NPY exists. |
| `NPY_STACKS/RADAR_STACK_HWC_640_*.npy` | `matched` | Notebook-compatible radar stack NPY exists. |
| `QA/QA_GRID_dx_m_640.tif` | `matched` | File exists under canonical uppercase `QA/`. |
| `QA/QA_GRID_dy_m_640.tif` | `matched` | File exists under canonical uppercase `QA/`. |
| `QA/QA_GRID_validmask_640.tif` | `matched` | File exists under canonical uppercase `QA/`. |
| `QA/RUN_MANIFEST.json` | `matched` | Manifest exists under canonical uppercase `QA/`. |
| `QA/sar/intermediates/sar_intermediate_manifest.json` | `matched` | Manifest exists under canonical uppercase `QA/`. |
| `QA/sar/intermediates/post_rtc/final_VV_dB.npy` | `matched` | Post-RTC SAR intermediate is a byte-equal copy of `npy_radar_bands/VV_dB.npy`. |
| `QA/sar/intermediates/post_rtc/final_VH_dB.npy` | `matched` | Post-RTC SAR intermediate is a byte-equal copy of `npy_radar_bands/VH_dB.npy`. |
| `QA/sar/intermediates/post_rtc/final_logRatio_dB.npy` | `matched` | Post-RTC SAR intermediate is a byte-equal copy of `npy_radar_bands/logRatio_dB.npy`. |
| `QA/sar/intermediates/post_rtc/final_angle.npy` | `matched` | Post-RTC SAR intermediate is a byte-equal copy of `npy_radar_bands/incidence.npy`. |

### Remaining Missing Notebook Outputs

These contract or notebook-reference outputs remain absent as real notebook-compatible outputs:

| Notebook output | Status | Notes |
|---|---|---|
| `QA/FOCUS_MASK_17m_inside_640.tif` | `renamed-equivalent-only` | App equivalent remains `full_job/focus/focus_zone_17m.tif`; no notebook-compatible QA alias was emitted in Phase 3. |
| `QA/SUMMARY_RADAR_*.csv` | `renamed-equivalent-only` | App equivalent remains `qa/sar/sar_summary.csv`; no notebook-compatible QA alias was emitted in Phase 3. |
| `QA/sar/intermediates/per_image_products_db/*.npy` | `not_implemented_no_source_equivalent` | Manifest records that production SAR does not persist this notebook intermediate. |
| `QA/sar/intermediates/pair_median/*.npy` | `not_implemented_no_source_equivalent` | Manifest records that production SAR does not persist this notebook intermediate. |
| `QA/sar/intermediates/final_median_pre_rtc/*.npy` | `not_implemented_no_source_equivalent` | Manifest records that production SAR does not persist this notebook intermediate. |
| `QA/sar/intermediates/post_sample_pre_rtc/*.npy` | `not_implemented_no_source_equivalent` | Manifest records that production SAR does not persist this notebook intermediate. |

### Intentionally Not Implemented Or No-Source Outputs

- Pre-RTC SAR intermediate stages are not reconstructed from final products. `QA/sar/intermediates/sar_intermediate_manifest.json` records the missing notebook stages as `not_implemented_no_source_equivalent`.

### App-Only Outputs Still Preserved

The fresh run still preserves app-only outputs, including:

- `objects_index.csv`
- `clusters_summary.csv`
- `alignment_qa.json`
- `alignment_audit.csv`
- `alignment_mask_selection.json`
- `grid_manifest.json`
- `run_status_history.json`
- `stage_*.manifest.json`
- Sentinel-2 index rasters
- `TRI.tif`
- `TWI.tif`
- `lst.tif`
- `full_job/*`
- `kmz/*`
- `objects/object_mask.npy`
- object patch arrays

### QA Casing Resolution

The notebook contract expects uppercase `QA/` paths. The original Post Phase 3A-3F audit found that notebook-compatible QA outputs resolved into an existing lowercase `qa/` folder on Windows.

This is now fixed. Verification run `86b6c713-21c6-4ece-8f43-0397ad0f7be2` completed `done`, the physical top-level folder is `QA/`, and there is no separate lowercase `qa/` top-level folder.

Notebook-compatible QA outputs now land under:

- `QA/QA_GRID_dx_m_640.tif`
- `QA/QA_GRID_dy_m_640.tif`
- `QA/QA_GRID_validmask_640.tif`
- `QA/RUN_MANIFEST.json`
- `QA/sar/intermediates/sar_intermediate_manifest.json`
- `QA/sar/intermediates/post_rtc/*.npy`
- `QA/REPORT_640_manifest.json`

No pipeline or GRID behavior was changed during this audit.
