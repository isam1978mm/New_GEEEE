# Plan B — Implement Not-Done Notebook Features In The App

Status: active implementation document.

Last update: 2026-06-22 — B3 item 27 KMZ heatmap / 3D visualization implemented; frozen notebook numeric parity still pending.

## Plan B scope: not-done-now items

| # | Not-done-now notebook item | Is it done now? | Can we make it in app? | Plan B note |
|---:|---|---|---:|---|
| 8 | Nano / treasure / geophysics stacks | 🟨 Partial | Yes | App port implemented for canonical cell 037 Nano stack and cell 039 Treasure/Geophysics stack. Outputs and tests pass. Frozen notebook numeric parity still pending. |
| 9 | More feature stacks / rename layers | 🟨 Partial | Yes | App port implemented for selected stack families: cell 050, 053, 051, 047, 052, and 054. Frozen notebook numeric parity still pending. |
| 15 | Bonus / simulator features | 🟨 Partial | Yes | App port implemented for cell 072 AUX_BONUS_FEATURES_STACK_640 and cell 073 SIM_GEOPHYSICAL_STACK_640. Outputs and tests pass. Frozen notebook numeric parity still pending. |
| 17 | Extra S2 era pulls / masks | 🟨 Partial | Yes | App port implemented for canonical cell 077 AIX_2022_2026_CLOUDLT3_EXTRA_TENSORS_STACK_640. Outputs and tests pass. Frozen notebook numeric parity still pending. |
| 18 | DEM-matched S2 masks | 🟨 Partial | Yes | App port implemented for canonical cell 081 AIX_2022_2026FEB_CLOUDLT3_DEM_MATCHED_MASKS_STACK_640. Outputs and tests pass. Frozen notebook numeric parity still pending. |
| 19 | Tesla v7.2 inference engines | 🟨 Partial | Yes | App port implemented for canonical cell 095 TESLA_V7_2_ATOMIC_INFERENCE_STACK_640. Frozen notebook numeric parity still pending. |
| 20 | Fusion center / intelligence tensors | 🟨 Partial | Yes | App port implemented for canonical cell 099 REPORT_640_FINAL_INTELLIGENCE_STACK_640. Outputs and tests pass. Frozen notebook numeric parity still pending. |
| 23 | ROI-constrained AI analysis inside 17m focus | 🟨 Partial | Yes | App port implemented for canonical cell 119. Pixel CSV, target CSV, and GeoJSON outputs and tests pass. Frozen notebook numeric parity still pending. |
| 24 | Hard classifiers / target type rules | 🟨 Partial | Yes | App port implemented for canonical cell 128 AI_HARD_TYPE_CLASSIFIER_CORE9. CSV, TXT, JSON outputs and tests pass. Frozen notebook numeric parity still pending. |
| 25 | Target CSV / TXT / JSON outputs | 🟨 Partial | Yes | App port implemented for canonical cell 121 AI_CORE_RING_SCENE_TARGETS_V7_2C and AI_CORE_RING_SCENE_DECISION_V7_2C. Outputs and tests pass. Frozen notebook numeric parity still pending. |
| 26 | GeoJSON detected-feature exports | 🟨 Partial | Yes | App port implemented for canonical cell 123 AI_FOCUS_17M_DETECTED_FEATURES_WGS84_V7_2.geojson. Outputs and tests pass. Frozen notebook numeric parity still pending. |
| 27 | KMZ heatmap / 3D target visualization | 🟨 Partial | Yes | App port implemented for canonical cell 155 AI_HEATMAP_CLASSIFICATION.png, AI_HEATMAP_CLASSIFICATION.kmz, and AI_3D_TARGET_VISUALIZATION.kmz. Outputs and tests pass. Frozen notebook numeric parity still pending. |
| 28 | AI requirements mapper for YOLO/CNN/Swin | 🟥 No | Yes | Planning/inspection feature. Easier than actual inference. |
| 29 | AI tensor builder for YOLO/CNN/Swin/SegFormer | 🟥 No | Yes | Define input shape, band order, normalization, and saved tensor contract. |
| 30 | Training / learn weights cells | 🟥 No | Yes, separate | Build as a separate training workflow, not a normal app stage. |
| 31 | CNN / Unet++ / Swin / SegFormer model build | 🟥 No | Yes | Requires selected model, weights policy, dependency plan, and CPU/GPU expectations. |
| 32 | CNN final target inference | 🟥 No | Yes | Requires AI tensor builder and selected model first. |
| 33 | Metal fingerprint diagnostic | 🟥 No | Yes | Good candidate for private diagnostic app stage. |
| 34 | Field-operation KMZ outputs | 🟥 No | Yes | Depends on final detections and geospatial output policy. |
| 38 | Live geemap overlays | 🟥 No | Replace | Do not port geemap. Build app-native map/layer UI. |
| 39 | Final probability map overlay + markers | 🟥 No | Yes | Depends on ML inference probability map output. |
| 40 | GPS/path tracing from targets | 🟥 No | Yes | Depends on final detector outputs and geometry/privacy policy. |

## Implemented Plan B results

B1 raster/tensor families implemented:
- Item 8: cells 037 and 039.
- Item 9: cells 050, 053, 051, 047, 052, and 054.
- Item 15: cells 072 and 073.
- Item 17: cell 077.
- Item 18: cell 081.
- Item 20: cell 099.
- Item 19: cell 095.

B2 focus and target contracts implemented:
- Item 23: cell 119 focus pixel CSV, target CSV, and focus GeoJSON.
- Item 24: cell 128 hard type classifier CSV/TXT/JSON.
- Item 25: cell 121 core/ring/scene CSV/TXT/JSON.
- Item 26: cell 123 WGS84 detected-feature GeoJSON.

B3 local/private visualization contracts implemented:
- Item 27: cell 155 heatmap PNG, heatmap KMZ, and 3D visualization KMZ.

### B3.1 result — item 27 KMZ heatmap / 3D target visualization

```text
Status:
  App port implemented for selected KMZ heatmap + 3D visualization outputs.
  Frozen notebook numeric parity is still pending.

Canonical notebook variant selected:
  cell_155 -> FINAL KMZ heatmap + 3D targets, fixed depth safe.

Implemented app outputs:
  full_job/focus/AI_HEATMAP_CLASSIFICATION.png
  full_job/focus/AI_HEATMAP_CLASSIFICATION.kmz
  full_job/focus/AI_3D_TARGET_VISUALIZATION.kmz

Validation done:
  focused focus-mask unit test passed.
  full-run integration test passed.
  local existing run regenerated and confirmed output files exist.
  FocusMaskStage artifact count confirmed as 18.
  Heatmap KMZ contains doc.kml and heat.png.
  Heatmap KML contains AI Heatmap Classification, GroundOverlay, LatLonBox, and source_cell=cell_155.
  3D visualization KMZ contains doc.kml.
  3D KML contains AI 3D Target Visualization, source_cell=cell_155, 5 Placemark entries, and relativeToGround altitude mode.

Privacy/artifact policy:
  All outputs are FILESYSTEM_ONLY and http_servable=False.
  Keep coordinate-bearing visualization outputs local/private by default.

Remaining validation:
  Run a fresh UI/orchestrator run so DB artifact registration includes the new B3.1 artifacts.
  Compare against frozen notebook outputs after reference files are selected/generated.
```

## Next main item

```text
Recommended next main item:
  Plan B item #34: Field-operation KMZ outputs.
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

## Bottom line

```text
All not-done-now items can be made in the app.
They are not blocked by impossibility.
They require implementation, contract selection, and validation against frozen notebook outputs.
```
