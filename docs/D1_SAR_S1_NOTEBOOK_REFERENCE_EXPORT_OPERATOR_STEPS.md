# D1 SAR/S1 Notebook Reference Export Operator Steps

## Status

The local SAR/S1 recovery inventory found that all required S1 filtered outputs are absent from both the source app run and the D1 reference bundle.

This document gives the operator-side export recipe for producing the required notebook reference files into a local staging folder. It does not change production SAR code and does not prove value parity by itself.

## Required outputs

The staging folder must contain exactly these output names:

```text
S1_ASC_VV_Filtered_640.tif
S1_ASC_VH_Filtered_640.tif
S1_DESC_VV_Filtered_640.tif
S1_DESC_VH_Filtered_640.tif
S1_ASC_VV_Filtered_640.npy
S1_ASC_VH_Filtered_640.npy
S1_DESC_VV_Filtered_640.npy
S1_DESC_VH_Filtered_640.npy
S1_FILTERED_LAYERS_STACK_640.npy
```

## Target staging folder

```text
data/private_references/notebook_frozen/new_ipynb_d1_20260615_local/sar_s1_capture_staging
```

## Notebook source contract

Use the notebook's S1 filtered export block, not the app's final RTC products.

The expected source behavior is:

```text
collection: COPERNICUS/S1_GRD
date window: 2022-01-01 to 2026-03-01
mode: IW
polarizations: VV and VH
orbit passes: newest ASCENDING and newest DESCENDING separately
filter: focal_mean(radius=1.5, kernelType='circle', units='pixels')
grid: existing notebook locked 640 grid
per-band order: ASC VV, ASC VH, DESC VV, DESC VH
stack shape: HWC
stack dtype: float32
```

## Operator steps

1. Open the same local `new.ipynb` that produced the D1 baseline.
2. Run prerequisite cells only as needed so the locked grid, ROI/region, output size, nodata value, GeoTIFF profile, tile sampling helper, and Earth Engine session are available.
3. Run the notebook S1 filtered export block that produces the four ASC/DESC filtered bands.
4. Direct the output path to the staging folder above.
5. Confirm the nine filenames exist in staging.
6. Run the capture helper dry-run.
7. Copy into the D1 bundle only after dry-run shows all nine files ready.

## Dry-run command

```powershell
python scripts/d1_prepare_sar_s1_reference_capture.py `
  --source-dir data/private_references/notebook_frozen/new_ipynb_d1_20260615_local/sar_s1_capture_staging `
  --bundle-root data/private_references/notebook_frozen/new_ipynb_d1_20260615_local `
  --report data/private_references/notebook_frozen/new_ipynb_d1_20260615_local/sar_s1_reference_capture_plan.local.json
```

Expected ready state:

```text
status: ready
required_output_count: 9
ready_to_copy_count: 9
missing_source_count: 0
copied_count: 9
dry_run: True
```

## Copy command

Run only after the dry-run is ready:

```powershell
python scripts/d1_prepare_sar_s1_reference_capture.py `
  --source-dir data/private_references/notebook_frozen/new_ipynb_d1_20260615_local/sar_s1_capture_staging `
  --bundle-root data/private_references/notebook_frozen/new_ipynb_d1_20260615_local `
  --report data/private_references/notebook_frozen/new_ipynb_d1_20260615_local/sar_s1_reference_capture_plan.local.json `
  --copy
```

## After copy

Re-finalize and validate the D1 manifest:

```powershell
python scripts/d1_finalize_reference_bundle.py `
  --bundle-root data/private_references/notebook_frozen/new_ipynb_d1_20260615_local `
  --notebook-version local-new-ipynb-version `
  --source-run-id a11309bf-ed47-4bf5-bbf4-f755b904065c `
  --operator Maher

python scripts/d1_validate_reference_manifest.py `
  --manifest data/private_references/notebook_frozen/new_ipynb_d1_20260615_local/manifest.local.json `
  --strict
```

Then rerun the SAR/S1 recovery inventory:

```powershell
python scripts/d1_sar_s1_recovery_contract.py `
  --app-output-dir data/runs/a11309bf-ed47-4bf5-bbf4-f755b904065c `
  --reference-sar-root data/private_references/notebook_frozen/new_ipynb_d1_20260615_local/artifacts/sar `
  --report data/private_references/notebook_frozen/new_ipynb_d1_20260615_local/sar_s1_recovery_contract.local.json
```

## Boundaries

Do not use these as substitutes:

```text
VV_dB.tif
VH_dB.tif
logRatio_dB.tif
incidence.tif
RADAR_*_640_app.*
RADAR_STACK_HWC_640_app.npy
radar_db_support_stack.npy
radar_linear_support_stack.npy
```

Those are not equivalent to the required S1 filtered outputs.

Do not change SAR math, source selection, orbit selection, pair selection, GRID behavior, writer paths, tolerance policy, API, frontend, or artifact serving as part of this reference capture step.
