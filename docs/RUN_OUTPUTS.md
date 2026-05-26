# Run Outputs

This guide explains what an operator gets after a run. It is operator-facing and separates what the UI shows, what is stored locally, what can be downloaded, and what remains internal.

It does not expand the current parity scope. It does not claim fresh-ROI notebook parity.

## What The UI Shows After A Run

The UI shows a public-safe run view:

- run ID
- run status
- current stage
- stage checklist
- status history
- visible public-safe artifacts
- guarded download links

The UI does not show target coordinates, raw spatial metadata, local machine locations, internal validation controls, raw processing errors, or secrets.

Operator reminder:

- use the actual running local port, currently `8007`
- after changing `.env` or code, restart the FastAPI server
- after a restart, hard reload the browser with `Ctrl+F5`
- confirm `/readyz` is healthy before creating a run

## What Exists Locally After A Run

Each run writes its working files under:

`data/runs/<run_id>/`

A completed or partially completed run can contain:

- grid manifest
- stage manifests
- GeoTIFF outputs
- NPY outputs
- CSV and JSON summaries
- QA and internal support files

The local run folder is the complete operator workspace for inspection and debugging. It can contain sensitive internal files that are intentionally not listed or downloaded through the UI.

## What Is Downloadable In The UI

The UI downloads only public-safe artifacts returned by the run detail API.

Downloads use the guarded route:

`/runs/{run_id}/artifacts/{artifact_name}`

The API decides whether an artifact can be served. The UI does not construct direct file links and does not show artifacts that the API omits.

If a run fails, zero downloadable artifacts is expected. Failed runs do not produce public-safe output downloads.

## What Is Local/Internal Only

The following stay local/internal unless a separate redacted public artifact is explicitly produced:

- `FILESYSTEM_ONLY` artifacts
- raw raster and array products unless explicitly public-safe
- QA, parity, and support files
- raw local run internals
- exact spatial metadata, local machine locations, raw processing exceptions, and secrets

Experimental classifier outputs are local-only. They are not part of the default web run surface and are not served by the UI.

## Current Implemented Output Families

This section lists output families implemented by the current app pipeline. Artifact visibility still depends on artifact class and the public API filter.

### GRID And Run Setup

Implemented local outputs:

- `grid_manifest`
- `grid_guard_summary`
- stage manifest for GRID setup

Operator meaning:

GRID defines the common processing frame for the run. It is the internal alignment contract that all raster and array stages must follow.

### DEM

Implemented local outputs:

- `dem_tif`
- `dem_npy`
- `dem_audit_summary`
- stage manifest for DEM

Operator meaning:

DEM is the terrain elevation base layer used by terrain derivatives and radar terrain correction support.

### Zero Shift

Implemented local outputs:

- `zero_shift_summary`
- `drift_audit`
- stage manifest for zero-shift checking

Operator meaning:

Zero shift checks whether outputs remain aligned to the run grid before downstream products are trusted.

### SAR

Implemented local outputs:

- `VV_dB`
- `VH_dB`
- `logRatio_dB`
- `incidence`
- SAR NPY band exports
- SAR pair diagnostics
- SAR summary CSV
- SAR nodata audit CSV
- SAR alignment summary
- stage manifest for SAR RTC

Operator meaning:

SAR products show radar backscatter and incidence information after the app-side RTC workflow. They support all-weather surface texture and structure analysis.

### Sentinel-2 Indices

Implemented local outputs:

- `NDVI`
- `NDWI`
- `NDMI`
- `NBR`
- `IRONOX`
- `IRON_SWIR`
- `BSI`
- `s2_indices_summary`
- stage manifest for Sentinel-2 indices

Operator meaning:

Sentinel-2 indices summarize vegetation, moisture, burn or bare-soil signals, and iron-related spectral responses.

### DEM Derivatives

Implemented local outputs:

- `slope`
- `aspect`
- `curvature`
- `TPI`
- `TRI`
- `roughness`
- `TWI`
- `dem_derivatives_summary`
- stage manifest for DEM derivatives

Operator meaning:

DEM derivatives describe terrain shape, steepness, roughness, relative position, and wetness-style terrain tendency. Some derivative outputs are app-only in the current notebook reference set, even though they are implemented by the app.

### Thermal

Implemented local outputs:

- `lst`
- `thermal_summary`
- stage manifest for thermal

Operator meaning:

Thermal output represents land-surface-temperature style signal aligned to the run grid.

### Feature Stacks

Implemented local outputs:

