# Tyrone Same-Month VH Relative Interpolation Holdout Result

Date: 2026-07-29

## Decision

**NOT GOOD TO GO for continuous unknown-candidate depth interpolation.**

The preregistered same-month VH formula did not reproduce the known TP5 and TP6 depths reliably when anchor pixels and evaluated pixels were spatially separated.

Zero of four directional splits passed the complete all-period, early-period, and late-period rules.

## Evidence

Workflow:

- workflow run: `30490944902`;
- artifact: `tyrone-vh-relative-holdout`;
- artifact ID: `8739699062`;
- selected public Sentinel-1 RTC acquisitions: 177;
- successful reads: 177;
- read failures: 0.

Fixed method:

- VH dB only;
- descending relative orbit 56;
- 2018–2023;
- same-month linear position between TP5 = 0.68072 m and TP6 = 0.94996 m;
- four west/east and north/south directional splits;
- abstention when anchor separation was below 0.25 dB;
- separate 2018–2020 and 2021–2023 checks.

## Split results

| Directional split | Usable months | Overall TP5 median absolute error | Overall TP6 median absolute error | Overall TP6 deeper fraction | Complete split decision |
|---|---:|---:|---:|---:|---|
| West anchors → east holdouts | 48 | 0.144 m | 0.136 m | 62.5% | Failed |
| East anchors → west holdouts | 40 | 0.177 m | 0.204 m | 75.0% | Failed |
| North anchors → south holdouts | 47 | 0.151 m | 0.128 m | 57.4% | Failed |
| South anchors → north holdouts | 31 | 0.200 m | 0.072 m | 74.2% | Failed |

Important examples:

- west-anchor/east-holdout early-period TP6 median absolute error was 0.214 m;
- east-anchor/west-holdout early-period TP6 median absolute error was 0.227 m;
- south-anchor/north-holdout early-period TP5 median absolute error was 0.304 m;
- north-anchor/south-holdout late-period paired ordering was only 53.6%.

The p10–p90 ranges were also wide and often extended well outside the two measured anchor depths. Therefore widening the output interval alone would not convert this into a defensible continuous-depth method.

## What remains usable

The known-zone local MVP remains valid for reviewed mappings:

- TP5 range: 0.65532–0.70612 m;
- TP6 range: 0.85090–1.04902 m.

The earlier whole-core VH ordering result also remains valid as provisional local ordering evidence.

## Post-hoc observation — not validation

Although continuous errors failed, the overall median estimates fell on the correct shallow/deep side for TP5 and TP6 in all four directional splits when classified using the midpoint between the two best measured depths.

This observation was made after viewing the holdout result. It cannot be counted as a passed test.

It does identify a more feasible target: a **two-band local depth output** instead of an exact interpolated metre value.

Proposed bands:

- shallow local band: 0.65532–0.70612 m;
- deep local band: 0.85090–1.04902 m;
- otherwise: abstain.

## Exact next step

Preregister a fresh temporal holdout using data not used in the 2018–2023 development period:

- holdout period: 2024-01-01 through 2026-06-30;
- same fixed orbit, geometry, spatial splits, and VH-only formula;
- classify only into the two measured numeric ranges;
- require consistent results across 2024 and 2025–June 2026;
- abstain when anchor separation or band confidence is inadequate.

If the fresh temporal holdout passes, implement a Tyrone-only experimental depth-band mode. It will return a measured numeric range, not a false precise depth.

## Safety state

```text
continuous_unknown_depth_ready = false
depth_band_ready = false
calibration_record_created = false
training_started = false
app_depth_enabled_by_default = false
```
