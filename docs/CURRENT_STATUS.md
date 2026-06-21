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
H5 score-band result doc
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

The operational parity checklist currently records these as closed or explicitly statused:

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
S1-1 core-band real app-vs-reference parity passed
S1 filtered stack tensor real app-vs-reference parity passed
PAN/optical component and stack real app-vs-reference parity passed
AI_READY support stack tensor real app-vs-reference parity passed
Standalone AI_READY Fraction/MH/AN filenames searched and not treated as the support-stack target
```

### Closed verifier/result docs

```text
docs/R1_REPORT_640_VERIFIER_RESULT.md
docs/AIREADY_S1_SECRET_LAYERS_VERIFIER_RESULT.md
docs/HYPER_1A_RES_2P5M_VERIFIER_RESULT.md
docs/HYPER_1B_CORE_TENSOR_NPY_VERIFIER_RESULT.md
docs/INT_1_INTERNAL_RASTER_VERIFIER_RESULT.md
docs/S1_1_CORE_BAND_VERIFIER_RESULT.md
docs/S1_FILTERED_STACK_VERIFIER_RESULT.md
docs/PAN_OPTICAL_VERIFIER_RESULT.md
docs/AI_READY_REMAINING_SUPPORT_STATUS.md
```

### R1 REPORT_640 safe result

```text
status: passed
pass_count: 3
fail_count: 0
missing_count: 0
comparison_unavailable_count: 0
```

### AIREADY-S1 secret-layer safe result

```text
overall_status: passed
expected_count: 6
compared_count: 6
counts_by_status:
  passed: 6
```

### HYPER-1A safe result

```text
overall_status: passed
expected_count: 2
compared_count: 2
counts_by_status:
  passed: 2
```

### HYPER-1B safe result

```text
overall_status: passed
expected_count: 2
compared_count: 2
counts_by_status:
  passed: 2
run_contract:
  status: comparable
```

### INT-1 safe result

```text
overall_status: passed
expected_count: 13
compared_count: 13
counts_by_status:
  passed: 13
family_count: 6
```

### S1-1 safe result

```text
overall_status: passed
expected_count: 8
compared_count: 8
counts_by_status:
  passed: 8
raster_value_comparison_available: true
npy_outputs_passed: true
max_abs_diff: 0.0 for all outputs
mean_abs_diff: 0.0 for all outputs
```

### S1 filtered stack safe result

```text
overall_status: passed
status: passed
output_name: S1_FILTERED_LAYERS_STACK_640.npy
shape_match: true
dtype_match: true
hash_match: true
count_compared_values: 1638400
count_nan_or_nodata_values: 0
max_abs_diff: 0.0
mean_abs_diff: 0.0
runtime_output_verified: true
notebook_value_parity_verified: true
```

### PAN/optical safe result

```text
components:
  overall_status: passed
  expected_count: 4
  compared_count: 4
  counts_by_status:
    passed: 4
  raster_value_comparison_available: true
  npy_outputs_passed: true

stack:
  overall_status: passed
  status: passed
  output_name: PAN_LAYERS_STACK_640.npy
  shape_match: true
  dtype_match: true
  hash_match: false
  count_compared_values: 819200
  count_nan_or_nodata_values: 0
  max_abs_diff: 5.960464477539063e-08
  mean_abs_diff: 9.302630132879131e-10
```

PAN canonical-reference note:

```text
The D1C bundle contains duplicate PAN component filenames.
The canonical component references are the OPT/PAN_TIFS_640 and OPT/PAN_NPY_640 copies.
The legacy/misplaced GEOTIFF_RADAR_BANDS and NPY_RADAR_BANDS copies are not used for PAN parity.
PAN_LAYERS_STACK_640.npy bands match the OPT/PAN_NPY_640 components.
```

### AI_READY support stack safe result

The earlier blocked wording for this family has been corrected. The real support-stack target is:

```text
ai_ready_support_stack.npy
```

Safe parity result:

```text
reference_exists: true
app_exists: true
matching_app_run: a11309bf-ed47-4bf5-bbf4-f755b904065c
reference_shape: [640, 640, 19]
app_shape: [640, 640, 19]
reference_dtype: float32
app_dtype: float32
hash_match: true
same_shape: true
same_dtype: true
same_values_exact: true
compared_count: 7782400
nan_count_ref: 0
nan_count_app: 0
max_abs_diff: 0.0
mean_abs_diff: 0.0
```

AI_READY support stack band list:

```text
VV_dB
VH_dB
logRatio_dB
incidence
NDVI
NDWI
NDMI
NBR
IRONOX
IRON_SWIR
BSI
slope
aspect
curvature
TPI
TRI
roughness
TWI
lst
```

Nonmatching app candidate rejected:

```text
e11d3280-a7b7-4c7c-a761-8b08ac9452f2
hash_match: false
max_abs_diff: 1.0
mean_abs_diff: 0.29361279566396
```

Standalone AI_READY Fraction/MH/AN note:

```text
The exact standalone planned filenames were searched but are not the support-stack parity target.
They are not channels in the 19-band ai_ready_support_stack.npy.
No standalone Fraction/MH/AN verifier pass is claimed.
```

## Safety boundary

```text
no verifier tolerance relaxation
no nonmatching app run treated as passing
no standalone AI_READY Fraction/MH/AN filenames aliased to ai_ready_support_stack.npy
no focus_zone_ai_ready_window.npy aliasing as a standalone Fraction/MH/AN output
no AI_BEH_* rasters treated as AI_READY remaining support-family equivalents
no legacy/misplaced RADAR_BANDS PAN copies treated as canonical
no final RTC or SAR/RADAR aliases treated as PAN equivalents
no private raster/NPY payloads committed
no public downloads, HTTP raster/array serving, or map overlays enabled
```

If the private D1/D1C files are missing locally, stop and reconcile the docs before proceeding.

## Active real app-vs-reference parity

```text
No active verifier gate selected yet after AI_READY support stack parity correction.
```

## Source-recovery items

These need explicit recovery/build work before verification:

```text
D1D object-table outputs
SAR/S1 support, intermediate, and QA/provenance outputs outside S1-1 and the filtered stack
Standalone AI_READY Fraction/MH/AN files only if the operator supplies real notebook/source evidence later
```

Do not fabricate outputs. Do not treat renamed app-native equivalents as notebook parity.

## Parked / future tracks

### External V6 notebook/source-lock track

```text
parked separate external notebook/package track
```

The external V6 track can restart only if the operator supplies:

```text
real external V6 notebook/export source
or
real frozen V6 package proving the workflow
```

### Real auth provider integration

```text
later / deployment work
```

### Public overlays / coordinate-bearing downloads

```text
future only / blocked for public or shared mode
```

## Recommended next choices

Choose one, not all at once:

```text
A. D1D object-table outputs
   Recover object-table outputs and compare only after same-run source evidence is available.

B. SAR/S1 remaining support, intermediate, and QA/provenance outputs
   Continue SAR/S1 work outside S1-1 and the filtered stack.

C. Real auth provider integration plan
   Only if VPS/deployment becomes the priority.
```

## Current recommendation

```text
Next: choose D1D object-table outputs or SAR/S1 remaining support/QA explicitly.
```
