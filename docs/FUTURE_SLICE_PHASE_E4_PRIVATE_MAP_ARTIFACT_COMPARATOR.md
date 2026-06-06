# Future Slice 06 / Phase E4 Private Map Artifact Comparator

## Scope

Phase E4 adds private comparator capability for Phase D map artifacts. It covers
private GeoJSON, private KMZ, and private heatmap JSON artifacts produced by the
Phase D private map artifact writers.

Phase E4 is comparator/verifier work only. It does not implement new writers, does
not change existing writer behavior, does not expose artifacts through API or
frontend, does not change artifact-serving policy, does not add public overlays or
operator overlay UI, and does not call Earth Engine.

## Supported Phase D Artifact Families

- `phase_d1_private_geojson` — private GeoJSON FeatureCollection
  (`private_features.geojson`)
- `phase_d2_private_kmz` — private KMZ point overlay with `doc.kml`
  (`private_points.kmz`)
- `phase_d3_private_heatmap_json` — private heatmap point JSON
  (`private_heatmap.json`)

The comparator reads existing private artifacts from the app output directory and
the frozen reference bundle directory. Test fixtures may create tiny temporary
GeoJSON, KMZ, and heatmap JSON artifacts under pytest temporary directories only.
Real frozen notebook references remain external and must not be committed.

## Comparator Behavior

The implementation module is:

`app/pipeline/parity/private_map_artifact_comparator.py`

It writes a private JSON report under:

`data/runs/<run_id>/manifests/phase_e4_private_map_artifact_comparator.json`

Comparison behavior by family:

1. GeoJSON
   - parses JSON
   - validates `FeatureCollection` structure
   - compares feature count
   - compares geometry type and coordinate values inside the private comparison
     context, with tolerance-based numeric coordinate comparison
2. KMZ
   - opens the KMZ/ZIP container
   - verifies the expected `doc.kml` entry exists
   - parses the KML as XML
   - compares placemark count and a private structural/content signature
     (placemark name plus coordinate values within tolerance)
3. Heatmap JSON
   - parses JSON
   - compares `schema_version` when present
   - compares the private point count
   - compares coordinate fields and weight/score fields with tolerance

Supported per-artifact statuses:

- `passed`
- `failed`
- `reference_missing`
- `app_output_missing`
- `comparison_unavailable`
- `skipped_by_request`
- `error`

Overall status is `passed` only when every selected artifact passes. Missing
references are not success. Missing app outputs are not success. A
`comparison_unavailable` result is not success. Structural mismatch is not success.
Numeric mismatch above tolerance is not success. A malformed artifact returns
`failed` or `error`, never `passed`.

## Tolerance And Structural Comparison Policy

Tolerance is configurable through `coordinate_atol` and `weight_atol`.

- Structural checks must pass first: FeatureCollection validity, KMZ `doc.kml`
  presence and KML parseability, heatmap points list and matching `schema_version`.
- Count checks must match: feature count, placemark count, heatmap point count.
- Numeric coordinate and weight/score comparisons use absolute tolerance.
- `max_abs_error` and `mean_abs_error` summarize the private numeric comparison in
  the private report only.

## Redacted Summary Behavior

Each result carries a `redacted_summary` that is safe for any later public surface.
The redacted summary excludes exact coordinates, raw geometry, KML contents,
heatmap point payloads, local filesystem paths, private hashes, and download URLs.
It carries only structural status flags, boolean verification flags, the family id,
and a private-boundary note.

Coordinate-bearing files are read only from the app output directory and the
reference bundle directory inside the private comparison context. The full private
report is filesystem-only under `run_dir` and is not a public DTO. No comparator
result makes private artifacts HTTP-servable, frontend-visible, or downloadable by
API.

## Runtime And Parity Flags

Runtime output presence and notebook-value parity remain separate.

- `runtime_output_verified=true` only when all selected app outputs are present.
- `notebook_value_parity_verified=true` only when every selected artifact passes
  value comparison.
- Any missing reference keeps `notebook_value_parity_verified=false`.
- Any missing app output keeps `runtime_output_verified=false`.

## Safety Boundary

Phase E4 does not:

- implement new map writers
- change existing GeoJSON, KMZ, or heatmap writer behavior
- expose private map artifacts through API or frontend
- add public downloads, public overlays, or operator overlay UI
- change artifact-serving policy
- call Earth Engine
- start backend runs
- generate map artifacts, rasters, or NPY arrays
- change raster or math formulas
- train models, run inference, or add ML dependencies
- implement H, I, G, or J follow-up work

The comparator report is private metadata only. It must not be used as approval for
API, frontend, or artifact-serving exposure.

## Later Work

Future slices may register this comparator inside the broader frozen-reference
verifier or extend private map artifact comparison. Those are separate
user-approved slices.
