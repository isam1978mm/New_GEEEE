# Sconondoa Phase 3 Georeference and Radar-Pixel Support Review — 2026-07-26

## Result

The georeferencing step was started and a provisional WGS84 QA file was created.

The original six-point Cell A and Cell C patches from the first go decision must **not** be sent to Earth Engine. Each patch is only about 9.16 m by 4.58 m, which is smaller than one clean Sentinel-1 analysis footprint.

The site-level document decision remains promising, but the execution geometry has been replaced with larger zones.

## Source basis

Reviewed records:

- Appendix A property survey map.
- Appendix B-3 Phase 3 pre-construction, post-excavation, and post-construction drawings.
- Final Engineering Report restoration statement for Cells A, B, and C.

Direct survey facts used:

- Appendix B-3 horizontal coordinates use an assumed local project datum.
- Appendix B-3 elevations use NAVD88.
- Appendix A uses NAD83(2011) New York State Plane, Central Zone, US survey feet.
- Cells A, B, and C have the same documented final surface assembly:
  - woven geotextile;
  - 8 inches compacted run-of-bank gravel;
  - 4 inches crushed stone.

## Original patch support failure

### Original shallow patch

Cell A points:

```text
121, 122, 123, 130, 131, 132
```

Calculated convex-hull support:

```text
area = 41.75 m²
rotated dimensions = 9.16 m × 4.58 m
```

### Original deep patch

Cell C points:

```text
316, 317, 318, 321, 322, 323
```

Calculated convex-hull support:

```text
area = 41.66 m²
rotated dimensions = 9.17 m × 4.56 m
```

These dimensions are too small for an honest clean Sentinel-1 depth-ordering comparison. The polygons would be dominated by mixed pixels and polygon-edge placement.

## Replacement shallow zone

Use the upper interior of Cell A, supported by points:

```text
109, 112, 118, 123, 127, 132, 138, 141, 150, 159
```

Direct final and bottom elevations give:

```text
sample count = 10
depth range = 10.8–12.0 ft
depth range = 3.292–3.658 m
mean depth = 11.52 ft
mean depth = 3.511 m
```

Calculated polygon support:

```text
area = 387.5 m²
minimum rotated dimension = 21.1 m
maximum rotated dimension = 25.6 m
```

This zone avoids the localized deeper Cell A area around points 142, 153, and 154.

## Replacement deep zone

Use one combined interior zone across Cells B and C.

Cell B support points:

```text
201, 202, 203, 204,
208, 209, 210,
212, 213, 214,
216, 217, 218,
220, 221, 222,
224, 225, 226
```

Cell C support points:

```text
306, 307, 308,
311, 312, 313,
316, 317, 318,
321, 322, 323,
326, 327, 328,
331, 332, 333
```

Direct final and bottom elevations give:

```text
sample count = 37
depth range = 15.2–16.7 ft
depth range = 4.633–5.090 m
mean depth = 16.014 ft
mean depth = 4.881 m
```

Calculated polygon support:

```text
area = 498.8 m²
minimum rotated dimension = 23.2 m
maximum rotated dimension = 24.3 m
```

The combined zone crosses the mapped B/C cell-limit line. This is disclosed in the QA file. Cells B and C have the same documented restoration assembly and non-overlapping depth ordering relative to the selected Cell A zone.

## Ordering margin

Using the conservative shallow maximum and deep minimum:

```text
deep minimum − shallow maximum
= 15.2 ft − 12.0 ft
= 3.2 ft
= 0.975 m
```

The selected survey samples therefore retain non-overlapping depth ranges.

## Provisional georeferencing

The Appendix B-3 local grid was tied provisionally to Appendix A by:

1. fitting Appendix A property-line pixels to the exact State Plane property courses;
2. fitting Appendix B-3 local grid coordinates to the B-3 drawing;
3. using five common Service Center building controls between the drawings;
4. solving a two-dimensional affine transform;
5. converting NAD83(2011) New York Central feet to WGS84.

Current control residuals:

```text
mean residual = 5.49 ft = 1.67 m
maximum residual = 11.44 ft = 3.49 m
```

This is useful for placement QA at Sentinel-1 scale, but it is not yet an authoritative survey transformation.

## Files added

```text
data/sconondoa_phase3_depth_ordering_qa_only.geojson
docs/DEPTH_SCONONDOA_GEOREFERENCE_PIXEL_SUPPORT_2026-07-26.md
```

The GeoJSON is deliberately marked:

```text
QA_ONLY_NOT_EXECUTION_READY
```

It must not be used for an Earth Engine query until placement is checked against an authoritative georeferenced control or a reliable imagery overlay.

## Decision

```text
SITE DOCUMENT SCREEN = GOOD TO GO
ORIGINAL SIX-POINT POLYGONS = REJECTED AS TOO SMALL
REPLACEMENT POLYGONS = NOMINAL 20 M SUPPORT PASSED
GEOREFERENCE = PROVISIONAL
EARTH ENGINE EXECUTION = HOLD
```

## Current status

```text
usable_calibration_rows = 0
numerical_depth_ready = no
app_depth_enabled = false
earth_engine_query_executed = no
original_patch_pixel_support = failed
replacement_patch_pixel_support = passed_nominal_20m
georeferenced_geojson_created = yes_qa_only
georeference_authoritatively_validated = no
```

## Next step

Validate the provisional WGS84 polygons against one authoritative common control point or a correctly georeferenced survey/imagery source. If the placement error remains safely below the polygon inward buffer, freeze the polygons and run the repository's Sentinel-1 coverage and matched-feature dry run before allowing live Earth Engine execution.
