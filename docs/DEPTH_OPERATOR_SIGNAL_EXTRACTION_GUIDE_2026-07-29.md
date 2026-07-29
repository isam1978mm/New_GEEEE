# Automatic reviewed signal extraction for local depth

Date: 2026-07-29

## What this adds

The operator no longer needs to type radar signal values manually.

The command reads the completed run's canonical:

```text
logRatio_dB.tif
```

That raster is the app's corrected neutral calculation:

```text
VV_dB - VH_dB
```

The command reduces the same raster over every reviewed anchor and candidate polygon, then creates the operator package config and candidate input automatically.

## What the operator still provides

The operator supplies one reviewed GeoJSON file containing:

- at least two measured anchor polygons;
- each anchor's measured minimum, best, and maximum depth;
- one or more candidate polygons when depth estimates are needed.

The operator does **not** type signal values.

## Built-in boundaries

The command:

- accepts only `logRatio_dB.tif` from the selected completed run;
- requires usable run quality;
- supports Polygon and MultiPolygon geometry;
- transforms the GeoJSON CRS to the raster CRS;
- erodes every polygon inward before reading pixels;
- requires a minimum valid-pixel count;
- rejects overlapping eroded interiors;
- uses the mean signal value;
- uses the full within-polygon standard deviation as candidate uncertainty;
- copies no geometry into generated output files;
- runs no classifier, PCA anomaly, target mask, or depth estimator.

Depth is calculated only later, after the operator reviews the extracted table and builds the private package.

## Input GeoJSON properties

Anchor:

```json
{
  "feature_id": "anchor-shallow",
  "role": "anchor",
  "depth_min_m": 0.40,
  "depth_best_m": 0.50,
  "depth_max_m": 0.60
}
```

Candidate:

```json
{
  "feature_id": "candidate-001",
  "role": "candidate"
}
```

Editable template:

```text
docs/examples/operator_depth_polygons.example.geojson
```

Replace every example geometry and value before use.

## Step 1 — Extract signals

```powershell
cd C:\Dev\New_GEE

python scripts\extract_operator_depth_signals.py `
  --run-dir C:\Dev\New_GEE\data\runs\<RUN_ID> `
  --polygons C:\PrivateDepth\reviewed-polygons.geojson `
  --output-dir C:\PrivateDepth\signal-extraction `
  --site-id my-local-site `
  --method-version my-local-method-v1 `
  --calibration-dataset-version my-local-data-v1
```

Defaults:

```text
input CRS = EPSG:4326
erosion = 2 pixels
minimum valid pixels = 20
```

For polygons already stored in the run raster's projected CRS:

```powershell
--input-crs EPSG:32613
```

The actual CRS must match the GeoJSON coordinates.

## Extraction outputs

```text
extracted_signals.csv
operator_depth_config.json
operator_depth_candidates.json
extraction_summary.json
```

Review `extracted_signals.csv` before continuing.

It includes:

- mean signal;
- signal standard deviation;
- median, minimum, and maximum;
- valid-pixel count;
- raw and eroded mask sizes;
- measured anchor depth ranges.

## Step 2 — Build the private package

```powershell
python scripts\build_operator_local_depth_package.py `
  --config C:\PrivateDepth\signal-extraction\operator_depth_config.json `
  --output-dir C:\PrivateDepth\my-local-package
```

The package builder verifies:

- at least two anchors;
- unique anchor IDs and signals;
- valid measured ranges;
- strict monotonic relationship between anchor signals and best depths;
- package checksums.

If the extracted anchors are not monotonic, the package is rejected. Do not reorder, delete, or modify anchors merely to force a result. Review the measurements, surfaces, polygons, and selected signal instead.

## Step 3 — Calculate candidate depth

```powershell
python scripts\run_operator_local_depth_for_existing_run.py `
  --run-dir C:\Dev\New_GEE\data\runs\<RUN_ID> `
  --package-dir C:\PrivateDepth\my-local-package `
  --candidate-input C:\PrivateDepth\signal-extraction\operator_depth_candidates.json
```

Private outputs:

```text
depth/depth_estimates.csv
depth/depth_summary.json
depth/depth_method_manifest.json
```

## How uncertainty is handled

The extractor uses the standard deviation of all valid pixels inside the eroded candidate polygon.

This is intentionally wider than a standard error. The interpolation stage evaluates:

```text
candidate signal - uncertainty
candidate signal
candidate signal + uncertainty
```

The final metre range covers the supported depths across that full signal interval.

If any part of the uncertainty interval extends beyond the measured anchor support, the app abstains instead of extrapolating.

## Current capability

```text
known-zone metre lookup = merged
operator local interpolation = merged
automatic reviewed signal extraction = implemented in PR #53 candidate branch
global depth model = not ready
unknown-AOI depth without local measured anchors = not supported
```

## Next product step

After this extractor is validated, the next UI slice can let the operator upload/draw anchor and candidate polygons and run these same private checks from the app rather than PowerShell.
