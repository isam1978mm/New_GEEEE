# Current Status

This document is the quick reconciliation point for the current repo state.

Use it before choosing the next task. It does not replace the detailed phase docs; it explains which tracks are active, complete, parked, or blocked.

For the detailed remaining checklist, see:

```text
docs/REMAINING_WORK_CHECKLIST.md
```

For the Plan C UI closeout note, see:

```text
docs/PLAN_C_UI_CLOSEOUT.md
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
Plan C UI safety/clarity pass: complete
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

### Plan C UI safety/clarity pass

Current result:

```text
status: complete
scope: frontend UI text, static UI tests, docs closeout
backend_changed: false
api_changed: false
parity_changed: false
artifact_contract_changed: false
```

Completed slices:

```text
C-UI-1 settings and operator private overlay safety clarity
C-UI-2 run workflow empty/error-state clarity
C-UI-3 guarded exports empty-state clarity
C-UI-4 run archive empty/filter-state clarity
C-UI-5 key downloads empty/footer guidance
C-UI-6 status history and diagnostics empty-state clarity
C-UI-7 final docs closeout
```

Boundary:

```text
No browser exposure of exact coordinates, private geometry, KMZ contents, raw payloads, filesystem paths, service-account material, private hashes, row-level classifier output, or private source references.
No claim that the browser creates operator identity, role headers, run authorization, backend preview access, or private-output authorization.
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
D1D object-table real app-vs-reference parity passed
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
docs/D1D_OBJECT_TABLE_VERIFIER_RESULT.md
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
