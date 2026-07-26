# Sconondoa Street Phase 3 Depth-Ordering Review — 2026-07-26

## Decision

```text
GOOD TO GO
```

This is a **go decision for a real Sentinel-1 depth-ordering method screen**, not a statement that numerical depth is already validated and not a populated calibration row.

## Source records reviewed

- `Report.HW.727008.2021-06-25.Final Engineering Report Text and Figures.pdf`
- `Report.HW.727008.2021-06-25.FER Appendices A through C-Survey Figures and Photos.pdf`
- Appendix B-3 Phase 3 pre-construction, post-excavation, and post-construction survey drawings

## Why the earlier surface-material blocker is resolved

The Final Engineering Report, Section 5.9.1.2, states that:

- woven geotextile separation fabric was installed above compacted backfill in each remedial excavation area;
- **Cells A, B, and C** and portions of Cells D and E were restored with the same surface assembly;
- that assembly was **8 inches of compacted run-of-bank gravel plus 4 inches of crushed stone**.

Cells A, B, and C therefore provide directly comparable restored surface material.

## Survey reference and quality notes

Appendix B-3 states:

- horizontal coordinates use an **assumed project datum**;
- elevations are referenced vertically to **NAVD88**;
- Thew Associates PE-LS, PLLC performed professional pre-construction, excavation-bottom, and post-construction surveys;
- Cell A bottom elevations were collected at 67 of 81 grid points during excavation and at the remaining 14 points on later survey dates;
- digital terrain models were generated from the surveyed surfaces;
- no explicit numerical plus/minus survey tolerance was found on the reviewed sheets.

## Selected shallow and deep areas

### Shallow area — Cell A interior patch

Use the interior six-point patch formed by grid points:

```text
121, 122, 123, 130, 131, 132
```

These points avoid the cell boundary and the localized deeper point at grid point 142.

Depth was calculated exactly as:

```text
post-construction final surface elevation - post-excavation bottom elevation
```

| Point | Final surface (ft NAVD88) | Bottom (ft NAVD88) | Depth (ft) | Depth (m) |
|---|---:|---:|---:|---:|
| 121 | 421.7 | 410.0 | 11.7 | 3.566 |
| 122 | 421.7 | 409.9 | 11.8 | 3.597 |
| 123 | 421.8 | 409.8 | 12.0 | 3.658 |
| 130 | 421.7 | 409.9 | 11.8 | 3.597 |
| 131 | 421.8 | 409.9 | 11.9 | 3.627 |
| 132 | 421.9 | 410.0 | 11.9 | 3.627 |

```text
shallow patch mean depth = 11.85 ft = 3.612 m
shallow patch range = 11.7 to 12.0 ft = 3.566 to 3.658 m
```

Local project coordinates:

| Point | Northing | Easting |
|---|---:|---:|
| 121 | 5,185.6 | 5,175.5 |
| 122 | 5,176.4 | 5,187.3 |
| 123 | 5,167.1 | 5,199.0 |
| 130 | 5,173.9 | 5,166.2 |
| 131 | 5,164.6 | 5,178.0 |
| 132 | 5,155.3 | 5,189.8 |

### Deep area — Cell C interior patch

Use the interior six-point patch formed by grid points:

```text
316, 317, 318, 321, 322, 323
```

These points are well inside Cell C and away from the western gravel-edge corridor and the Cell B boundary.

| Point | Final surface (ft NAVD88) | Bottom (ft NAVD88) | Depth (ft) | Depth (m) |
|---|---:|---:|---:|---:|
| 316 | 422.0 | 405.5 | 16.5 | 5.029 |
| 317 | 422.2 | 405.9 | 16.3 | 4.968 |
| 318 | 422.4 | 406.0 | 16.4 | 4.999 |
| 321 | 422.2 | 405.9 | 16.3 | 4.968 |
| 322 | 422.3 | 406.2 | 16.1 | 4.907 |
| 323 | 422.5 | 406.2 | 16.3 | 4.968 |

```text
deep patch mean depth = 16.32 ft = 4.973 m
deep patch range = 16.1 to 16.5 ft = 4.907 to 5.029 m
```

Local project coordinates:

| Point | Northing | Easting |
|---|---:|---:|
| 316 | 5,104.0 | 5,068.6 |
| 317 | 5,099.4 | 5,082.9 |
| 318 | 5,094.8 | 5,097.1 |
| 321 | 5,089.8 | 5,063.9 |
| 322 | 5,085.2 | 5,078.2 |
| 323 | 5,080.6 | 5,092.5 |

## Ordering margin

```text
deep mean - shallow mean = 4.47 ft = 1.36 m
```

The two selected patches have non-overlapping measured depth ranges and the same documented surface-restoration assembly.

## Areas to exclude

Do not include pixels intersecting or immediately adjacent to:

- the Service Center Building;
- Cell D asphalt parking and driveway restoration;
- Cell E and Cell F vegetated/topsoil restoration;
- Sconondoa Street and sidewalk strips;
- the western gravel-drive/utility corridor;
- gas, water, sanitary, and storm utilities;
- manholes, cleanouts, valves, and drainage structures;
- cell boundaries and sheet-pile lines;
- the localized deeper area around Cell A point 142;
- the building-side utility area along the east side of Cell B.

## GeoJSON conversion plan

The B-3 coordinates are on a local assumed project datum, so they cannot be written directly as WGS84 longitude/latitude.

1. Extract the selected grid-point coordinates and the cell-limit lines from the B-3 drawings.
2. Select at least three non-collinear control features visible both in B-3 and in a georeferenced source, preferably surveyed property corners, Service Center Building corners, road-edge intersections, or utility/manhole points.
3. Tie those controls to Appendix A/state-plane coordinates or another authoritative georeferenced survey.
4. Solve a two-dimensional affine transform from the local project coordinates to the authoritative projected CRS.
5. Check residual error on additional unused control points.
6. Transform the shallow and deep patch vertices.
7. Convert the projected coordinates to EPSG:4326 and write separate GeoJSON polygons.
8. Apply inward buffers so the radar polygons do not include cell edges, utilities, roads, or mixed restoration areas.

The six-point patches can be converted into conservative interior polygons using the outer points of each two-row grid patch, followed by an inward buffer sized for the final Sentinel-1 analysis scale.

## Current status

```text
usable_calibration_rows = 0
numerical_depth_ready = no
app_depth_enabled = false
earth_engine_query_executed = no
sconondoa_phase3_document_screen = good_to_go
comparable_surface_pair_confirmed = yes
shallow_patch = Cell A points 121,122,123,130,131,132
shallow_mean_depth_m = 3.612
deep_patch = Cell C points 316,317,318,321,322,323
deep_mean_depth_m = 4.973
```

## Next step

Create georeferenced GeoJSON polygons for the two selected patches, validate their placement against the site map and current imagery, and only then run the controlled Sentinel-1 depth-ordering screen.
