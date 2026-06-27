# Plan B item #39 — Final probability map overlay + markers

Status: implemented as a gated readiness manifest.

Frozen notebook numeric parity is still pending.

## Canonical notebook variant

```text
cell_238 -> final probability-map target engine / final_targets dependency
```

## Supporting notebook variants inspected

```text
cell_239 -> structural scanner, not selected because it uses torch convolution and exact coordinate prints.
cell_240 -> final decision scanner, not selected because it uses probabilities and exact coordinate prints.
cell_241 -> field navigation GeoJSON/KMZ, excluded from item #39.
cell_242 -> stairs/path tracing, reserved for item #40.
cell_243 -> live geemap overlay shell, already replaced by item #38 app-native overlay manifest.
cell_169 and cell_236 -> real model probability sources, blocked by item #32 gates.
```

## Implemented app output

```text
manifests/AI_FINAL_PROBABILITY_OVERLAY_GATE_V7_2.json
```

## Replacement contract

```text
Probability overlay gate/readiness manifest only.
Do not use geemap.
Do not import Earth Engine.
Do not import torch.
Do not run model inference.
Do not create probability maps.
Do not create overlay tiles.
Do not create markers.
Do not write GeoJSON or KMZ.
Do not expose exact coordinates.
Keep output local/private and filesystem-only.
```

## Future private outputs if later approved

```text
AI_INFERENCE_STAGE5/AI_MODEL_PROBABILITIES_640.npy
QA/AI_MODEL_ARCHAEO_INFERENCE_17M_V7_2.csv
QA/AI_MODEL_ARCHAEO_INFERENCE_17M_V7_2.json
manifests/AI_FINAL_PROBABILITY_OVERLAY_REDACTED_SUMMARY_V7_2.json
```

## Validation done

```text
final probability overlay gate parity test passed.
ai final inference gate parity test passed.
metal fingerprint diagnostic parity test passed.
operator overlay implementation design parity test passed after updating stale #38 family/tab expectations.
local existing run wrote manifests/AI_FINAL_PROBABILITY_OVERLAY_GATE_V7_2.json.
Report name confirmed as AI_FINAL_PROBABILITY_OVERLAY_GATE_V7_2.json.
Schema version confirmed as plan_b39_final_probability_overlay_gate_v1.
source_cell confirmed as cell_238.
status confirmed as implemented_probability_overlay_gate_only.
privacy confirmed as FILESYSTEM_ONLY.
http_servable, frontend_visible, and downloadable_via_api confirmed False.
uses_geemap, imports_earth_engine, imports_torch, and runs_model_inference confirmed False.
creates_probability_map, creates_overlay_tiles, creates_markers, creates_geojson, and creates_kmz confirmed False.
exposes_exact_coordinates, raw_geometry_in_manifest, and exact_coordinates_in_manifest confirmed False.
item #32 inference gate and item #38 live overlay manifest confirmed present.
item #32 real inference approved confirmed False.
probability_map_exists and target_records_exist confirmed False.
approved_for_probability_overlay confirmed False.
gate count confirmed as 7.
layer count confirmed as 4.
future probability map path confirmed as AI_INFERENCE_STAGE5/AI_MODEL_PROBABILITIES_640.npy.
next dependency-unblocking item confirmed as Plan B item #40 or approved continuation of #39 after real probability maps exist.
```

## Privacy/artifact policy

```text
Output is a local JSON manifest only.
No coordinates, raw geometry, model weights, model artifact, model execution, inference result, probability map, target CSV/JSON, GeoJSON, KMZ, public API artifact, or frontend artifact is created.
```

## Remaining validation

```text
Compare against frozen notebook outputs after reference files are selected/generated.
Real overlay/marker creation remains blocked until real #32 probability outputs and privacy/operator gates are approved.
```

## Next item

```text
Plan B item #40: GPS/path tracing from targets.
```
