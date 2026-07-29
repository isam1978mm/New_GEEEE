# Option 1 Syncrude 1990 Oil Sands Tailings Capping Study decisive result - 2026-07-29

## Decision

**NOT GOOD TO GO for numerical-depth calibration from the available public record.**

This is an **Option 1 - Global Numerical Depth** evidence result. Option 3 is not active.

## What is proven

The 1994 final report documents a large replicated field experiment built in July 1990 on the Syncrude Mildred Lake mine site.

### Full-scale plot geometry in the design drawing

The study used four treatments:

- 70 cm fair-quality soil;
- 50 cm fair-quality soil;
- 30 cm fair-quality soil;
- 70 cm poor-quality soil.

Each treatment was replicated in three blocks. Each complete treatment plot was approximately 60 m by 60 m. The plot layout shows a total study footprint approximately 246 m long in the main block and 246 m by 102 m across the other blocks.

This is large enough in principle for conservative Sentinel-1 interiors after excluding plot boundaries, access margins, wells and local disturbance.

### Final measured cap thickness

Cap thickness was measured after construction using 50 band-auger measurements per plot.

The report states that the fair-material treatment averages were approximately:

```text
70 cm target -> 80 cm measured average
50 cm target -> 58 cm measured average
30 cm target -> 39 cm measured average
```

Block-specific means shown in Figure 5 remain separated across the three replicated blocks. The report states that the three fair-material treatments had significantly different mean thicknesses.

### Comparable surface treatment

The 70, 50 and 30 cm fair treatments used the same source-material category, the same construction program, fertilizer, surface preparation and planted species pattern. Each plot contained the same four species subplots.

## Fatal blockers

### 1. No coordinate-controlled treatment polygons

The report provides:

- a local plot-layout drawing;
- dimensions;
- a north arrow;
- the relative block arrangement;
- a broad site-location map.

It does not provide:

- surveyed plot-corner coordinates;
- a stated horizontal datum;
- CAD or GIS files;
- a coordinate grid tied to the treatment boundaries;
- an official WGS84 treatment polygon.

The local layout cannot be placed on modern imagery with defensible positional accuracy without inventing control points.

### 2. No demonstrated stable Sentinel-1 period

The public record follows the plots only through the early 1990s. It documents several early disturbances:

- wind-blown tailings deposition during the first year;
- recapping and seeding of surrounding areas in 1991;
- one small erosion gully in Block 3;
- a bison intrusion affecting plots;
- groundwater wells installed in each plot.

The public package does not prove that the exact plots remained identifiable, intact and unchanged after 2014. No later coordinate-tied inspection, repair or land-use history was recovered for these plot boundaries.

### 3. Measurement uncertainty is not published as a usable polygon-depth uncertainty

The report documents 50 measurements per plot and statistically different treatment means, but it does not publish a final numerical confidence interval, standard error, survey tolerance or construction-thickness uncertainty for each treatment polygon in a form usable by the repository calibration validator.

## Gate table

```text
full-scale clean zones = PASS IN PRINCIPLE
final measured numerical depths = PASS
same-material depth contrast = PASS
numerical depth uncertainty = FAIL
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

Do not georeference the plot layout by visual matching alone. Reopen only if official coordinates or survey files and later plot-specific stability records are recovered.
