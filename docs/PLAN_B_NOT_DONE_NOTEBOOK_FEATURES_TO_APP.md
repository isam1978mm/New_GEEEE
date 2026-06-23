# Plan B — Implement Not-Done Notebook Features In The App

Status: active implementation document.

Last update: 2026-06-22 — B1 item 20 fusion intelligence stack implemented; frozen notebook numeric parity still pending.

Goal: after Plan A completes the partial notebook features, implement the notebook capabilities that are not done in the app now. These are real product capabilities from the notebook, not Colab/Drive setup behavior.

This document uses the notebook phase inventory as the source of scope. It does not claim these features are already fully validated against frozen notebook output.

## Meaning of columns

```text
Is it done now?
  🟩 Yes = complete enough in the app now
  🟨 Partial = some app coverage exists, but notebook capability is not fully reproduced
  🟥 No = not implemented as an app feature yet
  ⬜ Not needed = notebook/Colab-only behavior; app should replace or skip it

Can we make it in app?
  Yes = implement as app stage, service, UI feature, local/private output, or separate training workflow
  Replace = do not copy the notebook method; implement the app equivalent
```

## Plan B scope: not-done-now items

| # | Not-done-now notebook item | Is it done now? | Can we make it in app? | Plan B note |
|---:|---|---|---:|---|
| 8 | Nano / treasure / geophysics stacks | 🟨 Partial | Yes | App port implemented for canonical cell 037 Nano stack and cell 039 Treasure/Geophysics stack. Outputs and tests pass. Frozen notebook numeric parity still pending. |
| 9 | More feature stacks / rename layers | 🟨 Partial | Yes | App port implemented for selected stack families: cell 050 RAD_S0_MASTER_STACK_640, cell 053 RAD_MASTER_CUBE_640, cell 051 GPHYS_MASTER_STACK_640, cell 047 MASTER_RTC_REFINED_STACK_640, cell 052 ARCH_TARGETS_STACK_640, and cell 054 ULTIMATE_GPHYS_SCAN_640. Frozen notebook numeric parity still pending. |
| 15 | Bonus / simulator features | 🟨 Partial | Yes | App port implemented for cell 072 AUX_BONUS_FEATURES_STACK_640 and cell 073 SIM_GEOPHYSICAL_STACK_640. Outputs and tests pass. Frozen notebook numeric parity still pending. |
| 17 | Extra S2 era pulls / masks | 🟨 Partial | Yes | App port implemented for canonical cell 077 AIX_2022_2026_CLOUDLT3_EXTRA_TENSORS_STACK_640. Outputs and tests pass. Frozen notebook numeric parity still pending. |
| 18 | DEM-matched S2 masks | 🟨 Partial | Yes | App port implemented for canonical cell 081 AIX_2022_2026FEB_CLOUDLT3_DEM_MATCHED_MASKS_STACK_640. Outputs and tests pass. Frozen notebook numeric parity still pending. |
| 19 | Tesla v7.2 inference engines | 🟥 No | Yes | Major missing feature. Select one authoritative Tesla cell/version before implementation. |
| 20 | Fusion center / intelligence tensors | 🟨 Partial | Yes | App port implemented for canonical cell 099 REPORT_640_FINAL_INTELLIGENCE_STACK_640. Outputs and tests pass. Frozen notebook numeric parity still pending. |
| 23 | ROI-constrained AI analysis inside 17m focus | 🟥 No | Yes | Use the app focus window, then port the notebook's focus-region analysis logic. |
| 24 | Hard classifiers / target type rules | 🟥 No | Yes | Need clean rule specification from the final notebook classifier cells. |
| 25 | Target CSV / TXT / JSON outputs | 🟥 No | Yes | Define final target schema: columns, labels, confidence fields, and local/private policy. |
| 26 | GeoJSON detected-feature exports | 🟥 No | Yes | Generate after final target schema and detections exist. Should be private/local by default. |
| 27 | KMZ heatmap / 3D target visualization | 🟥 No | Yes | Depends on final target detections. Should be private/local by default. |
| 28 | AI requirements mapper for YOLO/CNN/Swin | 🟥 No | Yes | Planning/inspection feature. Easier than actual inference. |
| 29 | AI tensor builder for YOLO/CNN/Swin/SegFormer | 🟥 No | Yes | Define input shape, band order, normalization, and saved tensor contract. |
| 30 | Training / learn weights cells | 🟥 No | Yes, separate | Build as a separate training workflow, not a normal app stage. |
| 31 | CNN / Unet++ / Swin / SegFormer model build | 🟥 No | Yes | Requires selected model, weights policy, dependency plan, and CPU/GPU expectations. |
| 32 | CNN final target inference | 🟥 No | Yes | Requires AI tensor builder and selected model first. |
| 33 | Metal fingerprint diagnostic | 🟥 No | Yes | Good candidate for private diagnostic app stage. |
| 34 | Field-operation KMZ outputs | 🟥 No | Yes | Depends on final target detections and geospatial output policy. |
| 38 | Live geemap overlays | 🟥 No | Replace | Do not port geemap. Build app-native map/layer UI. |
| 39 | Final probability map overlay + markers | 🟥 No | Yes | Depends on ML inference probability map output. |
| 40 | GPS/path tracing from targets | 🟥 No | Yes | Depends on final target detector outputs and geometry/privacy policy. |

