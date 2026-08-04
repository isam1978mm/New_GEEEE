# Tyrone Route B map review — 2026-08-04

## Decision

The uploaded Route B target-map package advances the geometry route but does not yet unblock coordinates.

```text
2006 TP5/TP6 drawing to Tyrone local mine grid = feasible candidate
Tyrone local mine grid to NAD83 UTM/WGS84 = not yet proven
coordinate-tied TP5/TP6 geometry = blocked
numerical depth = not unlocked
```

Route A remains the existing pending EMNRD request. No new request or email is required.

## Files inspected

- 2007 Plate 2 — Tyrone Mine Tailing Area Characteristics and Facilities;
- 2006 3X As-Built Figure 2, PDF page 39;
- 2006 3X As-Built Figure 3, PDF page 40;
- 2006 3X As-Built Plate 1, PDF page 45;
- 2020 Figure 2-4, PDF page 125;
- 2020 Figure 2-17, PDF page 138;
- 2020 Plate 1, PDF page 146;
- 2020 Plate 2, PDF page 147.

## What the map package proves

### 1. A consistent local Easting/Northing grid exists

The 2007 Tailing Area Plate and the 2020 figures show a mine-local coordinate grid with labelled eastings and northings. The same reclaimed 3X impoundment is shown in that grid.

This provides a plausible intermediate coordinate system for transferring the 2006 TP5/TP6 drawing.

### 2. The 2006 and later maps share persistent geometry

The following classes of persistent features are visible across the map series:

- the reclaimed 3X impoundment perimeter and major perimeter bends;
- major crest/toe and bench geometry;
- surrounding access-road alignments;
- major drainage alignments;
- nearby reclaimed 2 and 3 impoundment geometry;
- labelled monitoring-well locations on the later maps.

This is enough to continue a controlled two-stage georeferencing attempt. It is not enough to accept a transformation merely by visually matching the outer 3X outline.

### 3. The later maps contain named geographic-tie candidates

The 2007 and 2020 maps show named monitoring wells near the 3X and 2 impoundments, including labels such as:

```text
27-2005-05
27-2005-04
27-2005-03
27-2005-06
27-2004-01
MVR-2
P2-4
P2-6
```

The New Mexico Office of the State Engineer publishes a Points of Diversion layer containing WGS84 geometry plus published UTM zone, datum, easting, northing, and coordinate-accuracy fields. These records may provide the independent geographic tie required to convert the mine-local grid to NAD83 UTM/WGS84.

A local fetcher has been added:

```text
scripts/fetch_tyrone_ose_pod_candidates.py
```

## Why geometry is still blocked

The map review has not yet established that any named map well is identical to a specific official POD record.

The following must still be completed:

1. Download official POD candidates around Tyrone.
2. Match map labels to POD identities using names, file numbers, locations, or supporting record links.
3. Reject records whose published coordinate accuracy is insufficient.
4. Use at least six defensible matches to fit the local-grid-to-UTM transformation.
5. Reserve at least two additional matches as independent check points.
6. Require independent check RMSE no greater than 5 m and maximum check residual no greater than 7.5 m.
7. Separately audit the 2006-drawing-to-local-grid transformation.
8. Digitize TP5, TP6, and exclusion features only after both transformations pass.
9. Prove a stable post-2014 Sentinel-1 interval before creating a calibration row.

## Route B transformation chain

```text
2006 TP5/TP6 drawing pixels
    ↓ controlled fit + independent checks
Tyrone local mine Easting/Northing grid
    ↓ named official well ties + independent checks
NAD83 UTM / WGS84
    ↓
TP5/TP6 research polygons and exclusion masks
```

Both transformations must pass. A good fit in only one stage is insufficient.

## Prohibited shortcuts

Do not:

- place TP5/TP6 by eye in Google Earth;
- use only the outer impoundment outline as all fit and check points;
- assume the mine-local grid is State Plane or UTM without proof;
- ignore published POD accuracy fields;
- enable Earth Engine calibration before independent checkpoints pass;
- call the result official survey geometry.

## Operational status

```text
route_a_existing_emnrd_request = active_waiting
new_email_or_request_required = false
route_b_target_maps_inspected = true
local_mine_grid_found = true
named_geographic_tie_candidates_found = true
official_pod_candidates_downloaded = false
map_well_to_pod_identity_proven = false
local_grid_to_utm_fit_run = false
coordinate_geometry_unblocked = false
stable_sentinel1_interval_proven = false
numerical_depth_ready = false
app_depth_enabled = false
campaign_004_status = paused_fallback
```

## Next execution sequence

1. Run the official POD candidate fetcher locally.
2. Inspect the ranked JSON/CSV for map-label matches and coordinate-quality fields.
3. If at least eight defensible well matches exist, collect six fit points and two independent check points.
4. If fewer than eight defensible matches exist, Route B remains blocked at the geographic-tie stage while Route A continues waiting.
