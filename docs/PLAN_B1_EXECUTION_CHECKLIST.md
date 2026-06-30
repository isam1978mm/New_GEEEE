# Plan B1 — Execution Checklist

Status: current B1 tracking document.

This checklist tracks Plan B1 notebook-reference parity work. It must stay aligned with the item-specific status docs and with `docs/PLAN_B1_REMAINING_CHECKLIST.md`.

## B1 rule

`Partial` means the app output exists and passed output-proof, but it has not yet been compared against frozen notebook reference outputs.

`Full` means the app output has been verified against frozen notebook reference outputs for the selected notebook cell/output family.

Do not mark an item `Full` just because the app writes files or tests pass. App output proof and frozen notebook parity are separate gates.

## Public/private boundary

Private reference root:

```text
C:\Dev\New_GEE_PRIVATE\FROZEN_NOTEBOOK_REFS\
```

Public repo may contain:

```text
comparison code
test scaffolding
redacted/hash manifests
docs explaining parity status
small non-sensitive fixtures only when explicitly approved
```

Public repo must not contain:

```text
exact coordinates
raw target geometry
private KMZ/KML/GeoJSON outputs
private target CSVs with sensitive location columns
raw probability maps
large raster/NPY reference outputs
model weights
private notebook run folders
```

## Universal item checklist

Each Plan B1 item must pass this checklist before status changes from `Partial` to `Full`:

```text
[x] canonical notebook cell documented
[x] notebook output family documented
[x] app owner stage/module documented
[x] app output path documented
[x] artifact class/privacy documented
[x] existing notebook reference outputs located, or no-export status explicitly documented
[x] references copied to private frozen-reference folder when available
[x] SHA256 hash recorded for each reference file when available
[x] comparison method documented when refs exist
[x] app output generated from comparable input/run when refs exist
[x] comparison report written when refs exist
[x] comparison passes within approved rules/tolerances, or item remains blocked/no-export
[x] no private raw reference output committed publicly
[x] aggregate Plan B table/checklist updated
```

## Phase 1 — concrete local outputs

### #23 — ROI-constrained AI analysis inside 17m focus

```text
Status: Full
Canonical cell: cell_123
Output family:
  AI_FOCUS_17M_PIXEL_REPORT_V7_2.csv
  AI_FOCUS_17M_TARGETS_V7_2.csv
  AI_FOCUS_17M_TARGETS_V7_2.geojson
App owner stage: FocusMaskStage
Privacy: FILESYSTEM_ONLY/private coordinate-bearing outputs
Pushed commit: 8ab7f0b feat: align focus 17m outputs with notebook
Status doc: docs/PLAN_B1_23_FREEZE_STATUS.md
```

Checklist:

```text
[x] notebook refs frozen privately
[x] SHA256 hashes recorded
[x] notebook cell 123 inspected
[x] same-export app harness built
[x] pixel CSV schema/row count/values matched
[x] target CSV schema/row count/values matched
[x] GeoJSON structure/properties/coordinates matched privately
[x] app helper patched to notebook-compatible output shape
[x] unit tests updated
[x] focused tests passed
[x] committed and pushed
```

### #24 — Hard classifier

```text
Status: Full
Canonical cell: cell_128
Output family:
  AI_HARD_TYPE_CLASSIFIER_CORE9.csv
  AI_HARD_TYPE_CLASSIFIER_CORE9.txt
  AI_HARD_TYPE_CLASSIFIER_CORE9.json
App owner stage: FocusMaskStage
Privacy: FILESYSTEM_ONLY
Pushed commit: acca221 feat: align hard type classifier with notebook
Status doc: docs/PLAN_B1_24_FREEZE_STATUS.md
```

Checklist:

```text
[x] notebook refs frozen privately
[x] SHA256 hashes recorded
[x] same-export raster inputs found
[x] same-export raster grids verified
[x] algorithm parity patch applied
[x] CSV schema and row count matched
[x] JSON comparison passed within approved tolerance
[x] TXT comparison passed
[x] focused tests passed
[x] committed and pushed
```

### #25 — Core-vs-ring-vs-scene decision

```text
Status: Full
Canonical cell: cell_121
Output family:
  AI_CORE_RING_SCENE_TARGETS_V7_2C.csv
  AI_CORE_RING_SCENE_DECISION_V7_2C.txt
  AI_CORE_RING_SCENE_DECISION_V7_2C.json
App owner stage: FocusMaskStage
Privacy: FILESYSTEM_ONLY
Pushed commit: 5f7cf9c feat: align core ring scene decision with notebook
Status doc: docs/PLAN_B1_25_FREEZE_STATUS.md
```

Checklist:

```text
[x] notebook refs frozen privately
[x] SHA256 hashes recorded
[x] notebook cell 121 inspected
[x] app gap proven by same-export comparison
[x] app helper patched to direct cell-121 logic
[x] CSV schema/row count/values matched
[x] TXT output matched
[x] JSON flat key set and values matched
[x] focused tests passed
[x] committed and pushed
```

### #33 — Metal fingerprint diagnostic

```text
Status: app-port / notebook-current-no-export
Canonical cell: cell_185
Notebook family: AI_METAL_FINGERPRINT_DIAGNOSTIC_V7_2
App owner stage: FocusMaskStage
App outputs:
  full_job/focus/AI_METAL_FINGERPRINT_DIAGNOSTIC_V7_2.csv
  full_job/focus/AI_METAL_FINGERPRINT_DIAGNOSTIC_V7_2.json
  full_job/focus/AI_METAL_FINGERPRINT_DIAGNOSTIC_V7_2.txt
Privacy: FILESYSTEM_ONLY
Pushed commit: fbccd02 feat: emit metal fingerprint diagnostic from focus stage
Status doc: docs/PLAN_B1_33_FREEZE_STATUS.md
```

