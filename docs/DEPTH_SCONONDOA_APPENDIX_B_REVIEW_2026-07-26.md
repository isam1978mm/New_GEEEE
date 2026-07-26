# Sconondoa Appendix B Review — 2026-07-26

**Branch:** `main`  
**Decision:** `NOT GOOD TO GO`  
**Reason:** excavation geometry and measured depths are available, but no defensible shallow-versus-deep pair has confirmed comparable final radar-facing surface conditions.

## Current status

```text
sconondoa_appendix_b_reviewed = yes
cell_geometry_available = yes
finite_excavation_measurements_available = yes
comparable_shallow_deep_surface_pair_confirmed = no
earth_engine_query_executed = no
usable_calibration_rows = 0
numerical_depth_ready = no
app_depth_enabled = false
```

## Main decision

Appendix B contains strong excavation geometry and professional survey evidence. The blocker is not the lack of excavation measurements. The blocker is linking those measurements to two separate areas whose post-restoration radar surfaces are demonstrably equivalent.

Selecting a shallow and deep cell without that proof could measure asphalt, gravel, drainage, compaction, moisture, utilities or infrastructure differences rather than excavation depth.

## Appendix B contents

Appendix B is organized into Phase 1, Phase 2 and Phase 3 as-built survey sets.

### B-1 — Phase 1

Cells shown:

- Cell I
- Cell II
- Cell III
- Cell IV

The drawings provide:

- surveyed cell boundaries;
- grid-point identifiers;
- northing and easting coordinates;
- pre-excavation elevations;
- post-excavation elevations;
- calculated or tabulated excavation depths;
- top-of-general-fill and top-of-subbase drawings;
- licensed-surveyor certification and benchmarks.

The four-cell arrangement and grid intersections are clearly visible.

Phase 1 was surveyed and completed around 2008, before Sentinel-1 operations. It cannot support a Sentinel-1 before-and-after excavation test. It could only be considered as a later static spatial comparison, which would still require proof that the cell surfaces remained comparable and unchanged.

### B-2 — Phase 2

Cells shown:

- Cell 1
- Cell 2
- Cell 3
- Cell 3A
- Cell 4
- Cell 5

The drawings contain visible excavation limits, grid points, coordinates, pre-construction elevations, post-excavation elevations, target-removal elevations and material-volume calculations.

The geometry is detailed enough to digitize separate cell polygons. Pages 14 through 24 show the principal Cell 1 through Cell 4 boundaries and surveyed point tables.

#### Verified Cell 2 calculations

The Cell 2 table directly lists pre-construction and post-excavation ground elevations.

| Survey point | Pre-construction | Post-excavation | Calculated excavation depth | Metres |
|---|---:|---:|---:|---:|
| 2A | 420.6 ft | 399.9 ft | 20.7 ft | 6.31 m |
| 2B | 418.9 ft | 400.5 ft | 18.4 ft | 5.61 m |
| 2C | 419.1 ft | 401.2 ft | 17.9 ft | 5.46 m |
| 2D | 419.2 ft | 401.6 ft | 17.6 ft | 5.36 m |
| 2N | 413.5 ft | 399.7 ft | 13.8 ft | 4.21 m |

These values are calculated as:

```text
excavation depth = pre-construction surface elevation - post-excavation bottom elevation
```

The Cell 2 drawing directly states a target-removal elevation of approximately 400.0 ft. It also distinguishes points affected by deeper regulator-approved excavation.

This proves that Cell 2 had finite, spatially variable excavation depths.

#### Cells 3 and 3A

The notes report separate excavation quantities and state that the post-excavation surveys were used to construct digital terrain models.

They also indicate:

- Cell 3 material above the target level;
- additional material below the target level;
- Cell 3A material above the target level;
- a small additional quantity below the target level.

Therefore, Cells 3 and 3A had finite surveyed excavation bottoms. The depth is not one constant number for an entire cell; it varies between grid points.

#### Cells 4 and 5

The later B-2 sheets show:

