# Plan B1 — Execution Checklist

Status: active roadmap/tracking document after B1 closure pass.

This checklist tracks Plan B1 notebook-reference parity work. It must stay aligned with the item-specific status docs and with `docs/PLAN_B1_REMAINING_CHECKLIST.md`.

## Current Plan B roadmap after B1 closure

Plain-English status:

```text
Closed in this B1 closure pass:
- #23 AI_FOCUS_17M outputs: Full same-export parity.
- #24 AI_HARD_TYPE_CLASSIFIER_CORE9: Full same-export parity.
- #25 AI_CORE_RING_SCENE_*_V7_2C: Full same-export parity.

Blocked/documented in this B1 closure pass:
- #33 AI_METAL_FINGERPRINT_DIAGNOSTIC_V7_2: app-port only / notebook-current-no-export.
  Do not mark Full unless a real notebook export appears or explicit no-export acceptance is approved.

Not closed by this B1 closure pass:
- #26 detected-feature GeoJSON: app-enhanced local contract; blocked for Full exact-file parity.
- #34 field-operation GeoJSON/KMZ.
- Phase 2 tensor/raster parity items.
- Phase 3 gated/replacement parity items.
```

Next pass order:

```text
1. B1-Followup concrete outputs:
   #26 is app-enhanced local / blocked for Full exact-file parity; then close #27, then #34.

2. Phase 2 tensor/raster parity:
   #8, #9, #15, #17, #18, #19, #20, #29.

3. Phase 3 gated/replacement parity:
   #28, #30, #31, #32, #39, #40.
```

Rule: remaining `Partial` items stay Partial until same-export frozen-reference proof, approved gate parity proof, or explicit blocked/no-export documentation exists.

---

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

## App-goal output policy update

Plan B follow-up work now uses the app-goal policy in `docs/PLAN_B_APP_GOAL_OUTPUT_POLICY.md`.

Important rule:

```text
Do not patch blindly for parity.
Use notebook cells as evidence, but keep the best local/private app contract when it is better for the app goal.
```

For remaining concrete output families, each item must be classified as one of:

```text
Full same-export parity
App-port / notebook-current-no-export
App-enhanced local contract
Production-redaction required
Blocked for Full parity
```

#26 current decision gate:

```text
AI_FOCUS_17M_DETECTED_FEATURES_WGS84_V7_2.geojson
App output exists.
Exact notebook export was not found in the downloaded notebook export.
Exact notebook writer cell for that filename was not found.
Notebook cell 123 writes AI_FOCUS_17M_TARGETS_V7_2.geojson instead.
Current app #26 output does not match the cell 123 GeoJSON contract exactly.
Next #26 step is app-goal schema design, not blind parity patching.
```


## #27 app-enhanced local visualization decision

```text
AI_HEATMAP_CLASSIFICATION.png
AI_HEATMAP_CLASSIFICATION.kmz
AI_3D_TARGET_VISUALIZATION.kmz
Status: app-enhanced local visualization contract.
Full exact-file parity is blocked because exact notebook exports are missing.
Real PNG/KMZ package validation passed after the writer fix.
Production-redaction required.
```

## Remaining concrete output families not closed by this Plan B1 pass

These are the next concrete output families to close before Phase 2 tensor/raster work.

```text
#26 — AI_FOCUS_17M_DETECTED_FEATURES_WGS84_V7_2.geojson
Status:
- App-enhanced local contract.
- Blocked for Full exact-file parity because no exact notebook export/writer exists.
- Production-redaction required before public/API exposure.

Plan:
- keep app-enhanced local output
- retain app classifier/core-ring-scene metadata
- add notebook cell 123 semantic fields when available
- document status in docs/PLAN_B1_26_APP_ENHANCED_STATUS.md
- test, commit, push

#27 — AI_HEATMAP_CLASSIFICATION.png / .kmz and AI_3D_TARGET_VISUALIZATION.kmz
Status:
- app-enhanced local visualization contract
- downloaded notebook export does not contain exact PNG/KMZ refs
- notebook writer candidates exist: cell 139, cell 155, cell 156
- app follows the cell-155-style local package shape with heat.png inside KMZ
- real PNG signature and KMZ package validation passed after #27 writer fix
- production-redaction required for coordinate-bearing KML/KMZ

#34 — FINAL_ARCHEO_INTELLIGENCE_MAP.geojson and TESLA_V7_2_FIELD_OPERATIONS.kmz
Plan:
- freeze notebook GeoJSON/KMZ refs privately
- hash refs
- compare GeoJSON privately
- compare KMZ/KML privately
- document, test, commit, push
```

