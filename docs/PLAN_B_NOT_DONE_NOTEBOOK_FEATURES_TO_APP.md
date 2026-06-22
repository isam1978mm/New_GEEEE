# Plan B — Implement Not-Done Notebook Features In The App

Status: active implementation document.

Last update: 2026-06-22 — B1 item 8 app port implemented; frozen notebook numeric parity still pending.

Goal: after Plan A completes the partial notebook features, implement the notebook capabilities that are not done in the app now. These are real product capabilities from the notebook, not Colab/Drive setup behavior.

This document uses the notebook phase inventory as the source of scope. It does not claim these features are already implemented.

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
| 9 | More feature stacks / rename layers | 🟥 No | Yes | Define output layer names and contracts, then add missing writers. |
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

Skipped for first B1 implementation:
  cell_036 -> duplicate/older Nano variant
  cell_044 -> explicitly experimental ALT variant
  cell_051 -> later Geophysical Master stack
  cell_054 -> later Ultimate Geophysical Scan

Implemented app outputs:
  NPY_STACKS/NANO_GEOPHYSICS_STACK_640.npy
  NPY_STACKS/TREASURE_GEOPHYSICS_STACK_640.npy
  NPY_RADAR_BANDS/{7 Plan B B1 bands}_640.npy
  GEOTIFF_RADAR_BANDS/{7 Plan B B1 bands}_640.tif
  GEOTIFF_RADAR_BANDS/{7 Plan B B1 bands}_640.tif.meta.json
  NPY_STACKS/STACK_ALIAS_MANIFEST.json entries for source_cell cell_037 and cell_039

Implementation choice:
  Use existing app SAR arrays VV_dB and VH_dB from npy_radar_bands.
  Do not add another Earth Engine sampling stage for these formulas.

Validation done:
  feature_stacks syntax check passed.
  focused feature stack tests passed.
  related SAR/alignment/runs API checks passed.
  full-run integration test passed.
  local existing run regenerated and confirmed output files/shapes exist.

Remaining:
  Run a fresh UI/orchestrator run so DB artifact registration includes the new B1 artifacts.
  Compare against frozen notebook outputs after reference files are selected/generated.
```

### Next main item scan after B1.1

```text
Recommended next main item:
  #9 More feature stacks / rename layers

Why:
  #8 now has an app implementation and local output proof.
  #9 is the next item in B1 and affects naming/contracts for later fusion and ML tensors.
  #15 bonus/simulator is optional.
  #17/#18 S2-era/mask work should come after stack naming/contracts are clean.
  #20 fusion/intelligence tensors should come after the stack family and rename contracts are stable.

Next action:
  Inspect exact notebook cells for item #9.
  Compare current app stack aliases, band names, and output folders.
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