## Plan B execution order

### B1 — Complete missing raster/tensor families

```text
Target items:
  8 Nano / treasure / geophysics stacks
  9 More feature stacks / rename layers
  15 Bonus / simulator features
  17 Extra S2 era pulls / masks
  18 DEM-matched S2 masks
  20 Fusion center / intelligence tensors

Outcome:
  all non-ML tensor/raster inputs required by the late notebook classifier phases exist in the app.
```

### B1.1 result — item 8 Nano / treasure / geophysics stacks

```text
Status:
  App port implemented.
  Frozen notebook numeric parity is still pending.

Canonical notebook variants selected:
  cell_037 -> NANO_GEOPHYSICS_STACK_640.npy
  cell_039 -> TREASURE_GEOPHYSICS_STACK_640.npy

Implemented app outputs:
  NPY_STACKS/NANO_GEOPHYSICS_STACK_640.npy
  NPY_STACKS/TREASURE_GEOPHYSICS_STACK_640.npy
  NPY_RADAR_BANDS/{7 Plan B B1 bands}_640.npy
  GEOTIFF_RADAR_BANDS/{7 Plan B B1 bands}_640.tif
  GEOTIFF_RADAR_BANDS/{7 Plan B B1 bands}_640.tif.meta.json
  NPY_STACKS/STACK_ALIAS_MANIFEST.json entries for source_cell cell_037 and cell_039

Remaining:
  Run a fresh UI/orchestrator run so DB artifact registration includes the new B1 artifacts.
  Compare against frozen notebook outputs after reference files are selected/generated.
```

### B1.2 through B1.7 result — item 9 More feature stacks / rename layers

```text
Status:
  App port implemented for the selected Phase G stack families.
  Frozen notebook numeric parity is still pending.

Canonical notebook variants selected:
  cell_050 -> RAD_S0_MASTER_STACK_640.npy
  cell_053 -> RAD_MASTER_CUBE_640.npy
  cell_051 -> GPHYS_MASTER_STACK_640.npy
  cell_047 -> MASTER_RTC_REFINED_STACK_640.npy
  cell_052 -> ARCH_TARGETS_STACK_640.npy
  cell_054 -> ULTIMATE_GPHYS_SCAN_640.npy

Validation done:
  focused feature stack tests passed.
  full-run integration tests passed.
  local existing run regenerated and confirmed output files/shapes exist.
  STACK_ALIAS_MANIFEST records selected source cells as implemented.

Remaining item #9 stack families:
  none identified in the selected Phase G set.
```

### B1.8 result — item 15 Bonus / simulator features