Do #26 first because it depends directly on the #23 target/GeoJSON contract that is now Full.

---

## Phase 2 — tensor/raster parity

Start Phase 2 only after the remaining concrete output families (#26, #27, #34) are closed or explicitly blocked.

Work order:

```text
1. #8 Nano / treasure / geophysics stacks
2. #9 More feature stacks / rename layers
3. #15 Bonus / simulator features
4. #17 Extra S2 era pulls / masks
5. #18 DEM-matched S2 masks
6. #19 Tesla v7.2 inference engines
7. #20 Fusion center / intelligence tensors
8. #29 AI tensor builder
```

Definition of done for each Phase 2 item:

```text
[ ] canonical notebook cell documented
[ ] notebook raster/tensor output family documented
[ ] private frozen refs copied
[ ] SHA256 hashes recorded
[ ] app output generated from comparable same export/run
[ ] shape comparison passed
[ ] dtype / nodata / finite policy comparison passed
[ ] band order comparison passed
[ ] numeric comparison passed within approved tolerance
[ ] private comparison report written
[ ] public status doc updated without raw private arrays/coordinates
[ ] tests passed
[ ] commit pushed
```

## Phase 3 — gated/replacement parity

Start Phase 3 after Phase 2, unless a specific gate is needed earlier for safety or planning.

Work order:

```text
1. #28 AI requirements mapper
2. #30 Training workflow boundary
3. #31 Model build policy
4. #32 Final inference gate
5. #39 Probability overlay gate
6. #40 GPS/path tracing gate
```

Definition of done for each Phase 3 item:

```text
[ ] canonical notebook cell documented
[ ] replacement/gate contract documented
[ ] proof that no forbidden live behavior is executed unless explicitly approved
[ ] manifest/schema comparison completed
[ ] privacy boundary verified
[ ] tests passed
[ ] status doc updated
[ ] commit pushed
```

Phase 3 items should not be marked as normal numeric Full parity unless they have real frozen notebook outputs and an approved direct comparison path. Otherwise, use `Full gate parity` or `replacement parity` wording.

## Working order

```text
Current state:
- B1 closure pass is done for #23/#24/#25.
- #33 is documented as app-port / notebook-current-no-export.

Next technical pass:
1. #26 detected-feature GeoJSON: app-enhanced local contract / blocked for Full parity.
2. #27 heatmap/3D visualization files.
3. #34 field-operation GeoJSON/KMZ.

Then:
4. Phase 2 tensor/raster parity.
5. Phase 3 gated/replacement parity.
```

## Immediate next task

```text
#26 app-enhanced local contract task:
[x] confirm app-generated AI_FOCUS_17M_DETECTED_FEATURES_WGS84_V7_2.geojson exists
[x] confirm exact notebook export is absent in the downloaded export
[x] inspect notebook candidate cells and closest cell 123 target contract
[x] keep app-enhanced local contract instead of blind parity patch
[x] add notebook semantic fields when available
[x] mark production-redaction required
[ ] commit and push #26 app-enhanced code/test/docs
```

## #26 app-enhanced local contract decision

```text
Status: App-enhanced local contract; blocked for Full exact-file parity.
Output: AI_FOCUS_17M_DETECTED_FEATURES_WGS84_V7_2.geojson
App owner stage: FocusMaskStage
Privacy: FILESYSTEM_ONLY / production-redaction required
Status doc: docs/PLAN_B1_26_APP_ENHANCED_STATUS.md
```

Decision:

```text
Keep the richer app-local #26 output because it is better for local operator use than forcing exact notebook parity.
Do not mark this item Full same-export parity unless a real notebook export for the exact app filename appears later.
```

Current app-enhanced behavior:

```text
[x] app emits the #26 GeoJSON output
[x] top-level metadata remains app-oriented: source cell/family, CRS, privacy
[x] geometry remains WGS84 Point for local/private operator use
[x] app classifier/core-ring-scene fields are retained
[x] notebook cell 123 semantic target fields are added when available
[x] production redaction is required before public/API exposure
```

Notebook evidence:

```text
[x] exact notebook export searched in downloaded export
[x] exact filename was not found
[x] notebook candidate cells inspected
[x] cell 123 writes AI_FOCUS_17M_TARGETS_V7_2.geojson, not the app #26 filename
[x] current app contract is intentionally app-enhanced, not exact parity
```
