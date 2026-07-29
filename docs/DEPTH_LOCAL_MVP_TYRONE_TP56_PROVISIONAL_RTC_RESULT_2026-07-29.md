# Tyrone TP5/TP6 Provisional Sentinel-1 RTC Ordering Result

Date: 2026-07-29

## Decision

**PROVISIONAL LOCAL ORDERING SUPPORTED — VH ONLY.**

This result is useful, but it is not yet an unknown-AOI depth model.

The preregistered public Sentinel-1 RTC test found that the deeper measured Tyrone zone, Test Plot 6, had higher VH backscatter than Test Plot 5 in 54 of 72 monthly comparisons (75%). VH passed the overall and every-season sign-consistency rules.

VV narrowly failed the preregistered rule. VV minus VH failed decisively.

## What was tested

Measured anchors:

- TP5: best 0.68072 m; measured interval 0.65532–0.70612 m.
- TP6: best 0.94996 m; measured interval 0.85090–1.04902 m.

Geometry:

- provisional plot placement derived from the 2006 as-built drawing, 2020 coordinate-grid drawing, multiple facility matches, and USGS mine-waste polygons;
- estimated registration uncertainty approximately 35–40 m;
- both plots eroded inward by 40 m before extraction;
- fixed-grid core pixel counts: TP5 = 20; TP6 = 29.

Radar protocol:

- Microsoft Planetary Computer `sentinel-1-rtc`;
- 2018-01-01 through 2023-12-31;
- descending relative orbit 56 selected by maximum month coverage only;
- 177 selected acquisitions, all read successfully;
- 72 usable calendar months;
- fixed 10 m EPSG:32612 grid;
- raw VV dB, VH dB, and VV minus VH dB only;
- no classifier, PCA anomaly, Option 5 anomaly score, or heuristic depth layer.

Workflow evidence:

- workflow run: `30489997733`;
- artifact: `tyrone-tp56-provisional-pc-rtc`;
- artifact ID: `8739341555`.

## Preregistered results

| Feature | Dominant TP6−TP5 sign | Dominant months | Fraction | Seasonal result | Decision |
|---|---:|---:|---:|---|---|
| VV dB | Positive | 50 / 72 | 69.4% | DJF failed at 55.6% | Failed |
| VH dB | Positive | 54 / 72 | 75.0% | All seasons passed, 66.7%–83.3% | Passed |
| VV−VH dB | Positive tie-break | 36 / 72 | 50.0% | Three seasons failed | Failed |

For VH:

- mean TP6−TP5 difference: +0.54995 dB;
- median difference: +0.61390 dB;
- Wilson 95% interval for the positive-month fraction: 0.6391–0.8356;
- season support:
  - DJF: 15/18 positive, 83.3%;
  - MAM: 12/18 positive, 66.7%;
  - JJA: 14/18 positive, 77.8%;
  - SON: 13/18 positive, 72.2%.

## Important limitation discovered after the pass

The VH separation is not temporally stationary:

- 2018–2020 mean TP6−TP5 VH difference: +0.31248 dB; 66.7% positive;
- 2021–2023 mean difference: +0.78742 dB; 83.3% positive.

The yearly mean difference increased from about +0.12 dB in 2018 to about +0.96 dB in 2023.

Therefore a single permanent conversion such as `depth = a + b × absolute VH` is not approved. Vegetation development, moisture, or other changing surface conditions could contribute to the separation.

The next method must compare an unknown local candidate with both anchors in the same acquisitions or months, so time-varying common conditions are controlled. It must also abstain when the TP5-to-TP6 VH separation is reversed or too small.

## What this result unlocks

It unlocks the next **Tyrone-only local interpolation research step**:

1. retain VH as the only candidate depth-ordering signal;
2. use same-month relative position between TP5 and TP6, not absolute VH;
3. test spatial holdouts within both plots;
4. use temporal holdouts and require stable results across early and late periods;
5. return a wide provisional range and abstain outside the two-anchor signal envelope.

## What remains blocked

```text
unknown_aoi_depth_ready = false
global_depth_ready = false
calibration_record_created = false
training_started = false
app_depth_enabled_by_default = false
```

The merged known-zone local MVP remains usable for reviewed TP5/TP6 mappings. Option 5 remains active and clearly NOT DEPTH.

## Exact next step

Preregister and run a Tyrone-only VH interpolation holdout test using spatially separated anchor and holdout pixels plus early/late temporal splits. No third-depth validation claim will be made; the goal is to decide whether a tightly bounded experimental local range can be emitted for an unknown candidate inside the same Tyrone scene.
