# Implementation Phase D Private Map Artifact Writers

Phase D adds one small private map-artifact writer slice.

## Selected Writer Family

Selected family:

- private GeoJSON FeatureCollection writer

Implemented module:

`app/pipeline/parity/private_map_artifact_writers.py`

The writer accepts already-computed private GeoJSON features and writes a private FeatureCollection under a caller-provided run directory.

## Output Type

The selected output is:

- GeoJSON FeatureCollection

It is private and filesystem-only. The private file may contain coordinate geometry, but only inside the run directory. The public/redacted summary excludes coordinates, geometry, local paths, hashes, download references, and frontend links.

The writer metadata defaults to:

- `artifact_class=FILESYSTEM_ONLY`
- `private_classification=PRIVATE_COORDINATE_ARTIFACT`
- `filesystem_only=true`
- `http_servable=false`
- `frontend_visible=false`
- `downloadable_via_api=false`

## Safety Boundary

Phase D does not:

- add public downloads
- add frontend previews
- add map tiles
- add public exact-coordinate overlays
- change artifact-serving policy
- expose coordinate artifacts through API or frontend
- call Earth Engine
- use Colab
- use Google Drive
- start backend runs
- generate rasters
- generate NPY arrays
- change raster, SAR, optical, DEM, PCA, GRID, classifier, or model math
- add classifier, model, training, or inference behavior
- port the full Tesla inference flow
- implement Phase E, F, G, H, I, or J behavior

## Path And Redaction Policy

The writer resolves output paths under the provided run directory and rejects path traversal. It writes only a private `.geojson` file under `private_map_artifacts/geojson/` by default.

The private internal result includes the local path for internal use. The redacted summary is safe for logs/tests and includes only artifact type, feature count, private classification, artifact class, and serving flags.

## Roadmap Boundary

Phase G will handle public exact-coordinate overlay access-control design later.

Phase E will handle frozen-reference verifier work later.
