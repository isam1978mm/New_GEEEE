# Tyrone VH Two-Band Fresh Temporal Holdout Preregistration

Date: 2026-07-29

## Purpose

Test the simplest remaining automatic local-depth output using Sentinel-1 data that were not used in development.

This test does **not** evaluate continuous metre interpolation. It evaluates only:

- shallow local range: **0.65532–0.70612 m**;
- deep local range: **0.85090–1.04902 m**;
- otherwise: **abstain**.

No test rule may be changed after the 2024–June 2026 results are read.

## Fresh holdout data

- Development data already examined: 2018-01-01 through 2023-12-31.
- Fresh holdout: 2024-01-01 through 2026-06-30.
- Source: Microsoft Planetary Computer `sentinel-1-rtc`.
- Polarization: VH only.
- Orbit: descending relative orbit 56.
- Monthly value: median of all successfully read acquisitions in that month.
- Geometry: the same provisional 40 m TP5 and TP6 cores used by the prior spatial holdout.
- Spatial splits:
  - west anchors → east holdouts;
  - east anchors → west holdouts;
  - north anchors → south holdouts;
  - south anchors → north holdouts.

## Fixed monthly rule

For each month and split:

1. Calculate mean VH dB in the TP5 and TP6 anchor halves.
2. Abstain for the month when TP6−TP5 anchor separation is below **0.25 dB**.
3. Calculate each holdout's relative position:

```text
position = (holdout_vh - anchor_tp5_vh) /
           (anchor_tp6_vh - anchor_tp5_vh)
```

4. Do not extrapolate outside position 0–1.
5. Classify:
   - position ≤ 1/3 → shallow;
   - position ≥ 2/3 → deep;
   - middle third → abstain.

The continuous depth value is retained only as a diagnostic. The proposed product output is one of the two measured ranges, never a false precise value.

## Frozen pass rules

Every spatial split is evaluated over:

- all fresh months;
- calendar year 2024;
- January 2025 through June 2026.

A period passes only when both known zones meet the frozen minimum coverage and conditional accuracy rules, and enough months classify both zones correctly together.

| Period | Eligible months | Zone coverage | Zone accuracy | Paired classified months | Paired correct fraction |
|---|---:|---:|---:|---:|---:|
| All | ≥12 | ≥50% | ≥80% | ≥6 | ≥80% |
| 2024 | ≥5 | ≥40% | ≥75% | ≥2 | ≥75% |
| 2025–June 2026 | ≥8 | ≥40% | ≥75% | ≥3 | ≥75% |

A spatial split passes only if all three periods pass.

The complete holdout passes only if at least **3 of 4** spatial splits pass.

## Decision boundary

If the test passes:

- a Tyrone-only experimental depth-band implementation may proceed;
- the output must remain local, provisional, and off by default;
- continuous unknown depth remains unsupported.

If the test fails:

- no automatic Tyrone depth-band output will be implemented from this VH rule;
- the reviewed known-zone lookup and operator-calibrated AOI tools remain usable.

## Safety state before execution

```text
continuous_unknown_depth_ready = false
depth_band_ready = false
calibration_record_created = false
training_started = false
app_depth_enabled_by_default = false
```
