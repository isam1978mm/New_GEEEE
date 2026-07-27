# Sconondoa Phase 3 Pixel-Support Dry Run — 2026-07-26

## Decision

```text
HOLD — CURRENT POLYGONS ARE TOO SMALL FOR A CLEAN 20 M SENTINEL-1 FOOTPRINT
```

The survey georeferencing correction remains valid. The excavation depths and comparable restoration evidence also remain valid.

The new blocker is the physical size and shape of the two selected polygons after allowing for the documented 1.1 m placement uncertainty.

## Test performed

The corrected WGS84 polygons were projected to UTM Zone 18N (`EPSG:32618`).

For each polygon:

1. the boundary was moved inward by 1.1 m to account for conservative placement uncertainty;
2. the maximum inscribed-circle diameter was calculated;
3. that diameter was compared with the planned 20 m Sentinel-1 analysis footprint.

A fully contained 20 m square necessarily contains a circle with a 10 m radius. Therefore, if the largest circle that fits inside a safe polygon has a diameter below 20 m, a clean 20 m square cannot fit either.

## Shallow polygon — upper Cell A

```text
original area = 387.206 m²
safe area after 1.1 m inward allowance = 306.680 m²
maximum inscribed radius = 8.318 m
maximum inscribed diameter = 16.637 m
clean 20 m footprint = NO
```

## Deep polygon — combined Cells B and C

```text
original area = 498.444 m²
safe area after 1.1 m inward allowance = 405.049 m²
maximum inscribed radius = 9.393 m
maximum inscribed diameter = 18.787 m
clean 20 m footprint = NO
```

The deep polygon also crosses the internal Cell B/Cell C boundary.

## Why the Sentinel-1 query was not run

The geometry gate failed first. Acquisition availability cannot repair a polygon that cannot contain one clean 20 m analysis footprint.

Therefore:

```text
Sentinel-1 catalogue query executed = no
Earth Engine query executed = no
radar backscatter extracted = no
calibration row created = no
```

This avoids producing a misleading result dominated by edge mixing, nearby surface features, or the internal B/C boundary.

## What this does not invalidate

The following remain supported by the engineering records:

- Phase 3 excavation depths are finite and surveyed;
- the shallow and deep depth ranges are non-overlapping;
- Cells A, B, and C have the same documented surface-restoration assembly;
- the survey-to-State-Plane georeferencing correction passed its independent holdout check.

Only the current execution polygons fail.

## Current status

```text
usable_calibration_rows = 0
numerical_depth_ready = no
app_depth_enabled = false
earth_engine_query_executed = no
survey_georeference_corrected = yes
depth_ordering_documented = yes
current_polygon_pixel_support = failed
live_radar_method_screen_ready = no
```

## Next step

Redesign larger shallow and deep polygons from the Phase 3 survey. Each replacement polygon must still preserve non-overlapping measured depth ranges and comparable restoration, while providing at least one clean 20 m interior footprint after the 1.1 m placement allowance.

Only after the replacement polygons pass this geometry gate should the Sentinel-1 acquisition and same-orbit coverage query run.
