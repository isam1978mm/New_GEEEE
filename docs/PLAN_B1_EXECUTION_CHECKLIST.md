# Plan B1 — Execution Checklist

Status: active B1 tracking document.

This checklist converts `docs/PLAN_B1_FROZEN_NOTEBOOK_REFERENCE_PARITY.md` into a working execution tracker. Use it before any Plan B1 code or parity-status change.

## B1 rule

`Partial` means the app output exists and passed output-proof, but it has not yet been compared against frozen notebook reference outputs.

`Full` means the app output has been verified against frozen notebook reference outputs for the selected notebook cell/output family.

Do not mark an item `Full` just because the app writes files or tests pass. App output proof and frozen notebook parity are separate gates.

## Public/private boundary

Private reference root:

```text
C:\Dev\New_GEE_PRIVATE\FROZEN_NOTEBOOK_REFS\
```

Per-item private layout:

```text
C:\Dev\New_GEE_PRIVATE\FROZEN_NOTEBOOK_REFS\plan_b_<ITEM>_cell_<CELL>\
  reference_manifest.json
  notebook_outputs\
  app_outputs_snapshot\
  comparison_reports\
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
[ ] canonical notebook cell documented
[ ] notebook output family documented
[ ] app owner stage/module documented
[ ] app output path documented
[ ] artifact class/privacy documented
[ ] existing notebook reference outputs located
[ ] references copied to private frozen-reference folder
[ ] SHA256 hash recorded for each reference file
[ ] comparison method documented
[ ] app output generated from comparable input/run
[ ] app output snapshot copied privately when needed
[ ] comparison report written
[ ] comparison passes within approved rules/tolerances
[ ] no private raw reference output committed publicly
[ ] aggregate Plan B table updated
```

## Comparison rules

### NPY/raster tensors

```text
[ ] same shape
[ ] same dtype or approved dtype conversion
[ ] same finite/nodata policy
[ ] same band order when stacked
[ ] numeric values match within approved tolerance
```

### CSV

```text
[ ] same required columns
[ ] same row count
[ ] same stable key fields
[ ] same text/category labels
[ ] numeric columns match within approved tolerance
[ ] volatile columns ignored only if documented
```

### JSON

```text
[ ] same required schema fields
[ ] same stable values
[ ] same record counts
[ ] numeric values match within approved tolerance
[ ] run IDs/local paths/timestamps normalized only if documented
```

### TXT

```text
[ ] same required section titles
[ ] same source cell markers
[ ] same record counts
[ ] same important result lines
[ ] formatting-only differences documented if accepted
```

### GeoJSON/KMZ/KML

These are private unless explicitly redacted.

Private exact mode:

```text
[ ] same feature count
[ ] geometry matches within tolerance
[ ] key non-volatile properties match
```

Redacted public mode:

```text
[ ] same feature count
[ ] same non-sensitive properties
[ ] no exact coordinates exposed in public report
[ ] no raw geometry exposed in public report
```

### Gate manifests

Gate-only items may become `Full gate parity` against the approved safe replacement contract. They are not full live-notebook behavior unless real model/probability/path outputs are later approved and implemented.

## Phase 1 — concrete local outputs

### #33 — Metal fingerprint diagnostic

```text
Status: app-owned output now implemented and pushed
Current app commit: fbccd02 feat: emit metal fingerprint diagnostic from focus stage
Canonical cell: cell_185
Notebook family: AI_METAL_FINGERPRINT_DIAGNOSTIC_V7_2
App owner stage: FocusMaskStage
App outputs:
  full_job/focus/AI_METAL_FINGERPRINT_DIAGNOSTIC_V7_2.csv
  full_job/focus/AI_METAL_FINGERPRINT_DIAGNOSTIC_V7_2.json
  full_job/focus/AI_METAL_FINGERPRINT_DIAGNOSTIC_V7_2.txt
Privacy: FILESYSTEM_ONLY
```

Checklist:

```text
[x] app parity module exists
[x] app owner stage emits outputs
[x] outputs registered as FILESYSTEM_ONLY artifacts
[x] focused parity/unit/inventory tests passed locally
[x] app-owned output patch pushed to main
[ ] existing notebook CSV/JSON/TXT located
[ ] notebook refs copied privately
[ ] SHA256 hashes recorded
[ ] app output snapshot copied privately
[ ] CSV comparison report written
[ ] JSON comparison report written
[ ] TXT comparison report written
[ ] status updated from Partial to Full if comparisons pass
```

