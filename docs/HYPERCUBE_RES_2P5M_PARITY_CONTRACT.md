# Hypercube Res 2P5M Parity Contract

## Purpose

Phase 4I locks source recovery and verification requirements for the notebook resampled hypercube outputs:

```text
FINAL_TESLA_V7_2_HYPERCUBE_RES_2p5M.tif
FINAL_TESLA_V7_2_HYPERCUBE_RES_2p5M.npy
```

The goal is to define what the 2.5 m hypercube means, what source evidence exists, and how future app-produced counterparts must be verified against frozen notebook references.

## Scope

Phase 4I adds:

- `app/pipeline/parity/hypercube_res25_recovery.py`
- `app/pipeline/parity/hypercube_res25_verify.py`
- `tests/parity/test_hypercube_res25_recovery.py`
- `tests/parity/test_hypercube_res25_verify.py`
- this contract document

This phase is recovery and verification-contract only. It does not generate the 2.5 m hypercube, implement resampling, change hypercube or feature-stack formulas, call Earth Engine, or integrate with the live pipeline.

## Non-Goals

Phase 4I does not:

- generate `FINAL_TESLA_V7_2_HYPERCUBE_RES_2p5M.tif`;
- generate `FINAL_TESLA_V7_2_HYPERCUBE_RES_2p5M.npy`;
- change hypercube assembly math;
- change feature-stack logic;
- change PCA logic;
- change raster math;
- alias current hypercube outputs as the 2.5 m resampled outputs;
- change API routes, frontend, database models, migrations, or artifact serving policy;
- add Earth Engine calls;
- commit `.tif` or `.npy` files.

## Current App Status

Current source inspection shows:

- `app/pipeline/stages/hypercube.py` writes:
  - `hypercube.tif`
  - `hypercube.npy`
  - `NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE.tif`
  - `NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE.npy`
  - `NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE_PATCHED_14B.tif`
- `app/pipeline/stages/feature_stacks.py` writes support stacks such as:
  - `science_core_stack.*`
  - `radar_linear_support_stack.*`
  - `radar_db_support_stack.*`
  - `ai_ready_support_stack.*`
  - `NPY_STACKS/RADAR_STACK_HWC_640_app.npy`

The app does not currently write:

- `FINAL_TESLA_V7_2_HYPERCUBE_RES_2p5M.tif`
- `FINAL_TESLA_V7_2_HYPERCUBE_RES_2p5M.npy`

Existing app hypercube outputs are not automatically equivalent to the 2.5 m resampled outputs. An explicit file with the correct notebook name is required before parity verification can pass.

## Authoritative Notebook Source

`notebooks/new.ipynb` contains an explicit resampling cell around lines `26996-27078`.

That cell shows:

- source input:
  - `STACK_DIR/FINAL_TESLA_V7_2_HYPERCUBE.tif`
- target resolution:
  - `OUTPUT_RES_M = 2.5`
- source loading:
  - `src.read().astype(np.float32)`
  - `band_names = list(src.descriptions)` when available
- zoom factor:
  - `zoom_factor = GRID['SCALE'] / OUTPUT_RES_M`
- resampling implementation:
  - `scipy.ndimage.zoom(..., order=3)`
  - comment labels this as super-resolution upsampling
- output transform update:
  - `new_transform = original_transform * Affine.scale(1/zoom_factor, 1/zoom_factor)`
- output filenames:
  - `FINAL_TESLA_V7_2_HYPERCUBE_RES_2p5M.tif`
  - `FINAL_TESLA_V7_2_HYPERCUBE_RES_2p5M.npy`
- GeoTIFF write behavior:
  - updates `height`, `width`, `transform`, and `dtype`
  - writes the upsampled band-first cube band by band
  - preserves band descriptions when available
- NPY write behavior:
  - `np.save(OUTPUT_PATH_NPY, upsampled_hypercube_data)`

This is authoritative source evidence for the 2.5 m output names, source input, target pixel size, CHW NPY layout, float32 dtype, and cubic interpolation behavior.

## Locked Expectations

Evidence-backed expectations from the notebook source:

- family: `hypercube/tensor outputs`
- target mode: `notebook_parity`
- classification: `notebook-parity`
- coordinate-bearing: `false`
- probability-only required: `false`
- HTTP servable: `false`
- expected source input:
  - `FINAL_TESLA_V7_2_HYPERCUBE.tif`
- expected band count:
  - `9`
- expected band order:
  1. `AI_READY_640_Secret_Gold_Halo`
  2. `AI_READY_640_Secret_Silver_Oxide`
  3. `AI_READY_640_Secret_Tunnel_Ceiling`
  4. `AI_READY_640_Secret_Thermal_Inertia`
  5. `AI_READY_640_Secret_Chemical_Protector`
  6. `AI_READY_640_Secret_Hidden_Doors`
  7. `REPORT_640_FINAL_Zero_Point_Targets`
  8. `REPORT_640_Mass_Report`
  9. `REPORT_640_Pottery_Report`
- expected NPY shape convention:
  - `CHW`
- expected GeoTIFF band layout:
  - multi-band GeoTIFF in preserved source band order
