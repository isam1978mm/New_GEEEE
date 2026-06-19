# Remaining Work Checklist

This document is the working checklist for choosing the next task after the H5 score-band aggregate review, R1 REPORT_640 verifier pass, AIREADY-S1 verifier pass, HYPER-1A verifier pass, and HYPER-1B verifier pass.

It separates completed work, next parity work, blocked parity work, source-recovery work, safety boundaries, and later/deployment-only work.

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
[x] AIREADY-S1 result doc recorded
[x] HYPER-1A RES_2p5M verifier passed
[x] HYPER-1A result doc recorded
[x] HYPER-1B core tensor/NPY verifier passed
[x] HYPER-1B result doc recorded
```

## 1. R1 REPORT_640 real app-vs-reference parity

Current state:

```text
[x] R1 plan written
[x] R1 runnable evidence collected
[x] R1 verifier passed
[x] R1 result recorded
```

R1 closeout result:

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

Safety boundary remains:

```text
[x] no raster payloads committed
[x] no exact coordinate-bearing paths committed
[x] no public REPORT_640 downloads enabled
[x] no HTTP raster serving enabled
[x] no map overlays enabled
```

## 2. AIREADY real app-vs-reference parity

Current state:

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

AIREADY-S1 closeout result:

```text
overall_status: passed
expected_count: 6
compared_count: 6
counts_by_status:
  passed: 6
```

Required AIREADY-S1 outputs passed:

```text
[x] AI_READY_640_Secret_Gold_Halo.tif
[x] AI_READY_640_Secret_Silver_Oxide.tif
[x] AI_READY_640_Secret_Tunnel_Ceiling.tif
[x] AI_READY_640_Secret_Thermal_Inertia.tif
[x] AI_READY_640_Secret_Chemical_Protector.tif
[x] AI_READY_640_Secret_Hidden_Doors.tif
```

Remaining AIREADY work:

```text
[ ] AIREADY-FR Fraction outputs: source known, app writer/output path still needed
[ ] AIREADY-MH Metal Hardness: source-recovery blocked
[ ] AIREADY-AN Magnetic/EM anomaly: source-recovery blocked
```

Do not claim all AIREADY parity from AIREADY-S1 alone.

## 3. HYPER-1A RES_2p5M real app-vs-reference parity

Current state:

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

HYPER-1A closeout result:

```text
overall_status: passed
expected_count: 2
compared_count: 2
counts_by_status:
  passed: 2
```

Required HYPER-1A outputs passed:

```text
[x] FINAL_TESLA_V7_2_HYPERCUBE_RES_2p5M.tif
[x] FINAL_TESLA_V7_2_HYPERCUBE_RES_2p5M.npy
```

Safety boundary remains:

```text
[x] no raster/NPY payloads committed
[x] no exact coordinate-bearing paths committed
[x] no public HYPER-1A downloads enabled
[x] no HTTP raster/tensor serving enabled
[x] no map overlays enabled
```

## 4. HYPER-1B core tensor/NPY real app-vs-reference parity

Current state:

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

HYPER-1B closeout result:

```text
overall_status: passed
expected_count: 2
compared_count: 2
counts_by_status:
  passed: 2
```

Required HYPER-1B outputs passed:

```text
[x] FINAL_TESLA_V7_2_HYPERCUBE.npy
[x] RADAR_STACK_HWC_640_*.npy
```

Safety boundary remains:

```text
[x] no tensor payloads committed
[x] no exact coordinate-bearing paths committed
[x] no public HYPER-1B downloads enabled
[x] no HTTP tensor serving enabled
[x] no map overlays enabled
```

## 5. Next blocked real app-vs-reference parity items

These are after R1, AIREADY-S1, HYPER-1A, and HYPER-1B.

```text
[ ] INT-1 internal raster real app-vs-reference parity          <- NEXT RECOMMENDED
[ ] S1-1 core-band real app-vs-reference parity
```

Common sub-checklist for each:

```text
[ ] Locate frozen D1C reference files
[ ] Locate or generate matching app files
[ ] Confirm app files are real app outputs, not copied references
[ ] Confirm CRS / scale / transform / shape / dtype / band semantics
[ ] Run family-specific verifier
[ ] Record safe docs-only result
```

## 6. Source-recovery items

These are not ready for verifier work yet.

```text
[ ] D1D object-table outputs
[ ] AI_READY remaining support families
[ ] SAR/S1 support, intermediate, and QA/provenance outputs
[ ] PAN/optical image components and stack
```

Do not fabricate outputs. Do not treat renamed app-native equivalents as notebook parity.

### 6A. D1D object-table outputs

```text
[ ] Recover/export same-run object-table family
[ ] Confirm objects_index.csv
[ ] Confirm clusters_summary.csv
[ ] Confirm related source tensors consistently match same run
[ ] Run D2-gated comparison
```

### 6B. AI_READY remaining support families

```text
[ ] AIREADY-FR: decide whether to build Fraction output writer path
[ ] AIREADY-MH: recover Metal Hardness source/writer contract
[ ] AIREADY-AN: recover Magnetic/EM anomaly source/writer contract
```

### 6C. SAR/S1 support/intermediate/QA outputs

```text
[ ] Recover exact notebook source contract
[ ] Recover selected source IDs / metadata
[ ] Confirm ASC/DESC filtered layers
[ ] Confirm S1_FILTERED_LAYERS_STACK_640.npy requirement
[ ] Confirm pre-RTC/intermediate/QA outputs
[ ] Add app writer path if missing
[ ] Verify only after source recovery
```

### 6D. PAN/optical image components and stack

```text
[ ] Recover optical/PAN source requirement
[ ] Confirm notebook source logic
[ ] Confirm PAN component outputs
[ ] Confirm PAN_LAYERS_STACK_640.npy
[ ] Add explicit source-driven PAN writer/run
[ ] Run PAN component and stack verifiers
```

## 7. H5 / prediction serving boundaries still blocked

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

## 8. Paid Imagery Request Package / old V6 status

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

## 9. Deployment/auth/public exposure — later only

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
1. INT-1 internal raster real app-vs-reference parity
   [ ] write/confirm INT-1 plan
   [ ] locate private D1C INT-1 reference files
   [ ] locate/generate private app INT-1 output files
   [ ] confirm required INT-1 file set
   [ ] run grid/source contract check
   [ ] run D2-gated verifier
   [ ] record INT-1 verifier result

2. After INT-1
   [ ] S1-1 parity

3. Heavier recovery
   [ ] D1D object tables
   [ ] AI_READY remaining support families
   [ ] SAR/S1 recovery/build
   [ ] PAN recovery/build

4. Later
   [ ] real auth provider
   [ ] public exposure review
   [ ] old external V6 source-lock track
```

## Next actionable item

```text
INT-1 internal raster real app-vs-reference parity plan
```
