# Meredosia CQA, As-Built, and Surface-Comparability Result — 2026-07-27

## Decision

```text
NOT GOOD TO GO FOR THE CURRENT SENTINEL-1 DEPTH TEST
```

The official Meredosia Construction Quality Assurance report and final as-built survey were recovered successfully. Meredosia has large, professionally surveyed closure areas and strong physical documentation, but it fails the core same-surface comparison requirement.

The capped Fly Ash Pond has a synthetic engineered surface. The confirmed-removed Bottom Ash Pond and East Fly Ash Stockpile areas have soil backfill and vegetation. A Sentinel-1 difference between these areas would mix the closure condition with a major surface-material difference and would not isolate buried depth.

No Earth Engine query was run and no calibration row was created.

## Evidence recovered

### Official CQA report

```text
report = Construction Quality Assurance Report — Closure of the Bottom Ash Pond and Fly Ash Pond
prepared_by = Geotechnology, Inc.
report_date = 2019-01-18
project = J024917.04
page_count = 1336
```

The report documents completed construction, inspections, material testing, licensed surveying, clean-closure certifications, geomembrane installation, synthetic-turf installation, sand-infill measurements, and a final as-built survey.

### Final as-built survey

Figure 2 is titled `FINAL AS-BUILT SURVEY` and documents:

```text
survey_source = David Mason & Associates, Inc.
aerial_and_ground_surface_date = 2018-11-30
licensed_surveyor_support = yes
vertical_datum = NAVD88
contour_interval_ft = 1
site_scale = 0 to 600 feet
```

The figure clearly separates the Fly Ash Pond, Bottom Ash Pond, Bottom Ash Pond Berm, Fly Ash Stockpile, Coal Pile, roads, drainage features, and surrounding infrastructure.

The public PDF does not state the horizontal datum or publish the contractor's original georeferenced aerial, point cloud, or digital terrain model. Therefore, an exact WGS84 execution polygon and numerical boundary-position uncertainty were not created.

## Confirmed removed areas

The CQA report states that CCR was removed from:

- the Bottom Ash Pond, except for the separate berm retained for river-dock access;
- the East Fly Ash Stockpile.

The report documents:

```text
Bottom Ash Pond CCR removal = 2018-03-12 through 2018-05-23
East Fly Ash Stockpile CCR removal = 2018-06-12 through 2018-07-11
CQA observation and approval = yes
final grading = yes
stormwater controls = yes
final vegetation = yes
```

After CQA approval, these areas were brought to final grade using non-CCR backfill, fitted with stormwater controls, fertilized, seeded, and vegetated.

This is strong confirmed-removal evidence.

## Capped positive area

The Fly Ash Pond received CCR excavated from the removed areas. Its subgrade was graded and compacted, then covered with:

```text
40-mil HDPE MicroSpike geomembrane
synthetic turf geotextile
sand infill
ArmorFill in drainage areas
```

The sand infill was measured with calipers on an approximately 100-foot grid and was specified as:

```text
0.50 to 0.75 inch
0.0127 to 0.01905 metre
```

This is actual construction-quality evidence for the surface system. It does not provide a buried soil-cover depth comparable with the vegetated removed areas.

## Fatal radar-comparison problem

The candidate pair would be:

```text
positive = capped Fly Ash Pond with synthetic turf over HDPE
negative = removed Bottom Ash Pond or stockpile with soil and vegetation
```

These surfaces are materially different.

A Sentinel-1 response difference could result from:

- synthetic turf versus living vegetation;
- exposed engineered sand infill versus soil;
- HDPE immediately beneath the turf;
- different roughness and moisture behavior;
- drainage-system geometry;
- the buried CCR condition.

The test could not separate these effects. Therefore, it would not be a defensible depth-calibration experiment.

## Same-surface alternative checked

The retained Bottom Ash Pond Berm also received ClosureTurf and has a surface more comparable with the Fly Ash Pond.

However:

```text
same engineered surface = yes
known non-overlapping depth contrast = no
confirmed negative condition = no
```

Both areas retain CCR beneath the engineered surface, and the public record does not establish two separate same-surface zones with different measured depths to the relevant interface.

This alternative does not rescue the site.

## Geometry and size

The broader closure project covers approximately 60 acres. The Bottom Ash Pond is approximately 11–13 acres and the Fly Ash Pond approximately 34–38 acres, so physical size is not the blocker.

```text
20 m physical support in principle = yes
exact execution geometry = no
pixel-purity test = not run
```

The geometry work was stopped because the surface-comparability gate already failed.

## Current status

```text
usable_positive_depth_site_groups = 0
usable_confirmed_negative_site_groups = 0
usable_calibration_rows = 0
numerical_depth_ready = no
app_depth_enabled = false
earth_engine_query_executed = no
meredosia_CQA_report_recovered = yes
meredosia_final_as_built_survey_recovered = yes
meredosia_confirmed_removal = yes
meredosia_physical_size_support = yes_in_principle
meredosia_same_surface_pair = no
meredosia_exact_wgs84_geometry = no
meredosia_calibration_row_ready = no
```

## Repository artifact

```text
data/meredosia_cqa_asbuilt_screen_result.json
```

## Next step

Close Meredosia for the current Sentinel-1 depth-calibration route. Continue only with a site where the positive and negative or shallow and deep zones have the same final radar-facing surface assembly, exact final survey geometry, supported uncertainty, and a stable observation period.
