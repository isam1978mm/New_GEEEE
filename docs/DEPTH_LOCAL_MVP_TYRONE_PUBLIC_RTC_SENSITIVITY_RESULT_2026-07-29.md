# Tyrone public RTC multi-placement sensitivity result

Date: 2026-07-29

## Decision

**NOT GOOD TO GO for automatic unknown-AOI depth interpolation.**

Final preregistered result:

```text
ordering_inconsistent
```

The public Sentinel-1 RTC data were complete and successfully processed. The result failed because the apparent TP6-versus-TP5 ordering changed materially across plausible map placements.

This does **not** remove the merged known-zone local-depth MVP. It means Tyrone cannot support an automatic radar-to-depth interpolation for an unknown candidate with the current provisional geometry.

## Plain-English result

The radar comparison depends too strongly on exactly where the old Test Plot drawing is placed on the modern map.

Some plausible placements make the deeper TP6 zone rank above TP5. Other plausible placements weaken the relationship, and one placement that passes all monthly and seasonal thresholds gives the opposite direction.

Therefore the tested signal is not stable enough to turn an unknown radar value into metres.

## Frozen protocol

Public source:

```text
Microsoft Planetary Computer
collection = sentinel-1-rtc
period = 2018-01-01 through 2023-12-31
```

Selected metadata-only orbit:

```text
orbit state = descending
relative orbit = 56
acquisitions = 177
distinct months = 72
```

Geometry ensemble:

```text
9 source-map translations × 4 map-to-ground transforms = 36 placements
20 m inward buffer on every TP5 and TP6 polygon
fixed 10 m grid in EPSG:32613
```

Primary neutral feature:

```text
monthly median VV_dB - monthly median VH_dB
```

The RTC linear intensity assets were converted using:

```text
10 × log10(linear intensity)
```

Forbidden outputs were not used:

- classifier output;
- PCA anomaly;
- target masks;
- report layers;
- heuristic target/depth features.

## Preregistered pass rule

A placement required:

```text
usable months >= 24
dominant sign fraction >= 0.70
all four seasons >= 4 usable months
each season supports the same sign in >= 0.60 of months
```

The overall screen required:

```text
at least 29 of 36 placements pass
all passing placements share one sign
```

## Numerical result

```text
catalog items = 264
selected acquisitions = 177
successful reads = 177
failed reads = 0
usable months = 72
usable placement-month rows = 2,592
fixed grid = 47 × 45 pixels
buffered-zone pixel counts = 81 to 100
passing placements = 9 of 36
required passing placements = 29 of 36
positive-sign passing placements = 8
negative-sign passing placements = 1
final status = ordering_inconsistent
```

All 36 placements had all 72 months. Every season contained 18 months per placement. There were no zero-difference months.

## Independent validation

The downloaded JSON and CSV files were recomputed independently.

Confirmed:

- exactly 36 unique placements;
- exactly 72 unique months;
- exactly 2,592 unique placement-month rows;
- no duplicate placement-month records;
- all 177 source-item rows succeeded;
- every source used descending relative orbit 56;
- package positive/negative counts matched recomputation;
- package dominant fractions matched recomputation exactly;
- all placement pass/fail decisions matched recomputation;
- nine placements passed;
- passing signs were eight positive and one negative.

## Why the screen failed

The failure is not caused by missing data:

```text
source availability = passed
orbit consistency = passed
monthly coverage = passed
valid-pixel threshold = passed
seasonal coverage = passed
```

The failure is caused by spatial sensitivity:

```text
required placement support = 80.6% (29/36)
actual placement support = 25.0% (9/36)
all passing signs equal = no
```

The strongest positive placement had 66 positive months and 6 negative months. A different plausible placement passed with 52 negative months and 20 positive months. That reversal prevents a defensible interpolation rule.

## Product consequence

Keep:

```text
Tyrone TP5 known-zone range = 0.65532–0.70612 m; best 0.68072 m
Tyrone TP6 known-zone range = 0.85090–1.04902 m; best 0.94996 m
```

These remain reviewed measured-zone lookup outputs.

Do not:

- fit a two-anchor unknown-AOI interpolation;
- select only the best-looking placement;
- discard the opposite-sign passing placement;
- change the thresholds after seeing the result;
- create a global calibration row;
- enable automatic unknown-candidate depth.

## Next feasible product step

Move to **operator-calibrated local AOI depth**:

1. operator supplies or imports two or more measured local zones/points;
2. the app validates geometry, measurement uncertainty, surface comparability, and run quality;
3. the app fits a local-only mapping and returns a wide provisional metre range;
4. it abstains outside the measured local support;
5. the existing known-zone lookup remains available when no interpolation is justified.

This path does not depend on finding a perfect public global calibration site.

## Final state

```text
local_depth_mvp_merged = true
known_zone_ranges_available = true
public_rtc_query_executed = true
ordering_supported = false
unknown_aoi_radar_depth_ready = false
calibration_record_created = false
global_training_started = false
app_depth_enabled_for_unknown_candidates = false
```
