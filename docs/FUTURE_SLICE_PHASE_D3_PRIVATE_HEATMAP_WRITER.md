# Future Slice 05 / Phase D3 Private Heatmap Writer

Phase D3 adds a private heatmap writer only.

## Selected Writer Family

Selected family:

- private heatmap JSON writer

Implemented module:

`app/pipeline/parity/private_map_artifact_writers.py`

The writer accepts already-computed private point summaries and writes one private heatmap JSON artifact under a caller-provided run directory. It does not compute scientific outputs, infer labels, or create public overlays.

## Heatmap JSON Behavior

The default output path is under:

`run_dir/private_map_artifacts/heatmap/`

The private JSON includes:

- schema version
- artifact type
- private artifact classification
- filesystem-only serving flags
- point count
- private point entries
- optional weight, score, probability, uncertainty, rank, or neutral class label values when supplied

Exact coordinates may exist only inside the private heatmap JSON file under the run directory.

## Redacted Summary Boundary

The private internal result may include the local path for internal tooling.

The redacted/public-safe summary must not include:

- exact coordinates
- raw geometry
- local filesystem paths
- private hashes
- heatmap file download URLs
- inline private point content

The artifact metadata defaults to:

- `artifact_class=FILESYSTEM_ONLY`
- `private_classification=PRIVATE_COORDINATE_ARTIFACT`
- `filesystem_only=true`
- `http_servable=false`
- `frontend_visible=false`
- `downloadable_via_api=false`

## Safety Boundary

Phase D3 does not:

- add public API exposure
- add frontend exposure
- add artifact-serving exposure
- add public overlays
- add operator overlay UI
- call Earth Engine
- use Colab
- use Google Drive
- start backend runs
- generate rasters
- generate NPY arrays
- create HTML map output
- create image output
- change raster or GRID math
- change classifier or model logic
- add training or inference behavior
- port the full Tesla flow

## Later Work

Phase E4 remains the later comparator slice for Phase D private map artifacts.