```text
Status:
  App port implemented.
  Frozen notebook numeric parity is still pending.

Canonical notebook variants selected:
  cell_072 -> AUX_BONUS_FEATURES_STACK_640.npy
  cell_073 -> SIM_GEOPHYSICAL_STACK_640.npy

Implemented app outputs:
  NPY_STACKS/AUX_BONUS_FEATURES_STACK_640.npy
  NPY_STACKS/SIM_GEOPHYSICAL_STACK_640.npy
  NPY_RADAR_BANDS/ENT_VV_LocalEntropy_w3_lin_640.npy
  NPY_RADAR_BANDS/AUX_OrbitalLogRatio_dB_640.npy
  NPY_RADAR_BANDS/AUX_VH_to_VV_MoistureProxy_lin_640.npy
  NPY_RADAR_BANDS/SIM_GPR_VoidScan_lin_640.npy
  NPY_RADAR_BANDS/SIM_MagneticAnomalies_lin_640.npy
  NPY_RADAR_BANDS/SIM_EMI_Conductivity_lin_640.npy
  NPY_RADAR_BANDS/SIM_MicroGravity_Density_lin_640.npy
  GEOTIFF_RADAR_BANDS/{7 item #15 bands}_640.tif
  GEOTIFF_RADAR_BANDS/{7 item #15 bands}_640.tif.meta.json
  NPY_STACKS/STACK_ALIAS_MANIFEST.json entries for source_cell cell_072 and cell_073

Validation done:
  focused feature stack test passed.
  full-run integration test passed.
  local existing run regenerated and confirmed output files/shapes exist.
  AUX_BONUS_FEATURES stack shape confirmed as (640, 640, 3) float32.
  SIM_GEOPHYSICAL stack shape confirmed as (640, 640, 4) float32.
```

### B1.9 result — item 17 Extra S2 era pulls / masks

```text
Status:
  App port implemented for the selected extra S2-era tensor stack.
  Frozen notebook numeric parity is still pending.

Canonical notebook variant selected:
  cell_077 -> AIX_2022_2026_CLOUDLT3_EXTRA_TENSORS_STACK_640.npy

Implemented app outputs:
  NPY_STACKS/AIX_2022_2026_CLOUDLT3_EXTRA_TENSORS_STACK_640.npy
  NPY_RADAR_BANDS/{13 AIX_2022_2026_CLOUDLT3 bands}_640.npy
  GEOTIFF_RADAR_BANDS/{13 AIX_2022_2026_CLOUDLT3 bands}_640.tif
  GEOTIFF_RADAR_BANDS/{13 AIX_2022_2026_CLOUDLT3 bands}_640.tif.meta.json
  NPY_STACKS/STACK_ALIAS_MANIFEST.json entry for source_cell cell_077

Implementation choice:
  Extend S2IndicesStage so the AIX stack is generated with the same run/grid contract as existing S2 outputs.
  In real backend mode, build seasonal S2/Landsat/topography tensors from the 2022-2026 cloud < 3 notebook rule.
  In deterministic/injected test mode, use a local deterministic AIX fetcher and do not call Earth Engine.
  Preserve the AIX alias in FeatureStacksStage so later stack rewrites keep the cell_077 manifest entry.

Validation done:
  focused S2 indices test passed.
  full-run integration test passed.
  local existing run regenerated and confirmed output files/shapes exist.
  AIX extra tensor stack shape confirmed as (640, 640, 13) float32.
  STACK_ALIAS_MANIFEST records source_cell cell_077 and status implemented.
```

### B1.10 result — item 18 DEM-matched S2 masks

