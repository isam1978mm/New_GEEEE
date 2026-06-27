# Plan B — Implement Not-Done Notebook Features In The App

Status: active implementation document.

Last update: 2026-06-22 — B4 item 32 final inference gate implemented; frozen notebook numeric parity still pending.

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
| 28 | AI requirements mapper for YOLO/CNN/Swin | 🟨 Partial | Yes | App port implemented for canonical cell 140 AI_MODEL_REQUIREMENTS_MAPPER_V7_2.json as a private planning manifest. No model training/inference/weights/dependency changes. Frozen notebook numeric parity still pending. |
| 29 | AI tensor builder for YOLO/CNN/Swin/SegFormer | 🟨 Partial | Yes | App port implemented for canonical cell 148 AI_TENSORS_STAGE4 outputs: full 52-band tensor, YOLO RGB, CNN tensor, Swin/SegFormer tensor, PCA RGB, negative mask, CSV, and JSON. No model training/inference/weights/dependency changes. Frozen notebook numeric parity still pending. |
| 30 | Training / learn weights cells | 🟨 Partial | Yes, separate | App port implemented for canonical cell 166 AI_TRAINING_WORKFLOW_BOUNDARY_V7_2.json as a separate-training-workflow boundary. No normal app training, dependency install, weight download, inference, or model artifacts. Frozen notebook numeric parity still pending. |
| 31 | CNN / Unet++ / Swin / SegFormer model build | 🟨 Partial | Yes | App port implemented for canonical cell 232 AI_MODEL_BUILD_POLICY_V7_2.json as a model-build policy/config manifest. No model instantiation, torch/timm/SMP imports, weight download, inference, training, or model artifacts. Frozen notebook numeric parity still pending. |
| 32 | CNN final target inference | 🟨 Partial | Yes | App port implemented for canonical cell 169 AI_FINAL_INFERENCE_GATE_V7_2.json as a gated inference-readiness manifest. No torch/model execution, weights, probability maps, target CSV/JSON, GeoJSON/KMZ, or exact-coordinate exposure. Frozen notebook numeric parity still pending. |
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

B4 AI planning/tensor/training/model/inference-gate contracts implemented:
- Item 28: cell 140 AI requirements mapper manifest.
- Item 29: cell 148 AI tensor builder outputs.
- Item 30: cell 166 AI training workflow boundary manifest.
- Item 31: cell 232 AI model build policy manifest.
- Item 32: cell 169 AI final inference gate manifest.

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

### B4.1 result — item 28 AI requirements mapper for YOLO/CNN/Swin

```text
Status:
  App port implemented for selected AI requirements mapper behavior.
  Frozen notebook numeric parity is still pending.

Canonical notebook variant selected:
  cell_140 -> STAGE 1 — MATRIX AUDIT + AI REQUIREMENTS MAPPER.

Implemented app output:
  manifests/AI_MODEL_REQUIREMENTS_MAPPER_V7_2.json

Implemented replacement contract:
  Requirements/planning manifest only.
  Do not build model tensors yet.
  Do not train models.
  Do not run inference.
  Do not download model weights.
  Do not add heavy ML dependencies.
  Do not create model artifacts.
  Keep output local/private and filesystem-only.

Mapped model families:
  YOLOv11
  CNN
  Swin
  SegFormer
  UnetPlusPlus

Validation done:
  ai requirements mapper parity test passed.
  classifier model inventory parity test passed.
  local existing run wrote manifests/AI_MODEL_REQUIREMENTS_MAPPER_V7_2.json.
  Report name confirmed as AI_MODEL_REQUIREMENTS_MAPPER_V7_2.json.
  Schema version confirmed as plan_b28_ai_requirements_mapper_v1.
  source_cell confirmed as cell_140.
  status confirmed as implemented_requirements_mapper_only.
  privacy confirmed as FILESYSTEM_ONLY.
  http_servable, frontend_visible, and downloadable_via_api confirmed False.
  trains_models, runs_inference, downloads_weights, adds_heavy_ml_dependencies, and creates_model_artifacts confirmed False.
  Model families confirmed as YOLOv11, CNN, Swin, SegFormer, and UnetPlusPlus.
  Requirement count confirmed as 5.
  Next dependency-unblocking item confirmed as Plan B item #29.

Privacy/artifact policy:
  Output is a local JSON manifest only.
  No coordinates, geometry, model weights, inference result, raster, NPY, GeoJSON, KMZ, or public API/frontend artifact is created.

Remaining validation:
  Compare against frozen notebook outputs after reference files are selected/generated.
```

### B4.2 result — item 29 AI tensor builder for YOLO/CNN/Swin/SegFormer

