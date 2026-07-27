# Sconondoa Phase 3 Georeference Correction — 2026-07-26

## Decision

```text
THE PLACEMENT ERROR WAS FIXABLE AND HAS BEEN CORRECTED.
```

The provisional QA GeoJSON must not be used. It is superseded by:

```text
data/sconondoa_phase3_depth_ordering_survey_corrected.geojson
```

The corrected file is ready for the repository's Sentinel-1 **coverage and pixel-support dry run**. It is not a calibration row, it does not enable numerical depth, and no Earth Engine query has been executed.

## What was wrong

The provisional transformation used an unconstrained affine fit assembled from approximate drawing controls. Its two horizontal scale factors were strongly inconsistent even though both source surveys use feet. That distorted the local Phase 3 survey grid and shifted the polygons materially.

Compared with the corrected placement:

```text
shallow polygon centroid shift = 23.9 m
deep polygon centroid shift = 34.0 m
```

The provisional file is therefore marked superseded and must not be uploaded to Earth Engine.

## Correct method

The corrected transformation uses the professional surveys themselves:

1. Appendix B-3 supplies the Phase 3 local assumed-datum grid and exact polygon vertices.
2. Appendix A supplies NAD83(2011) New York State Plane, Central Zone coordinates.
3. Three common permanent Service Center building corners were used as transformation controls.
4. A fourth, unused southwest building corner was retained as an independent holdout check.
5. Because both surveys use feet, the transformation was constrained to a unit-scale two-dimensional rotation and translation. This prevents artificial stretching of the survey grid.
6. State Plane coordinates were converted to WGS84 for GeoJSON output.

## Corrected transformation

Local Appendix B-3 easting/northing in feet is transformed to EPSG:6535 by:

```text
E_state =  0.97842794 * E_local - 0.20658839 * N_local + 1066120.4639
N_state =  0.20658839 * E_local + 0.97842794 * N_local + 1124114.5463
```

This is a rotation plus translation with no artificial change of survey scale.

## Placement checks

```text
building controls used = 3
control residual mean = 0.116 m
control residual maximum = 0.160 m
unused building-corner holdout residual = 0.639 m
Appendix A State Plane fit mean residual = 0.232 m
Appendix A State Plane fit maximum residual = 0.385 m
conservative combined placement uncertainty = 1.1 m
```

The 1.1 m conservative uncertainty is much smaller than the selected polygons' minimum dimensions:

```text
shallow minimum dimension = 21.1 m
deep minimum dimension = 23.2 m
```

## Corrected zones

### Shallow zone

```text
zone = upper Cell A
area = 387.5 m²
depth range = 3.292–3.658 m
mean depth = 3.511 m
```

### Deep zone

```text
zone = combined interior of Cells B and C
area = 498.8 m²
depth range = 4.633–5.090 m
mean depth = 4.881 m
```

The measured depth ranges remain non-overlapping. The deep polygon still crosses the internal B/C cell boundary; this remains declared in the GeoJSON and must be considered in the dry-run QA.

## File status

```text
data/sconondoa_phase3_depth_ordering_qa_only.geojson
status = SUPERSEDED_DO_NOT_USE

data/sconondoa_phase3_depth_ordering_survey_corrected.geojson
status = SURVEY_CONTROL_VALIDATED_READY_FOR_COVERAGE_DRY_RUN
```

## Current status

```text
usable_calibration_rows = 0
numerical_depth_ready = no
app_depth_enabled = false
earth_engine_query_executed = no
site_document_screen = good_to_go
survey_georeference_corrected = yes
independent_holdout_check = passed
corrected_geojson_created = yes
coverage_dry_run_ready = yes
live_depth_test_ready = no
```

## Next step

Run the non-training Sentinel-1 coverage and pixel-support dry run using only the corrected GeoJSON. The dry run must confirm acquisition availability, same-orbit support, clean interior pixels, and no excessive mixing with the building, roads, utilities, or the B/C internal boundary before any live method screen is allowed.
