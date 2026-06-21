# S1-1 core-band real app-vs-reference parity plan

Status: plan ready.

This is a planning document only.

No runtime code was changed.
No verifier code was changed.
No API or frontend code was changed.
No private artifacts were committed.
No raster or NPY files were generated.

## Goal

Move `S1-1 core-band real app-vs-reference parity` from blocked to runnable by defining the reference, app-output, source-contract, and verifier gates for the notebook Sentinel-1 ASC/DESC filtered core-band outputs.

S1-1 is the next parity gate after:

```text
R1 REPORT_640 verifier passed
AIREADY-S1 secret-layer verifier passed
HYPER-1A RES_2p5M verifier passed
HYPER-1B core tensor/NPY verifier passed
INT-1 internal AI_BEH raster verifier passed
```

## Scope

S1-1 covers the eight per-band Sentinel-1 ASC/DESC filtered core-band outputs documented in the SAR ASC/DESC recovery contract.

Required GeoTIFF outputs:

```text
GEOTIFF_RADAR_BANDS/S1_ASC_VV_Filtered_640.tif
GEOTIFF_RADAR_BANDS/S1_ASC_VH_Filtered_640.tif
GEOTIFF_RADAR_BANDS/S1_DESC_VV_Filtered_640.tif
GEOTIFF_RADAR_BANDS/S1_DESC_VH_Filtered_640.tif
```

Required NPY outputs:

```text
NPY_RADAR_BANDS/S1_ASC_VV_Filtered_640.npy
NPY_RADAR_BANDS/S1_ASC_VH_Filtered_640.npy
NPY_RADAR_BANDS/S1_DESC_VV_Filtered_640.npy
NPY_RADAR_BANDS/S1_DESC_VH_Filtered_640.npy
```

Out of scope for this S1-1 gate:

```text
S1_FILTERED_LAYERS_STACK_640.npy
final app RTC outputs such as VV_dB.tif / VH_dB.tif / logRatio_dB.tif / incidence.tif
RADAR_*_640_app aliases
radar_db_support_stack.npy
radar_linear_support_stack.npy
RADAR_STACK_HWC_640_app.npy
SAR/S1 QA/provenance/intermediate families not in the eight core-band files
```

The stack `S1_FILTERED_LAYERS_STACK_640.npy` remains a related but separate tensor/stack gate unless explicitly promoted later.

## Source contract from prior recovery docs

Prior SAR ASC/DESC recovery docs identify the notebook source contract for these outputs:

```text
collection: COPERNICUS/S1_GRD
date range: 2022-01-01 to 2026-03-01
mode: IW
polarizations: VV and VH
orbit passes: ASCENDING and DESCENDING
source selection: newest image per pass by descending system:time_start
filter: focal_mean(radius=1.5, kernelType='circle', units='pixels')
grid: locked 640 D1C grid
outputs: per-band GeoTIFF and per-band NPY
```

Known important distinction:

```text
The app final RTC products are not equivalent to these notebook support outputs.
Do not alias final RTC outputs as S1-1 core-band parity outputs.
```

## Existing verifier/tooling references

Known SAR/S1 recovery and verifier tooling references include:

```text
app/pipeline/parity/s1_filtered_stack_recovery.py
app/pipeline/parity/s1_filtered_stack_verify.py
scripts/d1_sar_s1_recovery_contract.py
scripts/d1_prepare_sar_s1_reference_capture.py
scripts/d1_export_sar_s1_filtered_app_outputs.py
```

Before implementation, inspect the existing tooling and decide whether S1-1 needs a per-band TIF/NPY verifier wrapper, or whether an existing verifier can be safely reused without expanding scope to the stack.

## Gate sequence

### Gate 1 — confirm D1C reference files

Confirm the D1C/D2 frozen reference bundle contains the eight S1-1 core-band files.

Required evidence:

```text
reference bundle root exists
reference_manifest.json exists
all four GeoTIFF references exist
all four NPY references exist
all eight references are manifest-listed or safely accounted for
reference files are not copied into Git
```