```text
Status:
  App port implemented for the selected DEM-matched S2 mask stack.
  Frozen notebook numeric parity is still pending.

Canonical notebook variant selected:
  cell_081 -> AIX_2022_2026FEB_CLOUDLT3_DEM_MATCHED_MASKS_STACK_640.npy

Implemented app outputs:
  NPY_STACKS/AIX_2022_2026FEB_CLOUDLT3_DEM_MATCHED_MASKS_STACK_640.npy
  NPY_RADAR_BANDS/{9 AIX_2022_2026FEB_CLOUDLT3 bands}_640.npy
  GEOTIFF_RADAR_BANDS/{9 AIX_2022_2026FEB_CLOUDLT3 bands}_640.tif
  GEOTIFF_RADAR_BANDS/{9 AIX_2022_2026FEB_CLOUDLT3 bands}_640.tif.meta.json
  NPY_STACKS/STACK_ALIAS_MANIFEST.json entry for source_cell cell_081

Implemented band order:
  AIX_2022_2026FEB_CLOUDLT3_MaskVegetationRoots_Norm01
  AIX_2022_2026FEB_CLOUDLT3_MaskWaterMoisture_Norm01
  AIX_2022_2026FEB_CLOUDLT3_IndexIronOxide_Norm01
  AIX_2022_2026FEB_CLOUDLT3_IndexFerricIron_Norm01
  AIX_2022_2026FEB_CLOUDLT3_IndexClayThermal_Norm01
  AIX_2022_2026FEB_CLOUDLT3_MaskCharcoalLead_Norm01
  AIX_2022_2026FEB_CLOUDLT3_MaskQuartzBasalt_Norm01
  AIX_2022_2026FEB_CLOUDLT3_MaskCarbonate_Norm01
  AIX_2022_2026FEB_CLOUDLT3_ThermalTimeSeriesAnomaly_Norm01

Implementation choice:
  Extend S2IndicesStage so the DEM-matched mask stack is generated with the same run/grid contract as existing S2 outputs.
  Keep existing app raw/index valid masks; cell_081 is a separate 9-band AI mask/index stack, not a duplicate of those valid masks.
  In real backend mode, build the cell_081 S2/Landsat formulas from the 2022-01-01 to 2026-02-28 cloud < 3 notebook rule.
  In deterministic/injected test mode, use a local deterministic AIX mask fetcher and do not call Earth Engine.
  Preserve the cell_081 alias in FeatureStacksStage so later stack rewrites keep the manifest entry.

Validation done:
  focused S2 indices test passed.
  full-run integration test passed.
  local existing run regenerated and confirmed output files/shapes exist.
  AIX DEM-matched masks stack shape confirmed as (640, 640, 9) float32.
  STACK_ALIAS_MANIFEST records source_cell cell_081 and status implemented.
```

### B1.11 result — item 20 Fusion center / intelligence tensors

```text
Status:
  App port implemented for the selected final intelligence report stack.
  Frozen notebook numeric parity is still pending.

Canonical notebook variant selected:
  cell_099 -> REPORT_640_FINAL_INTELLIGENCE_STACK_640.npy

Implemented app outputs:
  NPY_STACKS/REPORT_640_FINAL_INTELLIGENCE_STACK_640.npy
  NPY_RADAR_BANDS/REPORT_640_FINAL_Zero_Point_Targets_640.npy
  NPY_RADAR_BANDS/REPORT_640_Mass_Report_640.npy
  NPY_RADAR_BANDS/REPORT_640_Pottery_Report_640.npy
  GEOTIFF_RADAR_BANDS/REPORT_640_FINAL_Zero_Point_Targets_640.tif
  GEOTIFF_RADAR_BANDS/REPORT_640_Mass_Report_640.tif
  GEOTIFF_RADAR_BANDS/REPORT_640_Pottery_Report_640.tif
  GEOTIFF_RADAR_BANDS/{3 REPORT_640 bands}_640.tif.meta.json
  NPY_STACKS/STACK_ALIAS_MANIFEST.json entry for source_cell cell_099

Implemented band order:
  REPORT_640_FINAL_Zero_Point_Targets
  REPORT_640_Mass_Report
  REPORT_640_Pottery_Report

Implementation choice:
  Use cell_099 as canonical instead of cell_097 because cell_099 is the DEM-anchored final reprojection variant.
  Extend S2IndicesStage so the fusion intelligence stack is generated with the same run/grid contract as existing S2 outputs.
  In real backend mode, build the cell_099 S2/Landsat formulas from the 2022-01-01 to 2026-02-28 notebook rule.
  In deterministic/injected test mode, use a local deterministic fusion fetcher and do not call Earth Engine.
  Preserve the cell_099 alias in FeatureStacksStage so later stack rewrites keep the manifest entry.

Validation done:
  focused S2 indices test passed.
  full-run integration test passed.
  local existing run regenerated and confirmed output files/shapes exist.
  REPORT_640 final intelligence stack shape confirmed as (640, 640, 3) float32.
  STACK_ALIAS_MANIFEST records source_cell cell_099 and status implemented.

Remaining validation:
  Run a fresh UI/orchestrator run so DB artifact registration includes the new B1.11 artifacts.
  Compare against frozen notebook outputs after reference files are selected/generated.
```

