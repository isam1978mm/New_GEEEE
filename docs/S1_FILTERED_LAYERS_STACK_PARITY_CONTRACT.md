# S1 Filtered Layers Stack Parity Contract

## Purpose

Phase 4F locks source recovery and verification requirements for the notebook output:

```text
S1_FILTERED_LAYERS_STACK_640.npy
```

This output follows the eight per-band ASC/DESC Sentinel-1 support outputs but is handled separately because it is a tensor contract, not just a set of per-band files.

Phase 4F is recovery and verification-contract only. It does not generate the stack, implement stack production, change SAR math, change SAR RTC behavior, call Earth Engine, or integrate with the live pipeline.

## Scope

Phase 4F adds:

- `app/pipeline/parity/s1_filtered_stack_recovery.py`
- `app/pipeline/parity/s1_filtered_stack_verify.py`
- `tests/parity/test_s1_filtered_stack_recovery.py`
- `tests/parity/test_s1_filtered_stack_verify.py`
- this contract document

The work is limited to:

- source recovery for the notebook stack meaning;
- a machine-readable checklist for later implementation;
- an NPY verification harness for a future app-produced counterpart;
- JSON report writing under the run manifests directory.

## Non-Goals

Phase 4F does not:

- generate `S1_FILTERED_LAYERS_STACK_640.npy`;
- implement stack generation in the app;
- alias final SAR RTC outputs as this stack;
- change SAR formulas;
- change SAR RTC math;
- change SAR filtering logic;
- change selected image IDs;
- change pair selection;
- change GRID behavior;
- change API, frontend, database models, migrations, or artifact serving policy;
- add Earth Engine calls;
- commit raster or `.npy` outputs.

Final SAR RTC products and their current aliases remain non-equivalent to this stack.

## Authoritative Notebook Source

`notebooks/new.ipynb` contains authoritative source for `S1_FILTERED_LAYERS_STACK_640.npy` in the Sentinel-1 filtered-layer export block around lines `26182-26309`.

The notebook source shows:

- `speckle_filter()` uses `image.focal_mean(radius=1.5, kernelType='circle', units='pixels')`;
- the source collection is `ee.ImageCollection('COPERNICUS/S1_GRD')`;
- the date range is `2022-01-01` to `2026-03-01`;
- the notebook selects the newest `ASCENDING` image and the newest `DESCENDING` image separately;
- the notebook processes `VV` and `VH` for each pass;
- the four processed bands are appended in this exact order:
  - `S1_ASC_VV_Filtered`
  - `S1_ASC_VH_Filtered`
  - `S1_DESC_VV_Filtered`
  - `S1_DESC_VH_Filtered`
- the notebook allocates `cube = np.full((OUT_SIZE, OUT_SIZE, len(band_names_list)), NODATA, dtype=np.float32)`;
- the notebook fills `cube[:, :, bi]` in `band_names_list` order;
- the notebook writes `np.save(stack_path, cube.astype(np.float32))`.

This is evidence-backed source for:

- expected stack band order;
- expected HWC shape convention;
- expected float32 dtype;
- NODATA-filled allocation behavior.

## Locked Expectations

Evidence-backed expectations from the notebook source:

- output name: `S1_FILTERED_LAYERS_STACK_640.npy`
- family: `SAR/radar outputs`
- target mode: `notebook_parity`
- classification: `notebook-parity`
- artifact class: `FILESYSTEM_ONLY`
- HTTP servable: `false`
- coordinate-bearing: `false`
- probability-only required: `false`
- expected input outputs:
  - `S1_ASC_VV_Filtered_640.npy`
  - `S1_ASC_VH_Filtered_640.npy`
  - `S1_DESC_VV_Filtered_640.npy`
  - `S1_DESC_VH_Filtered_640.npy`
- expected band order:
  - `S1_ASC_VV_Filtered`
  - `S1_ASC_VH_Filtered`
  - `S1_DESC_VV_Filtered`
  - `S1_DESC_VH_Filtered`
- expected shape convention: `HWC`
- expected dtype: `float32`
- expected nodata policy: initialized with `NODATA`, sampled with `defaultValue=NODATA`, unresolved cells remain `NODATA`

## Remaining Unknowns

Phase 4F does not overstate what the notebook source proves.

Still requiring frozen notebook reference evidence:

- exact numeric shape for the captured reference run, although the notebook clearly uses `(OUT_SIZE, OUT_SIZE, bands)`;
- exact `NODATA` numeric value;
- whether the exported VV/VH values should be interpreted as dB or linear in downstream contract language;
- final unit wording for the stack manifest;
- tolerance expectations for notebook/app comparison;
- exact selected ASC/DESC image ids and acquisition timestamps for the frozen reference run.

These unknowns must remain explicit until a frozen notebook reference is available.

## Current App Status

The current app does not write `S1_FILTERED_LAYERS_STACK_640.npy`.

The following current app outputs are not equivalent:

- `VV_dB.tif`
- `VH_dB.tif`
- `logRatio_dB.tif`
- `incidence.tif`
- `GEOTIFF_RADAR_BANDS/RADAR_*_640_app.tif`
- `NPY_RADAR_BANDS/RADAR_*_640_app.npy`
- `stacks/tensor_support/radar_db_support_stack.npy`
- `stacks/tensor_support/radar_linear_support_stack.npy`
- `NPY_STACKS/RADAR_STACK_HWC_640_app.npy`

Those outputs are final RTC or app-defined support products. The notebook stack is a separate newest-pass filtered support export.

## Recovery Checklist

Phase 4F adds a machine-readable recovery checklist with:

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

The stack is classified as `exact_source_found`, but still `requires_reference_output` before implementation.

## Verifier Contract

Phase 4F adds an NPY-only verifier for a future app-produced counterpart.

The verifier:

- accepts app output directory, notebook reference directory, run directory, and run id;
- checks presence of `S1_FILTERED_LAYERS_STACK_640.npy` in app and reference trees;
- looks directly under the provided roots and under `NPY_STACKS/`;
- loads both arrays with NumPy;
- compares shape, dtype, NaN/invalid count, max absolute difference, mean absolute difference, compared value count, and tolerance pass/fail;
- records SHA256 for both files when present;
- writes:

```text
data/runs/<run_id>/manifests/s1_filtered_layers_stack_verification.json
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

- a frozen notebook `S1_FILTERED_LAYERS_STACK_640.npy` reference is captured;
- the four frozen per-band `S1_ASC_*` and `S1_DESC_*` NPY references are captured;
- unit wording and NODATA value are confirmed from the reference bundle;
- tolerance expectations are locked by verification.

No alias or writer should be added before that gate passes.

## Confirmation

Phase 4F does not generate the stack, change SAR math, change raster math, add Earth Engine calls, alter artifact serving, or integrate with the live pipeline.
