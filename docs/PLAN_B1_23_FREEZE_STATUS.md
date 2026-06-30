# Plan B1 #23 Freeze Status — AI_FOCUS_17M outputs

Status: Full locally — pending commit/push at time of writing.

## Notebook reference

Frozen notebook export files:

```text
AI_FOCUS_17M_PIXEL_REPORT_V7_2.csv
AI_FOCUS_17M_TARGETS_V7_2.csv
AI_FOCUS_17M_TARGETS_V7_2.geojson
```

Frozen reference folder:

```text
C:\Dev\New_GEE_PRIVATE\FROZEN_NOTEBOOK_REFS\plan_b_23_focus_17m\notebook_outputs
```

Notebook hash report:

```text
C:\Dev\New_GEE_PRIVATE\FROZEN_NOTEBOOK_REFS\plan_b_23_focus_17m\comparison_reports\plan_b23_notebook_hashes.txt
```

## Source notebook contract

The app was aligned to notebook cell 123:

```text
CELL 005.5 — ROI-CONSTRAINED AI TARGET INFERENCE (17m, NO CROP)
```

This cell owns the #23 output contract:

```text
AI_FOCUS_17M_PIXEL_REPORT_V7_2.csv
AI_FOCUS_17M_TARGETS_V7_2.csv
AI_FOCUS_17M_TARGETS_V7_2.geojson
```

The contract includes:

```text
X_native / Y_native
UTM_E / UTM_N
Lon / Lat
Google_Maps_Link
z_Gold / z_Silver / z_Tunnel / z_Thermal / z_Chemical / z_Doors / z_Zero / z_Mass / z_Pottery
محور_معدني / محور_فراغ / محور_بنيوي / درجة_مركبة
الهدف_المرجح / المحتوى_المرجح / نظام_الدفن_او_الحقبة_المرجحة / تحذير_الفخاخ
ثقة_الشكل_% / ثقة_المحتوى_% / ثقة_الحقبة_% / الثقة_النهائية_%
تفسير_الذكاء
```

## Same-export validation

Final same-export app-vs-notebook comparison:

```text
PIXEL CSV
columns_match: True
notebook_row_count: 9
app_row_count: 9
row_count_match: True
columns_only_in_notebook: NONE
columns_only_in_app: NONE
shared_value_mismatch_count: 0
shared_value_mismatch_fields: NONE
max_numeric_delta: 0

TARGETS CSV
columns_match: True
notebook_row_count: 5
app_row_count: 5
row_count_match: True
columns_only_in_notebook: NONE
columns_only_in_app: NONE
shared_value_mismatch_count: 0
shared_value_mismatch_fields: NONE
max_numeric_delta: 0

GEOJSON
top_type_match: True
feature_count_match: True
geometry_types_match: True
property_keys_match: True
property_keys_only_in_notebook: NONE
property_keys_only_in_app: NONE
coordinate_mismatch_count: 0
property_mismatch_count: 0
property_mismatch_keys: NONE

full_pass: True
```

Private summary:

```text
C:\Dev\New_GEE_PRIVATE\FROZEN_NOTEBOOK_REFS\plan_b_23_focus_17m\comparison_reports\plan_b23_same_export_after_patch_summary.json
```

Private app snapshot:

```text
C:\Dev\New_GEE_PRIVATE\FROZEN_NOTEBOOK_REFS\plan_b_23_focus_17m\same_export_app_logic_snapshot_after_patch
```

## Local tests

Focused validation passed:

```text
python -m py_compile .\app\pipeline\stages\focus_mask.py
python -m pytest tests/unit/test_focus_mask.py tests/unit/test_forbidden_terms.py tests/unit/test_full_job_artifact_inventory.py -q
4 passed
```

## Decision

```text
#23 is Full.
The app now implements the notebook-compatible AI_FOCUS_17M cell 123 output contract for the frozen same-export reference.
```

## Privacy

No raw coordinates, KMZ contents, or private arrays are committed in this document.
Private comparison artifacts remain under C:\Dev\New_GEE_PRIVATE.
