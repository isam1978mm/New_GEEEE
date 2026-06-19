# HYPER-1B core tensor/NPY real app-vs-reference parity plan

Status: plan ready.

This is a planning document only.

No runtime code was changed.

No verifier code was changed.

No API or frontend code was changed.

No private artifacts were committed.

No tensor or raster files were generated.

## Goal

Move `HYPER-1B core tensor/NPY real app-vs-reference parity` from blocked to runnable by defining the exact reference, app-output, run-contract, and verifier gates for the notebook core tensor outputs.

## Existing verifier

Existing CLI:

```text
python -m app.cli.hypercube_tensor_verify
```

Existing verifier:

```text
app/pipeline/parity/hypercube_tensor_verify.py
```

The CLI is D2-gated. It validates the frozen reference bundle, delegates to `verify_hypercube_tensor_parity`, prints a path-safe summary by default, and writes only a JSON report under `--run-dir`.

## Required outputs

The source-locked HYPER-1B verifier currently expects exactly two logical tensor outputs:

```text
logical_name: final_tesla_v7_2_hypercube_npy
required file: NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE.npy
shape convention: CHW
channel_axis: 0
channels: 9
```

```text
logical_name: radar_stack_hwc_640_npy
required file pattern: NPY_STACKS/RADAR_STACK_HWC_640_*.npy
preferred app file: NPY_STACKS/RADAR_STACK_HWC_640_app.npy
shape convention: HWC
channel_axis: -1
channels: 4
```

## Expected channel contracts

### final_tesla_v7_2_hypercube_npy

Expected channels:

```text
1. AI_READY_640_Secret_Gold_Halo
2. AI_READY_640_Secret_Silver_Oxide
3. AI_READY_640_Secret_Tunnel_Ceiling
4. AI_READY_640_Secret_Thermal_Inertia
5. AI_READY_640_Secret_Chemical_Protector
6. AI_READY_640_Secret_Hidden_Doors
7. REPORT_640_FINAL_Zero_Point_Targets
8. REPORT_640_Mass_Report
9. REPORT_640_Pottery_Report
```

### radar_stack_hwc_640_npy

Expected channels:

```text
1. VV_dB
2. VH_dB
3. logRatio_dB
4. angle
```

## Important distinction from HYPER-1A

HYPER-1A verified the resampled 2.5 m outputs:

```text
FINAL_TESLA_V7_2_HYPERCUBE_RES_2p5M.tif
FINAL_TESLA_V7_2_HYPERCUBE_RES_2p5M.npy
```

HYPER-1B verifies core tensor/NPY files at the base 640 grid:

```text
FINAL_TESLA_V7_2_HYPERCUBE.npy
RADAR_STACK_HWC_640_*.npy
```

Do not treat the HYPER-1A RES_2p5M outputs as HYPER-1B parity evidence.

## Gate sequence

### Gate 1 — locate D2-valid reference files

Confirm the formal D2 bundle contains the required HYPER-1B references:

```text
NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE.npy
NPY_STACKS/RADAR_STACK_HWC_640_*.npy
```

Required evidence:

```text
reference_manifest.json exists in the D2 bundle root
FINAL_TESLA_V7_2_HYPERCUBE.npy exists
exactly one RADAR_STACK_HWC_640_*.npy reference resolves
both required references are listed in the manifest
reference files are not copied into Git
```

### Gate 2 — locate app-produced HYPER-1B files

Find matching app output files under the selected app run:

```text
NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE.npy
NPY_STACKS/RADAR_STACK_HWC_640_app.npy
or exactly one NPY_STACKS/RADAR_STACK_HWC_640_*.npy
```

Required evidence:

```text
app output root exists under private/local run directory
both required app tensors exist
files were produced by the app pipeline or approved app writer path
files are not copied/renamed notebook reference files
```

### Gate 3 — run grid/source contract check

The HYPER-1B verifier includes a run-contract comparison. It checks:

```text
epsg_match
scale_match
size_match
transform_match
origin_delta
transform_delta
comparable
```

If the contract reports `not_comparable`, stop and diagnose. Do not patch this until the selected app run is proven to be the intended matching run.

Known risk from previous gates:

```text
a113 matched R1 and HYPER-1A source values.
e11 matched AIREADY-S1 secret layers.
```

For HYPER-1B, choose the app run by the tensor/grid evidence, not by assumption.

### Gate 4 — run D2-gated verifier

Verifier command shape:

```powershell
python -m app.cli.hypercube_tensor_verify `
  --app-output-dir <PRIVATE_APP_OUTPUT_ROOT> `
  --bundle-dir <PRIVATE_D2_REFERENCE_BUNDLE_ROOT> `
  --run-dir <PRIVATE_HYPER_1B_RUN_DIR> `
  --run-id <RUN_ID>
```

Expected close result:

```text
overall_status: passed
expected_count: 2
compared_count: 2
counts_by_status:
  passed: 2
```

Expected per-output result:

```text
final_tesla_v7_2_hypercube_npy: passed
radar_stack_hwc_640_npy: passed
```

### Gate 5 — diagnose failures without changing data

Failure meanings:

```text
blocked_needs_app_hypercube_tensor_run: selected app/reference grid contract is not comparable
missing_app_output: app did not produce required tensor
missing_reference_output: D2 reference bundle does not contain required tensor
ambiguous_app_output: more than one app tensor matched the source-locked locator
ambiguous_reference_output: more than one reference tensor matched the source-locked locator
shape_mismatch: NPY shape contract differs
dtype_mismatch: NPY dtype contract differs
value_mismatch: tensor values differ outside tolerance
error: unexpected read/compare error
```

Do not copy, rename, or alias tensors to force a pass.

### Gate 6 — record HYPER-1B result

Only after pass:

```text
[ ] Add docs-only HYPER-1B result
[ ] Include reference bundle identity
[ ] Include selected app run identity
[ ] Include rejected candidate run identity if applicable
[ ] Include verifier command shape
[ ] Include run-contract safe summary
[ ] Include status counts
[ ] Include tolerance
[ ] Include safe per-output summary
[ ] Do not include private tensor payloads
[ ] Do not include exact coordinate-bearing paths
[ ] Do not enable public downloads or serving
```

## Current HYPER-1B checklist

```text
[x] HYPER-1B plan written
[ ] locate D2-valid HYPER-1B reference files       <- NEXT
[ ] confirm reference FINAL_TESLA_V7_2_HYPERCUBE.npy exists
[ ] confirm exactly one reference RADAR_STACK_HWC_640_*.npy exists
[ ] confirm both references are manifest-listed
[ ] locate app-produced HYPER-1B output root
[ ] confirm app FINAL_TESLA_V7_2_HYPERCUBE.npy exists
[ ] confirm app RADAR_STACK_HWC_640 tensor exists
[ ] run contract check through verifier
[ ] run D2-gated verifier
[ ] record HYPER-1B verifier result
```

## Safety boundary

Still blocked:

```text
public HYPER-1B downloads
HTTP serving of HYPER-1B tensors
map overlays
raw private tensor payloads in Git
coordinate-bearing public exposure
claiming broader hypercube parity from HYPER-1B alone
claiming broader notebook parity from this result alone
```

Allowed:

```text
private local verifier report
safe docs-only pass/fail result
safe counts and status fields
```

## Decision

```text
hyper_1b_core_tensor_npy_real_app_parity_plan_ready
```

## Next actionable item

```text
HYPER-1B Gate 1: locate D2-valid core tensor reference files
```
