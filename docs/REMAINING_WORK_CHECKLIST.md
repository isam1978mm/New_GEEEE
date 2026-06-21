# Remaining Work Checklist

This document is the working checklist for choosing the next task after the H5 score-band aggregate review, R1 REPORT_640 verifier pass, AIREADY-S1 verifier pass, HYPER-1A verifier pass, HYPER-1B verifier pass, INT-1 verifier pass, S1-1 verifier pass, S1 filtered stack verifier pass, PAN/optical verifier pass, AI_READY support stack verifier pass, and D1D object-table verifier pass.

It separates completed work, next parity work, source-recovery work, safety boundaries, and later/deployment-only work.

## 0. Current baseline

```text
[x] Git expected clean
[x] Full pytest green
[x] Frontend build green
[x] Paid Imagery Request Package app flow implemented
[x] H4 private offline inference complete
[x] H5 operator-only aggregate summary implemented
[x] H5 score-band aggregate review written outside Git
[x] H5 score-band result doc recorded
[x] R1 REPORT_640 verifier passed
[x] R1 REPORT_640 result doc recorded
[x] AIREADY-S1 secret-layer verifier passed
[x] AIREADY-S1 result recorded
[x] HYPER-1A RES_2p5M verifier passed
[x] HYPER-1A result recorded
[x] HYPER-1B core tensor/NPY verifier passed
[x] HYPER-1B result recorded
[x] INT-1 internal AI_BEH raster verifier passed
[x] INT-1 result recorded
[x] S1-1 core-band verifier passed
[x] S1-1 result recorded
[x] S1 filtered stack verifier passed
[x] S1 filtered stack result recorded
[x] PAN/optical component verifier passed
[x] PAN/optical stack verifier passed
[x] PAN/optical result recorded
[x] AI_READY support stack reference found
[x] AI_READY support stack app candidate selected
[x] AI_READY support stack value parity passed
[x] AI_READY support stack status doc corrected
[x] D1D object-table reference found in D1 root
[x] D1D object-table app candidate selected
[x] D1D object-table hash/schema/row-count parity passed
[x] D1D object-table result recorded
```

## 1. Completed real app-vs-reference parity gates

### R1 REPORT_640

```text
[x] R1 plan written
[x] R1 runnable evidence collected
[x] R1 verifier passed
[x] R1 result recorded
```

Closeout result:

```text
status: passed
pass_count: 3
fail_count: 0
missing_count: 0
comparison_unavailable_count: 0
```

### AIREADY-S1 secret layers

```text
[x] AIREADY-S1 secret-layer reference files confirmed
[x] AIREADY-S1 app files confirmed
[x] AIREADY-S1 matching app candidate selected
[x] AIREADY-S1 secret-layer verifier passed
[x] AIREADY-S1 result recorded
```

Closeout result:

```text
overall_status: passed
expected_count: 6
compared_count: 6
counts_by_status:
  passed: 6
```

Do not claim all AIREADY parity from AIREADY-S1 alone.

### HYPER-1A RES_2p5M

```text
[x] HYPER-1A plan written
[x] reference RES_2p5M TIF/NPY found
[x] matching app candidate selected
[x] source hypercube values matched reference source exactly
[x] generator added and tested
[x] D2-gated HYPER-1A verifier passed
[x] HYPER-1A result recorded
```

Closeout result:

```text
overall_status: passed
expected_count: 2
compared_count: 2
counts_by_status:
  passed: 2
```

### HYPER-1B core tensor/NPY

```text
[x] HYPER-1B plan written
[x] reference FINAL_TESLA_V7_2_HYPERCUBE.npy found
[x] reference RADAR_STACK_HWC_640_*.npy found
[x] matching app candidate selected
[x] run-contract transform policy patched and tested
[x] D2-gated HYPER-1B verifier passed
[x] HYPER-1B result recorded
```

Closeout result:

```text
overall_status: passed
expected_count: 2
compared_count: 2
counts_by_status:
  passed: 2
```

### INT-1 internal AI_BEH rasters

```text
[x] INT-1 plan written
[x] D1C reference rasters confirmed for 13 AI_BEH outputs
[x] D1C-grid notebook rerun reproduced D1C for all 13 outputs
[x] D1C-grid source inputs exported privately
[x] canonical app writer patched to match notebook source/formula contract
[x] 13 canonical app rasters generated
[x] standard D2-gated verifier passed
[x] INT-1 result recorded
```

Closeout result:

```text
overall_status: passed
expected_count: 13
compared_count: 13
counts_by_status:
  passed: 13
family_count: 6
```

### S1-1 core-band Sentinel-1 ASC/DESC filtered outputs

```text
[x] S1-1 plan written
[x] four S1-1 GeoTIFF references exist
[x] four S1-1 NPY references exist
[x] matching app output root found
[x] all eight app files exist
[x] final RTC/app aliases rejected as non-equivalent
[x] SAR ASC/DESC verifier passed
[x] S1-1 result recorded
```

Closeout result:

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

### S1 filtered stack tensor

```text
[x] S1_FILTERED_LAYERS_STACK_640.npy app output found
[x] S1_FILTERED_LAYERS_STACK_640.npy reference output found
[x] current S1 filtered stack verifier passed
[x] S1 filtered stack result recorded
```

