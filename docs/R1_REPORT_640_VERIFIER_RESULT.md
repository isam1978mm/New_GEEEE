# R1 REPORT_640 verifier result

Status: passed.

This document records safe verifier status only.

No raster payloads are included.

No exact coordinate-bearing private paths are included.

No public downloads were enabled.

No API or frontend code was changed.

No private artifacts were committed.

## Verifier

```text
script: scripts/d1_compare_report_value_parity.py
schema_version: d1_report_value_parity_v1
created_at: 2026-06-19T13:46:28.298052+00:00
status: passed
ok: true
```

## Inputs

Reference side:

```text
private frozen D1C REPORT_640 reference bundle
three required REPORT_640 reference TIFs present
```

App side:

```text
app run id: a11309bf-ed47-4bf5-bbf4-f755b904065c
three required REPORT_640 app TIFs present
```

Rejected app candidate:

```text
e11d3280-a7b7-4c7c-a761-8b08ac9452f2
reason: different transform/origin from the selected reference bundle
```

Private verifier report:

```text
written outside Git under the private R1_REPORT_640 review area
```

## Required outputs

```text
REPORT_640_Pottery_Report.tif
REPORT_640_Mass_Report.tif
REPORT_640_FINAL_Zero_Point_Targets.tif
```

## Result summary

```text
pass_count: 3
fail_count: 0
missing_count: 0
comparison_unavailable_count: 0
```

## Tolerance policy

```text
atol: 1e-06
rtol: 1e-06
transform_atol: 1e-05
```

Benign metadata variance accepted by verifier policy:

```text
nodata: None vs -9999.0 accepted
transform/origin maximum delta: 3.227032721042633e-06
```

The transform/origin delta is below the configured `transform_atol`.

## Output-level results

### REPORT_640_Pottery_Report.tif

```text
status: passed
metadata_match: true
values_compared: true
within_tolerance: true
count_compared_pixels: 409600
count_nan_or_nodata_pixels: 0
max_abs_diff: 0.0
mean_abs_diff: 0.0
width_match: true
height_match: true
band_count_match: true
dtype_match: true
crs_match: true
transform_match: true
nodata_match: false
nodata_accepted: true
transform_max_abs_delta: 3.227032721042633e-06
```

### REPORT_640_Mass_Report.tif

```text
status: passed
metadata_match: true
values_compared: true
within_tolerance: true
count_compared_pixels: 409600
count_nan_or_nodata_pixels: 0
max_abs_diff: 0.0
mean_abs_diff: 0.0
width_match: true
height_match: true
band_count_match: true
dtype_match: true
crs_match: true
transform_match: true
nodata_match: false
nodata_accepted: true
transform_max_abs_delta: 3.227032721042633e-06
```

### REPORT_640_FINAL_Zero_Point_Targets.tif

```text
status: passed
metadata_match: true
values_compared: true
within_tolerance: true
count_compared_pixels: 409600
count_nan_or_nodata_pixels: 0
max_abs_diff: 0.0
mean_abs_diff: 0.0
width_match: true
height_match: true
band_count_match: true
dtype_match: true
crs_match: true
transform_match: true
nodata_match: false
nodata_accepted: true
transform_max_abs_delta: 3.227032721042633e-06
```

## Safety boundary

Still blocked:

```text
public REPORT_640 downloads
HTTP serving of REPORT_640 rasters
map overlays
raw private raster payloads in Git
coordinate-bearing public exposure
claiming broader notebook parity from this R1 result alone
```

Allowed and completed:

```text
private local verifier report
safe docs-only pass/fail result
safe aggregate counts and status fields
```

## R1 checklist closeout

```text
[x] reference root found
[x] 3 reference TIFs confirmed
[x] app output root selected
[x] 3 app TIFs confirmed
[x] e11 app candidate rejected as different grid/location
[x] metadata policy patched
[x] verifier tests passed
[x] D2-gated REPORT_640 value verifier passed
[x] R1 verifier result recorded
```

## Decision

```text
r1_report_640_real_app_vs_reference_parity_passed
```

## Next recommended task

```text
AIREADY real app-vs-reference parity plan
```