```text
Status:
  App port implemented for selected Stage 4 AI tensor-builder behavior.
  Frozen notebook numeric parity is still pending.

Canonical notebook variant selected:
  cell_148 -> STAGE 4 — AI TENSOR BUILDER for YOLOv11 / CNN / Swin / SegFormer.

Supporting notebook variants inspected:
  cell_147 -> normalized input/context builder.
  cell_231 -> later 3-layer RGB-like CNN input hint.

Implemented app outputs:
  AI_TENSORS_STAGE4/AI_FULL_52B_FLOAT32_640.npy
  AI_TENSORS_STAGE4/YOLOV11_RGB_640.npy
  AI_TENSORS_STAGE4/YOLOV11_RGB_VISUAL.tif
  AI_TENSORS_STAGE4/CNN_MULTI_24B_640.npy
  AI_TENSORS_STAGE4/SWINSEGFORMER_16B_640.npy
  AI_TENSORS_STAGE4/PCA_RGB_640.npy
  AI_TENSORS_STAGE4/AI_NEGATIVE_MASK_640.npy
  QA/STAGE4_AI_TENSOR_BUILDER.json
  QA/STAGE4_AI_TENSOR_BANDS.csv

Implemented replacement contract:
  Tensor builder only.
  Do not train models.
  Do not run inference.
  Do not download model weights.
  Do not add heavy ML dependencies.
  Do not create model artifacts.
  Keep outputs local/private and filesystem-only.
  Use deterministic band order, robust p2-p98 per-channel normalization, non-finite/nodata-to-0 handling, and zero-fill reporting for missing source bands.

Validation done:
  ai tensor builder parity test passed after fixing ensure_run_qa_dir import to app.pipeline.qa_paths.
  ai requirements mapper parity test passed.
  local existing run wrote all Stage 4 tensor outputs.
  Report, CSV, full tensor, YOLO RGB, YOLO visual TIF, CNN tensor, Swin tensor, PCA RGB, and negative mask outputs were confirmed present.
  source_cell confirmed as cell_148.
  status confirmed as implemented_tensor_builder_only.
  privacy confirmed as FILESYSTEM_ONLY.
  http_servable, frontend_visible, and downloadable_via_api confirmed False.
  trains_models, runs_inference, downloads_weights, adds_heavy_ml_dependencies, and creates_model_artifacts confirmed False.
  Full tensor shape confirmed as (52, 640, 640) float32.
  YOLO tensor shape confirmed as (3, 640, 640) float32.
  CNN tensor shape confirmed as (24, 640, 640) float32.
  Swin/SegFormer tensor shape confirmed as (16, 640, 640) float32.
  PCA RGB shape confirmed as (3, 640, 640) float32.
  Negative mask shape confirmed as (640, 640) float32.
  YOLO, CNN, Swin, and PCA ranges confirmed within 0-1.
  Negative mask binary check passed.
  Missing zero-filled source band count confirmed as 0 on the local existing run.

Privacy/artifact policy:
  Outputs are local tensor/report files only.
  No coordinates, raw geometry, model weights, inference result, GeoJSON, KMZ, public API artifact, or frontend artifact is created.

Remaining validation:
  Compare against frozen notebook outputs after reference files are selected/generated.
```

### B4.3 result — item 30 Training / learn weights cells

```text
Status:
  App port implemented for selected training/learn-weights boundary behavior.
  Frozen notebook numeric parity is still pending.

Canonical notebook variant selected:
  cell_166 -> PROFESSIONAL GLOBAL ARCHEO-TRAINING, low-memory safe 640x640 version.

Supporting notebook variants inspected:
  cell_150 -> dependency install probe.
  cell_151 -> expanded dependency install probe.
  cell_163 -> small 224 training scaffold.
  cell_164 -> 640 training scaffold memory-optimized 12GB.
  cell_165 -> high-fidelity 640 training variant.
  cell_167, cell_168, cell_169 -> model-based inference cells, excluded from item #30.

Implemented app output:
  manifests/AI_TRAINING_WORKFLOW_BOUNDARY_V7_2.json

Implemented replacement contract:
  Training workflow boundary only.
  Do not train models inside normal app runs.
  Do not install ML dependencies inside normal app runs.
  Do not download model weights.
  Do not write model artifacts.
  Do not run inference.
  Require a separate offline/private training workflow before any model build or inference work.

Validation done:
  ai training workflow boundary parity test passed.
  ai tensor builder parity test passed.
  ai requirements mapper parity test passed.
  local existing run wrote manifests/AI_TRAINING_WORKFLOW_BOUNDARY_V7_2.json.
  Report name confirmed as AI_TRAINING_WORKFLOW_BOUNDARY_V7_2.json.
  Schema version confirmed as plan_b30_ai_training_workflow_boundary_v1.
  source_cell confirmed as cell_166.
  status confirmed as implemented_training_workflow_boundary_only.
  privacy confirmed as FILESYSTEM_ONLY.
  http_servable, frontend_visible, and downloadable_via_api confirmed False.
  normal_app_runs_must_train_models, normal_app_runs_must_install_ml_dependencies, normal_app_runs_must_download_weights, normal_app_runs_must_write_model_artifacts, and normal_app_runs_must_run_inference confirmed False.
  separate_training_workflow_required confirmed True.
  selected canonical cell confirmed as cell_166.
  class count confirmed as 10.
  approval gate count confirmed as 10.
  training input dependency confirmed as Plan B item #29 AI_TENSORS_STAGE4 outputs.
  preferred input confirmed as AI_TENSORS_STAGE4/YOLOV11_RGB_640.npy.
  input shape confirmed as [3, 640, 640].
  no_runtime_pip_install confirmed True.
  must_run_outside_normal_app_pipeline confirmed True.
  next dependency-unblocking item confirmed as Plan B item #31.

Privacy/artifact policy:
  Output is a local JSON manifest only.
  No coordinates, raw geometry, dependency install, model weights, model artifact, training execution, inference result, GeoJSON, KMZ, public API artifact, or frontend artifact is created.

Remaining validation:
  Compare against frozen notebook outputs after reference files are selected/generated.
```

