# Plan A — Complete Partial Notebook Features In The App

Status: implementation closeout snapshot as of 2026-06-22.

Goal: before more parity work, complete the notebook features that are already partially present in the app. The app must copy the notebook purpose where it matters, while replacing Colab-only behavior with proper app/server behavior.

This document uses the notebook phase inventory as the source of scope. It does not claim the app already implements the full notebook AI/ML/classifier/KMZ system.

## Closeout summary

```text
Plan A is implementation-closed enough to stop before Plan B.

Validated focused roll-up:
  27 passed, 2 warnings

Validation scope:
  tests/unit/test_roi_contract.py
  tests/integration/test_run_roi_contract.py
  tests/unit/test_alignment_qa.py
  tests/unit/test_reference_tif_compare.py
  tests/unit/test_feature_stacks.py
  tests/unit/test_s2_indices.py
  tests/unit/test_focus_mask.py
  tests/unit/test_object_extract.py
  tests/integration/test_public_api_safety.py

Warnings were non-blocking:
  FastAPI/Starlette TestClient deprecation warning
  local pytest cache permission warning

Repo status after validation:
  clean
```

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

| # | Partial notebook item | Closeout status | Does app do it now? | Notebook-only? | Can we make it in app? | Plan A result |
|---:|---|---|---:|---:|---:|---|
| 2 | Map point picker / ROI selection | 🟩 Closed for Plan A | Yes | No | Yes | App-native coordinate/map-picker flow writes the same ROI/grid contract, including private ROI contract output. |
| 7 | Pixel-alignment QA | 🟩 Closed for Plan A | Yes | No | Yes | Alignment QA expanded to recursive official-TIF audit, with safe summaries and focused tests. |
| 8 | Nano / treasure / geophysics stacks | 🟨 Contract/scaffold closed; formulas deferred | Partial | No | Yes | Notebook-compatible stack aliases and manifest added. Unstable Nano/GPHYS/Ultimate formulas remain deferred until canonical formulas are selected. |
| 9 | More feature stacks / rename layers | 🟩 Closed for Plan A | Yes | No | Yes | Stack aliases, local-only tensor outputs, and manifest naming contract added. |
| 11 | Auditor / geometry consistency QA | 🟩 Closed for Plan A | Yes | No | Yes | Geometry/auditor coverage expanded via recursive alignment QA and reference-TIF comparison helper. |
| 17 | Extra S2 era pulls / masks | 🟩 Closed for Plan A | Yes | No | Yes | S2 date/cloud rules documented in DEM-matched mask manifest, including primary, secret-layer, and report-era rules. |
| 18 | DEM-matched S2 masks | 🟩 Closed for Plan A | Yes | No | Yes | DEM/grid-matched S2 raw-valid and index-valid masks added as local-only outputs. |
| 20 | Fusion center / named intelligence tensors | 🟨 Prerequisite scaffolding closed; inference deferred | Partial | No | Yes | Named tensor/alias scaffolding added. Final AI/classifier fusion formulas remain Plan B. |
| 21 | Thermal / DEM_GEO8 / zero-point report | 🟩 Closed for Plan A | Yes | No | Yes | Existing thermal/DEM/report products inspected; zero-point report is implemented. |
| 22 | 17m focus mask | 🟩 Closed for Plan A | Yes | No | Yes | Existing 17m focus mask validated; local-only target-output scaffolding added. |
| 25 | Target CSV / TXT / JSON outputs | 🟩 Closed for Plan A | Yes | No | Yes | Local target CSV/TXT/JSON outputs added. |
| 26 | GeoJSON detected-feature exports | 🟩 Closed for Plan A | Yes | No | Yes | Local-only pixel-grid detected-feature GeoJSON added, without geographic coordinates. |
| 36 | Reference-TIF comparison utilities | 🟩 Closed for Plan A | Yes | No | Yes | Safe reference-TIF comparison helper and tests added. |

## Plan A execution order

### A1 — UI / run input completion

```text
Target item:
  2 Map point picker / ROI selection

Outcome:
  app can start a run using the same point/ROI/grid intent as the notebook without Colab/geemap.

Closeout:
  backend ROI/grid contract verified
  API-created run writes PRIVATE/RUN_ROI_CONTRACT.json
  UI fixed-grid wording clarified
  QA grid transform tolerance documented for micro floating-origin deltas
```

### A2 — QA completion

```text
Target items:
  7 Pixel-alignment QA
  11 Auditor / geometry consistency QA
  36 Reference-TIF comparison utilities

Outcome:
  app has the notebook-style QA reports needed to trust every later output.

Closeout:
  recursive official-TIF alignment audit added
  reference-TIF comparison helper added
  public API safety regression passed
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

Closeout:
  notebook stack aliases added under local-only NPY_STACKS
  stack alias manifest added
  DEM-matched S2 raw/index masks added
  S2 era/date/cloud rules documented in manifest

Important deferred items:
  unstable Nano/GPHYS/Ultimate formulas are not claimed complete
  final AI/classifier fusion remains Plan B
```

### A4 — Focus and target-output scaffolding

```text
Target items:
  22 17m focus mask
  25 Target CSV / TXT / JSON outputs
  26 GeoJSON detected-feature exports

Outcome:
  app has the output containers needed by the later classifier/AI phases.

Closeout:
  17m focus mask regression passed
  target CSV/TXT/JSON outputs added
  detected-feature GeoJSON added as pixel-grid local-only output
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
[x] final notebook cell/variant selected where stable
[x] app stage/service/UI equivalent implemented
[x] output names and artifact classes defined
[x] local run output or focused deterministic output generated
[x] frozen notebook reference generated or selected where applicable
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
canonical Nano/GPHYS/Ultimate formulas where the notebook has duplicate or unstable variants
```

## Bottom line

```text
Plan A is closed enough to stop before Plan B.
The app now has the missing app-native contracts, QA scaffolding, mask/stack aliases, and local target/export containers needed before classifier work.
Do not claim Plan B AI/ML/classifier/KMZ behavior is implemented yet.
```