Stop if references are absent. Do not fabricate reference outputs.

### Gate 2 — inspect reference metadata and safe provenance

For the reference set, record only safe metadata:

```text
file presence/counts
relative family paths only
shape / width / height
CRS / transform / pixel size for GeoTIFFs
dtype
nodata
band count
NPY shape convention
finite / NaN / nodata counts
```

Do not record exact coordinate-bearing private paths in public docs.

### Gate 3 — locate or generate app-produced S1-1 files

Find or generate matching app files under a private app run directory.

Required evidence:

```text
app output root exists under private/local run directory
all eight required app files exist
files were produced by an approved app writer path
files are not copied/renamed D1C reference files
files are not aliases of final RTC outputs
```

If app files are missing, the next implementation task must build a source-driven writer for this exact notebook support output family.

### Gate 4 — source-contract check

Before verifier pass/fail diagnosis, prove the app output follows the S1-1 source contract:

```text
same D1C grid
same selected ASCENDING source image identity or explicitly recovered source equivalent
same selected DESCENDING source image identity or explicitly recovered source equivalent
same VV/VH band ordering
same focal_mean filter contract
same output naming and folder contract
same dtype and nodata policy
```

If source image IDs/timestamps are not available, stop and recover them from the private reference/run metadata before claiming parity.

### Gate 5 — run D2-gated comparison

Use an existing verifier if it exactly matches the S1-1 per-band scope. If not, add a narrow S1-1 verifier wrapper that compares only the eight required files.

Verifier must check:

```text
missing_app_output
missing_reference_output
metadata_mismatch
shape_mismatch
dtype_mismatch
nodata_mismatch
value_mismatch
comparison_unavailable
error
passed
```

Required metrics:

```text
expected_count: 8
compared_count
counts_by_status
per-output status
max_abs_diff
mean_abs_diff
finite_compared_count
nan_or_nodata_count
```

### Gate 6 — diagnose without relaxing policy blindly

If a verifier fails, classify the failure first:

```text
metadata mismatch
shape or dtype mismatch
source selection mismatch
ASC/DESC swap
VV/VH swap
filter/reprojection mismatch
nodata policy mismatch
value mismatch
comparison unavailable
```

Do not relax tolerance until the S1-1 verifier output proves a benign variance.

### Gate 7 — record safe docs-only result

Only after a standard verifier passes:

```text
add S1-1 result doc
update REMAINING_WORK_CHECKLIST.md
update CURRENT_STATUS.md
record counts/status only
keep private payloads outside Git
```

## Current S1-1 checklist

```text
[x] S1-1 plan written
[ ] locate D2-valid S1-1 reference files
[ ] confirm four S1-1 GeoTIFF references exist
[ ] confirm four S1-1 NPY references exist
[ ] confirm reference manifest coverage or safe equivalent evidence
[ ] inspect safe reference metadata
[ ] locate app-produced S1-1 output root
[ ] confirm all eight app files exist
[ ] reject final RTC/app aliases as non-equivalent
[ ] confirm selected ASC/DESC source image contract
[ ] confirm VV/VH and ASC/DESC ordering
[ ] run or implement narrow D2-gated S1-1 verifier
[ ] diagnose failures if any
[ ] record S1-1 verifier result only after pass
```

## Safety boundary

Still blocked:

```text
public S1-1 downloads
HTTP serving of S1-1 rasters/arrays
map overlays
raw private raster/NPY payloads in Git
coordinate-bearing public exposure
claiming broader SAR/S1 parity from S1-1 alone
aliasing final RTC products as S1-1 notebook outputs
```

Allowed:

```text
private local inspection commands
private local verifier report
safe docs-only plan/result
safe counts and status fields
relative output names
```

## Decision

```text
s1_1_core_band_real_app_parity_plan_ready
```

## Next actionable item

```text
S1-1 Gate 1: locate D2-valid S1-1 reference files
```
