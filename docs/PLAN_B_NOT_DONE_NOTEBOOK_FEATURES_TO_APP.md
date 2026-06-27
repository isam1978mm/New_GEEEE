# Plan B — Implement Not-Done Notebook Features In The App

Status: active implementation document.

Last update: 2026-06-22 — B3 item 38 app-native live overlay manifest implemented; frozen notebook numeric parity still pending.

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
| 34 | Field-operation KMZ outputs | 🟨 Partial | Yes | App port implemented for canonical cell 200 FINAL_ARCHEO_INTELLIGENCE_MAP.geojson and TESLA_V7_2_FIELD_OPERATIONS.kmz. Outputs and tests pass. Frozen notebook numeric parity still pending. |
| 38 | Live geemap overlays | 🟨 Partial | Replace | App-native replacement implemented for canonical cell 243 as APP_NATIVE_LIVE_OVERLAY_MANIFEST_V7_2.json plus operator-only coordinate-free preview family. No geemap port and no public tiles/coordinates. Frozen notebook numeric parity still pending. |
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
- Item 34: cell 200 field-operation GeoJSON and KMZ.
- Item 38: cell 243 app-native live overlay manifest and operator-only preview family.

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

### B3.2 result — item 34 Field-operation KMZ outputs

```text
Status:
  App port implemented for selected field-operation GeoJSON and KMZ outputs.
  Frozen notebook numeric parity is still pending.

Canonical notebook variant selected:
  cell_200 -> advanced field mapping / TESLA_V7_2_FIELD_OPERATIONS.

Implemented app outputs:
  full_job/focus/FINAL_ARCHEO_INTELLIGENCE_MAP.geojson
  full_job/focus/TESLA_V7_2_FIELD_OPERATIONS.kmz

Validation done:
  focused focus-mask unit test passed.
  full-run integration test passed.
  local existing run regenerated and confirmed output files exist.
  FocusMaskStage artifact count confirmed as 20.
  FINAL_ARCHEO_INTELLIGENCE_MAP.geojson is a FeatureCollection with source_cell cell_200, CRS EPSG:4326, and 5 Point features.
  Longitude/latitude ranges were validated without exposing exact coordinates.
  Feature properties include Source_Cell, Material_Content, Field_Notes, and UTM.
  TESLA_V7_2_FIELD_OPERATIONS.kmz contains doc.kml.
  Field KML contains Tesla v7.2 Mission: Advanced Intelligence Assets, source_cell=cell_200, 5 Placemark entries, and Strategic Intelligence Data.

Privacy/artifact policy:
  All outputs are FILESYSTEM_ONLY and http_servable=False.
  Keep coordinate-bearing field-operation outputs local/private by default.

Remaining validation:
  Run a fresh UI/orchestrator run so DB artifact registration includes the new B3.2 artifacts.
  Compare against frozen notebook outputs after reference files are selected/generated.
```

### B3.3 result — item 38 Live geemap overlays, replaced by app-native map/layer UI

```text
Status:
  App-native replacement implemented for selected live geemap overlay behavior.
  Frozen notebook numeric parity is still pending.

Canonical notebook variant selected:
  cell_243 -> live geemap.Map overlay of CNN probability matrix, markers, buffers, and corridor lines.

Implemented app output:
  full_job/focus/APP_NATIVE_LIVE_OVERLAY_MANIFEST_V7_2.json

Implemented operator-only preview family:
  plan_b38_live_overlay_manifest

Implemented replacement contract:
  Do not port geemap or create public map tiles.
  Write a local/private app-native layer manifest with source_cell cell_243.
  Represent HYBRID basemap, CNN digital matrix, detected markers, detected buffers, field-operation points, corridor candidates, and heatmap image overlay as manifest layers.
  Mark CNN probability and corridor layers as pending_dependency because they depend on later item #32/#39/#40 outputs.
  Extend the operator overlay preview service to return a coordinate-free manifest summary only.

Validation done:
  focused focus-mask unit test passed.
  operator overlay preview integration test passed.
  full-run integration test passed.
  local existing run regenerated and confirmed output file exists.
  FocusMaskStage artifact count confirmed as 21.
  Manifest type confirmed as AppNativeLiveOverlayManifest.
  source_cell confirmed as cell_243.
  privacy confirmed as FILESYSTEM_ONLY.
  http_servable and downloadable_via_api confirmed False.
  basemap confirmed HYBRID.
  target_count confirmed as 5.
  layer_count confirmed as 7.
  exact_coordinates_in_manifest and raw_geometry_in_manifest confirmed False.
  Required layers confirmed: hybrid_basemap, cnn_digital_matrix, detected_target_markers, detected_target_area_buffers, subterranean_corridor_candidates, heatmap_ground_overlay.
  Operator-only preview returned status 200 / allowed for plan_b38_live_overlay_manifest.
  Preview type confirmed as app_native_live_overlay_manifest.
  Preview response remained filesystem_only True, http_servable False, downloadable False, frontend_visible operator_only.
  Preview exact_coordinates_in_response and raw_geometry_in_response confirmed False.

Privacy/artifact policy:
  Output is FILESYSTEM_ONLY and http_servable=False.
  No public tiles, public download URL, exact-coordinate API payload, or raw geometry API payload is created.

Remaining validation:
  Run a fresh UI/orchestrator run so DB artifact registration includes the new B3.3 artifact.
  Compare against frozen notebook outputs after reference files are selected/generated.
```

## Next main item

```text
Recommended next main item:
  Plan B item #28: AI requirements mapper for YOLO/CNN/Swin.

Why:
  B3 local/private visualization contracts are now implemented through item #38.
  Item #39 depends on final probability-map output, and item #40 depends on final target/path outputs.
  The next dependency-unblocking work is B4: item #28 then #29 before CNN/model inference items #31/#32.
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