### B4.4 result — item 31 CNN / Unet++ / Swin / SegFormer model build

```text
Status:
  App port implemented for selected model-build policy behavior.
  Frozen notebook numeric parity is still pending.

Canonical notebook variant selected:
  cell_232 -> UnetPlusPlus with Swin encoder and ResNet50 fallback.

Supporting notebook variants inspected:
  cell_231 -> RGB-like input preprocessing hint.
  cell_233 -> experimental custom Swin-L + Unet++ decoder attempt, not selected.
  cell_234 -> ortho-calibrated inference/postprocess, excluded from item #31.
  cell_235 -> ResNet50 UnetPlusPlus fallback plus inference; fallback config only retained.
  cell_236 -> final target inference, excluded from item #31.
  cell_237 -> target map exports, excluded from item #31.

Implemented app output:
  manifests/AI_MODEL_BUILD_POLICY_V7_2.json

Implemented replacement contract:
  Model-build policy/config manifest only.
  Do not import torch, timm, or segmentation_models_pytorch.
  Do not instantiate models.
  Do not load or download weights.
  Do not run forward passes.
  Do not train models.
  Do not run inference.
  Do not write model artifacts.
  Keep output local/private and filesystem-only.

Selected model policy:
  Primary architecture: UnetPlusPlus.
  Primary encoder: tu-swin_base_patch4_window7_224.
  Fallback encoder: resnet50.
  Input channels: 3.
  Classes: 5.
  Preferred input: AI_TENSORS_STAGE4/YOLOV11_RGB_640.npy.
  Optional Swin adapter shape: [3, 224, 224].

Validation done:
  ai model build policy parity test passed.
  ai training workflow boundary parity test passed.
  ai tensor builder parity test passed.
  ai requirements mapper parity test passed.
  local existing run wrote manifests/AI_MODEL_BUILD_POLICY_V7_2.json.
  Report name confirmed as AI_MODEL_BUILD_POLICY_V7_2.json.
  Schema version confirmed as plan_b31_ai_model_build_policy_v1.
  source_cell confirmed as cell_232.
  status confirmed as implemented_model_build_policy_only.
  privacy confirmed as FILESYSTEM_ONLY.
  http_servable, frontend_visible, and downloadable_via_api confirmed False.
  normal_app_runs_must_build_models, normal_app_runs_must_train_models, normal_app_runs_must_install_ml_dependencies, normal_app_runs_must_download_weights, normal_app_runs_must_write_model_artifacts, and normal_app_runs_must_run_inference confirmed False.
  imports_torch, imports_timm, imports_segmentation_models_pytorch, instantiates_model, loads_weights, and runs_forward_pass confirmed False.
  selected canonical cell confirmed as cell_232.
  primary architecture confirmed as UnetPlusPlus.
  primary encoder confirmed as tu-swin_base_patch4_window7_224.
  fallback encoder confirmed as resnet50.
  in_channels confirmed as 3.
  classes confirmed as 5.
  app_runtime_weight_download_allowed and app_runtime_model_instantiation_allowed confirmed False.
  model-build gate count confirmed as 9.
  preferred input confirmed as AI_TENSORS_STAGE4/YOLOV11_RGB_640.npy.
  preferred input shape confirmed as [3, 640, 640].
  optional Swin adapter shape confirmed as [3, 224, 224].
  next dependency-unblocking item confirmed as Plan B item #32.

Privacy/artifact policy:
  Output is a local JSON manifest only.
  No coordinates, raw geometry, dependency install, model weights, model artifact, model execution, inference result, GeoJSON, KMZ, public API artifact, or frontend artifact is created.

Remaining validation:
  Compare against frozen notebook outputs after reference files are selected/generated.
```

