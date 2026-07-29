# Option 1 Syncrude 1983 Soil Reconstruction Project decisive result - 2026-07-29

## Decision

**NOT GOOD TO GO for numerical-depth calibration.**

This is an **Option 1 - Global Numerical Depth** evidence result. Option 3 is not active.

## What is proven

The 1992 five-year summary documents a large field experiment established in fall 1983 on a tailings-sand pad at the Syncrude Mildred Lake site.

The experiment used nine reconstructed-soil mixtures. Each mixture was tested at two mixing thicknesses:

- 20 cm;
- 40 cm.

Each treatment was replicated three times, producing 54 treatment plots.

The 20 cm and 40 cm treatments are a strong scientific design because the same reconstructed-soil mixture can be compared at two intended depths.

## Fatal size blocker

The report states that each individual treatment plot measured:

```text
44 m by 22 m
```

Each plot contained ten species subplots measuring approximately 10 m by 8 m, with 2-4 m buffer strips between plots.

The 22 m short dimension is fatal for the approved radar screen. After excluding:

- plot boundaries;
- buffer strips;
- species-subplot transitions;
- planted rows;
- monitoring locations;
- access and local disturbance;

no defensible 30-40 m clean interior can remain.

This failure is independent of whether the report contains measured final thicknesses or uncertainty. The geometry alone makes the treatment plots unsuitable for the approved Sentinel-1 comparison.

## Additional blockers

The public report also does not provide:

- coordinate-tied treatment polygons or surveyed corners;
- a modern official WGS84 plot layer;
- proof that the exact 1983 plots remained intact and unchanged after 2014;
- a documented plot-specific Sentinel-1 observation period.

## Gate table

```text
same-mixture 20 cm versus 40 cm design = PASS
replication = PASS
30-40 m clean interior = FAIL
coordinate-tied geometry = FAIL
stable Sentinel-1 period = FAIL
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

Do not continue into radar or georeferencing. The 22 m plot width is a permanent geometry failure for the approved method.
