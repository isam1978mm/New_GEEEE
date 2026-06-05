# Implementation Phase A Map ROI Preview

Phase A adds a preview-only operator workflow for selecting or entering a point and reviewing the local ROI/GRID metadata before queueing a backend run.

## Implemented Behavior

- The frontend run workflow includes manual latitude/longitude entry and a local click picker that updates the same coordinate fields.
- The frontend can request a preview from `POST /roi/preview` before queueing a run.
- The backend validates numeric latitude and longitude ranges.
- The backend computes deterministic local GRID preview metadata from the existing grid helper.
- The response uses public-response-safe field names and includes no artifact, download, path, hash, or private filesystem references.

## Preview Fields

The preview response includes:

- selected point values as north/south and east/west degrees
- ROI window values in projected meters
- reference system label and numeric code
- UTM zone and hemisphere
- grid width and height in cells
- cell size in meters
- affine coefficients from the existing grid helper
- warnings that the preview is local metadata only

## Safety Boundary

Phase A does not:

- call Earth Engine
- call `ee.Authenticate()`
- start a backend run
- call the run orchestrator
- generate rasters
- generate NPY arrays
- generate KMZ, KML, GeoJSON, HTML map, image, CSV, coordinate, classifier, or model artifacts
- expose private coordinate artifacts as downloads
- change artifact-serving policy
- change SAR, optical, DEM, PCA, GRID, raster, classifier, or model math

The preview endpoint is for operator pre-run review only. Phase B will handle controlled backend Earth Engine run flow later.
