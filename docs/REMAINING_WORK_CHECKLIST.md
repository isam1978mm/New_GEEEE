# Remaining Work Checklist

This document is the working checklist for choosing the next task after the H5 score-band aggregate review, R1 REPORT_640 verifier pass, AIREADY-S1 verifier pass, HYPER-1A verifier pass, HYPER-1B verifier pass, INT-1 verifier pass, S1-1 verifier pass, S1 filtered stack verifier pass, PAN/optical verifier pass, and AI_READY support stack verifier pass.

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

Required outputs passed:

```text
[x] REPORT_640_Pottery_Report.tif
[x] REPORT_640_Mass_Report.tif
[x] REPORT_640_FINAL_Zero_Point_Targets.tif
```

### AIREADY-S1 secret layers

```text
[x] AIREADY plan written
[x] AIREADY-S1 secret-layer reference files confirmed
[x] AIREADY-S1 app files confirmed
[x] AIREADY-S1 nested reference output directory support added
[x] AIREADY-S1 CLI tests passed
[x] AIREADY-S1 nonmatching app candidate rejected
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

Required outputs passed:

```text
[x] AI_READY_640_Secret_Gold_Halo.tif
[x] AI_READY_640_Secret_Silver_Oxide.tif
[x] AI_READY_640_Secret_Tunnel_Ceiling.tif
[x] AI_READY_640_Secret_Thermal_Inertia.tif
[x] AI_READY_640_Secret_Chemical_Protector.tif
[x] AI_READY_640_Secret_Hidden_Doors.tif
```

Do not claim all AIREADY parity from AIREADY-S1 alone.

### HYPER-1A RES_2p5M

```text
[x] HYPER-1A plan written
[x] D1C reference RES_2p5M TIF found
[x] D1C reference RES_2p5M NPY found
[x] app source hypercube found
[x] nonmatching app candidate rejected
[x] matching app candidate selected
[x] source hypercube values matched D1C source exactly
[x] generator added and tested
[x] app RES_2p5M TIF generated
[x] app RES_2p5M NPY generated
[x] verifier transform policy patched and tested
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
[x] D1C reference FINAL_TESLA_V7_2_HYPERCUBE.npy found
[x] D1C reference RADAR_STACK_HWC_640_*.npy found
[x] app FINAL_TESLA_V7_2_HYPERCUBE.npy found
[x] app RADAR_STACK_HWC_640_app.npy found
[x] nonmatching app candidate rejected
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
[x] cell-90 relation source active
[x] B8A source active
[x] StatueLogic raw source intermediate active
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
[x] locate D2-valid S1-1 reference files
[x] confirm four S1-1 GeoTIFF references exist
[x] confirm four S1-1 NPY references exist
[x] confirm reference manifest coverage
[x] inspect safe reference metadata
[x] locate app-produced S1-1 output root
[x] confirm all eight app files exist
[x] reject final RTC/app aliases as non-equivalent
[x] confirm source/export manifest exists
[x] confirm current SAR ASC/DESC verifier passed
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
[x] S1 filtered stack contract existed
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
runtime_output_verified: true
notebook_value_parity_verified: true
```

### PAN/optical component and stack outputs

```text
[x] PAN component reference filenames found
[x] duplicate PAN component paths identified
[x] duplicate PAN values compared
[x] canonical component reference selected: OPT/PAN_TIFS_640 and OPT/PAN_NPY_640
[x] PAN stack reference found
[x] stack bands matched canonical OPT/PAN_NPY_640 component arrays
[x] app-produced canonical PAN component files found
[x] app-produced PAN stack file found
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
raster_value_comparison_available: true
npy_outputs_passed: true
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
runtime_output_verified: true
notebook_value_parity_verified: true
```

Result doc:

```text
docs/PAN_OPTICAL_VERIFIER_RESULT.md
```

### AI_READY support stack tensor

```text
[x] Exact standalone Fraction/MH/AN names searched
[x] App AI_READY support stack found
[x] AI_READY support stack 19-band list confirmed
[x] Private notebook frozen reference found under data/private_references
[x] Matching app run selected: a11309bf-ed47-4bf5-bbf4-f755b904065c
[x] Nonmatching app run rejected: e11d3280-a7b7-4c7c-a761-8b08ac9452f2
[x] AI_READY support stack parity passed
[x] Earlier blocked wording corrected
```

Support-stack closeout result:

```text
artifact: ai_ready_support_stack.npy
reference_exists: true
app_exists: true
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

Band list:

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

Status doc:

```text
docs/AI_READY_REMAINING_SUPPORT_STATUS.md
```

AI_READY boundary:

```text
[x] no raster/NPY payloads committed
[x] no nonmatching app run treated as passing
[x] no standalone Fraction/MH/AN filenames aliased to ai_ready_support_stack.npy
[x] no focus_zone_ai_ready_window.npy aliasing as standalone Fraction/MH/AN output
[x] no AI_BEH_* rasters treated as AI_READY remaining support-family equivalents
[x] no fabricated, synthesized, or renamed outputs used
[x] no public AI_READY support-stack downloads enabled
[x] no HTTP raster/array serving enabled
[x] no map overlays enabled
```

Standalone Fraction/MH/AN note:

```text
The exact standalone planned filenames were searched.
They are not the active AI_READY support-stack parity target.
They are not channels in the 19-band support-stack band list.
No standalone Fraction/MH/AN verifier pass is claimed.
```

## 2. Remaining source-recovery / parity candidates

No next gate is selected yet. Choose one explicitly.

```text
[ ] D1D object-table outputs
    Recover/export same-run object table family and compare only after source evidence is available.

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
   [ ] locate private D1C reference files
   [ ] locate/generate private app output files
   [ ] confirm required file set
   [ ] run grid/source contract check
   [ ] run D2-gated verifier
   [ ] record safe docs-only result

3. Later:
   [ ] real auth provider
   [ ] public exposure review
   [ ] old external V6 source-lock track
```

## Next actionable item

```text
Choose next family: D1D object tables or SAR/S1 remaining support/QA.
```
