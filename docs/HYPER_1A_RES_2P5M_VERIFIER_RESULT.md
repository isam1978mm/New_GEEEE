# HYPER-1A RES_2p5M verifier result

Status: passed.

This document records safe verifier status only.

No raster or NPY payloads are included.

No exact coordinate-bearing private paths are included.

No public downloads were enabled.

No API or frontend code was changed.

No private artifacts were committed.

## Verifier

```text
CLI: python -m app.cli.hypercube_res25_verify
schema: hypercube_res_2p5m_parity_verification_v1
result: passed
```

The verifier was run with:

```text
D2 manifest bundle root: D1C_NEW_IPYNB_REFERENCE_2026_06_10
app run id: a11309bf-ed47-4bf5-bbf4-f755b904065c
run id: hyper-1a-a11309bf
```

A different app run candidate was rejected before this result:

```text
rejected app run id: e11d3280-a7b7-4c7c-a761-8b08ac9452f2
reason: different grid/location from the HYPER-1A D1C source hypercube and values did not match
```

## Required outputs

```text
FINAL_TESLA_V7_2_HYPERCUBE_RES_2p5M.tif
FINAL_TESLA_V7_2_HYPERCUBE_RES_2p5M.npy
```

## App output generation

The required app outputs were generated locally from the app-produced source hypercube:

```text
source: FINAL_TESLA_V7_2_HYPERCUBE.tif
method: scipy.ndimage.zoom(..., order=3)
source pixel size: 10 m
output pixel size: 2.5 m
zoom_factor: 4.0
band count: 9
expected output shape: CHW [9, 2560, 2560]
dtype: float32
```

Generation safety flags:

```text
reference_outputs_read: false
earth_engine_called: false
api_frontend_changed: false
raster_payloads_committed: false
```

Generated output sizes:

```text
FINAL_TESLA_V7_2_HYPERCUBE_RES_2p5M.npy: 235929728 bytes
FINAL_TESLA_V7_2_HYPERCUBE_RES_2p5M.tif: 197109211 bytes
```

## Source run selection

The selected source run was:

```text
a11309bf-ed47-4bf5-bbf4-f755b904065c
```

Source hypercube diagnostic before generation:

```text
NPY source shape_match: true
NPY source dtype_match: true
NPY source max_abs_diff: 0.0
NPY source mean_abs_diff: 0.0
NPY source allclose_1e-6: true
TIF source same_shape: true
TIF source max_abs_diff: 0.0
TIF source mean_abs_diff: 0.0
TIF source allclose_1e-6: true
```

The source TIF had benign metadata differences that did not affect values:

```text
small transform/origin floating difference
band-description prefix wording difference
```

## Result summary

```text
overall_status: passed
expected_count: 2
compared_count: 2
counts_by_status:
  passed: 2
```

## Tolerance policy

```text
atol: 1e-06
rtol: 1e-06
transform_atol: 1e-05
```

The GeoTIFF verifier permits only tiny transform/origin floating differences up to `transform_atol`. All value checks remain strict.

Observed benign transform/origin maximum delta:

```text
3.227032721042633e-06
```

## Output-level results

### FINAL_TESLA_V7_2_HYPERCUBE_RES_2p5M.npy

```text
status: passed
sha256_match: true
shape_match: true
dtype_match: true
compared_element_count: 58982400
app_finite_count: 58982400
reference_finite_count: 58982400
app_nan_count: 0
reference_nan_count: 0
app_inf_count: 0
reference_inf_count: 0
max_abs_diff: 0.0
mean_abs_diff: 0.0
allclose_pass: true
```

### FINAL_TESLA_V7_2_HYPERCUBE_RES_2p5M.tif

```text
status: passed
sha256_match: false
compared_element_count: 58975912
max_abs_diff: 0.0
mean_abs_diff: 0.0
allclose_pass: true
```

The GeoTIFF file hash differs because metadata is not byte-identical. Numeric value comparison passed exactly after the verifier accepted the benign transform/origin floating delta.

## Tests run locally

```text
tests/unit/test_hypercube_res25_transform_policy.py: 2 passed
tests/unit/test_hyper_1a_generate_res_2p5m.py: 3 passed
tests/unit/test_hypercube_res25_verify_cli.py: 4 passed
```

## Safety boundary

Still blocked:

```text
public HYPER-1A downloads
HTTP serving of HYPER-1A rasters or tensors
map overlays
raw private raster/NPY payloads in Git
coordinate-bearing public exposure
claiming broader hypercube parity from HYPER-1A alone
claiming broader notebook parity from this result alone
```

Allowed and completed:

```text
local app-side generation from matching app source
D2-gated private local verifier report
safe docs-only pass/fail result
safe counts and status fields
```

## HYPER-1A checklist closeout

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
[x] HYPER-1A verifier result recorded
```

## Decision

```text
hyper_1a_res_2p5m_real_app_vs_reference_parity_passed
```

## Next recommended task

```text
HYPER-1B core tensor/NPY real app-vs-reference parity plan
```
