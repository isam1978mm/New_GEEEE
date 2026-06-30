# Plan B1 Remaining Work Checklist

Rule: Do not mark any item Full unless the app output is compared against frozen notebook reference output from the same export/run, or the item is explicitly documented as notebook-no-export.

Rule: Do not compare app output to itself.

Rule: Do not use different run/grid outputs for parity decisions.

---

## Current B1 status

### #23 — AI_FOCUS_17M outputs

Status: Full — committed and pushed in `8ab7f0b`.

Notebook export family:
- `AI_FOCUS_17M_PIXEL_REPORT_V7_2.csv`
- `AI_FOCUS_17M_TARGETS_V7_2.csv`
- `AI_FOCUS_17M_TARGETS_V7_2.geojson`

Completed:
- [x] Frozen notebook references created under private `plan_b_23_focus_17m` folder.
- [x] Notebook hashes recorded.
- [x] Notebook source cell inspected: cell 123.
- [x] Same-export app harness built.
- [x] App helper patched to notebook-compatible output shape.
- [x] Unit tests updated for notebook-compatible #23 fields.
- [x] Same-export comparison passed:
  - CSV schemas and values matched.
  - GeoJSON structure/properties/coordinates matched.
  - `full_pass: True`.
- [x] Focused validation tests passed.
- [x] Docs updated.
- [x] Commit pushed.

Remaining:
- [x] No remaining #23 Plan B1 implementation gap.

---

### #24 — AI_HARD_TYPE_CLASSIFIER_CORE9

Status: Full — committed and pushed in `acca221`; final status docs pushed in `bb10358`.

Notebook export family:
- `AI_HARD_TYPE_CLASSIFIER_CORE9.csv`
- `AI_HARD_TYPE_CLASSIFIER_CORE9.json`
- `AI_HARD_TYPE_CLASSIFIER_CORE9.txt`

Completed:
- [x] Notebook files frozen.
- [x] App source identified.
- [x] Same-export raster inputs found.
- [x] Same-export raster grids verified.
- [x] Algorithm parity patch applied.
- [x] CSV notebook schema matched.
- [x] Same-export tolerant JSON comparison passed.
- [x] TXT comparison passed.
- [x] Same-export final comparison result:
  - `full_pass: True`
  - `json_max_numeric_delta: 0.0002373773411933`
- [x] Focused validation tests passed.
- [x] Docs updated.
- [x] Commit pushed.

Remaining:
- [x] No remaining #24 Plan B1 implementation gap.

---

### #25 — AI_CORE_RING_SCENE outputs

Status: Full — committed and pushed in `5f7cf9c`.

Notebook export family:
- `AI_CORE_RING_SCENE_TARGETS_V7_2C.csv`
- `AI_CORE_RING_SCENE_DECISION_V7_2C.json`
- `AI_CORE_RING_SCENE_DECISION_V7_2C.txt`

Completed:
- [x] Frozen notebook references created under private `plan_b_25_core_ring_scene` folder.
- [x] Notebook hashes recorded.
- [x] Notebook source cell inspected: cell 121.
- [x] Same-export app harness built.
- [x] App helper patched to direct notebook cell 121 logic.
- [x] Unit tests updated for notebook-compatible #25 fields.
- [x] Same-export comparison passed:
  - CSV matched.
  - TXT matched.
  - JSON flat key set matched.
  - JSON shared mismatches: `0`.
  - `full_pass: True`.
- [x] Focused validation tests passed.
- [x] Docs updated.
- [x] Commit pushed.

Remaining:
- [x] No remaining #25 Plan B1 implementation gap.

---

### #33 — AI_METAL_FINGERPRINT_DIAGNOSTIC_V7_2

Status: Partial / app-port only / notebook-current-cell has no file export.

Completed:
- [x] App emits:
  - `AI_METAL_FINGERPRINT_DIAGNOSTIC_V7_2.csv`
  - `AI_METAL_FINGERPRINT_DIAGNOSTIC_V7_2.json`
  - `AI_METAL_FINGERPRINT_DIAGNOSTIC_V7_2.txt`
- [x] Notebook cell exists for metal diagnostic.
- [x] Notebook cell checked for export/write lines.
- [x] Current notebook cell does not export #33 files.
- [x] Status documented.

Remaining:
- [x] Keep #33 blocked unless a real notebook export is added later.
- [x] Do not rerun expecting #33 files from current notebook.
- [x] Do not mark #33 Full without notebook export or explicit notebook-no-export acceptance.

---

## Final Plan B1 closure checklist

Implementation status:
- [x] #23 completed with same-export parity proof.
- [x] #24 completed with same-export parity proof.
- [x] #25 completed with same-export parity proof.
- [x] #33 documented as app-port-only / notebook-current-no-export.

Validation status:
- [x] Focused B1 tests passed for #23/#24/#25 work.
- [x] Artifact inventory tests passed during focused validation.
- [x] Git status was clean after each pushed item.
- [x] Pushed commits exist on `origin/main`.

Remaining:
- [ ] Optional: confirm remote CI status if GitHub Actions exposes a check for the latest commit.
- [ ] Optional: run the full unit suite if time allows.

---

## Next immediate action

No #23/#24/#25 Plan B1 implementation gap remains open.

Next work should start only after choosing a new Plan B item or deciding how to handle #33:
- keep #33 as app-port-only/no-export documented status, or
- add a real notebook export for #33 and rerun the freeze/compare workflow.
