# Plan B — Implement Not-Done Notebook Features In The App

Status: active implementation document.

Last update: 2026-06-22 — B1 item 9 fourth stack family implemented; frozen notebook numeric parity still pending.

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
| 9 | More feature stacks / rename layers | 🟨 Partial | Yes | Implemented so far: cell 050 RAD_S0_MASTER_STACK_640, cell 053 RAD_MASTER_CUBE_640, cell 051 GPHYS_MASTER_STACK_640, and cell 047 MASTER_RTC_REFINED_STACK_640. Remaining item #9 stack families still pending. Frozen notebook numeric parity still pending. |
| 15 | Bonus / simulator features | 🟥 No | Yes | Optional/private stage unless specifically required by target pipeline. |
| 17 | Extra S2 era pulls / masks | 🟥 No | Yes | Add historical/seasonal S2 pull stage using notebook date/cloud rules. |
| 18 | DEM-matched S2 masks | 🟥 No | Yes | Add or extend S2 mask products so they align to the DEM/grid contract. |
| 19 | Tesla v7.2 inference engines | 🟥 No | Yes | Major missing feature. Select one authoritative Tesla cell/version before implementation. |
| 20 | Fusion center / intelligence tensors | 🟥 No | Yes | Requires base layers and named tensor formulas. Should follow stack/mask completion. |
| 23 | ROI-constrained AI analysis inside 17m focus | 🟥 No | Yes | Use the app focus window, then port the notebook's focus-region analysis logic. |
| 24 | Hard classifiers / target type rules | 🟥 No | Yes | Need clean rule specification from the final notebook classifier cells. |
| 25 | Target CSV / TXT / JSON outputs | 🟥 No | Yes | Define final target schema: columns, labels, confidence fields, and local/private policy. |
| 26 | GeoJSON detected-feature exports | 🟥 No | Yes | Generate after final target schema and detections exist. Should be private/local by default. |
| 27 | KMZ heatmap / 3D target visualization | 🟥 No | Yes | Depends on final target detections. Should be private/local by default. |
| 28 | AI requirements mapper for YOLO/CNN/Swin | 🟥 No | Yes | Planning/inspection feature. Easier than actual inference. |
| 29 | AI tensor builder for YOLO/CNN/Swin/SegFormer | 🟥 No | Yes | Define input shape, band order, normalization, and saved tensor contract. |
| 30 | Training / learn weights cells | 🟥 No | Yes, separate | Build as a separate training workflow, not a normal app run stage. |
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

### B1.2 result — item 9 More feature stacks / rename layers, RAD_S0 stack family

```text
Status:
  App port implemented.
  Frozen notebook numeric parity is still pending.

Canonical notebook variant selected:
  cell_050 -> RAD_S0_MASTER_STACK_640.npy

Implemented app outputs:
  NPY_STACKS/RAD_S0_MASTER_STACK_640.npy
  NPY_RADAR_BANDS/{6 RAD_S0 bands}_640.npy
  GEOTIFF_RADAR_BANDS/{6 RAD_S0 bands}_640.tif
  GEOTIFF_RADAR_BANDS/{6 RAD_S0 bands}_640.tif.meta.json
  NPY_STACKS/STACK_ALIAS_MANIFEST.json entry for source_cell cell_050

Implemented band order:
  RAD_S0_VV_dB
  RAD_S0_VH_dB
  RAD_S0_VV_Med1p5px_dB
  RAD_S0_VH_Med1p5px_dB
  RAD_S0_VH_VV_Ratio_lin
  RAD_S0_Angle_deg

Validation done:
  focused feature stack test passed.
  full-run integration test passed.
  local existing run regenerated and confirmed output files/shapes exist.
  RAD_S0 stack shape confirmed as (640, 640, 6) float32.
  STACK_ALIAS_MANIFEST records source_cell cell_050 and status implemented.
```

### B1.3 result — item 9 More feature stacks / rename layers, Radar Master Cube family

```text
Status:
  App port implemented.
  Frozen notebook numeric parity is still pending.

Canonical notebook variant selected:
  cell_053 -> RAD_MASTER_CUBE_640.npy

Implemented app outputs:
  NPY_STACKS/RAD_MASTER_CUBE_640.npy
  NPY_RADAR_BANDS/RADM_VV_dB_640.npy
  NPY_RADAR_BANDS/RADM_VH_dB_640.npy
  NPY_RADAR_BANDS/RADM_VV_Med1p5px_dB_640.npy
  NPY_RADAR_BANDS/RADM_VV_Mean1p5px_dB_640.npy
  NPY_RADAR_BANDS/RADM_VH_VV_Ratio_lin_640.npy
  GEOTIFF_RADAR_BANDS/{5 RADM bands}_640.tif
  GEOTIFF_RADAR_BANDS/{5 RADM bands}_640.tif.meta.json
  NPY_STACKS/STACK_ALIAS_MANIFEST.json entry for source_cell cell_053

Implemented band order:
  RADM_VV_dB
  RADM_VH_dB
  RADM_VV_Med1p5px_dB
  RADM_VV_Mean1p5px_dB
  RADM_VH_VV_Ratio_lin

Validation done:
  focused feature stack test passed.
  full-run integration test passed.
  local existing run regenerated and confirmed output files/shapes exist.
  RAD_MASTER_CUBE stack shape confirmed as (640, 640, 5) float32.
  STACK_ALIAS_MANIFEST records source_cell cell_053 and status implemented.
```

