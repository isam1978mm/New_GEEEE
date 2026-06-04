# DEM Curv Laplacian Parity Verification Contract

## Purpose

Phase 4D2 adds a controlled verifier for comparing the app's existing Laplacian-style DEM curvature output against a frozen notebook reference output:

```text
app candidate: curvature.tif
notebook reference: curv_laplacian_640.tif
```

This phase is verification-only. It does not implement new DEM curvature formulas, create a `curv_laplacian_640.tif` writer, or alias `curvature.tif` into notebook parity output folders.

## Scope

The verifier accepts:

```text
app_output_dir
notebook_reference_dir
run_dir
run_id
```

The expected app file is:

```text
<app_output_dir>/curvature.tif
```

The expected notebook reference file is:

```text
<notebook_reference_dir>/curv_laplacian_640.tif
```

The verifier writes only:

```text
data/runs/<run_id>/manifests/dem_curv_laplacian_parity_verification.json
```

The report path is safely resolved under `run_dir`.

## Non-Goals

Phase 4D2 does not:

- change DEM formulas;
- change raster math;
- generate rasters;
- call Earth Engine;
- integrate into the live pipeline;
- create `DEM_GEO8_TIFS/curv_laplacian_640.tif`;
- copy or alias `curvature.tif`;
- change API, frontend, database, migrations, or artifact serving;
- mark notebook-value parity true from file existence alone.

## Candidate Equivalent Status

The app's `curvature.tif` is only a candidate equivalent for notebook `curv_laplacian_640.tif`. The current app formula is documented in Phase 4D as a Laplacian-style derivative:

```text
d2z_dxx + d2z_dyy
```

File existence is not parity proof. A frozen notebook reference output is required before notebook-value parity can pass.

## Report Fields

The JSON report includes:

```text
schema_version
run_id
created_at
app_output_dir
notebook_reference_dir
app_output_name
reference_output_name
app_path
reference_path
app_exists
reference_exists
metadata_compared
values_compared
width_match
height_match
crs_match
transform_match
dtype_match
nodata_match
band_count_match
max_abs_diff
mean_abs_diff
count_compared_pixels
count_nan_or_nodata_pixels
within_tolerance
runtime_output_verified
notebook_value_parity_verified
status
overall_status
classification
target_mode
artifact_class
http_servable
requires_coordinates
probability_only_required
raster_value_comparison_available
notes
```

Classification is:

```text
family: DEM/terrain outputs
target_mode: notebook_parity
classification: notebook-parity
artifact_class: LOCAL_SENSITIVE
requires_coordinates: false
probability_only_required: false
http_servable: false
```

## Comparison Behavior

When rasterio is available, the verifier compares:

```text
width
height
CRS
transform
dtype
nodata
band count
numeric values
```

Numeric comparison records:

```text
max_abs_diff
mean_abs_diff
count_compared_pixels
count_nan_or_nodata_pixels
within_tolerance
```

The verifier uses conservative default tolerance and allows caller-provided absolute and relative tolerance.

If rasterio is unavailable, the verifier reports `comparison_unavailable` and does not mark notebook-value parity true.

## Status Values

Per-report status values:

```text
passed
missing_app_output
missing_reference_output
metadata_mismatch
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

Interpretation:

- `passed`: app `curvature.tif` exists, reference `curv_laplacian_640.tif` exists, metadata matches, and values are within tolerance.
- `incomplete`: the app output or notebook reference output is missing.
- `failed`: both files exist but metadata or values do not match, or comparison errors occur.
- `comparison_unavailable`: both files exist but raster metadata/value comparison cannot run in the current environment.

`runtime_output_verified=true` means app `curvature.tif` existed at verification time. `notebook_value_parity_verified=true` is set only when the reference comparison passes.

## Next Step After Passing

Only after this verifier passes against a frozen notebook reference should a later phase consider adding a notebook-parity alias or writer for:

```text
DEM_GEO8_TIFS/curv_laplacian_640.tif
```

The later phase must preserve the existing `curvature.tif` behavior unless explicitly authorized to change it.