Checklist:

```text
[x] app owner stage emits outputs
[x] outputs registered as FILESYSTEM_ONLY artifacts
[x] focused parity/unit/inventory tests passed locally
[x] app-owned output patch pushed to main
[x] notebook cell inspected
[x] current notebook cell does not export #33 CSV/JSON/TXT files
[x] status documented as app-port / notebook-current-no-export
[ ] do not mark Full unless a real notebook export appears or no-export status is explicitly accepted as final
```

## Remaining concrete output families not closed by this Plan B1 pass

### #26 — GeoJSON detected-feature exports

```text
Status: Pending
Canonical cell: cell_123
Output:
  AI_FOCUS_17M_DETECTED_FEATURES_WGS84_V7_2.geojson
Privacy: private exact or redacted public summary only
```

```text
[ ] freeze notebook GeoJSON privately
[ ] hash ref
[ ] compare feature count
[ ] compare geometry privately within tolerance
[ ] compare key properties
[ ] write redacted public summary only
[ ] mark Full or document mismatch
```

### #27 — KMZ heatmap / 3D target visualization

```text
Status: Pending
Canonical cell: cell_155
Outputs:
  AI_HEATMAP_CLASSIFICATION.png
  AI_HEATMAP_CLASSIFICATION.kmz
  AI_3D_TARGET_VISUALIZATION.kmz
Privacy: FILESYSTEM_ONLY/private exact or redacted summary
```

```text
[ ] freeze notebook refs privately
[ ] hash refs
[ ] compare PNG dimensions/hash or approved visual metric
[ ] compare KMZ package contents
[ ] compare KML feature count/properties privately
[ ] write redacted public comparison summary
[ ] mark Full or document mismatch
```

### #34 — Field-operation KMZ outputs

```text
Status: Pending
Canonical cell: cell_200
Outputs:
  FINAL_ARCHEO_INTELLIGENCE_MAP.geojson
  TESLA_V7_2_FIELD_OPERATIONS.kmz
Privacy: FILESYSTEM_ONLY/private exact or redacted summary
```

```text
[ ] freeze notebook refs privately
[ ] hash refs
[ ] compare GeoJSON privately
[ ] compare KMZ/KML privately
[ ] write redacted public comparison summary
[ ] mark Full or document mismatch
```

## Phase 2 — tensor/raster parity

```text
#8 Nano / treasure / geophysics stacks
[ ] cells 037 and 039 documented
[ ] refs frozen
[ ] shape/dtype/band-order/nodata/value comparison complete
[ ] status updated

#9 More feature stacks / rename layers
[ ] cells 050, 053, 051, 047, 052, 054 documented
[ ] refs frozen
[ ] stack names/band order/shape/dtype/value comparison complete
[ ] status updated

#15 Bonus / simulator features
[ ] cells 072 and 073 documented
[ ] refs frozen
[ ] comparison complete
[ ] status updated

#17 Extra S2 era pulls / masks
[ ] cell 077 documented
[ ] refs frozen
[ ] mask/tensor comparison complete
[ ] status updated

#18 DEM-matched S2 masks
[ ] cell 081 documented
[ ] refs frozen
[ ] mask shape/dtype/nodata/value comparison complete
[ ] status updated

#19 Tesla v7.2 inference engines
[ ] cell 095 documented
[ ] refs frozen
[ ] implemented app stack compared to notebook stack
[ ] status updated

#20 Fusion center / intelligence tensors
[ ] cell 099 documented
[ ] refs frozen
[ ] tensor comparison complete
[ ] status updated

#29 AI tensor builder
[ ] cell 148 documented
[ ] refs frozen
[ ] tensor families/manifests compared
[ ] status updated
```

## Phase 3 — gated/replacement parity

```text
#28 AI requirements mapper
[ ] cell 140 documented
[ ] replacement manifest compared
[ ] Full gate parity or mismatch documented

#30 Training workflow boundary
[ ] cell 166 documented
[ ] boundary manifest compared
[ ] Full gate parity or mismatch documented

#31 Model build policy
[ ] cell 232 documented
[ ] policy manifest compared
[ ] Full gate parity or mismatch documented

#32 Final inference gate
[ ] cell 169 documented
[ ] inference-readiness gate compared
[ ] no real inference executed
[ ] Full gate parity or mismatch documented

#39 Probability overlay gate
[ ] cell 238 documented
[ ] probability-overlay gate compared
[ ] no real probability map/overlay created
[ ] Full gate parity or mismatch documented

#40 GPS/path tracing gate
[ ] cell 242 documented
[ ] GPS/path-tracing gate compared
[ ] no real path trace created unless approved
[ ] Full gate parity or mismatch documented
```

## Working order

```text
1. #23, #24, and #25 are complete/full for same-export parity.
2. #33 remains app-port / notebook-current-no-export unless a real notebook export appears.
3. Next concrete parity candidates: #26, #27, #34.
4. Then tensor/raster items #8, #9, #15, #17, #18, #19, #20, #29.
5. Finish gated/replacement items #28, #30, #31, #32, #39, #40.
```

## Immediate next task

```text
Choose next item from #26, #27, or #34. Do not continue #33 unless a real notebook export is produced or no-export status is explicitly accepted as final.
```
