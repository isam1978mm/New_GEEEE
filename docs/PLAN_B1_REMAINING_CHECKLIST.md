# Plan B1 Remaining Work Checklist

Rule: Do not mark any item Full unless the app output is compared against frozen notebook reference output from the same export/run, or the item is explicitly documented as notebook-no-export.

Rule: Do not compare app output to itself.

Rule: Do not use different run/grid outputs for parity decisions.

---

## Current B1 status

### #24 — AI_HARD_TYPE_CLASSIFIER_CORE9

Status: Full — committed and pushed in acca221.

Completed:
- [x] Notebook files frozen:
  - AI_HARD_TYPE_CLASSIFIER_CORE9.csv
  - AI_HARD_TYPE_CLASSIFIER_CORE9.json
  - AI_HARD_TYPE_CLASSIFIER_CORE9.txt
- [x] App source identified:
  - app/pipeline/stages/focus_mask.py
- [x] Same-export raster inputs found.
- [x] Same-export raster grids verified.
- [x] Algorithm parity patch applied.
- [x] CSV notebook schema now matches.
- [x] Same-export tolerant JSON comparison passed.
- [x] TXT comparison passed.
- [x] Same-export final comparison result:
  - full_pass: True
  - json_max_numeric_delta: 0.0002373773411933

Remaining:
- [x] Run focused tests after final mask-source label patch.
- [x] Run same-export comparison one final time.
- [x] Update docs/PLAN_B1_24_FREEZE_STATUS.md from Partial to Full.
- [x] Commit #24 code/test/checklist changes.
- [x] Push #24 commit.
- [ ] Confirm CI result.

---

### #33 — AI_METAL_FINGERPRINT_DIAGNOSTIC_V7_2

Status: Partial / app-port only / notebook has no file export.

Completed:
- [x] App emits:
  - AI_METAL_FINGERPRINT_DIAGNOSTIC_V7_2.csv
  - AI_METAL_FINGERPRINT_DIAGNOSTIC_V7_2.json
  - AI_METAL_FINGERPRINT_DIAGNOSTIC_V7_2.txt
- [x] Notebook cell exists for metal diagnostic.
- [x] Notebook cell checked for export/write lines.
- [x] Current notebook cell does not export #33 files.
- [x] Status documented.

Remaining:
- [ ] Keep #33 blocked unless a real notebook export is added later.
- [ ] Do not rerun expecting #33 files from current notebook.
- [ ] Do not mark #33 Full without notebook export or explicit “no-export” acceptance.

---

### #23 — AI_FOCUS_17M outputs

Status: Not completed in B1 freeze/parity workflow yet.

Known notebook export family:
- AI_FOCUS_17M_PIXEL_REPORT_V7_2.csv
- AI_FOCUS_17M_TARGETS_V7_2.csv
- AI_FOCUS_17M_TARGETS_V7_2.geojson

Remaining:
- [ ] Freeze notebook #23 files into private reference folder.
- [ ] Hash notebook #23 files.
- [ ] Identify app owner stage/source.
- [ ] Generate or locate comparable same-export app output.
- [ ] Compare CSV schemas.
- [ ] Compare CSV values.
- [ ] Compare GeoJSON structure safely without exposing private coordinates.
- [ ] Patch app only if same-export mismatch proves an app gap.
- [ ] Add/update tests.
- [ ] Document #23 status.
- [ ] Commit and push only after proof.

---

### #25 — AI_CORE_RING_SCENE outputs

Status: Not completed in B1 freeze/parity workflow yet.

Known notebook export family:
- AI_CORE_RING_SCENE_TARGETS_V7_2C.csv
- AI_CORE_RING_SCENE_DECISION_V7_2C.json
- AI_CORE_RING_SCENE_DECISION_V7_2C.txt

Remaining:
- [ ] Freeze notebook #25 files into private reference folder.
- [ ] Hash notebook #25 files.
- [ ] Identify app owner stage/source.
- [ ] Generate or locate comparable same-export app output.
- [ ] Compare CSV schema and values.
- [ ] Compare JSON contract.
- [ ] Compare TXT output.
- [ ] Patch app only if same-export mismatch proves an app gap.
- [ ] Add/update tests.
- [ ] Document #25 status.
- [ ] Commit and push only after proof.

---

## Final Plan B1 closure checklist

Remaining:
- [x] #24 committed and pushed.
- [ ] #23 completed or explicitly documented as blocked.
- [x] #25 completed or explicitly documented as blocked.
- [ ] #33 documented as notebook-no-export / app-port-only unless new export exists.
- [ ] Run focused B1 tests.
- [ ] Run artifact inventory tests.
- [ ] Run full unit suite if time allows.
- [ ] Confirm git status clean.
- [ ] Confirm pushed commit exists on origin/main.
- [ ] Update final B1 status document.

---

## Next immediate action

Finish #24 first because same-export parity already passed.

Next commands:
1. Run focused tests after label patch.
2. Update #24 status doc to Full.
3. Commit and push #24.

## Plan B1 #23 final status

Status: Full locally — pending commit/push at time of writing.

- [x] Freeze notebook #23 references.
- [x] Inspect notebook cell 123 contract.
- [x] Patch app #23 helper to notebook-compatible output shape.
- [x] Patch unit test expectations for notebook-compatible #23 fields.
- [x] Run forbidden-term test.
- [x] Run same-export comparison.
- [x] Same-export comparison full_pass: True.
- [x] Run focused validation tests.
- [ ] Commit #23 code/test/docs.
- [ ] Push #23 commit.

## Plan B1 #25 completion note

Status: **complete**.

#25 `AI_CORE_RING_SCENE_*_V7_2C` now matches notebook cell 121 on the same downloaded notebook export.

Evidence:

- Frozen notebook refs exist under `C:\Dev\New_GEE_PRIVATE\FROZEN_NOTEBOOK_REFS\plan_b_25_core_ring_scene\notebook_outputs`.
- Same-export comparison report: `comparison_reports\plan_b25_same_export_after_patch_summary.json`.
- Comparison result: CSV matched, TXT matched, JSON flat key set matched, JSON shared mismatches `0`, `full_pass: True`.
- Focused tests passed: `4 passed`.

Next Plan B1 item: no remaining #23/#24/#25 implementation gap is open. #33 remains app-port/docs status only unless a real notebook export appears.