- expected pixel size:
  - `2.5 m`
- expected resampling method:
  - `cubic`
- expected dtype:
  - `float32`

## Remaining Unknowns

Phase 4I keeps unresolved details explicit until frozen notebook references are available:

- exact frozen-reference width and height for the captured run;
- exact frozen-reference transform values after resampling;
- exact nodata sentinel preserved in the frozen reference GeoTIFF;
- whether any NaN values remain in the frozen reference NPY;
- final unit wording for the resampled outputs;
- comparison tolerance expectations for TIFF and NPY verification.

These are reference-dependent details, not source-free assumptions.

## Source Relationship

The resampled 2.5 m outputs are derived from the notebook `FINAL_TESLA_V7_2_HYPERCUBE.tif`.

They are not equivalent to:

- `hypercube.tif`
- `hypercube.npy`
- `NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE.npy`
- `NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE_PATCHED_14B.tif`
- `science_core_stack.*`
- `ai_ready_support_stack.*`

Those files may be useful source or context, but they are not parity substitutes for the 2.5 m resampled outputs.

## Recovery Checklist

Phase 4I adds a machine-readable checklist for both outputs with:

- source status;
- authoritative source flag;
- expected source input;
- expected band order and band count;
- expected shape convention;
- expected GeoTIFF band layout;
- expected pixel size and resampling method;
- expected dtype;
- expected nodata policy summary;
- required reference outputs and metadata;
- implementation blocker and next-action guidance.

Both outputs are tracked as `exact_source_found`, but still `requires_reference_output` before any later implementation slice can claim parity.

## Verifier Contract

Phase 4I adds a verifier for both resampled hypercube outputs.

The verifier accepts:

- app output directory
- notebook reference directory
- run directory
- run id

It checks both:

- `FINAL_TESLA_V7_2_HYPERCUBE_RES_2p5M.tif`
- `FINAL_TESLA_V7_2_HYPERCUBE_RES_2p5M.npy`

Lookup rules:

- directly under the provided root
- under `NPY_STACKS/`

For `.tif` files:

- if `rasterio` is available, compare:
  - width
  - height
  - CRS
  - transform
  - pixel size
  - dtype
  - nodata
  - band count
  - numeric values
- if `rasterio` is unavailable, report `comparison_unavailable`

For `.npy` files:

- load arrays with NumPy
- compare:
  - shape
  - dtype
  - NaN or invalid count
  - max absolute difference
  - mean absolute difference
  - compared value count
  - within tolerance

The verifier records SHA256 hashes for files that exist and writes:

```text
data/runs/<run_id>/manifests/hypercube_res_2p5m_parity_verification.json
```

It writes only the JSON report and does not write or modify `.tif` or `.npy` files.

## Status Values

Per-output status values:

```text
passed
missing_app_output
missing_reference_output
metadata_mismatch
value_mismatch
shape_mismatch
dtype_mismatch
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

`runtime_output_verified` and `notebook_value_parity_verified` remain separate:

- file existence is not parity proof;
- `runtime_output_verified=true` only means the expected app file exists and was examined;
- `notebook_value_parity_verified=true` is written only when comparison passes for that output.

## Report Fields

The JSON verification report includes:

```text
schema_version
run_id
created_at
app_output_dir
notebook_reference_dir
outputs
output_name
app_path
reference_path
app_exists
reference_exists
file_type
app_sha256
reference_sha256
hash_match
metadata_compared
values_compared
width_match
height_match
crs_match
transform_match
pixel_size_match
dtype_match
nodata_match
band_count_match
shape_match
max_abs_diff
mean_abs_diff
count_compared_values
count_nan_or_nodata_values
within_tolerance
runtime_output_verified
notebook_value_parity_verified
status
notes
classification
target_mode
artifact_class
http_servable
requires_coordinates
probability_only_required
overall_status
raster_value_comparison_available
```

## Interpretation

Use the verification report conservatively:

- `missing_app_output`: the app has not produced the required notebook-named file;
- `missing_reference_output`: frozen notebook evidence is missing, so notebook-value parity cannot pass;
- `comparison_unavailable`: typically means `rasterio` is not importable for TIFF comparison;
- `metadata_mismatch`, `shape_mismatch`, `dtype_mismatch`, or `value_mismatch`: a future app output is not yet parity-equivalent to the frozen notebook reference.

Passing verification does not implement the outputs. It only proves that a future app-produced counterpart matches the frozen notebook reference within the chosen tolerance.

## Implementation Gate

Later implementation can proceed only after:

- frozen notebook references for both 2.5 m outputs are captured;
- exact frozen-reference metadata is confirmed;
- tolerance expectations are locked through verification;
- a later implementation slice explicitly chooses whether to resample from the notebook-compatible `FINAL_TESLA_V7_2_HYPERCUBE.tif` path or another source-equivalent internal writer path.

Implementation must remain source/reference-driven.

## Confirmation

Phase 4I does not generate the 2.5 m hypercube, does not change hypercube math, does not change raster math, does not call Earth Engine, and does not integrate with the live pipeline.
