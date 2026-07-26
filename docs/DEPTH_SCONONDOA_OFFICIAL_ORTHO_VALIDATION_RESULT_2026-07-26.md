# Sconondoa Phase 3 Official Ortho Validation Result — 2026-07-26

## Decision

```text
DOCUMENT EVIDENCE = GOOD
REAL-WORLD PLACEMENT = SUPPORTED
CURRENT RADAR EXECUTION GEOMETRY = REJECTED
EARTH ENGINE QUERY = DO NOT RUN
```

The provisional Phase 3 polygons were checked against official NYS 2022 one-foot four-band orthoimagery and official building footprints.

The overlay supports the overall placement:

- the Service Center / maintenance building is east of the selected cells;
- Sconondoa Street is south of the selected cells;
- the shallow zone lies north of the deep zone;
- both zones lie on the expected Phase 3 restoration area;
- no gross georeference displacement was found.

This resolves the question of whether the provisional transform placed the polygons on the wrong property or wrong part of the site. It did not.

## Why Earth Engine still must not run

The official imagery exposed a separate radar-pixel purity problem.

The repository's planned analysis scale is 20 metres. The provisional transform also has a maximum control residual of 3.487 metres.

### Shallow Cell A zone

```text
nearest visible official building footprint = 19.008 m
conservative clearance after maximum residual = 15.521 m
```

The shallow zone is correctly placed on the gravel restoration area, but its building clearance is only borderline for a clean 20 m radar footprint.

### Deep combined Cell B/C zone

```text
nearest visible official building footprint = 6.213 m
second-nearest visible official building footprint = 9.391 m
conservative nearest clearance after maximum residual = 2.726 m
```

The deep zone sits between visible buildings. At a 20 m analysis scale, its radar response cannot be cleanly separated from strong building backscatter. This remains true even though the surveyed depth and surface-restoration evidence are valid.

The deep polygon therefore fails the execution geometry gate.

## What remains valid

The following findings are retained:

- Cells A, B, and C have comparable documented final restoration material.
- The selected shallow and deep survey samples have finite measured depths.
- Their depth ranges do not overlap.
- The provisional georeference is not grossly misplaced.
- The site remains useful as engineering evidence that suitable depth ordering exists on paper.

The following findings are not retained:

- the current deep polygon is not suitable for a clean Sentinel-1 test;
- no final execution-ready GeoJSON is approved;
- no Earth Engine query is authorized;
- no calibration row is created.

## Reproducible check

A draft pull request ran a one-off workflow that:

1. queried the official NYS 2022 ortho tile index;
2. downloaded the two intersecting official image tiles;
3. cropped the imagery around the provisional polygons;
4. overlaid the polygons and official building footprints;
5. wrote a validation report without calling Earth Engine.

The authoritative result is recorded in:

```text
data/sconondoa_phase3_official_ortho_validation_result.json
```

## Current status

```text
usable_calibration_rows = 0
numerical_depth_ready = no
app_depth_enabled = false
earth_engine_query_executed = no
sconondoa_document_evidence = good
sconondoa_georeference_placement = supported
sconondoa_current_shallow_zone = borderline_pixel_purity
sconondoa_current_deep_zone = rejected_building_proximity
final_geojson_frozen = no
```

## Next step

Close Sconondoa as an execution candidate for the current 20 m test geometry and return to the ordered candidate list. Test River Road first, then Auburn, then John Sevier. Do not resume generic candidate searching.
