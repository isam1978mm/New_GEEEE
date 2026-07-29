# Tyrone VH Two-Band Fresh Temporal Holdout Result

Date: 2026-07-29

## Decision

**NOT GOOD TO GO for automatic Tyrone shallow/deep depth-band output.**

The preregistered test used Sentinel-1 data from 2024-01-01 through 2026-06-30, which were not used in the 2018–2023 development work. Zero of four spatial splits passed the complete all-period, 2024, and 2025–June 2026 rules.

## Execution

- workflow run: `30492045036`;
- artifact: `tyrone-vh-depth-band-holdout`;
- artifact ID: `8740083260`;
- selected public Sentinel-1 RTC acquisitions: 73;
- successful reads: 73;
- read failures: 0;
- polarization: VH only;
- descending relative orbit: 56;
- output choices: shallow measured range, deep measured range, or abstain;
- classifier/PCA outputs used: no;
- Earth Engine query: no.

## Frozen numeric bands

- shallow: 0.65532–0.70612 m;
- deep: 0.85090–1.04902 m.

The method abstained outside the two confident relative-position regions and did not extrapolate beyond the two anchors.

## Result summary

Required passing spatial splits: 3 of 4.

Actual passing spatial splits: **0 of 4**.

| Spatial split | Fresh eligible months | TP5 coverage / accuracy | TP6 coverage / accuracy | Paired correct fraction | Complete result |
|---|---:|---:|---:|---:|---|
| West anchors → east holdouts | 16 | 31.3% / 80.0% | 37.5% / 50.0% | 66.7% | Failed |
| East anchors → west holdouts | 23 | 30.4% / 71.4% | 30.4% / 85.7% | 25.0% | Failed |
| North anchors → south holdouts | 21 | 28.6% / 83.3% | 33.3% / 42.9% | 50.0% | Failed |
| South anchors → north holdouts | 17 | 35.3% / 50.0% | 17.6% / 100.0% | 100.0% from only one paired month | Failed |

The period-specific checks also failed. Examples:

- west-anchor/east-holdout TP6 accuracy was only 33.3% in 2024;
- east-anchor/west-holdout paired correct fraction was 0% in 2025–June 2026;
- north-anchor/south-holdout TP6 accuracy was 50% in 2025–June 2026;
- south-anchor/north-holdout TP5 accuracy was 0% in 2025–June 2026.

The problem is not only conservative abstention. Confident wrong classifications remain present, especially for TP6 in multiple splits and TP5 in the later south-anchor split.

## Product decision

Do not implement an automatic Tyrone depth-band mode from this VH rule.

Do not loosen the frozen thresholds after seeing the result. Lowering the coverage or accuracy requirements would not remove the observed confident errors.

## What remains usable

The following merged modes remain available:

1. reviewed known-zone lookup, returning the measured range for an explicitly identified zone;
2. operator-calibrated local AOI interpolation using measured local anchors;
3. automatic extraction of the approved local radar signal from reviewed GeoJSON polygons;
4. abstention outside measured local signal support.

These are the feasible path because the operator supplies real local measured anchors and exact polygons rather than relying on the failed Tyrone transfer rule.

## Exact next step

Move the operator-calibrated local AOI workflow into the app interface:

- upload reviewed private GeoJSON zones;
- provide measured depth ranges for at least two anchor zones;
- extract the canonical radar signal automatically;
- build the local package;
- run supported candidates;
- show metre ranges only inside the measured local support;
- abstain elsewhere.

## Safety state

```text
continuous_unknown_depth_ready = false
tyrone_automatic_depth_band_ready = false
operator_calibrated_local_aoi_ready = true
calibration_record_created_from_tyrone = false
training_started = false
app_depth_enabled_by_default = false
```
