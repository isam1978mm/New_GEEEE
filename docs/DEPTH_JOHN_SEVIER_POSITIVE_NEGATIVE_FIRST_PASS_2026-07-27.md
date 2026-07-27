# John Sevier Positive/Negative First Pass — 2026-07-27

## Decision

```text
STRONGEST ORDERED LEAD SO FAR
POSITIVE/NEGATIVE PAIR DOCUMENTED IN PRINCIPLE
NOT YET CALIBRATION-ROW READY
```

John Sevier Bottom Ash Pond is the first candidate in the ordered River Road → Auburn → John Sevier sequence that is not immediately defeated by site size or the absence of a physically distinct comparison condition.

The public engineering record documents:

- an approximately 20-acre eastern area where CCR was consolidated and closed beneath an engineered cap;
- an approximately 22-acre western area from which CCR and some underlying soil were excavated, then graded for drainage and vegetated;
- completed closure in 2017;
- a 40-mil geomembrane and geocomposite drainage layer beneath 24 inches of cover soil on the eastern cap;
- recurring post-closure inspections reporting maintained vegetation and no significant structural deficiencies.

No Sentinel-1 or Earth Engine query was run.

## Potential positive area — eastern engineered cap

The completed alternative final-cover system is documented as:

```text
40-mil geomembrane
+ geocomposite drainage layer
+ 18 inches protective/infiltration soil
+ 6 inches vegetative/erosion soil
= 24 inches total cover soil
= 2.0 ft
= 0.6096 m
```

The closure plan states that the geosynthetic materials were installed and tested, that the soil layers were placed, and that a qualified professional engineer verified the final cover system was constructed in accordance with the CCR rule.

This supports a potential known-depth-positive condition defined as the vertical distance from the final vegetated surface to the top of the geomembrane/geocomposite system.

However, the public record recovered so far provides a constructed nominal layer thickness, not point-by-point final measured thicknesses or a numerical total uncertainty.

## Potential confirmed-negative area — western restored area

The closure plan states that CCR and some underlying soil were excavated from one portion of the unit and placed in the eastern consolidated area. Later inspection reports describe the western section as excavated down to native material, restored with fill for positive drainage, and vegetated.

This supports a potential confirmed-no-CCR comparison condition within the western restored area, provided the exact final excavation boundary can be recovered and later fill/infrastructure do not create an unsuitable radar surface.

The western area is not a zero-depth positive record. It is a potential confirmed-negative/control area.

## Size and timing

```text
eastern capped area ≈ 20 acres
western graded/vegetated area ≈ 22 acres
closure construction completed = December 2017
```

These areas are large enough in principle to support multiple 20 m Sentinel-1 footprints. Pixel purity has not yet been tested.

Post-closure inspection reports through 2024 describe maintained grass, no global slope instability, no sinkholes or depressions, and no significant inspection deficiencies. They also document drainage structures, piezometers, settlement points, and maintenance features that must be excluded from any execution geometry.

An 870-megawatt natural-gas plant continues to operate at the broader John Sevier site. Therefore, geometry must also be screened for buildings, roads, operating infrastructure, and strong radar scatterers.

## Public-record limitations

The following remain missing:

1. the exact as-built boundary between the eastern capped area and western excavated/restored area;
2. the as-built survey cited in the closure plan;
3. numerical horizontal survey accuracy;
4. construction tolerance and measurement accuracy for the 24-inch cover;
5. the publicly referenced FY2020 and 2023 Final Cover System Integrity Study reports;
6. point-by-point final cover-thickness measurements, if any;
7. a mapped stable interior positive polygon and confirmed-negative polygon;
8. a clean 20 m pixel-support result;
9. Sentinel-1 acquisition and same-orbit coverage results.

The publicly available annual inspection maps label facility boundaries approximate. They cannot be treated as the final survey boundary.

## Evidence classification

```text
eastern_cap_depth_definition = final_surface_to_top_of_geosynthetic_system
eastern_cap_nominal_depth_m = 0.6096
eastern_cap_actual_construction_supported = yes
eastern_cap_point_measurements_recovered = no
eastern_cap_numerical_uncertainty_recovered = no
western_CCR_removal_supported = yes
western_confirmed_negative_exact_polygon_recovered = no
positive_negative_pair_documented_in_principle = yes
```

## Current status

```text
usable_calibration_rows = 0
numerical_depth_ready = no
app_depth_enabled = false
earth_engine_query_executed = no
john_sevier_document_screen = strongest_ordered_lead
john_sevier_positive_condition = eastern_24_in_engineered_cap
john_sevier_negative_condition = western_excavated_to_native_restored_area
john_sevier_exact_as_built_geometry = missing
john_sevier_depth_uncertainty = missing
john_sevier_clean_20m_pair_confirmed = no
john_sevier_calibration_row_ready = no
```

## Next step

Recover the final-configuration/as-built drawing and any cover-integrity or construction-quality records. Then build conservative eastern positive and western negative polygons, exclude infrastructure and boundaries, and run the 20 m pixel-support gate before any Sentinel-1 catalogue or Earth Engine query.