# HYPER-1A RES_2p5M real app-vs-reference parity plan

Status: plan ready.

This is a planning document only.

No runtime code was changed.

No verifier code was changed.

No API or frontend code was changed.

No private artifacts were committed.

No raster or NPY files were generated.

## Goal

Move `HYPER-1A RES_2p5M real app-vs-reference parity` from blocked to runnable by defining the exact reference, app-output, and verifier gates for the notebook resampled hypercube outputs.

## Required outputs

The HYPER-1A target family is exactly:

```text
FINAL_TESLA_V7_2_HYPERCUBE_RES_2p5M.tif
FINAL_TESLA_V7_2_HYPERCUBE_RES_2p5M.npy
```

Both files are required. File existence alone is not parity proof.

## Existing source/contract

Existing contract:

```text
docs/HYPERCUBE_RES_2P5M_PARITY_CONTRACT.md
```

Existing verifier:

```text
app/pipeline/parity/hypercube_res25_verify.py
```

Existing CLI:

```text
python -m app.cli.hypercube_res25_verify
```

The verifier checks both direct-root and `NPY_STACKS/` lookup locations for the required files.

## Source expectations

The notebook source contract defines these outputs as resampled from:

```text
FINAL_TESLA_V7_2_HYPERCUBE.tif
```

Expected locked behavior:

```text
pixel size: 2.5 m
band count: 9
band order: notebook-preserved source band order
NPY shape convention: CHW
GeoTIFF layout: multi-band GeoTIFF
dtype: float32
resampling method: cubic
```

Expected band order:

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

## Current known risk

The app may not currently write the two required notebook-named `RES_2p5M` files.

The contract says these are not substitutes:

```text
hypercube.tif
hypercube.npy
NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE.npy
NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE_PATCHED_14B.tif
science_core_stack.*
ai_ready_support_stack.*
```

Do not alias, rename, or copy these as parity substitutes.

## Gate sequence

### Gate 1 — locate D2-valid reference files

Confirm the formal D2 bundle contains:

```text
FINAL_TESLA_V7_2_HYPERCUBE_RES_2p5M.tif
FINAL_TESLA_V7_2_HYPERCUBE_RES_2p5M.npy
```

Accepted reference locations:

```text
bundle root
bundle root / NPY_STACKS
```

Required evidence:

```text
reference_manifest.json exists in the D2 bundle root
both required reference files exist
both required reference files are listed in the manifest
reference files are not copied into Git
```

### Gate 2 — locate app-produced HYPER-1A outputs

Find an app run directory containing both required notebook-named files:

```text
FINAL_TESLA_V7_2_HYPERCUBE_RES_2p5M.tif
FINAL_TESLA_V7_2_HYPERCUBE_RES_2p5M.npy
```

Accepted app locations:

```text
app output root
app output root / NPY_STACKS
```

Required evidence:

```text
app output root exists under private/local run directory
both required app files exist
files were produced by app pipeline or approved app writer path
files are not copied/renamed notebook reference files
```

If app files are missing, stop. The next task becomes a source/reference-driven implementation slice to produce the notebook-named resampled outputs.

### Gate 3 — run D2-gated verifier

Verifier command shape:

```powershell
python -m app.cli.hypercube_res25_verify `
  --app-output-dir <PRIVATE_APP_OUTPUT_ROOT> `
  --bundle-dir <PRIVATE_D2_REFERENCE_BUNDLE_ROOT> `
  --run-dir <PRIVATE_HYPER_1A_RUN_DIR> `
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

Output-level expected result:

```text
resampled_hypercube_tif: passed
resampled_hypercube_npy: passed
```

### Gate 4 — diagnose failures without changing data

If the verifier fails, classify the failure:

```text
missing_app_output: app did not produce required notebook-named file
missing_reference_output: D2 reference bundle does not contain required file
metadata_mismatch: TIFF metadata/grid contract differs
shape_mismatch: NPY shape contract differs
dtype_mismatch: NPY dtype contract differs
value_mismatch: values differ outside tolerance
comparison_unavailable: environment dependency missing
```

Do not patch tolerance or metadata policy until the failure is understood from safe diagnostics.

### Gate 5 — record HYPER-1A result

Only after pass:

```text
[ ] Add docs-only HYPER-1A result
[ ] Include reference bundle identity
[ ] Include app output source/run identity
[ ] Include verifier command shape
[ ] Include status counts
[ ] Include tolerance
[ ] Include safe per-output summary
[ ] Do not include private raster or NPY payloads
[ ] Do not include exact coordinate-bearing paths
[ ] Do not enable public downloads or serving
```

## Current HYPER-1A checklist

```text
[x] HYPER-1A plan written
[ ] locate D2-valid HYPER-1A reference files       <- NEXT
[ ] confirm reference TIF exists
[ ] confirm reference NPY exists
[ ] confirm both references are manifest-listed
[ ] locate app-produced HYPER-1A output root
[ ] confirm app TIF exists
[ ] confirm app NPY exists
[ ] run D2-gated verifier
[ ] record HYPER-1A verifier result
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
```

Allowed:

```text
private local verifier report
safe docs-only pass/fail result
safe counts and status fields
```

## Decision

```text
hyper_1a_res_2p5m_real_app_parity_plan_ready
```

## Next actionable item

```text
HYPER-1A Gate 1: locate D2-valid RES_2p5M reference files
```
