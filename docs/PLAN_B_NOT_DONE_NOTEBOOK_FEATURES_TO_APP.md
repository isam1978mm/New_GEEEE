# Plan B — Implement Not-Done Notebook Features In The App

Status: active implementation document.

Last update: 2026-06-22 — B2 item 25 target CSV/TXT/JSON outputs implemented; frozen notebook numeric parity still pending.

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
| 19 | Tesla v7.2 inference engines | 🟨 Partial | Yes | App port implemented for canonical cell 095 TESLA_V7_2_ATOMIC_INFERENCE_STACK_640. Other item #19 variants remain separate: cell 100/101 target CSV scan, cell 102/103 geochemical secret layers/monitoring. Frozen notebook numeric parity still pending. |
| 20 | Fusion center / intelligence tensors | 🟨 Partial | Yes | App port implemented for canonical cell 099 REPORT_640_FINAL_INTELLIGENCE_STACK_640. Outputs and tests pass. Frozen notebook numeric parity still pending. |
| 23 | ROI-constrained AI analysis inside 17m focus | 🟨 Partial | Yes | App port implemented for canonical cell 119 ROI-constrained 17m focus analysis. Pixel CSV, target CSV, and target GeoJSON outputs and tests pass. Frozen notebook numeric parity still pending. |
| 24 | Hard classifiers / target type rules | 🟨 Partial | Yes | App port implemented for canonical cell 128 AI_HARD_TYPE_CLASSIFIER_CORE9. CSV, TXT, JSON outputs and tests pass. Frozen notebook numeric parity still pending. |
| 25 | Target CSV / TXT / JSON outputs | 🟨 Partial | Yes | App port implemented for canonical cell 121 AI_CORE_RING_SCENE_TARGETS_V7_2C and AI_CORE_RING_SCENE_DECISION_V7_2C. Outputs and tests pass. Frozen notebook numeric parity still pending. |
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
  19 Tesla v7.2 atomic inference stack

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

Validation done:
  focused S2 indices test passed.
  full-run integration test passed.
  local existing run regenerated and confirmed output files/shapes exist.
  REPORT_640 final intelligence stack shape confirmed as (640, 640, 3) float32.
  STACK_ALIAS_MANIFEST records source_cell cell_099 and status implemented.
```

### B1.12 result — item 19 Tesla v7.2 inference engines, Atomic Inference Engine

```text
Status:
  App port implemented for the selected Tesla v7.2 atomic material-signature stack.
  Frozen notebook numeric parity is still pending.

Canonical notebook variant selected:
  cell_095 -> TESLA_V7_2_ATOMIC_INFERENCE_STACK_640.npy

Implemented app outputs:
  NPY_STACKS/TESLA_V7_2_ATOMIC_INFERENCE_STACK_640.npy
  NPY_RADAR_BANDS/AI_BEH_Gold_Pure_Density_19_3_DOM_lin_640.npy
  NPY_RADAR_BANDS/AI_BEH_Artifacts_Jars_Chests_DOM_lin_640.npy
  NPY_RADAR_BANDS/AI_BEH_Mercury_RareChemicals_DOM_lin_640.npy
  NPY_RADAR_BANDS/AI_BEH_Gemstones_AncientGlass_DOM_lin_640.npy
  NPY_RADAR_BANDS/AI_BEH_Alloys_Statues_REL_ND_DOM_lin_640.npy
  GEOTIFF_RADAR_BANDS/AI_BEH_Gold_Pure_Density_19_3_DOM_lin_640.tif
  GEOTIFF_RADAR_BANDS/AI_BEH_Artifacts_Jars_Chests_DOM_lin_640.tif
  GEOTIFF_RADAR_BANDS/AI_BEH_Mercury_RareChemicals_DOM_lin_640.tif
  GEOTIFF_RADAR_BANDS/AI_BEH_Gemstones_AncientGlass_DOM_lin_640.tif
  GEOTIFF_RADAR_BANDS/AI_BEH_Alloys_Statues_REL_ND_DOM_lin_640.tif
  GEOTIFF_RADAR_BANDS/{5 AI_BEH bands}.tif.meta.json
  NPY_STACKS/STACK_ALIAS_MANIFEST.json entry for source_cell cell_095

