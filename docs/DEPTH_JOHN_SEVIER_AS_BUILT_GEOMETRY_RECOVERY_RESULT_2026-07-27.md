# John Sevier As-Built Geometry Recovery Result — 2026-07-27

## Decision

```text
DOCUMENTED POSITIVE/NEGATIVE CONDITIONS = STRONG
EXACT EXECUTION GEOMETRY = BLOCKED
EARTH ENGINE QUERY = DO NOT RUN
CALIBRATION ROW = NOT CREATED
```

John Sevier remains the strongest candidate in the completed River Road → Auburn → John Sevier sequence, but the public record still does not provide an exact, defensible as-built boundary for the eastern capped area and western excavated/restored area.

The site is therefore retained as strong engineering evidence and a future record-recovery candidate. It is not approved for polygon creation or Sentinel-1 execution.

## What remains supported

The official written closure plan supports all of the following:

- closure was completed in 2017;
- an approximately 20-acre eastern area contains consolidated CCR beneath an engineered final cover;
- an approximately 22-acre western area was excavated, graded for positive drainage, and vegetated;
- an earthen berm separates the capped eastern footprint from the western area;
- the eastern alternative final cover contains a 40-mil geomembrane, a geocomposite drainage layer, 18 inches of protective/infiltration soil, and 6 inches of vegetative/erosion soil;
- the nominal vertical distance from the final surface to the top of the geosynthetic system is 24 inches, or 0.6096 m;
- an as-built survey was used in the engineering record;
- post-closure inspections describe maintained vegetation and no major structural deficiencies.

This supports a positive/negative structure in principle:

```text
potential positive = eastern engineered cap
nominal positive depth = 0.6096 m to top of geosynthetic system
potential negative = western area excavated to native material and restored
```

## Exact geometry recovery attempted

The following public routes were checked:

1. TVA's 98 MB `257-73(c) History of Construction` report, which is listed in the official John Sevier CCR document library and is reported to contain the final-configuration figure and construction-drawing appendix.
2. The `tvawcma.com` mirror of the same TVA document path.
3. The World of Coal Ash 2013 John Sevier Bottom Ash Pond conference paper.
4. The World of Coal Ash 2015 John Sevier closure-sequencing conference paper.
5. The University of Kentucky UKnowledge record and direct-file endpoint for the 2015 paper (`article=1739`, `context=woca`).
6. Search-engine caches and indexed text for the TVA report and conference papers.
7. Public TVA annual engineering-inspection reports and maps.

A temporary draft pull request ran one-off download and extraction workflows. The TVA host, mirror host, flyash.info host, and UKnowledge direct-file endpoint did not yield a usable PDF to the automated runner. The branch produced only access-failure logs and no rendered map pages.

The temporary tooling is not merged because it did not recover evidence.

## Why the approximate maps are insufficient

The annual inspection maps depict the Bottom Ash Pond and major infrastructure, but their unit boundaries are labelled approximate. They cannot be promoted to survey-grade geometry or used to split the eastern cap from the western restored area.

The written closure plan gives area totals and directional descriptions but does not include the coordinate-bearing as-built boundary. A hand-drawn or imagery-estimated dividing line would invent the key calibration geometry.

Therefore no GeoJSON polygon is created.

## Separate depth-uncertainty blocker

Even if the as-built boundary were recovered, the public documents reviewed so far provide a constructed nominal 24-inch cover, not point-by-point final thickness measurements or a numerical total uncertainty for the surface-to-geosynthetic depth.

The missing geometry and missing numerical uncertainty are independent blockers.

## Current status

```text
usable_calibration_rows = 0
numerical_depth_ready = no
app_depth_enabled = false
earth_engine_query_executed = no
john_sevier_positive_negative_pair_documented = yes_in_principle
john_sevier_exact_as_built_geometry = unavailable_in_recovered_public_record
john_sevier_depth_uncertainty = missing
john_sevier_geojson_created = no
john_sevier_pixel_support_tested = no
john_sevier_live_radar_test_ready = no
```

## Next step

Return to the strongest unfinished complementary evidence routes:

1. **J.R. Whiting Ponds 1 and 2** for actual mapped positive cover-thickness measurements; seek the survey's numerical vertical accuracy and a stable comparison condition.
2. **Plant Kraft AP-1** for a surveyed confirmed-removal geometry; recover and render the post-excavation/excavation-limit drawing, then verify boundary uncertainty and stable timing.

Do not run Earth Engine until a candidate has exact geometry, defensible numerical depth or confirmed-negative evidence, uncertainty, and clean pixel support.
