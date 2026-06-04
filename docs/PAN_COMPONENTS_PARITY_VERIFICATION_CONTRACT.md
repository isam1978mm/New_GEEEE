# PAN Components Parity Verification Contract

## Purpose

Phase 4H adds a verification-only harness for the four notebook panchromatic component outputs:

```text
PAN_LS_Panchromatic_640.tif
PAN_S2_Panchromatic_10m_640.tif
PAN_LS_Panchromatic_640.npy
PAN_S2_Panchromatic_10m_640.npy
```

The goal is to compare future app-produced component files against frozen notebook references before any PAN stack implementation is attempted.

## Scope

Phase 4H adds:

- `app/pipeline/parity/pan_components_verify.py`
- `tests/parity/test_pan_components_verify.py`
- this contract document

The verifier writes only a JSON report under the run manifests directory. It does not generate rasters, generate `.npy` files, call Earth Engine, integrate with the live pipeline, or change artifact serving behavior.

## Non-Goals

Phase 4H does not:

- generate PAN component outputs;
- implement Landsat or Sentinel-2 panchromatic formulas;
- change optical or panchromatic math;
- alias existing optical outputs as PAN outputs;
- treat `s2_raw_cube.npy`, `science_core_stack.npy`, or other current optical outputs as notebook PAN equivalents;
- change API routes, frontend, database models, migrations, or artifact serving policy;
- add Earth Engine calls;
- commit raster or `.npy` files.

## Current App Status

Current app source inspection shows:

- `app/pipeline/stages/s2_indices.py` writes Sentinel-2 indices and `s2_raw_cube.npy`, not notebook PAN component outputs.
- `app/pipeline/stages/feature_stacks.py` writes generic optical/radar support stacks, not notebook PAN component outputs.
- the app does not currently write:
  - `PAN_LS_Panchromatic_640.tif`
  - `PAN_S2_Panchromatic_10m_640.tif`
  - `PAN_LS_Panchromatic_640.npy`
  - `PAN_S2_Panchromatic_10m_640.npy`

Existing optical outputs are therefore not automatically equivalent to notebook PAN component outputs. An explicit file with the correct notebook name is required before verification can pass for that output.

## Relationship To Phase 4G

Phase 4G locked the PAN stack contract for `PAN_LAYERS_STACK_640.npy`.

Phase 4H verifies the two per-layer component families that feed that stack:

- Landsat panchromatic component:
  - `PAN_LS_Panchromatic_640.tif`
  - `PAN_LS_Panchromatic_640.npy`
- Sentinel-2 panchromatic-equivalent component:
  - `PAN_S2_Panchromatic_10m_640.tif`
  - `PAN_S2_Panchromatic_10m_640.npy`

Later PAN stack implementation should remain source/reference-driven and should not proceed on assumption alone.

## Verifier Behavior

The Phase 4H verifier accepts:

- app output directory
- notebook reference directory
- run directory
- run id

For each of the four required outputs it:

1. checks app and reference presence;
2. records SHA256 hashes for files that exist;
3. for `.npy` files:
   - loads both arrays with NumPy;
   - compares shape, dtype, NaN or invalid count, max absolute difference, mean absolute difference, compared value count, and tolerance pass/fail;
4. for `.tif` files:
   - if `rasterio` is available, compares width, height, CRS, transform, dtype, nodata, band count, and numeric values;
   - if `rasterio` is not available, reports `comparison_unavailable`;
5. writes:

```text
data/runs/<run_id>/manifests/pan_components_parity_verification.json
```

The report path is resolved safely under the run directory. The verifier writes only the JSON report and does not write or modify `.tif` or `.npy` files.

## Lookup Rules

The verifier checks for exact notebook filenames:

- directly under the provided root; and
- under notebook-style optical subdirectories:
  - `OPT/PAN_TIFS_640/`
  - `OPT/PAN_NPY_640/`

This keeps the check compatible with future notebook-style parity layouts without treating unrelated current app files as equivalents.

## Output Classification

Each report entry preserves notebook-parity/private classification:

- family: `panchromatic/optical outputs`
- target mode: `notebook_parity`
- classification: `notebook-parity`
- coordinate-bearing: `false`
- probability-only required: `false`
- HTTP servable: `false`

Artifact class is recorded as:

- `LOCAL_SENSITIVE` for `.tif`
- `FILESYSTEM_ONLY` for `.npy`

No output defaults to `public_shared`.

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

`runtime_output_verified` and `notebook_value_parity_verified` remain separate.

- File existence alone is not parity proof.
- `runtime_output_verified=true` means the expected app file exists and was examined.
- `notebook_value_parity_verified=true` is written only when comparison succeeds for that output.

## Report Fields

The JSON report includes:

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

Use the report conservatively:

- `missing_app_output`: the app has not produced the required notebook-named file;
- `missing_reference_output`: frozen notebook evidence is missing, so notebook-value parity cannot pass;
- `comparison_unavailable`: typically means `rasterio` is not importable for TIFF comparison;
- `metadata_mismatch`, `shape_mismatch`, `dtype_mismatch`, or `value_mismatch`: the future app output is not yet parity-equivalent to the notebook reference.

Passing verification does not implement the outputs. It only establishes that a future app-produced counterpart matches the frozen notebook reference within the chosen tolerance.

## Next Step

After Phase 4H passes with real reference files, the next implementation slice can decide whether notebook-compatible PAN component writers are safe to add. That later work must remain source/reference-driven.

## Confirmation

Phase 4H is verification-only. It does not change optical or panchromatic math, does not generate rasters or `.npy` files, does not call Earth Engine, and does not integrate with the live pipeline.
