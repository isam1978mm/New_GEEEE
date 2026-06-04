# SAR ASC/DESC Support Stack Verification Contract

## Purpose

Phase 4E2 adds a private, filesystem-only verification harness for the notebook's frozen ascending/descending Sentinel-1 support stack outputs:

```text
S1_ASC_VV_Filtered_640.tif
S1_ASC_VH_Filtered_640.tif
S1_DESC_VV_Filtered_640.tif
S1_DESC_VH_Filtered_640.tif
S1_ASC_VV_Filtered_640.npy
S1_ASC_VH_Filtered_640.npy
S1_DESC_VV_Filtered_640.npy
S1_DESC_VH_Filtered_640.npy
```

The verifier checks app-produced counterpart files against frozen notebook reference files when both are provided. It records presence, hashes, metadata, shape, dtype, and numeric value comparison results in a run-local JSON report.

## Scope

Phase 4E2 is verification-only. It adds:

- `app/pipeline/parity/sar_asc_desc_verify.py`
- `tests/parity/test_sar_asc_desc_verify.py`
- this contract document

It does not implement ASC/DESC SAR generation, create aliases, call Earth Engine, integrate with the live pipeline, or write production rasters or NPY arrays.

## Non-Goals

Phase 4E2 does not change:

- SAR math;
- SAR RTC behavior;
- SAR filtering logic;
- selected image IDs;
- pair selection;
- GRID behavior;
- raster math;
- Sentinel-2, DEM, thermal, PCA, object extraction, or classifier logic;
- API routes, frontend, database models, migrations, or artifact serving policy;
- existing output names.

Final SAR RTC products such as `VV_dB.tif`, `VH_dB.tif`, `logRatio_dB.tif`, `incidence.tif`, or their existing notebook-compatible final aliases are not equivalent to the separate ASC/DESC support stacks and must not be treated as substitutes.

## Inputs

The verifier accepts:

- an app output directory;
- a frozen notebook reference directory;
- a run directory;
- a run id;
- optional absolute and relative numeric tolerances.

The expected files may be placed directly in each input directory. The verifier also recognizes the notebook-compatible subdirectories:

```text
GEOTIFF_RADAR_BANDS/
NPY_RADAR_BANDS/
```

This lookup is only for verification. It does not copy, alias, or generate files.

## Verification Behavior

For every required output, the verifier records:

- app/reference presence;
- app/reference SHA256 when files exist;
- hash match status when both files exist;
- runtime output presence;
- notebook-value parity status;
- private notebook-parity classification metadata.

For `.npy` files, NumPy is used to compare:

- shape;
- dtype;
- max absolute difference;
- mean absolute difference;
- count of compared values;
- count of NaN or nodata-like invalid values;
- tolerance pass/fail.

For `.tif` files, raster metadata and values are compared when `rasterio` is importable:

- width;
- height;
- CRS;
- transform;
- dtype;
- nodata;
- band count;
- numeric values.

If `rasterio` is not available, `.tif` outputs are reported as `comparison_unavailable`. Notebook-value parity remains false for those rasters.

## Report Output

The verifier writes:

```text
data/runs/<run_id>/manifests/sar_asc_desc_support_stack_verification.json
```

The path is resolved through the Phase 1 run-directory safety helper, so path traversal outside the run directory is rejected.

The report includes:

- `schema_version`
- `run_id`
- `created_at`
- `app_output_dir`
- `notebook_reference_dir`
- `outputs`
- `overall_status`
- `raster_value_comparison_available`
- `npy_outputs_passed`

Each output entry includes the required Phase 4E2 fields: file name, paths, existence flags, file type, hashes, metadata/value comparison flags, shape/dtype/metadata match fields, difference statistics, verification booleans, status, notes, classification, target mode, artifact class, HTTP serving flag, coordinate flag, and probability-only flag.

## Status Values

Output status values:

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

`notebook_value_parity_verified=true` is written only when comparison passes for that output. File existence is not parity proof.

## Classification And Exposure

All Phase 4E2 entries remain:

- family: `SAR/radar outputs`
- target mode: `notebook_parity`
- classification: `notebook-parity`
- coordinate-bearing: false
- probability-only required: false
- HTTP servable: false

No public/shared exposure decision is made in Phase 4E2.

## Reference Requirement

Frozen notebook references are required before notebook-value parity can pass. Later implementation must be source/reference-driven and must use the notebook ASC/DESC support-stack source locked in Phase 4E, not the app's final SAR RTC outputs as aliases.

## Confirmation

Phase 4E2 does not change SAR math, raster math, Earth Engine behavior, live pipeline behavior, API/frontend/database code, artifact serving policy, or existing output names. It does not generate rasters or NPY arrays.
