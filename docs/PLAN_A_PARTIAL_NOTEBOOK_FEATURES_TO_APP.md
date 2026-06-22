# Plan A — Complete Partial Notebook Features In The App

Status: planning document.

Goal: before more parity work, complete the notebook features that are already partially present in the app. The app must copy the notebook purpose where it matters, while replacing Colab-only behavior with proper app/server behavior.

This document uses the notebook phase inventory as the source of scope. It does not claim the app already implements the full notebook AI/ML/classifier/KMZ system.

## Meaning of columns

```text
Is it done now?
  🟩 Yes = complete enough in the app now
  🟨 Partial = some app coverage exists, but notebook capability is not fully reproduced
  🟥 No = not implemented as an app feature yet
  ⬜ Not needed = notebook/Colab-only behavior; app should replace or skip it

Notebook-only?
  Yes = behavior depends on Colab/Drive/geemap/manual notebook workflow and should not be copied exactly
  No = real product capability that can exist in the app

Can we make it in app?
  Yes = implement as app stage, service, UI feature, or local/private output
  Replace = do not copy the notebook method; implement the app equivalent
```

## Plan A scope: partial items only

| # | Partial notebook item | Is it done now? | Does app do it now? | Notebook-only? | Can we make it in app? | Plan A action |
|---:|---|---|---:|---:|---:|---|
| 2 | Map point picker / ROI selection | 🟨 Partial | Partial | No | Yes | Add app-native map picker or coordinate-entry flow that creates the same ROI/grid contract as the notebook. |
| 7 | Pixel-alignment QA | 🟨 Partial | Partial | No | Yes | Port selected notebook pixel-alignment checks into app QA reports. |
| 8 | Nano / treasure / geophysics stacks | 🟨 Partial | Partial | No | Yes | Select the final notebook variant, freeze expected output names, port formulas, emit matching TIF/NPY/stack outputs. |
| 9 | More feature stacks / rename layers | 🟨 Partial | Partial | No | Yes | Define the final layer-name contract and add missing stack writers. |
| 11 | Auditor / geometry consistency QA | 🟨 Partial | Partial | No | Yes | Port full notebook geometry/audit CSV checks into app QA stage. |
| 17 | Extra S2 era pulls / masks | 🟨 Partial | Partial | No | Yes | Add optional historical/seasonal S2 pull stage with notebook date/cloud rules. |
| 18 | DEM-matched S2 masks | 🟨 Partial | Partial | No | Yes | Add or extend S2 mask outputs so they are DEM/grid matched like notebook outputs. |
| 20 | Fusion center / named intelligence tensors | 🟨 Partial | Partial | No | Yes | Port named tensor formulas after required base layers exist. |
| 21 | Thermal / DEM_GEO8 / zero-point report | 🟨 Partial | Partial | No | Yes | DEM/thermal mostly exist; add missing DEM_GEO8 and zero-point report products. |
| 22 | 17m focus mask | 🟨 Partial | Partial | No | Yes | Keep existing app mask/window and add the notebook's focus-region AI analysis inputs/outputs. |
| 25 | Target CSV / TXT / JSON outputs | 🟨 Partial | Partial | No | Yes | Define final classifier target schema and add CSV/TXT/JSON writers. |
| 26 | GeoJSON detected-feature exports | 🟨 Partial | Partial | No | Yes | Add private/local GeoJSON export from final target detections. |
| 36 | Reference-TIF comparison utilities | 🟨 Partial | Partial | No | Yes | Port selected reference-TIF comparison utilities into app QA/debug tools. |

## Plan A execution order

### A1 — UI / run input completion

```text
Target item:
  2 Map point picker / ROI selection

Outcome:
  app can start a run using the same point/ROI/grid intent as the notebook without Colab/geemap.
```

### A2 — QA completion

```text
Target items:
  7 Pixel-alignment QA
  11 Auditor / geometry consistency QA
  36 Reference-TIF comparison utilities

Outcome:
  app has the notebook-style QA reports needed to trust every later output.
```

### A3 — Missing stack and mask completion

```text
Target items:
  8 Nano / treasure / geophysics stacks
  9 More feature stacks / rename layers
  17 Extra S2 era pulls / masks
  18 DEM-matched S2 masks
  20 Fusion center / named intelligence tensors
  21 Thermal / DEM_GEO8 / zero-point report

Outcome:
  app produces the missing notebook-derived raster/tensor families before classifier work starts.
```

### A4 — Focus and target-output scaffolding

```text
Target items:
  22 17m focus mask
  25 Target CSV / TXT / JSON outputs
  26 GeoJSON detected-feature exports

Outcome:
  app has the output containers needed by the later classifier/AI phases.
```

## Rules for Plan A

```text
1. Do not start by validating old partial parity only.
2. First port the missing notebook capability into app form.
3. For each item, choose one final notebook cell/variant; do not port duplicates blindly.
4. Replace Colab/Drive/geemap behavior with app-native equivalents.
5. Freeze expected outputs before validation.
6. Then compare app outputs to the frozen notebook outputs.
7. Keep sensitive outputs local/private unless a redacted public output is explicitly designed.
```

## Definition of done for each Plan A item

```text
[x] final notebook cell/variant selected
[x] app stage/service/UI equivalent implemented
[x] output names and artifact classes defined
[x] local run output generated
[x] frozen notebook reference generated or selected
[x] app-vs-notebook comparison passes or documented exception is approved
[x] tests added
```

## What Plan A does not include yet

These are bigger missing AI/ML/classifier phases and should become Plan B after Plan A is complete:

```text
Tesla v7.2 inference engines
hard rule-based target classifiers
CNN / Unet++ / Swin / SegFormer inference
YOLO/CNN/Swin/SegFormer tensor-to-detection flow
training / learn weights workflow
final probability map overlays
KMZ heatmap / 3D target visualization
field-operation KMZ outputs
GPS/path tracing from detected targets
```

## Bottom line

```text
All partial items can be made done in the app.
Plan A completes those partial features first.
Only after Plan A should we move to the fully missing AI/ML/classifier/KMZ system.
```
