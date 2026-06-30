# Plan B1 #25 Freeze / Parity Status

## Item

Plan B1 #25 — `AI_CORE_RING_SCENE_*_V7_2C` outputs.

Notebook source cell inspected:

- `CELL_INDEX: 121`
- `CELL 005C — CORE-vs-RING-vs-SCENE SCIENTIFIC DECISION`

Notebook frozen reference folder:

- `C:\Dev\New_GEE_PRIVATE\FROZEN_NOTEBOOK_REFS\plan_b_25_core_ring_scene\notebook_outputs`

Frozen notebook files:

- `AI_CORE_RING_SCENE_TARGETS_V7_2C.csv`
- `AI_CORE_RING_SCENE_DECISION_V7_2C.txt`
- `AI_CORE_RING_SCENE_DECISION_V7_2C.json`

## Notebook hashes

```text
AI_CORE_RING_SCENE_DECISION_V7_2C.json
20482671BFA65F8F49B8EF5F5F38EE5C858AFAFE881B15FB159C399F3175E9E8

AI_CORE_RING_SCENE_DECISION_V7_2C.txt
759258029C440C594471F2595E009B6F1BD9BB3BA660592EB947C35B75A3B6AE

AI_CORE_RING_SCENE_TARGETS_V7_2C.csv
04A66FA6FEB97EB1046D8AA557F1EE8CA483090CBD92672C223D5A170925D3E1
```

## App implementation status

Status: **Complete / same-export parity passed**.

The app now implements the notebook cell 121 logic directly for #25 instead of deriving the decision from the hard-type classifier wrapper.

Implemented behavior:

- Uses `focus_mask` as the core mask.
- Builds near/far/scene masks using the notebook cell 121 ring logic.
- Computes robust stats, effect sizes, and robust contrasts from the analysis bands.
- Computes notebook-compatible `void_score`, `entrance_score`, `metal_score`, and `pottery_score`.
- Computes notebook-compatible probabilities, reliability, detection confidence, interpretation confidence, final confidence, decision grade, scenario, entrance type, metal type, room count, content inference, burial style, directionality, and resolution note.
- Writes notebook-compatible CSV, TXT, and flat JSON output contracts.
- Preserves private filesystem-only artifact handling.

Special parity note:

- The downloaded single-band `AI_READY_640_Secret_Hidden_Doors.tif` stores some notebook hypercube sentinel values as `NaN`.
- For #25 `band_analysis` parity only, the app restores those `NaN` scene values to the notebook sentinel value so the frozen JSON matches the notebook export.
- This is intentionally scoped to #25 band-analysis parity and does not change global raster handling.

## Same-export comparison result

Comparison report:

- `C:\Dev\New_GEE_PRIVATE\FROZEN_NOTEBOOK_REFS\plan_b_25_core_ring_scene\comparison_reports\plan_b25_same_export_after_patch_summary.json`

Result:

```text
CSV
columns_match: True
row_count_match: True
shared_value_mismatch_count: 0

JSON
top_level_type_match: True
keys_only_in_notebook_count: 0
keys_only_in_app_count: 0
shared_value_mismatch_count: 0
max_numeric_delta: 1.3E-13

TXT
match_normalized_newlines: True

full_pass: True
```

## Local validation

Focused local validation passed:

```text
python -m py_compile .\app\pipeline\stages\focus_mask.py
python -m pytest tests/unit/test_focus_mask.py tests/unit/test_forbidden_terms.py tests/unit/test_full_job_artifact_inventory.py -q

4 passed
```

## Privacy

All notebook references and same-export snapshots remain under the private `New_GEE_PRIVATE` frozen-reference tree. No coordinates, raw arrays, KMZs, or private target geometry are documented in the public repo.