### B4.5 result — item 32 CNN final target inference

```text
Status:
  App port implemented for selected final inference behavior as a gated readiness manifest.
  Real model inference remains intentionally blocked until dependency/weights/model/privacy/operator gates are approved.
  Frozen notebook numeric parity is still pending.

Canonical notebook variant selected:
  cell_169 -> MODEL-BASED ARCHEO-INFERENCE with DEM/slope fusion and strict run outputs.

Supporting notebook variants inspected:
  cell_167 -> early professional scan, not selected.
  cell_168 -> model inference with DEM/slope fusion, superseded by cell_169.
  cell_232 -> model build plus immediate inference, handled by item #31 policy and inference remains gated.
  cell_235 -> ResNet50 fallback plus inference, fallback policy only retained.
  cell_236 -> final target inference grid-locked, secondary inference reference.
  cell_237 -> final target map exports, excluded from item #32.

Implemented app output:
  manifests/AI_FINAL_INFERENCE_GATE_V7_2.json

Implemented replacement contract:
  Inference gate/readiness manifest only.
  Do not import torch.
  Do not load model objects.
  Do not load or download weights.
  Do not instantiate models.
  Do not run forward passes.
  Do not write probability maps.
  Do not write target CSV/JSON.
  Do not write GeoJSON or KMZ.
  Do not expose exact coordinates.
  Keep output local/private and filesystem-only.

Future private outputs if later approved:
  QA/AI_MODEL_ARCHAEO_INFERENCE_17M_V7_2.csv
  QA/AI_MODEL_ARCHAEO_INFERENCE_17M_V7_2.json
  AI_INFERENCE_STAGE5/AI_MODEL_PROBABILITIES_640.npy
  manifests/AI_FINAL_INFERENCE_REDACTED_SUMMARY_V7_2.json

Validation done:
  ai final inference gate parity test passed after adding missing pathlib.Path import in the test.
  ai model build policy parity test passed.
  ai training workflow boundary parity test passed.
  ai tensor builder parity test passed.
  ai requirements mapper parity test passed.
  local existing run wrote manifests/AI_FINAL_INFERENCE_GATE_V7_2.json.
  Report name confirmed as AI_FINAL_INFERENCE_GATE_V7_2.json.
  Schema version confirmed as plan_b32_ai_final_inference_gate_v1.
  source_cell confirmed as cell_169.
  status confirmed as implemented_inference_gate_only.
  privacy confirmed as FILESYSTEM_ONLY.
  http_servable, frontend_visible, and downloadable_via_api confirmed False.
  normal_app_runs_must_run_inference, normal_app_runs_must_import_torch, normal_app_runs_must_load_weights, normal_app_runs_must_instantiate_model, normal_app_runs_must_write_coordinate_outputs, normal_app_runs_must_write_probability_maps, and normal_app_runs_must_write_geojson_or_kmz confirmed False.
  imports_torch, loads_model, loads_weights, runs_forward_pass, creates_probability_map, creates_target_csv, creates_target_json, and exposes_exact_coordinates confirmed False.
  selected canonical cell confirmed as cell_169.
  upstream readiness confirmed True for item #29 tensor outputs, item #30 training boundary, and item #31 model build policy.
  approved_for_real_inference confirmed False.
  inference gate count confirmed as 11.
  weights and dependency gates confirmed False.
  future private CSV path confirmed as QA/AI_MODEL_ARCHAEO_INFERENCE_17M_V7_2.csv.
  future private JSON path confirmed as QA/AI_MODEL_ARCHAEO_INFERENCE_17M_V7_2.json.
  next dependency-unblocking item confirmed as Plan B item #33 or approved continuation of #32 real inference after gates.

Privacy/artifact policy:
  Output is a local JSON manifest only.
  No coordinates, raw geometry, model weights, model artifact, model execution, inference result, probability map, target CSV/JSON, GeoJSON, KMZ, public API artifact, or frontend artifact is created.

Remaining validation:
  Compare against frozen notebook outputs after reference files are selected/generated.
  Real inference remains blocked until all gates are explicitly approved.
```

## Next main item

```text
Recommended next main item:
  Plan B item #33: Metal fingerprint diagnostic.

Why:
  Item #32 now records inference readiness and proves real inference is still blocked by dependency/weights/privacy/operator gates.
  Item #33 is a private diagnostic feature that can proceed without violating the blocked real-inference gates.
  Items #39/#40 should wait for approved probability/target outputs or remain manifest-only.
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
