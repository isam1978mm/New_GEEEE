# Phase 6 Private Map Artifact Parity Contract

Phase 6 covers coordinate/map/private notebook parity artifacts. It is an inventory,
private-output contract, safety-boundary, and verification-planning phase only.

Phase 6 does not generate coordinate/map/private artifacts. It does not generate
KMZ, KML, GeoJSON, HTML map, image, raster, or NPY files. It does not call Earth
Engine. It does not change science, raster, SAR, optical, DEM, PCA, GRID, object
extraction, or classifier logic.

Phase 6 does not change API, frontend, database, or artifact serving policy. It
does not expose coordinate/map artifacts through HTTP, does not add public
downloads, does not add frontend previews, and does not add map tiles or visual
overlays.

## Scope

Phase 6 tracks these private notebook-parity categories:

- `kmz_outputs`
- `geojson_outputs`
- `heatmap_outputs`
- `visual_map_outputs`
- `coordinate_bearing_filesystem_artifacts`
- `redaction_and_serving_policy`

The source-of-truth helper is:

- `app/pipeline/parity/private_map_artifact_inventory.py`

The helper writes only this JSON inventory report:

- `data/runs/<run_id>/manifests/phase_6_private_map_artifact_inventory.json`

## Privacy Boundary

All Phase 6 coordinate/map/private artifacts default to:

- `filesystem_only=true`
- `http_servable=false`
- `frontend_visible=false`
- `downloadable_via_api=false`
- `artifact_class=LOCAL_SENSITIVE` or `artifact_class=PRIVATE_COORDINATE_ARTIFACT`

Coordinate-bearing artifacts remain filesystem-only unless a later
user-approved phase changes policy. Phase 6 does not make private notebook
artifacts visible through API routes, frontend UI, artifact downloads, previews,
tiles, or overlays.

Public DTOs must stay redacted. They must not include latitude, longitude,
geometry, bounds, CRS transforms, local filesystem paths, or hashes for sensitive
private artifacts.

## Notebook Source Evidence

Notebook and extracted-cell evidence includes selected-point GeoJSON,
GeoJSON feature dumps, KMZ heatmap and target outputs, field mapping KMZ
outputs, visual map overlays, and exact coordinate printouts. Relevant extracted
cell notes include map setup and selected-point output near cells 9-11, GeoJSON
feature dump notes near cells 133 and 190, KMZ generation notes near cells
139, 155-162, 191, 200, 237, and 241, and live map overlay notes near cell 243.

The app already has private candidate artifacts in local stages, including:

- `full_job/location/site_location.geojson`
- `kmz/site_location.kmz`
- `kmz/field_ops_navigation.kmz`
- `full_job/field_ops/field_ops_report.json`
- `full_job/field_ops/field_ops_brief.txt`
- `full_job/gps/gps_point_comparison.json`
- `full_job/gps/gps_point_comparison.csv`
- `focus_zone_summary.json`

These app artifacts remain candidate private outputs only. Runtime artifact
presence is separate from notebook-value parity. Existing app artifacts are not
automatically equivalent to notebook coordinate/map artifacts.

## Category Decisions

| Category | Phase 6 status | Notes |
| --- | --- | --- |
| `kmz_outputs` | `reference_needed` | Notebook KMZ families are broader than current app KMZ outputs. Frozen notebook KMZ references and filename mapping are required before verifier design. |
| `geojson_outputs` | `source_recovery_needed` | The app has a private site-location GeoJSON candidate, but broader notebook feature schemas need source and reference evidence. |
| `heatmap_outputs` | `implementation_later` | Notebook heatmap artifacts depend on private coordinate overlays. No heatmap writer or verifier is added in Phase 6. |
| `visual_map_outputs` | `implementation_later` | Notebook interactive map artifacts remain private and are not exposed in the app. |
| `coordinate_bearing_filesystem_artifacts` | `inventory_only` | Existing app GPS, field-ops, and focus artifacts stay private and need source/reference reconciliation before any parity claim. |
| `redaction_and_serving_policy` | `covered_by_existing_contract` | The project redaction and serving boundary remains unchanged. |

## Verification Planning

Frozen notebook references are required before notebook-value parity can pass.
Later verifier slices must be source/reference-driven and must preserve the
private boundary. A future private verifier may compare file existence, filename
mapping, payload schema, coordinate precision policy, redacted-vs-private
separation, and artifact class metadata. That later work must not change public
serving behavior unless explicitly approved by the user in a separate phase.

Phase 6 follows Phase 5 and precedes Phase 7 in the full roadmap.
