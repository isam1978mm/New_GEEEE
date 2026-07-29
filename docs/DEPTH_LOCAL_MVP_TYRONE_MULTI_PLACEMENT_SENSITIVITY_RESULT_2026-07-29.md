# Tyrone provisional geometry multi-placement sensitivity result — 2026-07-29

## Decision

**NOT GOOD TO GO for unknown-AOI radar depth inference from the provisional Tyrone geometry.**

The first manually derived Test Plot 5/6 placement produced a promising local ordering result. That single placement was not enough. A required sensitivity test was therefore run across multiple plausible map transformations and positional shifts.

The ordering did not remain stable across the allowed geometry uncertainty.

This result does **not** remove or disable the local known-zone MVP. The merged MVP may still return the documented measured ranges when an operator explicitly selects the reviewed Tyrone zone IDs. It does not infer a new unknown AOI's depth from radar.

## What was tested

The test used:

- the measured Tyrone Test Plot 5 and Test Plot 6 depth anchors;
- provisional plot geometry derived from the 2006 as-built drawing and the 2020 closure-plan map;
- four alternative map-fit hypotheses;
- nine positional shifts for each fit;
- 36 geometry hypotheses total;
- a conservative 20 m plot-edge buffer;
- Sentinel-1 RTC from the Microsoft Planetary Computer;
- descending relative orbit 56;
- January 2018 through December 2023;
- 177 successfully read acquisitions covering 72 months;
- raw radar-derived polarization contrast only;
- no classifier output and no PCA anomaly score.

The primary comparison feature was:

```text
monthly median VV_dB minus monthly median VH_dB
```

## Result

```text
geometry hypotheses tested = 36
placements passing the local ordering screen = 9
passing placements with one shared sign = 8
passing placements required for robustness = 29
final status = ordering_inconsistent
```

The problem is not merely that many placements failed. The apparent direction also changed: at least one passing placement produced the opposite dominant sign. A depth relationship that changes direction when the provisional polygons move within their allowed registration uncertainty is not safe to use for unknown-area inference.

## What remains valid

The documentary ground truth remains strong:

- Test Plot 5 measured range: 0.65532–0.70612 m; best 0.68072 m;
- Test Plot 6 measured range: 0.85090–1.04902 m; best 0.94996 m;
- full-scale adjacent plots;
- comparable upper construction and revegetation;
- measured uncertainty.

The merged local-depth MVP remains valid for an explicit reviewed-zone lookup:

```text
tyrone_tp5 -> provisional measured local range
tyrone_tp6 -> provisional measured local range
```

This is a local lookup result, not a radar estimate for a new candidate.

## Operational state

```text
scientific_query_executed = true
earth_engine_query_executed = false
classifier_output_used = false
pca_anomaly_used = false
calibration_record_created = false
training_started = false
unknown_aoi_depth_enabled = false
app_depth_enabled = false
local_known_zone_mvp = available_off_by_default
```

## Exact blocker

The remaining blocker is positional certainty. The provisional transfer from the 2006 as-built drawing to geographic coordinates is too uncertain relative to the 10 m radar grid. Small allowed changes move the extracted pixels enough to alter the ordering result.

## Reopen rule

Unknown-AOI Tyrone radar interpolation may be reopened only after one of these occurs:

1. official Test Plot 5/6 CAD, GIS, surveyed corners, or another coordinate-controlled geometry source is recovered; or
2. an independently defensible georeference reduces the plot-position uncertainty enough that a preregistered sensitivity test passes consistently across the remaining uncertainty envelope.

## Current plan

- Keep the merged local measured-zone MVP.
- Do not expose Tyrone as an automatic radar-to-depth model.
- Keep Option 5 active and clearly labelled **NOT DEPTH**.
- Continue feasible depth work through operator-provided local calibration geometry or direct before/after elevation data.