### B1.4 result — item 9 More feature stacks / rename layers, GPHYS Master family

```text
Status:
  App port implemented.
  Frozen notebook numeric parity is still pending.

Canonical notebook variant selected:
  cell_051 -> GPHYS_MASTER_STACK_640.npy

Implemented app outputs:
  NPY_STACKS/GPHYS_MASTER_STACK_640.npy
  NPY_RADAR_BANDS/GPHYS_VV_dB_640.npy
  NPY_RADAR_BANDS/GPHYS_VH_dB_640.npy
  NPY_RADAR_BANDS/GPHYS_VV_Med1p5px_dB_640.npy
  NPY_RADAR_BANDS/GPHYS_VH_Med1p5px_dB_640.npy
  NPY_RADAR_BANDS/GPHYS_VV_SigmaMean1p5px_dB_640.npy
  NPY_RADAR_BANDS/GPHYS_VH_SigmaMean1p5px_dB_640.npy
  GEOTIFF_RADAR_BANDS/{6 GPHYS bands}_640.tif
  GEOTIFF_RADAR_BANDS/{6 GPHYS bands}_640.tif.meta.json
  NPY_STACKS/STACK_ALIAS_MANIFEST.json entry for source_cell cell_051

Implemented band order:
  GPHYS_VV_dB
  GPHYS_VH_dB
  GPHYS_VV_Med1p5px_dB
  GPHYS_VH_Med1p5px_dB
  GPHYS_VV_SigmaMean1p5px_dB
  GPHYS_VH_SigmaMean1p5px_dB

Validation done:
  focused feature stack test passed.
  full-run integration test passed.
  local existing run regenerated and confirmed output files/shapes exist.
  GPHYS_MASTER stack shape confirmed as (640, 640, 6) float32.
  STACK_ALIAS_MANIFEST records source_cell cell_051 and status implemented.
```

### B1.5 result — item 9 More feature stacks / rename layers, Master RTC Refined family

```text
Status:
  App port implemented.
  Frozen notebook numeric parity is still pending.

Canonical notebook variant selected:
  cell_047 -> MASTER_RTC_REFINED_STACK_640.npy

Implemented app outputs:
  NPY_STACKS/MASTER_RTC_REFINED_STACK_640.npy
  NPY_RADAR_BANDS/RAD_MasterVV_dB_640.npy
  NPY_RADAR_BANDS/RAD_MasterVH_dB_640.npy
  NPY_RADAR_BANDS/RAD_MasterAngle_deg_640.npy
  NPY_RADAR_BANDS/RAD_MasterVV_Median3m_dB_640.npy
  NPY_RADAR_BANDS/RAD_MasterVH_Median3m_dB_640.npy
  NPY_RADAR_BANDS/RAD_MasterVH_VV_Ratio_lin_640.npy
  GEOTIFF_RADAR_BANDS/{6 RAD_Master bands}_640.tif
  GEOTIFF_RADAR_BANDS/{6 RAD_Master bands}_640.tif.meta.json
  NPY_STACKS/STACK_ALIAS_MANIFEST.json entry for source_cell cell_047

Implemented band order:
  RAD_MasterVV_dB
  RAD_MasterVH_dB
  RAD_MasterAngle_deg
  RAD_MasterVV_Median3m_dB
  RAD_MasterVH_Median3m_dB
  RAD_MasterVH_VV_Ratio_lin

Implementation choice:
  Use existing app SAR arrays VV_dB, VH_dB, and incidence from npy_radar_bands.
  Compute the Master RTC Refined stack locally in FeatureStacksStage.
  Do not add another Earth Engine sampling stage for this stack family.

Validation done:
  focused feature stack test passed.
  full-run integration test passed.
  local existing run regenerated and confirmed output files/shapes exist.
  MASTER_RTC_REFINED stack shape confirmed as (640, 640, 6) float32.
  STACK_ALIAS_MANIFEST records source_cell cell_047 and status implemented.

Remaining item #9 families:
  cell_052 -> ARCH_TARGETS_STACK_640.npy
  cell_054 -> ULTIMATE_GPHYS_SCAN_640.npy

Remaining validation:
  Run a fresh UI/orchestrator run so DB artifact registration includes the new B1.5 artifacts.
  Compare against frozen notebook outputs after reference files are selected/generated.
```

### Next main item scan after B1.5

```text
Recommended next main item:
  Continue item #9 with the next stack-family target.

Candidate order:
  1. cell_052 -> ARCH_TARGETS_STACK_640.npy
  2. cell_054 -> ULTIMATE_GPHYS_SCAN_640.npy

Next action:
  Inspect exact formula requirements for cell_052 against current app arrays.
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
