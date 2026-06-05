# Implementation Phase B Controlled EE Run Flow

Phase B adds a controlled backend planning surface for Earth Engine acquisition requests.

## Implemented Behavior

- `POST /earth-engine/plan` validates a controlled Earth Engine planning request.
- The request accepts a point, acquisition dates, optional cloud threshold, SAR orbit, SAR polarization, and a dry-run flag.
- The backend returns safe planning metadata, auth readiness, planned provider families, query filters, and the Phase A ROI/GRID preview metadata.
- The frontend run workflow can request and display an Earth Engine backend planning result before queueing a run.

## Safety Boundary

Phase B does not:

- call Earth Engine during default dry-run planning
- use Colab
- use Google Drive
- use interactive `ee.Authenticate()`
- start the run orchestrator
- run the live backend pipeline
- change raster, SAR, optical, DEM, PCA, GRID, classifier, or model math
- generate rasters
- generate NPY arrays
- generate KMZ, KML, GeoJSON, HTML map, image, CSV, coordinate, classifier, or model artifacts
- expose private coordinate, map, classifier, or model artifacts
- change artifact-serving policy

## Auth Readiness

The planning service checks only whether backend auth inputs are present and whether real execution is enabled by configuration. It does not return service-account emails, key paths, secret values, hashes, or local filesystem paths.

If backend auth is missing, the plan reports `auth_not_configured` safely. If backend auth is present but real execution is not enabled, the plan reports `real_execution_disabled`. Default app behavior remains dry-run planning.

## Dry-Run Planning

Default planning is dry-run only. It validates parameters and computes local ROI/GRID metadata without importing Earth Engine, making network calls, creating files, or starting a backend run.

Phase C will handle defensible raster/feature writers later.
