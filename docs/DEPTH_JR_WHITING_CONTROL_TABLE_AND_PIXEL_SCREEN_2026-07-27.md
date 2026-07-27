# J.R. Whiting Control-Table and Pixel Screen — 2026-07-27

## Decision

```text
MEASURED POSITIVE-DEPTH EVIDENCE = STRONG
NOMINAL 20 M CELL SIZE = PASSED
DEFENSIBLE SHALLOW/DEEP ORDERING = NOT PASSED
CALIBRATION ROW = NOT CREATED
EARTH ENGINE QUERY = NOT RUN
```

The six official J.R. Whiting Ponds 1 and 2 Final Construction Documentation Report files were downloaded and indexed. The vector control-point table on Record Drawing Sheet 6 was extracted directly from the PDF without OCR.

The record drawing contains 107 final-cover thickness measurements at construction control points 1000 through 1106. The points are tied to a 100-foot construction-control grid.

## Construction and survey basis

The final cover was constructed as:

```text
18 inches protective cover
+ 6 inches topsoil
= 24 inches nominal total final cover
```

The report states that:

- thickness control used a GPS-controlled dozer and probe measurements;
- ROWE surveyed the protective-cover grade at construction control points on a 100-foot grid;
- ROWE then surveyed the top of topsoil at the same subgrade control points;
- the Record Drawing table calculates final-cover thickness from record topsoil elevation minus record subgrade elevation;
- the construction record survey was completed as needed between August 9 and November 21, 2019;
- the coordinate reference is Michigan State Plane South Zone NAD83 (2011), with elevations on NGVD29;
- ROWE was the professional certification surveyor and Jonathan Rick, P.S., was the lead surveyor.

## Extracted measured thicknesses

```text
measurement count = 107
minimum thickness = 2.03 ft = 0.618744 m
maximum thickness = 2.50 ft = 0.762000 m
mean thickness = 2.17785 ft = 0.663809 m
```

These are actual record-survey differences, not only the 24-inch design requirement.

The machine-readable screen result is recorded in:

```text
data/jr_whiting_control_table_screen_result.json
```

## Best nominal shallow cell

The best low-variation 100-foot grid cell found in the table uses control points:

```text
1068, 1067, 1075, 1076
```

Measured thicknesses:

```text
2.11, 2.14, 2.15, 2.14 ft
range = 2.11–2.15 ft
range = 0.643128–0.655320 m
mean = 2.135 ft = 0.650748 m
```

## Best nominal deep cell

The strongest 100-foot grid cell with all four corner values above the shallow-cell range uses control points:

```text
1039, 1040, 1052, 1051
```

Measured thicknesses:

```text
2.39, 2.33, 2.24, 2.22 ft
range = 2.22–2.39 ft
range = 0.676656–0.728472 m
mean = 2.295 ft = 0.699516 m
```

## Ordering margin

```text
deep minimum − shallow maximum
= 2.22 ft − 2.15 ft
= 0.07 ft
= 0.021336 m
```

The mean difference is:

```text
2.295 ft − 2.135 ft
= 0.160 ft
= 0.048768 m
```

The measured ranges are nominally non-overlapping, but the non-overlap is only about 2.1 centimetres.

## Pixel-size screen

Each selected cell is nominally:

```text
100 ft × 100 ft
= 30.48 m × 30.48 m
area = 929.0304 m²
```

A 20 m square could fit nominally with about 5.24 m of margin on each side before accounting for horizontal survey uncertainty and exclusions.

Therefore:

```text
nominal geometry size gate = passed
clean execution geometry = not passed
```

The mapped above-cap drainage network crosses the selected deep cell. The final-cover drawing contains additional drainage, monitoring, access, and boundary features that would require exclusion before any radar geometry could be approved.

## Why the depth pair is not defensible

No explicit numerical vertical or horizontal accuracy for the ROWE survey was found in the six-part public closeout package.

The report does provide construction acceptance tolerances:

```text
subgrade grade tolerance = 0.0 to -0.2 ft
protective-cover grade tolerance = +0.2 to 0.0 ft
```

Those values are construction acceptance limits relative to design. They do not establish the measurement uncertainty of the two surveyed elevations used to calculate each final-cover thickness.

The 0.07-ft nominal ordering gap cannot be treated as robust while the survey measurement uncertainty remains unstated. Construction tolerances are not substituted for survey uncertainty.

## Additional calibration limitation

J.R. Whiting provides strong positive-depth evidence, but it still lacks an independently confirmed no-target comparison footprint suitable for the calibration contract.

No background area selected only from imagery is treated as a confirmed negative.

## Current status

```text
usable_calibration_rows = 0
numerical_depth_ready = no
app_depth_enabled = false
earth_engine_query_executed = no
jr_whiting_measured_depth_points = 107
jr_whiting_actual_mapped_depths = yes
jr_whiting_nominal_20m_cell_support = yes
jr_whiting_depth_ordering_margin_m = 0.021336
jr_whiting_numerical_survey_accuracy = missing
jr_whiting_clean_depth_pair = no
jr_whiting_confirmed_negative = no
jr_whiting_calibration_row_ready = no
```

## Next step

Proceed to Plant Kraft AP-1. Recover and render the post-excavation topographic map and excavation-limit drawing, extract the exact confirmed-removal polygon, identify boundary-position uncertainty, and verify a stable post-removal surface period. Do not run Earth Engine until the geometry, uncertainty, and clean-pixel gates pass.
