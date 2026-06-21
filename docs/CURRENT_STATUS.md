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
AI_READY remaining support families blocked/source-capture status recorded
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

S1-1 safe result:

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

S1-1 result doc:

```text
docs/S1_1_CORE_BAND_VERIFIER_RESULT.md
```

S1 filtered stack safe result:

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

S1 filtered stack result doc:

```text
docs/S1_FILTERED_STACK_VERIFIER_RESULT.md
```

PAN/optical safe result:

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

PAN/optical result doc:

```text
docs/PAN_OPTICAL_VERIFIER_RESULT.md
```

PAN canonical-reference note:

```text
The D1C bundle contains duplicate PAN component filenames.
The canonical component references are the OPT/PAN_TIFS_640 and OPT/PAN_NPY_640 copies.
The legacy/misplaced GEOTIFF_RADAR_BANDS and NPY_RADAR_BANDS copies are not used for PAN parity.
PAN_LAYERS_STACK_640.npy bands match the OPT/PAN_NPY_640 components.
```

AI_READY remaining support-family status:

```text
status: blocked / source-capture required
exact D1C reference search: 0 of 7 found
reference manifest mentions: 0 of 7 found
exact app output search: 0 of 7 found
broad naming-drift search: no useful alternate Fraction/MH/AN notebook-named outputs found
```

AI_READY remaining support-family status doc:

```text
docs/AI_READY_REMAINING_SUPPORT_STATUS.md
```

AI_READY remaining support-family boundary:

```text
Do not claim all AIREADY parity complete from AIREADY-S1 alone.
Do not alias ai_ready_support_stack.* as the missing Fraction/MH/AN outputs.
Do not alias focus_zone_ai_ready_window.npy as any missing Fraction/MH/AN output.
Do not use AI_BEH_* rasters as AI_READY remaining support-family equivalents.
No fabricated, synthesized, or renamed outputs were used.
```

Safety boundary:

```text
current PAN component and PAN stack verifiers used
no verifier tolerance relaxation
no legacy/misplaced RADAR_BANDS PAN copies treated as canonical
no final RTC or SAR/RADAR aliases treated as PAN equivalents
no private raster/NPY payloads committed
no public downloads, HTTP raster/array serving, or map overlays enabled
```

If the private D1/D1C files are missing locally, stop and reconcile the docs before proceeding.

## Active real app-vs-reference parity

```text
No active verifier gate selected yet after AI_READY remaining support-family status recording.
```

## Source-recovery items

These need explicit recovery/build work before verification:

```text
D1D object-table outputs
SAR/S1 support, intermediate, and QA/provenance outputs outside S1-1 and the filtered stack
AI_READY remaining support families, only if new source captures / exact outputs are supplied later
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