Validation done:
  focused S2 indices test passed.
  full-run integration test passed.
  local existing run regenerated and confirmed output files/shapes exist.
  TESLA_V7_2_ATOMIC_INFERENCE stack shape confirmed as (640, 640, 5) float32.
  STACK_ALIAS_MANIFEST records source_cell cell_095 and status implemented.
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

### B2.1 result — item 23 ROI-constrained AI analysis inside 17m focus

```text
Status:
  App port implemented for the selected ROI-constrained 17m focus analysis.
  Frozen notebook numeric parity is still pending.

Canonical notebook variant selected:
  cell_119 -> ROI-constrained AI analysis inside 17m focus.

Implemented app outputs:
  full_job/focus/AI_FOCUS_17M_PIXEL_REPORT_V7_2.csv
  full_job/focus/AI_FOCUS_17M_TARGETS_V7_2.csv
  full_job/focus/AI_FOCUS_17M_TARGETS_V7_2.geojson
  Existing focus outputs remain:
    full_job/focus/focus_zone_17m.tif
    full_job/focus/focus_zone_17m.npy
    full_job/focus/focus_zone_ai_ready_window.npy
    full_job/focus/focus_zone_summary.json
    full_job/focus/focus_zone_band_summary.csv

Implemented analysis contract:
  Use the existing app 17m focus mask as the notebook Class_E equivalent.
  Load six secret layers:
    Secret_Gold_Halo
    Secret_Silver_Oxide
    Secret_Tunnel_Ceiling
    Secret_Thermal_Inertia
    Secret_Chemical_Protector
    Secret_Hidden_Doors
  Load three REPORT_640 layers:
    REPORT_640_FINAL_Zero_Point_Targets
    REPORT_640_Mass_Report
    REPORT_640_Pottery_Report
  Compute ROI-only robust-z bands and ROI_Composite_Score with the cell_119 weights.
  Write all focus pixels to the pixel report CSV.
  Write top five focus targets to the target report CSV and GeoJSON.

Privacy/artifact policy:
  All outputs are FILESYSTEM_ONLY and http_servable=False.
  Keep exact target GeoJSON and coordinate-bearing CSV local/private by default.

Validation done:
  focused focus-mask unit test passed.
  full-run integration test passed.
  local existing run regenerated and confirmed output files exist.
  Focus mask shape confirmed as (640, 640) float32.
  Focus mask pixel count confirmed as 9.
  Pixel report rows confirmed as 9.
  Target report rows confirmed as 5.
  GeoJSON type confirmed as FeatureCollection with 5 features.

Remaining validation:
  Run a fresh UI/orchestrator run so DB artifact registration includes the new B2.1 artifacts.
  Compare against frozen notebook outputs after reference files are selected/generated.
```

### B2.2 result — item 24 Hard classifiers / target type rules

```text
Status:
  App port implemented for the selected hard type classifier.
  Frozen notebook numeric parity is still pending.

Canonical notebook variant selected:
  cell_128 -> AI_HARD_TYPE_CLASSIFIER_CORE9.

Implemented app outputs:
  full_job/focus/AI_HARD_TYPE_CLASSIFIER_CORE9.csv
  full_job/focus/AI_HARD_TYPE_CLASSIFIER_CORE9.txt
  full_job/focus/AI_HARD_TYPE_CLASSIFIER_CORE9.json

Implemented classifier contract:
  Use the existing app 17m focus mask as the Core-9/focus core.
  Load the same six secret layers and three REPORT_640 layers used by item #23.
  Build core/ring/scene statistics and hard scores for:
    Primary_Class
    Void_Type
    Metal_Type
    Metal_Shape
    Content_Type
    Estimated_Stacked_Boxes
    Estimated_Aligned_Jars
    Final_Confidence
  Write one canonical classifier record to CSV, a text summary, and a JSON payload with source_cell cell_128.

Privacy/artifact policy:
  All outputs are FILESYSTEM_ONLY and http_servable=False.
  Keep coordinate-bearing and target-classifier outputs local/private by default.

Validation done:
  focused focus-mask unit test passed.
  full-run integration test passed.
  local existing run regenerated and confirmed output files exist.
  FocusMaskStage artifact count confirmed as 11.
  HARD_CLASSIFIER_ROWS confirmed as 1.
  SOURCE_CELL_CSV confirmed as cell_128.
  SOURCE_CELL_JSON confirmed as cell_128.
  STATUS_JSON confirmed as implemented.
  TXT_HAS_TITLE confirmed as True.
  Local run example produced Primary_Class UNRESOLVED_ANOMALY with Final_Confidence 0.4827.

Remaining validation:
  Run a fresh UI/orchestrator run so DB artifact registration includes the new B2.2 artifacts.
  Compare against frozen notebook outputs after reference files are selected/generated.
```

