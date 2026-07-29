# Tyrone Same-Month VH Relative Interpolation Holdout — Preregistration

Date: 2026-07-29

Status: preregistered before the holdout query

## Purpose

Test whether the VH ordering that passed for Tyrone TP5 and TP6 is spatially reproducible inside those two plots when anchor pixels and candidate pixels are kept separate.

This is an internal holdout test. It does not provide an independent third depth and cannot by itself validate interpolation for a new AOI.

## Prior result used to define this test

The previous preregistered test found:

- TP6−TP5 VH positive in 54 of 72 months;
- all seasons passed;
- absolute VH separation changed materially between 2018–2020 and 2021–2023.

Therefore this test uses only VH and only same-month relative placement between both anchors. It does not use absolute VH as a permanent depth conversion.

## Fixed source

- Microsoft Planetary Computer `sentinel-1-rtc`.
- Period: 2018-01-01 through 2023-12-31.
- Fixed orbit: descending relative orbit 56.
- Fixed 10 m EPSG:32612 grid.
- Monthly per-pixel median.
- No Earth Engine.

## Fixed geometry and spatial splits

The same provisional 40 m cores are used:

- TP5: 20 fixed-grid pixels.
- TP6: 29 fixed-grid pixels.

Each plot is divided using fixed pixel-centre medians into west/east and north/south parts. The four directional holdout tests are:

1. west anchor, east holdout;
2. east anchor, west holdout;
3. north anchor, south holdout;
4. south anchor, north holdout.

Every anchor and holdout subset must contain at least five valid pixels.

Fixed subset sizes before the query:

- TP5: west 8, east 12, south 6, north 14;
- TP6: west 12, east 17, south 9, north 20.

## Fixed same-month interpolation formula

For each split and month:

```text
anchor_separation = VH_TP6_anchor − VH_TP5_anchor
relative_position = (VH_candidate − VH_TP5_anchor) / anchor_separation
estimated_depth = depth_TP5 + relative_position × (depth_TP6 − depth_TP5)
```

Known best depths:

- TP5 = 0.68072 m.
- TP6 = 0.94996 m.

A month is used only if:

```text
anchor_separation >= 0.25 dB
```

This is an abstention rule. Estimated values are not clamped to the anchor range during evaluation.

## Fixed time periods

- all: 2018–2023;
- early: 2018–2020;
- late: 2021–2023.

## Pass rules

For each split and each time period, both held-out zones must pass their error rules and TP6 must retain the deeper estimated ordering.

### All-period rule

- at least 18 usable months;
- median absolute error no more than 0.10 m for each held-out zone;
- at least 75% of monthly estimates within 0.20 m of the known zone depth;
- TP6 estimated deeper than TP5 in at least 75% of paired usable months.

### Early and late rules

For each period separately:

- at least 8 usable months;
- median absolute error no more than 0.15 m for each zone;
- at least 65% of monthly estimates within 0.20 m;
- TP6 estimated deeper than TP5 in at least 65% of paired usable months.

A directional split passes only if all, early, and late pass. The overall internal holdout screen passes only if at least three of the four directional splits pass.

## Interpretation

If the screen passes, it supports spatial reproducibility of a Tyrone-only relative-VH method inside the two known-depth zones. It does not validate a third depth, another site, or a global model.

If the screen fails, unknown-candidate interpolation remains blocked and the app keeps only the known-zone lookup ranges.

Regardless of outcome:

```text
calibration_record_created = false
training_started = false
unknown_aoi_depth_ready = false
app_depth_enabled = false
```

## Prohibited inputs

No VV, VV−VH, classifier output, target mask, PCA anomaly, Option 5 anomaly, or heuristic treasure/geophysics layer may be substituted after results are seen.