### Next main item scan after B1.11

```text
Recommended next main item:
  Move to Plan B item #19: Tesla v7.2 inference engines.

Why:
  The selected B1 non-ML raster/tensor families are now app-ported through item #20.
  Item #19 was intentionally skipped until the raster/tensor inputs were available because it is a major ML/inference item.
  Frozen notebook numeric parity remains pending for implemented B1 items.

Next action:
  Inspect exact notebook cell(s) for item #19 Tesla v7.2 inference engines.
  Select one authoritative Tesla v7.2 cell/version before implementation.
  Produce a gap table before coding.
```

### B2 — Focus-analysis and target-output contracts

```text
Target items:
  23 ROI-constrained AI analysis inside 17m focus
  24 Hard classifiers / target type rules
  25 Target CSV / TXT / JSON outputs
  26 GeoJSON detected-feature exports

Outcome:
  the app has a clear target schema and produces classifier-style target outputs.
```

### B3 — Local/private map and KMZ outputs

```text
Target items:
  27 KMZ heatmap / 3D target visualization
  34 Field-operation KMZ outputs
  38 Live geemap overlays, replaced by app-native map UI
  39 Final probability map overlay + markers
  40 GPS/path tracing from targets

Outcome:
  the app can generate local/private geospatial visualization products after detections exist.
```

### B4 — ML preparation and model inference

```text
Target items:
  28 AI requirements mapper for YOLO/CNN/Swin
  29 AI tensor builder for YOLO/CNN/Swin/SegFormer
  30 Training / learn weights workflow
  31 CNN / Unet++ / Swin / SegFormer model build
  32 CNN final target inference

Outcome:
  the app has a reproducible ML input and inference path, with training separated from normal runs.
```

### B5 — Diagnostics

```text
Target item:
  33 Metal fingerprint diagnostic

Outcome:
  app can run notebook-style metal-signature diagnostics as local/private analysis.
```

## Rules for Plan B

```text
1. Do not validate incomplete app behavior as if it equals notebook capability.
2. Pick one final notebook cell/variant for each feature before implementation.
3. Do not port duplicate, broken, or experimental attempts blindly.
4. Replace Colab/geemap/Drive behavior with app-native equivalents.
5. Define output names, artifact classes, and privacy policy before writing outputs.
6. Freeze notebook reference outputs for each feature after the final variant is selected.
7. Compare app outputs against those frozen notebook outputs after implementation.
8. Keep exact coordinates, target geometry, KMZs, and raw target outputs local/private unless a redacted public artifact is explicitly designed.
```

## Definition of done for each Plan B item

```text
[x] authoritative notebook cell/variant selected
[x] formulas/rules/model inputs extracted into a clean contract
[x] app stage/service/UI equivalent implemented
[x] output names and artifact classes defined
[x] local run output generated
[x] frozen notebook reference generated or selected
[x] app-vs-notebook comparison passes or documented exception is approved
[x] tests added
```

## Bottom line

```text
All not-done-now items can be made in the app.
They are not blocked by impossibility.
They require implementation, contract selection, and validation against frozen notebook outputs.
```
