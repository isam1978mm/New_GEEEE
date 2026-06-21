# Current Status

This document is the quick reconciliation point for the current repo state.

Use it before choosing the next task. It does not replace the detailed phase docs; it explains which tracks are active, complete, parked, or blocked.

For the detailed remaining checklist, see:

```text
docs/REMAINING_WORK_CHECKLIST.md
```

## Green baseline

```text
full pytest: passing
git status expected: clean
private artifacts: outside Git
```

## Implemented app features

```text
Paid Imagery Request Package: implemented
H4 private offline inference: complete
H5 operator-only aggregate summary: implemented
H5 score-band aggregate review: complete outside Git
```

### Paid Imagery Request Package

The visible/user-facing feature name is:

```text
Paid Imagery Request Package
```

Internal `v6` route, path, filename, and test labels may remain for compatibility.

Current implemented behavior:

```text
Generate request package
Review package metadata
Retrieve package ZIP
Metadata-only UI panel
Operator token forwarding
Backend denial/unavailable handling
Browser E2E smoke test
```

Boundary:

```text
No package rows displayed in browser
No spatial payload bodies displayed in browser
Coordinate-bearing package outputs remain private/filesystem-only
```

### H4 private offline inference

Current result:

```text
status: h4_private_offline_inference_completed
score_rows_written: 868
prediction_files_written: true
api_frontend_changed: false
overlays_created: false
```

Private files remain outside Git under the private operator artifact root.

### H5 operator-only aggregate summary

Current implemented behavior:

```text
backend aggregate summary service
operator-only aggregate route
backend redaction tests
frontend aggregate summary panel
frontend no-row-leak tests
H5 score-band aggregate review script
H5 score-band write outside Git
H5 score-band write result doc
full CI/build passing
```

Allowed H5 output level:

```text
aggregate row count
score min / max / mean
score-band counts
rows by source
rows by split
status flags
```

Still blocked:

```text
sample_id
row-level scores
private paths
private source refs
feature values
model files
raw CSV downloads
map overlays
public serving
```

## Parity track status

The in-scope notebook is:

```text
notebooks/new.ipynb
```

The operational parity checklist currently records these as closed:

```text
D1/D1C frozen reference created outside Git
D2 frozen bundle validator implemented
D1A bundle-wide scope audit implemented
D1B source-locked baseline created
D1D object-table outputs documented as source-recovery
D3 DEM curvature parity accepted end-to-end
R1 REPORT_640 real app-vs-reference parity passed
AIREADY-S1 secret-layer real app-vs-reference parity passed
HYPER-1A RES_2p5M real app-vs-reference parity passed
HYPER-1B core tensor/NPY real app-vs-reference parity passed
INT-1 internal AI_BEH raster real app-vs-reference parity passed
S1-1 core-band real app-vs-reference parity plan written
```

R1 safe result:

```text
status: passed
pass_count: 3
fail_count: 0
missing_count: 0
comparison_unavailable_count: 0
```

R1 result doc:

```text
docs/R1_REPORT_640_VERIFIER_RESULT.md
```

AIREADY-S1 safe result:

```text
overall_status: passed
expected_count: 6
compared_count: 6
counts_by_status:
  passed: 6
```

AIREADY-S1 result doc:

```text
docs/AIREADY_S1_SECRET_LAYERS_VERIFIER_RESULT.md
```

HYPER-1A safe result:

```text
overall_status: passed
expected_count: 2
compared_count: 2
counts_by_status:
  passed: 2
```

HYPER-1A result doc:

```text
docs/HYPER_1A_RES_2P5M_VERIFIER_RESULT.md
```

HYPER-1B safe result:

```text
overall_status: passed
expected_count: 2
compared_count: 2
counts_by_status:
  passed: 2
run_contract:
  status: comparable
```

HYPER-1B result doc:

```text
docs/HYPER_1B_CORE_TENSOR_NPY_VERIFIER_RESULT.md
```

INT-1 safe result:

```text
overall_status: passed
expected_count: 13
compared_count: 13
counts_by_status:
  passed: 13
family_count: 6
```

INT-1 result doc:

```text
docs/INT_1_INTERNAL_RASTER_VERIFIER_RESULT.md
```

INT-1 safety boundary:

```text
standard D2-gated verifier used
no verifier tolerance relaxation
no reference rasters copied as app outputs
no private raster/NPY payloads committed
no public downloads, HTTP raster serving, or map overlays enabled
```

S1-1 plan doc:

```text
docs/S1_1_CORE_BAND_REAL_APP_PARITY_PLAN.md
```

S1-1 current gate:

```text
S1-1 Gate 1: locate D2-valid S1-1 reference files
```

If the private D1/D1C files are missing locally, stop and reconcile the docs before proceeding.

## Active real app-vs-reference parity

```text
S1-1 core-band real app-vs-reference parity
status: plan ready; reference-location gate next
```

S1-1 covers the eight notebook Sentinel-1 ASC/DESC filtered core-band files:

```text
GEOTIFF_RADAR_BANDS/S1_ASC_VV_Filtered_640.tif
GEOTIFF_RADAR_BANDS/S1_ASC_VH_Filtered_640.tif
GEOTIFF_RADAR_BANDS/S1_DESC_VV_Filtered_640.tif
GEOTIFF_RADAR_BANDS/S1_DESC_VH_Filtered_640.tif
NPY_RADAR_BANDS/S1_ASC_VV_Filtered_640.npy
NPY_RADAR_BANDS/S1_ASC_VH_Filtered_640.npy
NPY_RADAR_BANDS/S1_DESC_VV_Filtered_640.npy
NPY_RADAR_BANDS/S1_DESC_VH_Filtered_640.npy
```

Do not treat final app RTC outputs or RADAR_* app aliases as equivalent to S1-1.

## Source-recovery items

These need explicit recovery/build work before verification:

```text
D1D object-table outputs
AI_READY remaining support families
SAR/S1 support, intermediate, stack, and QA/provenance outputs outside S1-1
PAN/optical image components and stack
```

Do not fabricate outputs. Do not treat renamed app-native equivalents as notebook parity.

## Parked / future tracks

### External V6 notebook/source-lock track

Status:

```text
parked separate external notebook/package track
```

This is different from the implemented Paid Imagery Request Package app feature.

The external V6 track can restart only if the operator supplies:

```text
real external V6 notebook/export source
or
real frozen V6 package proving the workflow
```

### Real auth provider integration

Status:

```text
later / deployment work
```

The app has operator-token/header paths. A real provider integration is not the next local task unless deployment becomes the priority.

### Public overlays / coordinate-bearing downloads

Status:

```text
future only / blocked for public or shared mode
```

Private operator filesystem-only artifacts are allowed by gate. Public/shared coordinate exposure remains blocked.

## Recommended next choices

Choose one, not all at once:

```text
A. S1-1 Gate 1 reference-location check
   Confirm whether the D1C/D2 bundle contains the eight required S1-1 reference files.

B. Real auth provider integration plan
   Only if VPS/deployment becomes the priority.

C. Source-recovery planning
   Only after deciding to defer S1 verifier path work.
```

## Current recommendation

```text
Next: S1-1 Gate 1: locate D2-valid S1-1 reference files
```