- separate cell limits;
- point-number tables;
- northing and easting coordinates;
- pre-construction elevations;
- post-excavation elevations;
- areas of additional excavation highlighted in some tables;
- nearby roads, gravel drives, drainage, utilities and adjacent cells.

The cell geometry is mappable, but the drawings show substantial surface-context differences and infrastructure around and across these areas.

### B-3 — Phase 3

Cells shown:

- Cell A
- Cell B
- Cell C
- Cell D
- Cell E
- Cell F

The Phase 3 pre-construction drawing shows the six cell areas, the maintenance-facility building, asphalt parking, a gravel stockpile, roads, utilities and drainage features.

The post-construction drawings continue to show:

- asphalt parking;
- gravel areas and gravel boundaries;
- Sconondoa Street;
- maintenance-facility structures;
- water, sanitary and stormwater infrastructure;
- riprap or surge-stone areas;
- drainage structures;
- utility lines;
- excavation limits.

The Phase 3 maps provide enough geometry to digitize the cells, but the finished surface is not uniform across all six cells.

## Coordinate system and survey information

The survey sheets use a professional state-plane survey framework with:

- northing and easting coordinates;
- New York State Plane coordinates;
- Central Zone;
- elevations in feet;
- survey benchmarks;
- licensed New York land-surveyor seals.

The drawings appear to reference a modern state-plane horizontal datum and a national vertical datum. The general-note text was not consistently readable enough in every rendered sheet to claim the exact datum wording for every phase without a higher-resolution source drawing.

Therefore:

```text
coordinate_grid_present = yes
northing_easting_coordinates_present = yes
elevation_units = feet
exact_datum_wording_error_free = no
explicit_numerical_survey_tolerance_found = no
professional_certification_present = yes
benchmarks_present = yes
```

## Final-surface problem

The drawings identify or visibly distinguish several surface conditions:

- asphalt;
- gravel;
- gravel drives;
- riprap or surge stone;
- building footprints;
- landscaped or wooded edges;
- utility corridors;
- drainage areas;
- roads and parking surfaces.

They do not establish that two selected cells had the same final material, same thickness, same compaction, same moisture behaviour and same subsequent land use.

A line labelled `edge of gravel` proves where gravel was mapped. It does not prove that the entire adjacent excavation polygons received an equivalent radar-facing restoration system.

## Required exclusions

Any future polygon extraction would need substantial buffers around:

- Sconondoa Street;
- asphalt parking;
- the maintenance-facility building;
- gravel drives;
- rail or embankment areas;
- water lines;
- sanitary sewer;
- storm drainage;
- catch basins and manholes;
- wells and monitoring points;
- riprap or surge stone;
- sheet-pile boundaries;
- cell edges;
- stockpile areas;
- woods and vegetation boundaries;
- narrow cells or strips smaller than a practical Sentinel-1 pixel neighbourhood.

At Sentinel-1 scale, these exclusions may leave limited uncontaminated interior area.

## Gate evaluation

Requirements satisfied:

```text
finite_surveyed_excavation_bottoms = yes
different_excavation_depths = yes
cell_boundaries = yes
coordinates_and_control_points = yes
geometry_sufficient_for_digitization = yes
```

Requirements not satisfied:

```text
confirmed_comparable_finished_surface_pair = no
cell_wide_final_surface_matched_to_every_bottom_point = no
one_representative_depth_per_complete_cell = no
explicit_numerical_survey_uncertainty = no
clean_cell_interiors_demonstrated = no
sentinel1_pre_excavation_imagery_for_early_phases = no
```

## Final decision

```text
site = sconondoa
radar_depth_ordering_candidate = not_good_to_go
reason = comparable_final_surface_not_confirmed
earth_engine_query_executed = no
scientific_radar_linkage_outcome = not_evaluated
```

Do not create shallow/deep GeoJSON polygons and do not run the Sentinel-1 depth-ordering screen from these drawings alone.

## Next step

Close Sconondoa for the current calibration route. The next evidence search must require both of the following before a candidate advances:

1. finite measured or calculable depth zones; and
2. documented equivalent final surface construction and later land use across the compared zones.

Do not accept geometry and depth measurements alone as sufficient evidence.
