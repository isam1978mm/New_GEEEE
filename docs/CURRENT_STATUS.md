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
S1-1 core-band real app-vs-reference parity passed
S1 filtered stack tensor real app-vs-reference parity passed
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

S1-1 plan doc:

```text
docs/S1_1_CORE_BAND_REAL_APP_PARITY_PLAN.md
```

S1/SAR safety boundary:

```text
current SAR ASC/DESC and S1 filtered stack verifiers used
no verifier tolerance relaxation
no final RTC outputs treated as S1-1 or stack equivalents
no RADAR_* app aliases treated as S1-1 or stack equivalents
no radar_db_support_stack/radar_linear_support_stack aliasing as the filtered stack
no private raster/NPY payloads committed
no public downloads, HTTP raster/array serving, or map overlays enabled
```

If the private D1/D1C files are missing locally, stop and reconcile the docs before proceeding.

## Active real app-vs-reference parity

```text
No active verifier gate selected yet after S1 filtered stack.
```

## Source-recovery items

These need explicit recovery/build work before verification:

```text
D1D object-table outputs
AI_READY remaining support families
SAR/S1 support, intermediate, and QA/provenance outputs outside S1-1 and the filtered stack
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
A. PAN/optical component and stack parity
   Continue source-driven notebook parity work for optical/PAN artifacts.

B. AI_READY remaining support families
   AIREADY-FR, AIREADY-MH, and AIREADY-AN source/writer recovery.

C. D1D object-table outputs
   Recover object-table outputs and compare only after same-run source evidence is available.

D. SAR/S1 remaining support, intermediate, and QA/provenance outputs
   Continue SAR/S1 work outside S1-1 and the filtered stack.

E. Real auth provider integration plan
   Only if VPS/deployment becomes the priority.
```

## Current recommendation

```text
Next: choose the next parity/source-recovery family explicitly.
```
