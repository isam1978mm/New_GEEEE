# Phase 2 Item #20 — Fusion Center / Intelligence Tensors

Status: Partial / numeric parity blocked.

## Canonical notebook cell

```text id="h9z1a3"
cell 099:
  output bands:
    REPORT_640_FINAL_Zero_Point_Targets
    REPORT_640_Mass_Report
    REPORT_640_Pottery_Report

  formulas:
    Zero_Point     = final boolean intersection
    Mass_Report    = B12 * L9 ST_B10 / 1000
    Pottery_Report = B11 / B8A
```

## Export availability

Exact notebook stack refs were missing:

```text id="mqogyk"
REPORT_640_FINAL_INTELLIGENCE_STACK_640.npy
REPORT_640_FINAL_INTELLIGENCE_STACK_640.tif
```

Exact per-band notebook TIF refs were available and frozen privately:

```text id="a42h65"
REPORT_640_FINAL_Zero_Point_Targets.tif
REPORT_640_Mass_Report.tif
REPORT_640_Pottery_Report.tif
```

## App stack validation

```text id="nwit0f"
REPORT_640_FINAL_INTELLIGENCE_STACK_640.npy:
  exists
  shape: 640x640x3
  dtype: float32
  per-band NPY outputs: present
  per-band TIF outputs: present
  stack-vs-band max delta: 0.0
```

Validated band order:

```text id="piptov"
0. REPORT_640_FINAL_Zero_Point_Targets
1. REPORT_640_Mass_Report
2. REPORT_640_Pottery_Report
```

## Frozen notebook TIF comparison

```text id="cfprsd"
REPORT_640_FINAL_Zero_Point_Targets.tif:
  exact match: true
  max_abs_delta: 0.0

REPORT_640_Mass_Report.tif:
  exact match: false
  max_abs_delta observed: 143227.79296875 / 200614.40906223655

REPORT_640_Pottery_Report.tif:
  exact match: false
  max_abs_delta observed: 0.43912768363952637 / 0.39577358961105347
```

## Root cause

```text id="b6xfmi"
s2_indices.py EE builder matches canonical cell 099 formulas.

Current local run data does not provide notebook-equivalent cell 099 inputs:
  - local s2_raw_cube.npy has 7 bands and no B8A.
  - local s2_raw_cube.npy uses scaled reflectance-like values.
  - notebook cell 099 uses direct EE S2 bands including B8A and direct L9 ST_B10 values.
```

## Decision

```text id="w5kjgt"
Do not mark Full.
Do not patch formulas blindly.
Keep as Partial / numeric parity blocked until notebook-equivalent local B8A/S2/L9 inputs exist or an explicit app-goal exception is approved.
```
