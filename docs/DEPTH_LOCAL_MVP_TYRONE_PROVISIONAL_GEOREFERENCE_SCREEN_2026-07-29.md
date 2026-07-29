# Tyrone provisional georeference screen

Date: 2026-07-29

## Decision

**NOT GOOD TO GO as one fixed execution polygon.**

The 2006 Test Plot 5/6 drawing can be placed approximately on the 2020 Mangas Valley map, but the remaining registration ambiguity is too large to support one defensible 10 m Sentinel-1 extraction polygon.

This result does **not** reverse the merged local-depth MVP. The reviewed-zone lookup remains usable. It blocks only the next step that would infer an unknown candidate from radar.

## Method used

1. Confirmed the 2006 overview crop is an exact native-resolution crop of the official as-built figure.
2. Used the printed scale bars:
   - 2006 figure: 1,000 ft across 360 rendered pixels = 2.7778 ft/pixel.
   - 2020 figure: 4,400 ft across 320 rendered pixels = 13.75 ft/pixel.
3. Locked the scale ratio at 0.2020202 and north-up orientation.
4. Compared stable low-saturation contour and road linework outside the reclaimed/test-plot interiors.
5. Searched translation only; no free rescaling was allowed.
6. Used the No. 3 / No. 3X facility relationship as a semantic check so the main plot group remained on No. 3X and the separate No. 3 plot remained near No. 3.

## Numerical result

Best local chamfer placement on the 2020 rendered map:

```text
translation_x_px = 484
translation_y_px = 504
fixed_scale_ratio = 0.2020202
```

Near-best placements within the tight local score basin span approximately:

```text
x = 481 to 505 pixels
y = 477 to 507 pixels
```

At the 2020 map scale this is approximately:

```text
east-west span = 330 ft
north-south span = 413 ft
```

These spans are sensitivity bounds from the registration score surface, not a formal survey confidence interval.

## Plot-size comparison

Approximate minimum plot dimensions from the official 2006 drawing:

```text
Test Plot 5 minimum dimension ≈ 381 ft
Test Plot 6 minimum dimension ≈ 401 ft
```

Using half of the near-best north-south span as positional uncertainty gives about 206 ft. Adding a 20 m radar-edge exclusion adds about 66 ft.

Required minimum width for a surviving symmetric clean interior:

```text
2 × (206 ft + 66 ft) ≈ 544 ft
```

Both plots are narrower than this. Therefore the conservative clean interiors collapse.

## Geographic-control cross-check

A separate image-to-UTM similarity fit using the USGS polygon centroids for Tailings Impoundments No. 3, No. 3X, and No. 2 produced facility-centroid residuals of approximately:

```text
38 m
93 m
56 m
```

That independent check confirms that the map-to-ground step is also too uncertain for one fixed 10 m execution polygon.

## What remains usable

The merged local-depth MVP can still write the reviewed measured ranges:

```text
Tyrone TP5: 0.65532–0.70612 m; best 0.68072 m
Tyrone TP6: 0.85090–1.04902 m; best 0.94996 m
```

Those are known-zone lookup outputs, not unknown-AOI radar inference.

## Approved next step

Do not choose one supposedly exact polygon.

Run a **multi-placement sensitivity test** across the plausible georeference shifts. Extract only approved raw Sentinel-1 measurements and controls. Advance only if the TP6-versus-TP5 ordering remains consistent across the placement ensemble.

The sensitivity test must:

- preserve the fixed scale and north-up orientation;
- sample the near-best translation basin;
- use raw VV, VH, incidence, and neutral VV/VH transforms only;
- exclude classifier, PCA anomaly, target-mask, and report-layer outputs;
- report the fraction of placements supporting the same ordering;
- create no calibration row unless the preregistered threshold passes;
- keep app depth disabled if ordering is unstable.

## Current state

```text
local_depth_mvp_merged = true
known_zone_ranges_available = true
single_fixed_plot_geometry_ready = false
unknown_aoi_radar_depth_ready = false
earth_engine_sensitivity_query_executed = false
calibration_record_created = false
training_started = false
app_depth_enabled = false
```