### #24 — Hard classifier

```text
Status: Partial
Canonical cell: cell_128
Output family:
  AI_HARD_TYPE_CLASSIFIER_CORE9.csv
  AI_HARD_TYPE_CLASSIFIER_CORE9.txt
  AI_HARD_TYPE_CLASSIFIER_CORE9.json
Privacy: FILESYSTEM_ONLY
```

Checklist:

```text
[ ] confirm app owner stage emits files in full run
[ ] freeze notebook refs privately
[ ] hash refs
[ ] compare CSV required columns/row count/stable values
[ ] compare JSON schema/stable values
[ ] compare TXT title/source markers/record count
[ ] write comparison report
[ ] mark Full or document mismatch
```

### #25 — Target CSV/TXT/JSON outputs

```text
Status: Partial
Canonical cell: cell_121
Output family:
  AI_CORE_RING_SCENE_TARGETS_V7_2C.csv
  AI_CORE_RING_SCENE_DECISION_V7_2C.txt
  AI_CORE_RING_SCENE_DECISION_V7_2C.json
Privacy: FILESYSTEM_ONLY
```

Checklist:

```text
[ ] confirm app-owned output paths
[ ] freeze notebook refs privately
[ ] hash refs
[ ] compare CSV row count/stable fields/numeric tolerances
[ ] compare JSON stable schema and values
[ ] compare TXT sections/source markers
[ ] write comparison report
[ ] mark Full or document mismatch
```

### #26 — GeoJSON detected-feature exports

```text
Status: Partial
Canonical cell: cell_123
Output:
  AI_FOCUS_17M_DETECTED_FEATURES_WGS84_V7_2.geojson
Privacy: private exact or redacted public summary only
```

Checklist:

```text
[ ] confirm app output exists
[ ] freeze notebook GeoJSON privately
[ ] hash ref
[ ] compare feature count
[ ] compare geometry privately within tolerance
[ ] compare key properties
[ ] write redacted public summary only
[ ] mark Full or document mismatch
```

### #23 — ROI-constrained AI analysis inside 17m focus

```text
Status: Partial
Canonical cell: cell_119
Output family:
  AI_FOCUS_17M_PIXEL_REPORT_V7_2.csv
  AI_FOCUS_17M_TARGETS_V7_2.csv
  AI_FOCUS_17M_TARGETS_V7_2.geojson
Privacy: FILESYSTEM_ONLY/private coordinate-bearing outputs
```

Checklist:

```text
[ ] confirm app output files
[ ] freeze notebook refs privately
[ ] hash refs
[ ] compare pixel CSV schema/row count/numeric values
[ ] compare target CSV stable fields
[ ] compare GeoJSON privately or redacted
[ ] write comparison report
[ ] mark Full or document mismatch
```

### #27 — KMZ heatmap / 3D target visualization

```text
Status: Partial
Canonical cell: cell_155
Outputs:
  AI_HEATMAP_CLASSIFICATION.png
  AI_HEATMAP_CLASSIFICATION.kmz
  AI_3D_TARGET_VISUALIZATION.kmz
Privacy: FILESYSTEM_ONLY/private exact or redacted summary
```

Checklist:

```text
[ ] confirm app output files
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
Status: Partial
Canonical cell: cell_200
Outputs:
  FINAL_ARCHEO_INTELLIGENCE_MAP.geojson
  TESLA_V7_2_FIELD_OPERATIONS.kmz
Privacy: FILESYSTEM_ONLY/private exact or redacted summary
```

Checklist:

```text
[ ] confirm app output files
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
1. Finish #33 frozen-reference comparison.
2. Continue #24, #25, #26, #23, #27, #34.
3. Then tensor/raster items #8, #9, #15, #17, #18, #19, #20, #29.
4. Finish gated/replacement items #28, #30, #31, #32, #39, #40.
```

## Immediate next task

```text
#33 freeze task:
[ ] locate notebook-generated AI_METAL_FINGERPRINT_DIAGNOSTIC_V7_2 CSV/JSON/TXT
[ ] copy refs into private folder
[ ] hash refs
[ ] generate comparable app outputs
[ ] compare app outputs to refs
[ ] write comparison report
```
