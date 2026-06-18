# Remaining Work Checklist

This document is the working checklist for choosing the next task after the H5 score-band aggregate review.

It separates completed work, next R1 work, blocked parity work, source-recovery work, safety boundaries, and later/deployment-only work.

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
```

## 1. R1 REPORT_640 real app-vs-reference parity

Current state:

```text
[x] R1 plan written
[ ] R1 runnable evidence not collected yet
```

R1 is blocked, not failed, until all required app-output, reference-output, grid/source, and verifier gates pass.

### 1A. Locate frozen D1C REPORT_640 reference root

```text
[ ] Find private frozen D1C reference folder outside Git
[ ] Confirm reference root exists outside Git
[ ] Confirm reference bundle identity is known
[ ] Confirm D2 validator passes for the reference bundle
[ ] Confirm required reference TIF exists: REPORT_640_Pottery_Report.tif
[ ] Confirm required reference TIF exists: REPORT_640_Mass_Report.tif
[ ] Confirm required reference TIF exists: REPORT_640_FINAL_Zero_Point_Targets.tif
```

Stop condition:

```text
[ ] If reference files are missing locally, stop and reconcile D1/D1C docs before continuing.
```

### 1B. Locate or generate private app REPORT_640 output root

```text
[ ] Locate existing app-generated REPORT_640 output root
    OR
[ ] Generate app REPORT_640 outputs using approved app pipeline/writer path

[ ] Confirm app output root is outside Git or under a private run directory
[ ] Confirm required app TIF exists: REPORT_640_Pottery_Report.tif
[ ] Confirm required app TIF exists: REPORT_640_Mass_Report.tif
[ ] Confirm required app TIF exists: REPORT_640_FINAL_Zero_Point_Targets.tif
[ ] Confirm outputs were produced by app pipeline or approved app writer path
[ ] Confirm outputs are not copied/renamed notebook reference files
```

### 1C. D1C grid/source contract check

Before value parity, check:

```text
[ ] CRS matches
[ ] scale matches
[ ] width / height match
[ ] transform / origin match
[ ] band count matches
[ ] shape convention matches
[ ] dtype matches
[ ] nodata matches
[ ] output semantics match
```

### 1D. Run D2-gated REPORT_640 verifier

Verifier:

```text
scripts/d1_compare_report_value_parity.py
```

Command shape:

```powershell
python scripts/d1_compare_report_value_parity.py `
  --app-output-dir <PRIVATE_APP_REPORT_640_ROOT> `
  --reference-report-root <PRIVATE_D1C_REPORT_640_REFERENCE_ROOT> `
  --report <PRIVATE_R1_REPORT_640_PARITY_REPORT_JSON> `
  --json
```

Expected close result:

```text
[ ] status: passed
[ ] pass_count: 3
[ ] fail_count: 0
[ ] missing_count: 0
[ ] comparison_unavailable_count: 0
```

### 1E. Record R1 verifier result

Only after pass:

```text
[ ] Add docs-only R1 result
[ ] Include reference bundle identity
[ ] Include app output source/run identity
[ ] Include verifier command shape
[ ] Include status/pass/fail/missing/comparison_unavailable counts
[ ] Include tolerance
[ ] Do not include private raster contents
[ ] Do not include exact coordinates
[ ] Do not include private file payloads
```

## 2. Other blocked real app-vs-reference parity items

These are after R1, not before it.

```text
[ ] AIREADY real app-vs-reference parity
[ ] HYPER-1A RES_2p5M real app-vs-reference parity
[ ] HYPER-1B core tensor/NPY real app-vs-reference parity
[ ] INT-1 internal raster real app-vs-reference parity
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

## 3. Source-recovery items

These are not ready for verifier work yet.

```text
[ ] D1D object-table outputs
[ ] AI_READY remaining support families
[ ] SAR/S1 support, intermediate, and QA/provenance outputs
[ ] PAN/optical image components and stack
```

Do not fabricate outputs. Do not treat renamed app-native equivalents as notebook parity.

### 3A. D1D object-table outputs

```text
[ ] Recover/export same-run object-table family
[ ] Confirm objects_index.csv
[ ] Confirm clusters_summary.csv
[ ] Confirm related source tensors consistently match same run
[ ] Run D2-gated comparison
```

### 3B. AI_READY remaining support families

```text
[ ] Identify exact remaining family
[ ] Confirm source evidence
[ ] Define output paths
[ ] Define metadata contract
[ ] Freeze references
[ ] Add/build explicit recovery task
[ ] Verify after recovery
```

### 3C. SAR/S1 support/intermediate/QA outputs

```text
[ ] Recover exact notebook source contract
[ ] Recover selected source IDs / metadata
[ ] Confirm ASC/DESC filtered layers
[ ] Confirm S1_FILTERED_LAYERS_STACK_640.npy requirement
[ ] Confirm pre-RTC/intermediate/QA outputs
[ ] Add app writer path if missing
[ ] Verify only after source recovery
```

### 3D. PAN/optical image components and stack

```text
[ ] Recover optical/PAN source requirement
[ ] Confirm notebook source logic
[ ] Confirm PAN component outputs
[ ] Confirm PAN_LAYERS_STACK_640.npy
[ ] Add explicit source-driven PAN writer/run
[ ] Run PAN component and stack verifiers
```

## 4. H5 / prediction serving boundaries still blocked

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

## 5. Paid Imagery Request Package / old V6 status

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

## 6. Deployment/auth/public exposure — later only

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
1. R1 REPORT_640
   [ ] locate private D1C REPORT_640 reference root
   [ ] locate/generate private app REPORT_640 output root
   [ ] confirm 3 reference TIFs
   [ ] confirm 3 app TIFs
   [ ] run grid/source contract check
   [ ] run D2-gated verifier
   [ ] record R1 verifier result

2. After R1
   [ ] AIREADY real app-vs-reference parity
   [ ] HYPER-1A parity
   [ ] HYPER-1B parity
   [ ] INT-1 parity
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
R1 Gate 1: locate private D1C REPORT_640 reference root
```