Closeout result:

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
```

### PAN/optical component and stack outputs

```text
[x] duplicate PAN component paths identified
[x] canonical component reference selected: OPT/PAN_TIFS_640 and OPT/PAN_NPY_640
[x] app-produced canonical PAN component files found
[x] PAN component verifier passed
[x] PAN stack verifier passed
[x] PAN/optical result recorded
```

Component closeout result:

```text
overall_status: passed
expected_count: 4
compared_count: 4
counts_by_status:
  passed: 4
```

Stack closeout result:

```text
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

### AI_READY support stack tensor

```text
[x] App AI_READY support stack found
[x] 19-band list confirmed
[x] Private notebook frozen reference found under data/private_references
[x] Matching app run selected: a11309bf-ed47-4bf5-bbf4-f755b904065c
[x] Nonmatching app run rejected: e11d3280-a7b7-4c7c-a761-8b08ac9452f2
[x] AI_READY support stack parity passed
[x] Earlier blocked wording corrected
```

Closeout result:

```text
artifact: ai_ready_support_stack.npy
matching_app_run: a11309bf-ed47-4bf5-bbf4-f755b904065c
shape: [640, 640, 19]
dtype: float32
hash_match: true
same_values_exact: true
compared_count: 7782400
nan_count_ref: 0
nan_count_app: 0
max_abs_diff: 0.0
mean_abs_diff: 0.0
```

Standalone Fraction/MH/AN note:

```text
The exact standalone planned filenames were searched.
They are not the active AI_READY support-stack parity target.
They are not channels in the 19-band support-stack band list.
No standalone Fraction/MH/AN verifier pass is claimed.
```

### D1D object-table outputs

```text
[x] D1C bundle exact search done: object tables not found there
[x] wider D1 reference root searched
[x] reference object tables found: D1_NEW_IPYNB_REFERENCE_2026_06_10
[x] app outputs found in two runs
[x] matching app run selected by hash: e11d3280-a7b7-4c7c-a761-8b08ac9452f2
[x] schema-only / row-count / hash check completed
[x] D1D object-table parity passed
[x] D1D result recorded
```

Closeout result:

```text
overall_status: passed
reference_root_name: D1_NEW_IPYNB_REFERENCE_2026_06_10
matching_app_run: e11d3280-a7b7-4c7c-a761-8b08ac9452f2
expected_count: 2
passed_count: 2
```

Outputs:

```text
objects_index.csv:
  hash_match: true
  schema_match: true
  row_count_match: true
  row_count: 816
  column_count: 11

clusters_summary.csv:
  hash_match: true
  schema_match: true
  row_count_match: true
  row_count: 454
  column_count: 5
```

Result doc:

```text
docs/D1D_OBJECT_TABLE_VERIFIER_RESULT.md
```

D1D boundary:

```text
[x] no CSV rows committed
[x] no object patches committed
[x] no object_mask.npy payload committed
[x] no coordinate-bearing row values committed
[x] no public object-table downloads enabled
[x] no HTTP table/array serving enabled
[x] no map overlays enabled
```

## 2. Remaining source-recovery / parity candidates

No next gate is selected yet. Choose one explicitly.

```text
[ ] SAR/S1 support, intermediate, and QA/provenance outputs outside S1-1 and stack
    Do not broaden S1-1 or S1 filtered stack passes into all SAR/S1 parity.

[ ] Standalone AI_READY Fraction/MH/AN files
    Only if the operator supplies real notebook/source evidence later.
```

## 3. H5 / prediction serving boundaries still blocked

H5 is complete at aggregate level. These remain blocked:

```text
[ ] row-level prediction UI
[ ] raw prediction CSV download
[ ] sample_id exposure
[ ] private file paths in API/frontend responses
[ ] feature values in API/frontend responses
[ ] model artifact serving
[ ] feature matrix serving
[ ] map overlays
[ ] public serving
```

Allowed H5 level remains aggregate/redacted only.

## 4. Paid Imagery Request Package / old V6 status

No main work now.

```text
[x] Visible name corrected to Paid Imagery Request Package
[x] App UI/backend flow implemented
[x] Generate / review metadata / retrieve ZIP exists
[x] Metadata-only browser behavior
[ ] Optional later: operator enablement runbook
[ ] Optional later: full regression checklist
```

The external old V6 notebook/source-lock track remains parked:

```text
[ ] Later: provide real external V6 notebook/export source
[ ] Later: freeze V6 package
[ ] Later: source-lock V6 formulas
[ ] Later: decide whether app integrates more V6 workflow
```

Do not reopen this now.

## 5. Deployment/auth/public exposure — later only

```text
[ ] Real auth provider integration
    status: later / VPS or deployment work

[ ] Public location overlay exposure review
    status: future only

[ ] Public coordinate-bearing downloads
    status: blocked for public/shared mode
```

## Correct next order

```text
1. Choose the next source-recovery or parity family explicitly.

2. For the selected family:
   [ ] write/confirm plan
   [ ] locate private reference files
   [ ] locate/generate private app output files
   [ ] confirm required file set
   [ ] run grid/source contract check
   [ ] run D2-gated verifier or safe metadata/hash verifier as appropriate
   [ ] record safe docs-only result

3. Later:
   [ ] real auth provider
   [ ] public exposure review
   [ ] old external V6 source-lock track
```

## Next actionable item

```text
Choose next family: SAR/S1 remaining support/QA.
```
