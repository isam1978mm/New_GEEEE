# PAN Layers Stack Parity Contract

## Purpose

Phase 4G locks source recovery and verification requirements for the notebook output:

```text
PAN_LAYERS_STACK_640.npy
```

This output belongs to the notebook panchromatic and optical support family and must remain separate from the app's current S2 index outputs, optical support mask, and generic feature stacks.

Phase 4G is recovery and verification-contract only. It does not generate the stack, implement panchromatic production, change optical math, call Earth Engine, or integrate with the live pipeline.

## Scope

Phase 4G adds:

- `app/pipeline/parity/pan_stack_recovery.py`
- `app/pipeline/parity/pan_stack_verify.py`
- `tests/parity/test_pan_stack_recovery.py`
- `tests/parity/test_pan_stack_verify.py`
- this contract document

The work is limited to:

- source recovery for the notebook PAN stack meaning;
- a machine-readable checklist for later implementation;
- an NPY verification harness for a future app-produced counterpart;
- JSON report writing under the run manifests directory.

## Non-Goals

Phase 4G does not:

- generate `PAN_LAYERS_STACK_640.npy`;
- implement stack generation in the app;
- implement `PAN_LS_Panchromatic_640.*` or `PAN_S2_Panchromatic_10m_640.*` writers;
- alias existing optical outputs as PAN outputs;
- change Sentinel-2 formulas;
- change Landsat formulas;
- change panchromatic formulas;
- change SAR, DEM, thermal, PCA, object extraction, or classifier logic;
- change API, frontend, database models, migrations, or artifact serving policy;
- add Earth Engine calls;
- commit raster or `.npy` outputs.

Existing app outputs are not automatically equivalent to this stack.

## Authoritative Notebook Source

`notebooks/new.ipynb` contains two PAN export cells. The authoritative source for Phase 4G is the second optical-only PAN cell around lines `25645-25890` because it writes the optical family into `OPT/PAN_TIFS_640`, `OPT/PAN_NPY_640`, and `NPY_STACKS`, which matches the notebook output family this phase targets.

The notebook source shows:

- Landsat 9 panchromatic source:
  - `LANDSAT/LC09/C02/T1_TOA`
  - `select('B8')`
  - `resample('bilinear')`
  - renamed to `LS_Panchromatic`
- Sentinel-2 panchromatic-equivalent source:
  - `COPERNICUS/S2_SR_HARMONIZED`
  - `select(['B2', 'B3', 'B4', 'B8'])`
  - `reduce(ee.Reducer.mean())`
  - renamed to `S2_Panchromatic_10m`
- stack assembly:
  - `pan_stack = ee.Image.cat([landsat_pan_layer, sentinel_high_res])`
- band order is therefore:
  - `LS_Panchromatic`
  - `S2_Panchromatic_10m`
- stack sampling:
  - `cube = np.full((OUT_SIZE, OUT_SIZE, len(bands)), NODATA, dtype=np.float32)`
  - tiles are sampled with `sampleRectangle(defaultValue=NODATA)`
  - the cell applies `finite_or_nodata(arr)` before tile assignment
- per-band outputs:
  - `PAN_LS_Panchromatic_640.tif`
  - `PAN_S2_Panchromatic_10m_640.tif`
  - `PAN_LS_Panchromatic_640.npy`
  - `PAN_S2_Panchromatic_10m_640.npy`
- stack output:
  - `np.save(stack_path, cube.astype(np.float32))`
  - `stack_path = .../PAN_LAYERS_STACK_640.npy`

This is evidence-backed source for the stack band order, HWC shape convention, float32 dtype, and NODATA-filled allocation behavior.

## Locked Expectations

Evidence-backed expectations from the notebook source:

- output name: `PAN_LAYERS_STACK_640.npy`
- family: `panchromatic/optical outputs`
- target mode: `notebook_parity`
- classification: `notebook-parity`
- artifact class: `FILESYSTEM_ONLY`
- HTTP servable: `false`
- coordinate-bearing: `false`
- probability-only required: `false`
- expected input outputs:
  - `PAN_LS_Panchromatic_640.npy`
  - `PAN_S2_Panchromatic_10m_640.npy`