- `science_core_stack_tif`
- `science_core_stack_npy`
- `radar_linear_support_stack_tif`
- `radar_linear_support_stack_npy`
- `radar_db_support_stack_tif`
- `radar_db_support_stack_npy`
- `ai_ready_support_stack_tif`
- `ai_ready_support_stack_npy`
- `s2_mask_support_valid`
- `band_stats`
- `stack_presence_summary`
- `tensor_audit_summary`
- `geometry_consistency_summary`
- stage manifest for feature stacks

Operator meaning:

Feature stacks combine aligned raster layers into multi-band products for later analysis, QA, or downstream local workflows.

### Focus Mask

Implemented local outputs:

- `focus_zone_17m_tif`
- `focus_zone_17m_npy`
- `focus_zone_ai_ready_window`
- `focus_zone_summary`
- `focus_band_summary`
- stage manifest for focus mask

Operator meaning:

Focus mask products define and summarize a local analysis window around the run target. They remain internal unless a public-safe summary is produced.

### Location Exports

Implemented local outputs:

- `location_geojson`
- `location_kmz`
- stage manifest for location exports

Operator meaning:

Location exports are local operator support products. They are not public UI artifacts because they can carry exact target context.

### Field Ops Exports

Implemented local outputs:

- `field_ops_navigation_kmz`
- `field_ops_report`
- `field_ops_brief`
- stage manifest for field ops exports

Operator meaning:

Field ops outputs are local planning aids. They are treated as internal and are not part of the public-safe UI artifact list.

### GPS Comparison

Implemented local outputs:

- `gps_point_comparison_json`
- `gps_point_comparison_csv`
- stage manifest for GPS comparison

Operator meaning:

GPS comparison outputs support local operator checks against the run target and are not served publicly.

### Hypercube

Implemented local outputs:

- `hypercube_tif`
- `hypercube_npy`
- `hypercube_band_order`
- `hypercube_band_stats`
- `hypercube_norm_params`
- `hypercube_audit`
- stage manifest for hypercube

Operator meaning:

The hypercube combines multiple aligned bands into one analysis product for anomaly detection and downstream processing.

### PCA Anomaly

Implemented local outputs:

- `pca_anomaly_tif`
- `pca_eigenvalues`
- `parity_qa_summary`
- stage manifest for PCA anomaly

Operator meaning:

PCA anomaly output highlights pixels that differ from the dominant multi-band background patterns. It is a screening aid, not ground truth.

### Object Extraction

Implemented outputs:

- `objects_index`
- `clusters_summary`
- `object_mask`
- object patch NPY files
- stage manifest for object extraction

Operator meaning:

Object extraction groups anomaly-like pixels into candidate objects and public-safe summary tables. Per-object arrays remain local/internal.

### Alignment QA

Implemented outputs:

- `alignment_qa`
- `alignment_audit`
- `alignment_mask_selection`
- `alignment_summary_redacted`
- stage manifest for alignment QA

Operator meaning:

Alignment QA checks whether key raster outputs remain consistent with the run grid and gives the operator a safe summary of alignment health.

## Visible Public-Safe Artifact Families Today

The UI can only show artifacts returned by the public run detail API. In current tests and implementation, public-safe examples include:

- `objects_index`
- `clusters_summary`
- `alignment_qa`
- `alignment_audit`
- `alignment_mask_selection`

Local-sensitive and filesystem-only outputs may exist locally but are not shown in the UI artifact list.

## Future Or Contracted Output Families

The broader project contract includes additional output families or fuller forms of existing families. These are planned or contracted separately from the current public UI surface:

- richer redacted QA summaries
- additional public-safe previews if separately reviewed
- expanded field-operations packaging
- optional experimental classifier outputs, still CLI-only and `FILESYSTEM_ONLY`
- fuller notebook-tail products that remain outside accepted parity scope unless explicitly promoted
- future frozen-reference-set additions for outputs that are app-only today

These future or contracted families must not be treated as current public UI outputs unless the implementation, artifact class, redaction review, and tests are updated.

## Operator Reading Rule

If an output appears in the UI, it is a public-safe artifact selected by the API. If it exists only under `data/runs/<run_id>/`, it is local operator material and may contain internal information. Use the guarded UI download links for public-safe exports and use the local run folder only for trusted local inspection.

## Troubleshooting Readiness And DEM Failures

Use this check sequence before retrying a failed run:

1. Confirm the server was restarted after any `.env` or code change.
2. Hard reload the browser with `Ctrl+F5`.
3. Check `/readyz` on the active local port before queuing a run.
4. If `/readyz` reports `ee_not_ready`, inspect Earth Engine service-account configuration.
5. Verify `EE_SERVICE_ACCOUNT_KEY_PATH` points to an existing service-account JSON file.
6. Verify `.env` settings are separated cleanly, one setting per line.

If Earth Engine is not ready, the `DEM` stage can fail immediately and the run will not produce downloadable outputs.
