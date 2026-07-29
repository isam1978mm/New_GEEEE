# Option 1 Tyrone 3X Test Plots 5 and 6 decisive result - 2026-07-29

## Decision

**NOT GOOD TO GO for an Earth Engine depth-calibration comparison from the currently available public record.**

This is an **Option 1 - Global Numerical Depth** evidence result. Option 3 is not active.

Tyrone is not rejected because the measured depth pair is weak. It is one of the strongest measured pairs found so far. The route is blocked because the public package still does not provide exact coordinate-tied execution polygons or plot-specific post-2014 stability proof.

## What is proven

### Full-scale adjacent top-surface plots

The official 2006 as-built report and drawings define adjacent top-surface treatments on the reclaimed No. 3X Tailing Impoundment:

- Test Plot 5: nominal 2-foot cover, 4.06 acres;
- Test Plot 6: nominal 3-foot cover, 4.50 acres.

These are full-scale reclamation plots rather than narrow experimental strips. Their mapped size is sufficient in principle for conservative 30-40 m interiors after excluding boundaries and local instrumentation.

### Final measured cover thickness

Five confirmation pits were measured in each plot after cover placement and before seeding.

Test Plot 5 measurements:

```text
28, 26, 26, 28, 26 inches
mean = 26.8 inches
95% confidence interval = 25.8 to 27.8 inches
```

Test Plot 6 measurements:

```text
40, 35, 42, 36, 34 inches
mean = 37.4 inches
95% confidence interval = 33.5 to 41.3 inches
```

The as-built report states that overbuilt or underbuilt areas were graded toward design thickness and that the treatment means are statistically different at 95% confidence.

### Comparable radar-facing construction

The documentary record supports a strong surface match:

- both are adjacent top-surface plots on the same reclaimed impoundment;
- cover materials came from the same Gila Conglomerate borrow system;
- the upper 6 inches were selectively handled under the same texture and rock-content specification;
- the plots were built during the same reclamation program using the same placement process;
- the same seed mix, seeding process, mulch and crimping procedure were applied to the tailing test plots;
- both plots have low top-surface gradients compared with the outslope plots.

The material tables show natural within-plot and between-pit variation, but they do not establish a different designed upper-surface assembly for Plot 5 versus Plot 6.

### Construction and facility history

The 2020 closure plan confirms:

- reclamation started in 2004;
- seeding was completed in 2005;
- reclamation of the 3X Tailing Impoundment was completed in the fourth quarter of 2005;
- corrective work on the primary top-surface storm-water channel was completed in the first quarter of 2007;
- the facility continued to be identified as the Reclaimed 3X Tailing Impoundment in the 2020 closure plan.

The 2007 annual summary also records localized subsidence above the lysimeter installations in both top-surface plots and recommends a small berm, cable protection and hand reseeding around monitoring nests. These localized areas must be excluded from any future radar polygon.

## Fatal blockers

### 1. Exact coordinate-tied plot polygons are not public

The official as-built Figure 2 and Plate 1 provide:

- professional as-built topography;
- a survey boundary;
- north arrows and scale bars;
- mapped Test Plot 5 and Test Plot 6 boundaries;
- instrument and lysimeter locations.

However, the public drawings do not publish:

- a coordinate grid on the test-plot sheet;
- surveyed corner northings and eastings;
- a stated horizontal datum or coordinate system for the plot polygons;
- CAD, GIS or survey-point files containing the plot boundaries.

The 2020 official Mangas Valley figure provides a local coordinate grid for the whole Reclaimed 3X facility, but it does not show Test Plot 5 or Test Plot 6. Transferring the 2006 plot boundaries onto that later facility map by matching the outer impoundment shape would create derived geometry, not official coordinate-tied plot geometry. The public USGS mine-waste polygon is also a later imagery-digitized facility polygon, not a survey-certified treatment boundary.

Therefore no exact WGS84 execution polygons can be created without inventing positional certainty.

### 2. Plot-specific post-2014 stability is not proven

The 2020 closure plan supports long-term facility-level reclamation status and identifies no new full-facility earthwork after the 2007 drainage correction. That is useful but not enough to certify that the exact clean interiors of Plots 5 and 6 were unchanged throughout a Sentinel-1 period.

The public package does not provide later plot-specific records showing:

- the final extent of the 2006 lysimeter-subsidence correction;
- whether any later regrading, erosion repair, reseeding, instrumentation work or traffic affected the proposed interiors;
- a mapped repair history tied to Plot 5 and Plot 6;
- a documented stable observation interval after 2014 for the exact polygons.

## Gate table

```text
full-scale clean zones = PASS IN PRINCIPLE
final measured numerical depths = PASS
numerical uncertainty = PASS
matched radar-facing surfaces = PASS
coordinate-tied geometry = FAIL / EXTERNAL RECORD BLOCKER
stable Sentinel-1 period = FAIL / EXTERNAL RECORD BLOCKER
confirmed control for Option 4 = NOT ESTABLISHED
```

## Operational decision

```text
earth_engine_query_executed = false
calibration_record_created = false
usable_calibration_rows_added = 0
training_started = false
numerical_depth_ready = false
app_depth_enabled = false
option_3_active = false
```

Do not run Earth Engine using polygons estimated from imagery, the USGS facility polygon, DEM patterns, or a shape-matched transfer between drawings.

## What would reopen Tyrone

Tyrone can be reopened under Option 1 if the pending records request or another official source provides both:

1. CAD, GIS, surveyed corners, or another coordinate-controlled deliverable for Test Plots 5 and 6; and
2. later plot-specific inspection, repair and maintenance records establishing a stable post-2014 interval and the areas that must be excluded.

For Option 4, a separate confirmed comparable control would also be required.

## Current plan after this result

- Option 5 remains active in the app and remains labelled **NOT DEPTH**.
- Option 1 continues with other independent measured-site candidates.
- Option 4 remains available but inactive.
- Option 3 remains inactive.
- The Tyrone agency request remains pending; the user will report any response directly.