- expected band order:
  - `LS_Panchromatic`
  - `S2_Panchromatic_10m`
- expected shape convention: `HWC`
- expected dtype: `float32`
- expected nodata policy: initialized with `NODATA`, sampled with `defaultValue=NODATA`, non-finite values normalized through `finite_or_nodata()`

## Remaining Unknowns

Phase 4G keeps unresolved details explicit.

Still requiring frozen notebook reference evidence:

- exact numeric shape for the captured reference run, although the notebook clearly uses `(OUT_SIZE, OUT_SIZE, bands)`;
- exact `NODATA` numeric value;
- final unit wording for the Landsat TOA B8 layer and the Sentinel-2 mean(B2,B3,B4,B8) layer;
- tolerance expectations for notebook/app comparison;
- exact selected Landsat image id and Sentinel-2 image id for the frozen reference run;
- exact cloud filter and date-window metadata that should be preserved in later manifests.

These remain unknown until the frozen notebook reference bundle is available.

## Current App Status

The current app does not write:

- `PAN_LS_Panchromatic_640.tif`
- `PAN_S2_Panchromatic_10m_640.tif`
- `PAN_LS_Panchromatic_640.npy`
- `PAN_S2_Panchromatic_10m_640.npy`
- `PAN_LAYERS_STACK_640.npy`

Current app optical outputs that are not equivalents:

- `NDVI.tif`
- `NDWI.tif`
- `NDMI.tif`
- `NBR.tif`
- `IRONOX.tif`
- `IRON_SWIR.tif`
- `BSI.tif`
- `s2_raw_cube.npy`
- `stacks/optical_support/s2_mask_support_valid.tif`
- `stacks/tensor_support/science_core_stack.npy`

Those outputs serve different purposes and must not be aliased as PAN outputs.

## Recovery Checklist

Phase 4G adds a machine-readable recovery checklist with:

- source status;
- implementation status;
- authoritative source flag;
- expected input outputs;
- expected band order;
- expected shape convention;
- expected dtype;
- expected units summary;
- expected nodata policy;
- required reference outputs;
- required metadata;
- blockers and next-action guidance.

`PAN_LAYERS_STACK_640.npy` is classified as `exact_source_found`, but still `requires_reference_output` before implementation.

## Verifier Contract

Phase 4G adds an NPY-only verifier for a future app-produced counterpart.

The verifier:

- accepts app output directory, notebook reference directory, run directory, and run id;
- checks presence of `PAN_LAYERS_STACK_640.npy` in app and reference trees;
- looks directly under the provided roots and under `NPY_STACKS/`;
- loads both arrays with NumPy;
- compares shape, dtype, NaN or invalid count, max absolute difference, mean absolute difference, compared value count, and tolerance pass/fail;
- records SHA256 for both files when present;
- writes:

```text
data/runs/<run_id>/manifests/pan_layers_stack_verification.json
```

The verifier writes only the JSON report. It does not create, copy, or modify `.npy` outputs.

## Verification Status Values

Output status values:

```text
passed
missing_app_output
missing_reference_output
shape_mismatch
dtype_mismatch
value_mismatch
comparison_unavailable
error
```

Overall status values:

```text
passed
failed
incomplete
comparison_unavailable
```

`notebook_value_parity_verified=true` is written only when comparison passes.

## Implementation Gate

Later implementation must remain source/reference-driven.

Implementation is blocked until:

- a frozen notebook `PAN_LAYERS_STACK_640.npy` reference is captured;
- the frozen per-band PAN NPY and TIFF references are captured;
- unit wording and NODATA value are confirmed from the reference bundle;
- tolerance expectations are locked by verification.

No alias or writer should be added before that gate passes.

## Confirmation

Phase 4G does not generate the stack, change optical or panchromatic math, change raster math, add Earth Engine calls, alter artifact serving, or integrate with the live pipeline.