### B2.3 result — item 25 Target CSV / TXT / JSON outputs

```text
Status:
  App port implemented for the selected core/ring/scene target output contract.
  Frozen notebook numeric parity is still pending.

Canonical notebook variant selected:
  cell_121 -> AI_CORE_RING_SCENE_TARGETS_V7_2C / AI_CORE_RING_SCENE_DECISION_V7_2C.

Implemented app outputs:
  full_job/focus/AI_CORE_RING_SCENE_TARGETS_V7_2C.csv
  full_job/focus/AI_CORE_RING_SCENE_DECISION_V7_2C.txt
  full_job/focus/AI_CORE_RING_SCENE_DECISION_V7_2C.json

Implemented target-output contract:
  Use the existing app 17m focus mask as the notebook Class_E equivalent.
  Reuse item #23 ROI target records and item #24 hard classifier record.
  Write one final core/ring/scene target-decision CSV row with:
    Scenario
    Burial_Style_Inference
    Void_Probability
    Entrance_Probability
    Metal_Probability
    Pottery_Probability
    Reliability
    Detection_Confidence
    Interpretation_Confidence
    Final_Confidence
    Decision_Grade
    Entrance_Type
    Metal_Type
    Room_Count_Inference
    Content_Inference
    Dominant_Direction
    Directionality_Strength
    Resolution_Note
    Source_Cell
  Write matching TXT summary and JSON payload with source_cell cell_121 and embedded target/hard-classifier context.

Privacy/artifact policy:
  All outputs are FILESYSTEM_ONLY and http_servable=False.
  Keep target CSV/TXT/JSON outputs local/private by default.

Validation done:
  focused focus-mask unit test passed.
  full-run integration test passed.
  local existing run regenerated and confirmed output files exist.
  FocusMaskStage artifact count confirmed as 14.
  CORE_RING_ROWS confirmed as 1.
  SOURCE_CELL_CSV confirmed as cell_121.
  SOURCE_CELL_JSON confirmed as cell_121.
  STATUS_JSON confirmed as implemented.
  TARGET_COUNT_JSON confirmed as 5.
  TXT_HAS_TITLE confirmed as True.
  Local run example produced Decision_Grade C_LOW_CONFIDENCE_REVIEW and Final_Confidence 0.7047.

Remaining validation:
  Run a fresh UI/orchestrator run so DB artifact registration includes the new B2.3 artifacts.
  Compare against frozen notebook outputs after reference files are selected/generated.
```

### Next main item scan after B2.3

```text
Recommended next main item:
  Move to Plan B item #26: GeoJSON detected-feature exports.

Why:
  Item #23 now produces ROI-constrained pixel/target reports and a focus target GeoJSON.
  Item #24 now produces the hard type classifier CSV/TXT/JSON record.
  Item #25 now produces the core/ring/scene target CSV/TXT/JSON outputs.
  The next B2 contract item is standardizing/exporting detected-feature GeoJSON.
  Frozen notebook numeric parity remains pending for implemented B1/B2 items.

Next action:
  Inspect exact notebook cell(s) for item #26 GeoJSON detected-feature exports.
  Compare them against current focus target GeoJSON and target output JSON.
  Produce a gap table before coding.
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
