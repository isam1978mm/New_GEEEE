# Future Slice 04 / Phase D2 Private KMZ Writer

Phase D2 adds a private KMZ writer only.

## Selected Writer Family

Selected family:

- private KMZ point writer

Implemented module:

`app/pipeline/parity/private_map_artifact_writers.py`

The writer accepts already-computed private point summaries and writes one private KMZ file under a caller-provided run directory. It does not compute scientific outputs, infer labels, or create public overlays.

## KMZ And KML Behavior

The default output path is under:

`run_dir/private_map_artifacts/kmz/`

The KMZ contains a KML member named:

`doc.kml`

The private KML can contain exact point coordinate geometry because it remains inside the private KMZ file under the run directory. The KML supports neutral class labels such as `Class_A` and score/probability fields when those values are already present in the supplied private point payload.

## Redacted Summary Boundary

The private internal result may include the local path for internal tooling.

The redacted/public-safe summary must not include:

- exact coordinates
- raw geometry
- local filesystem paths
- private hashes
- KMZ download URLs
- KML inline content

The artifact metadata defaults to:

- `artifact_class=FILESYSTEM_ONLY`
- `private_classification=PRIVATE_COORDINATE_ARTIFACT`
- `filesystem_only=true`
- `http_servable=false`
- `frontend_visible=false`
- `downloadable_via_api=false`

## Safety Boundary

Phase D2 does not:

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
- change raster or GRID math
- change classifier or model logic
- add training or inference behavior
- port the full Tesla flow

## Later Work

Heatmap writer work remains Phase D3.

Phase E4 remains the later comparator slice for Phase D private map artifacts.
