# Secret Layers Parity Verification Contract

## Purpose

Phase 4C adds a controlled verification harness for the six `AI_READY_640_Secret_*` notebook-parity outputs. It verifies app-produced secret-layer rasters against frozen notebook reference rasters when those reference files are provided.

This phase is verification-only. It does not change `secret_layers.py` formulas, raster math, Earth Engine behavior, pipeline orchestration, API routes, frontend files, database models, artifact serving, existing output names, or runtime pipeline behavior.

## Scope

The required secret-layer raster outputs are:

```text
AI_READY_640_Secret_Gold_Halo.tif
AI_READY_640_Secret_Silver_Oxide.tif
AI_READY_640_Secret_Tunnel_Ceiling.tif
AI_READY_640_Secret_Thermal_Inertia.tif
AI_READY_640_Secret_Chemical_Protector.tif
AI_READY_640_Secret_Hidden_Doors.tif
```

`app/pipeline/stages/secret_layers.py` remains classified as a notebook-parity semantic raster stage, not clean defensible core by default. Source writer existence is not parity proof.

## Verification Inputs

The verifier accepts:

```text
app_output_dir
notebook_reference_dir
run_dir
run_id
```

For current app output layout, callers should pass the app directory that contains the six files, typically:

```text
data/runs/<run_id>/AI_READY_640/
```

The app output directory and notebook reference directory are read-only inputs for the verifier. Reference notebook outputs are required before notebook-value parity can be marked true.

## Report Output

The verifier writes only:

```text
data/runs/<run_id>/manifests/secret_layers_parity_verification.json
```

The report path is resolved under the run directory. Path traversal is rejected. The verifier does not write, modify, generate, or copy `.tif`, `.tiff`, `.npy`, or other raster/tensor files.

## Report Fields

The JSON report includes:

```text
schema_version
run_id
created_at
app_output_dir
notebook_reference_dir
outputs
classification
target_mode
artifact_class
http_servable
raster_value_comparison_available
overall_status
```

Each output item includes:

```text
output_name
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
classification
target_mode
artifact_class
http_servable
requires_coordinates
probability_only_required
app_sha256
reference_sha256
hash_match
notes
```

Secret-layer verification entries target `notebook_parity`, use `LOCAL_SENSITIVE`, and do not default to public/shared exposure or HTTP serving.

## Comparison Behavior

When a raster-reading dependency is available, the verifier compares:

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

If raster comparison is unavailable because the dependency is not importable, the verifier reports `comparison_unavailable`. It records SHA256 hashes for presence tracking, but hash equality alone is not notebook-value parity proof and does not set `notebook_value_parity_verified=true`.

## Status Values

Per-output statuses:

```text
passed
missing_app_output
missing_reference_output
metadata_mismatch
value_mismatch
comparison_unavailable
error
```

Overall statuses:

```text
passed
failed
incomplete
comparison_unavailable
```

Interpretation:

- `passed`: all six app outputs exist, all six reference outputs exist, metadata matches, and values are within tolerance.
- `incomplete`: at least one app output or reference output is missing.
- `failed`: all required files are present, but metadata or values do not match, or comparison errors occur.
- `comparison_unavailable`: required files are present but raster metadata/value comparison cannot run in the current environment.

`runtime_output_verified=true` means the app output file was present at verification time. `notebook_value_parity_verified=true` is set only when the matching reference comparison passes.

## Non-Goals

Phase 4C does not:

- change secret-layer formulas;
- generate real secret-layer rasters;
- call Earth Engine;
- run or integrate with the live pipeline;
- alter artifact serving policy;
- expose secret-layer artifacts in public/shared mode;
- change API, frontend, database, migrations, classifier behavior, or candidate logic;
- mark secret layers as fully implemented from file existence alone.

## Next Step After Passing Verification

After a real run and frozen notebook reference comparison pass, a later phase may update inventory/status reporting to record runtime output presence and notebook-value parity evidence. That later phase should cite the verification report path, tolerance, reference bundle identity, and any accepted differences.
