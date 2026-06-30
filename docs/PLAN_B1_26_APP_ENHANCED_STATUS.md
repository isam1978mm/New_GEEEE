# Plan B1 #26 — App-enhanced local detected-feature GeoJSON status

Status: App-enhanced local contract; blocked for Full exact-file parity.

## Output

```text
full_job/focus/AI_FOCUS_17M_DETECTED_FEATURES_WGS84_V7_2.geojson
```

## Decision

The app should keep the richer local/private detected-feature GeoJSON contract because it is better for local operation than forcing exact notebook parity.

This output combines:

```text
- app pipeline metadata
- WGS84 geometry for local/private operator use
- classifier and core-ring-scene context
- notebook cell 123 semantic target fields when available
```

## Why not Full parity

```text
Exact notebook export searched:
AI_FOCUS_17M_DETECTED_FEATURES_WGS84_V7_2.geojson

Result:
not found in the downloaded notebook export.

Notebook writer-cell inspection:
no inspected notebook cell writes that exact filename.
Notebook cell 123 writes AI_FOCUS_17M_TARGETS_V7_2.geojson instead.
```

So this item must not be marked `Full same-export parity` unless a real notebook export for the exact file appears later or the project explicitly accepts a different reference contract.

## App-enhanced fields

The #26 local output keeps app fields such as:

```text
Classification
Confidence
Decision_Grade
Final_Confidence
Hard_Content_Type
Hard_Metal_Type
Hard_Primary_Class
Hard_Void_Type
ROI_Composite_Score
Scenario
Source_Cell
Source_Notebook_Family
Target_ID
row / col
UTM_E / UTM_N
Lat / Lon
Google_Maps_Link
```

It also adds notebook semantic fields from the cell 123 target contract when available:

```text
الهدف_المرجح
المحتوى_المرجح
نظام_الدفن_او_الحقبة_المرجحة
تحذير_الفخاخ
ثقة_الشكل_%
ثقة_المحتوى_%
ثقة_الحقبة_%
الثقة_النهائية_%
تفسير_الذكاء
```

## Privacy / production note

```text
Local/private mode:
coordinates and Google Maps links may exist for operator use.

Production/public mode:
production redaction is required before exposing this artifact through any public API/UI.
```

## Validation

```text
Focused tests passed after the app-enhanced patch:
- tests/unit/test_focus_mask.py
- tests/unit/test_forbidden_terms.py
- tests/unit/test_full_job_artifact_inventory.py
```
