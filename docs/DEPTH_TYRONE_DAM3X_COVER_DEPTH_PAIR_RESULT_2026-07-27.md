# Tyrone Mine Dam 3X cover-depth result - 2026-07-27

## Decision

**NOT GOOD TO GO**

Tyrone Dam 3X is the strongest measured depth-pair candidate recovered so far. It passes the measured-depth, size, common-surface and numerical-depth-uncertainty screens. It fails because the public records do not provide coordinate-tied plot polygons or a plot-specific unchanged Sentinel-1 period.

## Why it advanced

The test plots were constructed concurrently with reclamation of the 3X Tailing Impoundment. The as-built report describes them as field-scale treatments intended to imitate full-scale reclamation operations.

The preferred pair is on the broad top surface:

- Test Plot 5: nominal 2-foot cover, 4.06 acres;
- Test Plot 6: nominal 3-foot cover, 4.50 acres.

Both polygons are large enough in principle to retain a 30-40 m clean interior after ordinary boundary and instrumentation exclusions.

## Final measured depths

Five final confirmation pits were excavated within each treatment after underbuilt or overbuilt areas had been regraded.

### Test Plot 5

```text
measured values = 28, 26, 26, 28, 26 inches
mean = 26.8 inches
95% confidence interval = 25.8-27.8 inches
```

### Test Plot 6

```text
measured values = 40, 35, 42, 36, 34 inches
mean = 37.4 inches
95% confidence interval = 33.5-41.3 inches
```

These are direct final measurements within official named treatment polygons. They are not design-only values or volume-derived averages.

## Matching surface construction

The two treatments were constructed under one reclamation program:

- Gila Conglomerate cover material from adjacent borrow areas;
- placement in controlled lifts;
- selective handling of the upper six inches to meet common material requirements;
- common seedbed preparation;
- the same seeding operation;
- common mulching and crimping.

The upper-foot soil-property results vary naturally between samples, but both plots use the same specified radar-facing construction family and revegetation procedure.

## Size check

The as-built engineering plate reports areas of 4.06 and 4.50 acres. Measurement of the published polygons against the plate scale shows narrow dimensions of roughly 110 m. Size is therefore not the fatal blocker.

Sparse lysimeters, instrument nests and cable runs occupy parts of both plots. Conservative exclusion is feasible only after the plot polygons are georeferenced exactly.

## Fatal blocker 1 - no coordinate-tied public polygons

The 2006 as-built plate provides:

- named plot boundaries;
- areas;
- as-built topographic contours;
- instrument locations;
- profiles and a drawing scale.

It does **not** provide:

- northing/easting vertices;
- a coordinate grid;
- a stated horizontal datum for the treatment polygons;
- a GIS, CAD or georeferenced raster file;
- numerical horizontal positioning accuracy.

The report states that construction grading used CAES and post-cover GPS surveys, but the public deliverable does not expose the coordinate data needed to place Test Plots 5 and 6 exactly in the app or Earth Engine.

Matching the old contours to current terrain or imagery would introduce unsupported positional assumptions and would violate the locked coordinate-tied-geometry requirement.

## Fatal blocker 2 - exact plot-level Sentinel-1 stability is not certified

The later records provide strong whole-unit evidence:

- reclamation and seeding were completed in 2005;
- storm-channel corrective actions were completed in early 2007;
- a facility CQA report was submitted in 2008;
- the 2020 closure plan identifies the 3X impoundment as reclaimed;
- the 2021 permit lists the reclaimed 3X unit among areas with partial financial-assurance release.

However, the later public drawings and permit do not preserve the exact Test Plot 5 and Test Plot 6 boundaries or certify that the proposed clean interiors remained physically unchanged during a specific Sentinel-1 period.

The early monitoring record also documents localized subsidence and repairs around lysimeters and instrument installations. Those features could be excluded if exact coordinates were available, but they cannot be excluded defensibly from an ungeoreferenced plate.

## Locked-gate result

```text
two large final measured depth zones = yes
matching upper soil/vegetation = yes
numerical depth uncertainty = yes
30-40 m clean interior in each = yes in principle
coordinate-tied geometry = no
exact stable Sentinel-1 period = no
```

## App status

```text
Usable calibration rows: 0
Numerical depth ready: No
App depth enabled: No
Earth Engine query executed: No
Training started: No
Plan changed: No
```

## Next action

Continue the approved search unchanged. Prioritize as-built reclamation packages that publish named measured treatment polygons together with coordinates, GIS/CAD geometry or a georeferenced survey deliverable, plus later records confirming an unchanged Sentinel-1 period.

Temporary PR #25 must be closed without merging.
