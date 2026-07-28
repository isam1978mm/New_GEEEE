# Option 2 — Rocky Mountain Arsenal radar-ordering test result — 2026-07-28

## Decision

**NOT GOOD TO GO**

Final bounded result:

```text
ordering_inconsistent
```

The mapped 3-foot zone did not remain above the mapped 2-foot zone consistently enough across months and seasons. This site cannot support a stable relative-depth ordering rule from the tested Sentinel-1 score.

## Plain-English result

The radar comparison sometimes put the 3-foot zone above the 2-foot zone, but the direction changed with the season.

- Summer and fall mostly followed the expected order.
- Winter and spring did not.
- The result therefore looks more like a seasonal surface response than a stable depth response.

The data-quality checks passed, so the failure is not explained by missing images, unequal pixel coverage, or a meaningful incidence-angle mismatch.

## Frozen test used

Candidate:

```text
Rocky Mountain Arsenal Integrated Cover System
```

Observation period:

```text
2022-01-01 through 2024-09-30
```

Sentinel-1 selection:

```text
collection = COPERNICUS/S1_GRD
instrument mode = IW
orbit pass = DESCENDING
relative orbit = 158
```

Primary score:

```text
VV_to_VH_linear_ratio = 10 ** ((VV_dB - VH_dB) / 10)
```

Frozen expected order:

```text
mapped 3-foot zone > mapped 2-foot zone
```

The direction and thresholds were fixed before the radar values were inspected.

## Numerical result

```text
usable acquisitions = 82
usable months = 33
positive months = 20
positive-month fraction = 0.6060606061
Wilson 95% lower bound = 0.4368344082
Wilson 95% upper bound = 0.7531689257
median monthly deep-minus-shallow difference = 0.3677915535
positive seasons = 2 of 4
non-positive seasons = 2 of 4
QA pass = true
```

The supported-ordering rule required all of the following:

- at least 18 usable months;
- at least 75% positive months;
- Wilson lower bound greater than 0.50;
- positive overall median difference;
- at least three positive seasons;
- passed geometry and valid-pixel QA.

The test failed the positive-month, Wilson-bound, and seasonal-consistency requirements.

## Seasonal result

| Season | Usable months | Median deep-minus-shallow difference | Positive-month fraction | Decision |
|---|---:|---:|---:|---|
| DJF | 8 | -0.3474764345 | 0.5000000000 | non-positive |
| MAM | 9 | -0.2449244211 | 0.2222222222 | non-positive |
| JJA | 9 | 1.4126770591 | 0.8888888889 | positive |
| SON | 7 | 1.3528517746 | 0.8571428571 | positive |

Two seasons were non-positive. Under the preregistered rule, that is enough to classify the result as `ordering_inconsistent`.

## Independent package validation

The uploaded result package was checked independently against its CSV files.

Confirmed:

- 82 acquisition rows;
- 33 monthly rows;
- four seasonal rows;
- no duplicate image identifiers;
- no missing values in the acquisition table;
- all acquisitions used descending relative orbit 158;
- minimum valid-pixel counts were 36 pixels in both zones;
- monthly medians recomputed from acquisition rows matched the supplied monthly file within floating-point precision;
- Wilson interval, seasonal counts, median difference, incidence QA, and pixel-balance QA all recomputed correctly.

Result-package SHA-256:

```text
744be7df9d3fbc8a58ab63cd09c61f5f02483afea6b82edc3202d3e5dbf02c18
```

Exact execution polygons and credentials are not recorded in this public document.

## What this means for the app

```text
calibrated depth = no
calibration row created = no
training started = no
app depth enabled = no
metres or centimetres reported = no
```

The test does not unlock numerical depth estimation. It also does not justify a seasonal-only depth rule, because the changing direction is evidence against a stable depth relationship.

## Stop decision

The RMA Option 2 route is closed.

Do not:

- reverse the expected direction after seeing the result;
- select only summer and fall;
- replace the frozen primary score with a better-looking diagnostic;
- train a model on this pair;
- buy paid imagery to rescue this failed Sentinel-1 ordering result;
- add any depth field to the production app.

## Next step

Choose a different independently documented site pair and preregister a new bounded ordering test before inspecting its radar values.

The next candidate should improve on RMA by providing:

- two large and clearly separated depth conditions;
- matching final surface construction;
- stable land use and vegetation;
- clean 30–40 m interiors;
- no seasonal drainage or maintenance contrast between zones;
- a comparison that can be repeated across more than one orbit without changing the expected direction.
