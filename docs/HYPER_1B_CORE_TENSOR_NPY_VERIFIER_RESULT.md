# HYPER-1B core tensor/NPY verifier result

Status: passed.

This document records safe verifier status only.

No tensor or raster payloads are included.

No exact coordinate-bearing private paths are included.

No public downloads were enabled.

No API or frontend code was changed.

No private artifacts were committed.

## Verifier

```text
CLI: python -m app.cli.hypercube_tensor_verify
schema: hypercube_tensor_npy_verification_v1
result: passed
```

The verifier was run with:

```text
D2 manifest bundle root: D1C_NEW_IPYNB_REFERENCE_2026_06_10
app run id: a11309bf-ed47-4bf5-bbf4-f755b904065c
run id: hyper-1b-a11309bf
```

A different app run candidate was rejected before this result:

```text
rejected app run id: e11d3280-a7b7-4c7c-a761-8b08ac9452f2
reason: different grid/location from the HYPER-1B D1C source contract and tensor values did not match
```

## Required outputs

```text
NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE.npy
NPY_STACKS/RADAR_STACK_HWC_640_*.npy
```

The selected app run used:

```text
NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE.npy
NPY_STACKS/RADAR_STACK_HWC_640_app.npy
```

## Result summary

```text
overall_status: passed
expected_count: 2
compared_count: 2
counts_by_status:
  passed: 2
```

## Run contract result

```text
status: comparable
comparable: true
epsg_match: true
scale_match: true
size_match: true
transform_match: true
```

The run contract accepted only a tiny transform/origin floating difference:

```text
transform_atol: 1e-05
origin_delta:
  3.227032721042633e-06
  -1.043081283569336e-07
```

The rejected candidate run had a large origin/grid mismatch and remained blocked.

## Tolerance policy

```text
atol: 1e-05
rtol: 1e-06
transform_atol: 1e-05
```

The tensor verifier used `atol=1e-05` because the radar stack had a very small floating delta. Shape, dtype, finite counts, and value comparison still had to pass.

## Output-level results

### final_tesla_v7_2_hypercube_npy

```text
status: passed
sha256_match: true
shape_match: true
dtype_match: true
compared_element_count: 3682691
app_finite_count: 3682691
reference_finite_count: 3682691
app_nan_count: 3709
reference_nan_count: 3709
app_inf_count: 0
reference_inf_count: 0
max_abs_diff: 0.0
mean_abs_diff: 0.0
allclose_pass: true
```

### radar_stack_hwc_640_npy

```text
status: passed
sha256_match: false
shape_match: true
dtype_match: true
compared_element_count: 1638400
app_finite_count: 1638400
reference_finite_count: 1638400
app_nan_count: 0
reference_nan_count: 0
app_inf_count: 0
reference_inf_count: 0
max_abs_diff: 6.67572021484375e-06
mean_abs_diff: 2.80010094133587e-07
allclose_pass: true
```

The radar tensor hash differs because the app and reference arrays are not byte-identical. Numeric comparison passed within the recorded tolerance.

## Rejected candidate run summary

```text
rejected app run id: e11d3280-a7b7-4c7c-a761-8b08ac9452f2
final_tesla_v7_2_hypercube_npy: value_mismatch
radar_stack_hwc_640_npy: value_mismatch
run_contract: not_comparable
reason: large grid/origin mismatch
```

Safe rejection metrics:

```text
final_tesla_v7_2_hypercube_npy max_abs_diff: 196456.265625
radar_stack_hwc_640_npy max_abs_diff: 19.9740629196167
```

## Tests run locally

```text
tests/unit/test_hypercube_tensor_transform_policy.py: 2 passed
```

Additional verifier evidence from the local run:

```text
D2-gated verifier overall_status: passed
git status: clean
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

Allowed and completed:

```text
D2-gated private local verifier report
safe docs-only pass/fail result
safe counts and status fields
safe selected/rejected app run ids
```

## HYPER-1B checklist closeout

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
[x] HYPER-1B verifier result recorded
```

## Decision

```text
hyper_1b_core_tensor_npy_real_app_vs_reference_parity_passed
```

## Next recommended task

```text
INT-1 internal raster real app-vs-reference parity plan
```
